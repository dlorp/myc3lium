/*
 * TAP Interface Helper Functions
 */

#ifndef TAP_H
#define TAP_H

#include <stddef.h>
#include <sys/types.h>

#define TAP_DEVICE_NAME  "lora0"
#define TAP_MTU          1500

/**
 * Create a TAP network interface
 * 
 * @param dev_name  Name of the TAP interface (e.g., "lora0")
 * @return File descriptor on success, -1 on error
 */
int tap_create(const char *dev_name);

/**
 * Set TAP interface MTU
 * 
 * @param dev_name  Name of the TAP interface
 * @param mtu       Maximum Transmission Unit size
 * @return 0 on success, -1 on error
 */
int tap_set_mtu(const char *dev_name, int mtu);

/**
 * Bring TAP interface up
 * 
 * @param dev_name  Name of the TAP interface
 * @return 0 on success, -1 on error
 */
int tap_set_up(const char *dev_name);

/**
 * Read an Ethernet frame from TAP interface
 * 
 * @param fd        TAP file descriptor
 * @param buf       Buffer to store frame
 * @param buf_size  Size of buffer
 * @return Number of bytes read, -1 on error
 */
ssize_t tap_read(int fd, void *buf, size_t buf_size);

/**
 * Write an Ethernet frame to TAP interface
 * 
 * @param fd    TAP file descriptor
 * @param buf   Frame data
 * @param len   Frame length
 * @return Number of bytes written, -1 on error
 */
ssize_t tap_write(int fd, const void *buf, size_t len);

#endif /* TAP_H */
