# ML Pipeline Invariants

**Read this file before changing FeatureRegistry, FeatureComputeCtx,
Regime_ComputeSignals, MLBuildContext, CoreModelZoo, stamp_write_for_model,
verify_model_stamp, or anything in the train→deploy→serve path.** Each
invariant has a "why" — knowing it prevents reintroducing the bug it caught.

Companion to `DOCS/CLAUDE_INVARIANTS.md` (engine-wide), scoped to ML.

## Train-serve feature parity (load-bearing — v5.8.1b + v5.9.x)

**Rule:** `Features_PackAll(&ctx, buf)` MUST produce bytewise-identical
floats on both the live engine path AND the backtest training path for
the same input state. Validated by:

1. EXTENSIBILITY equivalence test in `controller_test.cpp` —
   synthetic RegimeSignals input, asserts indices 0-33 match between
   `Features_PackAll` and the legacy `ModelFeatures_Pack` (frozen
   reference, retired in v5.9).
2. Phase 3 parity regression test (v5.9.2 EXTENSIBILITY block in
   `controller_test.cpp`) — generates a deterministic 5000-tick
   synthetic stream (cosine + linear drift, stepped volume,
   alternating buyer-maker), runs `Backtest_Run` with
   `collect_features=1` twice, diffs `feature_matrix` bytewise. Both
   runs MUST produce identical feature output across every sample
   row × feature column. Plus a regression-simulation: a 3rd run with
   one tick perturbed mid-stream MUST produce a non-zero diff (proves
   the assertion is non-tautological).

**Why:** v5.8 paper testing surfaced multiple "wired but unobserved"
failures where the live engine fell back to defaults silently. The
parity guarantee is structural, not validated-by-inspection.

**How to apply:** Adding a feature compute fn → must be drift-test
covered. Adding a state pointer to MLBuildContext → must be
populated in BOTH ControllerEventLoop.hpp:1818-1840 AND
ShardedBacktestDriver init.

## FEATURE_REGISTRY_HASH is part of the model fingerprint (v5.8.1b)

**Rule:** Any change to `FOREACH_FEATURE(X)` rows or `_VERSION` fields
flips `FEATURE_REGISTRY_HASH()`. Existing models with a stamp's
`feature_registry_hash` field that doesn't match get refused at load
when `held_out_gate_strict=1` (v5.8.6).

**Why:** Train-serve drift via feature-set divergence is the #1 silent-
bug source in ML systems. Hash-binding the registry + verifying at load
makes drift impossible to ship without operator awareness.

**How to apply:** Touching the registry → expect retrain. Update the
pinned hash snapshot in `controller_test.cpp` (currently
`0xfc9119b8ed47bcf9` post-v5.8.1b). Failing snapshot test forces a
deliberate "yes, I'm changing the contract" acknowledgment.

## MLBuildContext fully populated in live sharded path (v5.8.1b)

**Rule:** Every state pointer field on `MLBuildContext` must be
populated in `ControllerEventLoop.hpp:1818-1840` before
`Strategy_BuildParameters` dispatches to `ML_BuildParameters`. Adding
a new field requires a corresponding populator entry there +
ShardedBacktestDriver counterpart.

**Why:** ML_BuildParameters threads MLBuildContext fields into
`Regime_ComputeSignals`, which writes `RegimeSignals` that the feature
compute reads. Missing population on either side → different signals →
different features → silent train-serve drift.

**How to apply:** Adding a new state-bearing feature → populator entry
in BOTH ControllerEventLoop AND BacktestSharded. The Phase 3 parity
regression catches divergence at test-time.

## MODEL_FORMAT_VERSION bumps on wire-format change only (v5.8.1a, v5.9.3)

**Rule:** `MODEL_FORMAT_VERSION` is the *stamp body wire format*
version, not the engine SemVer. Bump it only when stamp body fields
are added/removed/renamed. Don't bump on every patch ship — that
would force needless retrains.

**Why:** v5.8.1a bumped 4→5 to add `feature_registry_hash`. v5.9.3
will bump 5→6 to add `feature_scaler_present` + `scaler_sha256`.
Between those, every ship inherits the same wire format. Distinguishes
"engine got patched" from "models need retrain."

**How to apply:** Stamp body change → bump version + add WARN-load
fallback for legacy stamps until grace period ends. Document the
bump in `DOCS/changelogs/`.

## Models load once at boot — hot-swap unsupported (v5.2.0)

**Rule:** `CoreModelZoo_TryLoadRole` runs once during
`EngineSharded_Init`. After that, the `ModelHandle` is read-only.
No code path may modify the handle in flight.

**Why:** ModelHandle is shared by all per-node threads via
seqlock-protected MLBuildContext. Modifying it during live trading
would race with hot-path reads.

**How to apply:** "Reload model" workflow = stop engine, edit
`core_N_model_dir=`, restart engine. Document the procedure
(see `DOCS/ML_TEST_RECIPES.md` rollback recipe, post-v5.9.4).
Future hot-swap (v5.10+) requires seqlock-protected ModelHandle.

## ML→SimpleDip fall-through emits CRITICAL health log (post-v5.9.0)

**Rule:** When an ML core fails to load its model (or model returns
NaN, or registry-hash mismatch in strict mode), the dispatcher
falls through to `SimpleDip_BuildParameters`. This fall-through MUST
emit a CRITICAL-level health log on each rebuild cycle (rate-limited
per-node to once per minute).

**Why:** Pre-v5.9.0 the fall-through was silent — operator paper-soaks
for hours not knowing ML never fired. Closes silent-degradation bug
class.

**How to apply:** New fall-through path → use
`HealthLog_Critical_RateLimited(...)` with `last_log_time_us` per-node
gate. Test in EXTENSIBILITY block.

## Feature compute returns FPN_Zero on missing state (v5.8.1b)

**Rule:** Every `ML_Compute_<Name>(ctx)` function returns
`FPN_Zero<F>()` on null `ctx` or null required input field. Never
NaN/Inf. Never undefined.

**Why:** Cold-start / warmup paths feed null `signals` or `short_rolling`.
Returning zeros lets the dispatcher safely produce a feature vector
that the ML model can score (will produce a low-confidence prediction);
returning NaN/Inf would propagate to model output.

**How to apply:** Adding a feature → use the canonical pattern
`return (ctx && ctx->signals) ? ctx->signals->X : FPN_Zero<F>();`.
For double-typed fields use `FPN_FromDouble<F>(ctx->signals->X)`.

## Features_PackAll validates output (post-v5.9.0)

**Rule:** `Features_PackAll(&ctx, buf)` returns -1 sentinel if any
feature value is NaN/Inf. Callers branch on `if (n < 0)` and
zero-the-buffer + skip prediction. Single source of truth for
validation; no per-caller duplication.

**Why:** Even with the Zero-on-missing-state invariant above, edge
cases (degenerate division, FPN_FromDouble overflow) can produce
NaN. Validating at the output is the last-line defense before
the model sees garbage.

**How to apply:** Adding a feature compute fn → no extra work
(packer-side validation covers it). Adding a new caller → branch
on `if (n < 0)` + log + skip-prediction.

## Stamp body locale-pinned for canonical signing (v5.3.0)

**Rule:** `stamp_write_for_model` MUST pin `LC_NUMERIC=C` (via
`uselocale(newlocale(LC_NUMERIC_MASK, "C", 0))`) before formatting
floats into the canonical body. `tools/stamp_model.sh` MUST set
`export LC_NUMERIC=C` at the top.

**Why:** awk/printf under `LC_NUMERIC=de_DE` produces "0,55" instead
of "0.55"; HMAC-SHA256 over the canonical body would differ silently
between train/verify if either side runs in a different locale.

**How to apply:** Adding a float field to the stamp body → use
%.6f or %g in BOTH the in-process body builder (ModelInference.hpp)
AND the bash script (stamp_model.sh). Bash + in-process bytewise
parity is regression-tested in `controller_test.cpp` (v5.8.8).

## Stamp body atomic write (v5.3.0)

**Rule:** `stamp_write_for_model` writes to `<model>.stamp.tmp`,
fsyncs, then renames to `<model>.stamp`. POSIX `rename(2)` is atomic
within a filesystem.

**Why:** Without atomic write, a process killed mid-write leaves a
half-stamp on disk that the verifier might accept (if HMAC happens
to match the truncated body). Operationally rare but worth $0 to
prevent.

**How to apply:** Future stamp-write paths → reuse the existing
tmp+rename pattern. New file-write workflows in the ML pipeline
(scaler sidecar in v5.9.3) → same pattern.

## Cfg fields distinguish explicit-set vs defaulted (post-v5.9.0)

**Rule:** Critical cfg fields (per-node strategy assignments,
held_out_stamp_secret, auto_stamp_on_held_out, model paths) MUST
track an explicit-set bitmap during `ControllerConfig_Parse`. The
TUI distinguishes "deliberate operator choice" from "defaulted
because cfg field missing" via a tri-state indicator.

**Why:** v5.8 paper testing: `backtest.cfg` lacked `core_N_strategy=`
lines → `ControllerConfig_Default` set all 16 cores to SIMPLE_DIP →
operator saw "0!" hardcoded warning, couldn't tell it was actually a
default. Closes the today-bug class.

**How to apply:** Adding a critical cfg field with a default → set
the explicit-set bit on parse. Surface in TUISnapshot. New "ML Status"
panel reads bits to render tri-state.

## Production deploy ritual is documented (post-v5.9.4)

**Rule:** Transitioning from paper to live (`use_real_money=1`) MUST
follow the checklist in `DOCS/ML_TEST_RECIPES.md` (the production
deploy recipe). Skip a step → silent failure mode in live.

Mandatory items (full list in the recipe doc):
1. All loaded models stamped + Verify Stamp green
2. `held_out_gate_strict=1` set
3. `held_out_stamp_secret` non-empty + matches training secret
4. Engine boot log shows `[model] X.bin: ... — ok` for every model
5. Engine header panel registry hash matches stamps
6. Paper-tested ≥24h on the SAME cfg shape

**Why:** Multi-step rituals are tribal knowledge until documented.
First production deploy without this checklist = high risk of
skipping a verification step.

**How to apply:** Any new "operationally critical" cfg field or
runtime check → recipe must document the verification step.

## Feature standardizer indexed by FeatureId (post-v5.9.3)

**Rule:** `FeatureStandardizer<F>` holds per-feature mean + stddev
arrays sized `NUM_REGISTERED_FEATURES`. Indexed by the
`FOREACH_FEATURE(X)` enum constants (`FEATURE_<NAME>`). NEVER
parallel hand-maintained arrays.

**Why:** The X-macro registry is the single source of truth for
feature ordering + count. Parallel arrays drift — was the bug
class v5.8 closed.

**How to apply:** Adding a feature → registry update propagates
to standardizer automatically (size + index). Static-asserts at
the standardizer struct enforce parity at compile time.

## Sidecar files travel with model (post-v5.9.3, post-v5.8.9)

**Rule:** `Save Run` copies all sidecar files alongside the model
into the run directory:
- `<model>.stamp` (signature/metadata)
- `<model>.scaler` (post-v5.9.3 — feature standardizer)

If a future v5.10+ adds another sidecar, `Save Run` MUST be updated.

**Why:** Pre-v5.8.9, Save Run copied only the model file → deployed
bundle was missing the stamp → live engine couldn't validate. Sidecar
companions belong together.

**How to apply:** New sidecar type → update `Save Run` copy logic
in `Backtest/BacktestPanels.hpp`. Test that bundle is complete on
re-load.

## held_out_gate_strict defaults to 0 — flip for production

**Rule:** `held_out_gate_strict=0` (warn-only) is the dev/paper
default. Production live trading with real money MUST flip to
`held_out_gate_strict=1` (refuse load on stamp failure).

**Why:** Default-warn is friction-friendly during development (legacy
unstamped models still load). Default-strict in production is
non-negotiable — drift catches must fire.

**How to apply:** `engine.cfg.example` documents this in the
"PRODUCTION DEPLOY CHECKLIST" comment block. Production deploy
recipe (above) includes a step to verify the flip.

---

## Recurring ML bug pattern this prevents

**Class 12 — Wired-but-unexercised ML paths.** From v5.8 paper
testing: features compile, registries declare, callers wire — but
no operator workflow actually exercises the code path. Symptom:
"the function exists, the test passes, but in real use the wiring
silently degrades or fall-through fires unobserved."

Every invariant above counters one or more cases of this:
- `MLBuildContext fully populated` — counters MLBuildContext
  populator drift (v5.4.x lesson)
- `Features_PackAll validates output` — counters silent NaN
  passthrough
- `ML→SimpleDip fall-through CRITICAL log` — counters silent
  degradation
- `Cfg explicit-set tracking` — counters silent default fallback
- `Production deploy ritual documented` — counters tribal-knowledge
  procedure gaps
- `Train-serve feature parity (Phase 3 regression)` — structural
  prevention vs verification

**Prevention principle:** "Wired but not exercised" gaps must be
caught at PR-time (regression test) or plan-time (readiness
Checks 15-17), not paper-test-time.

## Sidecar registry-hash binding (v5.9.3+)

**Rule:** When `feature_scaler_present=1` in the stamp body, the
`<model>.scaler` sidecar binary MUST embed the
`FEATURE_REGISTRY_HASH` it was computed under. Engine load refuses
when the sidecar's hash differs from the current build's hash, EVEN
IF the parent stamp's hash matches.

**Why:** v5.9.3 introduces a NEW train→serve handoff (the scaler).
If the FOREACH_FEATURE registry is reordered/changed between training
the scaler and loading it at engine boot, the scaler's
mean[i]/stddev[i] arrays index to a different feature set than what
Features_PackAll produces — silent feature mis-scaling. Two-layer
binding (stamp's hash AND scaler's hash) makes drift impossible to
ship without explicit retrain.

**How to apply:** Phase 4 must add `feature_registry_hash` to the
`.scaler` binary header. `CoreModelZoo_TryLoadRole` must verify both
hashes match the build's `FEATURE_REGISTRY_HASH()` before applying
the scaler.

## Stddev floor identity (v5.9.3+)

**Rule:** `SCALER_STDDEV_FLOOR` (constexpr default `1e-9`) MUST be
embedded in the `.scaler` sidecar (Q32 fixed-point), not just
constexpr in code. Both `_Compute` (training) and `_Apply` (serving)
read the floor from the sidecar. Future changes to the constexpr
default DO NOT silently change behavior for existing models.

**Why:** drift class — change `SCALER_STDDEV_FLOOR` from `1e-9` to
`1e-8` in code, deploy without retrain. Training-side scaler still
has its 1e-9 stats; serve-side now floors at 1e-8 → for any feature
where stddev was in [1e-9, 1e-8] range, divisor differs → output
differs. Persisted floor pins the contract per-model.

**How to apply:** Sidecar layout includes `[u32 stddev_floor_q]`
field at fixed offset. Both Compute and Apply read this field, not
the constexpr.

## 3-tier strict-mode behavior (v5.9.0+ generalized in v5.9.3)

**Rule:** For ANY train-serve handoff (stamp registry hash, scaler
load, format_version, future ensemble weights, etc.):

- `held_out_gate_strict=1` → REFUSE load on mismatch, model
  unavailable, ML→SimpleDip CRITICAL log fires
- `held_out_gate_strict=0` → WARN load, identity/default applied,
  distinct PerCoreSnap state surface (e.g.
  `ml_model_load_failed=1`, `ml_scaler_load_failed=1`),
  rate-limited CRITICAL log
- **Silent fallback is forbidden.** Every refusal/warn path surfaces
  to the operator.

**Why:** v5.9.0b shipped this for model load failure; v5.9.3 extends
to scaler load failure; future handoffs follow same shape. Operator
must always see when serve-time uses identity/default in place of
the trained artifact.

**How to apply:** When adding a new artifact verifier, mirror the
pattern: PerCoreSnap field + populator + ML Status panel branch +
rate-limited CRITICAL log. Tests must cover refuse-path AND
warn-path observability.

## Trainer atomic write contract (v5.3.0 generalized in v5.9.3)

**Rule:** Sidecar persist MUST complete (with sha verification of
on-disk file) BEFORE stamp emit. If persist fails, training run
aborts with no stamp written. If stamp emit fails, sidecar is
removed. No half-baked artifact pairs (stamp claiming
`feature_scaler_present=1` while sidecar is missing).

**Why:** half-baked artifact pair = exact silent-drift class v5.9
prevents. Engine boot would either refuse (strict, OK) or warn-load
with identity (non-strict, BAD — operator thinks model is using
trained scaler but it's actually identity).

**How to apply:** training pipeline ordering enforced as:
1. compute scaler in-memory
2. persist sidecar atomically (`.tmp` + `rename`)
3. compute SHA-256 from on-disk file (verify it landed; don't trust
   in-memory copy)
4. write stamp atomically with `scaler_sha256=<hex>`
5. on-cancel cleanup: remove orphan `.scaler` if persist completed
   but stamp emit didn't

## Feature output snapshot is part of the parity surface (v5.9.2a+)

**Rule:** `FEATURE_REGISTRY_HASH` catches X-macro structural changes
(add/remove/reorder rows, version field bumps). The v5.9.2a
snapshot tests catch FUNCTION-BODY changes (ML_Compute_*,
Regime_ComputeSignals, RollingStats math). Both layers are required;
neither alone is sufficient.

When modifying ANY function in the feature dependency tree, author
either:
- Preserves output bit-for-bit (numeric-equivalent refactor) — no
  test update needed
- OR updates the snapshot test's recorded values AND bumps the
  relevant `FOREACH_FEATURE` row's `version` field (so existing
  models refuse to load with the new feature semantics)

**Why:** pre-v5.9.2a, body changes silently passed `FEATURE_REGISTRY_HASH`
verification — model loaded fine, predictions silently drifted.
Snapshot tests detect via "expected vs actual feature output bytes"
at PR-time, forcing the version bump + retrain decision before merge.

**How to apply:** snapshot tests live at `tests/controller_test.cpp`
v5.9.2a EXTENSIBILITY block. When you change a feature compute fn:
- Run tests; if they fail, your change is detectable (intentional
  semantic shift)
- Either revert to bytewise-identical math, or update the recorded
  values + bump version field
- Document in CHANGELOG: "v5.X.Y bumped FEATURE_<NAME> version
  from N to N+1, retrain required"

This same discipline applies to `Regime_ComputeSignals`,
`RollingStats_Push`, and any function the snapshot test exercises.

## Strategy is role-agnostic (v5.11.62+)

**Rule:** The ML strategy predict path reads from `ezoo->primary_handles`
(set by the loader at boot to whichever role file was actually present
on disk: priority `buy_signal > barrier > regime`). It MUST NOT
hardcode a specific role array. Per-handle `buy_class_idx` tells
`Model_Predict` which output index to return as the buy probability;
`Model_Predict` returns `out_result[buy_class_idx]` for any model
regardless of `num_outputs`.

**Why:** The training pipeline saves models under different role names
depending on label kind (binary → `buy_signal.json`, 3-class
PEAK_VALLEY_STABLE → `barrier.json`, regression → `buy_signal.json`).
Pre-v5.11.62, the strategy ONLY read `ezoo->buy_signal[]`, so 3-class
multi-horizon training output was loaded successfully into
`ezoo->barrier[]` but the strategy then ignored it — engine.log showed
"ensemble active (4 total models)" but ML Status panel showed "core 0:
warmup: 8% model: LOAD FAILED" with predictions disabled. Operator
hit this 2026-05-08 on multi_2year_01 deployment.

**How to apply when adding a new model role:**
1. Add `ModelHandle<F> <new_role>;` field to `CoreModelZoo` struct,
   `ModelHandle<F> <new_role>[ENSEMBLE_HORIZON_MAX];` to
   `EnsembleModelZoo`.
2. Add `CORE_MODEL_<NEW_ROLE>` bitmask constant.
3. Add `CoreModelZoo_TryLoadRole(...)` calls in `LoadFromDir` and
   `LoadFromCfg`.
4. Add a branch to the priority chain in the primary-role selector
   (currently buy_signal > barrier > regime — extend per priority
   intent).
5. Add a branch to `EnsembleModelZoo_EnsurePrimary` (the test/legacy
   backfill helper) so synthesized state still works.

That's it. Strategy code, bandit ops, snapshot population, Settings
panel — all already read `primary_*` and need zero changes.

**Anti-pattern:** Reading `ezoo->buy_signal_count` in strategy / bandit
/ snapshot / display code. ALWAYS use `primary_count`. The buy_signal_count
field still exists (used by per-role iteration in the zoo internals
itself — load loop, role iteration switch, sibling scaler check) but
must NOT cross the strategy boundary. /parity-check should flag any
new strategy code touching `buy_signal_count` as a regression.

**Backstop:** `EnsembleModelZoo_EnsurePrimary(ezoo)` auto-promotes
buy_signal to primary when callers (tests, ad-hoc paths) synthesize
ezoo state by setting `buy_signal_count` directly. Idempotent —
post-loader callers that already set primary_handles bypass it. New
bandit / state ops MUST call `EnsurePrimary` first if they use
primary_*; otherwise tests that synthesize state will read 0 arms.

**Files load-bearing for this invariant:**
- `ML_Headers/CoreModelZoo.hpp` — primary_handles field + selector +
  EnsurePrimary helper
- `ML_Headers/ModelInference.hpp` — `Model_Predict` reads buy_class_idx
- `Strategies/MLStrategy.hpp` — predict path uses primary_*
- `Strategies/StrategyParameters.hpp` — bandit dispatch uses primary_*
- `CoreFrameworks/ShardedSnapshot.hpp` — n_horizons = primary_count

## Train↔serve role-naming integration contract (v5.11.62+)

**Rule:** Every model role used by the engine must have a matching
trainer save site + matching live loader entry, AND any new role
addition must update BOTH sides in the same ship.

**The contract (informal until v5.X formalizes it):**

| Surface | Trainer side | Live side |
|---|---|---|
| Role file name | `Training_ResolveRole` (`Backtest/LabelFunctions.hpp`, E.1.2.C) — side=1 ⇒ `exit`; else label kind picks among the buy roles (`barrier`/`regime`/`buy_signal`); exhaustively table-pinned (C.3g) | `ML_Headers/NodeModelZoo.hpp` — both loaders `TryLoadRole(..., "<role_name>", ...)` for each known role incl. `exit`; the stamp's `expected_role` is ENFORCED at the chokepoint (`Model_RoleCheckDecide`, C.3h) |
| Stamp body | `stamp_write_for_model` writes registry hashes + cfg + label params | `verify_model_stamp` parses + checks against runtime build |
| Scaler sidecar | ⚠ DEAD PATH at HEAD (2026-08-20): the only `FeatureStandardizer_Save` producer is the dead legacy worker — the reachable MH path emits NO `.scaler`; restore-vs-retire is the open D6 fork | `FeatureStandardizer_Load` post-`Model_Load` (skips when the stamp carries no scaler binding — the current state for every HEAD-trained model); stamp records `scaler_sha256` when bound |
| Multi-horizon dir | Trainer writes to `<base>_horizon_<H>/` per horizon | `EnsembleModelZoo_AutoDetectFromDir` scans siblings via `Model_ParseHorizonSibling` (the ONE matcher — shared with the Settings bundle picker, E.1.2.C 3G-ii) |
| Class-extraction (`buy_class_idx`) | Implicit in label_kind semantics (PEAK_VALLEY_STABLE → class 1 = peak) | Loader's primary-role selector sets per-handle `buy_class_idx` based on `num_outputs` |
| Priority chain | n/a (trainer doesn't know which is "primary") | Loader picks priority: `buy_signal > barrier > regime > <future>` |

**When adding a new label kind / role / output semantics:**

ML side (1):
- Add new `FOREACH_TARGET(X)` row in `Backtest/LabelFunctions.hpp`
- Add label-compute function (returns float per sample)
- Add label_kind → role_name branch in trainer save loop
- LABEL_REGISTRY_HASH() flips automatically — old stamps refuse to
  load (forces retrain, by design)

LIVE side (5 — the v5.11.62 invariant):
- Add `ModelHandle<F> <new_role>;` to CoreModelZoo + ensemble array
- Add `CORE_MODEL_<NEW>` bitmask
- Add `TryLoadRole(..., "<new_role>", ...)` calls in LoadFromDir / LoadFromCfg
- Add branch to primary-role priority chain (decide where new role sits)
- Add branch to `EnsurePrimary` helper

PARITY side (1):
- Run `/parity-check role` (or full `/parity-check`) to verify both sides agree
- Snapshot test for new label-compute fn body (v5.9.2a pattern)
- Test that trainer's role file name matches live's `TryLoadRole` call

**Anti-pattern:** Adding a new label kind on the trainer side WITHOUT
the corresponding live-side addition. Symptom: model file saves
successfully under a new name, engine boots fine (no error), but the
model is silently skipped — no role found by `TryLoadRole`, primary-role
selector doesn't see it, strategy stays empty. Operator hits "model:
LOAD FAILED" with no clear cause. /parity-check role-parity walk
catches this class of bug at design time.

## Mixed-output ensembles (v5.X — deferred)

**Current state:** A multi-horizon run picks ONE `label_kind` for all
horizons (training UI enforces it). Resulting ensemble has uniform
output type (all regression, all binary, all 3-class). Bandit blend
works because all horizons return prediction values on the same scale.

**Deferred capability:** Heterogeneous ensembles where horizon 1 is
binary buy_signal (output ∈ [0,1]), horizon 2 is regression (output
∈ [-0.05, +0.05]), horizon 3 is 3-class barrier (out_result[1] ∈ [0,1]).
Currently broken at the bandit-blend layer because outputs aren't on
the same scale — averaging a -0.04 regression prediction with a 0.6
binary probability is nonsense.

**Fix shape (when re-triggered):**
- Per-handle `prediction_normalizer_fn` (default: passthrough).
  Loader sets per role:
  - Regression → `clamp((pred + tp_pct) / (2×tp_pct), 0.5, ...)`
- Bandit blend operates on normalized values, all in [0, 1].
- `Model_Predict_Ensemble_Weighted` calls normalizer post-`Model_Predict`.

**Why deferred:** Trainer doesn't currently produce mixed-output
ensembles. When operator needs them (e.g. "regression at long horizons,
classification at short horizons"), training-side first needs UI for
per-horizon label_kind selection. Then live-side adds the normalizer.
Two-ship sequence; live side blocked on trainer support.

**Tracked in:** `plans/_cross-cutting/2026-05-07-deferred-items.md` "v5.11.62 caveat —
Composite-signal extraction" entry covers per-handle composition;
mixed-output normalization is a sibling concern with a different fix
shape (normalizer fn vs. extractor fn). Both extend Model_Predict
without touching strategy code.

