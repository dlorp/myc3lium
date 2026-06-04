/**
 * SLIP (Serial Line Internet Protocol) encoder/decoder — RFC 1055
 *
 * Byte-compatible with pi-slip-daemon.c on the Raspberry Pi side.
 * Constants and framing logic match exactly so both ends can exchange
 * Ethernet frames over a 921600 baud USB serial link.
 */

#pragma once

#include <cstddef>
#include <cstdint>

/* RFC 1055 framing constants — must match pi-slip-daemon.c */
constexpr uint8_t SLIP_END     = 0xC0;
constexpr uint8_t SLIP_ESC     = 0xDB;
constexpr uint8_t SLIP_ESC_END = 0xDC;
constexpr uint8_t SLIP_ESC_ESC = 0xDD;

/* Buffer sizing — matches Pi daemon TAP_MTU */
#ifndef SLIP_MTU
#define SLIP_MTU 1560
#endif

/* Worst case: every byte escaped + 2 END markers */
constexpr size_t SLIP_MAX_ENCODED = (SLIP_MTU * 2) + 2;

/**
 * SLIP decoder state machine.
 *
 * Feed bytes one at a time via decode_byte(). When a complete frame
 * is available, decode_byte() returns 1 and the frame is in buf[0..len-1].
 * After consuming the frame, call reset() before feeding more bytes.
 */
struct SlipDecoder {
    uint8_t buf[SLIP_MTU];
    size_t  len       = 0;
    bool    in_escape = false;
    bool    dropping  = false;  /* M5: discard until next SLIP_END after overflow */

    void reset();

    /**
     * Feed one byte to the decoder.
     * @return  1  complete frame ready in buf[0..len-1]
     *          0  need more bytes
     *         -1  frame too large (entered drop mode)
     */
    int decode_byte(uint8_t byte);
};

/**
 * SLIP-encode a raw frame into an output buffer.
 *
 * @param frame   Raw frame data (Ethernet frame from TAP)
 * @param len     Length of frame in bytes
 * @param out     Output buffer (must be at least SLIP_MAX_ENCODED bytes)
 * @return        Number of bytes written to out
 */
size_t slip_encode(const uint8_t* frame, size_t len, uint8_t* out);
