# Makefile for LoRa TAP Bridge
# Target: Raspberry Pi 4 (arm64, Debian Bookworm)

CC = gcc
CFLAGS = -Wall -Wextra -Werror -O2 -std=gnu11
LDFLAGS = -lgpiod

TARGET = lora-tap-bridge
SOURCES = lora-tap-bridge.c sx1262.c tap.c fragment.c
OBJECTS = $(SOURCES:.c=.o)
HEADERS = sx1262.h tap.h fragment.h

# Default target
all: $(TARGET)

# Link
$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)
	@echo "Built $(TARGET) successfully"

# Compile
%.o: %.c $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@

# Clean
clean:
	rm -f $(OBJECTS) $(TARGET)
	@echo "Cleaned build artifacts"

# Install (requires root for systemd service)
install: $(TARGET)
	install -m 755 $(TARGET) /usr/local/bin/
	@if [ -f lora-bridge.service ]; then \
		install -m 644 lora-bridge.service /etc/systemd/system/; \
		systemctl daemon-reload; \
		echo "Installed systemd service. Enable with: sudo systemctl enable lora-bridge"; \
	fi

# Uninstall
uninstall:
	rm -f /usr/local/bin/$(TARGET)
	@if [ -f /etc/systemd/system/lora-bridge.service ]; then \
		systemctl stop lora-bridge || true; \
		systemctl disable lora-bridge || true; \
		rm -f /etc/systemd/system/lora-bridge.service; \
		systemctl daemon-reload; \
	fi

# Test build
test: all
	@echo "Running basic sanity checks..."
	@file $(TARGET) | grep -q "ARM aarch64" && echo "✓ Built for ARM64" || echo "✗ Wrong architecture"
	@ldd $(TARGET) | grep -q "libgpiod" && echo "✓ Linked with libgpiod" || echo "✗ Missing libgpiod"

.PHONY: all clean install uninstall test
