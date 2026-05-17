# /dust report — 2026-05-17 — cfg infrastructure scoped to `.B` fold-in

**Scope:** 11 cfg-adjacent files (8.8k LOC total). Focus areas: rotting comments referencing pre-Path γ patterns, oversized fns, copy-paste, dead code, multi-site change leaks adjacent to `.B`'s parallel-registry consolidation work.

**Verdict: YELLOW** — notable dust to triage. ~5 candidates ride along cheaply at `.B` (already in surface area). 2 candidates warrant dedicated cleanup ship.

---

## Top-line summary

| Fold strategy | Count | Effort |
|---|---|---|
| **NATURAL fold at `.B`** (already in scope) | 5 | +0-0.5 h (text edits riding along) |
| **CHEAP fold at `.B`** (adjacent; small extension) | 3 | +0.5-1 h |
| **Deferred to dedicated cleanup ship** | 4 | ~2-3 h focused |

---

## CRITICAL — none.

## HIGH

### H1 — `HAS_SIDE_EFFECT` legacy alias 38 sites across codebase, comment says "remove at v5.15.5.F.4d codification"
**File:** `CoreFrameworks/CfgFieldRegistry.hpp:152-156` (alias declaration) + 38 use sites (`rg HAS_SIDE_EFFECT`)
- Comment: "Alias retained for 1 ship transition; remove at v5.15.5.F.4d codification."
- We are now AT `.F.4d.1.B`; `.F.4d` shipped 2026-05-16 WITHOUT removing the alias.
- 29 sites in `CfgFieldRegistry.hpp` + 5 in `ControllerConfig.hpp` + 4 elsewhere.
- **Action:** mechanical `replace_all HAS_SIDE_EFFECT → MANUAL_PARSER` across the 38 sites; delete alias line; remove the "remove at v5.15.5.F.4d codification" comment.
- **LOC delta:** ~-1 (alias line); 38 site renames are zero-LOC.
- **Risk:** LOW — semantic-identical rename via `#define HAS_SIDE_EFFECT = MANUAL_PARSER`.
- **`.B` fit:** NATURAL fold — `.B` already touches `FOREACH_STAMP_BOUND_CFG` removal which involves comment-text cleanup at ~8-10 sites; HAS_SIDE_EFFECT cleanup is the same shape (legacy alias hygiene that should land at the codification milestone).

### H2 — Duplicate eligibility-criteria comment in `MlCfgFlagRegistry.hpp`
**File:** `ML_Headers/MlCfgFlagRegistry.hpp:32-34`
```
// CFG-FLAG ELIGIBILITY (per TECH_DEBT-023): all 7 entries below pass all 5 criteria.
//======================================================================================================
// CFG-FLAG ELIGIBILITY (per TECH_DEBT-023): all 7 entries below pass all 5 criteria.
```
- Two adjacent header comment lines stating the same content (one before the close-bar `===`, one after).
- Plus count is stale: comment says "all 7 entries" but registry now has 12 rows (since `.A.5` PER_HORIZON_BARRIER_BLEND addition).
- **Action:** delete the duplicate + update "7" → "12" + reference: `.A.5/.F.4d` extensions.
- **LOC delta:** -2.
- **Risk:** zero.
- **`.B` fit:** NATURAL fold — `.B` already touches `FOREACH_ML_CFG_FLAG` 5→6 sig migration at this file.

## MED

### M1 — Stale "v5.14.8.0 / v5.14.7" version refs in `StampBoundModelConstRegistry.hpp` (~22 sites)
**File:** `ML_Headers/StampBoundModelConstRegistry.hpp` (multiple lines)
- File header (line 6) `[STAMP-BOUND MODEL-CONST REGISTRY — v5.14.8.0]` — version dated; current ship is `.F.4d.1`.
- Body comments reference `v5.14.8.A.0.b`, `v5.14.8.A.merged.4`, `v5.14.8.D`, `v5.14.9.D`, `v5.14.9.F.2`, `v5.14.10.B`, `v5.14.11.C` — 22 version-tag refs total.
- Most are LEGITIMATE archaeology (root-cause history, e.g., "v5.14.9.F.2 — confidence_composite_enabled migrated to ml_cfg_flags bitmap"). Don't strip these.
- BUT line 43 `legacy stamps means the parser leaves new fields untouched on a v5.14.7 stamp` is stale guidance — current legacy floor is v5.15.4 per drift-check gates.
- **Action:** leave archaeology comments alone; update file header version tag to current; update "v5.14.7 stamp" → "v5.15.4- stamp" (matches gate language in CfgDriftCheckRegistry.hpp:282-296).
- **LOC delta:** ~0 (text-only edits at 2-3 sites).
- **Risk:** zero.
- **`.B` fit:** CHEAP fold — this file isn't in `.B`'s primary edit scope (only crossed via "delete manual POST_CFG entry for `bandit_blend_ratio`" per `.B` Step 6.2 Item 4). Ride along the deletion edit with a header-tag refresh.

### M2 — `STAMP_MODEL_CONST_AUTOPOPULATE` QUARANTINED dead-macro keeps ~85 LOC live
**File:** `ML_Headers/StampBoundModelConstRegistry.hpp:651-758`
- `STAMP_MODEL_CONST_AUTOPOPULATE` quarantined v5.15.3.A (PARITY-022); macro body emits `static_assert(false)` to block future callers.
- But the `STAMP_AUTOPOPULATE_SET_HAS_<group>` dispatcher macros (8 macros, lines 708-716) + `STAMP_EMIT_CHECK_HAS_<group>` (lines 723-731) + `STAMP_PARSER_SET_HAS_<group>` (lines 740-747) + `STAMP_MODEL_CONST_AUTOPOPULATE_ONE` (lines 749-758) — all defined.
- Are SET_HAS / EMIT_CHECK / PARSER_SET genuinely dead? Spot-check shows they ARE used by parser/emit walker in ModelInference.hpp (`STAMP_PARSER_SET_HAS_*` + `STAMP_EMIT_CHECK_HAS_*`). Only `STAMP_AUTOPOPULATE_SET_HAS_*` + `STAMP_MODEL_CONST_AUTOPOPULATE_ONE` are tied to the quarantined macro.
- **Action:** trace `_AUTOPOPULATE_SET_HAS_*` + `_AUTOPOPULATE_ONE` usage; if zero callers (likely — top-level macro is quarantined), delete.
- **LOC delta:** -25 to -35 if dead.
- **Risk:** LOW — `static_assert(false)` already blocks the parent macro; supporting infrastructure can't be invoked from outside.
- **`.B` fit:** OUT OF SCOPE for `.B`. Defer to dedicated cleanup ship OR roll into `.F.4f` (already queued for `.F.4c.3` deferred scope cleanup).

### M3 — `ControllerConfig_Load` is 1158 lines (FN bloat)
**File:** `CoreFrameworks/ControllerConfig.hpp:2010-3168`
- Single fn carries: 38 LOC inline-comment-stripping + registry-driven parser dispatch (~150 LOC) + manual `CFG_PARSE_*` legacy parser block + per-core override parser block + per-core string-field branches + boot validation/normalization calls.
- Exceeds CLAUDE.md test-file discipline rule (>5k lines / >100 sections must split BEFORE adding more — same principle to fns).
- Adjacent: `ControllerConfig_Default` is also 451 LOC; `_NormalizeForMode` smaller (~30) but reachable cleanup.
- **Action:** decompose into helper fns: `parse_line_strip_comments(char*)`, `parse_registry_dispatch(cfg, key, val)`, `parse_legacy_block(cfg, key, val, ...)`, `parse_per_core_overrides(cfg, key, val)`. Each ~150-300 LOC.
- **LOC delta:** ~0 net (re-organization); cyclomatic complexity drops significantly.
- **Risk:** MED — load-bearing parser; test coverage is good but boundary discipline matters.
- **`.B` fit:** OUT OF SCOPE. Substantial refactor; warrants dedicated cleanup ship + audit.

### M4 — Copy-paste cohort-gate `BITMAP_IS_SET(cfg.gate_cfg_flags, ...)` pattern across 4 files
**Files:**
- `CfgDerivedInferenceCfgRegistry.hpp` — 13 `FPN_ToDouble(cfg.X)` instances
- `StampBoundCfgRegistry.hpp` — 23 instances  
- `CfgDriftCheckRegistry.hpp` — 14 instances
- 29 cross-file `MASK_*` references for the 4 main gate-flag bits.
- The same `(STAMP_HAS(*h, X) && BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED))` shape appears 10+ times across the cohort.
- **Action:** extract per-cohort gate-when helper: `inline bool drift_gate_bandit_enabled(const ControllerConfig<F>& cfg, const ModelHandle<F>& h)`. `.B`'s Phase 11 (per-cohort drift-check gate_when expressions via β4 sidecar) is ALREADY the structural fix for this — sparse `FOREACH_DRIFT_GATE` dispatched via fn-pointer table per H20 Pattern 1.
- **Action:** verify `.B`'s β4 sidecar pattern fully closes this multi-site change leak; ensure none of the 24 cohort rows fall outside the 6 cohort gates.
- **LOC delta:** ~0 net (collapsed into β4 sidecar already in `.B` scope).
- **Risk:** zero (it's what `.B` is doing).
- **`.B` fit:** NATURAL fold — already in primary scope; this finding VALIDATES that `.B`'s β4 design covers the cleanup surface.

## LOW

### L1 — `MlCfgFlagRegistry.hpp` comment block has dead pre-`.F.5+` reference
**File:** `ML_Headers/MlCfgFlagRegistry.hpp:45`
```
// Tuple: X(NAME, legacy_field, doc)
```
- Then line 51 immediately says: `// Tuple: X(NAME, legacy_field, display_label, section, doc)  [5-col v5.14.9.F.5+]`
- The first comment is the obsolete 3-col tuple shape; second is the current 5-col. The 3-col line is dead documentation that confuses readers.
- **Action:** delete line 45.
- **LOC delta:** -1.
- **Risk:** zero.
- **`.B` fit:** NATURAL fold — `.B` is migrating 5→6 sig at this file; will touch this comment block anyway.

### L2 — `CfgDerivedInferenceCfgRegistry.hpp` references "section 2a" + "manual ~20 LOC" — now historical
**File:** `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:46` + `:93` + `:127`
- Header comments reference `StampHelper.hpp section 2a at lines ~168-187` (manual block that was replaced by INFERENCE_CFG_AUTOPOPULATE at `.A.7`).
- At HEAD post-`.A.7`, those lines are no longer "manual" — they ARE the AUTOPOPULATE call. Comments still frame the registry as "replaces manual section".
- Once `.B` empties out `FOREACH_STAMP_BOUND_CFG`, this file remains a sister registry but the "replaces manual" framing reads odd to fresh readers.
- **Action:** light edit — drop "replaces ~20 LOC of manual section 2a" since section 2a is now structural (the AUTOPOPULATE call itself).
- **LOC delta:** -3 to -5.
- **Risk:** zero.
- **`.B` fit:** NATURAL fold — `.B`'s consumer-comment refresh sweep at Phase 12.

### L3 — `CFG_DRIFT_AUTOPOPULATE` mentioned in `.B` plan as "NEW" but pattern already exists structurally
- Spec-mention: `.B` Item Q3.B describes `CFG_DRIFT_AUTOPOPULATE` as new companion macro sister to `STAMP_CFG_AUTOPOPULATE` + `INFERENCE_CFG_AUTOPOPULATE`.
- The pattern shape is the 3rd application of `autopopulate-pattern-for-production-caller-class.md` (per `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:24-27` history comment).
- **Action:** verify `.B`'s `CFG_DRIFT_AUTOPOPULATE` lands the macro at `MemHeaders/CfgDriftCheckRegistry.hpp` (file-level homing decision) or at `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp` adjacent to INFERENCE_CFG_AUTOPOPULATE (cohesion). Suggest the latter for sister-pattern locality.
- **LOC delta:** structural decision; affects organization, not LOC.
- **Risk:** zero.
- **`.B` fit:** NATURAL — `.B`'s Step 8 lands this macro. Document the homing decision in plan body.

### L4 — `StampBoundCfgRegistry.hpp:180-186` reverted-attempt comment block clutters header
**File:** `ML_Headers/StampBoundCfgRegistry.hpp:180-186`
- 7-line comment block explaining a REVERTED migration attempt (4 entries moved to MODEL_CONST_POST_CFG).
- After `.B` empties FOREACH_STAMP_BOUND_CFG entirely, this archaeology comment in a dead registry adds zero value.
- **Action:** delete entire registry file at `.B` empty-out → comment evaporates.
- **LOC delta:** -267 (entire file).
- **Risk:** verify `.B` plan empties out via `#define FOREACH_STAMP_BOUND_CFG(X)` or via file deletion. Plan body line 43 says "fully deleted" — confirm deletion includes the source file.
- **`.B` fit:** NATURAL — already in scope per `.B` Step 12.

---

## Verdict

**YELLOW.**

Cheap fold-in at `.B` (TOTAL ~1.5-2 h extra):
1. **H1** HAS_SIDE_EFFECT → MANUAL_PARSER rename (38 sites) — NATURAL fold; ride the comment-cleanup sweep
2. **H2** Duplicate eligibility-criteria comment in MlCfgFlagRegistry.hpp — NATURAL fold
3. **M2 partial** Verify dead `_AUTOPOPULATE_SET_HAS_*` / `_AUTOPOPULATE_ONE` macros — if confirmed dead, delete (saves ~25 LOC)
4. **L1** Drop obsolete 3-col tuple comment in MlCfgFlagRegistry.hpp — NATURAL fold
5. **L2 + L3 + L4** Comment-text cleanup sweep at consumer-comment refresh phase — NATURAL fold

Deferred (dedicated cleanup ship; recommend rolling into `.F.4f` queued cleanup):
- **M2 full** STAMP_MODEL_CONST_AUTOPOPULATE quarantine scrub (verify + delete supporting dispatchers)
- **M3** `ControllerConfig_Load` decomposition (1158 LOC; high-risk refactor)
- **M1** StampBoundModelConstRegistry version-tag refresh (modest scope; better in dedicated archaeology pass)

**`.B` blast-radius caveat:** the wider-scope `.B` amendment under consideration is the right shape. M4 finding VALIDATES that `.B`'s β4 sidecar covers the BITMAP_IS_SET cohort-gate copy-paste; `.B`'s legacy registry empty-out (L4) is the canonical cleanup. The dust is NOT distinct work from `.B`; it IS `.B` plus a few text edits.

**Cross-ref:** sister to `/merge-scan` finding (merge-scan-2026-05-17-v5.15.5.F.4d.1.B.md) which catches the structural opportunities; this report catches the residual hygiene that rides along.
