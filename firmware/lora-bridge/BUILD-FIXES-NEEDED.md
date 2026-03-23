# Build Fixes Required for Next PR

These fixes were discovered during deployment testing on Raspberry Pi and need to be applied to main branch.

## Fix 1: Missing sys/types.h in tap.h

**File:** `firmware/lora-bridge/tap.h`

**Issue:**
```
tap.h:46:1: error: unknown type name 'ssize_t'; did you mean 'size_t'?
```

**Root cause:** `ssize_t` type not defined (needs `<sys/types.h>`)

**Fix applied on Pi:**
```diff
#ifndef TAP_H
#define TAP_H

#include <stddef.h>
+#include <sys/types.h>
```

**Line:** After line 7 (after `#include <stddef.h>`)

---

## Fix 2: Signedness comparison warning in fragment.c

**File:** `firmware/lora-bridge/fragment.c`

**Issue:**
```
fragment.c:134:13: error: comparison of integer expressions of different signedness: 'size_t' {aka 'long unsigned int'} and 'int' [-Werror=sign-compare]
```

**Root cause:** Comparing `size_t len` with `int` expression

**Fix applied on Pi:**
```diff
-    if (len < FRAG_HEADER_SIZE + frag->payload_len) {
+    if (len < (size_t)(FRAG_HEADER_SIZE + frag->payload_len)) {
```

**Line:** Line 134

---

## Verification

Both fixes tested on:
- **Platform:** Raspberry Pi 4 (arm64, Debian Bookworm)
- **Compiler:** gcc 12.2.0 with `-Wall -Wextra -Werror`
- **Result:** Clean build, no warnings

## Next Steps

1. Create PR with these two fixes
2. Title: "Fix build warnings on Raspberry Pi (ssize_t and signedness)"
3. Apply to main branch
4. Close this issue after merge

---

**Discovered:** 2026-03-22 18:37 AKDT
**Tested:** Raspberry Pi 4, arm64
**Status:** Verified working
