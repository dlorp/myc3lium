#!/bin/bash
set -e

echo "=== ESP32-S3 CAM HaLow Firmware Flash Script ==="
echo ""

# Directories
ESP_DIR="/Users/lorp/esp"
IDF_DIR="$ESP_DIR/esp-idf"
MORSE_DIR="$ESP_DIR/mm-iot-esp32"
PROJECT_DIR="$MORSE_DIR/examples/sta_connect"

# Step 1: Install ESP-IDF if not present
if [ ! -d "$IDF_DIR" ]; then
    echo "Installing ESP-IDF v5.2.2..."
    mkdir -p "$ESP_DIR"
    cd "$ESP_DIR"
    git clone -b v5.2.2 --recursive https://github.com/espressif/esp-idf.git
    cd esp-idf
    ./install.sh esp32s3
else
    echo "ESP-IDF already installed at $IDF_DIR"
fi

# Step 2: Activate ESP-IDF
echo "Activating ESP-IDF..."
source "$IDF_DIR/export.sh"

# Step 3: Clone MorseMicro SDK if not present
if [ ! -d "$MORSE_DIR" ]; then
    echo "Cloning MorseMicro ESP32 SDK..."
    cd "$ESP_DIR"
    git clone https://github.com/MorseMicro/mm-iot-esp32.git
else
    echo "MorseMicro SDK already at $MORSE_DIR"
fi

# Set environment
export MMIOT_ROOT="$MORSE_DIR"

# Step 4: Configure project
echo "Configuring project for ESP32-S3..."
cd "$PROJECT_DIR"
idf.py set-target esp32s3

# Step 5: Create sdkconfig with our settings
echo "Creating sdkconfig..."
cat > sdkconfig.defaults << 'SDKCONFIG'
# Morse Micro Configuration
CONFIG_MM_SPI_MOSI_GPIO=10
CONFIG_MM_SPI_MISO_GPIO=9
CONFIG_MM_SPI_CLK_GPIO=11
CONFIG_MM_SPI_CS_GPIO=8
CONFIG_MM_IRQ_GPIO=21
CONFIG_MM_RESETN_GPIO=3
CONFIG_MM_WAKE_GPIO=46
CONFIG_MM_BUSY_GPIO=7

# Firmware files
CONFIG_MM_BCF_FILE="bcf_mf15457.mbin"
CONFIG_MM_FW_FILE="mm6108-rl.mbin"
CONFIG_MMHAL_CHIP_TYPE_MM6108=y

# USB CDC
CONFIG_ESP_CONSOLE_USB_CDC=y
CONFIG_ESP_CONSOLE_SECONDARY_USB_SERIAL_JTAG=y

# Country code (US)
CONFIG_MORSE_COUNTRY_CODE="US"
SDKCONFIG

# Apply defaults
idf.py reconfigure

# Step 6: Build
echo ""
echo "Building firmware (this may take 5-10 minutes)..."
idf.py build

# Step 7: Find USB device
echo ""
echo "Looking for ESP32 USB device..."
DEVICE=$(ls /dev/cu.usbmodem* 2>/dev/null | head -1)

if [ -z "$DEVICE" ]; then
    DEVICE=$(ls /dev/cu.usbserial* 2>/dev/null | head -1)
fi

if [ -z "$DEVICE" ]; then
    echo "ERROR: No ESP32 device found!"
    echo "Please connect ESP32 via USB-C cable and try again"
    exit 1
fi

echo "Found device: $DEVICE"

# Step 8: Flash
echo ""
echo "Flashing firmware to ESP32..."
echo "(Hold BOOT button if flash fails)"
idf.py -p "$DEVICE" flash

# Step 9: Monitor
echo ""
echo "=== Firmware flashed successfully! ==="
echo ""
echo "Starting monitor (Ctrl+] to exit)..."
echo ""
idf.py -p "$DEVICE" monitor
