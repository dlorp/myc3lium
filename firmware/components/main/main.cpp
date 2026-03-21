#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "myc3_core.h"
#include "myc3_config.h"

static const char *TAG = "main";
static const TickType_t STATE_WATCHDOG_TIMEOUT_TICKS = pdMS_TO_TICKS(60000);

typedef struct {
    uint32_t retry_count;
    TickType_t last_transition_time;
    node_state_t last_state;
} state_context_t;

static void transition_state(state_context_t *context, node_state_t next_state) {
    if (context) {
        context->last_state = next_state;
        context->last_transition_time = xTaskGetTickCount();
    }
    myc3_core_set_state(next_state);
}

static bool state_timed_out(state_context_t *context, node_state_t state) {
    if (!context) {
        return false;
    }

    if (context->last_state != state) {
        context->last_state = state;
        context->last_transition_time = xTaskGetTickCount();
        return false;
    }

    return (xTaskGetTickCount() - context->last_transition_time) >=
           STATE_WATCHDOG_TIMEOUT_TICKS;
}

static void state_machine_task(void *pvParameters) {
    myc3_config_t config;
    state_context_t state_context = {
        .retry_count = 0,
        .last_transition_time = xTaskGetTickCount(),
        .last_state = NODE_STATE_BOOT,
    };
    
    ESP_LOGI(TAG, "State machine task started");
    
    while (1) {
        node_state_t state = myc3_core_get_state();
        
        switch (state) {
            case NODE_STATE_BOOT:
                ESP_LOGI(TAG, "STATE: BOOT - Initializing systems");
                myc3_core_load_config(&config);
                
                if (config.uuid[0] == '\0' || config.mesh_key[0] == '\0') {
                    ESP_LOGW(TAG, "Missing required secure config, entering SETUP_MODE");
                    transition_state(&state_context, NODE_STATE_SETUP_MODE);
                } else {
                    ESP_LOGI(TAG, "UUID found: %s", config.uuid);
                    transition_state(&state_context, NODE_STATE_CONFIG);
                }
                vTaskDelay(pdMS_TO_TICKS(100));
                break;
                
            case NODE_STATE_CONFIG:
                ESP_LOGI(TAG, "STATE: CONFIG - Validating configuration");
                myc3_core_load_config(&config);
                ESP_LOGI(TAG, "Node name: %s", config.node_name);
                ESP_LOGI(TAG, "Role: %u", (unsigned int)config.role);
                ESP_LOGI(TAG, "Variant: %u", config.hw_variant);
                if (config.mesh_key[0] == '\0') {
                    ESP_LOGW(TAG, "Mesh key missing after validation, entering SETUP_MODE");
                    transition_state(&state_context, NODE_STATE_SETUP_MODE);
                } else {
                    transition_state(&state_context, NODE_STATE_CONNECT);
                }
                vTaskDelay(pdMS_TO_TICKS(500));
                break;
                
            case NODE_STATE_SETUP_MODE:
                ESP_LOGI(TAG, "STATE: SETUP_MODE - Waiting for configuration");
                ESP_LOGI(TAG, "WebUI would be served on AP: myc3-setup-XXXX");
                if (state_timed_out(&state_context, state)) {
                    state_context.retry_count++;
                    ESP_LOGE(TAG,
                             "SETUP_MODE watchdog expired after 60s, forcing safe state (attempt %u)",
                             (unsigned int)state_context.retry_count);
                    transition_state(&state_context, NODE_STATE_ERROR);
                }
                vTaskDelay(pdMS_TO_TICKS(2000));
                break;
                
            case NODE_STATE_CONNECT:
                ESP_LOGI(TAG, "STATE: CONNECT - Attempting mesh connection");
                ESP_LOGI(TAG, "Mesh SSID: %s", config.mesh_ssid);
                if (state_timed_out(&state_context, state)) {
                    state_context.retry_count++;
                    ESP_LOGE(TAG,
                             "CONNECT watchdog expired after 60s, forcing safe state (attempt %u)",
                             (unsigned int)state_context.retry_count);
                    transition_state(&state_context, NODE_STATE_ERROR);
                } else {
                    transition_state(&state_context, NODE_STATE_POL_DETECT);
                }
                vTaskDelay(pdMS_TO_TICKS(1000));
                break;
                
            case NODE_STATE_POL_DETECT:
                ESP_LOGI(TAG, "STATE: POL_DETECT - Running antenna sweep");
                ESP_LOGI(TAG, "Sweeping RHCP/LHCP for best signal");
                transition_state(&state_context, NODE_STATE_OPERATIONAL);
                vTaskDelay(pdMS_TO_TICKS(1000));
                break;
                
            case NODE_STATE_OPERATIONAL:
                ESP_LOGI(TAG, "STATE: OPERATIONAL - Running normally");
                ESP_LOGI(TAG, "Heartbeat: %u uptime seconds", (unsigned int)(xTaskGetTickCount() / 1000));
                state_context.last_transition_time = xTaskGetTickCount();
                vTaskDelay(pdMS_TO_TICKS(5000));
                break;
                
            case NODE_STATE_ERROR:
                ESP_LOGE(TAG, "STATE: ERROR - Critical failure");
                state_context.last_transition_time = xTaskGetTickCount();
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
