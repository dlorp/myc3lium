#include "myc3_core.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_mac.h"
#include "esp_log.h"
#include <string.h>
#include <stdio.h>
#include <ctype.h>

static const char *TAG = "myc3_core";
static node_state_t current_state = NODE_STATE_BOOT;
static myc3_config_t cached_config = {0};

static void copy_bounded_string(char *dest, size_t dest_size, const char *src) {
    if (!dest || dest_size == 0) {
        return;
    }

    if (!src) {
        dest[0] = '\0';
        return;
    }

    strncpy(dest, src, dest_size - 1);
    dest[dest_size - 1] = '\0';
}

static bool load_nvs_string(nvs_handle_t nvs_handle,
                            const char *key,
                            char *dest,
                            size_t dest_size) {
    if (!dest || dest_size == 0) {
        return false;
    }

    size_t required_size = 0;
    esp_err_t ret = nvs_get_str(nvs_handle, key, NULL, &required_size);
    if (ret == ESP_ERR_NVS_NOT_FOUND) {
        dest[0] = '\0';
        return false;
    }

    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Failed to get size for %s: %s", key, esp_err_to_name(ret));
        dest[0] = '\0';
        return false;
    }

    if (required_size == 0 || required_size > dest_size) {
        ESP_LOGW(TAG, "NVS value for %s exceeds buffer (%u > %u)",
                 key,
                 (unsigned int)required_size,
                 (unsigned int)dest_size);
        dest[0] = '\0';
        return false;
    }

    ret = nvs_get_str(nvs_handle, key, dest, &required_size);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Failed to load %s: %s", key, esp_err_to_name(ret));
        dest[0] = '\0';
        return false;
    }

    dest[dest_size - 1] = '\0';
    return true;
}

static bool is_valid_uuid_format(const char *uuid) {
    static const int hyphen_positions[] = {8, 13, 18, 23};

    if (!uuid || strlen(uuid) != UUID_MAX - 1) {
        return false;
    }

    for (size_t i = 0; i < UUID_MAX - 1; ++i) {
        bool is_hyphen = false;
        for (size_t j = 0; j < sizeof(hyphen_positions) / sizeof(hyphen_positions[0]); ++j) {
            if ((int)i == hyphen_positions[j]) {
                is_hyphen = true;
                break;
            }
        }

        if (is_hyphen) {
            if (uuid[i] != '-') {
                return false;
            }
            continue;
        }

        if (!isxdigit((unsigned char)uuid[i])) {
            return false;
        }
    }

    return true;
}

static void generate_default_mesh_ssid(char *ssid, size_t ssid_size) {
    uint8_t mac[6] = {0};
    esp_err_t ret = esp_read_mac(mac, ESP_MAC_WIFI_STA);

    if (ret == ESP_OK) {
        snprintf(ssid,
                 ssid_size,
                 "myc3-%02X%02X%02X",
                 mac[3],
                 mac[4],
                 mac[5]);
        ssid[ssid_size - 1] = '\0';
        return;
    }

    ESP_LOGW(TAG, "Failed to read MAC for SSID generation: %s", esp_err_to_name(ret));
    copy_bounded_string(ssid, ssid_size, "myc3-mesh");
}

static void set_default_config(myc3_config_t *config) {
    memset(config, 0, sizeof(*config));
    generate_default_mesh_ssid(config->mesh_ssid, sizeof(config->mesh_ssid));
    copy_bounded_string(config->node_name, sizeof(config->node_name), "myc3-node");
    config->role = ROLE_SENSOR;
    config->pol_mode = 0;
    config->sleep_enabled = 1;
    config->wake_interval_sec = 60;
    config->tx_power_dbm = 14;
    config->rssi_rhcp = -100;
    config->rssi_lhcp = -100;
}

static void validate_config(myc3_config_t *config) {
    if (!is_valid_uuid_format(config->uuid)) {
        if (config->uuid[0] != '\0') {
            ESP_LOGW(TAG, "Invalid UUID format in config, clearing");
        }
        config->uuid[0] = '\0';
    }

    if ((int)config->role < ROLE_SENSOR || (int)config->role > ROLE_GATEWAY) {
        ESP_LOGW(TAG, "Invalid role %u, defaulting to sensor", (unsigned int)config->role);
        config->role = ROLE_SENSOR;
    }

    if (config->tx_power_dbm < TX_POWER_MIN_DBM || config->tx_power_dbm > TX_POWER_MAX_DBM) {
        ESP_LOGW(TAG, "Invalid TX power %d dBm, defaulting to 14", config->tx_power_dbm);
        config->tx_power_dbm = 14;
    }

    if (config->rssi_rhcp < RSSI_MIN_DBM || config->rssi_rhcp > RSSI_MAX_DBM) {
        ESP_LOGW(TAG, "Invalid RHCP RSSI %d, resetting", config->rssi_rhcp);
        config->rssi_rhcp = -100;
    }

    if (config->rssi_lhcp < RSSI_MIN_DBM || config->rssi_lhcp > RSSI_MAX_DBM) {
        ESP_LOGW(TAG, "Invalid LHCP RSSI %d, resetting", config->rssi_lhcp);
        config->rssi_lhcp = -100;
    }

    if (config->wake_interval_sec == 0 || config->wake_interval_sec > WAKE_INTERVAL_MAX_SEC) {
        ESP_LOGW(TAG, "Invalid wake interval %u sec, defaulting to 60",
                 (unsigned int)config->wake_interval_sec);
        config->wake_interval_sec = 60;
    }

    if (config->mesh_ssid[0] == '\0') {
        generate_default_mesh_ssid(config->mesh_ssid, sizeof(config->mesh_ssid));
    }

    if (config->node_name[0] == '\0') {
        copy_bounded_string(config->node_name, sizeof(config->node_name), "myc3-node");
    }

    if (config->mesh_key[0] == '\0') {
        ESP_LOGW(TAG, "Mesh key is empty, forcing setup mode");
        current_state = NODE_STATE_SETUP_MODE;
    }
}

void myc3_core_init(void) {
    ESP_LOGI(TAG, "Initializing myc3 core");
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_LOGW(TAG, "NVS flash needs erasing, formatting...");
        esp_err_t erase_ret = nvs_flash_erase();
        if (erase_ret != ESP_OK) {
            ESP_LOGE(TAG, "NVS erase failed: %s", esp_err_to_name(erase_ret));
            current_state = NODE_STATE_ERROR;
            return;
        }
        ret = nvs_flash_init();
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
        set_default_config(config);
        current_state = NODE_STATE_SETUP_MODE;
        return;
    }
    
    set_default_config(config);
    load_nvs_string(nvs_handle, "node_uuid", config->uuid, sizeof(config->uuid));
    load_nvs_string(nvs_handle, "node_name", config->node_name, sizeof(config->node_name));
    
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
    
    load_nvs_string(nvs_handle, "mesh_ssid", config->mesh_ssid, sizeof(config->mesh_ssid));
    load_nvs_string(nvs_handle, "mesh_key", config->mesh_key, sizeof(config->mesh_key));
    
    nvs_get_u32(nvs_handle, "router_ip", &config->router_ip);
    
    uint8_t sleep_val = 0;
    nvs_get_u8(nvs_handle, "sleep_enabled", &sleep_val);
    config->sleep_enabled = sleep_val;
    
    nvs_get_u16(nvs_handle, "wake_interval", &config->wake_interval_sec);
    nvs_get_i8(nvs_handle, "tx_power", &config->tx_power_dbm);
    
    nvs_get_u32(nvs_handle, "last_pol_check", &config->last_pol_check);
    
    nvs_close(nvs_handle);
    validate_config(config);
    
    memcpy(&cached_config, config, sizeof(myc3_config_t));
    ESP_LOGI(TAG, "Config loaded for node: %s", config->node_name);
}

void myc3_core_save_config(const myc3_config_t *config) {
    if (!config) {
        ESP_LOGE(TAG, "save_config: null config pointer");
        return;
    }

    myc3_config_t safe_config = {0};
    copy_bounded_string(safe_config.uuid, sizeof(safe_config.uuid), config->uuid);
    copy_bounded_string(safe_config.node_name, sizeof(safe_config.node_name), config->node_name);
    safe_config.role = config->role;
    safe_config.hw_variant = config->hw_variant;
    safe_config.pol_current = config->pol_current;
    safe_config.pol_mode = config->pol_mode;
    safe_config.rssi_rhcp = config->rssi_rhcp;
    safe_config.rssi_lhcp = config->rssi_lhcp;
    safe_config.pol_recheck_interval_min = config->pol_recheck_interval_min;
    copy_bounded_string(safe_config.mesh_ssid, sizeof(safe_config.mesh_ssid), config->mesh_ssid);
    copy_bounded_string(safe_config.mesh_key, sizeof(safe_config.mesh_key), config->mesh_key);
    safe_config.router_ip = config->router_ip;
    safe_config.sleep_enabled = config->sleep_enabled;
    safe_config.wake_interval_sec = config->wake_interval_sec;
    safe_config.tx_power_dbm = config->tx_power_dbm;
    safe_config.last_pol_check = config->last_pol_check;
    safe_config.current_state = config->current_state;
    validate_config(&safe_config);
    
    nvs_handle_t nvs_handle;
    esp_err_t ret = nvs_open("myc3", NVS_READWRITE, &nvs_handle);
    
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to open NVS handle: %s", esp_err_to_name(ret));
        return;
    }
    
    nvs_set_str(nvs_handle, "node_uuid", safe_config.uuid);
    nvs_set_str(nvs_handle, "node_name", safe_config.node_name);
    nvs_set_u8(nvs_handle, "node_role", (uint8_t)safe_config.role);
    nvs_set_u8(nvs_handle, "hw_variant", safe_config.hw_variant);
    
    nvs_set_u8(nvs_handle, "pol_mode", safe_config.pol_mode);
    nvs_set_u8(nvs_handle, "pol_current", (uint8_t)safe_config.pol_current);
    nvs_set_i8(nvs_handle, "rssi_rhcp", safe_config.rssi_rhcp);
    nvs_set_i8(nvs_handle, "rssi_lhcp", safe_config.rssi_lhcp);
    nvs_set_u16(nvs_handle, "pol_interval", safe_config.pol_recheck_interval_min);
    
    nvs_set_str(nvs_handle, "mesh_ssid", safe_config.mesh_ssid);
    nvs_set_str(nvs_handle, "mesh_key", safe_config.mesh_key);
    nvs_set_u32(nvs_handle, "router_ip", safe_config.router_ip);
    
    nvs_set_u8(nvs_handle, "sleep_enabled", safe_config.sleep_enabled);
    nvs_set_u16(nvs_handle, "wake_interval", safe_config.wake_interval_sec);
    nvs_set_i8(nvs_handle, "tx_power", safe_config.tx_power_dbm);
    
    nvs_set_u32(nvs_handle, "last_pol_check", safe_config.last_pol_check);
    
    nvs_commit(nvs_handle);
    nvs_close(nvs_handle);
    
    memcpy(&cached_config, &safe_config, sizeof(myc3_config_t));
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
    generate_default_mesh_ssid(cached_config.mesh_ssid, sizeof(cached_config.mesh_ssid));
    copy_bounded_string(cached_config.node_name, sizeof(cached_config.node_name), "myc3-node");
    current_state = NODE_STATE_SETUP_MODE;
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
