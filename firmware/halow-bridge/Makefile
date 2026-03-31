# Makefile for HaLow SLIP Bridge
# Target: Raspberry Pi 4 (arm64, Debian Bookworm)

CC = gcc
CFLAGS = -Wall -Wextra -Werror -O2 -std=gnu11
LDFLAGS =

TARGET = halow-slip-bridge
SOURCES = pi-slip-daemon.c
OBJECTS = $(SOURCES:.c=.o)

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)
	@echo "Built $(TARGET) successfully"

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET)

install: $(TARGET)
	install -m 755 $(TARGET) /usr/local/bin/
	install -m 750 halow-start.sh /usr/local/bin/
	@if [ -f halow-bridge.service ]; then \
		install -m 644 halow-bridge.service /etc/systemd/system/; \
		systemctl daemon-reload; \
		echo "Installed systemd service. Enable with: sudo systemctl enable halow-bridge"; \
	fi

uninstall:
	rm -f /usr/local/bin/$(TARGET) /usr/local/bin/halow-start.sh
	@if [ -f /etc/systemd/system/halow-bridge.service ]; then \
		systemctl stop halow-bridge || true; \
		systemctl disable halow-bridge || true; \
		rm -f /etc/systemd/system/halow-bridge.service; \
		systemctl daemon-reload; \
	fi

.PHONY: all clean install uninstall
