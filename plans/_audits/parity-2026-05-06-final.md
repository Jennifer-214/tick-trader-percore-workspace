# /parity-check report — 2026-05-06 (POST-CLOSURE RE-AUDIT, v5.10-final)

## Plan summary

- **HEAD** `1a22b19` (tag `v5.10.3` — "Display + observability surface")
- **Tests** 1636/0 (verified by `./build/controller_test` end-to-end run)
- **calls_graph_diff** not run (skill assumes existing tests pass; verified)
- **Audit scope** full (post-closure re-audit)
- **Cross-check baseline** post-v5.10.3 protections inventory (v5.10.0 stack
  + v5.10.1.A/B/C + v5.10.2.A/B + v5.10.3.A/B/C)

This is the POST-CLOSURE re-audit at v5.10-final. The original
`parity-2026-05-06-full.md` audit (HEAD = `7f0b9a9`) found 13
findings (2 CRITICAL, 6 HIGH, 5 MEDIUM, 2 LOW, 2 DOCUMENT-ONLY). The
operator shipped 3 close-out sub-ships in the same session
(v5.10.1 + v5.10.2 + v5.10.3) addressing 9 of 13. This re-audit
verifies each closure landed correctly and identifies any new gaps
that surfaced in the process.

---

## Closure verdict by Finding (re-audit)

| # | Severity | Original audit summary | Closure ship | **Re-audit verdict** |
|---|----------|------------------------|--------------|----------------------|
| 1 | CRITICAL | LABEL_REGISTRY_HASH dead in production (4 sites) | v5.10.1.A | **CLOSED** |
| 2 | CRITICAL | grid_member_count dead in production | v5.10.1.B (consume-side, Option C) | **CLOSED (consume-side)** — emit-side deferred per documented plan |
| 3 | HIGH | Hot swap bypasses inference_cfg drift block | v5.10.2.A | **CLOSED** |
| 4 | HIGH | Hot swap doesn't touch ensemble (mismatch) | v5.10.2.B (refusal path) | **CLOSED (Option A)** — full ensemble-swap deferred |
| 5/15 | HIGH (compound) / LOW | is_buyer_maker dropped between SPSC + slow-path | v5.10.3.C (comments + KNOWN_ISSUES) | **DOCUMENTED** — full plumb-through deferred |
| 6 | HIGH | AutoDetect args plumb-through (2 sites) | v5.10.1.C | **CLOSED** |
| 7 | HIGH | Drift block doesn't iterate ensemble handles | v5.10.2.A (single helper) | **CLOSED** |
| 8 | HIGH | TUI strat_stats[5] vs NUM_STRATEGIES=6 UB warning | v5.10.3.A | **CLOSED** (warning gone) |
| 9 | MEDIUM | drift state not surfaced to PerCoreSnap | v5.10.3.B | **CLOSED** |
| 10 | MEDIUM | cfg_drift counters stale after hot swap | v5.10.2.A (closes via #3) | **CLOSED** |
| 11 | MEDIUM | drift_history not snapshot-persisted | v5.10.3.C (KNOWN_ISSUES doc) | **DOCUMENTED** as planned |
| 12 | MEDIUM | Ensemble cfg unstamped (silent decision drift) | — | **DEFERRED to v5.11+** as planned |
| 13 | MEDIUM | Backtest path skips stamp verification (LoadFromDir, NOT AutoDetectFromDir) | — | **NEW GAP CONFIRMED OPEN** (see below) |
| 14 | LOW | Build warning -Wstringop-overflow at ControllerEventLoop.hpp:834 | — | **DEFERRED** (pre-existing, accepted) |
| 16 | DOCUMENT-ONLY | Producer SPSC drop class | — | DOCUMENT-ONLY (architectural) |
| 17 | DOCUMENT-ONLY | XGBoost training-script determinism | — | DOCUMENT-ONLY (operator-side) |

**9 of 13 closures verified correct. 1 unexpected open gap (Finding
#13). 4 expected-deferred items (#11, #12, #14 + #17).**

---

## Per-Finding closure verification

### Finding #1 — LABEL_REGISTRY_HASH plumb-through (CRITICAL → CLOSED)

**Verified:**
- **Emit site 1 (RFV):** `Backtest/BacktestEngine.hpp:1164-1167`
  ```cpp
  // v5.10.1.A — LABEL_REGISTRY_HASH plumb-through (parity-check Finding #1).
  inf.has_label_registry_hash = 1;
  inf.label_registry_hash     = LABEL_REGISTRY_HASH();
  ```
- **Emit site 2 (Train Model worker):** `Backtest/BacktestPanels.hpp:2682-2687`
  Same shape; both production stamp-emitters now populate the field.
- **Consume site 1 (live load):** `ML_Headers/CoreModelZoo.hpp:135-140` —
  `verify_model_stamp` called with 6 args including
  `LABEL_REGISTRY_HASH()` (was 5 args, defaulting 6th to 0 → silently
  bypassed).
- **Consume site 2 (UI Verify Stamp):** `Backtest/BacktestPanels.hpp:1289-1295` —
  same fix.
- **Include added:** `ML_Headers/CoreModelZoo.hpp:38` — `#include
  "../Backtest/LabelFunctions.hpp"` (so `LABEL_REGISTRY_HASH()` resolves).
- **Production round-trip test:** `tests/controller_test.cpp:13558-13628` —
  EXTENSIBILITY block "v5.10.1.A — LABEL_REGISTRY_HASH production-caller
  plumb-through". 5 `check()` calls including REFUSE-on-wrong-hash and
  ACCEPT-on-correct-hash via the production-path verify call shape.

**Conclusion:** Closure complete. The Surface L gap that originally
shipped v5.10.0d's verifier without production wiring is now closed.

### Finding #2 — grid_member_count consistency validator (CRITICAL → CLOSED consume-side)

**Verified (consume-side, Option C):**
- **Helper:** `EnsembleZoo_VerifyGridMemberConsistency<F>` at
  `ML_Headers/CoreModelZoo.hpp:1141-1208`. Templated, boundary-stable
  (no `ModelHandle` struct cascade). Re-parses each loaded handle's
  stamp file via `verify_model_stamp` to extract `grid_member_count`.
- **Caller:** `EnsembleModelZoo_AutoDetectFromDir` at
  `ML_Headers/CoreModelZoo.hpp:1310-1322` — runs validator after
  `EnsembleModelZoo_LoadFromCfg` returns; on REFUSE (return 0), unwinds
  via `EnsembleModelZoo_Free` and returns 0 (no models loaded).
- **Back-compat WARN log present:** lines 1199-1205 cite "TODO(v5.10.X):
  wire stamp_write_for_model into train_multi_horizon_worker_fn to
  emit stamps." (Closure of Finding #2's emit-side requires multi-
  horizon trainer integration, deferred per master plan recommendation.)
- **3 unit tests with 0xDEADBEEF mock-handle pattern:**
  `tests/controller_test.cpp:13396-13556` —
  - Test B.1: Uniform `grid_member_count = 3` → return 1 (OK)
  - Test B.2: Mismatched `grid_member_count` per handle → return 0 (REFUSE)
  - Test B.3: Legacy stamps without `has_grid_member_count` → return 1 + WARN
- **Distinct refusal log present:** lines 1184-1188 fire on mismatch.

**Conclusion:** Consume-side closure landed correctly. Emit-side
deferral matches the master plan + readiness check; documented in the
validator's WARN log AND in `DOCS/KNOWN_ISSUES.md`.

### Finding #3 — Hot swap bypasses drift block (HIGH → CLOSED)

**Verified:**
- **Helper extracted:** `CoreModelZoo_ValidateAgainstCfg<F>` at
  `CoreFrameworks/EngineSharded.hpp:362-568`. Subsumes:
  - v5.9.5h xgb-and-friends WARN (training_poll_interval +
    xgb_hyperparams + build_flags_hash) — gated by
    `!acknowledge_cross_binary_version_drift`
  - v5.9.5i inference_cfg drift Tier 1 REFUSE (freshness_tau,
    threshold_scale, barrier_gate_enabled) + Tier 2 WARN (hard_block,
    bandit, fees) — gated by `!acknowledge_inference_cfg_drift`
- **Boot loop call site:** `CoreFrameworks/EngineSharded.hpp:1119-1140`
  (replaces ~200 LOC of inline blocks)
- **Hot swap branch call site:** `CoreFrameworks/EngineSharded.hpp:2592-2607`
  (post-`CoreModelZoo_LoadFromDir` success). On `validate_rc < 0` in
  strict mode, sets `model_load_failed=1` (degraded-but-loaded
  semantics; true rollback deferred per documented commit message).
- **Distinguishable log prefix:** `core 0` vs `core 0 ensemble[2]`
  via the `loc[64]` snprintf at lines 384-389 of the helper.

**Conclusion:** All three prior inline blocks merged into single
helper, called from both boot AND hot-swap paths. Closure complete.

### Finding #4 — Hot swap REFUSED when ensemble active (HIGH → CLOSED)

**Verified at `CoreFrameworks/EngineSharded.hpp:2541-2560`:**
```cpp
} else if (state.cores[c].ensemble_handle != nullptr) {
    // v5.10.2.B — REFUSE hot swap when ensemble is active...
    fprintf(stderr,
        "[hot_swap] core %d REFUSED: ensemble inference "
        "active; ... Restart engine with new core_%d_model_dir...\n",
        c, c);
    __atomic_store_n(
        &g_shared.swap_model_path_requested[c], 0,
        __ATOMIC_RELEASE);
}
```
- Guard correctly clears `swap_model_path_requested[]` (button reset).
- Does NOT call `CoreModelZoo_Free(swap_zoo)` when ensemble active
  (correct: the else branch at line 2561+ handles the safe swap).
- Distinct log message confirms operator must restart to swap horizon set.
- Full ensemble swap (Option B) appropriately deferred to v5.10.2.X /
  v5.11+ if requested by operator.

**Conclusion:** Refusal-path implementation is correct.

### Finding #5/#15 — is_buyer_maker (HIGH compound bug → DOCUMENTED)

**Verified comment plumbing:**
- **TickRecorder_Push site:** `CoreFrameworks/EngineSharded.hpp:1467-1474` —
  detailed comment cites parity-check Finding #5, names the carry-
  forward as v5.1.2 architectural, notes train-serve parity preserved,
  cites the file at line 1474.
- **Slow-path RollingStats site:** `CoreFrameworks/EngineSharded.hpp:2669` —
  `/*is_buyer_maker=*/0, // TODO(parity-check Finding #5): plumb through
  scalar bus (v5.10.X)` — inline TODO.
- **BacktestSharded site:** `Backtest/BacktestSharded.hpp:85-91` —
  comment block notes `h->is_buyer_maker IS available; the conversion
  drops it to mirror the live slow-path's hardcoded-0 (parity-preserving
  for now).` Cites Finding #5.
- **KNOWN_ISSUES.md entry:** `DOCS/KNOWN_ISSUES.md:310-345` — full
  symptom + root cause + parity status (preserved) + mitigation +
  4h closure plan + cite to `parity-2026-05-06-full.md` Finding #5.

**Conclusion:** Document-only closure complete. Original Finding #5's
"effort estimate 1h (Step 1 alone) or 4h (full)" is preserved in the
KNOWN_ISSUES doc for v5.10.X / v5.11+ pickup.

### Finding #6 — AutoDetect args plumb-through (HIGH → CLOSED)

**Verified at 2 sites:**
- **Live caller:** `CoreFrameworks/EngineSharded.hpp:1076-1083` — passes
  `cfg.held_out_stamp_secret`, `FPN_ToDouble(cfg.gap_acceptable_threshold)`,
  `cfg.held_out_gate_strict`, `cfg.acknowledge_cross_binary_version_drift`.
- **Backtest caller:** `Backtest/BacktestSharded.hpp:306-313` — same shape.

**Note on file-line drift:** original audit cited
`EngineSharded.hpp:832-835` and `BacktestSharded.hpp:296-299`. Current
HEAD has these calls at lines 1076 and 306 respectively (file size
grew +244 in EngineSharded and +10 in BacktestSharded due to the
v5.10.2.A helper extraction). The closure is verified at the actual
call sites, not the original cited line numbers.

**Conclusion:** Both production callers now respect operator's
`held_out_gate_strict` cfg in ensemble mode.

### Finding #7 — Drift block iterates ensemble handles (HIGH → CLOSED)

**Verified inside the helper at `CoreFrameworks/EngineSharded.hpp:529-549`:**
```cpp
// 1. Single zoo: 4 roles
if (zoo) {
    check_handle(&zoo->buy_signal, "buy_signal", -1);
    check_handle(&zoo->barrier,    "barrier",    -1);
    check_handle(&zoo->regime,     "regime",     -1);
    check_handle(&zoo->exit,       "exit",       -1);
}
// 2. Ensemble handles (Finding #7 closure): 4 roles × N horizons
if (ezoo && ezoo->active) {
    for (int h = 0; h < ezoo->buy_signal_count; ++h)
        check_handle(&ezoo->buy_signal[h], "buy_signal", h);
    for (int h = 0; h < ezoo->barrier_count; ++h)
        check_handle(&ezoo->barrier[h], "barrier", h);
    for (int h = 0; h < ezoo->regime_count; ++h)
        check_handle(&ezoo->regime[h], "regime", h);
    for (int h = 0; h < ezoo->exit_predictor_count; ++h)
        check_handle(&ezoo->exit_predictor[h], "exit", h);
}
```
- Field name `exit_predictor` (NOT `exit`) used correctly for ensemble
  parallel arrays per `CoreModelZoo.hpp:616`.
- `h_idx >= 0` triggers the `core 0 ensemble[h]` log prefix (lines 384-389).
- Helper is invoked from boot (line 1126-1133) with `ezoo` derived from
  `state.cores[i].ensemble_handle`.

**Conclusion:** Ensemble handles now walk through the same Tier 1/Tier
2 drift detection as single zoo, with distinguishable per-horizon logs.

### Finding #8 — TUI strat_stats sizing (HIGH → CLOSED)

**Verified:**
- **Array declaration:** `DataStream/EngineTUI.hpp:911` —
  `StrategyStatsSnap strat_stats[NUM_STRATEGIES];` (was `[5]`, now 6).
- **Population loop:** `DataStream/EngineTUI.hpp:1422-1428` — iterates
  `< NUM_STRATEGIES_REAL` (= 5) for the source `ctrl->strategy_stats[]`,
  then explicitly `snap->strat_stats[NUM_STRATEGIES_REAL] = {};` zeros
  the AUTO bin.
- **Compile-time warning gone:** `./build.sh test` produces no
  `-Waggressive-loop-optimizations` warnings (TUIAnsi loops at `<
  NUM_STRATEGIES = 6` now read valid zero-init data at index 5).
- **Display↔execution invariant restored:** AUTO bin reads zero counts
  (intended), not garbage that varies by `-O` level.

**Conclusion:** UB closed; the warning that prompted the finding is
gone in current builds.

### Finding #9 — drift_history → PerCoreSnap (MEDIUM → CLOSED)

**Verified all 4 fields and their populator + render:**
- **PerCoreSnap fields** at `DataStream/EngineTUI.hpp:1113-1116`:
  ```cpp
  uint8_t  drift_breached;       // 1 = drift_history.breached at snapshot
  uint8_t  drift_kill_tripped;   // 1 = auto_kill_on_drift triggered
  uint16_t drift_n_samples;      // current ic_samples count (0..256)
  double   drift_avg_ic;         // live-computed avg IC over the ring
  ```
- **Populator** at `CoreFrameworks/ShardedSnapshot.hpp:480-488` — copies
  `breached`/`kill_tripped`/`count`, live-computes avg from
  `ic_samples[]` ring.
- **ML Status panel render** at `GUI/MLStatusPanel.hpp:219-238` — distinct
  branches:
  - `drift: KILLED (avg_ic=..., n=...)` in red on `drift_kill_tripped`
  - `drift: BREACHED (avg_ic=..., n=...)` in orange on `drift_breached`
    (without kill)
  - tooltip explains BREACHED vs KILLED + recovery steps
- **`SHARDED_SNAPSHOT_VERSION` unchanged at 6** — confirmed at
  `CoreFrameworks/ShardedSnapshotPersist.hpp:75`. Correct since
  PerCoreSnap is TUI-side only (not snapshot-persisted).

**Conclusion:** Section J discipline restored — drift-kill is now
distinguishable from MTM-kill / manual-kill.

### Finding #10 — cfg_drift counters stale after hot swap (MEDIUM → CLOSED via Finding #3)

**Verified inside the helper at `CoreFrameworks/EngineSharded.hpp:551-556`:**
```cpp
// Writeback drift counters (Finding #10 closure: now updated on hot-swap too)
if (ctx) {
    ctx->cfg_drift_tier1_count = ...;
    ctx->cfg_drift_tier2_count = ...;
    ctx->cfg_drift_strict_refused = ...;
}
```
Helper is called from both boot (line 1128, with `&state.cores[i]`) and
hot-swap (line 2592, with `&state.cores[c]`). Both writes mutate the
same `CoreContext.cfg_drift_*` fields.

**Conclusion:** Counters now reflect the latest stamp's drift state
post-swap (was frozen at boot-time values pre-fix).

### Finding #11 — drift_history not snapshot-persisted (MEDIUM → DOCUMENTED)

**Verified `DOCS/KNOWN_ISSUES.md:347-371`:**
- Symptom: drift detection re-warms from empty post-restart, taking up to
  `confidence_ic_floor_window` seconds (default 86400 = 24h) before
  re-arming.
- Root cause: `SHARDED_SNAPSHOT_VERSION=6` doesn't serialize
  `CoreContext.drift_history` (struct introduced at v5.10.0e;
  `ML_Headers/ConfidenceScore.hpp:265-273`).
- Mitigation: lower `confidence_ic_floor_window` for faster re-arming.
- Full closure plan: `~2.5h, v5.10.X or v5.11+` — bump
  `SHARDED_SNAPSHOT_VERSION` to 7, serialize 7 fields, add back-compat
  read for v6.
- Cites `parity-2026-05-06-full.md` Finding #11.

**Conclusion:** Document-only closure complete. Acceptable for v5.11
opening because drift detection is wall-clock-windowed (eventually
re-arms without operator action).

### Finding #12 — Ensemble cfg unstamped (MEDIUM → DEFERRED)

**Verified deferral.** No new wiring in `StampInferenceCfgInputs` for
ensemble cfg fields (ensemble_blend_mode, horizon_list, ensemble_bandit_eta,
etc.). Master plan recommendation was "defer to v5.11+"; this was
correctly NOT touched in v5.10 close.

**Conclusion:** Deferred as planned. v5.11 sprint should pick this up
as a Surface G stamp body extension (~2-3h, same shape as v5.9.5h
xgb_hyperparams).

### Finding #13 — Backtest path skips stamp verification (MEDIUM → **NEW GAP CONFIRMED OPEN**)

**Re-audit finding:** the task spec asked whether v5.10.1.C's plumb-
through covered Finding #13. **It does not.**

- **Original Finding #6 cited site:** `BacktestSharded.hpp:296-299` —
  `EnsembleModelZoo_AutoDetectFromDir` call (the ensemble-mode path).
- **Original Finding #13 cited site:** `BacktestSharded.hpp:256-257` —
  `CoreModelZoo_LoadFromDir` call (the single-zoo path).
- **v5.10.1.C diff verified via `git show 32155e1 -- Backtest/BacktestSharded.hpp`:**
  Only the `EnsembleModelZoo_AutoDetectFromDir` call site received the
  4-arg plumb-through. The `CoreModelZoo_LoadFromDir` call at the same
  file is **unchanged**.
- **Current state at `Backtest/BacktestSharded.hpp:262-264`:**
  ```cpp
  if (cfg.core_model_dir[i][0]) {
      loaded = CoreModelZoo_LoadFromDir(&ml_zoos[i],
                                         cfg.core_model_dir[i], backend);
      // ^ NO secret / gap / strict / drift args passed
  ```
  The function defaults: `secret=nullptr, gap=0.05, strict=0,
  acknowledge_cross_binary_drift=0`.
- **Live path (reference):** `CoreFrameworks/EngineSharded.hpp:1023-1026`
  passes `cfg.held_out_gate_strict` + `cfg.acknowledge_cross_binary_version_drift`.

**Severity rationale for re-audit:** still MEDIUM. Backtest train-time
verification is silently warn-only when operator runs
`held_out_gate_strict=1`. Live path is correct; backtest mismatches.
Same model triggers different verification outcomes between the two
suites a single operator workflow uses.

**Recommended fix (~30 min):** add the same 4 cfg-derived args to
`Backtest/BacktestSharded.hpp:263-264`:
```cpp
loaded = CoreModelZoo_LoadFromDir(
    &ml_zoos[i], cfg.core_model_dir[i], backend,
    cfg.held_out_stamp_secret,
    FPN_ToDouble(cfg.gap_acceptable_threshold),
    cfg.held_out_gate_strict,
    cfg.acknowledge_cross_binary_version_drift);
```

**Cross-ref:** sibling of Finding #6. Should have been closed in
v5.10.1.C alongside the AutoDetect call (same file, ~40 lines apart);
appears to have been an oversight. The v5.10.1.C commit message lists
only Finding #6 as the closure target.

**Status: OPEN — single-line fix recommended for v5.10.4 hotfix OR
absorb into v5.11.0 system-foundation kickoff.**

### Finding #14 — Build warning -Wstringop-overflow (LOW → DEFERRED)

**Verified still warning:** `./build.sh test` after `touch
CoreFrameworks/ControllerEventLoop.hpp` produces:
```
ControllerEventLoop.hpp:834:42: warning: writing 1 byte into a
region of size 0 [-Wstringop-overflow=]
```
Pre-existing, low severity. Left intentionally per task spec ("LOW
severity, deferred"). The recommended fix at original Finding #14
(static_assert on `MAX_EXECUTION_CORES` bound or `#pragma GCC
diagnostic ignored`) is a 15-min cosmetic fix for v5.11+.

**Conclusion:** Status unchanged — DEFERRED.

---

## What's NOT closed (re-audit confirmed)

| # | Severity | Status | Action |
|---|----------|--------|--------|
| 11 | MEDIUM | DOCUMENTED in `DOCS/KNOWN_ISSUES.md` | Acceptable for v5.11 open. Full closure ~2.5h. |
| 12 | MEDIUM | DEFERRED to v5.11+ as planned | Surface G stamp body extension (~2-3h). |
| 13 | MEDIUM | **NEW GAP CONFIRMED — single-line fix recommended** | ~30 min: plumb 4 cfg args to BacktestSharded.hpp:263 LoadFromDir call. |
| 14 | LOW | DEFERRED (pre-existing, accepted) | 15-min cosmetic fix possible in v5.11+. |
| 16 | DOCUMENT-ONLY | Architectural bound | Not closeable. |
| 17 | DOCUMENT-ONLY | Operator-side concern | Not closeable. |

---

## Behavior matrix (post-closure verification)

| Scenario | Trainer view | Engine view | Identical? |
|---|---|---|---|
| Feature pack output (FOREACH_FEATURE) | Computed via Features_PackAll | Computed via Features_PackAll | YES (snapshot test v5.9.2a) |
| Feature registry hash | Stamp embeds FEATURE_REGISTRY_HASH | Engine refuses on mismatch | YES (v5.8.6) |
| Label registry hash | Stamp embeds LABEL_REGISTRY_HASH | Engine refuses on mismatch (4 sites) | **YES (Finding #1 CLOSED)** |
| Grid member count | Stamp re-parsed at AutoDetect | Cross-handle agreement validated | **YES (consume-side; emit-side deferred per validator's WARN log)** |
| Scaler sidecar | scaler_sha256 in stamp | Engine verifies SHA on load | YES (v5.9.3a) |
| Confidence freshness tau | Stamp embeds; runtime cfg compared | Tier 1 REFUSE in strict | **YES at boot AND post-hot-swap (Finding #3 CLOSED)** |
| XGBoost hyperparams | Stamp embeds 8 fields | WARN on mismatch | **YES at boot AND post-hot-swap (Finding #3 CLOSED)** |
| Ensemble blend mode | Cfg-only, NOT stamp-bound | Operator-set both sides | **NO (Finding #12 deferred to v5.11+)** |
| Multi-horizon strict mode | AutoDetect respects cfg.held_out_gate_strict | Both live + backtest | **YES (Finding #6 CLOSED)** |
| Multi-horizon LoadFromDir backtest path | Defaults strict=0 | Live correctly passes cfg | **NO — Finding #13 OPEN** |
| Inference cfg drift on ensemble handles | Drift block walks single + ensemble | Single helper, both paths | **YES (Finding #7 CLOSED)** |
| Hot swap when ensemble active | REFUSED with clear log | Operator restarts to swap | **YES (Finding #4 CLOSED)** |
| cfg_drift counters post-hot-swap | Updated by helper at swap | Same helper as boot | **YES (Finding #10 CLOSED)** |
| FPN_Sin/Cos/Sqrt/Exp determinism | Bytewise across calls | Bytewise across calls | YES (v5.10.0b tests) |
| FPN-end-to-end RegimeSignals | hour_sin/cos via FPN_Sin/Cos | Same path | YES (boundary-stable refactor) |
| FlowFeatures internal FPN | Bytewise across runs | Bytewise across runs | YES (v5.9.2 replay test extends) |
| RollingStats is_buyer_maker | Hardcoded 0 (slow-path) | Hardcoded 0 (slow-path) | YES (both broken — Finding #5 documented) |
| Bandit state (per-regime) | Persisted to bandit_state.json | Loaded at boot | YES (v5.10.0a.G.9) |
| Drift history (IC ring) | N/A (training doesn't IC) | Re-warms from empty on restart | DOCUMENT-ONLY (Finding #11 documented) |
| TUI strat_stats AUTO bin | Display reads zero-init | Same | **YES (Finding #8 CLOSED — UB warning gone)** |
| Drift state observability | drift_breached/kill/avg_ic/n_samples → TUI | Distinct ML Status panel branches | **YES (Finding #9 CLOSED)** |

**Summary:** 18 of 21 scenarios at full identity post-closure. 1
deferred to v5.11+ (Finding #12 ensemble cfg). 1 newly-confirmed open
(Finding #13 BacktestSharded LoadFromDir). 1 documented (Finding #5
is_buyer_maker — train-serve PARITY preserved, just degraded feature).

---

## Cross-cutting observations

### What worked

The 3-ship close-out structure (v5.10.1 / v5.10.2 / v5.10.3) cleanly
separated concerns:
- **v5.10.1** = production-caller plumb-through (CRITICAL findings #1, #2,
  #6 — all the "verifier exists, but no production wiring" gaps)
- **v5.10.2** = boundary-stable helper extraction (closes 4 findings
  #3, #4, #7, #10 with a single helper +1 guard, replacing ~200 LOC of
  inline blocks). This is a textbook example of the
  CLAUDE.local.md rule: "prefer boundary-stable refactors over wide
  cascades."
- **v5.10.3** = display + observability + documentation (Section J
  discipline + KNOWN_ISSUES).

The single helper `CoreModelZoo_ValidateAgainstCfg<F>` is well-designed:
- Stable signature (zoo + ezoo + cfg + core_id + 3 strict-mode flags + ctx)
- Templated, callable from boot AND hot-swap
- Iterates single + ensemble parallel arrays uniformly (closes #7 cleanly)
- Writes back counters into ctx (closes #10 cleanly)
- Per-handle log prefix distinguishable (`core 0 ensemble[2]` vs
  `core 0`)
- Returns -1 on Tier 1 REFUSE for caller-specific handling
  (boot = log + leave; hot swap = degrade with `model_load_failed=1`)

### What didn't quite land

**Finding #13 oversight.** v5.10.1.C closed `EnsembleModelZoo_AutoDetectFromDir`
(Finding #6) at `BacktestSharded.hpp:296`. But the `CoreModelZoo_LoadFromDir`
call at `BacktestSharded.hpp:263` (Finding #13's site) was missed —
same file, ~30 lines earlier, same fix shape. The commit message
explicitly lists only Finding #6.

This is a small adjacent gap class: the readiness check / commit author
was scoped to "the AutoDetect call" rather than "all stamp-verifying
load calls in BacktestSharded." Easy to fix in a v5.10.4 hotfix
(~30 min: 1 line change + comment + commit + tag).

### Recommendations

**Option A (recommended):** Ship v5.10.4 hotfix to close Finding #13
before v5.11.0 kickoff. Single-line change at
`Backtest/BacktestSharded.hpp:263`. Mirrors the v5.10.1.C diff shape.
~30 min including tests passing.

**Option B (also acceptable):** Absorb Finding #13 into v5.11.0
system-foundation kickoff. The bug is parity-preserved at the train-
serve identity level (the ml model load happens before training, so
training and serving ARE consistent within a single backtest run); the
violation is between live-engine strict semantics and backtest-engine
strict semantics. Acceptable for v5.11.0 if operator's documented
workflow is "always run live with the model, never serve from backtest
predictions."

---

## Suggested next-step ship sequence

If choosing Option A:
1. **v5.10.4 — Finding #13 hotfix (MEDIUM, single-line)**
   - Plumb 4 cfg args to `BacktestSharded.hpp:263` LoadFromDir
   - Effort: ~30 min
   - Then `/parity-check` GREEN at v5.10.4 close → open v5.11.0

If choosing Option B:
1. Open v5.11.0 system-foundation kickoff. Add Finding #13 to v5.11.X
   queue alongside Finding #14 build warning + Finding #5 plumb-through
   (group as "v5.10 close-out hangover" subship).

---

## NOT a bug (verified-safe items)

Same as the original audit; v5.10 close did not regress any of these:

- **FOREACH_FEATURE registry stable** — FEATURE_REGISTRY_HASH unchanged
  across v5.10. Existing protections intact.
- **FPN_Sin/Cos/Sqrt/Exp bytewise determinism** — tests at
  controller_test.cpp:12964-13176 still pass.
- **Bandit state load/save round-trip** — v5.10.0a.next.2 replay-
  determinism test at controller_test.cpp:12610 still passes.
- **MODEL_FORMAT_VERSION = 5** — preserved across v5.10. Surface G
  forward-compat pattern (`has_*=0` flag for legacy stamps) used
  correctly for label_registry_hash and grid_member_count.
- **Tick consumption parity (Section A)** — `Tick<F>` (live) and
  `HistoricalTick` (backtest) remain identical post-conversion at the
  single chokepoint. is_buyer_maker drop intentional and documented.
- **Snapshot tests (v5.9.2a) still binding** — body-level snapshots
  unchanged in v5.10.
- **Atomic stamp write** — `.tmp + rename` POSIX atomic preserved.
- **HMAC signature inclusive of all key=value lines** — canonical body
  ordering preserved.
- **NaN-free feature pack** — Two-layer guard at Features_PackAll
  preserved.
- **Threading + initialization** — All v5.10 fields zero-init'd
  correctly:
  - PerCoreSnap drift_breached / drift_kill_tripped / drift_n_samples /
    drift_avg_ic populated via ShardedSnapshot.hpp:480-488
  - g_shared.swap_model_path_requested cleared at boot (EngineSharded.hpp:~1222)
  - cfg_drift_tier1/2_count + strict_refused written by helper on
    BOTH boot AND hot-swap paths
- **Engine version handshake (v5.8.6 + v5.9.4)** — cross-major / cross-
  minor / poll_interval boot WARN paths intact.

---

## Verdict — YELLOW (with clear path to GREEN)

**Sprint B (v5.10) close-out re-audit — YELLOW.**

The expected verdict per the task spec was "GREEN with documented
YELLOW caveats for the deferred Findings #2 emit-side, #11, #12, #14."
Re-audit confirms 9 of 13 closures landed correctly and 3 deferrals
match the master plan (#11, #12, #14 + #17). The unexpected gap is
**Finding #13** — the BacktestSharded `CoreModelZoo_LoadFromDir`
call at line 263 was missed by v5.10.1.C, which only addressed the
AutoDetectFromDir call (Finding #6) at the same file. Both findings
shared the same fix shape; closing one without the other reads as a
small scoping miss in the commit author's task scope.

This is a **small, well-defined, single-line fix.** Severity remains
MEDIUM (not CRITICAL or HIGH); it doesn't block any v5.11 work
structurally. Two reasonable paths:

- **Option A (recommended):** v5.10.4 hotfix (~30 min) → re-run
  `/parity-check` for true GREEN-at-close → open v5.11.0.
- **Option B:** absorb Finding #13 into v5.11 close-out hangover
  subship; open v5.11.0 immediately.

Either path is operationally sound. The blockers cited in the original
audit's verdict (Findings #1 and #2 CRITICAL) are both **CLOSED**.

**Five-bullet executive summary:**
1. **9 of 13 findings closed correctly across v5.10.1 + v5.10.2 +
   v5.10.3.** Tests 1636/0; UB warning at TUIAnsi.hpp gone; helper
   extraction subsumes ~200 LOC of inline boot+hot-swap drift blocks.
2. **CRITICAL Findings #1 and #2 are CLOSED.** LABEL_REGISTRY_HASH
   plumbed through 4 production sites (2 emit + 2 consume); grid_member_count
   consume-side validator runs at AutoDetectFromDir with 3 unit tests.
3. **HIGH hot-swap parity hardening (Findings #3, #4, #7, #10) shipped
   correctly via single helper + REFUSE-when-ensemble-active guard.**
   Boundary-stable design (no struct cascade); helper called from both
   boot and hot-swap paths.
4. **NEW GAP: Finding #13 (BacktestSharded LoadFromDir args) was
   missed by v5.10.1.C.** Single-line ~30-min fix. Adjacent to
   Finding #6's fix at the same file; commit message scoped only to
   Finding #6, missed Finding #13's similar shape. Easy hotfix or
   v5.11.0 absorb.
5. **Deferred items (#11 drift_history persistence, #12 ensemble cfg
   stamp-binding, #14 build warning, #5 is_buyer_maker plumb-through)
   are correctly tracked.** All three are documented in
   `DOCS/KNOWN_ISSUES.md` (where applicable) or in source-code
   TODO comments with file:line references back to this audit's
   sibling original report.

**Final note** — v5.10's parity hardening was substantively well-
executed. The single missed gap (Finding #13) is the kind of close-
adjacent oversight that the next `/parity-check` pass catches
exactly. Decision 15 ("parity-tested-by-construction") survived the
full v5.10 epic; the helper-extraction pattern at v5.10.2 is a strong
template for v5.11+ refactors.

**Top recommendation:** ship v5.10.4 hotfix for Finding #13 (~30 min);
re-run `/parity-check` for GREEN; open v5.11.0.

---

End of report.
