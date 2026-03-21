.PHONY: build-halow build-lora clean flash monitor help

VARIANT ?= halow
PORT ?= /dev/ttyUSB0
BAUD ?= 921600

help:
	@echo "myc3lium handheld firmware build targets"
	@echo ""
	@echo "Usage: make [target] VARIANT=<halow|lora> PORT=<device> BAUD=<rate>"
	@echo ""
	@echo "Targets:"
	@echo "  build-halow  Build for HT-HC01P variant (HaLow)"
	@echo "  build-lora   Build for SX1262 variant (LoRa+OLED)"
	@echo "  clean        Remove build artifacts"
	@echo "  flash        Flash to device (requires VARIANT)"
	@echo "  monitor      Open serial monitor"
	@echo "  help         Show this message"
	@echo ""
	@echo "Examples:"
	@echo "  make build-halow"
	@echo "  make build-lora"
	@echo "  make VARIANT=halow flash PORT=/dev/ttyUSB0"
	@echo "  make monitor PORT=/dev/ttyACM0"

build-halow:
	@echo "Building for HaLow variant..."
	@export MYC3_VARIANT=halow && idf.py build

build-lora:
	@echo "Building for LoRa variant..."
	@export MYC3_VARIANT=lora && idf.py build

clean:
	@echo "Cleaning build artifacts..."
	@idf.py fullclean

flash:
	@echo "Flashing $(VARIANT) variant to $(PORT)..."
	@export MYC3_VARIANT=$(VARIANT) && idf.py -p $(PORT) -b $(BAUD) flash

monitor:
	@echo "Opening serial monitor on $(PORT)..."
	@idf.py -p $(PORT) -b $(BAUD) monitor

build-check:
	@echo "Checking both variants compile..."
	@echo "Testing HaLow variant..."
	@export MYC3_VARIANT=halow && idf.py build > /dev/null 2>&1 && echo "  HaLow: OK" || echo "  HaLow: FAILED"
	@echo "Testing LoRa variant..."
	@export MYC3_VARIANT=lora && idf.py build > /dev/null 2>&1 && echo "  LoRa: OK" || echo "  LoRa: FAILED"
