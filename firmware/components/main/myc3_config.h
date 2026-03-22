#ifndef MYATTRIBUTE3_CONFIG_H
#define MYATTRIBUTE3_CONFIG_H

#define MYC3_FIRMWARE_VERSION "0.1.0"
#define MYC3_BUILD_DATE __DATE__
#define MYC3_BUILD_TIME __TIME__

#define POL_SAMPLES 10
#define POL_SWEEP_MS 100
#define POL_MARGIN_DB 3
#define POL_RECHECK_MIN 30

#define NVS_NODE_UUID "node_uuid"
#define NVS_NODE_NAME "node_name"
#define NVS_NODE_ROLE "node_role"
#define NVS_VARIANT "hw_variant"

#define NVS_POL_MODE "pol_mode"
#define NVS_POL_CURRENT "pol_current"
#define NVS_POL_INTERVAL "pol_interval"

#define NVS_MESH_SSID "mesh_ssid"
#define NVS_MESH_KEY "mesh_key"
#define NVS_ROUTER_IP "router_ip"

#define NVS_SLEEP_ENABLED "sleep_enabled"
#define NVS_WAKE_INTERVAL "wake_interval"
#define NVS_TX_POWER "tx_power"

#define NVS_RSSI_RHCP "rssi_rhcp"
#define NVS_RSSI_LHCP "rssi_lhcp"
#define NVS_LAST_POL_CHECK "last_pol_check"

#define DEFAULT_MESH_SSID "myc3-mesh"
#define DEFAULT_NODE_NAME "myc3-node"
#define DEFAULT_SLEEP_MODE 1
#define DEFAULT_WAKE_INTERVAL_SEC 60
#define DEFAULT_TX_POWER_DBM 14
#define DEFAULT_POL_RECHECK_MIN 30

#ifdef MYC3_VARIANT_HALOW
#define MYC3_VARIANT_NAME "halow"
#define MYC3_RADIO_TYPE "HT-HC01P"
#define GPIO_ANT_SW_CTRL 14
#define GPIO_ANT_SW_VDD 15
#endif

#ifdef MYC3_VARIANT_LORA
#define MYC3_VARIANT_NAME "lora"
#define MYC3_RADIO_TYPE "SX1262"
#define GPIO_ANT_SW_CTRL 2
#define GPIO_ANT_SW_VDD 3
#define GPIO_OLED_SDA 21
#define GPIO_OLED_SCL 22
#endif

#endif
