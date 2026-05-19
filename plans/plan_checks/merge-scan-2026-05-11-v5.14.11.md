# /merge-scan report — v5.14.11 online-corr-update — 2026-05-11

**Plan:** plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.11-online-corr-update.md
**HEAD:** e0cc877 (v5.14.10 umbrella)
**Mode:** Pre-coding audit of single plan against current codebase (post-v5.14.10).

---

## Scope reminder

v5.14.11 introduces incremental Welford-style online updates for the
Ridge correlation matrix. Two BuildCorr call sites (buy + exit), one
shared math kernel, one new struct (`RidgeOnlineState`), one cfg flag
(`ridge_online_corr`), optional AVX-512 path. No hot-path touch.

The merge-scan question is: where does this plan duplicate work the
current codebase already does, and where does the plan SHARE work it
could be unifying?

---

## Atomic load redundancies — N/A

Slow-path single-writer/single-reader per-ezoo invariant. No atomics
in the Ridge cycle.

## Clock-read redundancies — N/A

`last_compute_us` already tracked in `RidgeWeights` (line :102). No new
clock reads added by the plan.

## Cfg-access redundancies (priority: LOW; informational)

- `config->ridge_within_horizon` and `config->exit_blender_mode` are
  already cached in `gate_state->flags` via the v5.14.9.B.0 slow-path
  gate registry (`SlowPathGateRegistry.hpp:85` + `:89`), then read via
  `BITMAP_IS_SET(gate_state->flags, MASK_RIDGE_WITHIN_HORIZON_ACTIVE)`
  and `MASK_EXIT_BLENDER_ACTIVE` at StrategyParameters.hpp:965 +
  :1173. The new `cfg.ridge_online_corr` flag at StrategyParameters
  line ~1010 (per plan Step 3) reads `config->ridge_online_corr`
  DIRECTLY. **Lower-priority merge candidate:** add
  `MASK_RIDGE_ONLINE_CORR_ACTIVE` to the gate registry so the read is
  unified with the other Ridge-related gates in the same cached word.
  Cost-of-merge: one row in SlowPathGateRegistry.hpp + one cached-mask
  read site. Cost-of-skip: minor cache cost on hit, no semantic risk.
  **Defer to TECH_DEBT (audit all ridge_*/exit_blender_mode fields for
  ML_CFG_FLAG vs. SlowPathGateRegistry migration in a single cleanup
  sweep).**

## Function-body parallelism — HIGH PRIORITY (Class 18 mirror)

**Finding M1 — BuildHistoryFromRing duplicate ring-walk.** Lines
StrategyParameters.hpp:985-994 (buy) and :1184-1193 (exit) are
bytewise-identical except for variable names. Same loop structure,
same `__mod__` for ring indexing, same nested per-arm copy:

```
for k in [0, avail): ring_idx = (head - 1 - k + RING_SIZE) % RING_SIZE
  for i in [0, count): history[k * count + i] = ring[ring_idx].predictions[i]
```

This is **already** a Class 18 mirror in the v5.14.0 codebase
(pre-v5.14.11), and the plan's Step 3 doesn't extract a helper. The
new periodic-recompute branch at plan line 144-153 ADDS A THIRD CALL
SITE for ring-walk (recompute-from-scratch path), so the mirror grows
to 3 sites.

**Proposed unification:**

```cpp
template <unsigned F>
inline int BuildHistoryFromRewardRing(
    float* history_flat,                                   // [K * N]
    const PredictionRecord<F>* ring,                       // reward_ring
    int ring_head,                                         // reward_ring_head
    uint64_t predict_call_count,                           // gating
    int primary_count,                                     // N
    int max_depth = RIDGE_HISTORY_DEPTH);                  // K
```

Returns `avail` (records actually copied). Both call sites collapse to
1 line; recompute path also reuses. Same shape as the v5.14.2.E.1
`PostLoadSetup` extraction that closed PARITY-009/010/011/012.

**Recommendation:** **fold into v5.14.11.A** (alongside the math
kernel). Why: plan is already touching both BuildCorr sites; extracting
the ring walk in the SAME ship costs ~30 LOC + 1 helper; deferring
means v5.14.11.C touches both sites with the duplicated walk still in
place, and a follow-on ship pays the same boundary cost.

Per CLAUDE.md item 19 (structural-fix-preferred) + CLAUDE.local.md
2026-05-09: mirror across BUY ↔ EXIT is exactly the recurring shape
the rule was written for. Direct patches are for true one-offs;
mirror duplications get registries/helpers.

**Risk if deferred:** future contributor adds a third Ridge call site
(plausible — e.g., a calibration-replay path, or a "warmup smoke
Ridge" diagnostic) and copy-pastes the 10-line walk. Drift surface
identical to v5.9.5b production-caller class.

## State-field reuse — HIGH PRIORITY

**Finding M2 — RidgeOnlineState placement: extend RidgeWeights vs.
add separate struct on ezoo.**

Plan Step 3 says `ezoo->ridge_online_state` (separate ezoo field) AND
`ezoo_ex->exit_ridge_online_state` (sister field — implied by the
exit-side mirror). That's 2 new ezoo fields = 2 placement sites = 2
init sites + new tests duplicated for the exit side.

**Proposed unification:** add the online accumulators as fields of
`RidgeWeights<F>` itself (RidgeBlender.hpp:85, the existing struct):

```cpp
template <unsigned F>
struct RidgeWeights {
    // existing fields …
    double  online_mean[MAX_RIDGE_MODELS];
    double  online_M2[MAX_RIDGE_MODELS];
    double  online_outer_xy[MAX_RIDGE_MODELS][MAX_RIDGE_MODELS];
    uint64_t online_n;
    uint64_t online_cycles_since_recompute;
};
```

Wins:
- Buy-side gets it free via `ezoo->ridge_state.online_*`
- Exit-side gets it free via `ezoo_ex->exit_ridge_state.online_*`
- 1 init site (`RidgeWeights_Init` at line :374)
- 1 reset/finalize call signature, NO sister suffixes
- Future Ridge consumers (cross-horizon at ridge_across_horizons, or
  future cost-aware variants) inherit automatically
- Size cost: ~+576 bytes per RidgeWeights (8 means + 8 M2 + 64
  outer_xy + 16 counters at double precision = ~8.6KB per struct
  total, was ~8KB; still L2-resident per the existing comment at
  line :78)

**Recommendation:** **fold into v5.14.11.A.** Adopting the separate-
struct path locks 2 mirror sites into the design from v5.14.11.A
forward; switching later is a wider blast radius (rename in tests +
GUI + persist + 4 call sites).

CLAUDE.local.md "boundary-stable refactor" rule (2026-05-06): the
RidgeWeights boundary is already stable and Ridge-internal — the
plan's choice to add a SISTER struct on ezoo widens the surface
unnecessarily. Extension inside RidgeWeights keeps the cascade to 1
file.

## Cross-plan merge candidates

No other v5.14.11+ sub-plans are pending (v5.14.11 closes Phase 4;
v5.14.12+ unwritten). Cross-plan merge surface = empty.

## PostLoadSetup-registry candidate

**Finding M3 — `RidgeOnlineState` init via FOREACH_ENSEMBLE_POST_LOAD?**

The v5.14.10.C ship extended `FOREACH_ENSEMBLE_POST_LOAD` (CoreModelZoo.hpp:2370)
with `init_thompson_bandits` + `load_thompson_state` precisely because
"init must be unconditional so a cfg-flip mid-run sees pre-initialized
state" + "Class 18 mirror prevention via PostLoadSetup registry."

Same shape applies to RidgeOnlineState: cfg.ridge_online_corr can flip
from 0→1 mid-run; if `ridge_online_state` is zero-initialized but
never explicitly reset, the first Update sees stale memory (in
practice zero-init via struct default works, but the registry pattern
makes the contract explicit + symmetric across boot/backtest/hot-swap).

**Proposed:** add ONE registry entry:

```cpp
X(init_ridge_online,    RidgeOnlineState_Reset(&ezoo->ridge_state))
```

(And one more for exit-side if M2 is NOT adopted — but if M2 IS
adopted, exit-side inherits through the same ridge_state.online_*
fields, so this is one entry covering both surfaces.)

`RidgeOnlineState_Reset` zeros mean/M2/outer_xy/n/cycles. Called from
PostLoadSetup; idempotent; cheap.

Per `DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md`: any new
"initialize-once-at-boot/backtest/hot-swap" state should flow through
this registry. RidgeOnlineState qualifies.

**Recommendation:** **fold into v5.14.11.A** (alongside M2). Marginal
cost (~10 LOC).

## Branch-vs-branchless — N/A on slow-path

Plan's `if (cfg.ridge_online_corr)` and `if (++cycles > 1000)`
predicates are slow-path, low-frequency, predictable. Leave branched.

---

## Top-3 highest-impact items

1. **M1 (Function-body parallelism, BuildHistoryFromRing helper)** —
   HIGH PRIORITY. Two existing call sites + one new one (recompute
   reset) all need the same ring-walk. Extract a helper in v5.14.11.A.
   Class 18 mirror prevention; CLAUDE.md item 19 direct application.
   ~30 LOC extraction; saves recurrence risk + 20 LOC duplication.

2. **M2 (State-field reuse, RidgeOnlineState inside RidgeWeights)** —
   HIGH PRIORITY. Lock the structural choice in v5.14.11.A. Switching
   from sister struct to embedded later is a 5-file refactor (struct
   def + 2 call sites + tests + persist). Extending RidgeWeights now
   keeps the cascade to 1 file and the buy ↔ exit mirror collapses to
   "both ezoos own a RidgeWeights, both inherit online state."

3. **M3 (PostLoadSetup registry entry for ridge_online init)** —
   MEDIUM PRIORITY. Cheap; aligns with v5.14.10.C precedent; makes the
   cfg-flip-mid-run contract explicit. Adopt if M2 is adopted (single
   entry covers both buy + exit).

**Items deferred to TECH_DEBT:**

- Cfg-access redundancy for `ridge_online_corr` via gate registry
  cache (low priority; pair with future ML_CFG_FLAG migration audit
  of all `ridge_*` + `exit_blender_mode` fields).

**Items to leave alone:**

- Welford math kernel itself (plan correctly notes no codebase
  precedent; `RollingStats.hpp:83-87` is a different technique —
  running-sums Σx + Σx², numerically less stable; do not confuse).
  Implement fresh as the plan describes.
- v5.11.7 Bandit_GetProbabilities AVX-512 pattern reuse for v5.14.11.B
  vectorization. Plan correctly cites lines :139-162 as the
  bytewise-determinism template (FMA matches gcc fusion, scalar
  reductions preserve left-to-right order). No merge concern — the
  pattern IS the precedent.

---

## Verdict

GREEN with 3 amendments recommended. None of M1/M2/M3 changes the
plan's external shape (still v5.14.11.A → .B → .C → umbrella); they
reshape the INTERNAL structure of .A to land helper + struct-extension
+ registry entry in one ship rather than ship the mirror-prone
implementation + clean it up later.

If operator accepts M1+M2+M3, the v5.14.11.A LOC delta moves from
~200 → ~240. Plan's umbrella verification gate stays unchanged.

If operator defers any of M1/M2/M3 to a follow-on ship, the deferred
items MUST land in `DOCS/TECH_DEBT.md` per CLAUDE.local.md 2026-05-09.

**Class-18 mirror question explicit:** YES, this ship is the right
moment to extract the ring-walk helper. v5.14.11 touches both BuildCorr
sites; deferring means a future ship pays the boundary cost twice
(touch sites once to add online math, then again to extract helper).
Per CLAUDE.md item 19: structural fix preferred over direct patch when
the bug class can recur — BUY ↔ EXIT Ridge wiring has already drifted
once (v5.14.1.E added exit-side; buy + exit are not perfect mirrors
today). One more divergence pass before extraction would compound the
debt.
