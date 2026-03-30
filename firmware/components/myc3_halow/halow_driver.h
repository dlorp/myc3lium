#ifndef HALOW_DRIVER_H
#define HALOW_DRIVER_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define HALOW_MAX_FRAME_SIZE 1500

typedef enum {
    HALOW_RX = 0,
    HALOW_TX = 1,
} halow_mode_t;

typedef struct {
    int8_t rssi_dbm;
    uint8_t rssi_level;
    bool packet_valid;
} halow_rssi_t;

void halow_driver_init(void);
void halow_driver_deinit(void);

int halow_driver_get_rssi(void);

bool halow_driver_start_rx(void);
bool halow_driver_stop_rx(void);
bool halow_driver_transmit(const uint8_t *data, size_t len);

void halow_driver_set_tx_power(int8_t power_dbm);
int8_t halow_driver_get_tx_power(void);

bool halow_driver_join_mesh(const char *ssid, const char *key);
bool halow_driver_is_connected(void);

void halow_driver_reset(void);
const char *halow_driver_get_fw_version(void);

#ifdef __cplusplus
}
#endif

#endif
