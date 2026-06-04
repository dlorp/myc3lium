/**
 * MYC3LIUM Unified ESP32-S3-CAM Firmware
 *
 * Dual-core architecture:
 *   Core 0 (PRO_CPU): Arduino loop, camera, MJPEG HTTP server, heartbeat
 *   Core 1 (APP_CPU): SLIP serial bridge task (dedicated, high priority)
 *
 * The ESP32 acts as a SLIP endpoint at 192.168.1.1. The Pi runs
 * pi-slip-daemon which creates a TAP interface (halow0) at 192.168.1.2.
 * Ethernet frames are exchanged over USB serial at 921600 baud.
 *
 * TAP framing: The Pi side uses a TAP device (layer 2), so SLIP frames
 * contain full Ethernet frames (14-byte header + IP payload). On RX we
 * strip the Ethernet header before injecting into lwIP. On TX we prepend
 * a synthetic Ethernet header before SLIP-encoding.
 *
 * The camera captures QVGA JPEG frames and serves them as MJPEG over
 * HTTP on port 8080. The Pi backend can reach this at
 * http://192.168.1.1:8080/stream over the SLIP link.
 *
 * Hardware: Heltec ESP32-S3-CAM (OV3660, 8MB PSRAM)
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <atomic>
#include "esp_camera.h"
#include "esp_http_server.h"
#include "esp_netif.h"
#include "esp_heap_caps.h"
#include "lwip/ip_addr.h"
#include "lwip/netif.h"
#include "lwip/pbuf.h"
#include "lwip/tcpip.h"

#include "slip.h"

/* ------------------------------------------------------------------ */
/*  Pin definitions — Heltec ESP32-S3-CAM                             */
/* ------------------------------------------------------------------ */

#define PWDN_GPIO_NUM     -1
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     10
#define SIOD_GPIO_NUM     40
#define SIOC_GPIO_NUM     39
#define Y9_GPIO_NUM       48
#define Y8_GPIO_NUM       11
#define Y7_GPIO_NUM       12
#define Y6_GPIO_NUM       14
#define Y5_GPIO_NUM       16
#define Y4_GPIO_NUM       18
#define Y3_GPIO_NUM       17
#define Y2_GPIO_NUM       15
#define VSYNC_GPIO_NUM    38
#define HREF_GPIO_NUM     47
#define PCLK_GPIO_NUM     13

/* ------------------------------------------------------------------ */
/*  Build-time configuration (overridable via platformio.ini)         */
/* ------------------------------------------------------------------ */

#ifndef SLIP_BAUD
#define SLIP_BAUD 921600
#endif

#ifndef SLIP_MTU
#define SLIP_MTU 1560
#endif

#ifndef CAM_FPS
#define CAM_FPS 2
#endif
#if CAM_FPS < 1
#error "CAM_FPS must be >= 1"
#endif

#ifndef CAM_QUALITY
#define CAM_QUALITY 15
#endif

#ifndef CAM_PORT
#define CAM_PORT 8080
#endif

#ifndef ESP_IP
#define ESP_IP "192.168.1.1"
#endif

#ifndef PI_IP
#define PI_IP "192.168.1.2"
#endif

#ifndef PI_PORT
#define PI_PORT 8000
#endif

/* Ethernet header size (dest MAC + src MAC + EtherType) */
#undef ETH_HEADER_LEN  /* Avoid conflict with esp_eth_com.h */
#define ETH_HEADER_LEN 14
#define ETH_TYPE_IPV4  0x0800

/* Node identification — derived from MAC address at runtime */
static char node_id[24] = "m3l_cam_xx";

/* Heartbeat interval (ms) */
static const unsigned long HEARTBEAT_INTERVAL_MS = 10000;

/* Frame interval derived from FPS */
static const unsigned long FRAME_INTERVAL_MS = 1000 / CAM_FPS;

/* ------------------------------------------------------------------ */
/*  Global state — atomic counters for cross-core safety              */
/* ------------------------------------------------------------------ */

static bool camera_ok = false;
static httpd_handle_t stream_httpd = nullptr;
static unsigned long last_heartbeat = 0;
static std::atomic<uint32_t> frame_count{0};
static std::atomic<uint32_t> slip_tx_packets{0};
static std::atomic<uint32_t> slip_rx_packets{0};
static std::atomic<uint32_t> slip_rx_errors{0};
static int heartbeat_failures = 0;

/* The Heltec ESP32-S3-CAM has a CP2102 USB-UART on UART0.
 * There is only ONE physical serial connection to the Pi.
 * SLIP and debug share this UART — debug logging is disabled
 * to avoid corrupting the SLIP stream.
 * To enable debug output (breaks SLIP!), compile with -DDEBUG_SERIAL. */
#define SLIP_SERIAL Serial

#ifdef DEBUG_SERIAL
#define DBG_PRINT(...)    Serial.print(__VA_ARGS__)
#define DBG_PRINTLN(...)  Serial.println(__VA_ARGS__)
#define DBG_PRINTF(...)   Serial.printf(__VA_ARGS__)
#else
#define DBG_PRINT(...)    ((void)0)
#define DBG_PRINTLN(...)  ((void)0)
#define DBG_PRINTF(...)   ((void)0)
#endif

/* SLIP decoder state (used only by Core 1 task) */
static SlipDecoder slip_rx;

/* lwIP netif for SLIP — packets decoded on Core 1 get injected here */
static struct netif slip_netif;
static bool slip_netif_up = false;

/* Synthetic MAC addresses for Ethernet framing (TAP compatibility) */
static const uint8_t ESP_MAC[6]  = {0x02, 0x00, 0xC0, 0xA8, 0x01, 0x01};  /* 192.168.1.1 */
static const uint8_t PI_MAC[6]   = {0x02, 0x00, 0xC0, 0xA8, 0x01, 0x02};  /* 192.168.1.2 */

/* ------------------------------------------------------------------ */
/*  SLIP network interface (lwIP) — with TAP Ethernet framing         */
/* ------------------------------------------------------------------ */

/**
 * lwIP output callback — called when the IP stack wants to send a packet
 * out through the SLIP interface.
 *
 * Since the Pi uses a TAP device (layer 2), we must wrap the IP packet
 * in an Ethernet frame before SLIP-encoding it onto the serial link.
 *
 * Uses heap allocation (PSRAM) to avoid stack overflow in lwIP task context.
 */
static err_t slip_netif_output(struct netif* nif, struct pbuf* p, const ip4_addr_t* ipaddr)
{
    (void)nif;
    (void)ipaddr;

    uint16_t ip_len = p->tot_len;
    if (ip_len == 0 || ip_len > SLIP_MTU - ETH_HEADER_LEN) {
        return ERR_BUF;
    }

    /* Total frame = Ethernet header + IP payload */
    uint16_t frame_len = ETH_HEADER_LEN + ip_len;

    /* Heap-allocate to avoid ~4.7 KB stack pressure in lwIP task context */
    uint8_t* frame = (uint8_t*)heap_caps_malloc(SLIP_MTU, MALLOC_CAP_DEFAULT);
    uint8_t* encoded = (uint8_t*)heap_caps_malloc(SLIP_MAX_ENCODED, MALLOC_CAP_DEFAULT);
    if (!frame || !encoded) {
        free(frame);
        free(encoded);
        return ERR_MEM;
    }

    /* Build Ethernet header: dest=Pi, src=ESP32, type=IPv4 */
    memcpy(frame, PI_MAC, 6);
    memcpy(frame + 6, ESP_MAC, 6);
    frame[12] = (ETH_TYPE_IPV4 >> 8) & 0xFF;
    frame[13] = ETH_TYPE_IPV4 & 0xFF;

    /* Copy IP payload after Ethernet header */
    pbuf_copy_partial(p, frame + ETH_HEADER_LEN, ip_len, 0);

    /* SLIP-encode the full Ethernet frame and write to serial */
    size_t enc_len = slip_encode(frame, frame_len, encoded);

    size_t written = 0;
    while (written < enc_len) {
        size_t chunk = SLIP_SERIAL.write(encoded + written, enc_len - written);
        if (chunk == 0) {
            vTaskDelay(1);
            continue;
        }
        written += chunk;
    }

    free(frame);
    free(encoded);

    slip_tx_packets.fetch_add(1, std::memory_order_relaxed);
    return ERR_OK;
}

/**
 * lwIP netif init callback.
 */
static err_t slip_netif_init(struct netif* nif)
{
    nif->name[0] = 's';
    nif->name[1] = 'l';
    nif->output = slip_netif_output;
    nif->mtu = SLIP_MTU - ETH_HEADER_LEN;  /* IP MTU = SLIP MTU minus Ethernet header */
    nif->flags = NETIF_FLAG_LINK_UP | NETIF_FLAG_UP;
    return ERR_OK;
}

/**
 * Initialize the SLIP lwIP network interface with static IP.
 */
static bool init_slip_netif()
{
    ip4_addr_t ip, mask, gw;
    IP4_ADDR(&ip,   192, 168, 1, 1);
    IP4_ADDR(&mask,  255, 255, 255, 0);
    IP4_ADDR(&gw,   192, 168, 1, 2);

    /* Use tcpip_input (not netif_input) so packets are posted to the lwIP
     * thread's mailbox — safe to call from any FreeRTOS task/core. */
    if (netif_add(&slip_netif, &ip, &mask, &gw, nullptr, slip_netif_init, tcpip_input) == nullptr) {
        /* SLIP: netif_add failed */
        return false;
    }

    netif_set_up(&slip_netif);
    netif_set_link_up(&slip_netif);

    DBG_PRINTF("SLIP: netif up — %s/24 gw %s\n", ESP_IP, PI_IP);
    slip_netif_up = true;
    return true;
}

/* ------------------------------------------------------------------ */
/*  SLIP bridge task — pinned to Core 1                               */
/* ------------------------------------------------------------------ */

/**
 * Dedicated SLIP bridge task running on Core 1.
 *
 * Reads bytes from SLIP_SERIAL, decodes SLIP frames, strips the
 * Ethernet header (TAP framing from Pi), and injects the IP payload
 * into the lwIP stack via the slip_netif.
 * This task never returns.
 */
static void slip_bridge_task(void* param)
{
    (void)param;

    DBG_PRINTLN("SLIP: bridge task started on Core 1");
    slip_rx.reset();

    uint8_t serial_buf[512];

    for (;;) {
        int avail = SLIP_SERIAL.available();
        if (avail <= 0) {
            vTaskDelay(1);  /* Yield to other Core 1 tasks */
            continue;
        }

        /* Read available bytes (up to buffer size) */
        int to_read = min(avail, (int)sizeof(serial_buf));
        int n = SLIP_SERIAL.readBytes(serial_buf, to_read);

        for (int i = 0; i < n; i++) {
            int result = slip_rx.decode_byte(serial_buf[i]);

            if (result == 1) {
                /* Complete Ethernet frame from Pi — strip header, inject IP payload */
                if (slip_netif_up && slip_rx.len > ETH_HEADER_LEN) {
                    /* Verify it's IPv4 (EtherType 0x0800) */
                    uint16_t ethertype = (slip_rx.buf[12] << 8) | slip_rx.buf[13];
                    if (ethertype == ETH_TYPE_IPV4) {
                        uint16_t ip_len = slip_rx.len - ETH_HEADER_LEN;
                        struct pbuf* p = pbuf_alloc(PBUF_IP, ip_len, PBUF_RAM);
                        if (p != nullptr) {
                            pbuf_take(p, slip_rx.buf + ETH_HEADER_LEN, ip_len);
                            /* Post to lwIP thread — safe from Core 1 */
                            if (tcpip_input(p, &slip_netif) != ERR_OK) {
                                pbuf_free(p);
                            }
                        }
                    }
                    /* Non-IPv4 frames (ARP, etc.) are silently dropped —
                     * the SLIP link is point-to-point with static IPs,
                     * so ARP is not needed. */
                }
                slip_rx_packets.fetch_add(1, std::memory_order_relaxed);
                slip_rx.reset();
            } else if (result == -1) {
                slip_rx_errors.fetch_add(1, std::memory_order_relaxed);
                slip_rx.reset();
            }
        }
    }
}

/* ------------------------------------------------------------------ */
/*  Camera initialization                                             */
/* ------------------------------------------------------------------ */

static bool init_camera()
{
    camera_config_t config;
    memset(&config, 0, sizeof(config));

    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0       = Y2_GPIO_NUM;
    config.pin_d1       = Y3_GPIO_NUM;
    config.pin_d2       = Y4_GPIO_NUM;
    config.pin_d3       = Y5_GPIO_NUM;
    config.pin_d4       = Y6_GPIO_NUM;
    config.pin_d5       = Y7_GPIO_NUM;
    config.pin_d6       = Y8_GPIO_NUM;
    config.pin_d7       = Y9_GPIO_NUM;
    config.pin_xclk     = XCLK_GPIO_NUM;
    config.pin_pclk     = PCLK_GPIO_NUM;
    config.pin_vsync    = VSYNC_GPIO_NUM;
    config.pin_href     = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn     = PWDN_GPIO_NUM;
    config.pin_reset    = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;

    /* QVGA for bandwidth — SLIP serial can't handle higher resolutions */
    config.frame_size   = FRAMESIZE_QVGA;   /* 320x240 */
    config.jpeg_quality = CAM_QUALITY;       /* 15 (lower = better quality) */
    config.fb_count     = psramFound() ? 2 : 1;
    config.grab_mode    = CAMERA_GRAB_LATEST;

    if (psramFound()) {
        config.fb_location = CAMERA_FB_IN_PSRAM;
        DBG_PRINTF("PSRAM found (%d KB free)\n", ESP.getFreePsram() / 1024);
    }

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        DBG_PRINTF("Camera init failed: 0x%x\n", err);
        return false;
    }

    /* Sensor adjustments */
    sensor_t* s = esp_camera_sensor_get();
    if (s) {
        s->set_vflip(s, 1);
        s->set_hmirror(s, 1);
    }

    DBG_PRINTLN("Camera initialized: QVGA 320x240");
    return true;
}

/* ------------------------------------------------------------------ */
/*  MJPEG HTTP server                                                 */
/* ------------------------------------------------------------------ */

static const char* STREAM_CONTENT_TYPE = "multipart/x-mixed-replace; boundary=frame";
static const char* STREAM_BOUNDARY     = "\r\n--frame\r\n";
static const char* STREAM_PART         = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

/* Semaphore limits MJPEG stream to 1 concurrent client.
 * ESP32 camera DMA framebuffers are not safe for concurrent consumers. */
static SemaphoreHandle_t stream_sem = nullptr;

/**
 * MJPEG stream handler — serves continuous JPEG frames.
 * Limited to 1 concurrent client via semaphore to prevent DMA framebuffer races.
 */
static esp_err_t stream_handler(httpd_req_t* req)
{
    if (xSemaphoreTake(stream_sem, 0) != pdTRUE) {
        httpd_resp_set_status(req, "429 Too Many Requests");
        httpd_resp_send(req, "Stream in use", HTTPD_RESP_USE_STRLEN);
        return ESP_FAIL;
    }

    esp_err_t res = httpd_resp_set_type(req, STREAM_CONTENT_TYPE);
    if (res != ESP_OK) {
        xSemaphoreGive(stream_sem);
        return res;
    }

    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

    char part_buf[128];

    while (true) {
        camera_fb_t* fb = esp_camera_fb_get();
        if (!fb) {
            DBG_PRINTLN("Camera capture failed");
            res = ESP_FAIL;
            break;
        }

        /* Send boundary */
        res = httpd_resp_send_chunk(req, STREAM_BOUNDARY, strlen(STREAM_BOUNDARY));
        if (res != ESP_OK) {
            esp_camera_fb_return(fb);
            break;
        }

        /* Send part header */
        size_t hlen = snprintf(part_buf, sizeof(part_buf), STREAM_PART, fb->len);
        res = httpd_resp_send_chunk(req, part_buf, hlen);
        if (res != ESP_OK) {
            esp_camera_fb_return(fb);
            break;
        }

        /* Send JPEG data */
        res = httpd_resp_send_chunk(req, (const char*)fb->buf, fb->len);
        esp_camera_fb_return(fb);

        if (res != ESP_OK) break;

        frame_count.fetch_add(1, std::memory_order_relaxed);

        /* Rate limit to target FPS */
        vTaskDelay(pdMS_TO_TICKS(FRAME_INTERVAL_MS));
    }

    xSemaphoreGive(stream_sem);
    return res;
}

/**
 * Status endpoint — JSON with device info.
 */
static esp_err_t status_handler(httpd_req_t* req)
{
    JsonDocument doc;
    doc["node_id"]    = node_id;
    doc["uptime_s"]   = millis() / 1000;
    doc["free_heap"]  = ESP.getFreeHeap();
    doc["free_psram"] = psramFound() ? ESP.getFreePsram() : 0;
    doc["camera"]     = camera_ok;
    doc["stream_url"] = String("http://") + ESP_IP + ":" + String(CAM_PORT) + "/stream";
    doc["resolution"] = "QVGA";
    doc["target_fps"] = CAM_FPS;
    doc["frames"]     = frame_count.load(std::memory_order_relaxed);
    doc["slip_tx"]    = slip_tx_packets.load(std::memory_order_relaxed);
    doc["slip_rx"]    = slip_rx_packets.load(std::memory_order_relaxed);
    doc["slip_err"]   = slip_rx_errors.load(std::memory_order_relaxed);

    char buf[512];
    size_t len = serializeJson(doc, buf, sizeof(buf));
    if (len >= sizeof(buf)) {
        DBG_PRINTLN("WARNING: status JSON truncated");
    }

    httpd_resp_set_type(req, "application/json");
    return httpd_resp_send(req, buf, len);
}

/**
 * Snapshot endpoint — single JPEG frame.
 */
static esp_err_t snapshot_handler(httpd_req_t* req)
{
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }

    httpd_resp_set_type(req, "image/jpeg");
    httpd_resp_set_hdr(req, "Content-Disposition", "inline; filename=snapshot.jpg");
    esp_err_t res = httpd_resp_send(req, (const char*)fb->buf, fb->len);
    esp_camera_fb_return(fb);
    return res;
}

static void start_http_server()
{
    /* Initialize stream semaphore (1 concurrent client) */
    stream_sem = xSemaphoreCreateBinary();
    xSemaphoreGive(stream_sem);

    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = CAM_PORT;
    config.ctrl_port = CAM_PORT + 1;
    /* Allow large URI handlers for MJPEG streaming */
    config.stack_size = 8192;
    config.max_uri_handlers = 4;

    if (httpd_start(&stream_httpd, &config) != ESP_OK) {
        DBG_PRINTLN("HTTP server failed to start");
        return;
    }

    httpd_uri_t stream_uri = {
        .uri      = "/stream",
        .method   = HTTP_GET,
        .handler  = stream_handler,
        .user_ctx = nullptr
    };

    httpd_uri_t status_uri = {
        .uri      = "/status",
        .method   = HTTP_GET,
        .handler  = status_handler,
        .user_ctx = nullptr
    };

    httpd_uri_t snapshot_uri = {
        .uri      = "/snapshot",
        .method   = HTTP_GET,
        .handler  = snapshot_handler,
        .user_ctx = nullptr
    };

    httpd_register_uri_handler(stream_httpd, &stream_uri);
    httpd_register_uri_handler(stream_httpd, &status_uri);
    httpd_register_uri_handler(stream_httpd, &snapshot_uri);

    DBG_PRINTF("HTTP server started on port %d\n", CAM_PORT);
    DBG_PRINTF("  /stream   — MJPEG stream (%d FPS)\n", CAM_FPS);
    DBG_PRINTLN("  /status   — JSON device status");
    DBG_PRINTLN("  /snapshot — Single JPEG capture");
}

/* ------------------------------------------------------------------ */
/*  Heartbeat — HTTP POST to Pi backend                               */
/* ------------------------------------------------------------------ */

/**
 * Send periodic heartbeat to the Pi backend so it discovers this camera.
 * Uses plain HTTP POST (no WebSocket library needed).
 */
static void send_heartbeat()
{
    HTTPClient http;

    String url = String("http://") + PI_IP + ":" + String(PI_PORT)
               + "/api/cameras/heartbeat";

    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(5000);

    JsonDocument doc;
    doc["node_id"]    = node_id;
    doc["stream_url"] = String("http://") + ESP_IP + ":" + String(CAM_PORT) + "/stream";
    doc["resolution"] = "QVGA";
    doc["fps"]        = CAM_FPS;
    doc["free_heap"]  = ESP.getFreeHeap();
    doc["free_psram"] = psramFound() ? ESP.getFreePsram() : 0;
    doc["uptime_s"]   = millis() / 1000;
    doc["camera"]     = camera_ok;

    char payload[512];
    size_t written = serializeJson(doc, payload, sizeof(payload));
    if (written >= sizeof(payload)) {
        DBG_PRINTLN("WARNING: heartbeat JSON truncated");
        http.end();
        return;
    }

    int code = http.POST(payload);
    http.end();

    if (code == 200 || code == 204) {
        heartbeat_failures = 0;
    } else {
        heartbeat_failures++;
        if (heartbeat_failures <= 10 || heartbeat_failures % 60 == 0) {
            DBG_PRINTF("Heartbeat failed (code %d, attempt %d)\n",
                          code, heartbeat_failures);
        }
    }
}

/* ------------------------------------------------------------------ */
/*  Arduino setup / loop (Core 0)                                     */
/* ------------------------------------------------------------------ */

void setup()
{
    /* SLIP serial — shares UART0 with CP2102 USB-UART.
     * Must init at SLIP_BAUD (921600) since this is the data link.
     * No debug prints after this — they'd corrupt the SLIP stream. */
    SLIP_SERIAL.begin(SLIP_BAUD);
    delay(500);

    /* Derive node_id from MAC address (unique per board) */
    uint8_t mac[6];
    esp_efuse_mac_get_default(mac);
    snprintf(node_id, sizeof(node_id), "m3l_cam_%02x%02x", mac[4], mac[5]);

    /* Disable WiFi — we use SLIP, not WiFi, for network connectivity */
    WiFi.mode(WIFI_OFF);

    /* Initialize lwIP SLIP network interface */
    if (!init_slip_netif()) {
        DBG_PRINTLN("FATAL: SLIP netif init failed");
        while (true) { delay(1000); }
    }

    /* Launch SLIP bridge task on Core 1 */
    xTaskCreatePinnedToCore(
        slip_bridge_task,
        "slip_bridge",
        4096,           /* Stack size */
        nullptr,        /* Parameters */
        5,              /* Priority (higher than default 1) */
        nullptr,        /* Task handle */
        1               /* Core 1 */
    );

    /* Initialize camera */
    camera_ok = init_camera();
    if (!camera_ok) {
        DBG_PRINTLN("WARNING: Camera init failed — SLIP bridge still active");
        DBG_PRINTLN("         Camera endpoints will return errors");
    }

    /* Start HTTP server (serves MJPEG, status, snapshot) */
    start_http_server();

    DBG_PRINTLN("\nStartup complete:");
    DBG_PRINTF("  SLIP:   %s/24 via serial @ %d baud\n", ESP_IP, SLIP_BAUD);
    DBG_PRINTF("  Camera: %s (QVGA @ %d FPS)\n",
                  camera_ok ? "OK" : "FAILED", CAM_FPS);
    DBG_PRINTF("  HTTP:   port %d\n", CAM_PORT);
    DBG_PRINTF("  Heartbeat: every %lu ms to %s:%d\n",
                  HEARTBEAT_INTERVAL_MS, PI_IP, PI_PORT);
    DBG_PRINTF("  Free heap: %u bytes\n", ESP.getFreeHeap());
}

void loop()
{
    unsigned long now = millis();

    /* Send heartbeat to Pi backend */
    if (now - last_heartbeat >= HEARTBEAT_INTERVAL_MS) {
        send_heartbeat();
        last_heartbeat = now;
    }

    /* Periodic health log (every 60s) */
    static unsigned long last_health = 0;
    if (now - last_health >= 60000) {
        DBG_PRINTF("[health] heap=%u psram=%u frames=%u slip_tx=%u slip_rx=%u err=%u\n",
                      ESP.getFreeHeap(),
                      psramFound() ? ESP.getFreePsram() : 0,
                      frame_count.load(std::memory_order_relaxed),
                      slip_tx_packets.load(std::memory_order_relaxed),
                      slip_rx_packets.load(std::memory_order_relaxed),
                      slip_rx_errors.load(std::memory_order_relaxed));
        last_health = now;
    }

    delay(10);
}
