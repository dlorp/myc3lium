/*
 * LoRa TAP Bridge for myc3lium
 * 
 * Bridges Ethernet frames between TAP interface and SX1262 LoRa radio
 * Hardware: Waveshare SX1262 HAT on Raspberry Pi 4
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <time.h>
#include <sys/select.h>
#include <sys/time.h>

#include "sx1262.h"
#include "tap.h"
#include "fragment.h"

/* Global state */
static volatile sig_atomic_t running = 1;
static int tap_fd = -1;
static int irq_fd = -1;

/* Statistics */
static unsigned long tx_packets = 0;
static unsigned long rx_packets = 0;
static unsigned long tx_bytes = 0;
static unsigned long rx_bytes = 0;
static unsigned long tx_fragments = 0;
static unsigned long rx_fragments = 0;

/* Signal handler for clean shutdown - async-safe (CRITICAL-3) */
static void signal_handler(int sig)
{
    (void)sig;
    /* Security: Only use async-signal-safe operations in signal handler */
    running = 0;
}

/* Get current timestamp string */
static void get_timestamp(char *buf, size_t len)
{
    time_t now = time(NULL);
    struct tm *tm_info = localtime(&now);
    strftime(buf, len, "%Y-%m-%d %H:%M:%S", tm_info);
}

/* Print statistics */
static void print_stats(void)
{
    int reassembly_entries;
    unsigned long complete_frames, timeout_frames, corrupted_frames;
    
    reassembly_get_stats(&reassembly_entries, &complete_frames, 
                        &timeout_frames, &corrupted_frames);
    
    printf("\n=== Statistics ===\n");
    printf("TX: %lu packets, %lu bytes, %lu fragments\n", 
           tx_packets, tx_bytes, tx_fragments);
    printf("RX: %lu packets, %lu bytes, %lu fragments\n", 
           rx_packets, rx_bytes, rx_fragments);
    printf("Reassembly: %d active, %lu complete, %lu timeout, %lu corrupted\n",
           reassembly_entries, complete_frames, timeout_frames, corrupted_frames);
}

/* Wait for TX done with timeout */
static int wait_for_tx_done(int timeout_ms)
{
    struct timeval start, now;
    gettimeofday(&start, NULL);
    
    while (1) {
        uint16_t irq_status = sx1262_get_irq_status();
        
        if (irq_status & IRQ_TX_DONE) {
            sx1262_clear_irq_status(IRQ_TX_DONE);
            return 0;
        }
        
        if (irq_status & IRQ_TIMEOUT) {
            sx1262_clear_irq_status(IRQ_TIMEOUT);
            fprintf(stderr, "TX timeout\n");
            return -1;
        }
        
        /* Check timeout */
        gettimeofday(&now, NULL);
        long elapsed_ms = (now.tv_sec - start.tv_sec) * 1000 + 
                         (now.tv_usec - start.tv_usec) / 1000;
        
        if (elapsed_ms >= timeout_ms) {
            fprintf(stderr, "TX wait timeout\n");
            return -1;
        }
        
        usleep(1000); // 1ms
    }
}

/* Handle outgoing Ethernet frame from TAP */
static int handle_tap_read(void)
{
    uint8_t frame[TAP_MTU];
    char timestamp[32];
    
    ssize_t n = tap_read(tap_fd, frame, sizeof(frame));
    if (n < 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK) {
            return 0;
        }
        perror("tap_read");
        return -1;
    }
    
    if (n == 0) return 0;
    
    get_timestamp(timestamp, sizeof(timestamp));
    printf("[%s] TAP RX: %zd bytes\n", timestamp, n);
    
    /* Fragment the frame */
    lora_fragment_t frags[MAX_FRAGMENTS];
    int num_frags;
    
    if (fragment_frame(frame, n, frags, &num_frags) < 0) {
        fprintf(stderr, "Failed to fragment frame\n");
        return -1;
    }
    
    printf("[%s] Fragmenting into %d packets\n", timestamp, num_frags);
    
    /* Transmit each fragment */
    for (int i = 0; i < num_frags; i++) {
        uint8_t wire_buf[SX1262_MAX_PAYLOAD];
        size_t wire_len;
        
        if (fragment_encode(&frags[i], wire_buf, &wire_len) < 0) {
            fprintf(stderr, "Failed to encode fragment %d\n", i);
            continue;
        }
        
        if (sx1262_transmit(wire_buf, wire_len) < 0) {
            fprintf(stderr, "Failed to transmit fragment %d\n", i);
            continue;
        }
        
        /* Wait for TX done */
        if (wait_for_tx_done(500) < 0) {
            fprintf(stderr, "TX failed for fragment %d\n", i);
            continue;
        }
        
        tx_fragments++;
        printf("[%s] TX fragment %d/%d: %zu bytes\n", 
               timestamp, i + 1, num_frags, wire_len);
    }
    
    /* Return to RX mode */
    if (sx1262_set_rx(0xFFFFFF) < 0) {
        fprintf(stderr, "Failed to return to RX mode\n");
        return -1;
    }
    
    tx_packets++;
    tx_bytes += n;
    
    return 0;
}

/* Handle incoming LoRa packet */
static int handle_lora_irq(void)
{
    char timestamp[32];
    uint16_t irq_status = sx1262_get_irq_status();
    
    if (!(irq_status & IRQ_RX_DONE)) {
        /* Not RX done, clear and continue */
        sx1262_clear_irq_status(irq_status);
        return 0;
    }
    
    /* Clear RX done IRQ */
    sx1262_clear_irq_status(IRQ_RX_DONE);
    
    /* Receive packet */
    uint8_t wire_buf[SX1262_MAX_PAYLOAD];
    size_t wire_len;
    
    if (sx1262_receive(wire_buf, sizeof(wire_buf), &wire_len) < 0) {
        fprintf(stderr, "Failed to receive packet\n");
        return -1;
    }
    
    get_timestamp(timestamp, sizeof(timestamp));
    rx_fragments++;
    printf("[%s] RX fragment: %zu bytes\n", timestamp, wire_len);
    
    /* Decode fragment */
    lora_fragment_t frag;
    if (fragment_decode(wire_buf, wire_len, &frag) < 0) {
        fprintf(stderr, "Failed to decode fragment\n");
        return -1;
    }
    
    /* Reassemble */
    uint8_t complete_frame[MAX_FRAME_SIZE];
    size_t frame_len;
    
    int result = reassemble_fragment(&frag, complete_frame, &frame_len);
    
    if (result < 0) {
        fprintf(stderr, "Reassembly error\n");
        return -1;
    }
    
    if (result == 1) {
        /* Frame complete! */
        get_timestamp(timestamp, sizeof(timestamp));
        printf("[%s] Frame reassembled: %zu bytes\n", timestamp, frame_len);
        
        /* Write to TAP interface */
        if (tap_write(tap_fd, complete_frame, frame_len) < 0) {
            fprintf(stderr, "Failed to write to TAP\n");
            return -1;
        }
        
        rx_packets++;
        rx_bytes += frame_len;
        printf("[%s] TAP TX: %zu bytes\n", timestamp, frame_len);
    }
    
    /* Return to RX mode */
    if (sx1262_set_rx(0xFFFFFF) < 0) {
        fprintf(stderr, "Failed to return to RX mode\n");
        return -1;
    }
    
    return 0;
}

int main(int argc, char *argv[])
{
    int ret = 0;
    char timestamp[32];
    
    (void)argc;
    (void)argv;
    
    printf("=== myc3lium LoRa TAP Bridge ===\n");
    printf("Waveshare SX1262 HAT on Raspberry Pi 4\n\n");
    
    /* Install signal handlers */
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    /* Initialize fragmentation engine */
    fragment_init();
    
    /* Initialize SX1262 (GPIO + SPI) */
    printf("Initializing SX1262...\n");
    if (sx1262_init() < 0) {
        fprintf(stderr, "SX1262 initialization failed\n");
        ret = 1;
        goto cleanup;
    }
    
    /* Reset and configure SX1262 */
    if (sx1262_reset() < 0) {
        fprintf(stderr, "SX1262 reset failed\n");
        ret = 1;
        goto cleanup;
    }
    
    if (sx1262_configure() < 0) {
        fprintf(stderr, "SX1262 configuration failed\n");
        ret = 1;
        goto cleanup;
    }
    
    /* Create TAP interface */
    printf("\nCreating TAP interface: %s\n", TAP_DEVICE_NAME);
    tap_fd = tap_create(TAP_DEVICE_NAME);
    if (tap_fd < 0) {
        fprintf(stderr, "Failed to create TAP interface\n");
        ret = 1;
        goto cleanup;
    }
    
    /* Set MTU and bring interface up */
    if (tap_set_mtu(TAP_DEVICE_NAME, TAP_MTU) < 0) {
        fprintf(stderr, "Warning: Failed to set MTU\n");
    }
    
    if (tap_set_up(TAP_DEVICE_NAME) < 0) {
        fprintf(stderr, "Warning: Failed to bring interface up\n");
    }
    
    /* Open GPIO IRQ for DIO1 */
    irq_fd = gpio_open_irq(GPIO_DIO1);
    if (irq_fd < 0) {
        fprintf(stderr, "Failed to open GPIO IRQ\n");
        ret = 1;
        goto cleanup;
    }
    
    /* Start continuous RX */
    printf("\nStarting continuous RX mode...\n");
    if (sx1262_set_rx(0xFFFFFF) < 0) {
        fprintf(stderr, "Failed to start RX mode\n");
        ret = 1;
        goto cleanup;
    }
    
    get_timestamp(timestamp, sizeof(timestamp));
    printf("\n[%s] Bridge active: %s <-> SX1262 LoRa\n", 
           timestamp, TAP_DEVICE_NAME);
    printf("Configure with:\n");
    printf("  sudo ip addr add 10.0.0.1/24 dev %s\n", TAP_DEVICE_NAME);
    printf("  sudo ip route add 10.0.0.0/8 dev %s\n\n", TAP_DEVICE_NAME);
    
    /* Main event loop */
    time_t last_cleanup = time(NULL);
    time_t last_stats = time(NULL);
    
    int max_fd = (tap_fd > irq_fd ? tap_fd : irq_fd) + 1;
    
    while (running) {
        fd_set readfds;
        FD_ZERO(&readfds);
        FD_SET(tap_fd, &readfds);
        FD_SET(irq_fd, &readfds);
        
        struct timeval tv = {.tv_sec = 1, .tv_usec = 0};
        int select_ret = select(max_fd, &readfds, NULL, NULL, &tv);
        
        if (select_ret < 0) {
            if (errno == EINTR) continue;
            perror("select");
            ret = 1;
            break;
        }
        
        /* Handle TAP interface (outgoing frames) */
        if (FD_ISSET(tap_fd, &readfds)) {
            if (handle_tap_read() < 0) {
                fprintf(stderr, "TAP handler error\n");
            }
        }
        
        /* Handle LoRa IRQ (incoming packets) */
        if (FD_ISSET(irq_fd, &readfds)) {
            /* Clear IRQ event - just read to clear the fd */
            char dummy[64];
            if (read(irq_fd, dummy, sizeof(dummy)) > 0) {
                if (handle_lora_irq() < 0) {
                    fprintf(stderr, "LoRa IRQ handler error\n");
                }
            }
        }
        
        /* Periodic cleanup of stale reassembly entries */
        time_t now = time(NULL);
        if (now - last_cleanup >= 5) {
            int cleaned = reassembly_cleanup_expired(FRAG_TIMEOUT_SEC);
            if (cleaned > 0) {
                printf("Cleaned up %d expired reassembly entries\n", cleaned);
            }
            last_cleanup = now;
        }
        
        /* Print statistics every 60 seconds */
        if (now - last_stats >= 60) {
            print_stats();
            last_stats = now;
        }
    }
    
    /* Moved from signal handler to make it async-safe (CRITICAL-3) */
    printf("\nShutdown signal received...\n");
    printf("\n");
    print_stats();
    
cleanup:
    printf("\nCleaning up...\n");
    
    if (tap_fd >= 0) {
        close(tap_fd);
        tap_fd = -1;
    }
    
    if (irq_fd >= 0) {
        close(irq_fd);
        irq_fd = -1;
    }
    
    sx1262_cleanup();
    fragment_cleanup();
    
    printf("Shutdown complete\n");
    return ret;
}
