/*
 * HaLow SLIP Bridge for myc3lium
 *
 * Bridges Ethernet frames between a TAP interface and an ESP32 HaLow
 * radio connected via USB serial (CP210x). Uses SLIP framing to
 * delineate Ethernet frames on the serial byte stream.
 *
 * Reconstructed from deployed binary symbols + lora-tap-bridge.c template.
 * Original source: pi-slip-daemon.c (lorpBot workspace)
 *
 * Architecture:
 *   TAP(halow0) <--read/write--> SLIP encode/decode <--serial--> ESP32 HaLow
 *
 * TODO: Replace SLIP with COBS + CRC-32 for bounded overhead and error detection.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <fcntl.h>
#include <termios.h>
#include <sys/ioctl.h>
#include <sys/select.h>
#include <linux/if.h>
#include <linux/if_tun.h>

/* SLIP framing constants (RFC 1055) */
#define SLIP_END     0xC0
#define SLIP_ESC     0xDB
#define SLIP_ESC_END 0xDC
#define SLIP_ESC_ESC 0xDD

/* Buffer sizes */
#define TAP_MTU       1560  /* 1500 + headroom for BATMAN-adv overhead */
#define SERIAL_BUF    4096
#define SLIP_MAX_FRAME (TAP_MTU * 2 + 2)  /* Worst case: every byte escaped + 2 ENDs */

/* Defaults */
#define DEFAULT_TAP_NAME   "halow0"
#define DEFAULT_SERIAL_DEV "/dev/ttyUSB0"
#define DEFAULT_BAUD       921600

/* Global state */
static volatile sig_atomic_t running = 1;
static int tap_fd = -1;
static int serial_fd = -1;

/* Statistics */
static unsigned long tx_packets = 0;
static unsigned long rx_packets = 0;
static unsigned long tx_bytes = 0;
static unsigned long rx_bytes = 0;

/* SLIP decoder state */
typedef struct {
    uint8_t buf[TAP_MTU];
    size_t  len;
    int     in_escape;
    int     dropping;  /* M5: discard bytes until next SLIP_END after overflow */
} slip_decoder_t;

static slip_decoder_t slip_rx;

static void signal_handler(int sig)
{
    (void)sig;
    running = 0;
}

/* ---- TAP interface ---- */

static int create_tap(const char *dev_name)
{
    struct ifreq ifr;
    int fd;

    fd = open("/dev/net/tun", O_RDWR);
    if (fd < 0) {
        perror("open /dev/net/tun");
        return -1;
    }

    memset(&ifr, 0, sizeof(ifr));
    ifr.ifr_flags = IFF_TAP | IFF_NO_PI;
    strncpy(ifr.ifr_name, dev_name, IFNAMSIZ - 1);

    if (ioctl(fd, TUNSETIFF, (void *)&ifr) < 0) {
        perror("ioctl TUNSETIFF");
        close(fd);
        return -1;
    }

    printf("Created TAP interface: %s\n", ifr.ifr_name);
    return fd;
}

/* ---- Serial port ---- */

static int open_serial(const char *device, int baud)
{
    int fd = open(device, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (fd < 0) {
        perror("open serial");
        return -1;
    }

    /* Use TCGETS2/TCSETS2 for custom baud rates on Linux */
    struct termios2 tio;
    if (ioctl(fd, TCGETS2, &tio) < 0) {
        perror("TCGETS2");
        close(fd);
        return -1;
    }

    /* Raw mode */
    tio.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR |
                      IGNCR | ICRNL | IXON);
    tio.c_oflag &= ~OPOST;
    tio.c_lflag &= ~(ECHO | ECHONL | ICANON | ISIG | IEXTEN);
    tio.c_cflag &= ~(CSIZE | PARENB);
    tio.c_cflag |= CS8 | CLOCAL | CREAD;

    /* Custom baud rate */
    tio.c_cflag &= ~CBAUD;
    tio.c_cflag |= BOTHER;
    tio.c_ispeed = baud;
    tio.c_ospeed = baud;

    /* Non-blocking reads */
    tio.c_cc[VMIN] = 0;
    tio.c_cc[VTIME] = 0;

    if (ioctl(fd, TCSETS2, &tio) < 0) {
        perror("TCSETS2");
        close(fd);
        return -1;
    }

    tcflush(fd, TCIOFLUSH);

    printf("Opened serial: %s @ %d baud\n", device, baud);
    return fd;
}

/* ---- SLIP framing ---- */

static void slip_decoder_init(slip_decoder_t *dec)
{
    dec->len = 0;
    dec->in_escape = 0;
    dec->dropping = 0;
}

/*
 * Feed one byte to the SLIP decoder.
 * Returns 1 when a complete frame is available in dec->buf (length in dec->len).
 * Returns 0 when more bytes are needed.
 * Returns -1 on framing error (frame too large).
 */
static int slip_decode_byte(slip_decoder_t *dec, uint8_t byte)
{
    if (byte == SLIP_END) {
        /* M5: END always resyncs — stop dropping on frame boundary */
        dec->dropping = 0;
        if (dec->len > 0) {
            /* Frame complete */
            return 1;
        }
        /* Empty frame (inter-frame END), ignore */
        return 0;
    }

    /* M5: Discard bytes until next SLIP_END after overflow */
    if (dec->dropping) {
        return 0;
    }

    if (byte == SLIP_ESC) {
        dec->in_escape = 1;
        return 0;
    }

    if (dec->in_escape) {
        dec->in_escape = 0;
        if (byte == SLIP_ESC_END) {
            byte = SLIP_END;
        } else if (byte == SLIP_ESC_ESC) {
            byte = SLIP_ESC;
        }
        /* else: protocol violation, pass through */
    }

    if (dec->len >= sizeof(dec->buf)) {
        /* Frame too large — enter drop mode until next SLIP_END */
        fprintf(stderr, "SLIP: frame too large (%zu bytes), dropping until resync\n", dec->len);
        dec->len = 0;
        dec->in_escape = 0;
        dec->dropping = 1;
        return -1;
    }

    dec->buf[dec->len++] = byte;
    return 0;
}

/*
 * SLIP-encode an Ethernet frame and write to serial fd.
 * Returns number of bytes written, or -1 on error.
 */
static ssize_t slip_encode(int fd, const uint8_t *frame, size_t len)
{
    uint8_t slip_buf[SLIP_MAX_FRAME];
    size_t pos = 0;

    slip_buf[pos++] = SLIP_END;

    for (size_t i = 0; i < len; i++) {
        switch (frame[i]) {
        case SLIP_END:
            slip_buf[pos++] = SLIP_ESC;
            slip_buf[pos++] = SLIP_ESC_END;
            break;
        case SLIP_ESC:
            slip_buf[pos++] = SLIP_ESC;
            slip_buf[pos++] = SLIP_ESC_ESC;
            break;
        default:
            slip_buf[pos++] = frame[i];
            break;
        }
    }

    slip_buf[pos++] = SLIP_END;

    ssize_t written = 0;
    while ((size_t)written < pos) {
        ssize_t n = write(fd, slip_buf + written, pos - written);
        if (n < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                usleep(100);
                continue;
            }
            perror("write serial");
            return -1;
        }
        written += n;
    }

    return written;
}

/* ---- Main ---- */

int main(int argc, char *argv[])
{
    const char *tap_name = DEFAULT_TAP_NAME;
    const char *serial_dev = DEFAULT_SERIAL_DEV;
    int baud = DEFAULT_BAUD;

    /* Simple arg parsing: -t <tap> -d <serial> -b <baud> */
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-t") == 0 && i + 1 < argc) {
            tap_name = argv[++i];
        } else if (strcmp(argv[i], "-d") == 0 && i + 1 < argc) {
            serial_dev = argv[++i];
        } else if (strcmp(argv[i], "-b") == 0 && i + 1 < argc) {
            baud = atoi(argv[++i]);
        }
    }

    printf("HaLow SLIP Bridge starting...\n");

    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    /* Create TAP interface */
    tap_fd = create_tap(tap_name);
    if (tap_fd < 0) {
        return 1;
    }

    /* Open serial port */
    serial_fd = open_serial(serial_dev, baud);
    if (serial_fd < 0) {
        close(tap_fd);
        return 1;
    }

    slip_decoder_init(&slip_rx);

    printf("Bridge active (TAP mode): %s <-> %s\n", tap_name, serial_dev);
    printf("Configure with: sudo ip addr add 192.168.1.2/24 dev %s\n", tap_name);
    printf("               sudo ip link set %s up\n", tap_name);

    int max_fd = (tap_fd > serial_fd ? tap_fd : serial_fd) + 1;

    while (running) {
        fd_set readfds;
        FD_ZERO(&readfds);
        FD_SET(tap_fd, &readfds);
        FD_SET(serial_fd, &readfds);

        struct timeval tv = {.tv_sec = 1, .tv_usec = 0};
        int ret = select(max_fd, &readfds, NULL, NULL, &tv);

        if (ret < 0) {
            if (errno == EINTR) continue;
            perror("select");
            break;
        }

        /* TAP → serial (outgoing Ethernet frames) */
        if (FD_ISSET(tap_fd, &readfds)) {
            uint8_t frame[TAP_MTU];
            ssize_t n = read(tap_fd, frame, sizeof(frame));
            if (n > 0) {
                if (slip_encode(serial_fd, frame, n) > 0) {
                    tx_packets++;
                    tx_bytes += n;
                    printf("TX: %zd bytes (total: %lu pkts, %lu bytes)\n",
                           n, tx_packets, tx_bytes);
                }
            } else if (n < 0 && errno != EAGAIN) {
                perror("read tap");
            }
        }

        /* Serial → TAP (incoming SLIP frames) */
        if (FD_ISSET(serial_fd, &readfds)) {
            uint8_t buf[SERIAL_BUF];
            ssize_t n = read(serial_fd, buf, sizeof(buf));
            if (n > 0) {
                for (ssize_t i = 0; i < n; i++) {
                    int result = slip_decode_byte(&slip_rx, buf[i]);
                    if (result == 1) {
                        /* Complete frame received */
                        ssize_t w = write(tap_fd, slip_rx.buf, slip_rx.len);
                        if (w > 0) {
                            rx_packets++;
                            rx_bytes += slip_rx.len;
                            printf("RX: %zu bytes (total: %lu pkts, %lu bytes)\n",
                                   slip_rx.len, rx_packets, rx_bytes);
                        } else {
                            perror("write tap");
                        }
                        slip_rx.len = 0;
                    }
                }
            } else if (n < 0 && errno != EAGAIN) {
                perror("read serial");
            }
        }
    }

    printf("Shutting down...\n");
    printf("Final stats: TX %lu pkts/%lu bytes, RX %lu pkts/%lu bytes\n",
           tx_packets, tx_bytes, rx_packets, rx_bytes);

    if (tap_fd >= 0) close(tap_fd);
    if (serial_fd >= 0) close(serial_fd);

    printf("Shutdown complete\n");
    return 0;
}
