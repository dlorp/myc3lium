/*
 * SX1262 LoRa Radio Driver Header
 * Waveshare SX1262 HAT for Raspberry Pi
 */

#ifndef SX1262_H
#define SX1262_H

#include <stdint.h>
#include <stddef.h>

/* GPIO Pin Definitions */
#define GPIO_RESET  18
#define GPIO_BUSY   23
#define GPIO_DIO1   24

/* SPI Configuration */
#define SPI_DEVICE  "/dev/spidev0.0"
#define SPI_SPEED   2000000  // 2 MHz

/* SX1262 Commands */
#define CMD_SET_SLEEP               0x84
#define CMD_SET_STANDBY             0x80
#define CMD_SET_FS                  0xC1
#define CMD_SET_TX                  0x83
#define CMD_SET_RX                  0x82
#define CMD_STOP_TIMER_ON_PREAMBLE  0x9F
#define CMD_SET_RX_DUTY_CYCLE       0x94
#define CMD_SET_CAD                 0xC5
#define CMD_SET_TX_CONTINUOUS_WAVE  0xD1
#define CMD_SET_TX_INFINITE_PREAMBLE 0xD2
#define CMD_SET_REGULATOR_MODE      0x96
#define CMD_CALIBRATE               0x89
#define CMD_CALIBRATE_IMAGE         0x98
#define CMD_SET_PA_CONFIG           0x95
#define CMD_SET_RX_TX_FALLBACK_MODE 0x93

/* Configuration Commands */
#define CMD_WRITE_REGISTER          0x0D
#define CMD_READ_REGISTER           0x1D
#define CMD_WRITE_BUFFER            0x0E
#define CMD_READ_BUFFER             0x1E

/* Radio Configuration */
#define CMD_SET_DIO_IRQ_PARAMS      0x08
#define CMD_GET_IRQ_STATUS          0x12
#define CMD_CLR_IRQ_STATUS          0x02
#define CMD_SET_DIO2_AS_RF_SWITCH_CTRL 0x9D
#define CMD_SET_DIO3_AS_TCXO_CTRL   0x97
#define CMD_SET_RF_FREQUENCY        0x86
#define CMD_SET_PACKET_TYPE         0x8A
#define CMD_GET_PACKET_TYPE         0x11
#define CMD_SET_TX_PARAMS           0x8E
#define CMD_SET_MODULATION_PARAMS   0x8B
#define CMD_SET_PACKET_PARAMS       0x8C
#define CMD_SET_CAD_PARAMS          0x88
#define CMD_SET_BUFFER_BASE_ADDRESS 0x8F
#define CMD_SET_LORA_SYMB_NUM_TIMEOUT 0xA0

/* Status Commands */
#define CMD_GET_STATUS              0xC0
#define CMD_GET_RX_BUFFER_STATUS    0x13
#define CMD_GET_PACKET_STATUS       0x14
#define CMD_GET_RSSI_INST           0x15
#define CMD_GET_STATS               0x10
#define CMD_RESET_STATS             0x00

/* Standby Modes */
#define STDBY_RC    0x00
#define STDBY_XOSC  0x01

/* Packet Types */
#define PACKET_TYPE_GFSK  0x00
#define PACKET_TYPE_LORA  0x01

/* LoRa Spreading Factors */
#define LORA_SF5   0x05
#define LORA_SF6   0x06
#define LORA_SF7   0x07
#define LORA_SF8   0x08
#define LORA_SF9   0x09
#define LORA_SF10  0x0A
#define LORA_SF11  0x0B
#define LORA_SF12  0x0C

/* LoRa Bandwidths */
#define LORA_BW_7_81   0x00
#define LORA_BW_10_42  0x08
#define LORA_BW_15_63  0x01
#define LORA_BW_20_83  0x09
#define LORA_BW_31_25  0x02
#define LORA_BW_41_67  0x0A
#define LORA_BW_62_5   0x03
#define LORA_BW_125    0x04
#define LORA_BW_250    0x05
#define LORA_BW_500    0x06

/* LoRa Coding Rates */
#define LORA_CR_4_5  0x01
#define LORA_CR_4_6  0x02
#define LORA_CR_4_7  0x03
#define LORA_CR_4_8  0x04

/* IRQ Masks */
#define IRQ_TX_DONE                 0x0001
#define IRQ_RX_DONE                 0x0002
#define IRQ_PREAMBLE_DETECTED       0x0004
#define IRQ_SYNC_WORD_VALID         0x0008
#define IRQ_HEADER_VALID            0x0010
#define IRQ_HEADER_ERROR            0x0020
#define IRQ_CRC_ERROR               0x0040
#define IRQ_CAD_DONE                0x0080
#define IRQ_CAD_DETECTED            0x0100
#define IRQ_TIMEOUT                 0x0200
#define IRQ_ALL                     0x03FF

/* Maximum Payload Size - reduced to 254 to prevent buffer overflow (HIGH-5) */
#define SX1262_MAX_PAYLOAD  254

/* RF Frequency (915 MHz ISM band) */
#define RF_FREQUENCY  915000000UL

/* TX Power (dBm) */
#define TX_OUTPUT_POWER  14

/* Function Prototypes */
int sx1262_init(void);
void sx1262_cleanup(void);
int sx1262_reset(void);
int sx1262_configure(void);
int sx1262_set_standby(uint8_t mode);
int sx1262_set_packet_type(uint8_t type);
int sx1262_set_rf_frequency(uint32_t freq);
int sx1262_set_modulation_params(uint8_t sf, uint8_t bw, uint8_t cr);
int sx1262_set_packet_params(uint16_t preamble_len, uint8_t header_type,
                             uint8_t payload_len, uint8_t crc, uint8_t invert_iq);
int sx1262_set_dio_irq_params(uint16_t irq_mask, uint16_t dio1_mask,
                              uint16_t dio2_mask, uint16_t dio3_mask);
int sx1262_set_tx_params(int8_t power, uint8_t ramp_time);
int sx1262_set_buffer_base_address(uint8_t tx_base, uint8_t rx_base);
int sx1262_set_rx(uint32_t timeout);
int sx1262_set_tx(uint32_t timeout);
int sx1262_transmit(const uint8_t *data, size_t len);
int sx1262_receive(uint8_t *data, size_t max_len, size_t *rx_len);
uint16_t sx1262_get_irq_status(void);
int sx1262_clear_irq_status(uint16_t irq_mask);
int sx1262_wait_on_busy(void);

/* GPIO Functions */
int gpio_init(void);
void gpio_cleanup(void);
int gpio_read(int pin);
int gpio_write(int pin, int value);
int gpio_open_irq(int pin);

/* SPI Functions */
int spi_init(void);
void spi_cleanup(void);
int spi_transfer(const uint8_t *tx, uint8_t *rx, size_t len);

#endif /* SX1262_H */
