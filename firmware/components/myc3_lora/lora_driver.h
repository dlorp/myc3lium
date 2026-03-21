#ifndef LORA_DRIVER_H
#define LORA_DRIVER_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    LORA_FREQ_915MHZ = 915000000,
    LORA_FREQ_868MHZ = 868000000,
} lora_freq_t;

typedef enum {
    LORA_BW_125K = 0,
    LORA_BW_250K = 1,
    LORA_BW_500K = 2,
} lora_bandwidth_t;

typedef struct {
    int8_t rssi_dbm;
    int8_t snr_db;
    uint8_t rssi_level;
} lora_rssi_t;

void lora_driver_init(void);
void lora_driver_deinit(void);

int lora_driver_get_rssi(void);
int lora_driver_get_snr(void);

bool lora_driver_start_rx(void);
bool lora_driver_stop_rx(void);
bool lora_driver_transmit(const uint8_t *data, size_t len);

void lora_driver_set_tx_power(int8_t power_dbm);
int8_t lora_driver_get_tx_power(void);

void lora_driver_set_frequency(lora_freq_t freq);
void lora_driver_set_bandwidth(lora_bandwidth_t bw);

bool lora_driver_join_mesh(const char *network_key);
bool lora_driver_is_connected(void);

void lora_driver_reset(void);
const char *lora_driver_get_hw_version(void);

#ifdef __cplusplus
}
#endif

#endif
