# /plan-check — v5.15 sprint cohesion audit

**Date:** 2026-05-12
**Master plan:** `plans/v5.15-live-readiness/MASTER.md`
**Sub-plans audited:** 5 (v5.15.0 / .1 / .2 / .3 / .4)
**Companion living doc:** `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`
**Total estimated effort:** ~18-22h across 5 sub-ships (~590 LOC + tests)
**Auditor:** /plan-check subagent
**Codebase verification HEAD:** branch `feat/v5.14-foxml-port-and-maker`,
commit `1752fde` (v5.14.post1) at master read time (pre-branch-creation)

---

## Verdict: **YELLOW**

Sprint composes cleanly at the architectural + integration level. All
6 TECH_DEBT closures map to specific sub-ships; all 5 plans share a
consistent invariant grammar (Hot path UNTOUCHED, HMAC chain byte
preservation, Parity-tested-by-construction); the cross-plan
integration matrix has no hard conflicts; the decoupling-endgoal
roadmap is correctly cross-referenced in every sub-ship's verification
gate.

The YELLOW status is **NOT** a structural/integration breakage. It is
a cluster of **stale-claim drift items in the sub-plans** where file
paths, function names, and helper struct names referenced for
boot-gate / normalize / hot-swap mechanics don't match what exists in
the current codebase. These are all fixable with mechanical plan
amendments before .B/.A coding starts — no rescope needed — but they
WILL cause Step 0 failures or wasted cycles during coding if not
corrected first. The drift cluster + 1 minor sub-plan ordering
inconsistency are the only blockers.

---

## Cross-plan integration matrix (5x5)

|  | v5.15.0 | v5.15.1 | v5.15.2 | v5.15.3 | v5.15.4 |
|---|---|---|---|---|---|
| **v5.15.0** ModelHandle | — | OK — .1 reads h.has_flags via STAMP_HAS API | OK — .2 trading_mode adds 1 FOREACH_STAMP_BOUND_CFG row; .0 unifies parser via same registry | OK — .3 stamp_emit_for_horizon uses STAMP_HAS/SET API + AUTOPOPULATE companions established in .0 | OK — .4 HotSwapSnapshot doesn't touch stamp body emit; HMAC chain preserved orthogonal to ModelHandle migration |
| **v5.15.1** Model Health | (mirror) | — | OK — .2 boot gate reads .1's failure_flags drift bits (MASK_FAILURE_FEATURE_HASH_DRIFT etc.) | OK — .3 multi-horizon stamping populates HANDLE_HAS bits + scaler.feature_registry_hash that .1's drift cluster mirrors | OK — .4 hot-swap unification touches strict-mode handling orthogonal to .1's drift cluster |
| **v5.15.2** Boot gate | (mirror) | (mirror) | — | **YELLOW** — .3 batch mode (multi-horizon training in foxml_suite) bypasses .2's boot gate by design (training-side, not engine-side) — INTENTIONAL but worth explicit doc | OK — .4 normalize pass runs BEFORE .2's gate per .4's Step 1 ordering note ("Called from EngineSharded_Run AFTER cfg parse + BEFORE LiveReadiness_Verify"); MASTER cold-pickup §2 lists .4 after .2 |
| **v5.15.3** Multi-horizon | (mirror) | (mirror) | (mirror) | — | OK — .4 hot-swap is engine-side only; .3 libgomp setenv is foxml_suite-side only; orthogonal binaries |
| **v5.15.4** Strict defaults | (mirror) | (mirror) | (mirror) | (mirror) | — |

**No RED cells.** The 1 YELLOW cell (v5.15.2 / v5.15.3) is by-design
boundary (training-binary vs live-binary) but should be made explicit
in v5.15.3's plan or MASTER architectural-invariants table to avoid
future ambiguity about whether multi-horizon worker stamping requires
trading_mode plumbing.

---

## Dependency edge validation

### Edge 1: v5.15.1 depends on v5.15.0 — VERIFIED

v5.15.1.A drift detection reads `HANDLE_HAS(h, BUILD_FLAGS_HASH)` and
`h.stamp_build_flags_hash` — APIs introduced by v5.15.0.A ModelHandle
migration. v5.15.1 plan correctly cites v5.15.0 as predecessor
(`Predecessor: v5.15.0` in YAML header + cross-reference at end). The
MASTER cold-pickup §2 has v5.15.1 SECOND after v5.15.0 — consistent.

### Edge 2: v5.15.4 depends on v5.15.2 — VERIFIED

v5.15.4.A `ControllerConfig_NormalizeForMode` reads `cfg.trading_mode`
which is introduced in v5.15.2.A. v5.15.4 plan correctly cites
`Predecessor: v5.15.2` + the normalize pass guard
`if (cfg.trading_mode != TRADING_MODE_LIVE) return;` references
`TRADING_MODE_LIVE` enum value defined in v5.15.2.A. MASTER cold-pickup
§2 has v5.15.4 LAST (consuming .2's field) — consistent.

### Edge 3: v5.15.3 independent of v5.15.0/.1/.2; inherits canonical patterns — VERIFIED with caveat

v5.15.3.A `stamp_emit_for_horizon` uses `STAMP_CFG_AUTOPOPULATE`,
`STAMP_MODEL_CONST_AUTOPOPULATE`, `STAMP_SET` APIs. These are
established at v5.14.8.A.merged (pre-sprint) and survive v5.15.0
unchanged. v5.15.0 only restructures ModelHandle storage layout — the
STAMP_* API surface remains stable. v5.15.3.A could in theory ship
BEFORE v5.15.0 because it doesn't consume any v5.15.0-specific symbol.

MASTER cold-pickup §2 says v5.15.3 is "independent of v5.15.1/.2/.3/.4
but inherits canonical patterns" but lists v5.15.0 as predecessor in
the dependency edges section. Practical-execution-wise this is fine:
v5.15.0 ships first to lock the ModelHandle/has_flags shape; v5.15.3
then ships on the established API. Just a minor ordering claim
ambiguity (independent in principle, after v5.15.0 in practice).

### Edge 4 (NOT IN PROMPT BUT REQUIRED): v5.15.2 depends on v5.15.0 — VERIFIED

v5.15.2's `trading_mode` field flows through:
- `verify_model_stamp` parser (post-v5.15.0.B refactor)
- ModelStampResult / StampInferenceCfgInputs struct gen (FOREACH_STAMP_BOUND_CFG auto-flow)
- STAMP_CFG_AUTOPOPULATE at production callers

All these surfaces are touched by v5.15.0. v5.15.2 plan correctly says
`Predecessor: v5.15.0 (ModelHandle migration); independent of v5.15.1`.

### No circular dependencies detected.

### Ordering verdict:

Strict critical path: v5.15.0 → (v5.15.1 || v5.15.2 || v5.15.3) → v5.15.4

In MASTER cold-pickup §2 the order listed is .0 → .1 → .2 → .3 → .4
which is FINE because (a) .1/.2/.3 are independent of each other so
sequential is safe + simpler, (b) .4 depends on .2 so .2 ships
before .4 which is preserved.

---

## TECH_DEBT closure coverage verification

| Entry | Sub-ship claimed | Code-edit scope | Verified |
|---|---|---|---|
| **TECH_DEBT-003** (verify_model_stamp parser refactor) | v5.15.0.B | data-driven dispatch table; ~150 LOC; documented at v5.15.0 .B step 1-3 | ✅ |
| **TECH_DEBT-005** (single-zoo + ensemble hot-swap strict-mode unification) | v5.15.4.B | HotSwapSnapshot<F> infrastructure + capture/revert/discard helpers applied at BOTH EngineSharded.hpp:2836 single-zoo AND :2846 ensemble surfaces; ~130 LOC | ✅ (broadened per MASTER claim "BROADENED to ensemble") |
| **TECH_DEBT-014** (ModelHandle X-macro migration) | v5.15.0.A | 14 uint8_t has_* → uint64_t has_flags + STAMP_HAS API + X-macro generation; ~400 LOC | ✅ |
| **TECH_DEBT-024** (breakeven_on_profit wire-up) | v5.15.2.C | parallel read site at PortfolioController.hpp:670 sister to breakeven_on_partial; DORMANT marker removed at LifecycleCfgFlagRegistry.hpp:58; ~50 LOC | ✅ |
| **TECH_DEBT-028** (PerCoreSnap bool-as-uint8 → bitmap) | v5.15.1.B | 4 bool fields (ml_scaler_present, drift_breached, drift_kill_tripped, core_kill_tripped) migrated to existing state_flags uint16_t via PerCoreStateFlagsRegistry.hpp; ~80 LOC | ✅ |
| **TECH_DEBT-033** (/readiness wider-build check) | v5.15.2.D | NEW ledger entry written + /readiness Check 26 added to SKILL.md; ~30 LOC | ✅ (plan correctly notes ledger entry MUST be added at .D Step 0 since TECH_DEBT-033 does NOT yet exist in ledger as of read time) |
| **CLAUDE.local.md "XGBoost+libgomp+pthread" landmine** | v5.15.3.B | `setenv("OMP_NUM_THREADS", "1", 1)` at foxml_suite.cpp:main() entry; v5.11.45 forced-clamp removed at BacktestPanels.hpp:3886-3912 | ✅ (landmine entry IS the queryable record per CLAUDE.local.md "deferred items must be queryable" rule; closure logged inline + workspace-private CLAUDE.local.md mutation documented) |

**Coverage: 6/6 closures + 1 landmine. All map to specific code-edit
scopes in their named sub-ship.**

Verified TECH_DEBT-003, -005, -014, -024, -028 entries exist in
`tick-trader-percore-workspace/DOCS/TECH_DEBT.md` at lines 120, 145,
367, 562, 618 respectively. TECH_DEBT-033 is correctly noted as
absent-pending in v5.15.2 plan.

---

## Decoupling roadmap cross-reference status

Each sub-plan's verification gate includes the required checkbox:

| Sub-ship | "decoupling roadmap entry written" gate item present? | Roadmap breadcrumb section exists? | Cross-references align? |
|---|---|---|---|
| v5.15.0 | ✅ at gate line "Decoupling-endgoal roadmap entry written..." | ✅ §v5.15.0 (POSITIONING: ⬆️ positive) | ✅ — pattern claims align (X-macro stamp body + bit-packed has_flags = mmap-friendly wire format) |
| v5.15.1 | ✅ | ✅ §v5.15.1 (POSITIONING: ⬆️ positive) | ✅ — pattern claims align (failure_flags bitmap mmap-friendly; alignas(64) drift cluster preserves cache-line independence) |
| v5.15.2 | ✅ | ✅ §v5.15.2 (POSITIONING: ⬆️⬆️ strongly positive) | ✅ — pattern claims align (trading_mode stamp-bound; table-driven kLiveReadinessChecks[]; cached predicates) |
| v5.15.3 | ✅ | ⚠️ **§v5.15.3 (POSITIONING: ⬆️⬆️⬆️ load-bearing) claims SCOPE NOT IN THE PLAN** | **YELLOW** — see HIGH finding below |
| v5.15.4 | ✅ | ✅ §v5.15.4 (POSITIONING: ⬆️ positive) | ✅ — pattern claims align (HotSwapSnapshot atomic release-acquire publication; capture/validate/publish/revert) |

**HIGH FINDING (decoupling-roadmap drift):** The §v5.15.3 breadcrumb
in `2026-05-12-decoupling-endgoal-roadmap.md:167-228` describes scope
that is **NOT in the v5.15.3 sub-plan**:

- Roadmap describes "FOREACH_CLI_MODE X-macro registry introduced;
  pure training functions extracted (train_X_impl); batch mode entry
  at foxml_suite.cpp:main(); GUI buttons rewired to execv-spawn child
  processes; per-run logging structure (logging/foxml_suite/<run_name>/)"

- Actual v5.15.3 sub-plan only delivers: stamp_emit_for_horizon helper
  extraction (.A) + libgomp setenv at main() (.B) + parallel-mode
  stamping (.C) + tests (.D). NO FOREACH_CLI_MODE registry. NO
  train_X_impl extraction. NO GUI button rewiring to execv. NO per-run
  logging structure changes.

The roadmap section §v5.15.3 was written assuming a much larger scope
than the actual v5.15.3 plan contains. The breadcrumb correctly notes
the libgomp landmine close, but the rest of the "scope" claims do not
match v5.15.3's verification gate. Either:
- (A) The breadcrumb was drafted earlier when v5.15.3 was planned at
  larger scope; v5.15.3 contracted to current scope; breadcrumb didn't
  re-narrow. → Amend the roadmap breadcrumb to match actual scope.
- (B) The CLI/registry/execv scope was deliberately moved to a future
  ship; breadcrumb should note "DEFERRED to v5.16 / future" with a
  clear redirect.

**Recommendation: amend the §v5.15.3 breadcrumb in the roadmap doc to
match the actual v5.15.3 sub-plan scope** (helper extraction + libgomp
fix + parallel stamping). The pre-decoupling readiness checklist line
"FOREACH_CLI_MODE covers train_horizon, train_single, train_multi,
run_full_validation; (v5.15.3 covers...)" should be REMOVED or moved
to a future ship breadcrumb.

---

## Anti-breadcrumb sweep results

Per the going-forward rule 2026-05-12, no v5.15 sub-ship introduces:
- Callback registries with fn pointers crossing GUI ↔ engine boundary (NONE)
- In-process-only state that can't be mmap-exposed (NONE)
- Mutex protecting cross-thread state where seqlock would work (NONE; v5.15.4 HotSwapSnapshot uses release-acquire which IS the seqlock-style pattern per CLAUDE.md item 5)
- Inline-only training entry points that don't survive process boundary (v5.15.3.B fixes the OPPOSITE — process-startup setenv makes future cross-machine training via SSH/systemd-run feasible)

**Anti-breadcrumbs section in roadmap doc is correctly empty**.

The roadmap doc's "Examples of what would go here if it happened"
section explicitly calls out callback-registries-with-fn-pointers and
in-process mutex — and v5.15.4's HotSwapSnapshot deliberately uses
atomic release-acquire instead of mutex. Good.

---

## HIGH findings (integration conflicts; must-amend before coding)

### HIGH-1: ControllerConfigParser.hpp does NOT exist; parser logic lives inside ControllerConfig.hpp

**Surface:** v5.15.2 sub-plan repeatedly references
`CoreFrameworks/ControllerConfigParser.hpp` as the file housing the
parser. **This file does not exist in the codebase**.

The actual parser logic for cfg-key matches lives at
`CoreFrameworks/ControllerConfig.hpp:2371-2381` (verified by
`grep -n "reconcile_mode" CoreFrameworks/*.hpp`). The MASTER plan
correctly cites `CoreFrameworks/ControllerConfig.hpp:2371-2381` as the
canonical reference for `reconcile_mode` parser, but v5.15.2 plan
header + .A Step 2 + .A Step 3 + Cross-references section all say
ControllerConfigParser.hpp.

**Impact:** v5.15.2.A Step 2 (`Parser ... in ControllerConfigParser.hpp
parse_csv_engine_config; mirrors reconcile_mode pattern at line
2371-2381`) — coding will Step 0 fail because the file path is wrong.
Operator/agent must redirect to ControllerConfig.hpp.

**Fix:** Replace all `CoreFrameworks/ControllerConfigParser.hpp`
mentions in v5.15.2 with `CoreFrameworks/ControllerConfig.hpp` and the
function name `ControllerConfig_Parse` (verified search returns
nothing for `parse_csv_engine_config` either — actual parser entry
point needs verification).

**Recommended Step 0 addition to v5.15.2.A:** `rg -n "parser_kv\|parse_csv\|parse_engine_config\|ControllerConfig_Parse" CoreFrameworks/ControllerConfig.hpp` — locate the actual parser function name + line range.

### HIGH-2: core_strategy_explicit[] cfg field referenced in v5.15.2.B boot gate but does NOT exist

**Surface:** v5.15.2.B `check_all_cores_strategy_explicit` function
reads `cfg.core_strategy_explicit[c]` (line in .B Step 1):

```cpp
for (int c = 0; c < cfg.num_cores; ++c) {
    if (!cfg.core_strategy_explicit[c]) return false;
}
```

This array field does NOT exist in `ControllerConfig<F>` (grep returns
zero hits). The boot gate cannot compile without this tracking
infrastructure.

**Same class** as v5.15.4.A `ControllerConfigKeyExplicit` struct that
.A acknowledges may not exist ("If no tracking infrastructure exists,
.A includes adding minimal tracking"). The v5.15.2.B plan does NOT
acknowledge that `core_strategy_explicit` similarly needs to be added.

**Impact:** v5.15.2.B Step 1 won't compile. Either core_strategy_explicit
[] must be added as new tracking infrastructure (~15-30 LOC + parser
hook), OR the check_all_cores_strategy_explicit predicate must be
reformulated to detect "core had default-fallback strategy" some other
way (e.g., sentinel value -1 for "unset").

**Fix:** Either:
- (A) Amend v5.15.2.A to include "Tracking infrastructure: add
  `cfg.core_strategy_explicit[N]` uint8 array initialized to 0; parser
  sets to 1 when `core_N_strategy=...` key parsed." Then v5.15.2.B can
  use it.
- (B) Use a sentinel-pattern: cfg.core_strategy[c] = STRATEGY_UNSET
  (new enum value) as default; LiveReadiness checks for any UNSET.
  Lower-LOC; consistent with `cfg.engine_arch` default sentinel
  precedent (verify exists).

### HIGH-3: ControllerConfigKeyExplicit struct does NOT exist; v5.15.4.A acknowledges but underestimates LOC

**Surface:** v5.15.4.A `ControllerConfig_NormalizeForMode` reads
`key_explicit.has_model_verify_strict` and `key_explicit.has_reconcile_mode`
from a `ControllerConfigKeyExplicit&` parameter. This struct + its
populator (parser-side hook to set has_* on each key seen) do NOT
exist.

The sub-plan acknowledges this gap: ".A includes adding minimal
tracking: a `ParserState` struct with a bitmap (or small set) marking
each key seen. Cost: ~30 LOC additional".

**Impact:** YELLOW-flag finding rather than RED-flag because the plan
acknowledges the gap, but ~30 LOC additional estimate seems
optimistic. Tracking which cfg keys are explicitly set requires:
- New struct `ControllerConfigKeyExplicit` (or extending existing)
- Parser hook: every cfg-key match sets the corresponding has_*
- Default-init in `ControllerConfig_Default<F>` to clear all has_*
- Threading through to `ControllerConfig_NormalizeForMode` call site
- Tests for the tracking infrastructure itself (separate from
  normalize tests)

Realistic LOC: 50-80 (parser hook is per-key, not single-site).

**Fix:** Amend v5.15.4.A LOC estimate 50 → 80-100. Or split: ".A0"
add tracking infrastructure + tests; ".A1" normalize pass. The
combined ".A" at "50 LOC + 1-1.5h" looks under-scoped given the gap.

**Plus tie-in to HIGH-2:** if HIGH-2 fix (A) is taken (add
core_strategy_explicit[] in v5.15.2.A), the same infrastructure could
be EXTENDED in v5.15.4.A to cover model_verify_strict + reconcile_mode.
Cohort-audit candidate: build a unified `ControllerConfigKeyExplicit`
struct in v5.15.2.A as part of the tracking infrastructure (CLAUDE.md
item 16 reuse-audit applies — do once, reuse twice).

### HIGH-4: EngineSharded_HotSwapSingleZoo does NOT exist as named function

**Surface:** v5.15.4.B Step 2 Site 1 calls
`EngineSharded_HotSwapSingleZoo(swap_zoo, cfg, c, new_path,
swap_backend)`. This function does NOT exist (grep returns 0 hits).

The actual single-zoo hot-swap is inline at EngineSharded.hpp:2836-2845
(verified: `CoreModelZoo<F>* swap_zoo = (CoreModelZoo<F>*)
state.cores[c].model_handle; if (swap_zoo == nullptr) {...} else {...}`).
Inline code does CoreModelZoo_Free + CoreModelZoo_Init + path-load (at
:2923-2945 region).

By contrast, `EngineSharded_HotSwapEnsemble` DOES exist as a named
function in `CoreFrameworks/EnsembleHotSwap.hpp:45` (verified).

**Impact:** v5.15.4.B Step 2 Site 1 cannot call the named function as
written. Either the function needs to be EXTRACTED first (refactor the
inline code at :2836-2945 into `EngineSharded_HotSwapSingleZoo` in a
new header `CoreFrameworks/SingleZooHotSwap.hpp` mirroring ensemble's
extraction pattern), OR the snapshot capture/revert pattern is applied
directly inline at the call site.

**Fix:** Either:
- (A) Add a ".B0" sub-tag: extract inline single-zoo swap into
  `EngineSharded_HotSwapSingleZoo` template function in
  `CoreFrameworks/SingleZooHotSwap.hpp` (mirrors `EnsembleHotSwap.hpp:45`
  pattern). Then ".B1" applies snapshot/revert at both named call
  sites uniformly.
- (B) Apply snapshot/revert inline at the existing :2836-2945 block
  without extraction. Less helpful for future maintenance but cheaper.

Plan should pick one explicitly. Current code-fragment claim is
unbuildable.

### HIGH-5: v5.15.3 decoupling-roadmap breadcrumb describes out-of-scope work

Already documented in "Decoupling roadmap cross-reference status"
above. Listed here for HIGH-priority visibility because:
- The breadcrumb claims FOREACH_CLI_MODE registry, train_X_impl
  extraction, GUI button execv rewiring, per-run logging structure —
  none of which are in the v5.15.3 sub-plan.
- The pre-decoupling readiness checklist line cites v5.15.3 as
  covering items it does not.
- Future readers of the roadmap will assume v5.15.3 delivered things
  it didn't.

**Fix:** Amend roadmap §v5.15.3 to reflect actual sub-plan scope:
helper extraction (`stamp_emit_for_horizon`) + libgomp setenv at
foxml_suite.cpp:main() + parallel-mode stamping. Move
FOREACH_CLI_MODE, train_X_impl, GUI execv rewiring, per-run logging
to a FUTURE ship breadcrumb (e.g., v5.16-cli-extraction-future or
similar). Or explicitly note "DEFERRED — not delivered in v5.15.3".

---

## MEDIUM findings (cohesion improvements)

### MEDIUM-1: ModelInference.hpp size estimate stale

v5.15.0 MASTER cold-pickup §7 says "`ML_Headers/ModelInference.hpp`
is ~2500+ lines". Actual: 1994 lines (verified via `wc -l`). Minor
stale claim; doesn't break anything but inflates effort estimate.
Update to "~2000 lines".

### MEDIUM-2: rc convention asymmetry between single-zoo + ensemble hot-swap

v5.15.4.B Note correctly identifies: "existing single-zoo code uses
`rc != 0` for failure; ensemble code at line 2861 uses `rc == 0` for
failure (legacy convention). v5.15.4.B preserves both conventions per
their existing call sites — does NOT normalize to one convention
(orthogonal cleanup)."

This is a structural-fix-preferred candidate per CLAUDE.md item 19.
Preserving two opposite conventions for the same semantic operation
(swap+validate failure handling) IS a recurring bug class shape —
future callers will get it wrong. Per the going-forward rule
2026-05-09, "would compile-time enforcement prevent the next instance?"
applies here. Two options:
- (A) Accept the asymmetry per v5.15.4.B claim; add a TECH_DEBT-NNN
  entry tracking the deferral with clear trigger ("next time either
  hot-swap surface is modified").
- (B) Normalize the convention in v5.15.4.B itself (small additional
  scope; either flip single-zoo or flip ensemble to match).

The plan-check recommends (B) because the unification IS the structural
work — leaving the convention split is a known-debt sibling that the
unification ship is the cheapest moment to close.

### MEDIUM-3: v5.15.2 wire-format byte preservation discipline

v5.15.2.A Step 3 says "the new line `trading_mode=0\n` appears at the
canonical position dictated by FOREACH_STAMP_BOUND_CFG row order —
APPENDED at end-of-cfg-section because we added it as the last row
before the macro close."

This is the correct discipline per CLAUDE.md item 22 (PRE/POST registry
split for canonical-emit-order preservation). However, **the actual
FOREACH_STAMP_BOUND_CFG registry does NOT have PRE_CFG / POST_CFG
halves** (verified: only single FOREACH_STAMP_BOUND_CFG in
StampBoundCfgRegistry.hpp:99). It's the STAMP_BOUND_MODEL_CONST
registry that has PRE/POST halves (FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG
at :267, FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG at :377).

v5.15.2 plan should clarify: trading_mode appends to the SINGLE
FOREACH_STAMP_BOUND_CFG (not PRE/POST split). The byte-preservation
discipline still applies — appending preserves all prior row positions
— but the citation to CLAUDE.md item 22 wire-format-byte-preservation-
discipline.md should reference the single-registry append-only
discipline, not the PRE/POST split rationale.

### MEDIUM-4: v5.15.2 effort estimate sanity-check

Sum: .A 1h + .B 1.5h + .C 30-45min + .D 30min = 3.5-4.5h. MASTER cold
pickup §7 reconciles "~280 LOC" / "4-5h" — consistent. But .B Step 1
contains ~150 LOC of LiveReadinessCheck<F> templates including 9
predicate functions; if some of these need infrastructure work
(HIGH-2 core_strategy_explicit + HIGH-3 tracking infrastructure
extensions), .B alone could grow to 3-4h.

If HIGH-2 fix (A) chosen: +30 LOC + 30-45 min to .A for tracking
infrastructure → v5.15.2 total ~5-6h. Still acceptable but tighter.

**Recommend:** explicitly budget +1h to v5.15.2 for tracking
infrastructure addition (Caramel can decide later).

### MEDIUM-5: v5.15.1 PerCoreSnap value-field cluster offset claim needs verification

v5.15.1.B Step 2 declares the new drift cluster `alignas(64)
uint64_t handle_feature_hash_at_load` with `static_assert(offsetof
... % 64 == 0)`. The claim assumes inserting "near end of struct" lands
at a 64-byte-aligned offset.

This MUST be verified empirically at Step 0 — PerCoreSnap is currently
sized with various uint8/uint16/uint64 fields scattered (not all
aligned by 64). The new cluster MIGHT land at an offset that requires
preceding padding to hit 64-byte alignment. Cluster alignas(64) on
field DECLARATION will force GCC to align the cluster, but if the
struct's preceding section ends at offset 47, GCC inserts 17 bytes of
padding ahead of the cluster — making `offsetof(... % 64 == 0)` pass
but adding hidden padding that affects sizeof + future cluster
positioning.

**Recommend:** add to v5.15.1.B Step 0:
```bash
# Verify PerCoreSnap current layout
sed -n '981,1200p' DataStream/EngineTUI.hpp  # show full struct
# After writing the cluster, verify NO unexpected padding:
g++ -std=c++17 -c -fdiagnostics-print-offsets ... # or static_assert pattern
```

### MEDIUM-6: v5.15.3 single-horizon perf regression open question unresolved

v5.15.3 plan §"Open question for Caramel (single-horizon slowdown
trade-off)" explicitly asks for operator approval before .B coding
starts. The plan-check confirms this question is unresolved as of
plan-write time. The plan's recommendation (unconditional setenv) is
the simplest fix.

**Recommend:** before v5.15.3.B coding starts, operator confirms the
trade-off (single-horizon ~3-4x slower vs multi-horizon ~5x faster).
The fork-isolation alternative (~150 LOC + IPC complexity) is the
fallback if operator prefers single-horizon speed.

---

## LOW findings (informational)

### LOW-1: ML_Headers/ModelInference.hpp ~2500 → 1994 LOC stale

Already in MEDIUM-1. Listed here too for visibility.

### LOW-2: tests count baseline

MASTER says "2904/2904 tests pass at v5.14.post1". v5.15.0 target
~+20 tests; v5.15.1 ~+10; v5.15.2 ~+15; v5.15.3 ~+15; v5.15.4 ~+10.
Sum: ~2974. MASTER sprint umbrella target says "~2950+ target".
Consistent within 25 tests; minor under-estimate. Fine.

### LOW-3: PerCoreSnap struct line number

MASTER cold-pickup §4 cites `PerCoreSnap` struct at
`DataStream/EngineTUI.hpp:981`. Verified — matches actual line.

### LOW-4: Hot-swap site line numbers

MASTER + v5.15.4 cite `EngineSharded.hpp:2836` single-zoo +
`EngineSharded.hpp:2846` ensemble + ":2855" alt cite. Verified actual:
:2835 single-zoo declaration, :2846 ensemble else-if. Plan says "~2855"
in some references. Off by 5-10 lines; not blocking but should be
mechanically fixed during Step 0.

### LOW-5: Verify_model_stamp parser line count claim

MASTER says "~700 LOC if-else chain". TECH_DEBT-003 says same. Plan
v5.15.0 step 0 includes the rg command to enumerate keys (`rg -n
"strcmp(key, \"[^\"]+\"\) == 0" ML_Headers/ModelInference.hpp | head
-50`). Expected: ~30 keys. This should be verified at Step 0 before
proceeding.

### LOW-6: v5.15.0.A Step 0 enumerate-has-fields claim

v5.15.0.A Step 0 says "Expected output: 14 fields, ~25-40 read sites,
~30-50 write sites". Verified field count = 14 ✓. Read/write site
counts unverified at plan-check time; will be enumerated empirically
during .A Step 0 — appropriate.

### LOW-7: scaler.feature_registry_hash drift bit detection logic

v5.15.1.A `cfg_binding_drift` detection iterates FOREACH_STAMP_BOUND_CFG
to compare each stamp-bound field's stamp_value vs runtime cfg.* value;
or-sets the bit if any mismatch.

Per CLAUDE.md item 21 STAMP_CFG_AUTOPOPULATE companion, this drift
check IS the natural extension point. If FOREACH_STAMP_BOUND_CFG gains
a `STAMP_CFG_DRIFT_CHECK_ONE` companion macro alongside the existing
AUTOPOPULATE_ONE + STAMP_COUNT_ONE companions, the drift-check
auto-generates per-row + future rows pick it up automatically. v5.15.1
plan doesn't explicitly call out this companion macro pattern; it
should, per CLAUDE.md item 13.

**Recommend:** v5.15.1.A explicitly defines the `STAMP_CFG_DRIFT_CHECK_ONE`
companion macro alongside the existing AUTOPOPULATE_ONE pattern; drift
check at TryLoadRole walks `FOREACH_STAMP_BOUND_CFG(STAMP_CFG_DRIFT_CHECK_ONE)`.
This closes Class 18 (mirror function pattern) — drift check auto-flows
with each new stamp-bound cfg field; can't be forgotten.

### LOW-8: v5.15.2 cohort-audit verdict for trading_mode

MASTER §v5.15.2 DOD analysis correctly applies the cohort-audit (cfg-
flag-eligibility-criteria.md "Cohort audit when new field has
siblings" section). Verdict: trading_mode is enum-valued, not boolean,
not BIT_FLAG-eligible. Direct uint8_t storage is correct; cohort
homogeneous (reconcile_mode is also uint8_t enum; model_verify_strict
is int tri-state but enum-valued). No migration needed.

Verified — discipline applied correctly. No finding; informational
acknowledgment.

### LOW-9: v5.15.3.A scaler_sha256_hex parameter signature

v5.15.3.A `stamp_emit_for_horizon` takes 17 parameters (verified by
inspection). This is high; v5.15.3 plan helper signature contains
direct hyperparam snap fields (snap_max_depth, snap_learning_rate,
etc.) which look like they could be bundled into a small struct.

Per CLAUDE.md item 16 reuse-audit, this is a candidate for further
helper refactor — but acceptable at v5.15.3 scope. Defer to a future
ship if it grows. Not blocking.

---

## Synthesis

**Sprint composes cleanly architecturally.** All 6 TECH_DEBT closures
map to specific sub-ships; dependency edges are correct; integration
matrix has no hard conflicts; the decoupling-endgoal roadmap doc
captures the right positioning patterns; invariant grammar (Hot path
UNTOUCHED, HMAC chain byte preservation, Parity-tested-by-construction)
is consistent across all 5 plans; cold-pickup completeness (10 fields)
is honored in MASTER.

**The YELLOW status is driven by a cluster of stale-claim drift items
in v5.15.2 + v5.15.4 + the v5.15.3 decoupling roadmap breadcrumb.** All
findings are mechanically fixable plan amendments — no rescope, no
re-design. The 5 HIGH findings break down to:

- HIGH-1 + HIGH-4: file path / function name references that don't
  match the codebase (ControllerConfigParser.hpp, EngineSharded_HotSwapSingleZoo)
- HIGH-2 + HIGH-3: tracking infrastructure (core_strategy_explicit,
  ControllerConfigKeyExplicit) referenced as if it exists; doesn't yet.
  Sub-plans should either add it as explicit pre-work OR adopt
  sentinel-value alternatives.
- HIGH-5: roadmap breadcrumb describes out-of-scope work.

**Recommended amendments before v5.15.0.A coding starts:**

1. v5.15.2 sub-plan: replace `ControllerConfigParser.hpp` with
   `ControllerConfig.hpp` everywhere; identify the actual parser function
   name; update .A Step 2 + Cross-references.
2. v5.15.2 sub-plan: amend .A to include `cfg.core_strategy_explicit[]`
   tracking infrastructure (HIGH-2 fix A); reconcile with
   HIGH-3 by extending to `model_verify_strict_explicit` +
   `reconcile_mode_explicit` so v5.15.4.A doesn't need to add it
   separately (cohort-audit per CLAUDE.md item 16). +30-50 LOC, +30-45 min.
3. v5.15.4 sub-plan: amend .B to clarify single-zoo refactor approach —
   either ".B0 extract `EngineSharded_HotSwapSingleZoo` template
   then .B1 apply snapshot/revert at both named sites" OR "apply
   snapshot/revert inline at the existing :2836-2945 block".
4. v5.15.4 sub-plan: MEDIUM-2 — normalize rc convention asymmetry as
   part of v5.15.4.B (single-zoo rc!=0 = failure; ensemble rc==0 =
   failure). This IS the unification ship; cheapest moment to close.
   Or write TECH_DEBT-NNN entry tracking the deferral.
5. Decoupling roadmap doc §v5.15.3: amend breadcrumb to reflect actual
   v5.15.3 scope (helper extraction + libgomp setenv + parallel
   stamping). Move FOREACH_CLI_MODE / train_X_impl / GUI execv rewiring
   / per-run logging claims to a future ship breadcrumb.
6. v5.15.0 MASTER: minor LOC estimate fix (ModelInference.hpp ~2500 →
   ~2000).

**Recommended additional pre-coding audits (sub-ship-specific):**

The MASTER §Audit cadence table is well-designed. The pre-coding
audit gate for v5.15.0 (HIGH-RISK) is documented as "/parity-check +
/trace-deps + /readiness + /dod-audit in parallel BEFORE coding
starts" — verified-needed given HIGH-1 to HIGH-4 findings.

**After the 6 amendments listed above, the sprint becomes GREEN.** No
rescope needed; all 6 TECH_DEBT closures remain in scope; all
decoupling positioning preserved. The sprint should ship as planned
once the drift cluster is mechanically resolved.

**Critical path:** v5.15.0 (HIGH-RISK) → v5.15.1 || v5.15.2 ||
v5.15.3 → v5.15.4. Estimated total effort 18-22h. Sprint expected to
fit within a single working session per CLAUDE.local.md "no defer for
effort-avoidance" rule.

---

## Recommendations

### Must fix before coding

1. **HIGH-1 fix:** Replace `ControllerConfigParser.hpp` references in
   v5.15.2 sub-plan with `ControllerConfig.hpp` + actual parser
   function name. Verify by `grep -rn "parse_csv_engine_config" CoreFrameworks/`
   first to find the actual entry-point name.
2. **HIGH-2 fix:** Amend v5.15.2.A to add `core_strategy_explicit[]`
   tracking. Reconcile with HIGH-3 by building unified
   `ControllerConfigKeyExplicit` struct as part of .A so v5.15.4.A
   reuses it. +30-50 LOC, +30-45 min to .A.
3. **HIGH-3 fix:** Verify HIGH-2 amendment covers v5.15.4.A's needs;
   amend v5.15.4.A LOC estimate upward (50 → 50-80) if HIGH-2 doesn't
   fully cover.
4. **HIGH-4 fix:** Amend v5.15.4.B to choose single-zoo refactor
   approach explicitly (extract function vs apply inline).
5. **HIGH-5 fix:** Amend roadmap §v5.15.3 to match actual v5.15.3
   scope.

### Worth fixing during coding

6. **MEDIUM-2:** Normalize rc convention asymmetry in v5.15.4.B (or
   write TECH_DEBT entry).
7. **MEDIUM-3:** Clarify v5.15.2 cite — trading_mode appends to single
   FOREACH_STAMP_BOUND_CFG (not PRE/POST split).
8. **MEDIUM-4:** Budget +1h to v5.15.2 for tracking infra.
9. **LOW-7:** v5.15.1.A define `STAMP_CFG_DRIFT_CHECK_ONE` companion
   macro alongside AUTOPOPULATE_ONE for future-proof drift check.

### Acceptable risk (don't block)

10. **MEDIUM-5:** v5.15.1.B Step 0 add empirical PerCoreSnap layout
    verification.
11. **MEDIUM-6:** v5.15.3.B operator consult on single-horizon perf
    trade-off before .B coding starts (already flagged in plan).
12. **LOW-1 / LOW-4:** Stale line numbers (ModelInference.hpp size,
    hot-swap site +/-5 lines) — fix mechanically during Step 0.
13. **LOW-9:** v5.15.3.A 17-param signature is acceptable for v5.15.3;
    defer struct-bundling refactor.

---

## Verdict: **YELLOW**

Start sprint with v5.15.0.A pre-coding audits AFTER amending the 5
HIGH findings above (estimated 30-45 min of plan amendments). Sprint
is structurally sound; the YELLOW is mechanical drift that's well-
bounded to specific file paths and tracking-infrastructure gaps —
none of which require redesigning sub-ships or rescoping deliverables.

Once amendments are committed, the sprint becomes GREEN and v5.15.0.A
pre-coding audit gate (/parity-check + /trace-deps + /readiness +
/dod-audit in parallel) can proceed per MASTER §Audit cadence.
