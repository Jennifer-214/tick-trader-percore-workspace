---
type: skill-check
check_id: 23
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Latency accountability
established: 2026-05-18
---

# /readiness Check 23 — Latency accountability (v5.14.1.F+)

**Trigger:** plan adds code on hot path (≤500ns p99), slow path (≤100µs p99),
OMS drainer, or producer fan-out.

**Verdict:**
- **PASS** — plan includes path classification (hot/slow/OMS/producer/boot/training)
  + cost estimate (ns) + branchless analysis if hot + HOT_PATH_CHANGELOG.md
  entry committed in same ship (or "boot/training only" justification)
- **DRIFT-RISK** — latency-impact code without analysis. Per CLAUDE.md
  item 17, this is required discipline.

**Procedure:**
1. **Identify path:** hot / slow / OMS drainer / producer fan-out —
   consult `DOCS/HOT_PATH_CHANGELOG.md` cadence-tier classification for
   the current canonical function set.
2. **Verify analysis present:** path classification, cost estimate, branchless
   discussion if hot.
3. **Verify HOT_PATH_CHANGELOG entry planned/included:**
   - Hot path: ALWAYS required
   - Slow path: required if ≥10ns/cycle
   - Boot/training: NO entry; plan should explicitly note
4. **Cumulative-cost sanity check:** sum recent ships' per-cycle costs;
   flag if approaching 10% of path budget.

**Anti-pattern caught (v5.14.1.F 2026-05-09):** dispatcher add in slow path
without latency note. Caught by Caramel's "ensure we aren't adding unaccounted
latency" question. Check 23 mechanizes the prompting.

**Cross-references:**
- `CLAUDE.md` item 17 — latency-additions are tracked
- `DOCS/HOT_PATH_CHANGELOG.md` — running ledger
- `/latency-track` skill — emits draft changelog entries

**Effort:** 3-5 min per audit.
