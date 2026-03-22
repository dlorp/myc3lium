#include "halow_driver.h"
#include "esp_log.h"
#include "driver/uart.h"
#include <ctype.h>

static const char *TAG = "halow_driver";

static bool halow_initialized = false;

static bool is_safe_ssid(const char *value) {
    if (!value || value[0] == '\0') {
        return false;
    }

    for (size_t i = 0; value[i] != '\0'; ++i) {
        const unsigned char ch = (unsigned char)value[i];
        if (!(isalnum(ch) || ch == '-' || ch == '_')) {
            return false;
        }
    }

    return true;
}

void halow_driver_init(void) {
    ESP_LOGI(TAG, "Initializing HT-HC01P HaLow driver");
    
    halow_initialized = true;
    ESP_LOGI(TAG, "HaLow driver initialized (stub)");
}

void halow_driver_deinit(void) {
    ESP_LOGI(TAG, "Deinitializing HaLow driver");
    halow_initialized = false;
}

int halow_driver_get_rssi(void) {
    if (!halow_initialized) {
        ESP_LOGW(TAG, "get_rssi: driver not initialized");
        return -100;
    }
    
    ESP_LOGD(TAG, "Reading RSSI via AT command (stub)");
    return -70;
}

bool halow_driver_start_rx(void) {
    if (!halow_initialized) {
        ESP_LOGW(TAG, "start_rx: driver not initialized");
        return false;
    }
    
    ESP_LOGI(TAG, "Starting RX mode (stub)");
    return true;
}

bool halow_driver_stop_rx(void) {
    if (!halow_initialized) {
        ESP_LOGW(TAG, "stop_rx: driver not initialized");
        return false;
    }
    
    ESP_LOGI(TAG, "Stopping RX mode (stub)");
    return true;
}

bool halow_driver_transmit(const uint8_t *data, size_t len) {
    if (!halow_initialized) {
        ESP_LOGW(TAG, "transmit: driver not initialized");
        return false;
    }
    
    if (!data || len == 0) {
        ESP_LOGE(TAG, "transmit: invalid data");
        return false;
    }

    if (len > LORA_MAX_PACKET_SIZE) {
        ESP_LOGE(TAG, "transmit: payload length %u exceeds max %u",
                 (unsigned int)len,
                 (unsigned int)LORA_MAX_PACKET_SIZE);
        return false;
    }
    
    ESP_LOGI(TAG, "Transmitting %u bytes via HaLow (stub)", (unsigned int)len);
    return true;
}

void halow_driver_set_tx_power(int8_t power_dbm) {
    if (!halow_initialized) {
        ESP_LOGW(TAG, "set_tx_power: driver not initialized");
        return;
    }
    
    ESP_LOGI(TAG, "Setting TX power to %d dBm (stub)", power_dbm);
}

int8_t halow_driver_get_tx_power(void) {
    if (!halow_initialized) {
        ESP_LOGW(TAG, "get_tx_power: driver not initialized");
        return 0;
    }
    
    return 14;
}

bool halow_driver_join_mesh(const char *ssid, const char *key) {
    if (!halow_initialized) {
        ESP_LOGW(TAG, "join_mesh: driver not initialized");
        return false;
    }
    
    if (!ssid || !key) {
        ESP_LOGE(TAG, "join_mesh: invalid credentials");
        return false;
    }

    if (!is_safe_ssid(ssid) || !is_safe_ssid(key)) {
        ESP_LOGE(TAG, "join_mesh: rejected unsafe AT command input");
        return false;
    }
    
    ESP_LOGI(TAG, "Joining HaLow mesh: %s (stub)", ssid);
    return true;
}

bool halow_driver_is_connected(void) {
    if (!halow_initialized) {
        return false;
    }
    
    return true;
}

void halow_driver_reset(void) {
    if (!halow_initialized) {
        ESP_LOGW(TAG, "reset: driver not initialized");
        return;
    }
    
    ESP_LOGI(TAG, "Resetting HaLow module (stub)");
}

const char *halow_driver_get_fw_version(void) {
    return "HT-HC01P-FW-UNKNOWN";
}
