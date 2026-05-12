# /trace-deps report — v5.15.5 per-horizon TP/SL serving — 2026-05-12

Plan: `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.5-per-horizon-tp-sl-serving.md`
Verdict: **YELLOW with one RED must-fix** — plan is largely sound, references existing
patterns + auto-populate registries correctly, but has 3 blocking finds + 4 review items.

---

## Dependency chain map per surface

### Surface 1 — Per-arm barrier load (Phase A)
- `EnsembleModelZoo<F>` struct at `ML_Headers/CoreModelZoo.hpp:912` (NOT :919 — plan
  drift; :919 is `exit_predictor_count` field, struct opens at :912 with `alignas(64)`)
- `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG` at `ML_Headers/StampBoundModelConstRegistry.hpp:278`
  — `label_tp_pct` + `label_sl_pct` rows ALREADY EXIST at lines 366-369. Phase A
  Step 0 verifies this; verification PASSES — no registry extension needed.
- `STAMP_BOUND_MODEL_CONST_AUTOPOPULATE` companion at registry — auto-flows new
  reads. PASS.
- `CoreModelZoo_TryLoadRole` at `CoreModelZoo.hpp:120` — sig: 9 args (handle, dir,
  role_name, backend, secret, gap_thresh, strict, ack_drift, expected_feat_mask,
  expected_horizon, cfg_ptr). Returns int. PASS.
- `ENSEMBLE_HORIZON_MAX = 8` at `CoreModelZoo.hpp:902`. PASS.

### Surface 2 — Slow-path blend (Phase B)
- `weights_buf[]` declared at `StrategyParameters.hpp:892` — LOCAL TO NESTED IF-BLOCK
  (`if (use_weighted && ezoo->initialized_bandits)`). Plan claims read at line
  ~1029 (post-Ridge finalize, INSIDE the same block). PASS in source scope.
- `tp_pct = config->ml_tp_pct` at lines 1259-1260. PASS.
- `out->tp_pct = tp_pct` at lines 1431-1432. PASS.
- `mctx`, `ezoo`, `config` all in scope at 1259. PASS.

### Surface 3 — PostLoadSetup registry (Phase A bundle)
- `FOREACH_ENSEMBLE_POST_LOAD` at `CoreModelZoo.hpp:2474` — **9 existing entries**
  (`init_bandits`, `init_exit_bandits`, `blend_mode`, `disabled_horizons`,
  `load_bandit_state`, `save_interval`, `load_exit_bandit`, `init_thompson_bandits`,
  `load_thompson_state`). `FOREACH_ENSEMBLE_POST_LOAD_COUNT = 9`.
  Plan claims "7 entries; +1 for barrier-pack" — **count drift; current is 9 → 10
  after extension**.
- `EnsembleModelZoo_IsReadyForInference` at line 2533 — contract predicate; +1
  entry per new step.
- Tuple shape `X(name, expr)` — 2-tuple. Adding 1 row with `expr =
  EnsembleModelZoo_LoadPerArmBarriers(ezoo)` is mechanical. PASS.

### Surface 4 — Slow-path gate registry (Phase B helper)
- `FOREACH_SLOW_PATH_GATE` at `CoreFrameworks/SlowPathGateRegistry.hpp:69` —
  10 existing entries (LADDER, CONFIDENCE, COMPOSITE, RIDGE_WITHIN, EXIT_BLENDER,
  RIDGE_ONLINE_CORR, THOMPSON_ACTIVE, BANDIT_BOTH, LAZY_REBUILD, WS_FLATTEN).
  `static_assert(GATE_SLOW_PATH_TOTAL_COUNT <= 16)` caps at 16 → **6 bits
  headroom; plan adds 2 (BARRIER_BLEND_ACTIVE + BARRIER_SHADOW_ACTIVE)**. PASS.

### Surface 5 — Calibration log column registry
- `FOREACH_CALIB_LOG_COL` at `DataStream/CalibLogColRegistry.hpp:56` — 9 columns,
  tuple shape `X(name, fmt, expr)` (3-tuple). **NO emit_when predicate** in
  current tuple. Plan claims "5 new columns need entry order + emit_when
  predicates" — **DRIFT**: registry tuple has no predicate slot. Plan must
  either (a) extend tuple shape to add `emit_when` column (touches header
  emitter + row emitter macros) OR (b) drop the `emit_when` claim and accept
  always-emit (zero values for inactive shadow mode).

### Surface 6 — Bandit arm_names extraction (Rule 1 cache-layout)
- `BanditState.arm_names[8][32]` at `BanditLearning.hpp:70` — 256 bytes/regime ×
  NUM_REGIMES = 1280 bytes/ezoo across all bandits arrays.
- Read sites:
  - `BanditLearning.hpp:99` (Bandit_Init initial-name), `:112`
    (Bandit_SetArmName), `:337` (Bandit_GetProbabilities log), `:427`/`:429`
    (Bandit_Save JSON writer)
  - `CoreModelZoo.hpp:1380, 1390, 1427, 1437` (Init + SetArmName post-init)
  - `EngineTUI.hpp:719-730` (PerCoreSnap copy: `ctrl->bandit.arm_names[i]`)
  - `EngineTUI.hpp:668` (PerCoreSnap field `bandit_arm_names[5][32]`)
  - `DashboardPanels.hpp:1737-1739` (reads via `s->ml.bandit_arm_names`)
- Plan claim "MLStatusPanel/DashboardPanels reference `bandits[].arm_names`
  directly" — **PARTIALLY INCORRECT**: GUI reads via PerCoreSnap.bandit_arm_names,
  not directly. Plan should clarify the actual chain: extraction touches
  Bandit_* internal sites + the EngineTUI snapshot publish path; GUI side is
  untouched (just renames upstream).
- v5.14.10.B already added `exit_bandits[NUM_REGIMES]` + `thompson_bandits[NUM_REGIMES]`
  in EnsembleModelZoo — so 3 parallel bandit arrays × NUM_REGIMES bandits each ×
  256 bytes arm_names = ~3.75KB cache pollution. Rule 1 extraction is high-value.

### Surface 7 — Per-core override
- Plan cites `core_disabled_horizons[16][128]` at `ControllerConfig.hpp:1015` as
  per-core convention precedent. PASS.
- Per-core parsing convention (`core_N_<field>`) at `ControllerConfig.hpp:2714`+.
  PASS. Q3 (Phase B) — recommend YES, defer to v5.15.6 if scope tight (plan
  notes this).

### Surface 8 — Symmetric bandit_algorithm mode 3
- `FOREACH_BANDIT_ALGORITHM` at `BanditAlgorithmRegistry.hpp:87` — 3 modes
  (EXP3=0, THOMPSON=1, BOTH=2). Adding mode 3 (THOMPSON_DRIVES_EXP3_SHADOW) =
  1 row + 1 `BanditAlgo_<NAME>_Apply` function. PASS.

---

## Mirror data-flow findings (Class 18 risk)

Plan mirrors v5.14.10.B Thompson dual-mode (cfg.bandit_algorithm=2) to barrier
blend mode shadow (BOTH_BLEND_DRIVES / BOTH_DOMINANT_DRIVES). Walk per Step 6:

**Source range:** `bandit_algorithm == 2` cfg=2 dual-mode at `BanditAlgorithmRegistry.hpp:99-102`
(slow-path gate registry) + `BanditAlgo_Both_Apply` in registry (forward-declared
at :74).

**Data sources read by source:**
- `cfg.bandit_algorithm` → `cfg.barrier_blend_mode` (NEW; plan adds). PASS.
- `BanditState* exp3` + `ThompsonBanditState* thompson` → both per_arm_barriers
  (NEW; plan adds). PASS.
- `weights_out[]` + `chosen_arm_out` → `(actual_tp, shadow_tp, ...)` ring slots
  (NEW; plan adds `BarrierShadowRing`). PASS.

**Call sequence mirror (Step 6.A):**
Plan claims shadow logs via "ring buffer at EnsembleModelZoo similar to
`exit_reward_ring`". Source code at `CoreModelZoo.hpp:1160-1180`
(EnsembleModelZoo_RecordPrediction) is the precedent. Plan does NOT enumerate
which existing helper to mirror or whether ring access is per-cycle slow-path or
per-trade fill-time. **YELLOW**: Plan should cite the specific helper signature
to mirror (recommend `EnsembleModelZoo_RecordPrediction` pattern).

---

## Call sequence audit (PostLoadSetup, slow-path gate, calib log)

| Registry | Existing entries | Plan adds | Total | Headroom |
|---|---|---|---|---|
| FOREACH_ENSEMBLE_POST_LOAD | **9** (plan claims 7 → drift) | 1 (load_per_arm_barriers) | 10 | unbounded (registry-driven) |
| FOREACH_SLOW_PATH_GATE | 10 | 2 (BARRIER_BLEND_ACTIVE, BARRIER_SHADOW_ACTIVE) | 12 | 4 (cap=16) |
| FOREACH_CALIB_LOG_COL | 9 (no emit_when slot) | 5 (with emit_when — **tuple shape mismatch**) | 14 | unbounded |
| FOREACH_BARRIER_BLEND_MODE | 0 (new registry) | 5 modes | 5 | unbounded |
| FOREACH_BANDIT_ALGORITHM | 3 | 1 (mode 3) | 4 | unbounded |
| FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG | label_tp_pct/sl_pct ALREADY PRESENT | 0 | n/a | n/a |

---

## Cross-component plumbing verification

Chain: `verify_model_stamp populates sr.label_tp_pct/sl_pct →
STAMP_MODEL_CONST_AUTOPOPULATE writes to handle → TryLoadRole caller-side
extracts to ezoo->per_arm_buy_tp_pct[handle_idx] → ML_BuildParameters reads
weights_buf[]+per_arm_barriers[] → blends/picks dominant → out->tp_pct →
ParameterSlot seqlock → BG/SG_Evaluate hot path consumes`.

**Gaps:**
1. **Plan misattributes Phase A Step 2** ("In CoreModelZoo_TryLoadRole: when
   stamp has has_label_tp_pct, extract into ezoo"). TryLoadRole sig only sees
   `handle`, NOT ezoo. The extraction must happen at the CALLER scope in
   `EnsembleModelZoo_LoadFromCfg`'s role-loading loop around line
   `CoreModelZoo.hpp:1607-1626`. Plan needs to relocate the cited extraction
   site.
2. **Plan's Phase B Step 1 code excerpt cannot compile as-pasted.** `weights_buf[]`
   is declared at `StrategyParameters.hpp:892` inside a deeply-nested
   `if (use_weighted && ezoo->initialized_bandits)` block. Plan claims to use
   it at line 1259-1260 which is OUTSIDE that scope. Plan needs to either:
   (a) lift `weights_buf` declaration up to ML_BuildParameters function scope,
   or (b) compute `dominant_h` INSIDE the use_weighted block + pass a local
   variable down to the TP/SL assignment site. Either works; plan must specify.

---

## Blast radius for each existing-symbol modification

- `ezoo->active`, `ezoo->initialized_bandits`, `ezoo->initialized_exit_bandits`,
  `ezoo->initialized_thompson_bandits` → bit-packed into `init_flags`:
  **52 read/write sites across .hpp/.cpp** (rg-counted). High touch count;
  CLAUDE.local.md memory `feedback_avoid_substring_replace_all_on_member_access.md`
  applies — needs `BITMAP_IS_SET(ezoo->init_flags, MASK_*)` per-site targeted
  edit, not naive replace_all.
- `BanditState.arm_names` extraction → 4 BanditLearning.hpp sites + 4
  CoreModelZoo.hpp sites + 2 EngineTUI.hpp sites + 0 GUI sites (GUI reads via
  PerCoreSnap, untouched).
- `EnsembleModelZoo` field reorganization (Hot/Warm/Cold per Rule 4) — sizeof
  + offsetof asserts must follow; v5.15.4 already has `static_assert(sizeof
  (EnsembleModelZoo<64>) % 64 == 0)` at `CoreModelZoo.hpp:1040`. Test must
  hold after reorg.

---

## Verdict: **YELLOW with one RED must-fix**

### RED (BLOCKING — plan must update before Phase B coding):

1. **Phase B Step 1 scope bug** — `weights_buf[]` is out-of-scope at line 1259.
   Plan must specify the dominant_h computation site (inside use_weighted
   block) + a local var passing pattern OR a function-scope `weights_buf` lift.

### YELLOW (review; update before sub-ship A starts):

2. **Phase A Step 2 site misattribution** — extraction logic belongs in
   `EnsembleModelZoo_LoadFromCfg` caller scope (around line 1607-1626), NOT
   inside `CoreModelZoo_TryLoadRole` (which has no ezoo arg).
3. **FOREACH_CALIB_LOG_COL tuple shape** — registry has no emit_when slot.
   Plan must extend tuple shape (touches header + row emit macros) OR drop
   emit_when claim.
4. **PostLoadSetup count drift** — plan says "7 → 8"; actual "9 → 10".
   Documentation-only fix.
5. **ml_cfg_flags cohort-audit re-verification** — `per_horizon_barrier_blend`
   is a BOOLEAN; its sibling cohort is the ML boolean toggles ALREADY in
   `ml_cfg_flags` (confidence_enabled, composite_enabled, use_exit_model,
   lazy_rebuild, ridge_within_horizon, etc.), NOT the cfg-float `ml_tp_pct/
   ml_sl_pct` values. Per CLAUDE.local.md 2026-05-11 cohort-audit rule, the
   eligible cohort verdict is "migrate alongside" — plan currently defers to
   v5.15.6, which contradicts intra-family consistency.
6. **Mirror citation completeness** — `BarrierShadowRing` should explicitly
   cite the precedent helper sig (recommend `EnsembleModelZoo_RecordPrediction`
   at `CoreModelZoo.hpp:1160-1180` pattern).

### GREEN (verified):

- All cited DESIGN_SPECS docs exist in workspace (15/15).
- All registry headers cited exist; all X-macro tuple shapes (where unchanged)
  are PASS for proposed entry additions.
- `label_tp_pct` + `label_sl_pct` in PRE_CFG registry already present — Phase A
  Step 0 work is already done.
- Bandit algorithm mode 3 extension is clean (1 row, registry-driven).
- Slow-path gate bit headroom (6 free, plan uses 2). PASS.
- BITMAP_* API for `init_flags` is the canonical pattern (CLAUDE.md item 20).

---

## Recommendations

Before Phase A coding:
- Fix items 2, 3, 4, 5 (documentation/scope updates).

Before Phase B coding:
- **Fix item 1 (RED) — specify weights_buf scope strategy.**

Plan stays in YELLOW until items 1-5 are updated; item 6 is a review nice-to-
have. Once 1 is resolved + 2-5 are clarified, plan is GREEN for sub-ship A.
