/*
 * LoRa Packet Fragmentation/Reassembly Engine
 * 
 * Fragments Ethernet frames (up to 1500 bytes) into LoRa-sized chunks (≤255 bytes)
 * with a 3-byte header for reassembly.
 */

#ifndef FRAGMENT_H
#define FRAGMENT_H

#include <stdint.h>
#include <stddef.h>
#include <time.h>

/* Fragment Protocol Constants */
#define FRAG_HEADER_SIZE   3      // 3-byte header per fragment
#define FRAG_MAX_PAYLOAD   252    // 255 - 3 bytes header
#define MAX_FRAME_SIZE     1500   // Ethernet MTU
#define MAX_FRAGMENTS      6      // ceil(1500 / 252) = 6
#define MAX_FRAG_ID        16     // Fragment ID wraps at 16
#define FRAG_TIMEOUT_SEC   5      // Reassembly timeout
#define MAX_REASSEMBLY_ENTRIES 16 // Limit reassembly queue to prevent DoS

/* Fragment Header Structure (3 bytes):
 * Byte 0: [FRAG_ID (4 bits)] [TOTAL_FRAGS (4 bits)]
 * Byte 1: [FRAG_INDEX (8 bits)]
 * Byte 2: [PAYLOAD_LEN (8 bits)]
 */

/**
 * LoRa fragment structure
 */
typedef struct {
    uint8_t frag_id;       // Fragment ID (0-15, wraps around)
    uint8_t total_frags;   // Total number of fragments in this frame
    uint8_t frag_index;    // Index of this fragment (0-based)
    uint8_t payload_len;   // Length of payload in this fragment
    uint8_t payload[FRAG_MAX_PAYLOAD];
} lora_fragment_t;

/**
 * Reassembly entry for tracking incomplete frames
 */
typedef struct reassembly_entry {
    uint8_t frag_id;              // Fragment ID being reassembled
    uint8_t total_frags;          // Expected total fragments
    uint8_t received_mask;        // Bitmask of received fragments (up to 8)
    uint8_t data[MAX_FRAME_SIZE]; // Reassembled frame data
    size_t total_len;             // Total frame length so far
    time_t first_seen;            // Timestamp of first fragment
    struct reassembly_entry *next;
} reassembly_entry_t;

/**
 * Initialize fragmentation engine
 */
void fragment_init(void);

/**
 * Clean up fragmentation engine
 */
void fragment_cleanup(void);

/**
 * Fragment an Ethernet frame into LoRa-sized chunks
 * 
 * @param frame      Ethernet frame data
 * @param frame_len  Length of frame
 * @param frags      Output array of fragments (must hold MAX_FRAGMENTS)
 * @param num_frags  Output: number of fragments created
 * @return 0 on success, -1 on error
 */
int fragment_frame(const uint8_t *frame, size_t frame_len,
                   lora_fragment_t *frags, int *num_frags);

/**
 * Encode fragment into wire format (3-byte header + payload)
 * 
 * @param frag      Fragment to encode
 * @param out       Output buffer (must be at least 255 bytes)
 * @param out_len   Output: encoded length
 * @return 0 on success, -1 on error
 */
int fragment_encode(const lora_fragment_t *frag, uint8_t *out, size_t *out_len);

/**
 * Decode wire format into fragment structure
 * 
 * @param data      Wire format data
 * @param len       Length of data
 * @param frag      Output fragment
 * @return 0 on success, -1 on error
 */
int fragment_decode(const uint8_t *data, size_t len, lora_fragment_t *frag);

/**
 * Process received fragment and attempt reassembly
 * 
 * @param frag           Received fragment
 * @param complete_frame Output buffer for complete frame (if reassembly complete)
 * @param frame_len      Output: length of complete frame
 * @return 1 if frame complete, 0 if waiting for more, -1 on error
 */
int reassemble_fragment(const lora_fragment_t *frag, uint8_t *complete_frame,
                        size_t *frame_len);

/**
 * Clean up expired reassembly entries
 * 
 * @param timeout_sec  Maximum age in seconds before expiry
 * @return Number of entries cleaned up
 */
int reassembly_cleanup_expired(int timeout_sec);

/**
 * Get reassembly statistics
 * 
 * @param total_entries    Output: total active reassembly entries
 * @param complete_frames  Output: frames successfully reassembled
 * @param timeout_frames   Output: frames that timed out
 * @param corrupted_frames Output: frames with errors
 */
void reassembly_get_stats(int *total_entries, unsigned long *complete_frames,
                         unsigned long *timeout_frames, unsigned long *corrupted_frames);

#endif /* FRAGMENT_H */
