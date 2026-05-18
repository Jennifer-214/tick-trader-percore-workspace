# /readiness report — `.B.3` v1.10 plan body — BUILD-FORCED sequencing focus — 2026-05-18

**Scope:** focused audit on Step 1.5 ↔ 1.6.2 ↔ 1.6.3 sequencing coupling discovered during coding (Caramel surfaced after WIP-checkpoint 2 = engine `a406120`).

**Plan target:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.10 FULL
**Engine state:** HEAD = `a406120` (2 WIP-checkpoint commits ahead of rollback anchor `pre-v5.15.5.F.4d.1.B.3` cut at `9b62a72`)
**Build state:** 4093 PASS / 0 FAIL (856 parity_harness + 3237 controller_test)
**Plan-body version:** v1.10 (10 iterations from v1.2 + Batch 2 RE-SWEEP)

---

## Executive verdict — YELLOW

Plan body v1.10 has comprehensive coverage of step contents + cross-tool migration discipline (Layer 7) + 7 readiness Checks 31-37 + 3 codified meta-gaps M1/M2/M3. **HOWEVER:** the BUILD-FORCED sequencing list at lines 723-744 lists Step 1.5 BEFORE Step 1.6.2 + 1.6.3, but Caramel's coding-time discovery (validated against current code at HEAD) shows Step 1.5 swap **cannot land first** without losing wire-format byte semantics. **Recommended fix:** re-order BUILD-FORCED list to land Step 1.6.3 (struct-gen migrations) + Step 1.6.2 (bit-add) BEFORE Step 1.5 (INFERENCE_CFG_AUTOPOPULATE swap).

Additionally: line-number references for Step 1.6.5 test sites have SHIFTED post WIP commits (~5-15 lines).

---

## Per-Step sequencing verdict matrix

| Step | Plan body claim | Actual dependencies (verified at HEAD a406120) | Verdict |
|---|---|---|---|
| 0, 0.5a, 0.5b, 0.5c | Framework primitives FIRST | Independent at HEAD | CORRECT (LANDED in WIP) |
| 0.5d.a.0 | Before 0.5d.a (sister sig migration) | Verified — adds metadata_flags col required by 0.5d.a walker | CORRECT (LANDED in WIP) |
| 0.5d.a | Walker emit; before 0.5d.b/c/d | Verified at `CfgGateRegistry.hpp:307-321` | CORRECT (LANDED in WIP) |
| 0.5d.b/c/d | Sequential within 0.5d sub-cluster | **WIP comment at `CfgGateRegistry.hpp:397-401` says DEFERRED to AFTER 1.6.3** (drift walker needs `handle.barrier_gate_enabled` discrete field which Approach A struct-gen provides) | **DEPENDENCIES-MISSED** — plan body sequencing claims 0.5d.b/c/d come immediately after 0.5d.a, but they actually MUST wait for Step 1.6.3 |
| 1 | Independent test count-assertion migrations | LANDED in WIP-checkpoint 2; 6 sites confirmed | CORRECT |
| **1.5** | **Lands BEFORE Step 1.6.X per BUILD-FORCED line 728** | **At HEAD, Step 1.5 swap drops population of 11 prefixed `inf.inference_cfg_<name>` fields without framework picking them up. The 11 fields populated by legacy AUTOPOPULATE (`ml_tp_pct`/`ml_sl_pct`/`bandit_blend_ratio`/`barrier_blend_mode`/`per_horizon_barrier_blend`/`confidence_threshold_scale`/`barrier_gate_enabled`/`confidence_hard_block_threshold`/`held_out_fraction`/`fee_rate_maker`/`fee_rate_taker`) are NOT flagged STAMP_BOUND_CFG_DERIVED at HEAD — the framework walker's `if constexpr` filter excludes them.** Tests at `controller_test.cpp:25048-25055` will FAIL (assertions read `inf.inference_cfg_ml_tp_pct` which legacy populated; new walker doesn't). | **WRONG-ORDER** — Step 1.5 must land AFTER Step 1.6.3 (Approach A struct-gen creates unprefixed fields) + Step 1.6.2 (bit-add flags them) |
| 1.6.1 | Depends on 0.5b | LANDED in WIP-checkpoint 2; TECH_DEBT-093 FULL CLOSED | CORRECT |
| 1.6.2 | Depends on 0.5d.a.0 + 1.6.3 + 1.6.4 + 1.6.7 wire-key changes per line 730 | Lines 478-482 already capture **CORRECT** mandatory sequencing: 0.5b → 1.6.3 → 1.6.2 → Step 2. Line 730 BUILD-FORCED list says same. | CORRECT (well-captured) |
| 1.6.3 | Must land before Step 2 | Plan body says "before Step 2 deletion" — but also must land BEFORE Step 1.6.2 + Step 1.5 per the chain | **MOSTLY CORRECT but understated** — Step 1.6.3 is the LINCHPIN; everything from Step 1.5 onwards depends on it |
| 1.6.4 | Couples with Step 1.6.7 | Production canonical body emit — wire-format-changing step | CORRECT |
| 1.6.5 | 1 production + 7 test sites at specific lines | Lines drifted post WIP: plan claims `4821/4841/4859/22291/22312/22723/22734`; actual `4825/4845/4863/22305/22326/22737/22748` | **DEPENDENCIES-MISSED** — line numbers stale |
| 1.6.6 | After 0.5a framework reason_buf extension | LANDED in WIP; safe to start at Step 1.6.6 anytime post-0.5a | CORRECT |
| 1.6.6.a/.b | After 1.6.6 main | 15-row STAMP-side rename couples with Decision D 15-entry scope deletions | CORRECT |
| 1.6.7.0 | DESIGN_SPEC amendment at Step 0 BEFORE coding | Verify on disk pre-coding | CORRECT (verify status pending) |
| 1.6.7.1-3 | Couple with Step 1.6.4 | Constants + bounds check + bump | CORRECT |
| 1.6.7.4 | Parser back-compat (15 legacy keys) | Couples with Step 1.6.4 emit migration | CORRECT |
| 1.6.7.5 | After 1.6.7.4 | v1 fixture LOAD test | CORRECT |
| 1.6.7.6 | At ship close | TECH_DEBT-101 entry | CORRECT |
| 1.6.8 | Couples with Step 1.6.7 SOFT version bump | Cross-tool stamp_model.sh migration | CORRECT (sites verified at lines 221/240-262) |
| 1.7 | After Step 1.6.4 | Layer 5b invariant invocation | CORRECT |
| 2 | FORCED LAST | Build BREAKS if 1.5 + 1.6.3 + 1.6.4 + 1.6.5 + 1.6.6 not addressed | CORRECT |
| 3-9 | After Step 2 | Sequential post-deletion | CORRECT |

---

## Step 0.5d.b/c/d follow-up dependency map (Caramel's question #4)

Per WIP-checkpoint 2 commit message + `CfgGateRegistry.hpp:397-401` deferral comment:

| Sub-step | Plan body claim | Actual dependency | Verdict |
|---|---|---|---|
| 0.5d.b (parser dispatch for bitmap-flag wire keys) | Sequential within 0.5d after 0.5d.a | Needs `inf.barrier_gate_enabled` UNPREFIXED on ModelStampResult; provided by Step 1.6.3 Approach A struct-gen | **DEFERRED TO AFTER 1.6.3** |
| 0.5d.c (consumer migration sub-decision) | Sequential within 0.5d | Needs discrete fields exist on stamp structs (Step 1.6.3 provides) | **DEFERRED TO AFTER 1.6.3** |
| 0.5d.d (drift_check + populate_inference_cfg template fn extensions) | Sequential within 0.5d | Same — needs `handle.barrier_gate_enabled` discrete field for drift walker compile | **DEFERRED TO AFTER 1.6.3** |

**Recommended re-ordering:** Step 0.5d.b/c/d should be moved AFTER Step 1.6.3 in the BUILD-FORCED list. This matches actual code state at HEAD (WIP comment at CfgGateRegistry.hpp:397-401 already records the deferral).

---

## Step 9 ship-close auto-write scope verification

Cross-check against current state (post WIP-checkpoint 2):

| Auto-write claim | Status at HEAD | Verdict |
|---|---|---|
| Version.hpp bump `5.15.5.F.4d.1.B.2` → `5.15.5.F.4d.1.B.3` | Pending | CORRECT |
| CHANGELOG.md `.B.3` row | Pending | CORRECT |
| CLAUDE.local.md sprint state row update | Pending | CORRECT |
| TECH_DEBT-093 CLOSED | **ALREADY CLOSED at WIP-checkpoint 2** per commit message; plan body Step 9 says "8 TECH_DEBT-09X CLOSED" — count is now 7 remaining at coding-time + 1 done | **STALE** — plan body should reflect 1-already-closed (mechanical book-keeping) |
| TECH_DEBT-094 through -100 CLOSED at ship close | Pending — depend on Steps 1.6.2-1.6.7 still being coded | CORRECT |
| TECH_DEBT-101 NEW (parser back-compat deprecation) | Not yet in ledger | CORRECT (opens at ship close) |
| TECH_DEBT-103 NEW (locale-pin optimization) | Not yet in ledger | CORRECT |
| TECH_DEBT-105 NEW (sister-registry-sig-parity CI) per M1 | Not yet in ledger | CORRECT |
| TECH_DEBT-106 NEW (cross-tool-emit-parity CI) per M2 | Not yet in ledger | CORRECT |
| **TECH_DEBT-107 NEW (registry-default-vs-manual-default audit for 47 globals)** | **Promised in WIP-checkpoint 2 commit message but NOT in plan body Step 9 auto-write list** | **GAP** — plan body needs amendment to include TECH_DEBT-107 in Step 9 NEW-entries list |
| Class 31 + Class 32 codification with "False-positive surface" subsection per M3 | Pending | CORRECT |
| RECURRING_BUG_PATTERNS.md intro polish (codification template) | Pending | CORRECT |
| 6-7 NEW feedback memories at ship close | Pending; v1.3 batch (4) + v1.10 batch (2-3) | CORRECT |
| `/readiness` Checks 31-37 amendment | Pending | CORRECT |
| `/trace-deps` skill amendment | Pending | CORRECT |
| `/parity-check` skill amendment (Class 31 detection + Section E.5) | Pending | CORRECT |
| `/precoding-audit-gate` skill amendment (iteration-spiral tracking) | Pending | CORRECT |
| `audit-driven-pre-coding-gate.md` DESIGN_SPEC amendment | Pending | CORRECT |
| `future-oriented-plan-template.md` amendment | Pending | CORRECT |
| FEATURE_LOOKUP.md entry (stamp_format_version SOFT bump) | Pending | CORRECT |

---

## Cold-pickup completeness check (C.1-C.10)

| # | Field | Verdict |
|---|-------|---------|
| C.1 | Branch state | PASS — `feat/v5.15-live-readiness` |
| C.2 | Phase execution order matches dependency order | **YELLOW** — BUILD-FORCED list has Step 1.5 before 1.6.X but Step 1.5 actually depends on 1.6.3+1.6.2 |
| C.3 | First concrete move (Step 0) | PASS — pre-tag rollback anchor + DESIGN_SPECS Stage 2 DRAFT on disk |
| C.4 | Function/constructor names cited | PASS — `INFERENCE_CFG_POPULATE_FROM_DERIVED`, `populate_inference_cfg_from_derived`, `cfg_derived::drift_check_from_derived` etc. all verified at code |
| C.5 | File:line refs for tests/baselines | **YELLOW** — Step 1.6.5 lines stale (drift by ~5-15 lines post WIP); Step 1.6.2 consumer migration sites verified |
| C.6 | Stale-claim audit | **YELLOW** — Decision D claim "9 cohort" appears at line 105 (stale; should be 15 per v1.6 scope; plan body says these were CORRECTED but verified — section 91 has correct 15-scope; line 105 still says "9 cohort POST_CFG + 1 standalone" which is HONEST sub-scope vs total) |
| C.7 | Effort claims reconcile | PASS — ~22-32h focused estimate plausible for remaining work |
| C.8 | Source-audit references | PASS — 11 plan_checks reports cited (6 Batch 1 + 5 Batch 2) |
| C.9 | Predecessor/dependent plans named with paths | PASS |
| C.10 | Tag names locked | PASS — `pre-v5.15.5.F.4d.1.B.3` rollback anchor; ship tag `v5.15.5.F.4d.1.B.3` |

---

## Top 5 NEW findings (sequencing dependencies + auto-write scope)

### 1. CRIT — Step 1.5 BUILD-FORCED placement is WRONG

**Surface:** plan body BUILD-FORCED list at line 728 says `Step 1.5 (INFERENCE_CFG_AUTOPOPULATE swap; 2 sites)` BEFORE Step 1.6.1+. Plan body Step 1.5 body itself at line 384-387 says "Verify wire-format byte preservation under SOFT bump (Decision F covers)" — but Decision F covers PARSER back-compat (read side), NOT emit side.

**Verified at HEAD:**
- Legacy `INFERENCE_CFG_AUTOPOPULATE` (line 148 of `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp`) writes to PREFIXED `inf.inference_cfg_<name>` for 16 fields
- Framework `INFERENCE_CFG_POPULATE_FROM_DERIVED` (line 411 of `MemHeaders/CfgGateRegistry.hpp`) writes to UNPREFIXED `inf.<name>` for 19 STAMP_BOUND_CFG_DERIVED-flagged per-core fields
- **Field sets DIFFER**: legacy writes 11 prefixed-only fields (`ml_tp_pct`/`ml_sl_pct`/`barrier_blend_mode`/`per_horizon_barrier_blend`/`confidence_threshold_scale`/`barrier_gate_enabled`/`confidence_hard_block_threshold`/`held_out_fraction`/`bandit_blend_ratio`/`fee_rate_maker`/`fee_rate_taker`) which framework does NOT pick up until Step 1.6.2 flags them + Step 1.6.3 struct-gen creates unprefixed counterparts

**Impact:** Step 1.5 swap at HEAD would silently drop wire-format population for 11 fields. Tests at `controller_test.cpp:25048-25055` would FAIL because they assert `inf.inference_cfg_ml_tp_pct == 0.0007` (set by legacy macro; new walker doesn't touch this field).

**Recommended fix:** re-order BUILD-FORCED list. New sequence:
1. Step 0/0.5a/0.5b/0.5c/0.5d.a.0/0.5d.a (LANDED in WIP)
2. Step 1 (LANDED in WIP)
3. Step 1.6.1 (LANDED in WIP)
4. **Step 1.6.3 (struct-gen migrations) — LINCHPIN; creates unprefixed `inf.<name>` for 15 fields via Approach A**
5. **Step 1.6.2 (bit-add for 15 fields)** — flags them so framework walker picks them up
6. Step 0.5d.b/c/d (drift walker rejoin + parser dispatch; needs Step 1.6.3 discrete fields)
7. **Step 1.5 (INFERENCE_CFG_AUTOPOPULATE swap) — NOW safe because Step 1.6.2+1.6.3 ensured framework picks up the previously-prefixed fields under their new unprefixed names**
8. Step 1.6.4 (production canonical body emit migration; couples with Step 1.6.7.1-3 version bump)
9. Step 1.6.5 (STAMP_CFG_AUTOPOPULATE swap; line numbers need refresh)
10. Step 1.6.6 + .a + .b (drift walker migration + CfgDriftCheck row substitutions + 15-row STAMP-side rename)
11. Step 1.6.7.4 (parser back-compat for 15 legacy prefixed keys)
12. Step 1.6.7.5 (v1 fixture LOAD test)
13. Step 1.6.8 (stamp_model.sh cross-tool migration)
14. Step 1.7 (Layer 5b invariant)
15. Step 2 (DELETE legacy registries) — FORCED LAST
16. Step 3-9

### 2. HIGH — Step 0.5d.b/c/d sequencing assumption violated by WIP code state

**Surface:** plan body lines 371-373 list Step 0.5d.b/c/d as "sequential within 0.5d" implying they follow Step 0.5d.a directly. **`CfgGateRegistry.hpp:397-401` comment** (landed in WIP) records they were DEFERRED to AFTER Step 1.6.3 because the drift walker for FOREACH_GATE_CFG_FLAG needs `handle.barrier_gate_enabled` discrete field on ModelStampResult.

**Fix:** plan body Step 0.5d body needs amendment to say "Step 0.5d.b/c/d DEFERRED to AFTER Step 1.6.3 lands discrete field auto-gen via Approach A; tracked at code site `CfgGateRegistry.hpp:397-401`".

### 3. HIGH — TECH_DEBT-107 promised in WIP commit but missing from plan body Step 9 auto-write list

**Surface:** WIP-checkpoint 2 commit message (engine `a406120`) promises:
> TECH_DEBT-107 NEW — Registry default vs manual default audit for 47 globals (mismatches identified at Step 1.6.1 closure; e.g., warmup_ticks registry default=0 but manual=128). Audit + reconcile (either update registry default OR keep manual override + document rationale per field). LOW priority; future-headache reducer via full auto-defaults activation when registry is single source of truth.

Plan body Step 9 NEW-entries list at lines 798-803 enumerates -101/-103/-105/-106 but does NOT mention -107. **Plan body needs amendment** to add TECH_DEBT-107 line in Step 9 NEW-entries enumeration + add corresponding row to "Verification gate" + "TECH_DEBT auto-write expectations" sections.

### 4. MED — Step 1.6.5 line numbers have drifted post WIP commits

**Surface:** plan body line 508 lists STAMP_CFG_AUTOPOPULATE test sites as `4821, 4841, 4859, 22291, 22312, 22723, 22734`.
**Verified at HEAD `a406120`:** actual lines are `4825, 4845, 4863, 22305, 22326, 22737, 22748` (drift ~4-15 lines per site).

**Fix:** plan body needs mechanical line-number refresh for Step 1.6.5 (and consumer-migration sites at Step 1.6.2's line ~430-446 may have similar drift; spot-check at coding time).

### 5. LOW — TECH_DEBT-093 already CLOSED at WIP; plan body Step 9 says "8 closed" still accurate but bookkeeping subtle

**Surface:** plan body Step 9 says "8 TECH_DEBT-09X CLOSED" (93-100). WIP commit closed -093 already. The total of 8 is still correct (the ship will eventually close 8 by ship-close time), but mid-coding plan body claim that ALL eight close at ship-close is technically stale (-093 closed mid-ship).

**Fix:** minor cosmetic; clarify in plan body that TECH_DEBT-093 closed at WIP, -094 through -100 close at ship-close completion. Not a blocker.

---

## Recommended re-ordering of BUILD-FORCED list in plan body

Replace plan body lines 723-744 with:

```
## Steps sequencing (BUILD-FORCED) — corrected per coding-time discoveries

**Critical sequencing constraint** (build BREAKS or wire-format silently regresses if violated):

PHASE A — Framework primitives (LANDED at WIP-checkpoint 1+2):
- Step 0 (pre-tag rollback anchor + DESIGN_SPECS Stage 2 DRAFTs on disk)
- Step 0.5a (drift_check_from_derived reason_buf + reason_cap extension)
- Step 0.5b (Path α 12→13-col STORAGE_T cascade for FOREACH_GLOBAL_CFG_FIELD)
- Step 0.5c (tt::cfg_parse_field<T> char[N] branch)
- Step 0.5d.a.0 (FOREACH_GATE_CFG_FLAG 5→6 col sister-registry sig migration; M1b first canonical)
- Step 0.5d.a (X_STAMP_CFG_POPULATE_GATE_CFG_FLAG sister walker emit)

PHASE B — Test-only migrations (LANDED at WIP-checkpoint 2):
- Step 1 (6 test count-assertion migrations)

PHASE C — gap_acceptable_threshold cleanup (LANDED at WIP-checkpoint 2):
- Step 1.6.1 (TECH_DEBT-093 FULL CLOSURE — 4 sites)

PHASE D — Struct-gen FIRST (NEW SEQUENCING per Caramel coding-time discovery):
- Step 1.6.3 (TECH_DEBT-095 — ModelInference struct-gen migrations; LINCHPIN — creates unprefixed inf.<name> fields)
- Step 1.6.2 (TECH_DEBT-094 + -100 + -104 — 15-entry bit-add per Decision D mechanism 1)
- Step 0.5d.b/c/d (drift walker rejoin + parser dispatch + remaining template fn extensions; needs Step 1.6.3 discrete fields)

PHASE E — INFERENCE_CFG_AUTOPOPULATE swap (NOW safe — wire-format byte-preserving):
- Step 1.5 (INFERENCE_CFG_AUTOPOPULATE swap; 2 sites; tests at 25048-25055 update to read inf.<name> unprefixed)

PHASE F — Production wire-format migration (forces stamp_format_version bump):
- Step 1.6.4 (TECH_DEBT-096 — production canonical body emit migration; wire-format-changing step)
- Step 1.6.5 (TECH_DEBT-097 — STAMP_CFG_AUTOPOPULATE swap; 1 production + 7 test sites at REFRESHED lines 4825/4845/4863/22305/22326/22737/22748)
- Step 1.6.6 + .a + .b (TECH_DEBT-098 — drift walker migration + 4 CfgDriftCheck row substitutions + 15-row STAMP-side rename)

PHASE G — stamp_format_version SOFT bump (couples with Phase F):
- Step 1.6.7.0 (DESIGN_SPEC amendment Stage 2 DRAFT at Step 0)
- Step 1.6.7.1-3 (extract literal + bounds check + bump)
- Step 1.6.7.4 (parser back-compat layer; 15 legacy prefixed keys)
- Step 1.6.7.5 (v1 fixture LOAD test)
- Step 1.6.7.6 (TECH_DEBT-101 entry)

PHASE H — Cross-tool migration (couples with Phase G):
- Step 1.6.8 (stamp_model.sh: 6 wire-key renames + line 221 version literal bump + line 244 orphan delete; ~45 min)

PHASE I — Layer 5b invariant invocation:
- Step 1.7 (after Step 1.6.4 lands production walker)

PHASE J — Legacy registry deletion (FORCED LAST):
- Step 2 (DELETE legacy registry headers; build BREAKS if Phase D-I migrations missing)

PHASE K — CI gates + cleanup:
- Step 3 (FOREACH_REGISTRY enrollment row deletions)
- Step 4 (CI Check 9 compile-time static_assert)
- Step 5 (v5.14 stamp fixture regression test)
- Step 6 (DESIGN_SPECS cleanup + NEW sections)
- Step 7 (residual SUPERSEDED ref cleanup)
- Step 8 (/test-strength-audit final pass)
- Step 9 (build verify + ship close + 7 auto-writes per current scope INCLUDING TECH_DEBT-107)
```

---

## Inflection assessment

**Total findings vs prior /readiness runs:**
- Batch 1 (v1.2 audit): 4 HIGH + multiple gaps
- Batch 2 RE-SWEEP (v1.9 audit): 1 NEW HIGH + 3 NEW MED + 3 NEW LOW — bookkeeping-class
- **This run (v1.10 + coding-time discoveries against engine `a406120`):** 1 NEW CRIT (Step 1.5 BUILD-FORCED placement) + 2 NEW HIGH (0.5d.b/c/d deferral + TECH_DEBT-107 gap) + 1 NEW MED (line drift) + 1 NEW LOW

**Spiral characterization:** these are FRESH-SURFACE findings caught by CODING-TIME verification against actual code state at HEAD `a406120` (2 WIP commits ahead of pre-tag). They are NOT same-surface getting smaller; they are dependency-graph-validation findings that emerged when implementation hit the structural reality. Per `feedback_iteration_spiral_signals_audit_meta_gap`, this is the EXPECTED kind of finding when coding-discovery + plan-body claim collide.

**Meta-gap NEW M4 candidate (LOW priority):** plan body BUILD-FORCED list sequencing was inferred from plan-time reasoning but never validated against an actual code-state probe. Future plans for refactors with N≥10 inter-step dependencies should include a "Code-state validation" check item — a single grep + ls + sample-build to verify each claimed dependency edge holds at HEAD. **Codify decision:** decline to codify M4 at this ship — the catch happened at the right place (coding time), the plan body had enough fidelity that the discovery was easy, and `feedback_iteration_spiral_signals_audit_meta_gap` already covers the broader discipline. Track as informal observation in postmortem.

---

## Recommended next sequence to execute

Per the corrected BUILD-FORCED list above. **Immediate next action:**

1. **AMEND PLAN BODY** before continuing coding (per Caramel's "consult-before-coding" + `feedback_recheck_designspecs_on_pushback`):
   - Re-order Step 1.5 to AFTER Step 1.6.3 + 1.6.2 + 0.5d.b/c/d
   - Move Step 0.5d.b/c/d AFTER Step 1.6.3
   - Add TECH_DEBT-107 to Step 9 NEW-entries enumeration
   - Refresh Step 1.6.5 line numbers (4825/4845/4863/22305/22326/22737/22748)
   - Document the discovery in plan body "Coding-time discoveries" section (sister to .B.2 postmortem Discovery 5/6 pattern)

2. **NEXT CODING STEP** after plan body amendment: **Step 1.6.3** (ModelInference struct-gen migrations) — the linchpin. Approach A unconditional struct-gen at:
   - `ModelInference.hpp:1196-1199` (ModelStampResult)
   - `ModelInference.hpp:1396-1401` (parser dispatch)
   - `ModelInference.hpp:1640-1643` (StampInferenceCfgInputs)

   This creates unprefixed `inf.<name>`/`handle.<name>` discrete fields for all flagged STAMP_BOUND_CFG_DERIVED rows codebase-wide. UNBLOCKS Steps 1.6.2 + 1.5 + 0.5d.b/c/d.

3. **THEN Step 1.6.2** (15-entry bit-add per Decision D mechanism 1). Framework walker activates for the 15 cohort + model-state fields.

4. **THEN Step 1.5** (INFERENCE_CFG_AUTOPOPULATE swap) — at this point, framework walker AT LEAST writes the same field set as legacy (under unprefixed names), so wire-format change is captured by the Step 1.6.7 SOFT bump (which couples with Step 1.6.4). Tests at 25048-25055 update to read `inf.ml_tp_pct` etc. (Approach A discrete field) instead of `inf.inference_cfg_ml_tp_pct`.

---

## Verdict: YELLOW

**Recommended action:** amend plan body BUILD-FORCED list + Step 0.5d.b/c/d body + Step 1.5 body + Step 9 auto-writes BEFORE continuing Step 1.6.3 coding. ~30 min plan-body amendment work; saves 1-2h of coding-time backtracking under stale sequencing.

Plan content is otherwise comprehensive + GREEN-ready. The sequencing issue is mechanical (re-ordering 4 step rows in BUILD-FORCED list + 1 deferral note in Step 0.5d).
