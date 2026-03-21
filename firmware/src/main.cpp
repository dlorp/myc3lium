#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "myc3_core.h"
#include "myc3_config.h"

static const char *TAG = "main";

static void state_machine_task(void *pvParameters) {
    myc3_config_t config;
    
    ESP_LOGI(TAG, "State machine task started");
    
    while (1) {
        node_state_t state = myc3_core_get_state();
        
        switch (state) {
            case NODE_STATE_BOOT:
                ESP_LOGI(TAG, "STATE: BOOT - Initializing systems");
                myc3_core_load_config(&config);
                
                if (config.uuid[0] == '\0') {
                    ESP_LOGW(TAG, "No valid UUID found, entering SETUP_MODE");
                    myc3_core_set_state(NODE_STATE_SETUP_MODE);
                } else {
                    ESP_LOGI(TAG, "UUID found: %s", config.uuid);
                    myc3_core_set_state(NODE_STATE_CONFIG);
                }
                vTaskDelay(pdMS_TO_TICKS(100));
                break;
                
            case NODE_STATE_CONFIG:
                ESP_LOGI(TAG, "STATE: CONFIG - Validating configuration");
                myc3_core_load_config(&config);
                ESP_LOGI(TAG, "Node name: %s", config.node_name);
                ESP_LOGI(TAG, "Role: %u", (unsigned int)config.role);
                ESP_LOGI(TAG, "Variant: %u", config.hw_variant);
                myc3_core_set_state(NODE_STATE_CONNECT);
                vTaskDelay(pdMS_TO_TICKS(500));
                break;
                
            case NODE_STATE_SETUP_MODE:
                ESP_LOGI(TAG, "STATE: SETUP_MODE - Waiting for configuration");
                ESP_LOGI(TAG, "WebUI would be served on AP: myc3-setup-XXXX");
                vTaskDelay(pdMS_TO_TICKS(2000));
                break;
                
            case NODE_STATE_CONNECT:
                ESP_LOGI(TAG, "STATE: CONNECT - Attempting mesh connection");
                ESP_LOGI(TAG, "Mesh SSID: %s", config.mesh_ssid);
                myc3_core_set_state(NODE_STATE_POL_DETECT);
                vTaskDelay(pdMS_TO_TICKS(1000));
                break;
                
            case NODE_STATE_POL_DETECT:
                ESP_LOGI(TAG, "STATE: POL_DETECT - Running antenna sweep");
                ESP_LOGI(TAG, "Current polarization: %s (mode: %u)", 
                    config.pol_current == POL_RHCP ? "RHCP" : 
                    config.pol_current == POL_LHCP ? "LHCP" : "UNKNOWN",
                    config.pol_mode);
                ESP_LOGI(TAG, "Sweeping RHCP (current RSSI: %d dBm)", config.rssi_rhcp);
                vTaskDelay(pdMS_TO_TICKS(200));
                ESP_LOGI(TAG, "Sweeping LHCP (current RSSI: %d dBm)", config.rssi_lhcp);
                vTaskDelay(pdMS_TO_TICKS(200));
                
                if (config.rssi_rhcp > config.rssi_lhcp) {
                    ESP_LOGI(TAG, "Selected RHCP: %d dBm > LHCP: %d dBm (delta: %d dB)", 
                        config.rssi_rhcp, config.rssi_lhcp, 
                        config.rssi_rhcp - config.rssi_lhcp);
                    config.pol_current = POL_RHCP;
                } else {
                    ESP_LOGI(TAG, "Selected LHCP: %d dBm > RHCP: %d dBm (delta: %d dB)", 
                        config.rssi_lhcp, config.rssi_rhcp, 
                        config.rssi_lhcp - config.rssi_rhcp);
                    config.pol_current = POL_LHCP;
                }
                
                ESP_LOGI(TAG, "Polarization detection complete. Active: %s", 
                    config.pol_current == POL_RHCP ? "RHCP" : "LHCP");
                ESP_LOGI(TAG, "Next recheck in %u minutes", config.pol_recheck_interval_min);
                
                myc3_core_set_state(NODE_STATE_OPERATIONAL);
                vTaskDelay(pdMS_TO_TICKS(600));
                break;
                
            case NODE_STATE_OPERATIONAL:
                ESP_LOGI(TAG, "STATE: OPERATIONAL - Running normally");
                ESP_LOGI(TAG, "Heartbeat: %u uptime seconds", (unsigned int)(xTaskGetTickCount() / 1000));
                vTaskDelay(pdMS_TO_TICKS(5000));
                break;
                
            case NODE_STATE_ERROR:
                ESP_LOGE(TAG, "STATE: ERROR - Critical failure");
                vTaskDelay(pdMS_TO_TICKS(2000));
                break;
                
            default:
                ESP_LOGW(TAG, "Unknown state: %u", (unsigned int)state);
                vTaskDelay(pdMS_TO_TICKS(1000));
                break;
        }
    }
}

extern "C" void app_main(void) {
    ESP_LOGI(TAG, "Starting myc3lium handheld firmware");
    ESP_LOGI(TAG, "Firmware version: %s", MYC3_FIRMWARE_VERSION);
    ESP_LOGI(TAG, "Variant: %s", MYC3_VARIANT_NAME);
    ESP_LOGI(TAG, "Radio: %s", MYC3_RADIO_TYPE);
    ESP_LOGI(TAG, "Build: %s %s", MYC3_BUILD_DATE, MYC3_BUILD_TIME);
    
    myc3_core_init();
    
    ESP_LOGI(TAG, "Creating state machine task");
    xTaskCreate(state_machine_task, "state_machine", 4096, NULL, 5, NULL);
}
