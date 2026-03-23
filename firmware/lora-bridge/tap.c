/*
 * TAP Interface Helper Functions Implementation
 */

#include "tap.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <linux/if.h>
#include <linux/if_tun.h>

int tap_create(const char *dev_name)
{
    struct ifreq ifr;
    int fd, err;
    
    /* Open TUN/TAP device */
    fd = open("/dev/net/tun", O_RDWR);
    if (fd < 0) {
        perror("open /dev/net/tun");
        return -1;
    }
    
    /* Configure TAP interface */
    memset(&ifr, 0, sizeof(ifr));
    ifr.ifr_flags = IFF_TAP | IFF_NO_PI;  // TAP mode, no packet info header
    strncpy(ifr.ifr_name, dev_name, IFNAMSIZ - 1);
    
    err = ioctl(fd, TUNSETIFF, (void *)&ifr);
    if (err < 0) {
        perror("ioctl TUNSETIFF");
        close(fd);
        return -1;
    }
    
    printf("Created TAP interface: %s\n", ifr.ifr_name);
    return fd;
}

int tap_set_mtu(const char *dev_name, int mtu)
{
    struct ifreq ifr;
    int sockfd;
    
    sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        perror("socket");
        return -1;
    }
    
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, dev_name, IFNAMSIZ - 1);
    ifr.ifr_mtu = mtu;
    
    if (ioctl(sockfd, SIOCSIFMTU, &ifr) < 0) {
        perror("ioctl SIOCSIFMTU");
        close(sockfd);
        return -1;
    }
    
    close(sockfd);
    return 0;
}

int tap_set_up(const char *dev_name)
{
    struct ifreq ifr;
    int sockfd;
    
    sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        perror("socket");
        return -1;
    }
    
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, dev_name, IFNAMSIZ - 1);
    
    /* Get current flags */
    if (ioctl(sockfd, SIOCGIFFLAGS, &ifr) < 0) {
        perror("ioctl SIOCGIFFLAGS");
        close(sockfd);
        return -1;
    }
    
    /* Set UP flag */
    ifr.ifr_flags |= IFF_UP | IFF_RUNNING;
    
    if (ioctl(sockfd, SIOCSIFFLAGS, &ifr) < 0) {
        perror("ioctl SIOCSIFFLAGS");
        close(sockfd);
        return -1;
    }
    
    close(sockfd);
    printf("Interface %s is UP\n", dev_name);
    return 0;
}

ssize_t tap_read(int fd, void *buf, size_t buf_size)
{
    ssize_t n = read(fd, buf, buf_size);
    if (n < 0 && errno != EAGAIN && errno != EWOULDBLOCK) {
        perror("tap_read");
        return -1;
    }
    return n;
}

ssize_t tap_write(int fd, const void *buf, size_t len)
{
    ssize_t n = write(fd, buf, len);
    if (n < 0) {
        perror("tap_write");
        return -1;
    }
    return n;
}
