# /merge-scan — v5.15 sprint reuse-merge opportunities

**Date:** 2026-05-12
**Scope:** v5.15 sprint master + 5 sub-plans (~1850 LOC); cross-plan + cross-codebase scan
**Skill:** `/merge-scan` per `~/code/tick-trader-percore-workspace/claude-skills/merge-scan/SKILL.md`

---

## Verdict: **YELLOW** — 3 HIGH findings worth folding in BEFORE coding; 2 MEDIUM consolidations; 4 LOW/informational

**Why YELLOW (not RED):** none of the merges are coding-blocking. The plans are
internally consistent + leverage existing patterns (FOREACH_FAILURE_MODE,
BITMAP_*, STAMP_HAS, STAMP_CFG_AUTOPOPULATE) cleanly. Most HIGH findings are
"the plans propose a NEW thing; existing infrastructure already does this in
the same shape" — fold the existing into the plan + remove duplication
upfront vs. shipping then refactoring.

**Three HIGH findings (consolidate BEFORE coding):**

1. **v5.15.1 drift detection chokepoint already EXISTS at TryLoadRole post-verify_model_stamp** (X-macro drift comparison via FOREACH_STAMP_BOUND_CFG). Plan proposes adding chokepoint as if new. Plan should EXTEND the existing X-macro loop, not add parallel detection logic.
2. **v5.15.4 HotSwapSnapshot infrastructure should reuse the existing double-buffered atomic-publish pattern from `DataStream/BinanceDepth.hpp`** (BookSnapshot snapshots[2] + active_idx atomic). Plan invents new struct ground-up; same shape exists ready to template-extract.
3. **v5.15.4 ControllerConfigKeyExplicit bitmap should reuse `core_strategies_explicit_set` precedent** (uint16_t bitmap at ControllerConfig.hpp:917). Plan invents new struct of bool fields; existing pattern says bitmap.

---

## Cross-plan merge candidates (within v5.15)

### HIGH-1 — v5.15.1 drift chokepoint duplicates an existing X-macro loop

**Plan claim** (v5.15.1.A Step 2): "Each new bit gets set at the **single
chokepoint** where the comparison happens... Chokepoint for v5.15.1 drift
detection: `CoreModelZoo_TryLoadRole` (immediately after `verify_model_stamp`
returns success)... For CFG_BINDING_DRIFT: iterate FOREACH_STAMP_BOUND_CFG
and compare each stamp-bound field's stamp_value vs runtime cfg.* value;
OR-set the bit if any mismatch."

**Codebase reality:** this loop **already exists at `ML_Headers/CoreModelZoo.hpp:206-225`**:
```cpp
if (cfg_ptr && sr.valid > 0) {
    const ControllerConfig<F>& cfg = *cfg_ptr;
    #define X(name, type, fmt, default_val, get_cfg_expr, emit_when, emit_source) \
        if (sr.has_##name) {                                                \
            type cfg_val = (type)(get_cfg_expr);                            \
            if (sr.name != cfg_val) {                                       \
                sr.inference_cfg_drift_count++;                             \
                if (sr.reason[0] == '\0') {                                 \
                    snprintf(sr.reason, sizeof(sr.reason),                  \
                        "%s drift: stamp=" fmt " cfg=" fmt,                 \
                        #name, sr.name, cfg_val);                           \
                }                                                            \
            }                                                                \
        }
    FOREACH_STAMP_BOUND_CFG(X)
    #undef X
    if (sr.inference_cfg_drift_count > 0) {
        sr.valid = 0;  // treat drift as verification failure
    }
}
```

This X-macro loop ALREADY:
- Walks every FOREACH_STAMP_BOUND_CFG entry
- Compares stamp_value vs cfg value
- Increments `sr.inference_cfg_drift_count` per mismatch
- Captures first-drift `sr.reason`
- Sets `sr.valid = 0` if any drift

**Proposed merge:** v5.15.1 should NOT add a parallel `if
(handle.stamp_build_flags_hash != BUILD_FLAGS_HASH_RUNTIME) FAILURE_SET(...)`
chain. Instead, extend the existing X-macro body to ALSO `FAILURE_SET` on
the per-core failure_flags. One line addition inside the existing macro:

```cpp
#define X(name, type, fmt, default_val, get_cfg_expr, emit_when, emit_source) \
    if (sr.has_##name) { \
        type cfg_val = (type)(get_cfg_expr); \
        if (sr.name != cfg_val) { \
            sr.inference_cfg_drift_count++; \
            FAILURE_SET(*per_core_snap, cfg_binding_drift);  // NEW v5.15.1 \
            ... \
        } \
    }
```

For the non-cfg drift bits (FEATURE_HASH_DRIFT / LABEL_HASH_DRIFT /
BUILD_FLAGS_DRIFT / SCALER_DRIFT): `verify_model_stamp` already checks
`expected_feature_registry_hash` / `expected_label_registry_hash` and
populates failure modes via `sr.valid = 0`. The drift bits should be set
in the same scope where these checks ALREADY happen
(`ML_Headers/ModelInference.hpp:1295+` parser body), not at the TryLoadRole
post-verify wrapper. Saves a duplicate compare round.

**Impact:** prevents v5.15.1 from baking in a duplicated drift-detection
path; reduces v5.15.1.A from ~120 LOC to ~60 LOC; CFG_BINDING_DRIFT becomes
a 1-line addition inside an existing loop.

**Severity:** HIGH (prevents two parallel drift detectors in the codebase).

---

### HIGH-2 — v5.15.4 HotSwapSnapshot should reuse BinanceDepth's double-buffer pattern

**Plan claim** (v5.15.4.B Step 1): "NEW struct `HotSwapSnapshot { EnsembleModelZoo<F>* prev_ezoo; int prev_n_models; uint64_t snapshot_seq; }`... `alignas(64)` (cross-thread access from slow-path + boot gate). snapshot_seq uses `__atomic_store(_, _, __ATOMIC_RELEASE)` on publish + acquire-load on read; standard release-acquire sync"

**Codebase reality:** `DataStream/BinanceDepth.hpp:80-89` ALREADY implements the
double-buffered atomic-publish-or-rollback pattern:
```cpp
template <unsigned F> struct DepthSharedState {
    BookSnapshot<F> snapshots[2];
    int active_idx;              // atomic: index the engine reads
    int quit_requested;
    ...
};
```
Publish (line 307-317):
```cpp
int back = 1 - __atomic_load_n(&shared->active_idx, __ATOMIC_ACQUIRE);
shared->snapshots[back] = shared->snapshots[shared->active_idx];
...  // populate back
__atomic_store_n(&shared->active_idx, back, __ATOMIC_RELEASE);
```

This is a CANONICAL release-acquire double-buffer with seqlock-style publish.
Same shape v5.15.4 needs (two states: pre-swap, post-swap; atomic flip on
validate success; rollback by NOT flipping).

**Proposed merge:** template-extract a generic `DoubleBufferedAtomic<T>` to
`MemHeaders/DoubleBuffered.hpp`, applied at BOTH:
- `DataStream/BinanceDepth.hpp` (existing — refactor to use the template)
- `CoreFrameworks/HotSwap.hpp` (new v5.15.4 site)

Capture / Revert / Discard become methods on the same template. Saves
~50-80 LOC of v5.15.4 NEW code; eliminates a parallel cross-thread sync
implementation that future contributors must reason about separately.

Alternative (lighter): v5.15.4 references BinanceDepth as canonical
precedent in its HotSwap.hpp header comment + uses identical ATOMIC_RELEASE
/ ATOMIC_ACQUIRE semantics (already planned). Even without extraction,
the consistency win matters for future audit.

**Severity:** HIGH (consistency boundary for cross-thread sync patterns;
the codebase has 1 canonical pattern, the plan invents a second).

---

### HIGH-3 — v5.15.4 ControllerConfigKeyExplicit should reuse existing bitmap pattern

**Plan claim** (v5.15.4.A Step 0): "the post-parse normalize pass must
distinguish 'operator explicitly set model_verify_strict=0' (honor) from
'operator didn't set it' (apply strict default)... If no tracking
infrastructure exists, .A includes adding minimal tracking: a `ParserState`
struct with a bitmap (or small set) marking each key seen."

**Codebase reality:** an explicit-set bitmap pattern ALREADY exists for
strategy keys at `CoreFrameworks/ControllerConfig.hpp:917`:
```cpp
uint16_t core_strategies_explicit_set;     // v5.9.0c
```
Parsed at `:2499`:
```cpp
cfg.core_strategies_explicit_set |= (uint16_t)(1u << core_idx);
```
Read at `:2700`:
```cpp
if (cfg.num_execution_cores > 0 && cfg.core_strategies_explicit_set == 0) {
    // hardcoded fallback warning
}
```

**Proposed merge:** v5.15.4 should add `cfg.cfg_keys_explicit_set` as a
**uint64_t bitmap** with named MASK constants (`MASK_CFG_KEY_TRADING_MODE`,
`MASK_CFG_KEY_MODEL_VERIFY_STRICT`, `MASK_CFG_KEY_RECONCILE_MODE`, ...) —
NOT a struct of `has_*` bool fields. Same shape as the existing
`core_strategies_explicit_set`, same shape as `STAMP_HAS` / `FAILURE_*` /
`STATE_FLAG_*` (the BITMAP_* API established in CLAUDE.md item 20).

Parser sets `cfg.cfg_keys_explicit_set |= MASK_CFG_KEY_TRADING_MODE;` at
the `if (strcmp(key, "trading_mode") == 0)` branch. Normalize pass reads
`BITMAP_IS_SET(cfg.cfg_keys_explicit_set, MASK_CFG_KEY_MODEL_VERIFY_STRICT)`.
Per CLAUDE.md item 20 (BITMAP_* API): explicit consistency with the
established pattern wins.

**Caveat:** v5.15.4 only needs 2 flags initially (`model_verify_strict` +
`reconcile_mode`). CLAUDE.md item 20 says "When 3+ boolean flags coexist
in a single struct, bit-pack." With 2 flags today + obvious near-term
growth to 5-10 flags (every cfg key that participates in normalize), the
bitmap is correct. The cohort-audit rule from CLAUDE.local.md
2026-05-11 also leans toward bitmap when "obvious near-term growth"
exists (which is the case for normalize tracking).

**Impact:** v5.15.4.A becomes a uint64_t addition + a few MASK constants
+ parser hooks; ~30 LOC vs. ~50 LOC for a struct-of-bool approach. More
importantly: future contributors discover the existing pattern
(BITMAP_IS_SET / BITMAP_SET) and use it uniformly.

**Severity:** HIGH (consistency with the codebase's established bitmap API;
reverses precedent if not done now).

---

### MEDIUM-1 — v5.15.3 stamp_emit_for_horizon should ALSO replace single-horizon's manual block

**Plan claim** (v5.15.3.A Step 1): "Extract `stamp_emit_for_horizon` helper.
The helper is shared by .A (single-thread) and .C (parallel-thread).
Single source-of-truth for per-horizon stamp assembly."

**Codebase reality:** single-horizon training at
`Backtest/BacktestPanels.hpp:3206-3266` (`train_model_worker_fn` post-v5.14.post1)
has ~60 LOC of explicit STAMP_SET / inf.* population. The
`stamp_emit_for_horizon` helper as designed could ALSO be called from
single-horizon path with `horizon_idx=0`, `horizon_count=1`,
`grid_member_count=1`. Adding canonical single-horizon adoption would unify
THREE callers (single-horizon, multi-horizon serial, multi-horizon parallel)
on one helper.

**Counter-argument:** single-horizon doesn't have per-horizon TP/SL/ticks
parameters; its emit reads cfg.label_lookahead_ticks / cfg.label_tp_pct /
cfg.label_sl_pct DIRECTLY. The helper interface forces single-horizon to
plumb those through as parameters, which is verbose.

**Proposed merge:** v5.15.3 helper could take 2 forms:
- Form A — narrow helper for MULTI-HORIZON sites only (current plan); single-horizon stays as it is. Risk: future Class 18 drift between single-horizon and multi-horizon stamp emit.
- Form B — broader helper unifying all 3 sites; single-horizon calls
  `stamp_emit_for_horizon(path, cfg, 0, 1, cfg.label_lookahead_ticks,
  cfg.label_tp_pct, cfg.label_sl_pct, ...)`. ~30 LOC saved in
  BacktestPanels.hpp.

**Per CLAUDE.md item 19** (structural fix preferred when bug class can
recur): the v5.14.post1 patch was a single-horizon stamp body migration
gap caught after v5.14.8 ship. The class is "production-caller assembles
stamp inputs" — there were originally 2 production callers (single +
multi); v5.15.3 keeps 2 callers. Form B would reduce to 1 caller +
extinguish the class fully.

**Recommendation:** Form B. Single-horizon migration is a ~30 LOC edit at
the v5.15.3.A site. Bumps total v5.15.3 LOC by ~30 but closes the class
fully + makes the next stamping change a 1-row helper update.

**Severity:** MEDIUM (Class 18 mirror prevention; deferrable but worth
folding in given the helper is being extracted anyway).

---

### MEDIUM-2 — v5.15.2 LiveReadiness_Verify table-driven dispatch aligns with FOREACH_SLOW_PATH_GATE shape

**Plan claim** (v5.15.2.B Step 1): "kLiveReadinessChecks[] — `static
constexpr LiveReadinessCheck<F> kLiveReadinessChecks[]` array... boot gate
table-driven, ADDING a new check = 1 row + 1 fn definition."

**Codebase reality:** `CoreFrameworks/SlowPathGateRegistry.hpp` already has
`FOREACH_SLOW_PATH_GATE(X)` X-macro registry with table-driven dispatch +
auto-generated bit positions + AUTOPOPULATE walks. Same shape, different
domain (per-core slow-path gates vs. boot-time pre-flight gates).

**Proposed merge:** v5.15.2 should declare the live-readiness checklist as
`FOREACH_LIVE_READINESS_CHECK(X)` X-macro registry, matching the
SlowPathGate shape:
```cpp
#define FOREACH_LIVE_READINESS_CHECK(X) \
    X(SECRET_NONEMPTY,           REFUSE, check_secret_nonempty<F>, \
      "set held_out_stamp_secret in secrets.cfg") \
    X(MLOCKALL_SUCCEEDED,        REFUSE, check_mlockall_succeeded<F>, \
      "run engine as root OR set require_mlockall=0 (degraded)") \
    ...
```
Then kLiveReadinessChecks[] is X-macro-expanded; severity / fn / hint /
auto-generated bit positions for ledger / count macros.

**Wins:** consistent with the existing slow-path-gate-registry-pattern
DESIGN_SPEC. Adding a new check stays a 1-row change. Bit positions for
"which check failed" surface to PerCoreSnap via auto-generated
`FAILURE_LIVE_READINESS_SECRET_NONEMPTY` bit.

**Counter-argument:** the v5.15.2 plan already has 9 checks; the constexpr
array is structurally identical to the X-macro registry; the auto-gen
benefits (count macro, MASK constants) aren't critical at boot.

**Severity:** MEDIUM (consistency upside; not pattern-violation if not
done). Defer to TECH_DEBT if not folded in v5.15.2.

---

### LOW-1 — v5.15.0 + v5.15.3 share STAMP_HAS / STAMP_SET API; no new accessors needed

**Verification:** v5.15.0 introduces HANDLE_HAS / HANDLE_SET / HANDLE_CLR
for ModelHandle bit-packed has_flags. Existing STAMP_HAS / STAMP_SET /
STAMP_CLR (at `StampBoundModelConstRegistry.hpp:567-569`) for
ModelStampResult + StampInferenceCfgInputs.

```cpp
// Existing (StampBoundModelConstRegistry.hpp):
#define STAMP_HAS(s, name)  BITMAP_IS_SET((s).has_flags, MASK_##name)
#define STAMP_SET(s, name)  BITMAP_SET((s).has_flags, MASK_##name)

// Proposed v5.15.0 (ModelInference.hpp):
#define HANDLE_HAS(h, name)  BITMAP_IS_SET((h).has_flags, MASK_HANDLE_HAS_##name)
#define HANDLE_SET(h, name)  BITMAP_SET((h).has_flags, MASK_HANDLE_HAS_##name)
```

**Both** alias to BITMAP_* primitives via the same shape; **both** assume
`has_flags` is the underlying field name. Consistent API shape +
consistent naming convention.

**Caveat:** HANDLE_* uses `MASK_HANDLE_HAS_` prefix; STAMP_* uses bare
`MASK_` prefix. Inconsistent. Future could be:
- Option A — rename STAMP_* MASK constants to `MASK_STAMP_HAS_<X>`
  (consistent prefix) — wide cascade, not feasible
- Option B — name HANDLE_* MASK constants as bare `MASK_HANDLE_<X>` (drop
  the HAS infix; symmetrical with STAMP_HAS using just `MASK_<X>`)
- Option C — keep both as proposed; document the asymmetry

**Recommendation:** **Option B** if v5.15.0 hasn't started yet. Names like
`MASK_HANDLE_TRAINING_POLL_INTERVAL` mirror `MASK_training_poll_interval`
(STAMP) — both are "presence" flags; both use the same shape; both differ
only in prefix. Cleaner than the verbose `MASK_HANDLE_HAS_*`.

**Severity:** LOW (style consistency; doesn't break anything).

---

### LOW-2 — v5.15.0 ModelHandle field count is 15 not 14 or 16

**Verification:** `grep -c "^\s*uint8_t\s\+has_" ML_Headers/ModelInference.hpp` reports **15** uint8_t has_* fields. Plan says 14-16 range. Confirmed:
```
has_training_poll_interval    has_stamp_num_outputs
has_xgb_hyperparams            has_build_flags_hash
has_stamp_inference_cfg        has_stamp_bandit
has_stamp_fees                 has_stamp_xgb_train_nthread
has_stamp_label_params         has_stamp_scaler_sha256
has_overlay_hash               has_effective_hash
has_training_timestamp_us      has_run_name
has_scaler  (in scaler struct, not ModelHandle directly — exclude)
```

So the migration count is **14** if `has_scaler` (FeatureStandardizer
member) is excluded; **15** if included. Plan can stay at 14 with note.

**Severity:** LOW (informational; trivial).

---

### LOW-3 — v5.15.4 normalize pass tests COULD share fixture with v5.15.2 trading_mode round-trip tests

Both v5.15.2 + v5.15.4 use the same `ControllerConfig<64> cfg;
ControllerConfig_Default<64>(cfg); cfg.trading_mode = TRADING_MODE_LIVE;`
fixture. Test extraction is mechanical + saves ~5-10 LOC.

**Severity:** LOW (test infrastructure; nice-to-have).

---

### LOW-4 — v5.15.0 parser refactor could share dispatch with v5.15.1's failure_flags-set

If v5.15.0.B's `verify_model_stamp` parser becomes data-driven, the
dispatch table entries could OPTIONALLY include a `failure_bit` column.
On parser detect-failure, table walker SETS the failure bit on the
per-core snap. Reduces 2 walks (parse + drift detect) to 1 walk.

**Counter:** v5.15.0.B parser walks the file once; v5.15.1's drift detect
walks at TryLoadRole post-verify. Different scopes (parse-time vs.
load-time). Compute is already minimal at boot. Don't fold unless
v5.15.1 surfaces a real perf concern.

**Severity:** LOW (premature optimization; defer).

---

## Cross-codebase reuse opportunities (existing code already has it)

### HIGH-4 — v5.15.2 kLiveReadinessChecks REUSES existing checks scattered across boot

**Existing boot-time checks:**
- `cfg.held_out_stamp_secret[0] != '\0'` — checked at
  `ML_Headers/CoreModelZoo.hpp:181` (verify_model_stamp call) — but no
  pre-flight refuse
- `cfg.require_mlockall` — checked at `main.cpp:198-208` (level_required) —
  exits early if can't lock
- `cfg.core_strategies_explicit_set` — checked at
  `ControllerConfig.hpp:2700-2701` (hardcoded fallback warning)
- `cfg.model_max_age_hours` + `m->training_timestamp_us` — checked at
  `CoreModelZoo_CheckStaleModel` (CoreModelZoo.hpp:2503) — returns -1 in
  strict
- Feature/label/build_flags hash drift — checked via
  `FOREACH_STAMP_BOUND_CFG` X-macro at `CoreModelZoo.hpp:206-225`
- `model_verify_strict` — controls REFUSE-vs-WARN per check

**Plan recommendation:** v5.15.2 kLiveReadinessChecks SHOULD reference
these existing check functions as the predicate `fn` field, not
re-implement them. Specifically:
- `check_secret_nonempty<F>` → reads `cfg.held_out_stamp_secret[0]`
- `check_mlockall_succeeded<F>` → reads the existing capture
  point (need to add `s.mlockall_succeeded` to `EngineShardedState<F>`
  populated from main.cpp's mlockall() call)
- `check_all_cores_strategy_explicit<F>` → reads
  `cfg.core_strategies_explicit_set` — `popcount(it) ==
  cfg.num_execution_cores`
- `check_model_max_age_set<F>` → reads `cfg.model_max_age_hours` +
  per-handle `m->training_timestamp_us` via `CoreModelZoo_CheckStaleModel`
- `check_no_feature_hash_drift<F>` → reads
  `BITMAP_IS_SET(per_core_snap.failure_flags,
  MASK_FAILURE_FEATURE_HASH_DRIFT)` after v5.15.1.A wires it

**Plan as-drafted:** v5.15.2.B Step 1 actually does this in spirit (the
example fn definitions read `cfg.held_out_stamp_secret[0]`, `s.cores[c].percore_snap.failure_flags`, etc.).
Cross-codebase reuse already adequate at design level. The MEDIUM-2
proposal above (FOREACH_LIVE_READINESS_CHECK X-macro) further consolidates.

**Severity:** HIGH if existing checks were ignored; MEDIUM-confirmed
adequate after re-reading the plan. Verify at coding time.

---

### MEDIUM-3 — v5.15.3 per-horizon stamp logic could leverage Backtest_RunFullValidation as canonical

**Existing canonical pattern:** `Backtest/BacktestEngine.hpp:1147-1220`
(`Backtest_RunFullValidation` STAMP_SET assembly) +
`Backtest/BacktestPanels.hpp:3206-3266` (train_model_worker_fn
post-v5.14.post1). v5.15.3 plan references both. Helper extraction
already follows the canonical shape.

**Verification:** plan's stamp_emit_for_horizon body (v5.15.3.A Step 1) is
~70 LOC, sequencing STAMP_CFG_AUTOPOPULATE + STAMP_MODEL_CONST_AUTOPOPULATE
+ per-horizon manual fields (label_lookahead_ticks / tp_pct / sl_pct /
grid_member_count / horizon_idx / horizon_count / model_num_outputs /
xgb_hyperparams / build_flags_hash / label_registry_hash / scaler /
run_name). Matches the canonical shape.

**Severity:** MEDIUM-confirmed adequate (no new merge).

---

### LOW-5 — CLI arg parsing in main.cpp / foxml_suite.cpp is minimal

**Verification:** `main.cpp:134` uses `const char *cfg_path = (argc > 1) ?
argv[1] : "engine.cfg";`. `foxml_suite.cpp:86` has `int main(int argc, char
*argv[])` but no argv parsing (looks at it but doesn't use argv currently).

**Plan implication:** v5.15.3's hinted FOREACH_CLI_MODE for batch
training would be NEW infrastructure. Plan doesn't actually define
FOREACH_CLI_MODE — only references it in the DOD pass + verification gate
("FOREACH_CLI_MODE dispatch uses fn-pointer table"). This is a hint at
future work that doesn't land in v5.15.3.

If v5.15.3 DOES add CLI parsing for `--batch --train-multi N` (referenced
in test commands at v5.15.3.D Test 5), it should mirror the engine's
minimal pattern (positional argv access) or introduce a getopt_long style.
Don't over-engineer FOREACH_CLI_MODE in v5.15.3; defer if not concretely
needed.

**Severity:** LOW (informational; plan is ambiguous about CLI infrastructure).

---

### LOW-6 — Progress IPC via files: no existing pattern

**Verification:** No `.progress` files / status file patterns found in
codebase. Existing `status_msg` is in-process state on
`MultiHorizonRunState` / `FvRunState` structs, surfaced via GUI thread
read.

**Plan implication:** v5.15.3's CLI/batch mode (if implemented) would
either need to (a) write progress to stderr (operator-shell-visible) or
(b) introduce file-based progress IPC. No existing pattern to consume.

If v5.15.3 introduces file-based progress, capture as future merge
candidate when 2nd consumer emerges.

**Severity:** LOW (no existing duplication; greenfield).

---

## Helper extraction opportunities (NEW helpers identified)

### M-1 — stamp_emit_for_horizon (v5.15.3.A) — already planned

Plan correctly identifies + extracts this helper. See MEDIUM-1 above for
the question of whether single-horizon also adopts it.

### M-2 — HotSwapSnapshot capture/revert/discard (v5.15.4.B) — already planned

Plan correctly extracts the capture/revert/discard trio. See HIGH-2 above
for the reuse-with-BinanceDepth concern.

### M-3 — LiveReadiness_Verify (v5.15.2.B) — already planned

Plan correctly extracts as a self-contained boot-time validator. See
MEDIUM-2 (FOREACH_LIVE_READINESS_CHECK X-macro) for the registry-driven
alternative.

### M-4 — ControllerConfig_NormalizeForMode (v5.15.4.A) — already planned

Plan correctly extracts as a post-parse normalize pass. See HIGH-3 above
for the `key_explicit` bitmap concern.

---

## API consistency checks (BITMAP_*, STAMP_*, HANDLE_*, FAILURE_* naming/shape)

### CHECK-1 — BITMAP_* API canonical use across v5.15

**Findings:**

| Sub-plan | BITMAP_* application | Consistency |
|---|---|---|
| v5.15.0 | uint64_t `has_flags` for ModelHandle via `BITMAP_IS_SET / SET / CLR` | CONSISTENT |
| v5.15.1 | uint16_t `failure_flags` extension; uint16_t `state_flags` migration | CONSISTENT |
| v5.15.4 | NEW uint64_t `cfg_keys_explicit_set` (suggested per HIGH-3) | should become consistent |

All sub-plans use `BITMAP_IS_SET / SET / CLR` from
`MemHeaders/BitmapMacros.hpp`. **Atomic ordering:** v5.15.0 + v5.15.1 are
slow-path-single-writer (no atomic needed; non-atomic BITMAP_SET).
v5.15.4's `g_swap_seq` uses `__ATOMIC_RELAXED` (acceptable for
seqlock-like counters). HotSwapSnapshot pointer publication uses
`__ATOMIC_RELEASE` + acquire-load (matches BinanceDepth.hpp precedent).

**Verdict:** API usage is CONSISTENT across sub-plans. Minor nit: ensure
HotSwapSnapshot's `snapshot_taken` byte is published with same memory
order as the pointer fields (likely needs ATOMIC_RELEASE if
cross-thread-visible).

### CHECK-2 — STAMP_HAS vs HANDLE_HAS naming asymmetry

**Findings:**

- STAMP_HAS (existing): `MASK_<entry_name>` — bare prefix (e.g.,
  `MASK_training_poll_interval`)
- STAMP_SET (existing): `MASK_<entry_name>`
- FAILURE_SET (existing): `FAILURE_MASK_<entry_name>` — prefix
- STATE_FLAG_SET (existing): `MASK_<UPPERCASE_NAME>` — prefix
- HANDLE_HAS (proposed v5.15.0): `MASK_HANDLE_HAS_<entry_name>` — long prefix

**Inconsistency:** prefix conventions are heterogeneous across the
codebase already. v5.15.0's `MASK_HANDLE_HAS_*` introduces yet another
variant. See LOW-1 above for the `MASK_HANDLE_*` (no `_HAS_` infix)
alternative.

**Verdict:** **LOW** action item. Either standardize on `MASK_HANDLE_*`
(drop HAS) for the new API, or accept the asymmetry. Existing FAILURE_*
shape is also `FAILURE_MASK_*` with prefix; HANDLE_* could follow that
shape as `HANDLE_MASK_*` for symmetry. Document + pick at coding time.

### CHECK-3 — STAMP_CFG_AUTOPOPULATE companion macro presence

**Findings:** STAMP_CFG_AUTOPOPULATE + STAMP_MODEL_CONST_AUTOPOPULATE
both exist (at `StampBoundCfgRegistry.hpp:210` +
`StampBoundModelConstRegistry.hpp:601`). v5.15.0.B parser refactor +
v5.15.3 stamp_emit_for_horizon both consume them correctly. v5.15.2's
trading_mode addition flows through STAMP_CFG_AUTOPOPULATE auto-expansion
at 7 consumer sites (per plan's auto-flow walk in v5.15.2.A Step 4).

**Verdict:** AUTOPOPULATE companions correctly leveraged across sub-plans.
CONSISTENT.

### CHECK-4 — FAILURE_SET / FAILURE_ATOMIC_SET cross-thread visibility

**Findings:** v5.15.1.A drift bits are SET at slow-path / boot time
(single-writer); GUI reads via TUISnapshot publication (existing pattern).
Cross-thread visibility is via TUISnapshot's seqlock publication, not via
atomic write on failure_flags directly. Plan correctly uses non-atomic
FAILURE_SET; matches v5.14.8.B precedent at
`CoreFrameworks/ShardedSnapshot.hpp:609,644`.

**Verdict:** CONSISTENT.

---

## HIGH findings (merges that prevent duplication baking in)

1. **HIGH-1: v5.15.1 drift chokepoint duplicates existing FOREACH_STAMP_BOUND_CFG X-macro loop** at CoreModelZoo.hpp:206-225. Extend the existing loop with FAILURE_SET; don't add parallel detection. ~60 LOC saved + structural prevention of two parallel drift detectors.
2. **HIGH-2: v5.15.4 HotSwapSnapshot reinvents the BinanceDepth.hpp double-buffer pattern** (BookSnapshot snapshots[2] + active_idx). Reuse via template-extraction OR reference as precedent in HotSwap.hpp header.
3. **HIGH-3: v5.15.4 ControllerConfigKeyExplicit should be a uint64_t bitmap** mirroring core_strategies_explicit_set + STAMP_HAS / FAILURE_* / STATE_FLAG_* — NOT a struct of bool fields. Per CLAUDE.md item 20.

---

## MEDIUM findings (nice-to-have consolidations)

1. **MEDIUM-1: stamp_emit_for_horizon should also replace single-horizon's manual block** at BacktestPanels.hpp:3206-3266. Unifies 3 callers on 1 helper; +30 LOC in v5.15.3 vs. eventual Class 18 mirror drift.
2. **MEDIUM-2: kLiveReadinessChecks should be FOREACH_LIVE_READINESS_CHECK X-macro** mirroring SlowPathGateRegistry. Consistency upside.
3. **MEDIUM-3: v5.15.3 helper already follows Backtest_RunFullValidation canonical shape** — CONFIRMED adequate; no merge action.

---

## LOW findings (informational; defer-to-future-ship candidates)

1. **LOW-1: HANDLE_HAS naming prefix asymmetry** with STAMP_HAS / FAILURE_* conventions. Pick `MASK_HANDLE_*` (no HAS_) for symmetry with STAMP, or `HANDLE_MASK_*` for symmetry with FAILURE_*. Document at coding time.
2. **LOW-2: ModelHandle has_* field count is 15** (including has_scaler in FeatureStandardizer), 14 if you exclude has_scaler. Plan can stay at 14 with note.
3. **LOW-3: v5.15.2 + v5.15.4 tests share TRADING_MODE_LIVE fixture** — extract a test helper at coding time if convenient.
4. **LOW-4: v5.15.0 parser dispatch could OPTIONALLY include failure_bit column** — defer unless v5.15.1 surfaces perf concern.
5. **LOW-5: CLI arg parsing in foxml_suite.cpp is greenfield** — don't over-engineer FOREACH_CLI_MODE in v5.15.3; defer if not concretely needed.
6. **LOW-6: Progress IPC via files: no existing pattern** — greenfield if v5.15.3 introduces.

---

## Synthesis

**Folding the 3 HIGH findings into v5.15 plan amendments BEFORE coding starts:**

- **HIGH-1** (v5.15.1 drift chokepoint): amend v5.15.1.A Step 2 to extend the existing `FOREACH_STAMP_BOUND_CFG` X-macro loop at `ML_Headers/CoreModelZoo.hpp:206-225` with `FAILURE_SET(*per_core_snap, cfg_binding_drift);` inside the existing mismatch branch. For feature/label/build_flags drift bits: hook them into `verify_model_stamp` body where the same comparisons ALREADY happen (`ML_Headers/ModelInference.hpp:1385+` for feature_registry_hash; similar for label/build). v5.15.1.A LOC drops from ~120 to ~60.
- **HIGH-2** (HotSwapSnapshot reinventing BinanceDepth's pattern): two options — (a) template-extract DoubleBufferedAtomic<T> in v5.15.4 (saves 50-80 LOC, refactor 1 existing site, single canonical pattern); (b) keep separate but document precedent in HotSwap.hpp header + match ATOMIC_RELEASE / ATOMIC_ACQUIRE semantics exactly. Either preserves consistency.
- **HIGH-3** (ControllerConfigKeyExplicit bitmap): amend v5.15.4.A Step 0 to introduce `cfg.cfg_keys_explicit_set` as uint64_t bitmap with `MASK_CFG_KEY_*` constants. Mirrors `core_strategies_explicit_set` precedent + CLAUDE.md item 20 BITMAP_* API discipline.

**MEDIUM findings: fold MEDIUM-1 (single-horizon adoption of stamp_emit_for_horizon) into v5.15.3 to extinguish the Class 18 mirror class fully. Defer MEDIUM-2 (FOREACH_LIVE_READINESS_CHECK X-macro) to a future ship unless additional checks land in the same v5.15.2 scope.**

**LOW findings: address at coding time or defer to TECH_DEBT.**

**Blocking?** No. None of the HIGH findings are coding-blockers; all are
"do upfront vs. clean up after" decisions. Plan is internally consistent +
leverages existing patterns. The HIGH findings tighten consistency with
the codebase's established patterns; folding them in upfront is cheap
(~5-10 minutes per plan amendment) vs. shipping then refactoring after
operator notices the duplication.

**Recommendation:** Address HIGH-1 + HIGH-3 in plan amendments (15-30
min); defer HIGH-2 decision to v5.15.4 coding time (template extraction
is bigger scope; documenting precedent is sufficient). Fold MEDIUM-1
into v5.15.3 (single-horizon adoption is mechanical). Proceed to coding.

---

## Audit commands run

```bash
# Cross-plan inventory
ls /home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/
# → MASTER.md + 5 subplan files; total ~135K (read in full)

# Existing patterns
grep -rn "FAILURE_SET|FAILURE_ATOMIC_SET" /home/caramel/code/FoxML_Trader_v2/
# → 2 sites in ShardedSnapshot.hpp + 4 sites in tests/

grep -rn "core_strategies_explicit_set" CoreFrameworks/ControllerConfig.hpp
# → Lines 917, 1560, 2499, 2700-2701 (existing explicit-set bitmap precedent)

grep -n "FOREACH_STAMP_BOUND_CFG" ML_Headers/CoreModelZoo.hpp
# → Line 221 (X-macro drift detection ALREADY EXISTS at 206-225)

grep -c "^\s*uint8_t\s\+has_" ML_Headers/ModelInference.hpp
# → 15 fields (LOW-2 note)

grep -c "strcmp(key" ML_Headers/ModelInference.hpp
# → 34 parser strcmp branches (matches plan estimate)

grep -n "active_idx" DataStream/BinanceDepth.hpp
# → Lines 82, 212, 307-317 (canonical double-buffer atomic-publish pattern)

rg -n "FOREACH_STRATEGY|FOREACH_FAILURE_MODE|FOREACH_PER_CORE_STATE_FLAG|FOREACH_SLOW_PATH_GATE" --type-add 'cpp:*.hpp' --type cpp -g '!build*'
# → 4 existing X-macro registries; v5.15.0/.1/.4 extend these via same pattern

rg -n "EngineSharded_HotSwapEnsemble|EnsembleHotSwap" --type cpp --type-add 'cpp:*.hpp' -g '!build*'
# → CoreFrameworks/EnsembleHotSwap.hpp:45 (existing hot-swap helper; canonical)

grep -n "BITMAP_IS_SET" MemHeaders/BitmapMacros.hpp
# → Line 78 (canonical BITMAP_* API)

grep -n "STAMP_HAS|MASK_HANDLE_HAS" MemHeaders/BitmapMacros.hpp ML_Headers/StampBoundModelConstRegistry.hpp
# → STAMP_HAS at line 567 (existing); HANDLE_HAS does NOT exist yet (v5.15.0 introduces)
```

---

## Cross-references

- Parent plan: `plans/v5.15-live-readiness/MASTER.md`
- Sister audits (run in parallel for v5.15.0 HIGH-RISK ship): `/parity-check`, `/trace-deps`, `/readiness`, `/dod-audit`
- CLAUDE.md items: 16 (reuse-audit), 19 (structural fix preferred), 20 (BITMAP_* API), 21 (AUTOPOPULATE companion)
- CLAUDE.local.md going-forward rules: structural-fix-preferred (2026-05-09), cohort-audit (2026-05-11)
- DESIGN_SPECS: bitmap-flag-api, x-macro-registry-with-presence-dispatch, autopopulate-pattern-for-production-caller-class, structural-fix-preferred-decision-framework
- Precedent: v5.12.1.A.2 (canonical clock_gettime reuse merge that motivated this skill)
