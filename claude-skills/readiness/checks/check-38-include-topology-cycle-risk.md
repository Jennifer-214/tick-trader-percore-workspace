---
type: skill-check
check_id: 38
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Include topology cycle risk (meta-discipline M4 / Pillar B7)
established: 2026-05-18
---

# /readiness Check 38 — Include topology cycle risk (meta-discipline M4 / Pillar B7)

**When this fires:** plan body proposes new cross-directory include relationship (`MemHeaders/` ↔ `CoreFrameworks/` ↔ `ML_Headers/`).

**What to verify:** map current include graph for the affected files (`rg "#include" <files>`). Inspect new include edges proposed by migration. Compute: any cycle in resulting graph? Mitigations available if cycle detected (forward declarations / template parameterization / header split).

**Verdict:** PASS if no cycle OR cycle-mitigation specified; GAP if new include edge introduces cycle without mitigation note.

**Cross-references:** `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` § B7. `DESIGN_PHILOSOPHY.md` § 11.5 M4.

**Effort:** 5-10 min per audit (one grep per affected file).
