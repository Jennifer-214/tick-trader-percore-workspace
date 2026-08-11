# ML architecture — design notes + future-direction brainstorm

**Status:** BRAINSTORM — pre-design capture. Not a plan; not an active design spec. Stash for `DOCS/ML_ARCHITECTURE.md` drafting at `.F.4d` ship close (or later — operator decision on timing).

**Why this file exists:** during `.F.4d` Step 1 implementation (`Thompson_GetSoftmaxWeights` + `Order::flags_packed` bit-pack), Caramel surfaced architectural reflections on the dual-model setup that warrant capture before they rot in chat history. Per CLAUDE.local.md "New docs default to private" + `plans/_future/` destination convention.

---

## Current architecture (at HEAD `7538ace` — pre-`.F.4d`)

`EnsembleModelZoo<F>` at `ML_Headers/NodeModelZoo.hpp:953` defines 4 distinct model role arrays:

| Role array | Purpose | Bandit driver | Reward attribution |
|---|---|---|---|
| `buy_signal[ENSEMBLE_HORIZON_MAX]` | ENTRY decision (when to buy) | `bandits[NUM_REGIMES]` (Exp3 currently; `.F.4d` adds Thompson option) | per-arm buy-side reward signal |
| `exit_predictor[ENSEMBLE_HORIZON_MAX]` | EXIT decision (when to sell / hold) | `exit_bandits[NUM_REGIMES]` (Exp3 only at HEAD; `.F.4d` adds `thompson_exit_bandits[]` mirror) | per-arm exit-side reward signal |
| `barrier[ENSEMBLE_HORIZON_MAX]` | per-horizon TP/SL prediction | n/a (per-arm direct) | barrier-specific (separate channel) |
| `regime[ENSEMBLE_HORIZON_MAX]` | market regime classifier | n/a | regime classifier accuracy |

Per-side independence: 4 distinct ML pipelines, 2 distinct bandit pools, separate cfg thresholds (`confidence_hard_block_threshold` for entry, `exit_threshold` for hold-vs-exit decision at `ControllerConfig.hpp:788`).

---

## Caramel's brainstorm (2026-05-16 during `.F.4d` Step 1 coding)

> *"i feel like i overengineered that because i just wanted to try something exotic, but also the exit side could have a new label like 'maximized returns' or 'mean held time to peak return from entry point' or something these are just thoughts for when we document it"*

> *"we should definitely document this and add like a setting with different setups someone can choose i think or as a config setting per core i think, that sounds like the best idea"*

Two distinct ideas surfaced:

### Idea 1 — Per-core model-architecture-mode cfg flag

NEW cfg field: `core_N_ml_architecture_mode` (enum). Operator picks per-core which ML setup to use. Enumerated options:

| Mode | Entry side | Exit side | Use case |
|---|---|---|---|
| `DUAL_ML` (current default) | ML `buy_signal` | ML `exit_predictor` | full specialization; current behavior |
| `ML_ENTRY_RULE_EXIT` | ML `buy_signal` | rule-based (fixed TP/SL + time-exit) | HFT classic; simpler exit |
| `RULE_ENTRY_ML_EXIT` | rule-based (regime + indicator gates) | ML `exit_predictor` | retail trader pattern |
| `JOINT_POLICY` (future) | single joint RL policy emitting position-size deltas | (same) | end-to-end RL; most sample-efficient |
| `RULE_ONLY` | rule-based both sides | (same) | baseline; no ML at all |

**Why per-core:** allows A/B comparison across cores (e.g., core 0 = DUAL_ML, core 1 = ML_ENTRY_RULE_EXIT). Operator sees divergent PnL streams per-core; informs which setup to keep + which to drop.

**Implementation cost estimate:** ~6-10h focused. Touches: new `ml_architecture_mode` enum + cfg field + per-core override + slow-path gate predicate dispatch (mode-dependent dispatch table per `branchless-dispatch-discipline.md` Pattern 1). Each mode needs explicit code path (entry side + exit side decision logic per mode). New `STAMP_BOUND` for replay-determinism.

**Why not just "skip the ML if cfg flag says rule":** because the rule-based fallbacks for entry + exit don't exist in code yet — currently if ML strategy is selected, ML drives. Adding modes means writing explicit rule-based entry + exit code paths + wiring them via mode dispatch.

**Status:** future work; NOT in `.F.4d` scope. Candidate for post-v5.15-umbrella feature ship (after operational items + paper-test validate the current dual-ML setup is stable).

### Idea 2 — Exit-side label redesign (maximized-returns variant)

Current `exit_predictor` label (need to verify in code): probably "what's the exit probability at this horizon" or "did we exit profitably." The model learns to predict P(exit-now-is-good).

**Caramel's brainstorm labels:**
- `"maximized returns"` — what fraction of the peak achievable return from entry-time did this exit capture? (Counterfactual: had we held until peak, return would have been X; we exited at Y; label = Y/X. Reward = capture-efficiency.)
- `"mean held time to peak return from entry point"` — average time from entry to the post-entry price peak. Model learns to time exit near peak-return moments, not just "exit when profitable."

**Why this matters:** current label likely trains exit-predictor to be CONSERVATIVE (exit when profit > threshold) rather than OPTIMAL (exit at peak). The "maximized returns" label rewards capturing-the-peak behavior — model would hold longer when peak is still ahead, exit sooner when peak has passed.

**Trade-offs:**
- **Pro:** higher expected returns if model can identify peak proximity
- **Pro:** label is forward-looking + intuitive ("did we capture most of the available return?")
- **Pro:** matches the "hold to maximize returns" framing already in `cfg.exit_threshold` semantics
- **Con:** label requires LOOKAHEAD at training time (we know the peak after the fact); careful to avoid leakage at inference
- **Con:** model could overfit to noise — sometimes "peak" is just market microstructure noise, not a real signal
- **Con:** training-serve parity concern — if labels are computed differently in train vs serve (training has lookahead; serve doesn't), parity audit at every retrain
- **Con:** could increase variance — model holds longer, more exposure to adverse moves; risk-adjusted return may not improve

**Implementation cost estimate:** ~4-6h to add as ALTERNATIVE label option (operator picks via cfg flag `exit_label_kind`); ~2-3h to validate via backtest A/B against current label; iteration loop with paper-test for the rest. NOT trivial but bounded.

**Status:** future work; NOT in `.F.4d` scope. Sequence after Idea 1 (mode flag) ships so this label can be tested via the `ML_ENTRY_RULE_EXIT` mode (rule-entry isolates exit-label variance).

### Operator self-critique to capture

> *"i feel like i overengineered that because i just wanted to try something exotic"*

Documenting as design-philosophy note: the dual-model + per-side-bandit architecture WAS partially exploratory. At current scale (paper trading, modest labeled data, operator-debuggability priority) it has clear pros (specialization, independent calibration, reward attribution clarity). At LARGER scale (live trading, abundant labeled data, less debuggability need) the joint RL policy approach OR rule-based hybrids could outperform structurally.

**The structural complexity (mirror sites) WAS a real cost** — Class 18 mirror risk + per-side bandit duplication + asymmetric drift exposure. `.F.4d` Thread B `FOREACH_BANDIT_SIDE` meta-X-macro AMORTIZES this cost by making the buy/exit mirror auto-generated rather than hand-mirrored. So the dual-model setup is now structurally cheap to maintain even though it was historically expensive.

**Bottom line:** not a bad call given priorities at the time; the cost was real but is now structurally closed by `.F.4d` framework; future architectural changes (Idea 1 mode flag, Idea 2 label redesign) can be added on top without re-litigating the dual-model decision.

---

## Promotion path to `DOCS/ML_ARCHITECTURE.md`

When `.F.4d` ships + we draft `DOCS/ML_ARCHITECTURE.md`, this brainstorm provides:

1. **Section "Current architecture"** — 4 model roles + bandit per side + reward attribution (above table)
2. **Section "Design rationale + trade-offs"** — dual-model pros/cons (from earlier chat exchange; recap above in self-critique)
3. **Section "Future directions"** — Idea 1 mode flag + Idea 2 label redesign as numbered enhancement candidates with cost estimates + sequencing
4. **Section "When dual-model wins / when it doesn't"** — guidance for future contributors deciding whether to add a new mode vs extend dual-model

Suggested file location at promotion time: `DOCS/ML_ARCHITECTURE.md` (public engine repo `DOCS/`; symlinked from workspace per existing convention). Length target: ~300-500 lines markdown. Should cross-reference `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md`, `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md`, `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md`, current `.F.4d` ship's FOREACH_BANDIT_SIDE meta-X-macro pattern.

---

## Pointers (for future doc drafting)

- `ML_Headers/NodeModelZoo.hpp:953` — EnsembleModelZoo<F> struct with 4 model role arrays
- `ML_Headers/NodeModelZoo.hpp:1003-1012` — bandits[] + exit_bandits[] + thompson_bandits[] state
- `CoreFrameworks/ControllerConfig.hpp:788` — `exit_threshold` cfg field + hold-vs-exit semantics
- `CoreFrameworks/ControllerConfig.hpp:970` — `confidence_ic_floor` cfg field (entry-side related)
- `Strategies/StrategyInterface.hpp:181-196` — FOREACH_REGIME enumeration (5 regimes)
- `Strategies/MLStrategy.hpp` (if exists) — ML strategy dispatch
- `Backtest/LabelFunctions.hpp` — existing label function shapes (where Idea 2 new label would land)
- `.F.4d` merged plan body § G — FOREACH_BANDIT_SIDE auto-mirror infrastructure

---

## `.F.4d` framework decisions captured (2026-05-16 coding session)

The following structural pattern decisions were made + shipped during `.F.4d` Phase II coding. Capture here so the future `DOCS/ML_ARCHITECTURE.md` draft can lift them into the canonical doc.

### Decision A: Pattern 5 sink-fn-pointer for Thompson_Update branchless dispatch

**What:** `EnsembleModelZoo<F>` gained two fn-pointer fields (`thompson_update_fn` + `exit_thompson_update_fn`) of type `ThompsonUpdateFn = void(*)(ThompsonBanditState*, int arm, double reward)`. Default value at struct construction = `&noop_thompson_update` (compile-time-defined empty fn). Boot wiring at `_InitThompsonBandits` (buy) + `_InitExitThompsonBandits` (exit) sets to `&real_thompson_update` (delegates to `Thompson_Update`) when subsystem actually initializes.

**Why:** pre-.F.4d reward-attribution dispatch sites had per-call branches like `if (cfg.bandit_algorithm == THOMPSON || ...) { Thompson_Update(...); }`. Data-dependent control-flow per H20; predictor-warmup cost on cfg-flip; leaves callsite-by-callsite drift risk when adding new bandit modes (each new mode → every dispatch site needs updating = Class 18 mirror risk). The sink-fn-pointer pattern eliminates the branch entirely at every consumer site:
```cpp
ezoo->thompson_update_fn(&ezoo->thompson_bandits[regime], arm, reward);  // always-called; branchless
```
Cost: ~1-2ns indirect call (predicted to same target → no mispredict; same target until boot reconfigures). Closes Class 24 sister + Class 28 instances structurally for the dispatch family.

**Implementation:**
- `ML_Headers/ThompsonBandit.hpp` — `noop_thompson_update` + `real_thompson_update` + `ThompsonUpdateFn` typedef
- `ML_Headers/NodeModelZoo.hpp` — `thompson_update_fn` + `exit_thompson_update_fn` fields on `EnsembleModelZoo<F>`; default-init in `_Init`; boot-wire in `_InitThompsonBandits` / `_InitExitThompsonBandits`

**Pattern doc:** `DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md` (Pattern 5 of `branchless-dispatch-discipline.md`). `.F.4d` is the 5th canonical application.

### Decision B: FOREACH_BANDIT_SIDE meta-X-macro for buy/exit symmetry — hybrid auto-mirror

**What:** new meta-X-macro `FOREACH_BANDIT_SIDE(X) X(buy) X(exit)` at `ML_Headers/bandit_dispatch_table.hpp`. Single 2-row registry serves as site-of-truth for buy/exit per-side symmetry. Per § G of `.F.4d` merged plan body.

**What's auto-mirrored via the meta-X-macro:**
- `MASK_EZOO_<SIDE>_THOMPSON_READY` init flags (clean macro name-concat; no rename cost)
- (deferred per TECH_DEBT-084) full per-side fn families: init / load / save / dispatch table / sink-fn field

**What's hand-mirrored (intentional design trade-off):**
- `thompson_bandits` (buy-implicit; existing name) + `thompson_exit_bandits` (exit-explicit) — asymmetric field names; full symmetric rename to `buy_thompson_bandits` would cascade across ~50 call sites
- `EnsembleModelZoo_InitThompsonBandits` (buy) + `EnsembleModelZoo_InitExitThompsonBandits` (exit) — hand-mirror fn bodies

**Why hybrid?** Pure-auto-gen via macro name-concat requires the existing `thompson_bandits` field to be renamed `buy_thompson_bandits` for symmetry. At 2 current sides + 3-4 projected, hand-mirror is the cheaper short-term call. Full symmetric rename + auto-gen tracked at **TECH_DEBT-084** for `.F.4f` cleanup ship OR trigger-driven (when a 3rd per-side axis is proposed).

**Future addition of 3rd side (e.g., per-symbol Thompson):**
- Today: ~30-50 lines of hand-written mirror per fn family × 4 fn families = ~150-200 lines
- Post-TECH_DEBT-084: 1 row in `FOREACH_BANDIT_SIDE` + relevant cfg field

### Decision C: 5-state bandit expansion with 7-arg metadata-driven dispatch

**What:** `FOREACH_BANDIT_ALGORITHM` expanded from 3 states to 5, with tuple widened from 4-col `(name, val, fn, doc)` to 7-col `(name, val, fn, exp3_up, thompson_up, drives, doc)`. The metadata bits (`exp3_up` / `thompson_up` / `drives` token) drive auto-derived dispatch primitives via X-macro reduction.

**States:**
- 0 = EXP3 (default; unchanged; Thompson frozen)
- 1 = THOMPSON (Thompson only; Class 24 fix — posterior now updates from rewards)
- 2 = EXP3_OP_THOMPSON_GHOST (was "BOTH" pre-.F.4d; Option C wire-byte preservation; Class 24 sister attribution fix flips chosen_arm to Exp3's argmax)
- 3 = THOMPSON_OP_EXP3_GHOST (NEW; Thompson drives + Exp3 shadow-learns)
- 4 = BLENDED (NEW EXPERIMENTAL; weighted blend via thompson_exp3_blend_alpha)

**Auto-derived primitives:**
- `BANDIT_EXP3_UPDATE_MASK` / `BANDIT_THOMPSON_UPDATE_MASK` via X-macro reduction over (exp3_up / thompson_up) bits
- Dead-state assert via X-macro reduction (`(exp3_up || thompson_up)` per row)
- Dispatch table fn-pointers indexed by enum value
- Reward dispatch tables (Step 1.B) — `?:` chain auto-selects leaf reward fn per row from `(exp3_up, thompson_up)` metadata; adding a 6th algorithm = 1 row → both buy + exit reward tables auto-extend

**Adding a 6th algorithm:** 1 row in `FOREACH_BANDIT_ALGORITHM` with metadata tuple → dispatch table + dead-state assert + reward dispatch (both sides via `FOREACH_BANDIT_SIDE`) + COUNT + ToString/FromString all auto-extend. ZERO callsite changes at the dispatch boundary. Closes Class 18 + Class 28 structurally for the dispatch family.

**Option C wire-byte preservation:** cfg=0/1/2 numeric values unchanged across `.F.4d`; legacy stamps + cfg files load cleanly. Semantic flip for cfg=2 documented in cfg.example tooltip + postmortem. Legacy "BOTH" / "Both" / "both" string aliases preserved in `FromString` for operator-cfg backward compat.

**Dispatch contract widened 5-arg → 6-arg:** added `double blend_alpha` for BLENDED state per § J of merged plan body. Decision over seqlock-cached-read: prefer fn-arg widening (uniform contract; no Class 27 cache-mirror on BanditState). Non-BLENDED states pass `(void)blend_alpha;` (ignored).

### Decision D: Order::flags_packed bandit context bit-pack (Pattern 4 decision-time binding)

**What:** `Order<F>::flags_packed` (uint32_t) gained 9 new bits for bandit context at decision time:
- Bits 17-19: `bandit_active_state` (3 bits; ≤8 states; 5 currently used)
- Bits 20-22: `bandit_regime` (3 bits; ≤8 regimes; 5 currently)
- Bits 23-25: `bandit_chosen_arm` (3 bits; ≤8 arms; ENSEMBLE_HORIZON_MAX)
- Bits 26-31: 6 bits free headroom

**Why:** bandit context (which state + regime + arm drove the decision) flows with the Order through the trade lifecycle. Reward attribution at calib emit + DrainPostFill reads from Order::flags_packed directly — no Class 27 scalar cfg-mirror cache on OmsState. Pattern 4 (decision-time data binding) sister to existing `MASK_ORDER_PRE_RESOLVED` bit at bit 16.

**Accessors:** `MBS_*` (multi-bit-state) branchless via shift+mask:
- `MBS_OrderBanditActiveState(o)` / `MBS_OrderBanditRegime(o)` / `MBS_OrderBanditChosenArm(o)` — read
- `MBS_OrderSetBanditContext(o, state, regime, arm)` — write (clear-and-set in one expression)

**Order<F> size:** UNCHANGED at 320B (uses existing free bits in uint32_t). 5th canonical application of `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md` INVARIANT pattern.

**Bit-width invariants:** static_asserted in `ML_Headers/bandit_dispatch_table.hpp` (where `FOREACH_BANDIT_ALGORITHM_COUNT` + `NUM_REGIMES` + `ENSEMBLE_HORIZON_MAX` are visible). Tied to `MASK_ORDER_BANDIT_3BIT == 0x7` so future mask widening cascades automatically.

**Cross-ref:** `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` Stage 3 amendment v1.2 (sibling-array carrier + bit-pack carrier mechanisms for Pattern 4; Order::pre_resolved sub-struct unchanged at 2 fields).

### Decision E: ParseFast.hpp + BanditLearning.hpp explicit cstdint (latent IWYU fix)

**What:** added explicit `#include <cstdint>` to `CoreFrameworks/ParseFast.hpp` + `ML_Headers/BanditLearning.hpp`. Both used `uintN_t` without including cstdint; were relying on transitive include chains (latent IWYU bug).

**Why:** removing an unused-include band-aid from `bandit_dispatch_table.hpp` exposed the chain break. Fixed at root rather than band-aiding. 8 other headers have the same latent IWYU gap (tracked in TECH_DEBT-083 for sweep in `.F.4f` cleanup ship).

### Cross-link to TECH_DEBT entries opened during `.F.4d` coding

- **TECH_DEBT-081** — `.F.4c.3.A` symbol axis residual migration (KIND_STRING + multi-symbol DataStream + ~9 BinanceConfig.symbol consumer migration; triggers post-`.F.4e`)
- **TECH_DEBT-082** — `.F.5` 3 unmigrated fields per-core eligibility audit (`confidence_ic_floor` / `lazy_rebuild_price_threshold_pct` / `exit_threshold`)
- **TECH_DEBT-083** — IWYU hygiene sweep (8 headers use `uintN_t` without direct cstdint; latent)
- **TECH_DEBT-084** — Full symmetric rename of `thompson_bandits` → `buy_thompson_bandits` + FOREACH_BANDIT_SIDE full auto-gen across all 6 per-side symbol families

---

## Tail-latency cost analysis for `.F.4d` framework additions (precise per Caramel pushback 2026-05-16)

Fuzzy phrasings like "negligible" or "doesn't meaningfully contribute" elided the actual non-zero costs. Precise per-source-of-latency breakdown:

### Sources of tail-latency contribution (where the code DOES cost)

**1. Cold start (first call after engine boot)**
- **Cost:** ~30-100 ns one-time per unique callsite (indirect call BTB miss + L1i miss on target fn body)
- **Affects:** first 1-2 slow-path cycles after engine startup
- **Visible at:** p99.99 of the warmup window (the first few cycles of a fresh boot); not visible in steady-state p99/p99.9
- **Total budget impact:** ~1-2 cycles × 100 ns ≈ 200 ns absolute; over a session of millions of cycles this rounds to zero

**2. Cfg-flip at runtime (operator changes `cfg.bandit_algorithm`)**
- **Cost:** ~60-200 ns one-time per flip (1-2 indirect call mispredicts as predictor re-warms for new fn pointer target)
- **Affects:** first 1-2 slow-path cycles after each cfg-flip
- **Frequency:** operator-driven; rare in production (mostly happens during paper-test tuning)
- **Visible at:** p99.99 of the brief window around each flip; not visible in normal operation

**3. Sustained operation (after warmup)**
- **Cost:** ~1-2 ns per reward-dispatch call (predicted indirect call via L1-hot BTB target)
- **Affects:** EVERY reward-attribution call (per-fill or per-cycle slow path)
- **Visible at:** baseline shift of ~1-2 ns on the reward-attribution path latency distribution
- **vs pre-.F.4d:** direct branch with predicted-not-taken was ~similar (1-2 ns); net equivalent
- **Slow-path budget:** 100 µs total; 1-2 ns is 0.001-0.002% utilization; negligible vs budget but technically non-zero

**4. Cache pressure from `EnsembleModelZoo<F>` growth**
- **What grew:** +1024B (`thompson_exit_bandits[NUM_REGIMES]` = 5 × 200B + alignment padding) + 16B (`thompson_update_fn` + `exit_thompson_update_fn` fn-pointer fields)
- **Cost:** GENUINELY UNKNOWN without profile data
- **Could be:** 0 ns (if new fields stay in COLD cluster + don't evict any hot field)
- **Could be:** ~10-50 ns per slow-path cycle (if growth pushes hot fields out of L1 + forces L2 fetches on the slow-path read set)
- **Affects:** slow-path entry latency distribution depending on cache configuration
- **Mitigation:** new fields placed per `cache-layout-discipline-for-hot-side-structs.md` rules (HOT/WARM/COLD cluster discipline) — `thompson_exit_bandits[]` sits next to `thompson_bandits[]` in LARGE HOT arrays section; fn pointers in HOT scalars; padding fields explicit
- **Action:** profile post-paper-test to verify cache pressure within tolerance; flag in HP_REFACTOR.md observation O5 if regression detected

### Sources that DON'T contribute (precise)

**1. Compile-time `if constexpr` branches in leaf reward fns**
- ZERO runtime cost. Template instantiation picks one side at compile; the other branch is dead-code-eliminated. Not present in the binary at all.

**2. Save/Load mirrors (`_SaveExitThompsonState` + `_LoadExitThompsonState`)**
- Boot/shutdown only. Not in any trading path. Disk IO dwarfs any if-statement cost by 6+ orders of magnitude.

**3. State-dependent defensive guards (nullptr checks; init-flag bit-tests; `n_arms < 2` early-returns)**
- Predictor warms up on first call + perfect-predicts forever after. Same target every call; same outcome every call. Affects cold start only (~30-100 ns one-time per guard), zero amortized cost.

**4. Bit-pack accessors (`MBS_OrderBanditActiveState` etc.)**
- Pure shift + mask operations. No branches. ~1 ns per access. Zero tail variance.

### Comparison vs pre-.F.4d behavior

Pre-.F.4d reward-attribution dispatch had per-call branches like:
```cpp
if (cfg.bandit_algorithm == THOMPSON || cfg.bandit_algorithm == BOTH) {
    Thompson_Update(&ezoo->thompson_bandits[r], arm, reward);
}
```

This was:
- Data-dependent control-flow on cfg-stable predicate (predictor warms up + stays correct)
- Same warmup cost on cfg-flip (~60-200 ns one-time)
- Same sustained cost (~1-2 ns predicted branch)
- Plus Class 28 anti-pattern (per H20) + Class 18 mirror risk (per-site drift)

**Net delta `.F.4d` vs pre-`.F.4d`:**
- Warmup + sustained costs: roughly equivalent
- Cache pressure: NEW (~1KB growth on EnsembleModelZoo) — uncertain magnitude, needs profile
- Class 28 + Class 18 risks: STRUCTURALLY CLOSED at attribution surface
- Future-maintenance cost (adding a 6th bandit algorithm): O(N) per-site → O(1) registry row

The framework trades a small POTENTIAL cache-pressure cost (unmeasured) for elimination of dispatch-family bug classes + 1-row-mechanical extensibility. Worth confirming via profile post-paper-test; if cache pressure shows regression, HP_REFACTOR.md observation O5 + cluster-placement rework triggers.

### Triggers for re-evaluation

- **Paper-test surfaces slow-path p99 regression** → profile cache miss rates around `EnsembleModelZoo<F>` field accesses; consider relocating fn-pointer fields out of HOT cluster if they evict hotter fields.
- **Adding a 3rd per-side axis (per-symbol Thompson?)** triggers TECH_DEBT-084 evaluation + further struct growth analysis.
- **Operator reports cfg-flip stutter** → could indicate predictor warmup is more visible than expected; pre-warm by calling each algorithm's apply_fn once at boot.
