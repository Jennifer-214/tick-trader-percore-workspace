# /parity-check report — v5.15.5 per-horizon TP/SL serving

## Plan summary

- HEAD `56435af` (v5.15 umbrella close).
- Audit scope: focused parity on a new train↔serve handoff surface
  (per-arm barriers loaded into ezoo from stamp; slow-path dispatch
  via 5-mode FOREACH_BARRIER_BLEND_MODE; cfg-drift Tier 1 promotion).
- Cross-check baseline: post-v5.15.4 protections inventory; PARITY-001
  through PARITY-023 are FIXED/CLOSED. Next allocatable ID is
  PARITY-024 (matches plan claim line 117).

The plan extends existing protected surfaces (stamp body, ezoo,
slow-path dispatch). The structural ground (FOREACH_STAMP_BOUND_CFG
+ STAMP_CFG_AUTOPOPULATE + SlowPathGateState + Surface G `has_*`
forward-compat + Class 18 PostLoadSetup registries + shadow-load hot
swap from v5.15.4) is mature; many parity surfaces are tested-by-
construction already.

---

## Per-surface drift verdict

| Surface | Verdict | Notes |
|---|---|---|
| **A. Tick consumption** | PASS — UNAFFECTED | Plan does not touch the tick path. |
| **B. Feature pipeline** | PASS — UNAFFECTED | No FOREACH_FEATURE / compute body change. |
| **C. Label pipeline** | PASS — UNAFFECTED | `label_tp_pct`/`label_sl_pct` are already in `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG` at lines 366-369. No new label kinds. |
| **D. Scaler sidecar** | PASS — UNAFFECTED | No scaler shape change. |
| **E. Stamp body schema** | DRIFT-SAFE | New `barrier_blend_mode` row in `FOREACH_STAMP_BOUND_CFG` flows via STAMP_CFG_AUTOPOPULATE; legacy stamps `has_barrier_blend_mode=0` → drift check skips silently (Surface G). HMAC byte preservation guaranteed if added at registry END (see HMAC check below). |
| **F. Cfg parity** | DRIFT-RISK (NEW: PARITY-024) | `ml_tp_pct` / `ml_sl_pct` Tier 1 promotion changes refuse behavior; legacy operator workflows where cfg-side barriers diverge by design will newly trigger WARN even in loose mode. Mitigation in plan: WARN only outside strict; `acknowledge_inference_cfg_drift=1` opt-out exists. |
| **G. Cross-binary handshake** | PASS — UNAFFECTED | No engine_version / build-flags / cadence change. |
| **H. Threading + init** | DRIFT-SAFE | EnsembleModelZoo extension; `EnsembleModelZoo_Init` / `_Free` reset paths flagged in plan Step A.3 — confirmed needed. PostLoadSetup registry add-step also flagged (Phase A wires it). |
| **I. Determinism** | DRIFT-SAFE (PROVISO) | Scalar path determinism via FPN_FromDouble<F>((double)float) round-trip is bytewise stable; argmax via `>` (not `>=`) is deterministic for tied weights → uniform-weights case picks idx 0 every time. AVX-512 sizing of `per_arm_barriers[16]` is layout-only in v5.15.5; vectorization deferred to v5.15.6 with required SHA-256 lock test. |
| **J. Observability** | DRIFT-SAFE w/ ADDITIONS REQUIRED | New PerCoreSnap field `ml_last_buy_dominant_horizon` mirrors v5.13.6.A exit-side pattern; new `barrier_mode_used` field also needed under modes 3-4. Shadow ring telemetry is new; needs an explicit `barrier_shadow_event_count` failure-mode field per CLAUDE.md item 13 (FOREACH_FAILURE_MODE). |
| **K. Build warnings** | DEFERRED — RUN POST-CODING | Not testable pre-code. Sprint-end full build + sanitizers required. |
| **L. Production-caller field-population** | DRIFT-SAFE | STAMP_CFG_AUTOPOPULATE handles `barrier_blend_mode` automatically across train_model_worker_fn, Backtest_RunFullValidation, EngineSharded.hpp emits (v5.14.1.E.E.B precedent). The previously-missing `STAMP_MODEL_CONST_AUTOPOPULATE` (PARITY-022) is not required because `label_tp_pct`/`label_sl_pct` are already in the registry from prior ships and populated via existing `StampHelper.hpp:241-242` path. |

---

## Cfg-drift Tier 1 promotion risk analysis

Plan Phase C promotes `ml_tp_pct` + `ml_sl_pct` to Tier 1. Current
Tier 1 set (`CoreFrameworks/ModelValidation.hpp:184-203`) = only
`confidence_threshold_scale` + `barrier_gate_enabled`. Tier 1
semantics: REFUSE in strict mode, WARN in loose mode.

**Risk analysis:**
- **Legacy stamps (pre-v5.15.5).** Surface G holds: `has_inference_cfg`
  / `has_*` flag absence → check skips silently per
  `ModelValidation.hpp:176`. Legacy operators are NOT impacted.
- **v5.15.5+ stamps + cfg drift in strict mode.** REFUSE fires. This
  is the intended behavior; the gap is closed.
- **v5.15.5+ stamps + cfg drift in LOOSE mode (NEW).** WARN fires
  (loud log line). Operators who deliberately train with one barrier
  and serve with a different one (e.g., "train tight, serve wide
  during paper-test") will see new noise. Acceptable but document.
- **`acknowledge_inference_cfg_drift=1` ack path.** Existing escape
  at line 176; covers Tier 1 + Tier 2 uniformly. Plan Phase C Step 2
  needs to verify this cfg flag does NOT need a per-tier split.
  Currently it's a single cfg ack; the ack covers both tiers (matches
  pattern). Acceptable.

**Recommended fix (DRIFT-SAFE):** ship Tier 1 promotion as
spec'd. Plan documents the loose-mode behavior in CHANGELOG. The
`barrier_blend_mode` Tier 1 binding (Phase A Step 1 line 274) is
the more important closure — without it, operator-side cfg flips of
mode while a v5.15.5 stamp is loaded would create silent drift.

---

## HMAC chain preservation check

`FOREACH_STAMP_BOUND_CFG` emit order is HMAC-locked
(`PRE_CFG → FOREACH_STAMP_BOUND_CFG → POST_CFG` per CLAUDE.md item 22).

**Plan addition:** new `barrier_blend_mode` row in
`FOREACH_STAMP_BOUND_CFG` (StampBoundCfgRegistry.hpp). The current
registry ends at line 175-176 with `trading_mode` (v5.15.2).

**HMAC byte-equivalence rules from
`wire-format-byte-preservation-discipline.md`:**
1. New row must be appended at the END of the existing registry, NOT
   inserted in the middle (would shift downstream entries' canonical
   wire-byte positions).
2. `emit_when` predicate must be TRUE for v5.15.5+ stamps; FALSE
   would mean legacy stamps have it absent. Plan says default
   `barrier_blend_mode=LEGACY` (= 0). The eligibility decision:
   emit unconditionally (`1`) so the stamp captures the
   training-time mode regardless. Mirrors `trading_mode` (always
   emits, `1`).
3. `BITMAP_BIT` vs `DIRECT_FIELD`: since
   `per_horizon_barrier_blend` is a direct cfg int (NOT in
   `ml_cfg_flags`), use `DIRECT_FIELD`. Compatible with
   STAMP_CFG_AUTOPOPULATE.

**VERDICT: HMAC chain preservation GREEN** if plan adds the row at
the END (after `trading_mode` at line 175-176) with `1` as
`emit_when` and `DIRECT_FIELD` source. Legacy stamp byte-positions
unchanged.

---

## Section J findings — observability surface coverage

The plan extends MLStatusPanel with a buy-side dominant-horizon
display field (`ml_last_buy_dominant_horizon`). Phase B Step 2 cites
the v5.13.6.A `ml_last_exit_dominant_horizon` pattern correctly
(verified at `DataStream/EngineTUI.hpp:1090` +
`GUI/MLStatusPanel.hpp:183-186` +
`CoreFrameworks/ShardedSnapshot.hpp:598`).

**Required additional observability for shadow modes 3-4:**
- **`barrier_mode_used`** PerCoreSnap field (uint8_t enum of
  FOREACH_BARRIER_BLEND_MODE). MLStatusPanel renders alongside
  the dominant_horizon display. Critical: under modes 3-4 the
  operator must SEE which mode actually drove the trade to
  attribute paper-test outcomes correctly.
- **`barrier_shadow_event_count`** counter (COUNTER_U32 in
  FOREACH_FAILURE_MODE). Without it, shadow-ring drops or telemetry
  failures are invisible. Pattern matches `ml_nan_prediction_events`
  (FailureModeRegistry.hpp:148-153).
- **Rate-limited CRITICAL log** for mode-N when ezoo lacks barriers
  but cfg requested mode-N. Pattern matches
  `Health_LogCriticalRateLimited` calls used throughout
  StrategyParameters.hpp.

**VERDICT: Section J — DRIFT-RISK** for shadow modes 3-4 without
the additional observability fields. Recommend bundling into Phase
A as part of the failure-mode registry extension.

---

## Section L findings — production-caller field-population audit

Walked the field-population sites for `barrier_blend_mode`:

1. **Field defined in struct** — YES (added to
   `StampInferenceCfgInputs` via FOREACH_STAMP_BOUND_CFG row
   expansion).
2. **Verifier reads it via X-macro** — YES via the AUTOPOPULATE
   walk at `CoreModelZoo.hpp:208-241`.
3. **Every production caller populates it** — VERIFY before
   coding. Production callers (post-PARITY-020 v5.15.3 closure):
   - `BacktestEngine.hpp` Backtest_RunFullValidation — auto-populates
     via STAMP_CFG_AUTOPOPULATE.
   - `train_model_worker_fn` — fixed in v5.15.3 to auto-populate.
   - `EngineSharded.hpp` emit paths (if any train-only models stamp
     here) — should not stamp; verify.
4. **CLI tool exposes it** — `tools/stamp_model.sh` (bash) auto-flow
   via `tools/gen_stamp_writer.py` (per the X-macro generator
   pattern). Verify after Phase A.
5. **GUI suite cfg/UI input** — Dropdown auto-derives from
   `FOREACH_BARRIER_BLEND_MODE` per the v5.13.5 Label Kind CSV
   pattern. GREEN by construction.

**VERDICT: Section L — DRIFT-SAFE** by construction via existing
AUTOPOPULATE machinery. No new production-caller class can recur for
this field.

---

## Shadow mode determinism verification

Plan modes 3 (BOTH_BLEND_DRIVES) and 4 (BOTH_DOMINANT_DRIVES) each
compute BOTH the blended barrier AND the dominant barrier per cycle
+ push records to a 256-deep shadow ring on ezoo.

**Replay determinism check (CLAUDE.md item 25):**
- Inputs to both paths: `weights_buf[]` (already finalized
  pre-mode-dispatch at StrategyParameters.hpp:1029); `ezoo->per_arm_buy_tp_pct[]`
  / `per_arm_buy_sl_pct[]` (stamp-loaded, immutable post-load).
- `weights_buf[]` provenance: Exp3-IX bandit (deterministic given
  seed+rewards) OR Thompson with splitmix64 PRNG seeded by
  `cfg.thompson_rng_seed` (deterministic per PARITY-014 close).
- Dominant argmax: branchless `>` semantics → ties resolve to first
  index (idx 0); bytewise stable across runs.
- Blend: `Σ wᵢ · barrierᵢ` over constant `primary_count`
  iterations; FP64 multiply-accumulate is deterministic for fixed
  input order (matches CLAUDE.md item 26 constant-iter pattern).
- Shadow ring records: `(actual_tp, shadow_tp, actual_sl, shadow_sl,
  weights_buf, dominant_idx)`. All inputs are deterministic; record
  push is a slow-path-only sequenced write.

**Gap:** plan does not specify that shadow ring records are written
to a struct with explicit `_padding = 0` per CLAUDE.md item 27. If
the operator persists shadow records cross-run via JSON sidecar
(plan mentions `barrier_mode_shadow_stats.json` at line 184-186),
locale pinning (LC_NUMERIC=C) must be applied per the
v5.14.10.C precedent (`Bandit_SaveJSON` at BanditLearning.hpp:386-388).

**VERDICT: Shadow mode determinism — DRIFT-SAFE** in-memory; **DRIFT-RISK**
for the JSON sidecar without explicit locale pinning. Recommend
plan Phase A Step adds the `newlocale(LC_NUMERIC_MASK, "C", 0)`
sequence to the shadow-stats writer.

---

## Per-arm reward observability invariant check under modes 3/4

CLAUDE.md item 24: per-arm direction-graded reward holds (rewards
computed PER-ARM independently against actual price movement; not
gated by which arm fired).

**Mode 3 (BOTH_BLEND_DRIVES):** blend value drives the trade; dominant
is shadow. The CHOICE that drove the trade is the BLEND (a mixed
position over all arms). Reward attribution stays per-arm because
each arm's PREDICTION is graded against the actual outcome
independently — the trade-outcome attribution layer is unaffected
by the barrier-blend mode (barriers are output policy, not the
prediction grading signal). **HOLDS.**

**Mode 4 (BOTH_DOMINANT_DRIVES):** dominant arm drives; blend is
shadow. Same reasoning: per-arm prediction-grading is independent of
which arm's BARRIER was used; CLAUDE.md item 24's "reward
attribution moves from per-arm prediction-grading to per-arm
trade-outcome attribution" caveat is NOT crossed here because
v5.15.5 doesn't move attribution to trade-outcome. **HOLDS.**

**v6.0+ caution (DOCUMENT-ONLY).** If a future maker-order placement
mode is added (per CLAUDE.md item 24 warning), the
barrier-mode choice could ALTER market impact / fill probability
per arm — breaking the invariant for that surface. v5.15.5 doesn't
do that.

**VERDICT: Per-arm reward observability — PASS.** Both shadow modes
preserve the invariant. Plan line 188-191 correctly states this.

---

## Bandit arm_names extraction risk (Rule 1)

Plan line 501 proposes extracting `BanditState.arm_names[8][32]`
into a new `BanditDisplayMeta` struct as part of the cache-layout
discipline sweep.

**Verified callers reading `arm_names`:**
- `ML_Headers/BanditLearning.hpp:337` — `Bandit_Print` diagnostic
- `ML_Headers/BanditLearning.hpp:429` — `Bandit_SaveJSON` write
  path
- `DataStream/EngineTUI.hpp:719` — TUI snapshot populate, reads
  from `ctrl->bandit.arm_names` (LEGACY single-bandit, not ezoo)
- `Bandit_LoadJSON` does NOT parse arm_names (verified at lines
  552-677); arm_names are write-only in persistence

**Verified non-callers (no risk):**
- No code reads `ezoo->bandits[r].arm_names[i]` (grep returned zero).
- No memcmp/offsetof on `BanditState` (grep returned zero).

**Migration safety:**
- `Bandit_Print` + `Bandit_SaveJSON` must update to read from the
  new `BanditDisplayMeta` path (~3 file edits).
- `EngineTUI.hpp:719` reads `ctrl->bandit.arm_names` — this is the
  LEGACY single-bandit on PortfolioController, NOT the
  ezoo->bandits. If Rule 1 only moves ezoo->bandits.arm_names out,
  the legacy path is unaffected. If Rule 1 also moves
  `ctrl->bandit.arm_names` out, EngineTUI.hpp line 719 + 730 must
  update to read from `ctrl->bandit_display_meta.arm_names`.

**VERDICT: Rule 1 arm_names extraction — DRIFT-SAFE** if plan
explicitly enumerates ALL 3-4 callers in Phase A.1 Step list. Risk
becomes DRIFT-BUG if any caller is missed. Mitigate via a
controller_test check that `sizeof(BanditState)` shrinks by
exactly `BANDIT_MAX_ARMS * 32 * NUM_REGIMES` after the move (catches
incomplete extraction).

---

## Recommended fixes per finding

| Finding | Severity | Recommended fix | Class |
|---|---|---|---|
| F1: Tier 1 loose-mode noise | LOW | Document in CHANGELOG; operator already has `acknowledge_inference_cfg_drift=1` escape | DRIFT-SAFE |
| F2: Shadow JSON locale pinning missing in plan spec | MEDIUM | Add `newlocale(LC_NUMERIC_MASK, "C", 0)` to shadow-stats writer per Bandit_SaveJSON precedent | DRIFT-RISK |
| F3: Missing PerCoreSnap fields for modes 3-4 | HIGH | Bundle `barrier_mode_used` + `barrier_shadow_event_count` into Phase A failure-mode registry extension | DRIFT-RISK |
| F4: Rule 1 arm_names extraction caller enumeration | MEDIUM | Plan A.1 lists all 3-4 callers explicitly; add `static_assert` test for sizeof shrinkage | DRIFT-RISK |
| F5: AVX-512 sizing without SHA-256 lock | DOCUMENT-ONLY | Plan correctly defers vectorization to v5.15.6; scalar path is bytewise determined now | DRIFT-SAFE |
| F6: Q1 (dominant lacks stamped barriers, mixed ensemble) | MEDIUM | Plan answer (fall back to cfg) is correct; ensure WARN log surfaces the mixed condition once per slow-path cycle (rate-limited) | DRIFT-SAFE |
| F7: HMAC byte preservation if barrier_blend_mode inserted mid-registry | HIGH | Append at END of FOREACH_STAMP_BOUND_CFG after `trading_mode` row (line 175-176); verify test asserts byte-equivalent stamp output for legacy cfg shape | DRIFT-RISK |

---

## Verdict: YELLOW

Proceed with the following must-fix amendments BEFORE Phase A coding:

1. **F3 (HIGH)** — add `barrier_mode_used` + `barrier_shadow_event_count`
   to FOREACH_FAILURE_MODE in Phase A scope. Without these,
   shadow-mode telemetry has silent failure modes.
2. **F7 (HIGH)** — Phase A Step that adds `barrier_blend_mode` row
   to `FOREACH_STAMP_BOUND_CFG` explicitly states "append AFTER the
   `trading_mode` row at line 175-176" so reviewer + future-Claude
   see the HMAC ordering rule.
3. **F2 (MEDIUM)** — shadow-stats JSON writer pins LC_NUMERIC=C via
   `newlocale` + `uselocale` sequence per Bandit_SaveJSON precedent.
4. **F4 (MEDIUM)** — Phase A enumerates all `arm_names` callers
   explicitly + adds the sizeof shrinkage `static_assert` test.

All four are mechanical plan-text amendments (~15 min); no design
revision needed. The structural ground is solid; the plan correctly
identifies all major patterns (X-macro, AUTOPOPULATE, PostLoadSetup
registry, slow-path gate cache, FOREACH_FAILURE_MODE,
calibration-log-column-registry).

PARITY-024 auto-written to `DOCS/PARITY_ISSUES.md` for the
`ml_tp_pct`/`ml_sl_pct` Tier 1 promotion as the canonical entry
closing the train-serve barrier-parity gap.

---

## NOT a bug (verified-safe items)

- Per-arm reward observability under modes 3-4 (CLAUDE.md item 24
  invariant HOLDS).
- HMAC chain preservation if `barrier_blend_mode` appended at
  registry END.
- Scalar argmax determinism via `>` semantics.
- Legacy stamp Surface G compatibility (`has_*=0` → drift check
  silent skip).
- `Bandit_LoadJSON` does NOT round-trip arm_names → extraction safe
  on the persistence path.
- AVX-512 sizing of `per_arm_barriers[16]` is layout-only; scalar
  path is the load-bearing surface in v5.15.5.

---

## Suggested ship sequence (unchanged from plan)

The 7-sub-ship layout (.A → .G + umbrella) is correctly sequenced.
After must-fix amendments above:
- v5.15.5.A — per-arm barrier load + mode dispatch + shadow telemetry
  + bandit Rule 1 + observability + cfg-drift binding (largest ship;
  amendments fold cleanly)
- v5.15.5.B-E — cache-layout sweeps (separate concerns, mechanical)
- v5.15.5.F — sprint-end verification (run `/parity-check` again
  here for post-coding confirmation)
- v5.15.5.G — symmetric Thompson mode 3
- v5.15.5 umbrella — sprint-close
