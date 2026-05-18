# /merge-scan re-sweep — v5.15.5.F.4d.1.B.3 (Legacy empty-out) v1.9 FULL — 2026-05-17

**Plan body audited:** `subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.9 DRAFT (FULL)
**Engine HEAD:** `9b62a72` (v5.15.5.F.4d.1.B.2 ship close)
**Scope:** scoped (focused on v1.3 → v1.9 NEW scope additions; codebase cross-reference for verification)
**Prior audit:** `plan_checks/merge-scan-2026-05-17-v5.15.5.F.4d.1.B.3.md` (against v1.2; GREEN; Decision E.2 recommendation)
**Skill version:** post-2026-05-14 uniform parameter contract; Stage 0 DESIGN_PHILOSOPHY preload § 4 + § 7
**Verdict:** **GREEN with 2 MINOR merge candidates (Focus areas 1 + 7).** v1.9-added scope is substantively audit-clean on reuse-merge concerns. Decision E.2 implementation correctly identified at HEAD. Iteration-spiral termination achieved at v1.9 final sweep.

---

## Summary table — per-focus-area verdict

| Focus area | Sites added / scope | Sites eliminated | Verdict | Notes |
|---|---|---|---|---|
| 1. Step 0.5d framework walker extension | ~30-40 LOC × 4 sub-steps = ~120-160 LOC for FOREACH_GATE_CFG_FLAG path (4 walker bodies copy-pattern from FOREACH_ML_CFG_FLAG) | Closes Class 32 model-state instances (5 fields); enables bit-add for `barrier_gate_enabled` | **YELLOW — 1 minor reuse candidate** | See § 1 — shared walker abstraction over N bitmap-flag registries possible but defers PROPORTIONATELY |
| 2. Step 1.6.6.b 15-row STAMP-side rename | 15 mechanical replace_all-safe edits (~30-60 min) | 15 prefix-asymmetry instances at drift-check consumer | **GREEN — no new merge** | Per-row rename IS the right shape; no shared helper opportunity |
| 3. Decision F (F.2) 15-entry parser back-compat | Closed-set X-macro `FOREACH_LEGACY_PREFIXED_KEY` ~25-30 LOC | 15 inline strcmp branches that would otherwise exist | **GREEN — INLINE MERGE confirmed** | Per `canonical-sister-extension-discipline.md` § INLINE MERGE; correct verdict in plan body |
| 4. Step 1.6.8 stamp_model.sh tooling migration | 6-7 mechanical sed replacements in bash | 6 wire-key prefix surfaces (matches engine emit) | **GREEN — no new merge** | Per-line sed/edit IS the right shape; no shared bash function reuse opportunity |
| 5. Step 1.6.2 v1.6 expansion 5 NEW fields | 5 metadata_flags bit-adds at CfgFieldRegistry + GateCfgFlagRegistry | 5 Class 32 model-state instances | **GREEN — already merged** | 5 fields integrate cleanly with original 10; consumer migration enumerated together |
| 6. Cross-cutting per-field replace_all loop (lines 374-385) | 15-field bash for-loop documented inline | N/A (procedure capture) | **GREEN — appropriate as bash procedure** | Codifying as separate `tools/migrate_legacy_prefix.sh` would be over-architecture for 1-shot use |
| 7. 4 new memories + 4 going-forward rules + Checks 31-35 + 5 skill amendments | ~10 ledger amendments at ship close | Methodology gaps closed (4 pillars) | **YELLOW — 1 minor merge candidate** | See § 7 — Checks 31-35 consolidation opportunity + skill amendment cross-references |

**Top-3 ship-level merge candidates** (none HIGH risk; all PROPORTIONATE per `feedback_proportionate_response_to_audit_findings`):

1. Focus area 1 — Inner-callable shared walker abstraction over N bitmap-flag registries (DEFER candidate; see § 1)
2. Focus area 7 — `/readiness` Checks 31-35 → grouped audit composite verb (refinement candidate; see § 7)
3. Decision E.2 — implementation at v1.9 verified correct (no change needed; see § 8)

---

## 1. Step 0.5d framework walker extension — YELLOW with PROPORTIONATE deferral

### 1.1 Sister registry surface confirmed

Walked the FOREACH_*_FLAG family at HEAD:

| Registry | File | Storage | metadata_flags col? | STAMP_BOUND_CFG_DERIVED usage |
|---|---|---|---|---|
| `FOREACH_ML_CFG_FLAG` | `ML_Headers/MlCfgFlagRegistry.hpp:58` | uint16_t | **YES (6-col v5.15.5.F.4d.1.B.2+)** | 5 rows use bit (PER_HORIZON_BARRIER_BLEND adds at this ship per Step 1.6.2 v1.5 entry 5) |
| `FOREACH_GATE_CFG_FLAG` | `CoreFrameworks/GateCfgFlagRegistry.hpp:46` | uint8_t | NO (5-col v5.14.9.F.5+) | 0 rows; v1.9 Step 0.5d adds dispatch for `barrier_gate_enabled` |
| `FOREACH_LIFECYCLE_CFG_FLAG` | `CoreFrameworks/LifecycleCfgFlagRegistry.hpp:46` | uint8_t | NO (5-col) | 0 rows; no stamp-bound flags currently |
| `FOREACH_RISK_CFG_FLAG` | `CoreFrameworks/RiskCfgFlagRegistry.hpp:25` | uint8_t | NO | 0 rows |
| `FOREACH_OPS_CFG_FLAG` | `CoreFrameworks/OpsCfgFlagRegistry.hpp:39` | uint8_t | NO | 0 rows |
| `FOREACH_CORE_STATE_FLAG` | `MemHeaders/CoreStateFlagRegistry.hpp:66` | (runtime state) | N/A | N/A — runtime not cfg-bound |
| `FOREACH_OMS_STATE_FLAG` | `MemHeaders/OmsStateFlagRegistry.hpp:100` | (runtime state) | N/A | N/A — runtime not cfg-bound |
| `FOREACH_PER_ARM_FLAG` | `ML_Headers/PerArmFlagRegistry.hpp:86` | (per-bandit-arm state) | N/A | N/A — runtime not cfg-bound |
| `FOREACH_EZOO_INIT_FLAG` | `ML_Headers/EzooInitFlagRegistry.hpp:79` | (ezoo init state) | N/A | N/A — runtime not cfg-bound |

**Two CFG_FLAG-family registries are stamp-eligible: ML_CFG_FLAG (already dispatching) + GATE_CFG_FLAG (Step 0.5d adds dispatch).**

### 1.2 Walker body parallelism at HEAD

`CfgGateRegistry.hpp:296-305` (`X_STAMP_CFG_POPULATE_ML_CFG_FLAG`) + `:352-360` (`X_DRIFT_CHECK_ML_CFG_FLAG`) — TWO walker bodies, 8-9 lines each — identical shape modulo MASK prefix + cfg.<flags>_field + the row-tuple arity.

**v1.9 Step 0.5d (sub-steps 0.5d.a, 0.5d.b, 0.5d.d) proposes copying both walker bodies for GATE_CFG_FLAG.** That is:
- 0.5d.a: copy `X_STAMP_CFG_POPULATE_ML_CFG_FLAG` → `X_STAMP_CFG_POPULATE_GATE_CFG_FLAG` (~10 LOC)
- 0.5d.d: copy `X_DRIFT_CHECK_ML_CFG_FLAG` → `X_DRIFT_CHECK_GATE_CFG_FLAG` (~10 LOC)
- AND populate_inference_cfg counterpart for both — 4 walker bodies total

**Total Step 0.5d LOC: ~40-60 LOC (4 walker bodies × ~10 LOC each + parser dispatch at 0.5d.b)** vs v1.9 plan body's "~30 LOC" v1.6 estimate or "~120-160 LOC" v1.7 honest revision.

### 1.3 Reuse-merge candidate — Inner-callable shared walker (PROPORTIONATE DEFER)

**Shape:** The 4 walker bodies (per-core, global, ML_CFG_FLAG × 3 functions = populate_inf / populate_stamp / drift_check) share the SAME outer structure (`#define X_…(args); FOREACH_<REGISTRY>(X_…); #undef X_…`). The ONLY thing that varies per walker is the inner action `(line emit / inf field write / drift compare)`.

**Hypothetical inner-callable abstraction:**
```cpp
// In CfgGateRegistry.hpp — new shared abstraction:
template <typename Per Action>
void walk_stamp_bound_cfg_derived(const ControllerConfig<F>& cfg, Action action) {
    #define X_WALK(...) if constexpr (...has bit...) action(...);
    FOREACH_PER_CORE_CFG_FIELD(X_WALK);
    FOREACH_GLOBAL_CFG_FIELD(X_WALK);
    FOREACH_ML_CFG_FLAG(X_WALK);
    FOREACH_GATE_CFG_FLAG(X_WALK);  // adds at Step 0.5d
    #undef X_WALK
}
```

Then `populate_inference_cfg` / `populate_stamp_cfg` / `drift_check` each becomes a 2-line invocation passing a per-row action lambda. ~120 LOC body deduplication.

**Sites-added-vs-eliminated:**
- Cost: ~30-50 LOC new abstraction + 3 callers each ~10 LOC = ~60-80 LOC total
- Eliminated: ~140-180 LOC across 3 walker bodies × 4 inner walks each at v1.9 final state (~580 LOC at v1.9 versus ~430 LOC at HEAD)
- Ratio: **~70:160 — sites-eliminated wins**

**Verdict:** **PROPORTIONATE DEFER per `feedback_framework_layer_payoff_diminishing_returns`.** Recognition markers:
- Lifecycle phase: `.B.3` is at-or-past consolidation inflection per Caramel's recent surfacing ("walked one or two stops past where the payoff curve flattened")
- Generic-abstraction-over-N-registries adds a META layer past the inflection point (already-merged registries → meta-walker over them)
- v1.9 plan body's per-callsite copy-pattern is mechanically clean + each walker body is intentionally local + readable
- Adding the meta-walker would require lambda-based action passing which is harder to debug than X-macro inline expansion (template instantiation errors vs preprocessor errors)

**Recommendation:** **leave the 4 walker body copies in place at `.B.3`.** Document as TECH_DEBT-NEW entry "Inner-callable shared walker for cfg-derived consumer functions — ~140 LOC dedupe; DEFER post-paper-test per framework-layer payoff diminishing returns" at ship close. Future maintenance ship can revisit if a 3rd CFG_FLAG registry needs stamp-bound dispatch.

**Class 32 generic auto-gen prevention pattern:** Class 32 codification at `.B.3` is the prefix-asymmetry detection mechanism itself. No generic "auto-gen prevention" framework needed — the codification IS the detection. Future bitmap-flag registry additions follow the discipline of column-1 name matching consumer access name (the documented anti-pattern).

---

## 2. Step 1.6.6.b 15-row STAMP-side rename — GREEN

### 2.1 Per-row rename shape

15 rows at `CfgDriftCheckRegistry.hpp:236-311` each have the same `h->inference_cfg_<X>` → `h->X` pattern. No shared helper would absorb the complexity — the rename is the value (column-1 wire-key alignment with source-field name; Class 32 closure).

### 2.2 Sister pattern check at StampBoundModelConstRegistry.hpp

Walked `StampBoundModelConstRegistry.hpp:280-302` (PRE_CFG section at HEAD):

```
X(inference_cfg_confidence_threshold_scale, ..., inf->confidence_threshold_scale, inf->has_inference_cfg, ...)
X(inference_cfg_barrier_gate_enabled,       ..., inf->barrier_gate_enabled,       inf->has_inference_cfg, ...)
X(inference_cfg_bandit_blend_ratio,         ..., inf->bandit_blend_ratio,         inf->has_bandit, ...)
```

**Critical finding (PRE-EXISTING Class 32 instance):** PRE_CFG entries at lines 281-302 ALREADY use the pattern `column-1: inference_cfg_<X>=` wire-key + `column-7: inf->X` UNPREFIXED struct field access. This IS the Class 32 anti-pattern at the wire-key column vs source-name column asymmetry.

PRE_CFG entries are **NOT in v1.9 deletion scope** (they're MODEL_CONST entries, not POST_CFG cfg-derived). They emit at production wire format from the parent registry walker. **They preserve Class 32 INSTANCE survival at PRE_CFG section** — wire key reads `inference_cfg_<X>=` (parser symbol) but struct field is `inf-><X>` (consumer access).

**Operator-visible impact:** Class 32 codification says "prefix asymmetry at column-1 wire-key vs column-7 source-name". The codification SCOPE clarification needed: are PRE_CFG entries Class 32 instances that survive `.B.3`? Plan body Decision D scope explicitly says "POST_CFG entries deleted" — PRE_CFG entries with same asymmetry NOT in deletion scope but ARE structural instances of the codified pattern.

**Recommendation:** Plan body's Class 32 codification at ship close should EXPLICITLY note "PRE_CFG section retains same prefix-asymmetry at column-1 wire-key vs column-7 source-name pattern; these are LEGITIMATE prefix-asymmetry (wire-key namespaces a logically-bound group; source-name is consumer-friendly unprefixed) and Class 32 codification distinguishes 'legitimate namespacing prefix' from 'duplicate-emit asymmetry'." Otherwise `/bug-check` at next sweep may flag PRE_CFG entries as Class 32 instances when they're actually the legitimate-namespacing precedent.

**Minor amendment recommendation:** add 2-3 sentences to Class 32 codification text clarifying the distinction. Not a merge candidate per se, but discipline-completeness.

### 2.3 No merge opportunity at Step 1.6.6.b

15-row mechanical rename is the right shape. Per-row rename is the value (struct field alignment). Sister pattern at StampBoundModelConstRegistry PRE_CFG is INTENTIONALLY different (legitimate namespacing). **GREEN.**

---

## 3. Decision F (F.2) 15-entry parser back-compat — GREEN INLINE MERGE confirmed

### 3.1 Cost-benefit verification

Plan body proposes (Step 1.6.7.4) closed-set X-macro `FOREACH_LEGACY_PREFIXED_KEY(X)` listing 15 keys with their unprefixed sister field names. Per `canonical-sister-extension-discipline.md` § INLINE MERGE.

**Hand-walked counterfactual (15 separate strcmp branches):**
- Per-key: `if (strcmp(key, "inference_cfg_<X>") == 0) { call_parse_for_<X>(); continue; }` × 15 = ~30 LOC + parallel per-key code at parser dispatch site (~30-45 LOC)
- INLINE MERGE X-macro approach: `FOREACH_LEGACY_PREFIXED_KEY(X)` 15-row tuple + 1 dispatch macro expansion = ~25-30 LOC closed-set body + 1 expansion site

**Ratio: 1 dispatch site (~10 LOC expansion) replaces 15 inline branches (~30-45 LOC)**. Structural win confirmed.

**Time-bounded discipline:** plan body opens TECH_DEBT-101 tracking eventual deprecation (when production v1 stamps eliminated). Closed set + time-bounded → INLINE MERGE is per-canonical-sister-extension-discipline.md.

### 3.2 Anti-pattern check

NOT Class 18 (mirror state) — parser-only; ONE consumer (the parser dispatch). NOT Class 21 (parallel descriptors) — INLINE merge means the X-macro IS the descriptor body. NOT Class 32 — column-1 IS the wire-key (legacy keys); no source-name vs wire-key asymmetry within the back-compat layer.

**GREEN — INLINE MERGE confirmed correct per canonical-sister-extension-discipline.md § INLINE MERGE.**

---

## 4. Step 1.6.8 stamp_model.sh tooling migration — GREEN

### 4.1 Bash script shape

Walked `tools/stamp_model.sh:233-272` at HEAD:
- Lines 240-244: `inference_cfg_confidence_threshold_scale=` / `inference_cfg_barrier_gate_enabled=` / `inference_cfg_confidence_hard_block_threshold=` / `inference_cfg_held_out_fraction=` / `inference_cfg_freshness_tau=` — 5 keys in ONE multi-line heredoc-style append
- Line 251: `inference_cfg_bandit_blend_ratio=` — standalone append (gated by `BANDIT_BLEND` var presence)
- Lines 261-262: `inference_cfg_fee_rate_maker=` + `inference_cfg_fee_rate_taker=` — paired heredoc append (gated by both vars)

Each block has the same shape: `CANONICAL="${CANONICAL}<key>=${<VAR>_FMT}\n..."`.

### 4.2 Reuse opportunity check

**Bash function abstraction (`append_cfg_line()`)?**

Hypothetically:
```bash
append_cfg_line() {
    local key="$1"; local fmt="$2"
    CANONICAL="${CANONICAL}${key}=${fmt}
"
}
```

Then 6-7 invocations replace 3 heredoc blocks. **But:** the existing heredoc blocks group SEMANTICALLY-PAIRED keys (5-key inference_cfg group emit together; fee maker+taker paired; bandit standalone). Bash heredoc is the idiomatic shape for multi-line group emission. Adding `append_cfg_line` wrapper per line breaks the visual grouping and adds 1 function declaration + repeated invocations.

**Sites-added vs eliminated:**
- Cost: ~5 LOC function declaration + 6-7 invocations (~6-7 LOC)
- Eliminated: 3 heredoc structures (~5-8 LOC saved per heredoc = ~15-20 LOC total)
- Ratio: **~12:15-20 — broken-even or slight saving**

**Verdict per `feedback_proportionate_response_to_audit_findings`:** REJECT — heredoc grouping is the right idiomatic shape for bash. Per-line edit IS the appropriate migration.

**`tools/migrate_legacy_prefix.sh` for engine + bash combined?**

Could be a 1-shot sed script: `sed -i 's/inference_cfg_\(<key>\)=/\1=/g' tools/stamp_model.sh`. But:
- Engine-side migration is structural (X-macro registry deletion + struct-gen migration); not sed-replaceable
- Bash-side migration is 6-7 keys; sed-friendly but 1-shot
- A combined helper script would be USED ONCE during `.B.3` coding and never again

**Verdict:** EFFORT-AVOIDANCE per `feedback_no_defer_for_effort` — codifying a helper script is over-architecture for 1-shot mechanical work. Plan body's "~30 min focused" estimate is right.

**GREEN — no merge opportunity; per-line sed edits IS the right shape.**

---

## 5. Step 1.6.2 v1.6 expansion (5 NEW fields) — GREEN already merged

### 5.1 Consumer migration consolidation

5 NEW fields' consumer sites at `CoreModelZoo.hpp:400-419` integrate WITH original 10's consumer sites at lines 411-412. v1.8 comprehensive consumer enumeration captures all 149 sites across 8 files; per-file site counts in plan body line 363-369.

### 5.2 STAMP_HAS site consolidation

Plan body lines 391-394 enumerate STAMP_HAS migration sites:
- `BacktestPanels.hpp:1865` — `STAMP_HAS(v, inference_cfg_bandit_blend_ratio)` → `v.has_bandit_blend_ratio`
- `CfgDriftCheckRegistry.hpp:250` — `STAMP_HAS(*h, inference_cfg_bandit_blend_ratio)` → `h->has_bandit_blend_ratio`
- `CoreModelZoo.hpp:409` — `STAMP_HAS(sr, inference_cfg_bandit_blend_ratio)` → `sr.has_bandit_blend_ratio`

These 3 are bandit_blend_ratio sites. 5 NEW fields' STAMP_HAS sites would follow same pattern. Plan body's "per-call migration" guidance covers — no shared helper opportunity (each STAMP_HAS site has different surrounding context).

**Conclusion:** 5 NEW fields integrate cleanly with original 10's consumer migration. No NEW merge candidate. **GREEN.**

---

## 6. Cross-cutting per-field replace_all loop (lines 374-385) — GREEN appropriate

### 6.1 Loop shape

15-field for-loop with `rg -l "inference_cfg_${FIELD}\b" | xargs sed -i "s/\binference_cfg_${FIELD}\b/${FIELD}/g"` + build verify between iterations.

### 6.2 Batched-replace + single-build-verify alternative

Hypothetically: one mega-replace_all with all 15 patterns simultaneously, then ONE final build verify. Cost saved: 14 intermediate build verifies × ~1-2 min each = ~14-28 min total.

**Risk:** if ANY field's replace_all conflicts (substring overlap; unexpected consumer pattern not anticipated), the SINGLE final build verify catches it but doesn't isolate which field was problematic. Per-field build verify isolates the failing field immediately + allows rollback of just that field's edit.

**Per `feedback_avoid_substring_replace_all_on_member_access`:** the loop pattern uses full-token `\b` boundary matching — safe per the discipline. But the 15 fields include similar names (`confidence_threshold_scale` + `confidence_hard_block_threshold`; `fee_rate_maker` + `fee_rate_taker`; etc.) — per-field isolation makes any per-field anomaly visible.

**Verdict:** plan body's per-field-iteration + build-verify-each shape is the safer + more diagnosable approach. Time cost ~20-30 min total is acceptable. **GREEN.**

**`tools/migrate_legacy_prefix.sh` codification?** Same answer as § 4.2 — 1-shot use; not worth codifying. The bash loop in plan body lines 374-385 IS the codification (procedure-based capture per `feedback_enumerate_consumers_before_registry_row_deletion`).

---

## 7. Going-forward rules + Checks 31-35 + skill amendments — YELLOW minor merge candidate

### 7.1 Going-forward rules consolidation check

v1.9 ship-close auto-write proposes 4 NEW going-forward rules:
1. 4-pillar self-audit (DESIGN_SPECS + anti-pattern + operator-impact + novel-alternative)
2. Comprehensive consumer enumeration before registry-row deletion
3. Iteration-spiral signals audit meta-gap
4. Future-headache vs optimization scope framework

**Consolidation candidate:** Rules 1 + 2 + 3 are all REACTIVE-companion to existing PROACTIVE rules (per CLAUDE.local.md cross-refs). Could fold into ONE meta-rule "4-pillar discipline applies to all 4 audit-related concerns" — but each rule has a DIFFERENT trigger:
- Rule 1: before surfacing recommendations
- Rule 2: before registry-row deletion
- Rule 3: when iteration count hits 4+
- Rule 4: when scope-discoveries surface during refactor

**Verdict per `feedback_evaluate_options_on_robustness_latency_design_not_time`:** distinct triggers → distinct rules. Consolidating to ONE rule would lose the discoverability benefit (each cross-references the specific anti-pattern it prevents). **Keep as 4 separate rules.**

### 7.2 Checks 31-35 consolidation check

v1.9 ship-close auto-write proposes 5 NEW `/readiness` checks:
- Check 31: anti-pattern catalog rigor (Classes 1-30)
- Check 32: operator migration surfaced
- Check 33: novel alternative considered
- Check 34: comprehensive consumer enumeration for registry-row-deletion scope
- Check 35: iteration-spiral meta-gap recognition (verify if 5+ amendments, META-gap codified)

**Minor merge candidate:** Checks 31 + 32 + 33 are all "4-pillar self-audit" dimensions per `feedback_audit_own_proposals_with_same_rigor`. Could be a SINGLE composite check "Pre-coding rigor: 4-pillar self-audit complete" with 4 sub-bullets (DESIGN_SPECS / anti-pattern / operator / novel). Then Check 32 = consumer-enumeration discipline; Check 33 = iteration-spiral recognition. Net: 3 checks instead of 5.

**Sites-added vs eliminated:**
- 5 separate checks: 5 grep verifications + 5 evaluation lines = ~10 lines in `/readiness` SKILL.md output
- 3 composite checks: 3 verification blocks + 4 sub-bullet evaluation = ~8 lines
- Ratio: ~3 lines saved

**Verdict per `feedback_proportionate_response_to_audit_findings`:** marginal gain; either shape works. Plan body's 5-separate-check shape has discoverability advantage (each check is independently grep-able). Composite has aggregation advantage (single "rigor section" in `/readiness` output).

**Recommendation:** **lean toward 3 composite checks** per Caramel framing "we picked the right direction and walked one or two stops past where the payoff curve flattened" — 5 separate checks is past the inflection point for this domain. Plan body amendment minor:

```
- Check 31: 4-pillar pre-coding rigor complete
  - 31.a: DESIGN_SPECS cross-check section present
  - 31.b: Anti-pattern catalog cross-check section present (Classes 1-30 + new classes)
  - 31.c: Operator migration impact section present
  - 31.d: Novel alternative consideration section present
- Check 32: Comprehensive consumer enumeration (if scope includes registry-row deletion / rename)
- Check 33: Iteration-spiral meta-gap recognition (if 5+ amendments)
```

### 7.3 Skill amendment cross-references

v1.9 ship-close auto-write proposes 5 skill amendments:
- `/readiness` Checks 31-35
- `/trace-deps` standard output enrichment for registry-row-deletion scope (comprehensive consumer enumeration)
- `/parity-check` Class 31 detection
- `/precoding-audit-gate` iteration-spiral tracking + consumer enumeration verification
- `audit-driven-pre-coding-gate.md` DESIGN_SPEC amendment

**Sharing opportunity check:** `/readiness` Check 32 + `/trace-deps` enrichment + `/precoding-audit-gate` iteration tracking all reference the same underlying primitive: "comprehensive consumer enumeration". Could there be ONE DESIGN_SPEC `comprehensive-consumer-enumeration-discipline.md` that all 3 skills compose-by-reference?

**Sister DESIGN_SPECS at HEAD:** `canonical-sister-extension-discipline.md` (producer side) + `audit-scope-taxonomy.md` (audit invocations) + `pattern-codification-lifecycle.md` (codification timing). NONE specifically cover comprehensive consumer enumeration.

**Hypothetical new DESIGN_SPEC body:**
- Trigger: registry-row deletion / rename / column-1-vs-source-name change
- Procedure: ONE comprehensive `rg` covering all access patterns (dot/arrow/STAMP_HAS/token-paste/macro) across codebase-wide file types
- Output: per-file site counts + per-pattern counts; flag if >30 sites for procedure-based capture
- Cross-references: per-file replace_all loop pattern from this plan body (lines 374-385)

**Sites-added-vs-eliminated:**
- Cost: ~80-120 LOC new DESIGN_SPEC body (one-time codification)
- Eliminated: 3 cross-skill duplication (skill amendments each refer to consumer enumeration discipline in their own text)
- Ratio: Adds a 1-time spec; saves discipline drift if skills evolve independently

**Verdict per `feedback_motivated_collaborator_for_caramel` + `feedback_audit_canonical_sister_before_new_infra`:** considering whether to add NEW DESIGN_SPEC vs EXTEND existing `canonical-sister-extension-discipline.md` (producer side; this would be the consumer-side companion):

- **EXTEND option:** add new section "Comprehensive consumer enumeration (consumer side; companion to canonical-sister registry inspection)" to `canonical-sister-extension-discipline.md`
- **NEW SPEC option:** standalone `comprehensive-consumer-enumeration-discipline.md`

**EXTEND preferred:** the producer-side sister inspection + consumer-side enumeration are TWO SIDES of the same registry-change discipline. Keeping them in ONE spec preserves the holistic view. Cross-references from `feedback_enumerate_consumers_before_registry_row_deletion` already cite `canonical-sister-extension-discipline.md` as sister.

**Recommendation:** plan body Step 1.6.6.b auto-write line should clarify "EXTEND `canonical-sister-extension-discipline.md` with consumer-side section (NOT new standalone spec)". Currently the plan body doesn't specify whether to create new DESIGN_SPEC or extend; this clarification prevents future drift.

### 7.4 Conclusion for § 7

**YELLOW minor merge candidates:**
1. Compress Checks 31-33 → composite Check 31 with 4 sub-bullets; preserve 32 (consumer enum) + 33 (iteration spiral) as standalone
2. Specify "EXTEND `canonical-sister-extension-discipline.md` with consumer-side section" rather than implicit standalone-spec creation

Both are MINOR (discoverability + spec organization); not ship-blockers. Plan body amendment recommended at v1.10 if any iteration remains; otherwise capture as discovery for ship-close auto-write.

---

## 8. Decision E.2 implementation verification at v1.9

### 8.1 Plan body Step 1.6.6.a content

```
4 CfgDriftCheck row substitutions to COHORT_GATE_* macros at CfgDriftCheckRegistry.hpp —
line 272 thompson_exp3_blend_alpha gate → COHORT_GATE_BANDIT_BLEND_STATE_4;
lines 300 (ml_tp_pct), 304 (ml_sl_pct), 308 (barrier_blend_mode) gates → COHORT_GATE_PER_HORIZON_BARRIER
```

### 8.2 Verification at HEAD `9b62a72`

Walked `CfgDriftCheckRegistry.hpp` at the 4 sites:

| Line | Current expression | Plan body substitution | Match? |
|---|---|---|---|
| 272 | `(STAMP_HAS(*h, inference_cfg) && (cfg.bandit_algorithm == 4))` | substitute `(cfg.bandit_algorithm == 4)` → `COHORT_GATE_BANDIT_BLEND_STATE_4` | **CORRECT** — `MlCfgFlagRegistry.hpp:116` defines `COHORT_GATE_BANDIT_BLEND_STATE_4` as `(cfg.bandit_algorithm == 4)` — byte-identical |
| 300 | `(STAMP_HAS(*h, inference_cfg) && BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_PER_HORIZON_BARRIER_BLEND))` | substitute → `COHORT_GATE_PER_HORIZON_BARRIER` | **CORRECT** — `MlCfgFlagRegistry.hpp:120` defines `COHORT_GATE_PER_HORIZON_BARRIER` as `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_PER_HORIZON_BARRIER_BLEND)` — byte-identical |
| 304 | same as 300 | same | **CORRECT** |
| 308 | same as 300 | same | **CORRECT** |

**All 4 substitution sites identified accurately at v1.9. Plan body Step 1.6.6.a edits will preserve byte-identical gate semantic — pure dedupe of inline expression vs macro reference.**

### 8.3 Path γ #3 closure marker

Per prior v1.2-sweep report § 2.5: **PARTIAL (2-of-3 unified) → MOSTLY (3-of-3 unified at cohort cells that share semantic)**. The 14 preserve-as-is rows (CROSS_BINARY forensic + bandit-boundary semantic + fees group + build flags hash) take (B) ACCEPT WITH RATIONALE verdict per `feedback_proportionate_response_to_audit_findings`.

**(E.2) implementation verified accurate at v1.9. No change required.**

---

## 9. Inflection assessment — does v1.9 introduce new reuse opportunities OR is it audit-clean on merge concerns?

### 9.1 Iteration-spiral termination check per `feedback_iteration_spiral_signals_audit_meta_gap`

v1.3 → v1.9 amendment trajectory:
- v1.3: Caramel pushbacks (4 dimensions × multiple checks)
- v1.4: 5 readiness gaps
- v1.5: Class 32 codification + Decision D 9→10
- v1.6: TECH_DEBT-104 closure (5 NEW fields)
- v1.7: 2 material findings (15-row STAMP-side rename + 0.5d effort revision)
- v1.8: consumer-enumeration meta-gap codified (149 sites comprehensive grep)
- v1.9: operator-tooling enumeration gap closed (`tools/stamp_model.sh`)

**v1.9 final sweep markers:**
- Iteration trajectory finds smaller scope each iteration (lower-hit files at v1.9: comment refs only in Version.hpp + 3 others — ACCEPTED as-is)
- Meta-gap codified at v1.8 (consumer enumeration discipline)
- v1.9 finds 1 tooling site + 4 lower-hit files marked ACCEPTED — **inflection reached**

**Conclusion:** v1.9 IS the inflection point per the spiral-termination discipline. Plan body should NOT continue amending unless a NEW material finding surfaces — which this re-sweep DID NOT surface.

### 9.2 v1.3 → v1.9 NEW scope reuse-merge findings summary

This re-sweep walked the 7 focus areas requested and surfaced:
- 0 HIGH or MED reuse-merge opportunities (no parallel walker bodies, no atomic-load patterns, no clock-read patterns, no scalar cfg-mirror caches in v1.9-added scope)
- 2 YELLOW minor candidates: Focus area 1 inner-callable shared walker (PROPORTIONATE DEFER); Focus area 7 Checks 31-35 consolidation
- 5 GREEN: Focus areas 2, 3, 4, 5, 6 — no new merge opportunities; v1.9 additions are audit-clean

**Inflection-assessment verdict:** v1.9-added scope is substantively audit-clean on merge concerns. The 2 YELLOW minor candidates are both PROPORTIONATE DEFERS per `feedback_framework_layer_payoff_diminishing_returns` lifecycle phase — they should be captured as TECH_DEBT entries at ship close, not addressed at `.B.3` coding.

---

## 10. Comparison with prior v1.2 audit verdict

| Surface | v1.2 (prior audit) | v1.9 (this re-sweep) | Change |
|---|---|---|---|
| Decision E recommendation | E.2 (PROPORTIONATE; 4-row substitution) | E.2 implementation correctly identified | UNCHANGED — already implemented in plan body Step 1.6.6.a |
| Sites added vs eliminated overall ratio | ~110-240 added vs ~5-N eliminated; CHARTER-LEVEL FAVORABLE | ~140-180 added (4 walker bodies at Step 0.5d + parser back-compat + struct-gen extensions) vs ~150-180 mirror anti-pattern instances eliminated | UNCHANGED character — ship-level wins |
| Path γ #3 closure marker | PARTIAL → MOSTLY at .B.3 close per E.2 | Same; verified accurate at v1.9 | UNCHANGED |
| Reuse-merge candidates | 3 minor flags (struct-gen extension proceed; reason_buf no-sister; legacy fold-out no meta-pattern) | 2 minor flags (inner-callable shared walker DEFER; Checks 31-35 consolidation) | NEW v1.9-specific findings |

**Net assessment:** v1.9 expanded the ship's scope substantially (15 deletions vs 9-10 at v1.5; 149 consumer sites enumerated; framework walker extension for FOREACH_GATE_CFG_FLAG; tooling migration). The expanded scope did NOT introduce new HIGH-impact reuse-merge candidates. The 2 minor candidates surfaced (Focus areas 1, 7) are both PROPORTIONATE DEFERS appropriate for post-paper-test code-moving wins per `feedback_framework_layer_payoff_diminishing_returns`.

---

## 11. Latency rule-of-thumb compliance

All v1.9-added scope is slow-path / boot / test cadence per plan body verification gate ("HOT_PATH_CHANGELOG: NONE entry"). Per `DESIGN_PHILOSOPHY.md` § 4: zero merge-savings to extract from hot path (untouched). Per § 7: structural-fix family applies; framework consolidation IS the work.

`tools/calls_graph_diff.sh verify` confirms at ship close.

**No latency-merge opportunities surfaced for v1.9 expanded scope.**

---

## 12. Verification gate alignment

Plan body's verification gate section (lines 651-654) already lists:
- `/merge-scan` GREEN — Path γ #3 PARTIAL → MOSTLY per Decision E (E.2)

**This re-sweep verdict matches: GREEN with 2 minor YELLOW candidates that are DEFER-appropriate.** Plan body verification gate is accurate at v1.9.

**Optional minor plan body amendment recommendations (NOT ship-blockers):**

1. § 7.1 — Class 32 codification text addition: explicit distinction between legitimate-namespacing-prefix at PRE_CFG entries vs duplicate-emit-asymmetry at POST_CFG (~2-3 sentences in `DOCS/RECURRING_BUG_PATTERNS.md` codification at ship close)
2. § 7.2 — compress Checks 31-33 → composite Check 31 with 4 sub-bullets (preserves discoverability with composite aggregation)
3. § 7.3 — clarify "EXTEND `canonical-sister-extension-discipline.md` with consumer-side section" rather than implicit new spec creation
4. § 1.3 — open TECH_DEBT-NEW entry at ship close: "Inner-callable shared walker for cfg-derived consumer functions — ~140 LOC dedupe opportunity; DEFER post-paper-test per framework-layer payoff diminishing returns"

All 4 are MINOR and capturable as ship-close auto-write discoveries; none warrant a v1.10 amendment cycle.

---

## 13. Overall recommendation

**GREEN. v1.9 plan body is audit-clean on merge-scan concerns at expanded scope.**

### Top-3 highest-impact items for ship-close (auto-write at `.B.3` postmortem)

1. **TECH_DEBT-NEW entry:** Inner-callable shared walker abstraction for cfg-derived consumer template fns (~140 LOC dedupe opportunity; DEFER post-paper-test; lifecycle-phase appropriate)
2. **RECURRING_BUG_PATTERNS Class 32 codification text:** distinguish legitimate-namespacing-prefix (PRE_CFG section) from duplicate-emit-asymmetry (POST_CFG section deleted at this ship). Prevents future `/bug-check` false-positives at PRE_CFG entries.
3. **Plan body Checks 31-35 consolidation:** composite Check 31 with 4 sub-bullets + standalone Check 32 (consumer enum) + Check 33 (iteration spiral) = 3 checks instead of 5. Apply during ship-close `/readiness` skill amendment.

### Items deferrable (TECH_DEBT entries; not at `.B.3`)

- Inner-callable shared walker abstraction (per § 1.3)
- New `comprehensive-consumer-enumeration-discipline.md` standalone spec (REJECTED in favor of EXTENDING `canonical-sister-extension-discipline.md` with consumer-side section)

### Items to leave alone (intentional structure)

- Per-row STAMP-side renames at Step 1.6.6.b (15 rows; no helper opportunity)
- Per-key parser back-compat X-macro (15 entries; INLINE MERGE confirmed)
- Per-line bash sed in stamp_model.sh (6-7 keys; heredoc grouping is idiomatic)
- Per-field replace_all loop in plan body (15 fields; per-build-verify isolation valuable)
- 4 separate going-forward rules at ship close (distinct triggers; consolidation loses discoverability)

---

**End of /merge-scan re-sweep report.** v1.9 plan body GREEN. Decision E.2 implementation verified accurate (4 substitution sites at CfgDriftCheckRegistry.hpp lines 272/300/304/308). Inflection assessment: v1.9 IS the spiral-termination point per `feedback_iteration_spiral_signals_audit_meta_gap`; no further plan body amendments warranted. 2 minor YELLOW candidates surface as ship-close auto-write discoveries, not ship-blockers.
