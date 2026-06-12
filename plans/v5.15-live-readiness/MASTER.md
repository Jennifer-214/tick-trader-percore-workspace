# v5.15 — Live-readiness hardening + ModelHandle structural unification — MASTER

> [!IMPORTANT]
> **▶ CURRENT STATE (2026-06-10) — the MASTER body below is HISTORICAL (drafted 2026-05-12, pre-`.E`); preserved as the original sprint-origin record, not the live state.**
> Most recent ship: **`v5.15.5.F.4d.1.E.0.9` — Ship B (decimal money)**, SHIPPED 2026-06-10 (engine `c2d0987`, suite 3285/0).
> The **`.E` sub-sprint** (per-node sharding + decimal-money numeric core + live-readiness) is the live trajectory — full index at `E-MASTER-REFERENCE.md`. **`.E.0` phase COMPLETE**: `.E.0.1` determinism net = tag `.E.0.6`; `.E.0.2` meta-error-tracking = tag `.E.0.5`; numeric core A/A.5/B = `.E.0.7/.8/.9` — all shipped.
> **`.E.0.10` Net-1 (pre-`.E.1` characterization net) IN-FLIGHT (updated 2026-06-11):** D-190 P&L-gross capital bug FIXED + the **cross-thread torn-read CLASS** found (9 sites, 3 live capital-control) → **`.E.1` is now a HARD LIVE-ENABLE GATE**. **Progress 2026-06-11:** oms-ts-1 fee-exact characterization (suite 3347/0 at that milestone); adversarial-default made BINDING (TECH_DEBT-164 part 3 + AR-8/AR-9); context-aware loading shipped (TECH_DEBT-163); **5-agent adversarial money-hunt → 14 findings (3 NEW HIGH capital bugs A1-A8)**, all documented (register + TECH_DEBT-168→171 + PARITY-039 + folded into `.E.1`/SWAR); **A1 CLOSED** (per-node TP/SL single-source helper + restore fix; 3-agent independent refute SOUND; suite **3368/0**); **H22 scale-invariance invariant** added; over-defer rule made BIDIRECTIONAL; module-scoped CLAUDE.md rollout (3/7). Pickup → the latest `handoffs/2026-06-11-*-handoff.md` (the ACTIVE one).
> **NEXT (after Net-1) = `.E.1` Foundation: Core→Node rename + per-node drainer absorption + multi-exchange registry** (v0.1 plan, **RED**/pre-audit-gate). Pre-`.E.1` gates per the `.E.0.5` DoD = Net-1 PERSIST characterization + guard-matrix-no-HOLE.
> **Live sprint-state SSoT for the `.E` era:** `CLAUDE.local.md` § Current sprint state + `E-MASTER-REFERENCE.md` + `decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md` (D-168..D-189).

**Date drafted:** 2026-05-12 (post v5.14 sprint close + v5.14.post1 patch)
**Branch:** `feat/v5.15-live-readiness` (CREATE from engine tag `v5.14.post1` =
commit `1752fde`, per 2026-05-12 amendment — v5.14 has known
BacktestPanels.hpp gui/suite compile errors that post1 fixed; branching
from v5.14 would break v5.15.0's wider-build verification gate. post1 fix
lines later get replaced by v5.15.3.B helper switch — second structural
touch of the same code).
**Predecessor:** v5.14 sealed at `v5.14`; post-release patch `v5.14.post1`
(commit `1752fde`) for `train_model_worker_fn` stamp body migration gap fix
**Rollback anchor:** `pre-v5.15` = `v5.14` (sprint baseline)
**Sister plans:**
- `subplans/2026-05-12-v5.15.0-modelhandle-migration.md` — HIGH-RISK
- `subplans/2026-05-12-v5.15.1-model-health-panel.md` — LOW-RISK
- `subplans/2026-05-12-v5.15.2-live-readiness-boot-gate.md` — MEDIUM-RISK
- `subplans/2026-05-12-v5.15.3-multi-horizon-worker-stamping.md` — LOW-RISK
- `subplans/2026-05-12-v5.15.4-live-mode-strict-defaults.md` — MEDIUM-RISK

---

## Why this sprint exists

v5.14 shipped the MATH layer (Ridge blending, composite confidence,
Thompson bandit, hot-swap ensemble, stamp body unification) + the
STRUCTURAL discipline (X-macro registries, AUTOPOPULATE companions,
parity-tested-by-construction). The engine boots, models load,
inference fires, drift is detected.

What's missing is the **operator-side surface**: visibility +
gates + strict defaults that turn "engine runs" into "engine
runs safely under live conditions." A `./engine` boot log review
2026-05-11 surfaced 5 specific gaps:

1. **feature_hash mismatch** silent in UI — drift detected, not surfaced
2. **Empty stamp secret** accepted in live mode — model verification toothless
3. **mlockall failed** soft-warning only — page faults under live load possible
4. **"4/4 handles missing grid_member_count"** — multi-horizon worker
   never wired to stamp emit path (TODO since v5.10.X)
5. **Hardcoded strategy fallback** when per-core not configured — operator
   may not realize cores defaulted

Plus the architectural gap from v5.14.8.A: ModelHandle survived the
Option 1 stamp body unification as an asymmetric struct (manual
declarations + inconsistent prefix policy + 16 uint8_t `has_*` direct
fields where ModelStampResult/StampInferenceCfgInputs got registry-driven
+ bit-packed `has_flags` via STAMP_SET()).

v5.15 closes **both classes** in one focused sprint: the operational
visibility surfaces AND the ModelHandle structural unification. Plus
absorbs **6 TECH_DEBT entries** with naturally-overlapping surface
area, per the "structural fix preferred when bug class can recur"
rule (CLAUDE.md item 19; CLAUDE.local.md going-forward rule
2026-05-09).

**Operator framing 2026-05-12:** *"lets fully deal with these,
remember even if its more work today, creating solutions that make
it easier going forward are preferred."* — Caramel.

---

## Architectural invariants (PRESERVE through sprint)

| Invariant | Verification |
|---|---|
| **Hot path UNTOUCHED** | All new work is slow-path-only or boot-only. `BG_Evaluate` / `SG_Evaluate` / `ExecutionCore_Tick` zero changes. Verified via `tools/calls_graph_diff.sh` + bench gate. |
| **HMAC chain byte-equivalent** | v5.15.0 ModelHandle migration MUST NOT change canonical stamp body byte layout (registry order preserved; PRE_CFG/POST_CFG halves unchanged). v5.15.4 cfg-default-flip MUST NOT change stamp body emit at the canonical byte level. Verified via round-trip HMAC test + SHA-256 lock on representative stamps. |
| **Forward-compat Surface G `has_*` flags** | v5.14-era stamps MUST load cleanly on v5.15 engine (no `MODEL_FORMAT_VERSION` bump). Verified via legacy-stamp load test. |
| **Parity-tested-by-construction (item 15)** | Every train→serve handoff surface touched (trading_mode cfg field stamp-binding, ModelHandle field re-route, multi-horizon worker stamp emit) gets a registry/binding/snapshot rather than ad-hoc test. New `trading_mode` stamps via FOREACH_STAMP_BOUND_CFG. |
| **Branchless on hot path** | Zero new hot-path branches. Slow-path predicate caches (`is_live` etc.) use cached state at slow-path entry (item 18(c)). |
| **No mode field except via stamp-bound cfg** | New `trading_mode` cfg field MUST be stamp-bound (model carries its training-time mode) so future paper-vs-live divergence is auditable. |
| **Default cfg = pre-v5.15 behavior** | `trading_mode = 0` (PAPER) is default; legacy cfgs unset = PAPER; behavior unchanged unless operator explicitly sets `trading_mode=live`. |
| **No new TECH_DEBT** | All 6 absorbed entries close; no "deferred substantial-progress" downgrades unless honestly required. |

---

## Sprint sizing (post-amendments 2026-05-12)

| Sub-ship | LOC | Time | Risk | Key amendments |
|---|---|---|---|---|
| v5.15.0 | ~580 | 5-6h | HIGH | comprehensive Step 0 grep (caught missed ModelValidation.hpp + FeatureRegistryOverlay.hpp sites); Option C shared MASK_STAMP_HAS_* bit positions; file:line corrections |
| v5.15.1 | ~220 | 3-4h | LOW | FOREACH_ARCH_FIELD_DRIFT new registry; drift consolidation into existing CFG X-macro loop (closes /merge-scan HIGH-1) |
| v5.15.2 | ~330 | 4-5h | MEDIUM | FOREACH_LIVE_READINESS_CHECK X-macro (closes /merge-scan MEDIUM-2); ControllerConfig.hpp:2371 parser location fix |
| v5.15.3 | ~200 | 3.5-4h | MEDIUM | Stamp_AssembleAndEmit helper from RFV (closes PARITY-020 + PARITY-021 structurally); FullValidationResults plumb-through (3 req_grid_* fields appended); libgomp setenv at foxml_suite.cpp:main(); v5.11.45 forced-serial WORKAROUND REMOVED; FOREACH_CLI_MODE DEFERRED to TECH_DEBT-034 |
| v5.15.4 | ~330 | 5-6h | MEDIUM+ | shadow-load (`aligned_alloc(64)` + `__atomic_exchange_n` + Free-old) replaces broken HotSwapSnapshot (closes PARITY-023); `alignas(64)` retrofit on EnsembleModelZoo + CoreModelZoo + size static_asserts; ControllerConfigKeyExplicit uint16_t bitmap; DoubleBufferedAtomic<T> DEFERRED to TECH_DEBT-035 |
| **Total** | **~1660** | **21-25h** | — | **~6-8 days** (-190 LOC vs pre-amendment after closing speculative scope-creep + adding structural primitives) |

## Sub-ship phasing

### v5.15.0 — ModelHandle X-macro migration + verify_model_stamp parser refactor [HIGH-RISK; 5-6h]

**Surface:** `ML_Headers/ModelInference.hpp` ModelHandle struct (~16 has_*
direct fields → `uint64_t has_flags` bit-packed) + `verify_model_stamp`
parser (~700 LOC if-else chain → data-driven dispatch table).

**Why bundled:** ModelHandle migration touches every caller that reads
`h.has_<field>` and every site that populates ModelHandle.has_* from the
parser. The parser refactor closes the same Class 18 mirror (FOREACH_*
emit was registry-driven at v5.14.8; parse was left manual). Both sides
of the boundary become registry-driven together. Closing them in
separate ships would have us touching ModelHandle twice.

**TECH_DEBT closures:** -014 (ModelHandle migration) + **-003**
(verify_model_stamp parser refactor)

**Sub-tags:**
- .A — ModelHandle struct rewrite via X-macro generation; STAMP_HAS/SET
  bitmap macros; ~14-20 caller migrations (CoreModelZoo, EngineSharded
  boot, StrategyParameters reads, tests)
- .B — verify_model_stamp parser → data-driven dispatch table
  (table-of-`{key, parser_fn, target_offset, mask_bit}` walked at parse
  time; adding a new key becomes a 1-row registry addition)
- .C — HMAC round-trip + byte-equivalence tests; legacy-stamp load test
  for forward-compat verification

**Pre-coding audit gate:** `/parity-check` + `/trace-deps` + `/readiness`
+ `/dod-audit` in parallel BEFORE coding starts. Same class as
v5.14.8.A.merged (which had the train_model_worker_fn site miss → post1
patch). The mechanical-migration class requires the per-site verification
list, not "rebuild and see if test passes."

### v5.15.1 — Model Health CollapsingHeader + PerCoreSnap bitmap [LOW-RISK; 3-4h]

**Surface:** `GUI/MLStatusPanel.hpp` (new CollapsingHeader "Model Health"
between existing "Ensemble (multi-horizon)" + "Thompson Bayesian
dashboard") + `MemHeaders/FailureModeRegistry.hpp` (FOREACH_FAILURE_MODE
extension: ~7 new BIT_FLAG entries) + `DataStream/EngineTUI.hpp`
PerCoreSnap (4 bool-as-uint8 fields → uint8_t `per_core_state_flags`
bitmap; existing `state_flags` uint16_t may absorb if headroom permits).

**New failure-mode entries (BIT_FLAG storage class):**
- FEATURE_HASH_DRIFT (feature_registry_hash at load vs current)
- LABEL_HASH_DRIFT (label_registry_hash at load vs current)
- BUILD_FLAGS_DRIFT (build_flags_hash at load vs current)
- SCALER_DRIFT (scaler.feature_registry_hash vs handle.feature_registry_hash)
- CFG_BINDING_DRIFT (stamp-bound cfg field count or value mismatch)
- STAMP_HMAC_NOT_VERIFIED (held_out_stamp_secret was empty at load)
- MODEL_AGE_WARN (training_timestamp_us > model_max_age_hours)

Confirm uint16_t failure_flags headroom (currently 2 entries pre-.1; +7 =
9 of 16 slots used) OR expand to uint32_t if needed.

**TECH_DEBT closures:** -028 (PerCoreSnap bool-as-uint8 → bitmap)

**Display↔execution invariant (CLAUDE.md item 12):** every new
PerCoreSnap field gets its GUI render in the same sub-ship. The 4
existing fields being bitmap-migrated keep their existing GUI renders.

### v5.15.2 — Live-readiness boot gate + cfg.mode introduction + breakeven_on_profit wire-up + /readiness wider-build [MEDIUM-RISK; 4-5h]

**Surface:** `CoreFrameworks/EngineSharded.hpp` boot path (new
LiveReadiness_Verify gate; cfg_mode enum dispatch) +
`CoreFrameworks/ControllerConfig.hpp` (NEW `trading_mode` cfg field as
uint8 enum) + `CoreFrameworks/ControllerConfigParser.hpp` (string-keyed
enum parse, mirroring `reconcile_mode` precedent at line 2371-2381) +
`CoreFrameworks/PortfolioController.hpp` (breakeven_on_profit wire-up
near line 670 where `breakeven_on_partial` is already read).

**cfg.mode introduction (structural design):**

```cpp
// New enum near reconcile_mode (~line 855 in ControllerConfig.hpp):
enum TradingMode : uint8_t {
    TRADING_MODE_PAPER  = 0,  // default; gates default-off
    TRADING_MODE_LIVE   = 1,  // pre-flight REFUSE on missing items
    TRADING_MODE_SHADOW = 2,  // future: live data + simulated fills
};
uint8_t trading_mode;  // TradingMode; default 0 (PAPER)
```

- Parser: `trading_mode=paper|live|shadow` string-keyed (mirrors
  reconcile_mode at 2371-2381)
- Stamp-bound via `FOREACH_STAMP_BOUND_CFG` — model carries training-time
  mode for audit trail (parity-tested by construction)
- Slow-path predicate cache: `gate_state.is_live` derived once at
  slow-path entry (mode rarely changes; item 18(c) cached predicate)
- Legacy cfgs default unset → PAPER → behavior unchanged

**Pre-flight checklist (REFUSE when `trading_mode == LIVE` and any item
fails; WARN otherwise):**

1. `held_out_stamp_secret` nonempty
2. `mlockall` succeeded (cfg.require_mlockall + mlockall() syscall OK)
3. All cores have explicit `core_N_strategy` cfg (no hardcoded fallback)
4. All cores have model loaded if strategy is ML
5. `model_max_age_hours` > 0 AND no stale-model handles
6. `feature_registry_hash` matches across all loaded handles
7. `label_registry_hash` matches across all loaded handles
8. `build_flags_hash` matches across all loaded handles
9. No `STAMP_HMAC_NOT_VERIFIED` failure flags set after model load

**breakeven_on_profit wire-up (TECH_DEBT-024 close):**

Located dormant entry at `CoreFrameworks/LifecycleCfgFlagRegistry.hpp:58`
(`MASK_LIFECYCLE_CFG_BREAKEVEN_ON_PROFIT` defined; zero read sites).
Sister `breakeven_on_partial` IS wired at
`CoreFrameworks/PortfolioController.hpp:670`. Wire-up adds a parallel
read site for breakeven_on_profit triggered when position crosses net
profit (not partial fill). ~30-50 LOC + test. Updates registry comment
to remove "DORMANT" marker.

**TECH_DEBT-033 /readiness skill wider-build check:** Add Check N+1 to
`/readiness` skill: verify last sprint's close included `./build.sh gui
suite tsan asan all` (not just `test`). v5.14.post1 was the warning
shot; structural fix is the skill-side gate.

**TECH_DEBT closures:** -024 (breakeven_on_profit wire-up) + -033
(wider-build check)

### v5.15.3 — Multi-horizon worker stamping + libgomp pthread-race fix (CLAUDE.local.md landmine close) [MEDIUM-RISK; 2.5-3h]

**Surface:** `Backtest/BacktestPanels.hpp:3792` (`train_multi_horizon_worker_fn`)
+ per-horizon FV helper at `:3419`. Boot log "4/4 handles missing
grid_member_count" surfaces this: multi-horizon worker writes models but
never calls `stamp_write_for_model`. Single-horizon path (post-v5.14.post1)
properly stamps via `train_model_worker_fn` at line 3206.

**Canonical references for the pattern application:**
- `Backtest/BacktestEngine.hpp:1147-1220` (`Backtest_RunFullValidation`)
- `Backtest/BacktestPanels.hpp:3206-3266` (`train_model_worker_fn`,
  post-v5.14.post1)

**Apply:** assemble `StampInferenceCfgInputs` via
`STAMP_MODEL_CONST_AUTOPOPULATE` companion; call `stamp_write_for_model`
per horizon after each model file write. HMAC chain implications: each
stamp carries its own grid_member_count + horizon_idx + horizon_count;
all 3 fields already in FOREACH_STAMP_BOUND_MODEL_CONST (verified during
v5.14.8.E).

**Parallel-mode bundled** (Caramel 2026-05-12 — *"i dont really wanna
defer this, we should come up with a fix"*): the v5.11.45 segfault
landmine gets the proper fix already documented in CLAUDE.local.md
("Known landmine" 2026-05-07): `setenv("OMP_NUM_THREADS", "1", 1)` at
`foxml_suite.cpp:main()` BEFORE any pthread or library init. libgomp's
team-pool allocation race eliminated because all teams have size 1 → no
allocation needed → no race surface. Forced-serial workaround at
`BacktestPanels.hpp:3886-3912` removed; default `multi_horizon_max_threads`
behavior restored.

**Trade-off:** XGBoost loses internal OpenMP parallelism (single-horizon
training ~3-4x slower on multi-core CPUs); parallel multi-horizon trains
N horizons in ~per-horizon-time (N-x speedup for grid workflows). Net
throughput favorable for grid-training-heavy workflows. ./engine (live
binary) unaffected — engine doesn't run XGBoost training; inference is
single-threaded per CLAUDE.md item 18.

### v5.15.4 — mode=LIVE strict defaults + hot-swap unification (single-zoo + ensemble) [MEDIUM-RISK; 3.5-4.5h]

**Surface:** `CoreFrameworks/EngineSharded.hpp` boot (~line 2820,
single-zoo hot-swap site for TECH_DEBT-005) + post-parse normalize pass
(new function `ControllerConfig_NormalizeForMode` at parse-end) that
applies `trading_mode == LIVE` default-flips.

**Strict default-flips when `trading_mode == LIVE` and operator didn't
override:**

- `model_verify_strict` 0 → 1 (was WARN; becomes STRICT)
- `reconcile_mode` 1 (WARN) → 0 (STRICT) — if dry_run not explicitly set
- `cfg.held_out_stamp_secret` empty → boot REFUSE (already in v5.15.2's
  checklist; this is the corollary on parse side)

**TECH_DEBT-005 unification (hot-swap strict-mode handling via shadow-load):**

Boot does Free + null + flag on validate failure. Hot-swap dispatcher
in `EngineSharded.hpp` (single-zoo + ensemble) both do
flag-only (v5.10.0c "log-and-leave" semantics; the TODO comment
notes it). [Line anchors stripped — pre-`.B.6` subfolder split.]

**Plan-draft 1 (capture-pointer-and-revert) had a FATAL FLAW** caught by
/parity-check PARITY-023: `_Free` destroys data IN-PLACE; captured
pointer points at freed memory after the swap; revert impossible.

**Correct fix: shadow-load pattern (NEW DESIGN_SPEC).** Allocate NEW
ezoo/zoo into SEPARATE memory via `aligned_alloc(64, sizeof(T))`; load
+ validate into the new allocation; atomically swap pointer via
`__atomic_exchange_n` ONLY after validate succeeds; Free OLD state
AFTER swap (single-owner: per-core slow-path thread is sole reader of
container pointer; safe to Free immediately).

Plus: **`alignas(64)` retrofit on EnsembleModelZoo + CoreModelZoo**
(neither currently has explicit alignment despite containing
cache-aware members — ModelHandle alignas(64) post-v5.15.0;
RidgeWeights AVX-512 vectorized per item 25). Required for
`aligned_alloc(64, sizeof(T))` to actually satisfy member alignment.

~330 LOC + tests. NEW DESIGN_SPEC: `shadow-load-state-transition-pattern.md`.

**TECH_DEBT closures:** -005 (hot-swap strict-mode unification)

---

## v5.15.5 series (MASTER amendment 2026-05-18 — pipeline catch-up)

**Status: substantial sub-ship series not previously catalogued in MASTER.** MASTER last touched 2026-05-11; the v5.15.5.B / .C / .F series (universal cfg field registry consolidation; cfg-stamp-binding framework; cross-tool decoupling) shipped/in-flight without MASTER updates.

This section is a catch-up index — per-ship detail lives in the respective subplans/postmortems; this section provides navigation.

### v5.15.5.B — EventLoopState cache-layout sweep + 9 Class-18 mirror closures [SHIPPED]
- Tag: `v5.15.5.B.*`
- 9 mirror-state instances closed structurally; foundational for mmap-mediated decoupling
- Decoupling-positioning: ⬆️⬆️⬆️ STRONGLY POSITIVE per `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`

### v5.15.5.C — OrderManagerState cache-layout sweep + bit-packing + wire-format registry [SHIPPED]
- Tag: `v5.15.5.C.*`
- OMS cluster reorg + multi-bit state encoding substrate
- Decoupling-positioning: ⬆️⬆️⬆️ STRONGLY POSITIVE

### v5.15.5.F.4b/c/c.3/d — Universal cfg field registry framework consolidation [SHIPPED]
- Series: `.F.4b` (boolean subset; KIND_BOOL) → `.F.4c` (KIND_DOUBLE/_PCT subset; Path γ correction Option E) → `.F.4c.3` (per-core sharding + Class 27 closure + WIP2d-1.B.0c CI tool) → `.F.4d` (STAMP_BOUND derived filter framework; sister specs landed)
- Closes TECH_DEBT-009 PARTIAL (boolean + KIND_DOUBLE subsets); H15/H16/H17/H18/H19/H20 codified
- NEW DESIGN_SPECS landed across series: universal-cfg-field-registry-pattern, type-trait-dispatch-via-tt-namespace, categorical-tag-applicability-pattern, branchless-dispatch-discipline, audit-scope-taxonomy, decision-time-data-binding-pattern, multi-state-dispatch-with-per-state-update-metadata, sidecar-override-pattern-for-registry-auto-flows, meta-registry-pattern-for-codebase-registry-discipline, metadata-bit-driven-derived-filter-framework, framework-composition-overview

### v5.15.5.F.4d.1 — Cfg-derived consumer framework + cross-tool elimination [IN-FLIGHT]
- `.A` (LANDED 2026-05-17): framework primitive infrastructure; metadata-bit-driven-derived-filter-framework Option E first canonical
- `.B.1` (LANDED 2026-05-17): NEW `MemHeaders/CfgGateRegistry.hpp` framework consolidation; sidecar pattern + 3 derived-filter consumer template fns + 12 sister-extension verdicts. NEW DESIGN_SPECS: cfg-derived-consumer-framework + canonical-sister-extension-discipline + failure-attribution-buffer-pattern
- `.B.2` (LANDED 2026-05-17): cohort migration; 15 cfg fields flag STAMP_BOUND_CFG_DERIVED; FOREACH_ML_CFG_FLAG 5→6 col migration; COHORT_GATE_* macros codified
- **`.B.3` (IN-FLIGHT 2026-05-19): Legacy empty-out + cross-tool decoupling via Phase L + Phase K 47-globals registry-default sweep (v1.16 scope expansion 2026-05-19 per Caramel "no defers" directive).** Plan body: `subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.16. Engine state at WIP-checkpoint 7 (Step 1.6.2 cohort bit-add + Step 0.5d.b/c verified covered + Step 1.5 INFERENCE_CFG_AUTOPOPULATE elimination LANDED 2026-05-19). Scope: Steps 1.6.2 ✓ → 0.5d.b/c ✓ → 1.5 ✓ → Phase F same-commit trio (Step 1.6.4 + 1.6.7 + 1.6.8' **Phase L**) → 1.6.6 → Step 2 (legacy registry deletion FORCED LAST) → Steps 8.5 + 8.6 (Phase K NEW v1.16: spec extension + TECH_DEBT-107 47-globals sweep) → Steps 3-9 ship close. **Phase L is framework-driven CLI binary `tools/stamp_model_cli.cpp` replacing `tools/stamp_model.sh` (closes TECH_DEBT-001 — oldest open item; 3 major versions overdue).** Estimated ~17-23h focused coding from current state (~3.5-4h v1.16 Phase K addition). **CLOSES 14 TECH_DEBT entries total** (-001/-018/-093/-094/-095/-096/-097/-098/-099/-100/-102/-104/-107 NEW v1.16/-109); NEW 6 entries (-101/-103/-105 [folds to .D]/-106 [folds to .D]/-110/-111 [folds to .D]); net -8 (was -6 pre-v1.16). **v1.16 sprint arc adjustment:** `.C` adds per-core override emission CLI (2nd canonical of framework-driven-cli-binary-pattern → proves pattern + enables CI tool at `.D`); `.D` consolidates TECH_DEBT-105+106+111 into ONE `tools/check_framework_consumer_invariants.py` (sister to `registry-coverage-ci-check-pattern.md` Shape B). After `.D`, framework consolidation truly locked; only categorical/trigger-based deferrals remain.
- **`.B.4` (SHIPPED 2026-05-27): Train-serve execution-layer parity structural extract + B-full SHARDED centralized-arch full surface deletion + Phase Cx-cfg-cohort comprehensive cfg field re-categorization.** Plan body: `subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md` v1.7.6 (5 path iterations Path 1→2v5). Postmortem: `postmortems/2026-05-27-v5.15.5.F.4d.1.B.4-postmortem.md`. WIP-12 framework layer extract → WIP-13 BACKTEST slow-path migration → WIP-14a operator-facing-doc cohort + stale comment cleanup → WIP-14b 51-site `engine_arch=centralized` SHARDED full surface deletion (B14 1st canonical leaves-first ordering at OPERATOR-USE layer) → WIP-15 Phase C.4.5 PARITY-031 closure (BACKTEST_REGIME_SAMPLE_CORE named constant) + Phase C.6 parity_harness `--pay-fees-in-bnb` extension → WIP-16 9-field GLOBAL re-categorization + 2 H14 violation closures (enable_mtm_kill_switch + sl_cooldown_adaptive → CFG-FLAG BITMAP) + NEW EMIT_PER_CORE_CFG_DEFAULT_GLOBAL_MIRROR walker. **Closes 7 PARITY entries** (026/027/028/029/030/031/032). **NEW DESIGN_SPECS**: `cfg-field-categorization-discipline.md` (Stage 2 DRAFT v1.0; 4-category decision tree + 5-step re-categorization migration + sister-pattern co-location + DOD audit). **Stage promotions**: M5 (train-serve execution-layer parity) Stage 2→3 first canonical via EngineCommon extract; M6 (body-content arg enumeration) Stage 2→3 via WIP-12 helper extracts; M7 (structural enforcement when memory insufficient) Stage 2→3 via B-Plus v0.4 generator mode + /capture-audit Check 8 mechanical sidecar; B14 (multi-surface deletion ordering) Stage 2→3 first canonical via WIP-14b 51-site cohort; B15 (unconditionalization latent assumption audit) Stage 2 DRAFT 1st instance (Stage 3 deferred to 2nd canonical). **Class catalog updates**: Class 25 recurrence_count 2→3 (Cx-B exit_threshold cosmetic fix); Class 26 recurrence_count 1→11 (10 NEW worked instances from 9-field GLOBAL re-categorization); Class 33 NEW (consumer-enumeration-undercount on deletion). **5 NEW sister memories**: feedback_operator_pushback_as_audit_signal, feedback_categorize_by_consumer_pattern_not_field_name, feedback_cfg_field_categorization_at_registry_add_time, feedback_no_question_boxes (canonical file; M7 escalation evidence), feedback_motivated_collaborator_for_caramel (amended). **NEW /readiness Check 44** (cfg field categorization plan-time verification; sister to CI Check 8 commit-time). Tests: 3215/0 (verified at ship close; earlier 3217 claim was pre-WIP-16 baseline). GPG-signed tag `v5.15.5.F.4d.1.B.4`. 18 commits ahead of origin pushed at ship close.
- **`.B.5`-`.B.11` (NEW; QUEUED 2026-05-25): File-size discipline maintenance umbrella.** Sibling-umbrella plan body: `subplans/2026-05-25-v5.15.5.F.4d.1.B-file-size-maintenance.md`. Closes TECH_DEBT-029 + TECH_DEBT-114 structurally across 7 ships. Codifies subfolder split pattern as Stage 3 first canonical at `.B.6` ship (NEW addition to `file-size-split-discipline.md` v1.0 → v1.1). ~7-12 days focused total. Per-ship plan bodies drafted at planning-time per `feedback_plan_right_not_fast`.
- `.C / .D / .F.4e` future ships: per `feedback_new_plans_use_future_oriented_template`; details when scoped

**Decoupling-positioning across .F.4d.1.B series:** ⬆️⬆️⬆️ STRONGLY POSITIVE — first framework-driven CLI binary precedent (Phase L) enables FOREACH_CLI_MODE registry application at decoupling sprint; cfg-stamp-binding never-refactor-again at runtime + cross-tool surfaces.

**See:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` for in-flight ship details; `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` for accumulated breadcrumbs.

---

## TECH_DEBT closure table

| Entry | Sub-ship | Closure form |
|---|---|---|
| **TECH_DEBT-003** | v5.15.0 | ✅ CLOSED — `verify_model_stamp` parser refactored to data-driven dispatch table; new keys = 1-row registry addition |
| **TECH_DEBT-005** | v5.15.4 | ✅ CLOSED — hot-swap (single-zoo + ensemble) unified via shadow-load pattern (`aligned_alloc(64)` + `__atomic_exchange_n` + Free-old); replaces broken HotSwapSnapshot design (PARITY-023 fatal flaw) |
| **TECH_DEBT-028** | v5.15.1 | ✅ CLOSED — PerCoreSnap 4 bool-as-uint8 fields migrated to existing `state_flags` uint16_t bitmap with 4 new MASK_* constants |
| **NEW TECH_DEBT-034** | (deferred to v5.16+) | FOREACH_CLI_MODE registry + batch mode CLI + per-run logging structure — speculative scope cut from v5.15.3 after root-cause reframe; foundation prepared by v5.15.3.A helper extraction |
| **NEW TECH_DEBT-035** | (deferred to v5.16+) | Engine-side state-exposure protocol + DoubleBufferedAtomic<T> template extraction — premature for v5.15.4 (HotSwap is single-owner; doesn't need it); BinanceDepth.hpp:80-89 stays as canonical precedent |
| **CLAUDE.local.md landmine** | v5.15.3.C | ✅ FIXED — XGBoost+libgomp+pthread segfault via process-startup `setenv("OMP_NUM_THREADS", "1", 1)`; v5.11.45 forced-serial workaround REMOVED |
| **TECH_DEBT-014** | v5.15.0 | ✅ CLOSED — ModelHandle migrated to FOREACH_STAMP_BOUND_MODEL_CONST X-macro generation; bit-packed `has_flags` uint64_t |
| **TECH_DEBT-024** | v5.15.2 | ✅ CLOSED — `breakeven_on_profit` wired in `PortfolioController.hpp` ratchet path; "DORMANT" marker removed |
| **TECH_DEBT-033** | v5.15.2 | ✅ CLOSED — `/readiness` skill Check N+1 added (verify last sprint's close ran wider build, not just `test`) |

**Total: 6 closures.** Each MUST update `tick-trader-percore-workspace/DOCS/TECH_DEBT.md`
in the corresponding sub-ship per the auto-write contract (CLAUDE.local.md going-forward rule 2026-05-09).

---

## Audit cadence (per Caramel's 2026-05-10 rule)

| Sub-ship | Risk | Pre-coding audit | Sub-ship-close audit |
|---|---|---|---|
| v5.15.0 | HIGH | `/parity-check` + `/trace-deps` + `/readiness` + `/dod-audit` in parallel BEFORE coding | `/parity-check` GREEN; HMAC byte-equivalence proven |
| v5.15.1 | LOW | none | `/merge-scan` for FOREACH_FAILURE_MODE reuse opportunities |
| v5.15.2 | MEDIUM | `/parity-check` (cfg parser + stamp-binding for new trading_mode); `/dod-audit` (slow-path-gate-registry-pattern for boot gate) | `/dod-audit` GREEN; new trading_mode stamp-bound + parity-tested |
| v5.15.3 | MEDIUM | `/parity-check` (cross-mode byte-equivalence of serial vs parallel per-horizon stamps; libgomp setenv side-effects) + `/dod-audit` (helper extraction; landmine-close documentation discipline) | ASan + TSan clean under 3/8-thread parallel training; engine load test verifies no `grid_member_count` warnings |
| v5.15.4 | MEDIUM | `/parity-check` (cfg-default-flip MUST NOT change stamp body emit bytes); `/dod-audit` (snapshot infrastructure for hot-swap unification) | `/parity-check` GREEN; legacy-cfg load test verifies no behavior change |

**Mid-sprint audit suggestions fire when:** v5.15.0 HIGH-RISK ship closes
→ before v5.15.1/.2/.3/.4 inherit any new patterns; new ModelHandle
canonical layout field-tested for first time → audit before v5.15.3
multi-horizon worker uses the same pattern.

---

## Verification gate (sprint close: v5.15 umbrella)

- [ ] All tests pass (~2904 → ~2950+ target; +N new tests across sub-ships)
- [ ] `./build.sh test` GREEN
- [ ] `./build.sh gui suite tsan asan all` GREEN (NEW post-v5.14.post1 discipline)
- [ ] `./build.sh test` re-run after wider builds — no test-target regression
- [ ] **HMAC chain byte-equivalence test** for ModelHandle migration
      (v5.15.0): synthesize representative ModelHandle pre/post-migration;
      emit stamp body; verify SHA-256-locked byte-identical to v5.14.post1
      baseline OR document expected differences with explicit registry
      rationale
- [ ] **Legacy-stamp load test** (v5.15.0): load a v5.14-era stamp on
      v5.15-engine; verify loads cleanly (Surface G forward-compat
      preserved; no MODEL_FORMAT_VERSION bump)
- [ ] **trading_mode round-trip test** (v5.15.2): set
      `trading_mode=paper|live|shadow` in cfg; parse; verify
      stamp body carries the parsed value; verify boot gate REFUSE/WARN
      dispatches correctly
- [ ] **Pre-flight checklist trip test** (v5.15.2): with
      `trading_mode=live` and ONE pre-flight item failing, verify boot
      REFUSES + logs the specific failure with actionable message
- [ ] **breakeven_on_profit ratchet test** (v5.15.2): with the bit set,
      verify SL ratchets to breakeven when position crosses net profit;
      with bit unset, verify no ratchet
- [ ] **Single-zoo hot-swap unification test** (v5.15.4): hot-swap
      simulating validate failure; verify pre-swap snapshot reverts
      cleanly; in-flight predictions unaffected
- [ ] Hot path UNTOUCHED — verified via `tools/calls_graph_diff.sh` +
      `DOCS/HOT_PATH_CHANGELOG.md` audit (new PerCoreSnap fields in
      v5.15.1 are slow-path only)
- [ ] All 6 TECH_DEBT closures land in `DOCS/TECH_DEBT.md` with proper
      status updates
- [ ] CHANGELOG.md row written for sprint umbrella (v5.15)
- [ ] HOT_PATH_CHANGELOG entries for any slow-path additions
- [ ] Version.hpp bumped per sub-ship (5.14.post1 → 5.15.0 → 5.15.1 →
      ... → 5.15)
- [ ] Sub-ship postmortems written before sprint umbrella tag
- [ ] Workspace synced after sprint umbrella

---

## Cold-pickup completeness (10 fields per CLAUDE.local.md rule)

1. **Branch state.** Create `feat/v5.15-live-readiness` from engine tag
   `v5.14` (commit `c4e45d1`), NOT from `v5.14.post1`:
   ```bash
   cd /home/caramel/code/FoxML_Trader_v2
   git checkout -b feat/v5.15-live-readiness v5.14
   ```
   Workspace branch follows: `main` continues. Rollback anchors:
   `pre-v5.15` = `v5.14`; `pre-v5.15.0` = engine HEAD pre-ModelHandle-migration.

2. **Phase execution order MATCHES dependency order:**
   - v5.15.0 FIRST — ModelHandle migration is foundational; v5.15.1
     consumes the unified `has_flags` for drift surfacing; v5.15.3
     consumes the canonical pattern for multi-horizon stamping
   - v5.15.1 SECOND — Model Health panel reads v5.15.0's drift bits
   - v5.15.2 — independent of .1; can ship parallel after .0 closes
   - v5.15.3 — independent; can ship parallel after .0 closes. Closes
     CLAUDE.local.md "Known landmine" 2026-05-07 (XGBoost+libgomp+pthread)
     via process-startup setenv fix; also lands per-horizon stamp emit
     for both serial + parallel multi-horizon workers.
   - v5.15.4 — consumes v5.15.2's trading_mode field

3. **First concrete move per sub-ship:** see each subplan's "Step 0"
   section.

4. **Function / constructor / macro names** (verified against current
   code 2026-05-12):
   - `ModelHandle` struct at `ML_Headers/ModelInference.hpp:239`
     (16 uint8_t has_* fields currently)
   - `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG` at
     `ML_Headers/StampBoundModelConstRegistry.hpp:267`
   - `FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG` at `:377`
   - `STAMP_MODEL_CONST_AUTOPOPULATE` at `:601`
   - `STAMP_MODEL_CONST_AUTOPOPULATE_ONE` at `:680`
   - `STAMP_HAS / SET / CLR` macros at `MemHeaders/BitmapMacros.hpp:78-90`
   - `FOREACH_FAILURE_MODE` at `MemHeaders/FailureModeRegistry.hpp:122`
     (uint16_t storage; static_assert at :212)
   - `FOREACH_LIFECYCLE_CFG_FLAG` at
     `CoreFrameworks/LifecycleCfgFlagRegistry.hpp:55`
     (`MASK_LIFECYCLE_CFG_BREAKEVEN_ON_PROFIT` at :58, dormant per
     TECH_DEBT-024)
   - `breakeven_on_partial` wire-up site at
     `CoreFrameworks/PortfolioController.hpp:670` (sister; canonical
     reference for breakeven_on_profit wire-up)
   - `reconcile_mode` parser at
     `CoreFrameworks/ControllerConfig.hpp:2371-2381` (canonical
     reference for trading_mode string-keyed enum parse)
   - `EngineSharded_Run` in `CoreFrameworks/EngineSharded.hpp`
     (boot path; insert point for LiveReadiness_Verify gate)
   - Single-zoo hot-swap site in `CoreFrameworks/EngineSharded.hpp`
     (`v5.10.0c "log-and-leave"` semantics; TECH_DEBT-005 target)
   - `train_model_worker_fn` (single-horizon canonical post-v5.14.post1)
     at `Backtest/BacktestPanels.hpp:3206-3266`
   - `train_multi_horizon_worker_fn` (target for v5.15.3 stamping) at
     `Backtest/BacktestPanels.hpp:3792`
   - `mh_per_horizon_parallel_worker` (parallel variant; default-off per
     CLAUDE.local.md XGBoost+libgomp landmine 2026-05-07) at
     `Backtest/BacktestPanels.hpp:3763`
   - `MLStatusPanel.hpp` at `GUI/MLStatusPanel.hpp` (~504 LOC; existing
     CollapsingHeaders at :320 "Ensemble (multi-horizon)" + :420
     "Thompson Bayesian dashboard"; Model Health inserts between)
   - `PerCoreSnap` struct at `DataStream/EngineTUI.hpp:981`

5. **File:line refs for cited tests / baselines:**
   - 2904/2904 tests pass at `v5.14.post1` (postmortem confirmation;
     handoff baseline). v5.15.0 target ~+20 new tests; sprint umbrella
     target ~+50.
   - tests/controller_test.cpp ModelHandle test sites: enumerate via
     `grep -n "h\.has_\|ModelHandle " tests/controller_test.cpp` at
     v5.15.0 Step 0 (migration list)
   - Canonical migration reference for v5.15.0:
     `Backtest/BacktestEngine.hpp:1147-1220`
     (`Backtest_RunFullValidation` already-migrated sibling)
   - v5.14.post1 sibling fix at `Backtest/BacktestPanels.hpp:3206-3266`
     (`train_model_worker_fn` post-migration; canonical reference for
     multi-horizon stamping pattern)
   - breakeven_on_profit test currently at
     `tests/controller_test.cpp:21803` ("default breakeven_on_profit bit
     OFF (DORMANT — TECH_DEBT-024)"). v5.15.2 amends + adds wired-up
     tests.

6. **Stale-claim audit (completed 2026-05-12 pre-draft):**
   - ✅ ModelHandle has 16 uint8_t has_* fields (handoff said ~17;
     actual 16)
   - ✅ FOREACH_FAILURE_MODE uint16_t storage with static_assert
     (`MemHeaders/FailureModeRegistry.hpp:212`); 2 entries pre-v5.15;
     +7 = 9 of 16; safe
   - ✅ MLStatusPanel is its own file `GUI/MLStatusPanel.hpp` (handoff
     said "DashboardPanels.hpp or similar")
   - ✅ `train_multi_horizon_worker_fn` at `BacktestPanels.hpp:3792`
   - ✅ All cited cfg fields exist: `require_mlockall` (493),
     `model_max_age_hours` (554), `calibration_log_path` (655),
     `held_out_stamp_secret` (768), `reconcile_mode` (865),
     `model_verify_strict` (1538)
   - ⚠️ **`cfg.mode` does NOT exist** — handoff assumed it does;
     v5.15.2 INTRODUCES `trading_mode` cfg field as part of structural
     design (not derived predicate hack)
   - ✅ TECH_DEBT-033 NOT yet in ledger (handoff correct); v5.15.2 Step
     0 writes the entry before sub-ship work
   - ✅ TECH_DEBT-003 surface (`verify_model_stamp` parser ~700 LOC)
     confirmed at `ML_Headers/ModelInference.hpp` (entry at
     TECH_DEBT.md:120-132)
   - ✅ TECH_DEBT-024 surface (`breakeven_on_profit` dormant at
     LifecycleCfgFlagRegistry.hpp:58; sister at PortfolioController.hpp:670)
   - ✅ Tests count: 2904 per handoff (postmortem confirmation; not
     re-run this session). `tests_passed` counter in
     `tests/controller_test.cpp:63`.

7. **Effort claims reconcile:**
   - v5.15.0 ModelHandle migration: ~400 LOC + ~150 LOC parser refactor
     = ~550 LOC. `ML_Headers/ModelInference.hpp` is ~2500+ lines;
     migration reaches ~14-20 caller files.
   - v5.15.1 Model Health panel: ~200 LOC GUI + ~50 LOC PerCoreSnap
     bitmap = ~250 LOC. MLStatusPanel.hpp 504 lines → ~700 post.
   - v5.15.2: ~150 LOC boot gate + ~80 LOC trading_mode cfg + ~50 LOC
     breakeven wire-up + ~20 LOC /readiness check = ~280 LOC.
   - v5.15.3 multi-horizon stamping: ~50 LOC. Mechanical pattern apply.
   - v5.15.4: ~50 LOC strict defaults + ~130 LOC hot-swap snapshot
     infrastructure (covers both single-zoo + ensemble surfaces) = ~180 LOC.

8. **Source-audit references with paths:**
   - Predecessor sprint:
     `plans/v5.14-foxml-port-and-maker/MASTER.md` (sealed)
   - Last sub-sprint postmortem:
     `plans/v5.14-foxml-port-and-maker/postmortems/2026-05-11-v5.14.11-session-postmortem.md`
   - Post-release-fixes log:
     `plans/v5.14-foxml-port-and-maker/postmortems/2026-05-11-v5.14-post-release-fixes.md`
   - Boot log analysis context: chat-time review 2026-05-11; 5 issue
     classes documented
   - Kickoff handoff (this prompt's source):
     `plans/v5.15-live-readiness/handoffs/2026-05-12-v5.15-kickoff-handoff.md`

9. **Predecessor / dependent plans named with paths:**
   - Predecessor: `plans/v5.14-foxml-port-and-maker/MASTER.md` (sealed
     `v5.14` umbrella + `v5.14.post1` patch)
   - Sister: `TESTING_NOTES/v5.12-v5.14-mini.md` (operator paper-test
     guide; v5.15 ships consume this)
   - Dependent (post-v5.15): operator paper-test session

10. **Tag names locked + rollback anchors:**
    - Sprint umbrella: `v5.15` (annotated; created after all sub-ships ship)
    - Sub-ship tags: `v5.15.0`, `v5.15.1`, `v5.15.2`, `v5.15.3`, `v5.15.4`
    - Pre-tag rollback: `pre-v5.15` = `v5.14`;
      `pre-v5.15.0` = engine HEAD pre-migration;
      `pre-v5.15.1` etc. created after each preceding sub-ship lands
    - Post-sprint patches if needed: `v5.15.post1`, `v5.15.post2`, etc.
      (per `.postN` scheme established v5.14.post1)

---

## Data-Oriented Design analysis (per-sub-ship pattern application)

Caramel's framing 2026-05-12: *"make sure were analuzing for proper
struct alignment as well, and other stuff similar to that like the
bitmaps please, those are always welcome."* — DOD discipline is
always-on. Every sub-ship that touches a struct, snapshot field, or
state cluster gets an explicit DOD pass against the catalog. Items
flagged below are MUST-APPLY at the indicated sub-ship; the relevant
DESIGN_SPECS doc + CLAUDE.md item are cited inline.

### v5.15.0 — ModelHandle migration

| DOD concern | Decision | Reference |
|---|---|---|
| **Struct alignment** | `alignas(64)` on ModelHandle (read in slow-path inference dispatch; sized for cache-line); explicit static_assert(sizeof(ModelHandle) % 64 == 0) | `per-snapshot-cluster-layout-pattern.md`; CLAUDE.md item 12 |
| **Bit-packing has_*** | 16 uint8_t has_* fields → 1 uint64_t `has_flags`; saves 15 bytes per handle; branchless `STAMP_HAS(h, name)` check via mask AND | `bitmap-flag-api.md`; CLAUDE.md item 20 |
| **Bit-position stability** | bit positions assigned by FOREACH expansion order; MUST be stable across builds OR use named MASK_STAMP_HAS_* constants (preferred — already established for ModelStampResult) | `x-macro-registry-with-presence-dispatch.md` |
| **Cluster layout (hot-vs-cold)** | hot cluster (booster ptr, has_flags, expected_num_features, expected_num_classes) FIRST 64B; cold cluster (training_run_name char[64], training_timestamp_us, scaler bind data char[65]) SECOND 64B+ | `per-snapshot-cluster-layout-pattern.md` |
| **Padding determinism** | explicit `int<N>_t _padding<N> = 0;` fields between sub-clusters if the migrated layout exposes a gap; struct used in byte-equivalence test contexts (HMAC round-trip) | CLAUDE.md item 27; `struct-padding-determinism-pattern.md` |
| **False sharing risk** | ModelHandle is read by inference (slow-path); never cross-thread-mutated post-load. No false sharing risk. | — |
| **AVX-512 byte determinism** | N/A (no SIMD math on ModelHandle directly) | — |

### v5.15.1 — Model Health panel + PerCoreSnap bitmap

| DOD concern | Decision | Reference |
|---|---|---|
| **PerCoreSnap alignas(64)** | already established via v5.14.10.0 cluster layout. New drift bits MUST land in existing failure_flags uint16_t cluster (no new top-level fields if avoidable). | `per-snapshot-cluster-layout-pattern.md` |
| **Failure-mode bitmap headroom** | uint16_t failure_flags currently 2 entries; +7 = 9 of 16 used. Safe margin remains. **Verify static_assert at FailureModeRegistry.hpp:212 still passes.** | `bitmap-flag-api.md`; CLAUDE.md item 20 |
| **PerCoreSnap 4-bool bitmap (TECH_DEBT-028)** | 4 uint8_t booleans (`ml_scaler_present`, `drift_breached`, `drift_kill_tripped`, `core_kill_tripped`) → uint8_t `per_core_state_flags` bitmap with 4 MASK_PER_CORE_* constants. Saves 3 bytes per PerCoreSnap. | `bitmap-flag-api.md`; CLAUDE.md item 20 |
| **New value-fields (hashes, timestamps)** | `label_hash_at_load`, `feature_hash_at_load`, `build_flags_hash_at_load` (uint64 each), `model_age_seconds_at_load` (uint64) — cluster together; insert in cold-cluster region per CLAUDE.md item 12 display↔execution invariant (GUI reads cold, no hot-path consumer). | `per-snapshot-cluster-layout-pattern.md` |
| **Cross-thread sharing** | slow-path writes hashes at model-load; GUI thread reads. Standard PerCoreSnap publication via double-buffered TUISnapshot (already established). No new sync infrastructure needed. | CLAUDE.md item 8 (TUI decoupling) |
| **Padding determinism** | PerCoreSnap not in byte-equivalence test path today; verify if v5.15.1 introduces any (e.g., snapshot SHA-256 lock test). If yes: explicit padding fields. | CLAUDE.md item 27 |

### v5.15.2 — Live-readiness boot gate + trading_mode + breakeven wire-up

| DOD concern | Decision | Reference |
|---|---|---|
| **trading_mode field placement** | new uint8_t `trading_mode` in ControllerConfig — pack with sister uint8_t cfg fields (`reconcile_mode` at line 865 is the natural sibling cluster); avoid creating a new isolated field that wastes 7 bytes of padding | `per-snapshot-cluster-layout-pattern.md` (cfg analog: HOT-CLUSTER alignas(8) at start of 5 domain bitmaps per v5.14.9.F); item 13 reuse-audit |
| **Cohort audit for trading_mode** | per CLAUDE.local.md going-forward rule 2026-05-11 (cohort-audit when new cfg field has siblings): siblings = `reconcile_mode` (uint8_t enum), `model_verify_strict` (int tri-state). `trading_mode` is uint8_t enum; same family. **Cohort verdict:** all 3 are enum-valued, not boolean, not BIT_FLAG-eligible. Direct uint8_t storage is correct; cohort already homogeneous. No migration needed. | `cfg-flag-eligibility-criteria.md` (5-criteria + cohort section); CLAUDE.local.md 2026-05-11 |
| **trading_mode dispatch (slow-path predicate cache)** | derived `gate_state.is_live = (trading_mode == TRADING_MODE_LIVE)` once at slow-path entry; cached predicate per CLAUDE.md item 18(c) | `slow-path-gate-registry-pattern.md` |
| **Boot gate REFUSE list** | one-time cost path (boot only); no alignment concern. Static array of `LiveReadinessCheck { const char* name; bool (*fn)(const ControllerConfig<F>&, const EngineShardedState<F>&); }` — table-driven dispatch; new check = 1-row addition | `curve-registry-pattern.md` (enum-driven dispatch precedent) |
| **breakeven_on_profit read site** | mirrors `BITMAP_IS_SET(ctrl->config.lifecycle_cfg_flags, MASK_LIFECYCLE_CFG_BREAKEVEN_ON_PARTIAL)` at PortfolioController.hpp:670; same bitmap; no new field | `bitmap-flag-api.md`; CLAUDE.md item 20 |
| **Padding determinism** | trading_mode stamp-bound via FOREACH_STAMP_BOUND_CFG; stamp body emit MUST stay byte-equivalent for legacy stamps (Surface G `has_trading_mode` flag preserves forward-compat). | CLAUDE.md item 27 + item 15 |

### v5.15.3 — Multi-horizon worker stamping

| DOD concern | Decision | Reference |
|---|---|---|
| **No new struct fields** | mechanical pattern apply only; stamp body assembly uses existing STAMP_MODEL_CONST_AUTOPOPULATE companion | — |
| **HMAC chain byte preservation** | per-horizon stamp emit walks the same FOREACH_STAMP_BOUND_MODEL_CONST registry; each stamp's body is byte-identical to single-horizon emit modulo per-horizon fields (grid_member_count, horizon_idx, horizon_count) | `wire-format-byte-preservation-discipline.md` |
| **No alignment regression** | no struct changes | — |

### v5.15.4 — Live mode strict defaults + hot-swap unification

**AMENDED 2026-05-12 post-PARITY-023:** original capture-pointer + Revert
design was structurally broken (Free destroys data in-place; captured
pointers point at freed memory). Plan amended to use SHADOW-LOAD pattern
(`shadow-load-state-transition-pattern.md`): allocate new state into
SEPARATE memory + load + validate + atomic_exchange + Free-old. No
HotSwapSnapshot struct needed; no revert path needed; failure just Free's
the new (failed) allocation.

| DOD concern | Decision | Reference |
|---|---|---|
| **Hot-swap shadow-load** | `aligned_alloc(64, sizeof(EnsembleModelZoo<F>))` for new state allocation; `__atomic_exchange_n(slot, new, __ATOMIC_ACQ_REL)` for swap; Free OLD state after swap succeeds; on failure Free NEW state with pre-swap untouched. NO HotSwapSnapshot struct; no revert path. Same pattern for single-zoo (`CoreModelZoo<F>*`) + ensemble (`EnsembleModelZoo<F>*`) cases. | `shadow-load-state-transition-pattern.md` (canonical pattern); v5.15.4 subplan |
| **alignas(64) retrofit on EnsembleModelZoo + CoreModelZoo** | required for `aligned_alloc(64)` allocation to round-trip cleanly + cache-line discipline on cross-thread access. `static_assert(sizeof(T) % 64 == 0)` verifies size alignment. | `per-snapshot-cluster-layout-pattern.md` |
| **trading_mode default-flip without struct change** | post-parse normalize pass mutates existing cfg fields (model_verify_strict, reconcile_mode); no new fields. No alignment concern. | — |
| **Stamp body byte-equivalence** | default-flip MUST NOT change stamp body emit at canonical byte level — verified via `/parity-check` (cfg-default-flip is a parse-time normalize; stamp emit reads normalized value; legacy cfgs with explicit overrides still produce same stamp body bytes) | `wire-format-byte-preservation-discipline.md`; CLAUDE.md item 15 |
| **Cross-thread atomic swap** | `__atomic_exchange_n` on aligned pointer = single x86_64 instruction; lock-free; readers see old OR new, never torn. Single-owner write (boot gate / operator-triggered slow-path) means no RCU grace period needed before Free-old. | CLAUDE.md item 5 (lock-free reader-side discipline) |

### Cross-sprint DOD invariants (every sub-ship)

- No new false-sharing risk introduced (cross-thread writes always on
  separate cache lines from hot-path reads)
- All new struct fields with byte-equivalence consumers (HMAC,
  memcmp, SHA-256-lock tests) get explicit `_padding<N> = 0` fields
  per CLAUDE.md item 27 if a gap exists
- All new boolean storage uses BITMAP_* API (CLAUDE.md item 20); no new
  byte-per-flag patterns
- All new enum cfg fields go through the cohort-audit per
  CLAUDE.local.md going-forward rule 2026-05-11
- `/dod-audit` skill runs at each sub-ship close to verify the catalog
  was applied; HIGH-RISK ships also at pre-coding gate

---

## DESIGN_SPECS / CLAUDE.md cross-references

Catalog: `tick-trader-percore-workspace/DESIGN_SPECS/README.md`
(27 patterns post-v5.14.11.B).

| Sub-ship | DESIGN_SPECS that MUST be read | CLAUDE.md items |
|---|---|---|
| v5.15.0 | x-macro-registry-with-presence-dispatch, autopopulate-pattern-for-production-caller-class, pre-post-cfg-registry-split-for-emit-order-preservation, bitmap-flag-api, wire-format-byte-preservation-discipline, struct-padding-determinism-pattern, audit-driven-pre-coding-gate, structural-fix-preferred-decision-framework | 13, 15, 19, 20, 21, 22, 27 |
| v5.15.1 | bitmap-flag-api, per-snapshot-cluster-layout-pattern, transient-aggregation-bitmap-pattern | 1, 12, 20 |
| v5.15.2 | slow-path-gate-registry-pattern, curve-registry-pattern (for trading_mode enum dispatch), cfg-flag-eligibility-criteria (cohort audit per going-forward rule 2026-05-11) | 13, 18 |
| v5.15.3 | wire-format-byte-preservation-discipline, autopopulate-pattern-for-production-caller-class, avx512-byte-determinism-pattern (cross-mode byte-identity test extends item 25 discipline) | 15, 16 (reuse-audit; helper extraction), 21, 22, 25 |
| v5.15.4 | shadow-load-state-transition-pattern (PRIMARY — canonical pattern for HotSwap unification), cfg-flag-eligibility-criteria, structural-fix-preferred-decision-framework, per-snapshot-cluster-layout-pattern (alignas(64) retrofit on zoo containers), wire-format-byte-preservation-discipline (default-flip MUST NOT change stamp body bytes) | 5, 13, 15, 19, 27 |

---

## What's intentionally NOT in scope for v5.15

Per "no rotting tech debt" rule, this list captures explicit deferrals:

- **Operational safety audit** (drawdown circuit breaker, daily PnL cap,
  position size limits, kill switch) — sequenced AFTER v5.15 closes;
  paper-test informs design
- **Order book data source / Maker MVP** (TECH_DEBT-008) — deferred
  indefinitely per existing entry; no consistent order book data source
- **Paper-test execution** — sequenced AFTER v5.15 ships
- **TECH_DEBT-011 FOREACH_PER_CORE_SNAP_FIELD full registry** —
  10-15h architectural ship; would scope-creep v5.15.1 by ~5x. The
  failure-mode subset (7 new entries in v5.15.1) doesn't trigger the
  broader visible-state registry; defer until 5+ general PerCoreSnap
  fields land in one umbrella.
- **TECH_DEBT-009 FOREACH_CFG_FIELD non-bool subset** — trigger
  requires 3+ new non-bool cfg fields in one umbrella; v5.15 adds 1
  (trading_mode). Defer.
- **TECH_DEBT-018 /precoding-audit Layer 1 orchestrator skill** —
  workflow improvement; manual 4-subagent dispatch field-tested in
  v5.15.0. Codification = separate ship.
- **TECH_DEBT-022 cfg parser perfect-hash dispatch** — boot-only
  optimization; not live-readiness scope.
- **TECH_DEBT-026 per-core bandit_algorithm override** — different
  feature; not gated by live-readiness.
- **TECH_DEBT-029 Source file length reduction** — separate cleanup
  sprint per its entry.
- **TECH_DEBT-031 MetricsLog FOREACH registry** — different surface; no
  v5.15 touch.
- **TECH_DEBT-032 CLAUDE.md context-management cleanup** — separate
  sprint per its entry.

---

## References

**Engine codebase entry points:**
- `CLAUDE.md` (always loaded; items 1-27)
- `CLAUDE.local.md` (private project memory; going-forward rules)
- `DOCS/CLAUDE_ML_INVARIANTS.md` — read for v5.15.0 (FeatureRegistry /
  MLBuildContext / train-serve path) + v5.15.3 (multi-horizon worker
  stamping)
- `DOCS/CLAUDE_INVARIANTS.md` — read for v5.15.2 (boot path / cfg parser)
  + v5.15.4 (cfg defaults)
- `DOCS/CLAUDE_INTEGRATION.md` — read for v5.15.1 (new GUI panel / new
  PerCoreSnap fields / FOREACH_FAILURE_MODE extension) + v5.15.2 (new
  cfg field trading_mode)
- `DOCS/CLAUDE_REVIEW.md` — referenced for the 10-item cold-pickup
  checklist (this MASTER follows it)
- `DOCS/STRATEGY_AND_CODING_RULES.md` (private; 11 strict invariants)
- `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` (private; 13 parts; relevant for
  v5.15.2 if boot gate touches slow-path)

**Workspace deliverables:**
- `tick-trader-percore-workspace/DESIGN_SPECS/README.md` (27 patterns)
- `tick-trader-percore-workspace/DOCS/TECH_DEBT.md` (30 entries; 6 to
  close)
- `tick-trader-percore-workspace/DOCS/HOT_PATH_CHANGELOG.md` (sprint-end
  if hot-path additions)
- `tick-trader-percore-workspace/DOCS/CHANGELOG.md` (sprint-end row)
- `tick-trader-percore-workspace/TESTING_NOTES/v5.12-v5.14-mini.md`
  (operator paper-test guide; reference for paper-test cadence post-v5.15)
