# r3LAY Context

**Project:** TUI AI research assistant (I OWN THIS)
**Location:** `/Users/lorp/.openclaw/workspace/r3LAY`
**Status:** Active development

---

## Project-Specific Axioms

**[R3LAY-001]** Target vertical domains (automotive, electronics, software, DIY)
> Deep domain focus beats broad coverage

**[R3LAY-002]** Hybrid RAG architecture (local LLM + curated knowledge)
> Combine AI intelligence with structured domain knowledge

**[R3LAY-003]** Terminal-native first, GUI optional
> CLI tools iterate faster than GUI frameworks

---

## Key Decisions

**2026-03-05:** Decided to support Subaru SSM1 protocol for EJ22 diagnostics
- Complements GARAGE-BUDDY historical tracking
- Real-time + historical = complete workshop awareness

**2026-03-05:** Built NES/SNES ROM analyzer as r3LAY module
- Terminal aesthetic, zero dependencies
- Fan translation workflow support

---

## Patterns

**Complementary Tool Pairs:**
- Historical tracking (GARAGE-BUDDY) + Real-time monitoring (OBD2-TUI)
- Catalog tools + Live analysis tools
- Each reinforces the other

**Constraint-Driven Design:**
- GameBoy palette (4 colors) forces interesting patterns
- OBD2 2Hz update rate → responsive UI design challenge
- Terminal-only → forces clarity, no hiding behind visuals

---

## Active Work

- [ ] Automotive module (OBD2 + diagnostics)
- [ ] Retro gaming module (ROM analysis, save management)
- [ ] Electronics module (parts catalog, datasheets)

---

_This context is loaded when working on r3LAY. Global axioms in MEMORY.md still apply._
