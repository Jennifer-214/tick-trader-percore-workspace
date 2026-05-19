---
type: skill-check
check_id: 37
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Transitional state coexistence budget (meta-discipline M4 / Pillar B3)
established: 2026-05-18
---

# /readiness Check 37 — Transitional state coexistence budget (meta-discipline M4 / Pillar B3)

**When this fires:** plan body proposes multi-step migration where SOURCE pattern + TARGET pattern co-exist temporarily (e.g., legacy walker + new framework walker both alive between Step N and Step M).

**What to verify:** plan body annotates "transitional state allowed; size budget = N KB; resolves at Step <N>" explicitly. Estimate peak struct size or memory footprint during coexistence. Verify ≤25KB per struct (suggested ceiling for boot-time structs) OR ≤100KB program-wide.

**Verdict:** PASS if annotation + budget present; GAP if implicit coexistence without budget annotation.

**Cross-references:** `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` § B3. `DESIGN_PHILOSOPHY.md` § 11.5 M4.

**Effort:** 3-5 min per audit.
