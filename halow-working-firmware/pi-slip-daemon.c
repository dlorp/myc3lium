/*
 * HaLow SLIP Bridge Daemon for Raspberry Pi
 * Fixed for custom baud rates using termios2
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <sys/select.h>
#include <linux/if.h>
#include <linux/if_tun.h>
#include <asm/termbits.h>
#include <signal.h>

#define SERIAL_DEV "/dev/ttyUSB0"
#define SERIAL_BAUD 921600
#define TAP_NAME "halow0"
#define MTU 1500

// SLIP protocol constants
#define SLIP_END 0xC0
#define SLIP_ESC 0xDB
#define SLIP_ESC_END 0xDC
#define SLIP_ESC_ESC 0xDD

static int running = 1;
static int tap_fd = -1;
static int serial_fd = -1;
static unsigned long tx_packets = 0;
static unsigned long rx_packets = 0;
static unsigned long tx_bytes = 0;
static unsigned long rx_bytes = 0;

void signal_handler(int sig)
{
    printf("\nShutting down...\n");
    running = 0;
}

int create_tap(const char *name)
{
    struct ifreq ifr;
    int fd, err;
    
    fd = open("/dev/net/tun", O_RDWR);
    if (fd < 0) {
        perror("open /dev/net/tun");
        return -1;
    }
    
    memset(&ifr, 0, sizeof(ifr));
    ifr.ifr_flags = IFF_TAP | IFF_NO_PI;
    strncpy(ifr.ifr_name, name, IFNAMSIZ - 1);
    
    err = ioctl(fd, TUNSETIFF, (void *)&ifr);
    if (err < 0) {
        perror("ioctl TUNSETIFF");
        close(fd);
        return -1;
    }
    
    printf("Created TAP interface: %s\n", ifr.ifr_name);
    return fd;
}

int open_serial_custom_baud(const char *dev, int baud_rate)
{
    struct termios2 tio;
    int fd;
    
    fd = open(dev, O_RDWR | O_NOCTTY | O_NDELAY);
    if (fd < 0) {
        perror("open serial");
        return -1;
    }
    
    // Get current serial port settings
    if (ioctl(fd, TCGETS2, &tio)) {
        perror("TCGETS2");
        close(fd);
        return -1;
    }
    
    // Set custom baud rate
    tio.c_cflag &= ~CBAUD;
    tio.c_cflag |= BOTHER;
    tio.c_ispeed = baud_rate;
    tio.c_ospeed = baud_rate;
    
    // Configure: 8N1, no flow control, raw mode
    tio.c_cflag &= ~PARENB;  // No parity
    tio.c_cflag &= ~CSTOPB;  // 1 stop bit
    tio.c_cflag &= ~CSIZE;
    tio.c_cflag |= CS8;      // 8 data bits
    tio.c_cflag &= ~CRTSCTS; // No hardware flow control
    tio.c_cflag |= CREAD | CLOCAL;
    
    tio.c_lflag = 0;         // No canonical, echo, signals
    tio.c_oflag = 0;         // No output processing
    tio.c_iflag = 0;         // No input processing
    
    tio.c_cc[VMIN]  = 0;
    tio.c_cc[VTIME] = 1;     // 0.1 sec read timeout
    
    // Apply settings
    if (ioctl(fd, TCSETS2, &tio)) {
        perror("TCSETS2");
        close(fd);
        return -1;
    }
    
    // Flush buffers
    tcflush(fd, TCIOFLUSH);
    
    printf("Opened serial: %s @ %d baud\n", dev, baud_rate);
    return fd;
}

// SLIP decode state
typedef struct {
    unsigned char buf[MTU * 2];
    size_t len;
    int escaped;
} slip_decoder_t;

void slip_decoder_init(slip_decoder_t *d)
{
    d->len = 0;
    d->escaped = 0;
}

int slip_decode_byte(slip_decoder_t *d, unsigned char c, unsigned char *out, size_t out_size)
{
    if (c == SLIP_END) {
        if (d->len > 0) {
            if (d->len <= out_size) {
                memcpy(out, d->buf, d->len);
                size_t pkt_len = d->len;
                d->len = 0;
                d->escaped = 0;
                return pkt_len;
            } else {
                d->len = 0;
                d->escaped = 0;
                return -1;
            }
        }
        return 0;
    }
    
    if (d->escaped) {
        if (c == SLIP_ESC_END) c = SLIP_END;
        else if (c == SLIP_ESC_ESC) c = SLIP_ESC;
        d->escaped = 0;
    } else if (c == SLIP_ESC) {
        d->escaped = 1;
        return 0;
    }
    
    if (d->len < sizeof(d->buf)) {
        d->buf[d->len++] = c;
    } else {
        d->len = 0;
        d->escaped = 0;
        return -1;
    }
    
    return 0;
}

ssize_t slip_encode(const unsigned char *in, size_t in_len, unsigned char *out, size_t out_size)
{
    size_t out_len = 0;
    
    if (out_len + 1 > out_size) return -1;
    out[out_len++] = SLIP_END;
    
    for (size_t i = 0; i < in_len; i++) {
        unsigned char c = in[i];
        
        if (c == SLIP_END) {
            if (out_len + 2 > out_size) return -1;
            out[out_len++] = SLIP_ESC;
            out[out_len++] = SLIP_ESC_END;
        } else if (c == SLIP_ESC) {
            if (out_len + 2 > out_size) return -1;
            out[out_len++] = SLIP_ESC;
            out[out_len++] = SLIP_ESC_ESC;
        } else {
            if (out_len + 1 > out_size) return -1;
            out[out_len++] = c;
        }
    }
    
    if (out_len + 1 > out_size) return -1;
    out[out_len++] = SLIP_END;
    
    return out_len;
}

int main(int argc, char **argv)
{
    unsigned char tap_buf[MTU];
    unsigned char serial_buf[256];
    unsigned char slip_buf[MTU * 2];
    slip_decoder_t decoder;
    fd_set readfds;
    int max_fd;
    
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    printf("HaLow SLIP Bridge starting...\n");
    
    tap_fd = create_tap(TAP_NAME);
    if (tap_fd < 0) return 1;
    
    serial_fd = open_serial_custom_baud(SERIAL_DEV, SERIAL_BAUD);
    if (serial_fd < 0) {
        close(tap_fd);
        return 1;
    }
    
    slip_decoder_init(&decoder);
    max_fd = (tap_fd > serial_fd ? tap_fd : serial_fd) + 1;
    
    printf("Bridge active (TAP mode): %s <-> %s\n", TAP_NAME, SERIAL_DEV);
    printf("Configure with: sudo ip addr add 192.168.1.2/24 dev %s\n", TAP_NAME);
    printf("               sudo ip link set %s up\n", TAP_NAME);
    
    while (running) {
        FD_ZERO(&readfds);
        FD_SET(tap_fd, &readfds);
        FD_SET(serial_fd, &readfds);
        
        struct timeval tv = { .tv_sec = 1, .tv_usec = 0 };
        int ret = select(max_fd, &readfds, NULL, NULL, &tv);
        
        if (ret < 0) {
            if (errno == EINTR) continue;
            perror("select");
            break;
        }
        
        if (ret == 0) continue;
        
        if (FD_ISSET(tap_fd, &readfds)) {
            ssize_t n = read(tap_fd, tap_buf, sizeof(tap_buf));
            if (n < 0) {
                perror("read tap");
                break;
            }
            if (n > 0) {
                tx_packets++;
                tx_bytes += n;
                printf("TX: %ld bytes (total: %lu pkts, %lu bytes)\n", n, tx_packets, tx_bytes);
                ssize_t encoded = slip_encode(tap_buf, n, slip_buf, sizeof(slip_buf));
                if (encoded > 0) {
                    write(serial_fd, slip_buf, encoded);
                }
            }
        }
        
        if (FD_ISSET(serial_fd, &readfds)) {
            ssize_t n = read(serial_fd, serial_buf, sizeof(serial_buf));
            if (n < 0) {
                perror("read serial");
                break;
            }
            
            for (ssize_t i = 0; i < n; i++) {
                int pkt_len = slip_decode_byte(&decoder, serial_buf[i], tap_buf, sizeof(tap_buf));
                if (pkt_len > 0) {
                    rx_packets++;
                    rx_bytes += pkt_len;
                    printf("RX: %d bytes (total: %lu pkts, %lu bytes)\n", pkt_len, rx_packets, rx_bytes);
                    write(tap_fd, tap_buf, pkt_len);
                } else if (pkt_len < 0) {
                    slip_decoder_init(&decoder);
                }
            }
        }
    }
    
    close(tap_fd);
    close(serial_fd);
    printf("Shutdown complete\n");
    return 0;
}
