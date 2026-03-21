#include "myc3_core.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_log.h"
#include <string.h>
#include <stdio.h>

static const char *TAG = "myc3_core";
static node_state_t current_state = NODE_STATE_BOOT;
static myc3_config_t cached_config = {0};

void myc3_core_init(void) {
    ESP_LOGI(TAG, "Initializing myc3 core");
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_LOGW(TAG, "NVS flash needs erasing, formatting...");
        nvs_flash_erase();
        nvs_flash_init();
    }
    
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "NVS init failed: %s", esp_err_to_name(ret));
        current_state = NODE_STATE_ERROR;
        return;
    }
    
    current_state = NODE_STATE_BOOT;
    ESP_LOGI(TAG, "Core initialized");
}

void myc3_core_load_config(myc3_config_t *config) {
    if (!config) {
        ESP_LOGE(TAG, "load_config: null config pointer");
        return;
    }
    
    nvs_handle_t nvs_handle;
    esp_err_t ret = nvs_open("myc3", NVS_READONLY, &nvs_handle);
    
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "NVS namespace 'myc3' not found, using defaults");
        memset(config, 0, sizeof(myc3_config_t));
        strcpy(config->mesh_ssid, "myc3-mesh");
        strcpy(config->node_name, "myc3-node");
        config->role = ROLE_SENSOR;
        config->pol_mode = 0;
        config->sleep_enabled = 1;
        config->wake_interval_sec = 60;
        config->tx_power_dbm = 14;
        return;
    }
    
    memset(config, 0, sizeof(myc3_config_t));
    
    size_t required_size = sizeof(config->uuid);
    nvs_get_str(nvs_handle, "node_uuid", config->uuid, &required_size);
    
    required_size = sizeof(config->node_name);
    nvs_get_str(nvs_handle, "node_name", config->node_name, &required_size);
    
    uint8_t role_val = 0;
    nvs_get_u8(nvs_handle, "node_role", &role_val);
    config->role = (node_role_t)role_val;
    
    nvs_get_u8(nvs_handle, "hw_variant", &config->hw_variant);
    
    uint8_t pol_val = 0;
    nvs_get_u8(nvs_handle, "pol_mode", &pol_val);
    config->pol_mode = pol_val;
    
    uint8_t pol_current_val = 0;
    nvs_get_u8(nvs_handle, "pol_current", &pol_current_val);
    config->pol_current = (pol_state_t)pol_current_val;
    
    nvs_get_i8(nvs_handle, "rssi_rhcp", &config->rssi_rhcp);
    nvs_get_i8(nvs_handle, "rssi_lhcp", &config->rssi_lhcp);
    nvs_get_u16(nvs_handle, "pol_interval", &config->pol_recheck_interval_min);
    
    required_size = sizeof(config->mesh_ssid);
    nvs_get_str(nvs_handle, "mesh_ssid", config->mesh_ssid, &required_size);
    
    required_size = sizeof(config->mesh_key);
    nvs_get_str(nvs_handle, "mesh_key", config->mesh_key, &required_size);
    
    nvs_get_u32(nvs_handle, "router_ip", &config->router_ip);
    
    uint8_t sleep_val = 0;
    nvs_get_u8(nvs_handle, "sleep_enabled", &sleep_val);
    config->sleep_enabled = sleep_val;
    
    nvs_get_u16(nvs_handle, "wake_interval", &config->wake_interval_sec);
    nvs_get_i8(nvs_handle, "tx_power", &config->tx_power_dbm);
    
    nvs_get_u32(nvs_handle, "last_pol_check", &config->last_pol_check);
    
    nvs_close(nvs_handle);
    
    memcpy(&cached_config, config, sizeof(myc3_config_t));
    ESP_LOGI(TAG, "Config loaded for node: %s", config->node_name);
}

void myc3_core_save_config(const myc3_config_t *config) {
    if (!config) {
        ESP_LOGE(TAG, "save_config: null config pointer");
        return;
    }
    
    nvs_handle_t nvs_handle;
    esp_err_t ret = nvs_open("myc3", NVS_READWRITE, &nvs_handle);
    
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to open NVS handle: %s", esp_err_to_name(ret));
        return;
    }
    
    nvs_set_str(nvs_handle, "node_uuid", config->uuid);
    nvs_set_str(nvs_handle, "node_name", config->node_name);
    nvs_set_u8(nvs_handle, "node_role", (uint8_t)config->role);
    nvs_set_u8(nvs_handle, "hw_variant", config->hw_variant);
    
    nvs_set_u8(nvs_handle, "pol_mode", config->pol_mode);
    nvs_set_u8(nvs_handle, "pol_current", (uint8_t)config->pol_current);
    nvs_set_i8(nvs_handle, "rssi_rhcp", config->rssi_rhcp);
    nvs_set_i8(nvs_handle, "rssi_lhcp", config->rssi_lhcp);
    nvs_set_u16(nvs_handle, "pol_interval", config->pol_recheck_interval_min);
    
    nvs_set_str(nvs_handle, "mesh_ssid", config->mesh_ssid);
    nvs_set_str(nvs_handle, "mesh_key", config->mesh_key);
    nvs_set_u32(nvs_handle, "router_ip", config->router_ip);
    
    nvs_set_u8(nvs_handle, "sleep_enabled", config->sleep_enabled);
    nvs_set_u16(nvs_handle, "wake_interval", config->wake_interval_sec);
    nvs_set_i8(nvs_handle, "tx_power", config->tx_power_dbm);
    
    nvs_set_u32(nvs_handle, "last_pol_check", config->last_pol_check);
    
    nvs_commit(nvs_handle);
    nvs_close(nvs_handle);
    
    memcpy(&cached_config, config, sizeof(myc3_config_t));
    ESP_LOGI(TAG, "Config saved successfully");
}

void myc3_core_reset_config(void) {
    ESP_LOGW(TAG, "Resetting configuration to defaults");
    nvs_handle_t nvs_handle;
    
    if (nvs_open("myc3", NVS_READWRITE, &nvs_handle) == ESP_OK) {
        nvs_erase_all(nvs_handle);
        nvs_commit(nvs_handle);
        nvs_close(nvs_handle);
    }
    
    memset(&cached_config, 0, sizeof(myc3_config_t));
    strcpy(cached_config.mesh_ssid, "myc3-mesh");
    strcpy(cached_config.node_name, "myc3-node");
}

void myc3_core_set_state(node_state_t state) {
    current_state = state;
    ESP_LOGI(TAG, "State changed to: %u", (unsigned int)state);
}

node_state_t myc3_core_get_state(void) {
    return current_state;
}

void myc3_core_get_uuid(char *uuid_buf, size_t buf_len) {
    if (uuid_buf && buf_len > 0) {
        strncpy(uuid_buf, cached_config.uuid, buf_len - 1);
        uuid_buf[buf_len - 1] = '\0';
    }
}

void myc3_core_set_node_name(const char *name) {
    if (name) {
        strncpy(cached_config.node_name, name, sizeof(cached_config.node_name) - 1);
        cached_config.node_name[sizeof(cached_config.node_name) - 1] = '\0';
    }
}
