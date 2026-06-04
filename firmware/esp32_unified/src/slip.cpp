/**
 * SLIP encoder/decoder implementation — RFC 1055
 *
 * Mirrors the framing logic in pi-slip-daemon.c exactly:
 * - Leading END, data (with ESC sequences), trailing END
 * - Overflow drops until next END (M5 resync behavior)
 * - Protocol violation on bad escape: pass byte through
 */

#include "slip.h"

#include <cstring>

void SlipDecoder::reset()
{
    len = 0;
    in_escape = false;
    /* Note: dropping is NOT cleared here — only SLIP_END clears it */
}

int SlipDecoder::decode_byte(uint8_t byte)
{
    if (byte == SLIP_END) {
        /* END always resyncs — stop dropping on frame boundary */
        dropping = false;
        if (len > 0) {
            return 1;  /* Frame complete */
        }
        /* Empty frame (inter-frame END), ignore */
        return 0;
    }

    /* M5: Discard bytes until next SLIP_END after overflow */
    if (dropping) {
        return 0;
    }

    if (byte == SLIP_ESC) {
        in_escape = true;
        return 0;
    }

    if (in_escape) {
        in_escape = false;
        if (byte == SLIP_ESC_END) {
            byte = SLIP_END;
        } else if (byte == SLIP_ESC_ESC) {
            byte = SLIP_ESC;
        }
        /* else: protocol violation, pass through (matches Pi behavior) */
    }

    if (len >= sizeof(buf)) {
        /* Frame too large — enter drop mode until next SLIP_END */
        len = 0;
        in_escape = false;
        dropping = true;
        return -1;
    }

    buf[len++] = byte;
    return 0;
}

size_t slip_encode(const uint8_t* frame, size_t len, uint8_t* out)
{
    /* Refuse to encode frames larger than MTU — caller must check */
    if (len > SLIP_MTU) {
        return 0;
    }

    size_t pos = 0;

    /* Leading END (flushes any line noise on receiver) */
    out[pos++] = SLIP_END;

    for (size_t i = 0; i < len; i++) {
        switch (frame[i]) {
        case SLIP_END:
            out[pos++] = SLIP_ESC;
            out[pos++] = SLIP_ESC_END;
            break;
        case SLIP_ESC:
            out[pos++] = SLIP_ESC;
            out[pos++] = SLIP_ESC_ESC;
            break;
        default:
            out[pos++] = frame[i];
            break;
        }
    }

    /* Trailing END */
    out[pos++] = SLIP_END;

    return pos;
}
