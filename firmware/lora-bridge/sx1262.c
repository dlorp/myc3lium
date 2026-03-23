/*
 * SX1262 LoRa Radio Driver Implementation
 * Hardware: Waveshare SX1262 HAT on Raspberry Pi 4
 */

#include "sx1262.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>
#include <gpiod.h>

/* Global GPIO and SPI handles */
static int spi_fd = -1;
static struct gpiod_chip *gpio_chip = NULL;
static struct gpiod_line *gpio_reset = NULL;
static struct gpiod_line *gpio_busy = NULL;
static struct gpiod_line *gpio_dio1 = NULL;

/* SPI Initialization */
int spi_init(void)
{
    uint8_t mode = SPI_MODE_0;
    uint8_t bits = 8;
    uint32_t speed = SPI_SPEED;

    spi_fd = open(SPI_DEVICE, O_RDWR);
    if (spi_fd < 0) {
        perror("open spi device");
        return -1;
    }

    if (ioctl(spi_fd, SPI_IOC_WR_MODE, &mode) < 0) {
        perror("SPI_IOC_WR_MODE");
        close(spi_fd);
        return -1;
    }

    if (ioctl(spi_fd, SPI_IOC_WR_BITS_PER_WORD, &bits) < 0) {
        perror("SPI_IOC_WR_BITS_PER_WORD");
        close(spi_fd);
        return -1;
    }

    if (ioctl(spi_fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed) < 0) {
        perror("SPI_IOC_WR_MAX_SPEED_HZ");
        close(spi_fd);
        return -1;
    }

    return spi_fd;
}

void spi_cleanup(void)
{
    if (spi_fd >= 0) {
        close(spi_fd);
        spi_fd = -1;
    }
}

int spi_transfer(const uint8_t *tx, uint8_t *rx, size_t len)
{
    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)tx,
        .rx_buf = (unsigned long)rx,
        .len = len,
        .speed_hz = SPI_SPEED,
        .bits_per_word = 8,
    };

    int ret = ioctl(spi_fd, SPI_IOC_MESSAGE(1), &tr);
    if (ret < 0) {
        perror("spi_transfer");
        return -1;
    }
    return 0;
}

/* GPIO Initialization using libgpiod */
int gpio_init(void)
{
    gpio_chip = gpiod_chip_open("/dev/gpiochip0");
    if (!gpio_chip) {
        perror("gpiod_chip_open");
        return -1;
    }

    /* RESET: Output, initially high */
    gpio_reset = gpiod_chip_get_line(gpio_chip, GPIO_RESET);
    if (!gpio_reset || gpiod_line_request_output(gpio_reset, "sx1262-reset", 1) < 0) {
        perror("gpio_reset request");
        return -1;
    }

    /* BUSY: Input */
    gpio_busy = gpiod_chip_get_line(gpio_chip, GPIO_BUSY);
    if (!gpio_busy || gpiod_line_request_input(gpio_busy, "sx1262-busy") < 0) {
        perror("gpio_busy request");
        return -1;
    }

    /* DIO1: Input for IRQ */
    gpio_dio1 = gpiod_chip_get_line(gpio_chip, GPIO_DIO1);
    if (!gpio_dio1 || gpiod_line_request_input(gpio_dio1, "sx1262-dio1") < 0) {
        perror("gpio_dio1 request");
        return -1;
    }

    return 0;
}

void gpio_cleanup(void)
{
    if (gpio_reset) {
        gpiod_line_release(gpio_reset);
        gpio_reset = NULL;
    }
    if (gpio_busy) {
        gpiod_line_release(gpio_busy);
        gpio_busy = NULL;
    }
    if (gpio_dio1) {
        gpiod_line_release(gpio_dio1);
        gpio_dio1 = NULL;
    }
    if (gpio_chip) {
        gpiod_chip_close(gpio_chip);
        gpio_chip = NULL;
    }
}

int gpio_read(int pin)
{
    struct gpiod_line *line = NULL;
    
    if (pin == GPIO_BUSY) line = gpio_busy;
    else if (pin == GPIO_DIO1) line = gpio_dio1;
    
    if (!line) return -1;
    return gpiod_line_get_value(line);
}

int gpio_write(int pin, int value)
{
    if (pin == GPIO_RESET && gpio_reset) {
        return gpiod_line_set_value(gpio_reset, value);
    }
    return -1;
}

int gpio_open_irq(int pin)
{
    if (pin != GPIO_DIO1 || !gpio_dio1) return -1;
    
    /* Release input request and re-request with edge events */
    gpiod_line_release(gpio_dio1);
    
    gpio_dio1 = gpiod_chip_get_line(gpio_chip, GPIO_DIO1);
    if (!gpio_dio1) {
        perror("gpio_dio1 re-request");
        return -1;
    }
    
    /* Request rising edge events */
    if (gpiod_line_request_rising_edge_events(gpio_dio1, "sx1262-irq") < 0) {
        perror("gpiod_line_request_rising_edge_events");
        return -1;
    }
    
    /* Get file descriptor for select() */
    int fd = gpiod_line_event_get_fd(gpio_dio1);
    if (fd < 0) {
        perror("gpiod_line_event_get_fd");
        return -1;
    }
    
    return fd;
}

/* SX1262 Wait on BUSY */
int sx1262_wait_on_busy(void)
{
    int timeout = 1000; // 1 second timeout
    while (gpio_read(GPIO_BUSY) == 1 && timeout-- > 0) {
        usleep(1000); // 1ms
    }
    
    if (timeout <= 0) {
        fprintf(stderr, "sx1262: BUSY timeout\n");
        return -1;
    }
    return 0;
}

/* SX1262 Command Helper */
static int sx1262_write_command(uint8_t opcode, const uint8_t *params, size_t len)
{
    /* Security: Validate size to prevent buffer overflow (HIGH-4) */
    if (len > 255) {
        fprintf(stderr, "SPI command too long: %zu > 255\n", len);
        return -1;
    }

    if (sx1262_wait_on_busy() < 0) return -1;

    uint8_t tx[256] = {opcode};
    uint8_t rx[256] = {0};
    
    if (params && len > 0) {
        memcpy(tx + 1, params, len);
    }
    
    return spi_transfer(tx, rx, len + 1);
}

static int sx1262_read_command(uint8_t opcode, uint8_t *data, size_t len)
{
    if (sx1262_wait_on_busy() < 0) return -1;

    uint8_t tx[256] = {opcode, 0x00}; // Status byte
    uint8_t rx[256] = {0};
    
    if (spi_transfer(tx, rx, len + 2) < 0) return -1;
    
    memcpy(data, rx + 2, len);
    return 0;
}

/* SX1262 Initialization */
int sx1262_init(void)
{
    if (gpio_init() < 0) {
        fprintf(stderr, "GPIO initialization failed\n");
        return -1;
    }

    if (spi_init() < 0) {
        fprintf(stderr, "SPI initialization failed\n");
        goto cleanup_gpio;
    }

    return 0;

cleanup_gpio:
    /* Cleanup GPIO if SPI initialization fails */
    gpio_cleanup();
    return -1;
}

void sx1262_cleanup(void)
{
    spi_cleanup();
    gpio_cleanup();
}

/* SX1262 Reset */
int sx1262_reset(void)
{
    printf("Resetting SX1262...\n");
    
    if (gpio_write(GPIO_RESET, 0) < 0) return -1;
    usleep(10000); // 10ms
    
    if (gpio_write(GPIO_RESET, 1) < 0) return -1;
    usleep(20000); // 20ms
    
    return sx1262_wait_on_busy();
}

/* SX1262 Configuration Commands */
int sx1262_set_standby(uint8_t mode)
{
    return sx1262_write_command(CMD_SET_STANDBY, &mode, 1);
}

int sx1262_set_packet_type(uint8_t type)
{
    return sx1262_write_command(CMD_SET_PACKET_TYPE, &type, 1);
}

int sx1262_set_rf_frequency(uint32_t freq)
{
    // Convert frequency to SX1262 register value
    // freq_reg = (freq * 2^25) / 32000000
    uint64_t freq_reg = ((uint64_t)freq << 25) / 32000000ULL;
    
    uint8_t params[4] = {
        (freq_reg >> 24) & 0xFF,
        (freq_reg >> 16) & 0xFF,
        (freq_reg >> 8) & 0xFF,
        freq_reg & 0xFF
    };
    
    return sx1262_write_command(CMD_SET_RF_FREQUENCY, params, 4);
}

int sx1262_set_modulation_params(uint8_t sf, uint8_t bw, uint8_t cr)
{
    uint8_t params[4] = {sf, bw, cr, 0x00}; // Last byte: low data rate optimize (0=off)
    return sx1262_write_command(CMD_SET_MODULATION_PARAMS, params, 4);
}

int sx1262_set_packet_params(uint16_t preamble_len, uint8_t header_type,
                             uint8_t payload_len, uint8_t crc, uint8_t invert_iq)
{
    uint8_t params[6] = {
        (preamble_len >> 8) & 0xFF,
        preamble_len & 0xFF,
        header_type,  // 0=variable, 1=fixed
        payload_len,
        crc,          // 1=on, 0=off
        invert_iq     // 0=standard, 1=inverted
    };
    
    return sx1262_write_command(CMD_SET_PACKET_PARAMS, params, 6);
}

int sx1262_set_dio_irq_params(uint16_t irq_mask, uint16_t dio1_mask,
                              uint16_t dio2_mask, uint16_t dio3_mask)
{
    uint8_t params[8] = {
        (irq_mask >> 8) & 0xFF, irq_mask & 0xFF,
        (dio1_mask >> 8) & 0xFF, dio1_mask & 0xFF,
        (dio2_mask >> 8) & 0xFF, dio2_mask & 0xFF,
        (dio3_mask >> 8) & 0xFF, dio3_mask & 0xFF
    };
    
    return sx1262_write_command(CMD_SET_DIO_IRQ_PARAMS, params, 8);
}

int sx1262_set_tx_params(int8_t power, uint8_t ramp_time)
{
    uint8_t params[2] = {(uint8_t)power, ramp_time};
    return sx1262_write_command(CMD_SET_TX_PARAMS, params, 2);
}

int sx1262_set_buffer_base_address(uint8_t tx_base, uint8_t rx_base)
{
    uint8_t params[2] = {tx_base, rx_base};
    return sx1262_write_command(CMD_SET_BUFFER_BASE_ADDRESS, params, 2);
}

int sx1262_set_rx(uint32_t timeout)
{
    // timeout: 0xFFFFFF = continuous RX
    uint8_t params[3] = {
        (timeout >> 16) & 0xFF,
        (timeout >> 8) & 0xFF,
        timeout & 0xFF
    };
    
    return sx1262_write_command(CMD_SET_RX, params, 3);
}

int sx1262_set_tx(uint32_t timeout)
{
    uint8_t params[3] = {
        (timeout >> 16) & 0xFF,
        (timeout >> 8) & 0xFF,
        timeout & 0xFF
    };
    
    return sx1262_write_command(CMD_SET_TX, params, 3);
}

uint16_t sx1262_get_irq_status(void)
{
    uint8_t status[2] = {0};
    
    if (sx1262_read_command(CMD_GET_IRQ_STATUS, status, 2) < 0) {
        return 0;
    }
    
    return (status[0] << 8) | status[1];
}

int sx1262_clear_irq_status(uint16_t irq_mask)
{
    uint8_t params[2] = {
        (irq_mask >> 8) & 0xFF,
        irq_mask & 0xFF
    };
    
    return sx1262_write_command(CMD_CLR_IRQ_STATUS, params, 2);
}

/* Complete SX1262 Configuration */
int sx1262_configure(void)
{
    printf("Configuring SX1262 for LoRa operation...\n");

    /* Step 1: Set Standby mode */
    if (sx1262_set_standby(STDBY_RC) < 0) {
        fprintf(stderr, "Failed to set standby mode\n");
        return -1;
    }

    /* Step 2: Set packet type to LoRa */
    if (sx1262_set_packet_type(PACKET_TYPE_LORA) < 0) {
        fprintf(stderr, "Failed to set packet type\n");
        return -1;
    }

    /* Step 3: Set RF frequency (915 MHz) */
    if (sx1262_set_rf_frequency(RF_FREQUENCY) < 0) {
        fprintf(stderr, "Failed to set RF frequency\n");
        return -1;
    }

    /* Step 4: Set modulation parameters (SF7, BW125, CR4/5) */
    if (sx1262_set_modulation_params(LORA_SF7, LORA_BW_125, LORA_CR_4_5) < 0) {
        fprintf(stderr, "Failed to set modulation params\n");
        return -1;
    }

    /* Step 5: Set packet parameters */
    if (sx1262_set_packet_params(8, 0, 0xFF, 1, 0) < 0) {
        fprintf(stderr, "Failed to set packet params\n");
        return -1;
    }

    /* Step 6: Set buffer base addresses */
    if (sx1262_set_buffer_base_address(0x00, 0x00) < 0) {
        fprintf(stderr, "Failed to set buffer base addresses\n");
        return -1;
    }

    /* Step 7: Configure DIO IRQ (RxDone and TxDone) */
    if (sx1262_set_dio_irq_params(IRQ_RX_DONE | IRQ_TX_DONE,
                                   IRQ_RX_DONE | IRQ_TX_DONE,
                                   0x0000, 0x0000) < 0) {
        fprintf(stderr, "Failed to set DIO IRQ params\n");
        return -1;
    }

    /* Step 8: Set TX parameters */
    if (sx1262_set_tx_params(TX_OUTPUT_POWER, 0x04) < 0) {
        fprintf(stderr, "Failed to set TX params\n");
        return -1;
    }

    printf("SX1262 configured successfully\n");
    return 0;
}

/* Transmit Data */
int sx1262_transmit(const uint8_t *data, size_t len)
{
    if (len > SX1262_MAX_PAYLOAD) {
        fprintf(stderr, "Payload too large: %zu > %d\n", len, SX1262_MAX_PAYLOAD);
        return -1;
    }

    /* Write payload to buffer */
    if (sx1262_wait_on_busy() < 0) return -1;
    
    uint8_t tx[256] = {CMD_WRITE_BUFFER, 0x00}; // Offset 0
    memcpy(tx + 2, data, len);
    
    uint8_t rx[256] = {0};
    if (spi_transfer(tx, rx, len + 2) < 0) return -1;

    /* Update packet length */
    if (sx1262_set_packet_params(8, 0, len, 1, 0) < 0) return -1;

    /* Start transmission */
    if (sx1262_set_tx(0x000000) < 0) return -1; // No timeout

    return 0;
}

/* Receive Data */
int sx1262_receive(uint8_t *data, size_t max_len, size_t *rx_len)
{
    /* Get RX buffer status */
    uint8_t status[2] = {0};
    
    if (sx1262_read_command(CMD_GET_RX_BUFFER_STATUS, status, 2) < 0) {
        return -1;
    }
    
    uint8_t payload_len = status[0];
    uint8_t rx_start_ptr = status[1];
    
    if (payload_len > max_len) {
        fprintf(stderr, "RX buffer overflow: %d > %zu\n", payload_len, max_len);
        return -1;
    }

    /* Read payload from buffer */
    if (sx1262_wait_on_busy() < 0) return -1;
    
    uint8_t tx[258] = {CMD_READ_BUFFER, rx_start_ptr, 0x00}; // Status byte
    uint8_t rx[258] = {0};
    
    if (spi_transfer(tx, rx, payload_len + 3) < 0) return -1;
    
    memcpy(data, rx + 3, payload_len);
    *rx_len = payload_len;

    return 0;
}
