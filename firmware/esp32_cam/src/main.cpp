/**
 * MYC3LIUM ESP32-S3 CAM Firmware
 * 
 * Camera streaming node with ATAK integration
 * - OV3660 camera (2MP)
 * - RTMP streaming to intelligence API
 * - WebSocket connection to mesh backend
 * - Motion detection
 * - Low-power operation
 */

#include <Arduino.h>
#include <WiFi.h>
#include <ArduinoWebsockets.h>
#include <ArduinoJson.h>
#include "esp_camera.h"
#include "esp_timer.h"
#include "esp_http_server.h"

// Camera pins for ESP32-S3-CAM (Heltec)
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

// Configuration
const char* WIFI_SSID = "MYCELIUM_MESH";
const char* WIFI_PASSWORD = "your_mesh_password";
const char* WS_SERVER = "ws://192.168.1.100:8000/ws/intelligence";
const char* API_TOKEN = "your_api_token_here";

// Node identification
const char* NODE_ID = "m3l_cam_01";

// WebSocket client
using namespace websockets;
WebsocketsClient ws_client;

// Camera config
camera_config_t camera_config;

// State
bool camera_initialized = false;
bool ws_connected = false;
unsigned long last_frame_time = 0;
unsigned long last_heartbeat = 0;
const unsigned long FRAME_INTERVAL = 100;  // 10 FPS
const unsigned long HEARTBEAT_INTERVAL = 5000;  // 5s

// MJPEG streaming server
httpd_handle_t stream_httpd = NULL;

/**
 * Initialize camera
 */
bool init_camera() {
    camera_config.ledc_channel = LEDC_CHANNEL_0;
    camera_config.ledc_timer = LEDC_TIMER_0;
    camera_config.pin_d0 = Y2_GPIO_NUM;
    camera_config.pin_d1 = Y3_GPIO_NUM;
    camera_config.pin_d2 = Y4_GPIO_NUM;
    camera_config.pin_d3 = Y5_GPIO_NUM;
    camera_config.pin_d4 = Y6_GPIO_NUM;
    camera_config.pin_d5 = Y7_GPIO_NUM;
    camera_config.pin_d6 = Y8_GPIO_NUM;
    camera_config.pin_d7 = Y9_GPIO_NUM;
    camera_config.pin_xclk = XCLK_GPIO_NUM;
    camera_config.pin_pclk = PCLK_GPIO_NUM;
    camera_config.pin_vsync = VSYNC_GPIO_NUM;
    camera_config.pin_href = HREF_GPIO_NUM;
    camera_config.pin_sscb_sda = SIOD_GPIO_NUM;
    camera_config.pin_sscb_scl = SIOC_GPIO_NUM;
    camera_config.pin_pwdn = PWDN_GPIO_NUM;
    camera_config.pin_reset = RESET_GPIO_NUM;
    camera_config.xclk_freq_hz = 20000000;
    camera_config.pixel_format = PIXFORMAT_JPEG;
    
    // High quality for ATAK integration
    if (psramFound()) {
        camera_config.frame_size = FRAMESIZE_SVGA;  // 800x600
        camera_config.jpeg_quality = 10;  // 0-63 lower means higher quality
        camera_config.fb_count = 2;
    } else {
        camera_config.frame_size = FRAMESIZE_VGA;   // 640x480
        camera_config.jpeg_quality = 12;
        camera_config.fb_count = 1;
    }
    
    // Initialize camera
    esp_err_t err = esp_camera_init(&camera_config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed with error 0x%x\n", err);
        return false;
    }
    
    // Get sensor
    sensor_t* s = esp_camera_sensor_get();
    
    // Flip image if needed
    s->set_vflip(s, 1);
    s->set_hmirror(s, 1);
    
    Serial.println("Camera initialized");
    return true;
}

/**
 * MJPEG streaming handler
 */
esp_err_t stream_handler(httpd_req_t *req) {
    camera_fb_t* fb = NULL;
    esp_err_t res = ESP_OK;
    size_t _jpg_buf_len = 0;
    uint8_t* _jpg_buf = NULL;
    char part_buf[64];
    
    res = httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=frame");
    if (res != ESP_OK) {
        return res;
    }
    
    while (true) {
        fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("Camera capture failed");
            res = ESP_FAIL;
            break;
        }
        
        _jpg_buf_len = fb->len;
        _jpg_buf = fb->buf;
        
        if (res == ESP_OK) {
            size_t hlen = snprintf(part_buf, 64, 
                "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", 
                _jpg_buf_len);
            res = httpd_resp_send_chunk(req, part_buf, hlen);
        }
        
        if (res == ESP_OK) {
            res = httpd_resp_send_chunk(req, (const char*)_jpg_buf, _jpg_buf_len);
        }
        
        if (res == ESP_OK) {
            res = httpd_resp_send_chunk(req, "\r\n", 2);
        }
        
        esp_camera_fb_return(fb);
        
        if (res != ESP_OK) {
            break;
        }
    }
    
    return res;
}

/**
 * Start MJPEG streaming server
 */
void start_stream_server() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 8080;
    
    httpd_uri_t stream_uri = {
        .uri       = "/stream",
        .method    = HTTP_GET,
        .handler   = stream_handler,
        .user_ctx  = NULL
    };
    
    if (httpd_start(&stream_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, &stream_uri);
        Serial.println("Stream server started on port 8080");
    }
}

/**
 * Connect to WebSocket
 */
bool connect_websocket() {
    // Add authentication token to URL
    String ws_url = String(WS_SERVER) + "?token=" + String(API_TOKEN);
    
    ws_client.onMessage([](WebsocketsMessage message) {
        Serial.print("Received: ");
        Serial.println(message.data());
        
        // Parse command
        StaticJsonDocument<512> doc;
        DeserializationError error = deserializeJson(doc, message.data());
        
        if (!error) {
            const char* type = doc["type"];
            
            if (strcmp(type, "capture") == 0) {
                // Capture single frame and send
                camera_fb_t* fb = esp_camera_fb_get();
                if (fb) {
                    // Send frame via WebSocket (base64 encoded)
                    // Implementation depends on size limits
                    esp_camera_fb_return(fb);
                }
            }
        }
    });
    
    ws_client.onEvent([](WebsocketsEvent event, String data) {
        if (event == WebsocketsEvent::ConnectionOpened) {
            Serial.println("WebSocket connected");
            ws_connected = true;
        } else if (event == WebsocketsEvent::ConnectionClosed) {
            Serial.println("WebSocket disconnected");
            ws_connected = false;
        }
    });
    
    return ws_client.connect(ws_url);
}

/**
 * Send heartbeat to mesh
 */
void send_heartbeat() {
    if (!ws_connected) return;
    
    StaticJsonDocument<256> doc;
    doc["type"] = "heartbeat";
    doc["node_id"] = NODE_ID;
    doc["uptime"] = millis() / 1000;
    doc["free_heap"] = ESP.getFreeHeap();
    doc["stream_url"] = "http://" + WiFi.localIP().toString() + ":8080/stream";
    
    String json;
    serializeJson(doc, json);
    
    ws_client.send(json);
}

/**
 * Setup
 */
void setup() {
    Serial.begin(115200);
    Serial.println("\nMYC3LIUM ESP32-S3 CAM starting...");
    
    // Initialize camera
    if (!init_camera()) {
        Serial.println("Camera initialization failed!");
        while (1) {
            delay(1000);
        }
    }
    camera_initialized = true;
    
    // Connect to WiFi
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    Serial.print("Connecting to WiFi");
    int retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 20) {
        delay(500);
        Serial.print(".");
        retries++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi connected");
        Serial.print("IP address: ");
        Serial.println(WiFi.localIP());
        
        // Start streaming server
        start_stream_server();
        
        // Connect to WebSocket
        if (connect_websocket()) {
            Serial.println("WebSocket connected");
        }
    } else {
        Serial.println("\nWiFi connection failed");
    }
}

/**
 * Main loop
 */
void loop() {
    unsigned long now = millis();
    
    // Maintain WebSocket connection
    if (WiFi.status() == WL_CONNECTED) {
        if (ws_connected) {
            ws_client.poll();
        } else {
            // Try to reconnect
            if (now - last_heartbeat > 5000) {
                Serial.println("Attempting WebSocket reconnect...");
                connect_websocket();
                last_heartbeat = now;
            }
        }
        
        // Send heartbeat
        if (ws_connected && now - last_heartbeat > HEARTBEAT_INTERVAL) {
            send_heartbeat();
            last_heartbeat = now;
        }
    } else {
        // WiFi disconnected, try to reconnect
        WiFi.reconnect();
        delay(1000);
    }
    
    delay(10);
}
