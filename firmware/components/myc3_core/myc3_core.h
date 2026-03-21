#ifndef MYC3_CORE_H
#define MYC3_CORE_H

#include <stdint.h>
#include <stdbool.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

#define UUID_MAX 37
#define NODE_NAME_MAX 32
#define SSID_MAX 32
#define MESH_KEY_MAX 64
#define WAKE_INTERVAL_MAX_SEC 3600
#define TX_POWER_MIN_DBM (-4)
#define TX_POWER_MAX_DBM 20
#define RSSI_MIN_DBM (-120)
#define RSSI_MAX_DBM 0

typedef enum {
    NODE_STATE_BOOT = 0,
    NODE_STATE_CONFIG,
    NODE_STATE_SETUP_MODE,
    NODE_STATE_CONNECT,
    NODE_STATE_POL_DETECT,
    NODE_STATE_OPERATIONAL,
    NODE_STATE_ERROR,
} node_state_t;

typedef enum {
    POL_UNKNOWN = 0,
    POL_RHCP = 1,
    POL_LHCP = 2,
} pol_state_t;

typedef enum {
    ROLE_SENSOR = 0,
    ROLE_RELAY = 1,
    ROLE_ENDPOINT = 2,
    ROLE_GATEWAY = 3,
} node_role_t;

typedef struct {
    char uuid[UUID_MAX];
    char node_name[NODE_NAME_MAX];
    node_role_t role;
    uint8_t hw_variant;
    
    pol_state_t pol_current;
    uint8_t pol_mode;
    int8_t rssi_rhcp;
    int8_t rssi_lhcp;
    uint16_t pol_recheck_interval_min;
    
    char mesh_ssid[SSID_MAX];
    char mesh_key[MESH_KEY_MAX];
    uint32_t router_ip;
    
    uint8_t sleep_enabled;
    uint16_t wake_interval_sec;
    int8_t tx_power_dbm;
    
    uint32_t last_pol_check;
    node_state_t current_state;
} myc3_config_t;

void myc3_core_init(void);
void myc3_core_load_config(myc3_config_t *config);
void myc3_core_save_config(const myc3_config_t *config);
void myc3_core_reset_config(void);
void myc3_core_set_state(node_state_t state);
node_state_t myc3_core_get_state(void);
void myc3_core_get_uuid(char *uuid_buf, size_t buf_len);
void myc3_core_set_node_name(const char *name);

#ifdef __cplusplus
}
#endif

#endif
