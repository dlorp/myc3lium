/*
 * LoRa Packet Fragmentation/Reassembly Engine Implementation
 */

#include "fragment.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* Global state */
static reassembly_entry_t *reassembly_list = NULL;
static uint8_t next_frag_id = 0;
static unsigned long stats_complete_frames = 0;
static unsigned long stats_timeout_frames = 0;
static unsigned long stats_corrupted_frames = 0;

void fragment_init(void)
{
    reassembly_list = NULL;
    next_frag_id = 0;
    stats_complete_frames = 0;
    stats_timeout_frames = 0;
    stats_corrupted_frames = 0;
}

void fragment_cleanup(void)
{
    reassembly_entry_t *entry = reassembly_list;
    while (entry) {
        reassembly_entry_t *next = entry->next;
        free(entry);
        entry = next;
    }
    reassembly_list = NULL;
}

int fragment_frame(const uint8_t *frame, size_t frame_len,
                   lora_fragment_t *frags, int *num_frags)
{
    if (!frame || !frags || !num_frags) {
        return -1;
    }

    if (frame_len > MAX_FRAME_SIZE) {
        fprintf(stderr, "Frame too large: %zu > %d\n", frame_len, MAX_FRAME_SIZE);
        return -1;
    }

    /* Calculate number of fragments needed */
    *num_frags = (frame_len + FRAG_MAX_PAYLOAD - 1) / FRAG_MAX_PAYLOAD;
    
    if (*num_frags > MAX_FRAGMENTS) {
        fprintf(stderr, "Too many fragments: %d > %d\n", *num_frags, MAX_FRAGMENTS);
        return -1;
    }

    uint8_t frag_id = next_frag_id;
    next_frag_id = (next_frag_id + 1) % MAX_FRAG_ID;

    /* Create fragments */
    for (int i = 0; i < *num_frags; i++) {
        frags[i].frag_id = frag_id;
        frags[i].total_frags = *num_frags;
        frags[i].frag_index = i;
        
        size_t offset = i * FRAG_MAX_PAYLOAD;
        size_t remaining = frame_len - offset;
        frags[i].payload_len = (remaining > FRAG_MAX_PAYLOAD) 
                               ? FRAG_MAX_PAYLOAD : remaining;
        
        memcpy(frags[i].payload, frame + offset, frags[i].payload_len);
    }

    return 0;
}

int fragment_encode(const lora_fragment_t *frag, uint8_t *out, size_t *out_len)
{
    if (!frag || !out || !out_len) {
        return -1;
    }

    /* Security: Validate payload length to prevent buffer overflow (HIGH-3) */
    if (frag->payload_len > FRAG_MAX_PAYLOAD) {
        fprintf(stderr, "Payload length too large: %d > %d\n",
                frag->payload_len, FRAG_MAX_PAYLOAD);
        return -1;
    }

    /* Header: 3 bytes */
    out[0] = ((frag->frag_id & 0x0F) << 4) | (frag->total_frags & 0x0F);
    out[1] = frag->frag_index;
    out[2] = frag->payload_len;

    /* Payload */
    memcpy(out + FRAG_HEADER_SIZE, frag->payload, frag->payload_len);

    *out_len = FRAG_HEADER_SIZE + frag->payload_len;
    return 0;
}

int fragment_decode(const uint8_t *data, size_t len, lora_fragment_t *frag)
{
    if (!data || !frag || len < FRAG_HEADER_SIZE) {
        return -1;
    }

    /* Decode header */
    frag->frag_id = (data[0] >> 4) & 0x0F;
    frag->total_frags = data[0] & 0x0F;
    frag->frag_index = data[1];
    frag->payload_len = data[2];

    /* Validate */
    if (frag->payload_len > FRAG_MAX_PAYLOAD) {
        fprintf(stderr, "Invalid payload length: %d\n", frag->payload_len);
        return -1;
    }

    /* Security: Validate fragment index is within bounds (CRITICAL-2) */
    if (frag->frag_index >= MAX_FRAGMENTS) {
        fprintf(stderr, "Fragment index exceeds maximum: %d >= %d\n", 
                frag->frag_index, MAX_FRAGMENTS);
        return -1;
    }

    if (frag->frag_index >= frag->total_frags) {
        fprintf(stderr, "Invalid fragment index: %d >= %d\n", 
                frag->frag_index, frag->total_frags);
        return -1;
    }

    if (len < FRAG_HEADER_SIZE + frag->payload_len) {
        fprintf(stderr, "Truncated fragment: %zu < %d\n", 
                len, FRAG_HEADER_SIZE + frag->payload_len);
        return -1;
    }

    /* Copy payload */
    memcpy(frag->payload, data + FRAG_HEADER_SIZE, frag->payload_len);

    return 0;
}

static reassembly_entry_t *find_or_create_entry(uint8_t frag_id, uint8_t total_frags)
{
    /* Search for existing entry */
    int count = 0;
    reassembly_entry_t *entry = reassembly_list;
    while (entry) {
        if (entry->frag_id == frag_id) {
            return entry;
        }
        count++;
        entry = entry->next;
    }

    /* Security: Enforce limit to prevent memory exhaustion DoS (MEDIUM-3) */
    if (count >= MAX_REASSEMBLY_ENTRIES) {
        fprintf(stderr, "Too many reassembly entries (%d), rejecting new frame\n", count);
        return NULL;
    }

    /* Create new entry */
    entry = calloc(1, sizeof(reassembly_entry_t));
    if (!entry) {
        perror("calloc reassembly_entry");
        return NULL;
    }

    entry->frag_id = frag_id;
    entry->total_frags = total_frags;
    entry->received_mask = 0;
    entry->total_len = 0;
    entry->first_seen = time(NULL);
    entry->next = reassembly_list;
    reassembly_list = entry;

    return entry;
}

static void remove_entry(reassembly_entry_t *target)
{
    if (!target) return;

    reassembly_entry_t **ptr = &reassembly_list;
    while (*ptr) {
        if (*ptr == target) {
            *ptr = target->next;
            free(target);
            return;
        }
        ptr = &(*ptr)->next;
    }
}

int reassemble_fragment(const lora_fragment_t *frag, uint8_t *complete_frame,
                        size_t *frame_len)
{
    if (!frag || !complete_frame || !frame_len) {
        return -1;
    }

    /* Security: Validate total_frags to prevent buffer overflow (CRITICAL-1) */
    if (frag->total_frags == 0 || frag->total_frags > MAX_FRAGMENTS) {
        stats_corrupted_frames++;
        return -1;
    }

    /* Security: Validate fragment index is within bounds (CRITICAL-1) */
    if (frag->frag_index >= MAX_FRAGMENTS) {
        stats_corrupted_frames++;
        return -1;
    }

    if (frag->frag_index >= frag->total_frags) {
        stats_corrupted_frames++;
        return -1;
    }

    /* Find or create reassembly entry */
    reassembly_entry_t *entry = find_or_create_entry(frag->frag_id, frag->total_frags);
    if (!entry) {
        return -1;
    }

    /* Check if already received this fragment (bitmask only works for ≤8 fragments) */
    if (frag->total_frags <= 8 && (entry->received_mask & (1 << frag->frag_index))) {
        /* Duplicate fragment, ignore */
        return 0;
    }

    /* Copy fragment data */
    size_t offset = frag->frag_index * FRAG_MAX_PAYLOAD;
    if (offset + frag->payload_len > MAX_FRAME_SIZE) {
        fprintf(stderr, "Reassembly overflow: %zu + %d > %d\n",
                offset, frag->payload_len, MAX_FRAME_SIZE);
        stats_corrupted_frames++;
        remove_entry(entry);
        return -1;
    }

    memcpy(entry->data + offset, frag->payload, frag->payload_len);

    /* Update tracking */
    if (frag->total_frags <= 8) {
        entry->received_mask |= (1 << frag->frag_index);
    }

    /* Update total length (track highest offset) */
    size_t end = offset + frag->payload_len;
    if (end > entry->total_len) {
        entry->total_len = end;
    }

    /* Check if all fragments received */
    /* Validate total_frags before bitmask calculation to prevent UB if total_frags > 31 */
    if (frag->total_frags <= 8) {
        int expected_mask = (1 << frag->total_frags) - 1;
        if (entry->received_mask == expected_mask) {
            /* Frame complete! */
            memcpy(complete_frame, entry->data, entry->total_len);
            *frame_len = entry->total_len;
            
            stats_complete_frames++;
            remove_entry(entry);
            return 1;
        }
    }

    /* Still waiting for more fragments */
    return 0;
}

int reassembly_cleanup_expired(int timeout_sec)
{
    time_t now = time(NULL);
    int cleaned = 0;

    reassembly_entry_t **ptr = &reassembly_list;
    while (*ptr) {
        reassembly_entry_t *entry = *ptr;
        
        if (now - entry->first_seen >= timeout_sec) {
            /* Timeout expired */
            stats_timeout_frames++;
            *ptr = entry->next;
            free(entry);
            cleaned++;
        } else {
            ptr = &entry->next;
        }
    }

    return cleaned;
}

void reassembly_get_stats(int *total_entries, unsigned long *complete_frames,
                         unsigned long *timeout_frames, unsigned long *corrupted_frames)
{
    /* Count active entries */
    int count = 0;
    reassembly_entry_t *entry = reassembly_list;
    while (entry) {
        count++;
        entry = entry->next;
    }

    if (total_entries) *total_entries = count;
    if (complete_frames) *complete_frames = stats_complete_frames;
    if (timeout_frames) *timeout_frames = stats_timeout_frames;
    if (corrupted_frames) *corrupted_frames = stats_corrupted_frames;
}
