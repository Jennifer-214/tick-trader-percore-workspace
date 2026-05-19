# /parity-check report — 2026-05-10 — v5.14.10 AMENDED plan re-audit

## Plan summary

- **Plan:** `plans/v5.14-foxml-port-and-maker/subplans/2026-05-10-v5.14.10-bayesian-thompson-bandit.md`
- **Date amended:** 2026-05-10 (post pre-coding audit gate + Caramel consult)
- **Sub-tag structure:** .0 (PerCoreSnap layout) → .A (Thompson math + FOREACH_BANDIT_ALGORITHM) → .B (engine wiring + stamp-bind) → .C (persistence + tt::json_io) → .D (display + FOREACH_CALIB_LOG_COL + cfg=2 telemetry) → .E (tests + propagation)
- **HEAD branch:** `feat/v5.14-foxml-port-and-maker` (latest commit `490618b` per git status)
- **Audit scope:** Re-audit focused on the 4 architectural decisions baked in; PARITY-013/014/015 closure verification; new parity surfaces introduced by amendment
- **Cross-check baseline:** prior /parity-check report at `parity-check-2026-05-10-v5.14.10-thompson-bandit.md` (pre-amendment, YELLOW with PARITY-013/014/015 OPEN)
- **Re-verification effort:** ~12 min code-walk against HEAD

---

## Verdict

**YELLOW** — proceed with 2 mechanical fixes before .0 coding starts.

The amendment substantially closes PARITY-013 (RESOLVED in .B), PARITY-014 (RESOLVED in .A), and PARITY-015 (RESOLVED in .D). All 4 architectural decisions (A/B/C/D) are well-spec'd and align with established v5.13.4.C / v5.14.1.E / v5.14.9.A precedents. The new sub-ship .0 (PerCoreSnap layout audit + unified bandit telemetry cluster) is sound and properly closes TECH_DEBT-011.

Two NEW findings introduced by amendment that need pre-coding fixes — both are line-ref / field-name staleness propagated from the original plan and the prior /parity-check report:

- 1× **MEDIUM** (NEW-1): plan still cites stale field name `ensemble_bandit_arm_probs[8]` (3 plan locations) — ACTUAL field name in PerCoreSnap is `ensemble_weights[5][8]` (DataStream/EngineTUI.hpp:1193). Operator implementing .0 / .D will look in wrong place.
- 1× **MEDIUM** (NEW-2): plan still cites publish path as `EngineSharded.hpp:646-694` (3 plan locations) — ACTUAL publish site is `CoreFrameworks/ShardedSnapshot.hpp:677-694` (function `TUI_CopySnapshotSharded` at line 42). EngineSharded.hpp:646-694 is the hardcoded-strategy-boot-guard block, completely unrelated. .D Step 2 writer-extension will land in the wrong file.

Both are ~2-min fixes (s/EngineSharded.hpp:646-694/ShardedSnapshot.hpp:677-694/g; s/ensemble_bandit_arm_probs/ensemble_weights/g) but block clean execution if not corrected before coding. NO CRITICAL findings.

NEW parity surfaces introduced (thompson_state.json wire format, FOREACH_CALIB_LOG_COL, PerCoreSnap cluster restructure, 4 stamp-bind drift tests) all check out with the established discipline patterns.

---

## Confirmation status — PARITY-013/014/015

### PARITY-013 — `cfg.bandit_algorithm` not stamp-bound — **RESOLVED in .B Step 9**

Amended plan Step 9 of v5.14.10.B specifies:

```
Stamp-bind 4 cfg fields via FOREACH_STAMP_BOUND_CFG (mirror cfg.exit_blender_mode at StampBoundCfgRegistry.hpp:137-138):

X(bandit_algorithm,         int,    "%d",    0,   cfg.bandit_algorithm,                          (cfg.bandit_algorithm != 0), DIRECT_FIELD)
X(thompson_mu_prior,        double, "%.17g", 0.0, FPN_ToDouble(cfg.thompson_mu_prior),           (cfg.bandit_algorithm != 0), DIRECT_FIELD)
X(thompson_precision_prior, double, "%.17g", 1.0, FPN_ToDouble(cfg.thompson_precision_prior),    (cfg.bandit_algorithm != 0), DIRECT_FIELD)
X(thompson_precision_obs,   double, "%.17g", 1.0, FPN_ToDouble(cfg.thompson_precision_obs),      (cfg.bandit_algorithm != 0), DIRECT_FIELD)
```

Verified against HEAD:
- `cfg.exit_blender_mode` at `ML_Headers/StampBoundCfgRegistry.hpp:137-138` — pattern matches exactly
- `cfg.exit_blender_mode` declared at `CoreFrameworks/ControllerConfig.hpp:1104` — analogous INT enum precedent
- Presence dispatch `(cfg.bandit_algorithm != 0)` correctly gates emit so legacy stamps (Exp3-only deployments before v5.14.10) won't have bandit_algorithm=0 emitted, preserving back-compat. Mirrors `(cfg.exit_blender_mode != 0)` shape.
- `STAMP_CFG_AUTOPOPULATE` auto-flow (CLAUDE.md item 21) covers all 4 entries automatically — no manual Train Model worker / BacktestEngine / BacktestPanels populator code required
- `thompson_rng_seed` correctly EXCLUDED from stamp binding (RNG state is runtime-only; affects within-run determinism, not cross-stamp model behavior — documented inline in plan amendment)
- 4 stamp-bind drift tests (Step 10) mirror the v5.14.9.C ladder cfg drift tests pattern

**Minor nit:** plan amendment Step 9 shows `default = 1.0` for thompson_precision_prior + thompson_precision_obs (correct cfg defaults), but the prior PARITY-013 entry in PARITY_ISSUES.md uses `0.0`. The `0.0` was intentional in PARITY_ISSUES (legacy-stamp absence default = neutral); the `1.0` in plan is the actual cfg default. This is the standard tension — Surface G default for forward-compat MUST be the value that means "neutral" / "as if unset", not the cfg default. Recommend: keep stamp default = `0.0` (neutral) for thompson_precision_prior + thompson_precision_obs to allow legacy stamps to load without fabricating a precision value. Document inline in Step 9.

**Status:** RESOLVED (with minor default-value discipline reminder above).

---

### PARITY-014 — Replay-determinism std::normal_distribution unsafe — **RESOLVED in .A Step 2 + Step 7**

Amended plan Step 2 of v5.14.10.A specifies:

> **own Box-Muller using raw `mt19937_64::operator()`** — NOT `std::normal_distribution` (libstdc++-implementation-defined; breaks cross-binary determinism). PARITY-014 fix.

And REUSE list (line 66):

> C++ standard `<random>` mt19937_64 (USE raw `operator()` 64-bit output; NOT `std::normal_distribution` which is libstdc++-implementation-defined and breaks cross-binary determinism)

Step 7 of .A specifies:

> **Step 7:** SHA-256-locked sample-trace snapshot test (replay-determinism contract; PARITY-014)
>   - Seed = 42; run Thompson_Sample 1000 iterations; SHA-256 the byte sequence of chosen_arm outputs; lock the hash
>   - Cross-binary cross-version reproducibility verified

Verified:
- `std::mt19937_64::operator()` raw 64-bit output IS standardized by C++11 §29.6.5.2 (per prior PARITY-014 entry); deterministic across libstdc++/libc++ versions
- Box-Muller cos transform uses only std::log + std::sqrt + std::cos / std::sin (IEEE-754 deterministic)
- `rng_state` field stored as uint64 + serialized as `%016lx` hex (locked in .C Step 3) → bytewise round-trip
- SHA-256-locked sample-trace snapshot test catches any future drift (compiler / libstdc++ minor / cross-vendor) immediately
- Step 1 struct field is `uint64_t rng_state` (matches plan Section "TRULY NEW" line 70: "own Box-Muller via raw mt19937_64::operator()")
- Plan Section "Latency analysis" line 326 correctly re-emphasizes: "Own Box-Muller using raw mt19937_64::operator() 64-bit output — NOT std::normal_distribution which is libstdc++-implementation-defined"
- Test landing in v5.14.10.E Step 1 lists the SHA-256 snapshot test among the ~15 new tests

**Status:** RESOLVED. Multiple-layer reinforcement (struct doc + impl doc + REUSE-list doc + Latency-analysis doc + 2 test references) reduces the probability that future contributors re-introduce std::normal_distribution.

---

### PARITY-015 — Display↔execution invariant breach — **RESOLVED in .D Step 1+2+6**

Amended plan Step 1 of v5.14.10.D specifies the FULL Bayesian dashboard in unified bandit telemetry cluster:

```cpp
// Bit-packed state byte (per CLAUDE.md item 20):
//   bit 0: thompson_bandit_active
//   bits 1-3: thompson_chosen_arm (0-7)
//   bits 4-7: reserved
uint8_t  thompson_state;                              // 1B (replaces 2 separate u8 fields)
// Display arrays (float matches GUI precision needs; bytes saved vs double):
float    thompson_mu_post[BANDIT_MAX_ARMS];           // 32B
float    thompson_precision_post[BANDIT_MAX_ARMS];    // 32B
uint32_t thompson_total_pulls[BANDIT_MAX_ARMS];       // 32B (matches BanditState.pulls width)
```

Step 6 of .D specifies the panel branch:

> **Step 6:** ML Status panel branch — render thompson_mu_post bars + precision_post error bars + total_pulls counts when `bandit_algorithm == 1` or `bandit_algorithm == 2` (FULL Bayesian dashboard view)

Verified against HEAD:
- Existing Exp3 telemetry surfaces in `PerCoreSnap` (DataStream/EngineTUI.hpp:1188-1196): `ensemble_active`, `ensemble_n_horizons`, `ensemble_horizon_ticks[8]`, `ensemble_last_predicted_regime`, `ensemble_last_predicted_horizon_idx`, `ensemble_weights[5][8]`, `ensemble_n_updates_per_regime[5]`, `ensemble_blend_mode[16]`, `ensemble_disabled_horizon_mask` — Thompson plan-amendment fields parallel these symmetrically
- Bit-packing `thompson_state` byte (1 active bit + 3 chosen-arm bits + 4 reserved) is consistent with CLAUDE.md item 20 (Portfolio bitmap precedent + `failure_flags` BIT_FLAG pattern at EngineTUI.hpp:1098)
- Float precision for display arrays acceptable (~7 sig digits sufficient for visualization; doubles only needed for math kernel which lives in ThompsonBanditState struct itself)
- `uint32_t thompson_total_pulls[BANDIT_MAX_ARMS]` (32B) matches `BanditState.pulls` (int per arm × 8 arms = 32B effective) — wire-format width discipline preserved
- Cluster sizing: `thompson_state(1B) + thompson_mu_post(32B) + thompson_precision_post(32B) + thompson_total_pulls(32B) = 97B` (rounded with 7B padding to 104B) → fits nicely with adjacent Exp3 cluster (~64B) within the unified 192B / 3-cache-line region from .0
- ML Status panel branch differentiating "Bandit Algorithm: Exp3 / Thompson / Both" + per-regime per-arm posterior table satisfies the operator-debugability surface called out in the original PARITY-015 finding
- Cfg=2 dual-mode telemetry per-fill calibration log gains 2 columns (thompson_chosen_arm + exp3_chosen_arm) — wired via FOREACH_CALIB_LOG_COL registry (.D Step 3-5)

**Status:** RESOLVED — full Bayesian dashboard (5 PerCoreSnap fields + ML Status panel branch + cfg=2 calib log columns) addresses operator visibility needs symmetrically with Exp3 path.

---

## NEW findings introduced by amendment

### MEDIUM

#### NEW-1 — Stale field name `ensemble_bandit_arm_probs` cited 3 times in amended plan; actual field is `ensemble_weights[5][8]`

**Severity rationale:** Operator implementing .0 / .D will grep the codebase for `ensemble_bandit_arm_probs` and find ZERO occurrences (verified via `rg -n "ensemble_bandit_arm_probs"` against full repo). Step 0 of .0 says "identify what's currently adjacent to `ensemble_bandit_arm_probs` in PerCoreSnap struct" — operator will be confused; field doesn't exist by that name.

**Sites in plan:**
- Plan line 61 (REUSE list): "`ensemble_bandit_arm_probs[8]` PerCoreSnap field (Exp3 telemetry surface)"
- Plan line 122 (Step 0 of .0): "identify what's currently adjacent to `ensemble_bandit_arm_probs`"
- Plan line 256 (Step 2 of .D): "Update slow-path snapshot publish path ... mirror lines 646-694 ensemble_bandit_arm_probs pattern"

**Truth (verified):**
- Field name in PerCoreSnap struct: `double ensemble_weights[5][8]` (DataStream/EngineTUI.hpp:1193)
- Companion field: `int ensemble_n_updates_per_regime[5]` (DataStream/EngineTUI.hpp:1194)
- Cluster summary (lines 1184-1196 in DataStream/EngineTUI.hpp):
  ```cpp
  uint8_t  ensemble_active;
  uint8_t  ensemble_n_horizons;
  int      ensemble_horizon_ticks[8];
  int      ensemble_last_predicted_regime;
  int      ensemble_last_predicted_horizon_idx;
  double   ensemble_weights[5][8];               // [regime][horizon]; 5 = NUM_REGIMES
  int      ensemble_n_updates_per_regime[5];     // total_steps per bandit
  char     ensemble_blend_mode[16];
  uint32_t ensemble_disabled_horizon_mask;
  ```

**Recommended fix:** plan-text edit (3 sites) — replace `ensemble_bandit_arm_probs[8]` with `ensemble_weights[5][8]` (with note that it's `[regime][horizon]` matrix, not a single 8-element array). 2 min plan amendment; 0 incremental code.

**Cross-ref:** No PARITY-NNN entry needed (plan-text staleness, no code bug). Just a plan-amendment fix.

---

#### NEW-2 — Stale file path `EngineSharded.hpp:646-694` cited 3 times in amended plan; actual publish site is `ShardedSnapshot.hpp:677-694`

**Severity rationale:** .D Step 2 says "Update slow-path snapshot publish path in `EngineSharded.hpp`" — operator will open the wrong file. EngineSharded.hpp:646-694 is the hardcoded-strategy-boot-guard block (`fprintf(stderr, "[sharded] ERROR: live mode (use_real_money=1) with %d hardcoded strategy core(s)..."`), completely unrelated to ensemble snapshot publish.

**Sites in plan:**
- Plan line 61 (REUSE list): "write site at `EngineSharded.hpp:646-694`"
- Plan line 256 (Step 2 of .D): "Update slow-path snapshot publish path in `EngineSharded.hpp` (mirror lines 646-694..."
- Plan line 213 (.B Step 4 implicit reference inherited from prior /parity-check report's stale claim — verify before coding)

**Truth (verified):**
- Publish function: `inline static void TUI_CopySnapshotSharded(...)` at `CoreFrameworks/ShardedSnapshot.hpp:42` (function start)
- Ensemble fields populated at `CoreFrameworks/ShardedSnapshot.hpp:654-694` (lines 654: `es.ensemble_active = 1`; 682: `es.ensemble_weights[r][h] = probs[h]`; 687: `es.ensemble_n_updates_per_regime[r] = ezoo->bandits[r].total_steps`)
- The struct definition lives in `DataStream/EngineTUI.hpp:980` (`struct PerCoreSnap`); the publish writer is in `ShardedSnapshot.hpp`. Plan Step 1 of .0 correctly cites `CoreFrameworks/ShardedSnapshot.hpp` for the struct walk — but actually that's wrong too; the struct lives in EngineTUI.hpp.

**This is a 2-file confusion that both prior plan + prior parity-check report have wrong:**
- `DataStream/EngineTUI.hpp:980-1199` — `PerCoreSnap` struct DEFINITION
- `CoreFrameworks/ShardedSnapshot.hpp:42-...` — `TUI_CopySnapshotSharded` PUBLISH function (writes into PerCoreSnap)
- `CoreFrameworks/EngineSharded.hpp:646-694` — UNRELATED hardcoded-strategy-boot-guard

**Recommended fix:** plan-text edit:
1. Plan line 61: replace `EngineSharded.hpp:646-694` → `CoreFrameworks/ShardedSnapshot.hpp:677-694` (or 654-694 for full ensemble cluster)
2. Plan line 122 (Step 0 of .0): walk `DataStream/EngineTUI.hpp:980-1199` for struct field inventory
3. Plan line 123 (Step 1 of .0): replace `CoreFrameworks/ShardedSnapshot.hpp` (struct definition is NOT here) with `DataStream/EngineTUI.hpp:980-1199`
4. Plan line 256 (Step 2 of .D): replace `EngineSharded.hpp` → `CoreFrameworks/ShardedSnapshot.hpp` for publish writer extension; mirror lines `654-694` (or `677-694` for the per-regime block specifically)

5 min plan amendment; 0 incremental code.

**Cross-ref:** No PARITY-NNN entry needed (plan-text staleness). But: this is the SECOND time this exact mis-citation has propagated (it was wrong in the prior /parity-check report, copied verbatim into PARITY-015 entry, then carried into the amended plan). Recommend updating PARITY_ISSUES.md PARITY-015 entry to correct the file path so future audits don't re-propagate.

---

## Cross-cutting concerns — NEW parity surfaces introduced by amendment

### XC-A — thompson_state.json wire format (Layer 1-6 byte preservation)

Amended plan .C Step 3 specifies wire format with full Layer-by-Layer compliance vs `wire-format-byte-preservation-discipline.md`:

| Layer | Discipline | Plan compliance |
|---|---|---|
| **Layer 1** — Pre-coding gate via /parity-check Section E | Registry order matches emit order | N/A — thompson_state.json is sidecar JSON, not stamp body. No FOREACH registry; manual emit per `Bandit_SaveJSON` precedent. |
| **Layer 2** — Locale pinning at emit construction | `uselocale(newlocale(LC_NUMERIC_MASK, "C", 0))` at function entry; restore on return | **YES** — explicitly specified in Step 3. Also addresses TECH_DEBT-027 opportunistically in Step 4 (Bandit_SaveJSON gets same fix). |
| **Layer 3** — Registry tuple's `fmt` column | `%.17g` for doubles; `%016lx` hex for opaque uint64 state | **YES** — Step 3 explicit on per-field fmt strings. Matches `BANDIT_STATE_FORMAT_VERSION` precedent at BanditLearning.hpp:404 (`%.17g`). |
| **Layer 4** — Post-coding round-trip HMAC test | thompson_state.json is NOT HMAC-signed (sidecar; bundle-id check via SHA equivalence) | N/A — sidecar uses model_bundle_sha256 binding (Bandit_LoadJSON pattern). |
| **Layer 5** — Canonical body snapshot test (locked hash) | Persistence round-trip test: save → load → bytewise identical posterior + RNG state | **YES** — Step 7 of .C ("Persistence round-trip tests (save → load → bytewise identical posterior + RNG state across runs)"). |
| **Layer 6** — Surface G discipline (back-compat for legacy stamps) | format_version=1 + missing thompson_state.json → uniform priors stay (Surface G forward-compat-by-absence) | **YES** — explicit in plan line 87: "thompson_state.json: forward-compat-by-absence (Layer 6 wire-format-byte-preservation; same shape as v5.13.4.C exit_bandit_state.json)". Mirror of `EnsembleModelZoo_LoadExitBanditState` at CoreModelZoo.hpp:1942 (returns 0 cleanly when file missing). |

**Status:** GREEN — wire format properly disciplined.

**Atomic-write reminder:** Plan Step 4 (.C) inherits `Bandit_SaveJSON` pattern at `BanditLearning.hpp:376` (`tmp_path = path + ".tmp"; fopen + fprintf + fclose; rename(tmp_path, path)`). Atomic via `.tmp + rename`. Plan amendment Step 4 should call this out explicitly so reviewer doesn't accept non-atomic implementation.

### XC-B — PerCoreSnap layout reorganization (.0 cluster restructure)

Amended plan .0 reorders existing PerCoreSnap fields into unified clusters per concern (bandit / ridge / confidence / ladder / regime / etc.) with `alignas(64)` per cluster + arrays-first reorder.

**Risk:** any existing snapshot field offset assumptions in tests / replay tools / display panels could break.

**Verification (against HEAD):**

```bash
$ rg -n "offsetof\s*\(\s*PerCoreSnap" --include="*.cpp" --include="*.hpp"
[no results]
```

No `offsetof(PerCoreSnap, ...)` static asserts exist in the current codebase. Field access is by name (`snap->per_core[i].ensemble_weights[r][h]`), not by offset. **Safe to reorder fields.**

Plan .0 Step 5 explicitly adds offset stability tests (`static_assert(offsetof(PerCoreSnap, X) == EXPECTED)`) AFTER restructure — locks the new layout going forward. Sound discipline.

**Status:** GREEN — no existing offset assumptions to break; .0 establishes them.

**Reminder for .0 implementer:** the snapshot is double-buffered via `TUISnapshot` (DataStream/EngineTUI.hpp:1198 `PerCoreSnap per_core[16];`). Reader threads (GUI / TUI) memcpy the snapshot under a seqlock; field names are stable but byte offsets shift. Verify ALL reader sites compile after the reorder (Step 3 of .0 calls this out: "verify TUISnapshot publish path still aligns + all reader sites compile").

### XC-C — FOREACH_CALIB_LOG_COL registry — additive-only for legacy reads?

Amended plan .D Step 3 introduces FOREACH_CALIB_LOG_COL registry with 5 columns (closes TECH_DEBT-010):

```cpp
X(exp3_chosen_arm,     int,    /*expr*/, "Exp3 argmax weight arm")
X(thompson_chosen_arm, int,    /*expr*/, "Thompson posterior sample arm")
X(regime_id_at_pick,   int,    /*expr*/, "Regime ID at decision time")
X(exp3_weights_csv,    string, /*expr*/, "Comma-sep Exp3 weights")
X(thompson_mu_csv,     string, /*expr*/, "Comma-sep Thompson posterior means")
```

**Risk:** if cfg=0 (Exp3-only default) operator's per-fill calibration log changes row format, downstream tools (offline analysis scripts, paper-test tooling) break.

**Plan compliance:** Step 5 says "Activate cfg=2 telemetry — log Exp3 weights + Thompson choice per fill via the new registry-driven writer". This implies the calib log writer ONLY fires when cfg=2 is active — for cfg=0 / cfg=1 deployments, no row format change. Should be explicitly called out in plan Step 5 with: "calibration log row format is UNCHANGED for cfg=0 (Exp3-only); new columns appear ONLY when cfg=2 is set". Otherwise an operator running cfg=1 (Thompson-only) might see a partial row with thompson_chosen_arm but no exp3_chosen_arm and panic.

**Recommended fix:** plan amendment Step 5 of .D — add 1 sentence: "FOREACH_CALIB_LOG_COL writer activated ONLY when `cfg.bandit_algorithm == 2` (BANDIT_BOTH_ACTIVE gate predicate from .B Step 8). cfg=0 + cfg=1 deployments retain pre-v5.14.10 calib log row format."

**Status:** YELLOW — mostly OK but the "additive-only for legacy reads" guarantee should be explicit in the plan.

### XC-D — 4 stamp-bind drift tests — does presence dispatch `(cfg.bandit_algorithm != 0)` correctly gate emit?

Amended plan .B Step 9 + Step 10 specify 4 stamp-bind drift tests per X-macro entry. Presence dispatch `(cfg.bandit_algorithm != 0)` correctly gates emit so that:

- Legacy stamps (Exp3-only) emit ZERO bandit_algorithm-related fields → has_*=0 across the board → PARITY-013 stamp-binding silently disabled for legacy installs (fine; they can't drift if Exp3 is the only path)
- New stamps (cfg.bandit_algorithm=1 or 2) emit 4 fields → drift detection armed
- Cross-major engine bumps don't break: stamp body extension via `has_*` flag is additive (Surface G discipline)

Verified pattern matches:
- `cfg.exit_blender_mode` at StampBoundCfgRegistry.hpp:137-138 (`(cfg.exit_blender_mode != 0), DIRECT_FIELD`) — same shape; same default = 0 means "not enabled" → not emitted
- `cfg.ridge_within_horizon` + `cfg.ridge_across_horizons` at lines 102-105 (`(cfg.ridge_within_horizon || cfg.ridge_across_horizons), DIRECT_FIELD`) — same group-emit-when-any pattern (closed PARITY-004)

**Status:** GREEN — presence dispatch correctly gates emit. Drift tests should mirror v5.14.9.C ladder cfg drift tests pattern.

### XC-E — Cross-version load compat for thompson_state.json

Amended plan line 87 ("thompson_state.json: forward-compat-by-absence (Layer 6 wire-format-byte-preservation; same shape as v5.13.4.C exit_bandit_state.json)") + line 232 (FOREACH_ENSEMBLE_POST_LOAD `load_thompson_state` registry entry).

Verified pattern (HEAD `EnsembleModelZoo_LoadExitBanditState` at CoreModelZoo.hpp:1942):

```cpp
inline int EnsembleModelZoo_LoadExitBanditState(...) {
    if (!ezoo || !ezoo->initialized_exit_bandits) return 0;
    if (ezoo->exit_predictor_count < 2) return 0;
    ...
    int loaded = Bandit_LoadJSON(ezoo->exit_bandits, NUM_REGIMES, path,
                                   expected_id, ezoo->exit_predictor_count);
    if (loaded) {
        fprintf(stderr, "[ensemble] loaded exit_bandit state from %s\n", path);
    } else if (access(path, F_OK) == 0) {
        fprintf(stderr, "[ensemble] exit_bandit_state.json present but "
                        "rejected (format/sha/n_arms mismatch); "
                        "starting uniform\n");
    }
    return loaded;
}
```

Returns 0 cleanly when file missing OR format/sha/n_arms mismatch. Bandit state stays at initialization defaults (uniform priors). For Thompson:

- Legacy install (no thompson_state.json): `_LoadThompsonState` returns 0 → priors stay at `cfg.thompson_mu_prior` / `cfg.thompson_precision_prior` defaults → safe cold-start
- format_version=2 future: `Bandit_LoadJSON` rejects (returns 0) per BanditLearning.hpp:535 → priors stay at defaults → safe cross-version downgrade
- model_bundle_sha mismatch: rejected (returns 0); priors reset → prevents stale weights from prior bundle silently re-applying

**Status:** GREEN — cross-version load compat properly handled via existing precedent.

---

## Behavior matrix (verify train and serve agree under each cfg)

| Scenario | Trainer view | Engine view | Identical? |
|---|---|---|---|
| Default cfg (cfg.bandit_algorithm=0; Exp3 path) | Bandit_GetProbabilities → weights_buf | bandit_algo_fns[0](ezoo, ...) → BanditAlgo_Exp3_Apply → weights_buf | YES (Exp3 default = bytewise-unchanged from pre-v5.14.10; .E Step 1 verifies via cfg=0 bytewise-identical test) |
| cfg.bandit_algorithm=1 (Thompson) | N/A (no training-time Thompson; runtime-only state) | bandit_algo_fns[1](ezoo, ...) → BanditAlgo_Thompson_Apply → one-hot weights_buf at chosen_arm | N/A — runtime-only state; no train-side equivalent |
| cfg.bandit_algorithm=2 (Both) | Same as Exp3 (training does Exp3 alone) | Exp3 weights drive action; Thompson chosen_arm logged in calib log | NO behavioral difference; per-fill telemetry only — acceptable |
| Restart with thompson_state.json present (compatible bundle SHA) | N/A | `_LoadThompsonState` overlays posteriors; Exp3 path unchanged | YES (Exp3) / N/A (Thompson runtime-only) |
| Restart with thompson_state.json missing | N/A | Uniform priors stay (per `_LoadExitBanditState` precedent); no boot REFUSE | YES (legacy stamp behavior preserved) |
| Restart with thompson_state.json present + INCOMPATIBLE bundle SHA | N/A | `_LoadThompsonState` returns 0; priors reset → uniform; stderr WARN | YES (no stale state silently re-applies) |
| Cfg drift: trained cfg.bandit_algorithm=0; deployed cfg=1 | Stamp body has bandit_algorithm=0 (or absent if pre-v5.14.10 stamp) | Live cfg.bandit_algorithm=1 → drift detected via FOREACH_STAMP_BOUND_CFG check (.B Step 9) | YES with .B Step 9 (PARITY-013 closed) |
| Cfg drift: trained cfg=1; deployed cfg=0 (operator disables Thompson) | Stamp body has bandit_algorithm=1 + 3 hyperparams | Live cfg.bandit_algorithm=0 → drift detected; soft-WARN per existing 3-tier strict-mode | YES with .B Step 9 |
| Replay determinism (same seed + same reward sequence) | N/A (no training-time Thompson) | mt19937_64 raw output → Box-Muller → identical sample sequence | YES (PARITY-014 closed via own Box-Muller + SHA-256-locked sample-trace test) |
| Cross-binary replay (libstdc++-13 dev → libstdc++-12 prod) | N/A | mt19937_64 raw output is C++11-standardized; identical across stdlib versions | YES with own Box-Muller (PARITY-014 closed) |

All rows satisfy parity discipline post-amendment. The "Cfg drift" rows specifically rely on .B Step 9 stamp-binding (PARITY-013 fix). The "Replay determinism" rows rely on .A Step 2 own-Box-Muller (PARITY-014 fix).

---

## Mechanical fix recommendations (apply before .0 coding)

| # | Fix | Plan line(s) | Effort |
|---|---|---|---|
| 1 | Replace `ensemble_bandit_arm_probs[8]` → `ensemble_weights[5][8]` (3 sites) | 61, 122, 256 | 2 min |
| 2 | Replace `EngineSharded.hpp:646-694` → `CoreFrameworks/ShardedSnapshot.hpp:677-694` (3 sites) | 61, 256, possibly 213 | 2 min |
| 3 | Plan line 122 (.0 Step 0): clarify struct lives in `DataStream/EngineTUI.hpp:980-1199`, NOT ShardedSnapshot.hpp | 122-123 | 1 min |
| 4 | Plan line 123 (.0 Step 1): walk `DataStream/EngineTUI.hpp:980-1199` for struct field inventory (publish writer is in ShardedSnapshot.hpp) | 123 | 1 min |
| 5 | Plan .D Step 5: explicitly state "calibration log row format UNCHANGED for cfg=0 + cfg=1; new columns ONLY active when cfg=2" | 268 | 1 min |
| 6 | Plan .B Step 9: stamp-default discipline reminder — keep `default = 0.0` for thompson_precision_prior + thompson_precision_obs (neutral / "as if unset") even though cfg default is 1.0 | 207-208 | 1 min |
| 7 | Update PARITY_ISSUES.md PARITY-015 entry to correct the file path (was: `CoreFrameworks/EngineSharded.hpp:646-694`; should be: `CoreFrameworks/ShardedSnapshot.hpp:677-694`) | n/a | 2 min |

Total: ~10 min plan-text amendment, no code impact.

---

## Suggested ship sequence (post-amendment confirmed)

Plan's 6-sub-tag structure (.0 → .A → .B → .C → .D → .E) is sound and well-sequenced. Re-confirmed:

| Sub-tag | Scope | LOC est | PARITY closure |
|---|---|---|---|
| v5.14.10.0 | PerCoreSnap layout audit + unified bandit telemetry cluster + per-snapshot-cluster-layout-pattern.md DESIGN_SPECS | ~80-150 | TECH_DEBT-011 substantial close |
| v5.14.10.A | FOREACH_BANDIT_ALGORITHM registry + Thompson math kernel + own Box-Muller + SHA-256 sample-trace test | ~400-500 | PARITY-014 closed |
| v5.14.10.B | Engine wiring + 5 cfg fields + 4 stamp-binds + 2 slow-path-gate predicates + hysteresis-skip | ~150 | PARITY-013 closed |
| v5.14.10.C | thompson_state.json persistence + tt::json_io extraction + FOREACH_ENSEMBLE_POST_LOAD extension + locale pinning + TECH_DEBT-027 opportunistic | ~150 | (sidecar wire format + Class 18 prevention) |
| v5.14.10.D | FULL Bayesian dashboard (5 PerCoreSnap fields) + ML Status panel branch + FOREACH_CALIB_LOG_COL registry + cfg=2 telemetry | ~250 | PARITY-015 closed; TECH_DEBT-010 closed |
| v5.14.10.E | Tests (~+15) + propagation + Version.hpp bumps + workspace sync | ~200 | (sprint-close discipline) |
| v5.14.10 | umbrella tag | — | — |

Total: ~1230-1400 LOC over 6 sub-tags + umbrella. Closes 2 TECH_DEBT items + 3 PARITY items + prevents Class 18 mirror recurrence.

---

## NOT a bug (verified-safe items)

- **FOREACH_STAMP_BOUND_CFG presence dispatch** — `(cfg.bandit_algorithm != 0)` correctly gates emit; legacy stamps omit fields cleanly; new stamps emit 4 fields; drift detected on serving-time cfg mismatch. Pattern verified against `cfg.exit_blender_mode` and `cfg.ridge_within_horizon` precedents.
- **STAMP_CFG_AUTOPOPULATE auto-flow** — adding 4 X-rows to FOREACH_STAMP_BOUND_CFG covers ALL production-caller construction sites (Train Model worker, BacktestEngine, BacktestPanels) automatically per CLAUDE.md item 21. v5.9.5b production-caller class structurally extinguished — Thompson stamp-binding cannot have the silent-disable bug that PARITY-002/003/004/005/008 had.
- **Cross-binary determinism** — `std::mt19937_64::operator()` raw 64-bit output IS standardized by C++11 §29.6.5.2; deterministic across libstdc++ minor versions and across libc++ implementations. PARITY-014 fix (own Box-Muller) is sufficient.
- **Bit-packed thompson_state byte** — single u8 with bit 0 (active) + bits 1-3 (chosen_arm 0-7) + bits 4-7 reserved. Mirrors `failure_flags` BIT_FLAG pattern at EngineTUI.hpp:1098. Per CLAUDE.md item 20.
- **Forward-compat-by-absence for thompson_state.json** — missing file → uniform priors stay (no boot REFUSE); incompatible bundle SHA → reset to uniform with WARN. Mirrors v5.13.4.C `EnsembleModelZoo_LoadExitBanditState` exactly.
- **Cache-line layout** — unified bandit telemetry cluster occupies 3 cache lines (192 bytes). Writer-side invalidations: 1-3 lines/cycle; reader-side fetches: 1-3 lines/frame. Negligible vs existing per-cycle write traffic.
- **Plan line refs (most)** — verified correct against HEAD: `cfg.exit_blender_mode` at StampBoundCfgRegistry.hpp:137-138 ✓; `bandits[NUM_REGIMES]` at CoreModelZoo.hpp:833 ✓; `exit_bandits[NUM_REGIMES]` at 845 ✓; `ridge_state` at 862 ✓; `exit_ridge_state` at 868 ✓; `_InitBandits` at 1238 ✓; `_InitExitBandits` at 1286 ✓; `_SaveBanditState` at 1865 ✓; `_SaveExitBanditState` at 1887 ✓; `_LoadBanditState` at 1911 ✓; `_LoadExitBanditState` at 1942 ✓; `Bandit_JsonFindKey` at BanditLearning.hpp:440 ✓; `_JsonParseDoubleArray` at 455 ✓; `_JsonParseIntArray` at 473 ✓; `FOREACH_ENSEMBLE_POST_LOAD` at CoreModelZoo.hpp:2088-2104 ✓; `EnsembleModelZoo_IsReadyForInference` at 2137-2151 ✓; `Bandit_GetProbabilities` calls at StrategyParameters.hpp:899/900/912 (plan cites 899/912 — also correct, just understates by one) ✓; `BANDIT_MAX_ARMS = 8` at BanditLearning.hpp:60 ✓.
- **Plan claim "Hot path UNTOUCHED"** — confirmed: ML_BuildParameters is slow-path; Thompson dispatch lives in slow-path rebuild context; never in BG_Evaluate / SG_Evaluate. p99 ≤500ns hot-path target unaffected.
- **Plan claim "default 0 preserves Exp3 path bytewise"** — confirmed via the FOREACH_BANDIT_ALGORITHM dispatch table; cfg=0 → `bandit_algo_fns[0]` → `BanditAlgo_Exp3_Apply` → calls existing `Bandit_GetProbabilities` directly. No behavior change for default deployments.

---

## PARITY_ISSUES.md status post-audit

Prior-audit auto-written entries (PARITY-013/014/015) are already in `DOCS/PARITY_ISSUES.md`. This re-audit confirms all 3 are RESOLVED in the amended plan (target ships .B / .A / .D respectively). NO new PARITY-NNN entries required from this audit.

Recommended PARITY-015 entry update (see Mechanical fix #7 above) to correct the file path citation; can be done as part of the mechanical-fixes commit.

When v5.14.10 closes (after .E ships), run `/parity-check` once more to flip PARITY-013/014/015 to FIXED status (per ledger discipline: FIXED → CLOSED transition needs ONE clean parity-check run).

---

## Map-update suggestions (post-audit)

- **DOCS/PARITY_ISSUES.md** — update PARITY-015 file path citation (mechanical fix #7); flip PARITY-013/014/015 to FIXED post-v5.14.10 close
- **DOCS/PARITY_LIFECYCLE.md** — bandit-state JSON files now a documented surface triplet: bandit_state.json + exit_bandit_state.json + thompson_state.json. After v5.14.10.C ships, append paragraph documenting the triplet and the shared `_LoadXxxBanditState` pattern.
- **DOCS/CLAUDE_ML_INVARIANTS.md** — consider a sentence about "non-deterministic <random> distributions are forbidden in train-serve paths; raw mt19937_64 output + own-the-math is the discipline" once .A ships and PARITY-014 closes.
- **DESIGN_SPECS/data-disciplines/per-snapshot-cluster-layout-pattern.md** — NEW; ships with v5.14.10.0 per plan
- **DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md** — NEW; ships with v5.14.10.D per plan
- **CLAUDE.md** — consider promoting "deterministic <random> usage" to a CLAUDE.md item once the Thompson math kernel + SHA-256 snapshot test land (per going-forward rule "codify design principles in CLAUDE.md as patterns mature" — v5.14.8 codification precedent for items 19-23).

---

## Summary for /parity-check verdict

**YELLOW** — proceed with 7 mechanical fixes (~10 min total) before .0 coding starts. PARITY-013/014/015 are RESOLVED in the amended plan (target ships .B / .A / .D). All 4 architectural decisions (A/B/C/D) properly aligned with established patterns. NEW parity surfaces (thompson_state.json, PerCoreSnap cluster restructure, FOREACH_CALIB_LOG_COL, 4 stamp-bind drift tests) all check out with discipline. No CRITICAL findings. The 2 NEW MEDIUM findings (NEW-1 stale field name, NEW-2 stale file path) are propagation of staleness from prior /parity-check report — fixable in plan text without affecting code design.

Once mechanical fixes #1-7 land, plan is GREEN for coding kickoff at .0.
