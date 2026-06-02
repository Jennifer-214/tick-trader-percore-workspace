---
type: skill-check
check_id: 25
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: TECH_DEBT.md surface-area scan
established: 2026-05-18
---

# /readiness Check 25 — TECH_DEBT.md surface-area scan (v5.14.2.E+)

**When this fires:**
Before declaring a ship complete, OR before starting a ship plan, scan
`DOCS/TECH_DEBT.md` for entries whose surface area overlaps with the
ship's files-touched.

**What to verify:**
1. **Read `DOCS/TECH_DEBT.md`** entries (workspace symlink in engine repo).
2. **For each TECH_DEBT entry whose `Surface:` field overlaps with the
   ship's files-touched:** decide explicitly:
   - **Address now** — bundle the cleanup into this ship + close the entry
   - **Refresh entry** — update cost estimate / trigger / context if stale
   - **Defer with rationale** — confirm trigger isn't met; ship comment
     references the entry
   - **Classify by subsumption (opportunistic closure, 2026-06-02):** of the matching entries, CLOSE the ones this ship SUBSUMES / trivially-completes (≈0 marginal cost — built the primitive / already in the surface); cross-link + leave-tracked the ones merely ADJACENT (a distinct deliverable + test + trigger). Discriminator = marginal-cost, NOT surface-adjacency. See `feedback_opportunistic_tech_debt_closure`.
3. **DO NOT silently leave entries stale** (e.g., old cost estimate that
   no longer reflects current code).
4. **Auto-write contract:** if Check 25 surfaces a NEW deferral candidate
   (not yet in TECH_DEBT.md), agent MUST add it now (don't defer to
   "operator copies after review"). Same discipline as PARITY_ISSUES.md
   auto-write.

**Anti-pattern caught (v5.14.2.E 2026-05-09):** Caramel: "what if I forget
about that stuff, like doesn't addressing the deferred items now make
future maintenance easier?" Pre-Check-25, deferred items hid in code
comments / postmortems / chat memory + got forgotten. TECH_DEBT.md +
Check 25 surfaces them at every ship.

**Cross-references:**
- `DOCS/TECH_DEBT.md` (the ledger)
- `DOCS/PARITY_ISSUES.md` (sister ledger; different class)
- `CLAUDE.local.md` auto-write contract

**Effort:** 2-5 min per audit (longer if many TECH_DEBT entries match the
ship's surface).
