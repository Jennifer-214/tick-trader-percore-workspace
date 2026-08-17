---
type: agent-report
agent_class: i-class
date: 2026-08-17
engine_head: a160123
directive: "For each of the 18 stamp wire keys with no production producer: live consumer? behaviour when absent? classify (a) live defect / (b) inert / (c) operator-call"
status: verbatim-at-receipt
---

> Saved VERBATIM at receipt. Orchestrator wrote the file; the agent was read-only.
> Orchestrator verification notes are in `README.md`, NOT inline — the report is unedited.

---

# Stamp EMIT-path audit — the 18 wire keys with no production producer

**Surface:** model-stamp HMAC-signed body emit (H9) · engine root `/home/caramel/code/FoxML_Trader_v2`
**Date:** 2026-08-17 · HEAD `a160123` (branch `feat/v5.15-live-readiness`)
**Roots searched (explicitly named, per Landmine 19):** `ML_Headers/ CoreFrameworks/ Backtest/ DataStream/ GUI/ Strategies/ MemHeaders/ FixedPoint/ tests/ tools/ scripts/ main.cpp foxml_suite.cpp` + the on-disk stamp corpus under `models/`.

## Headline

**The brief is CORRECT on all counts — count, key list, and producer set. I independently re-derived it and found no missed producer.** But the classification is not 18-inert-tidiness: **10 of the 18 are class (a)**, and one of them — the `inference_cfg` group bit — is the single input to **two independent train→serve cfg-drift gates** at HEAD, one of which carries three `REFUSE_STRICT` rows. It is the `feature_mask` shape again, one level up: not one gate, a whole gate *layer*.

**Additionally I found a defect the brief did not scope, with the same root cause and a higher live severity:** the `.B.3` cfg-derived migration built the emit half and the parse half but **never built the parse→handle half**, so ~30 cfg-derived handle fields are permanently zero and the drift rows that read them compare `0` against live cfg. Two `REFUSE_STRICT` rows are armed to fire on **every** model load under default cfg. That is in § ADJACENT below and it is the thing I would verify first.

---

## Part 0 — Verification of the brief's arithmetic (independent re-derivation)

| Claim | Verdict | Evidence |
|---|---|---|
| `FOREACH_STAMP_BOUND_MODEL_CONST` at `StampBoundModelConstRegistry.hpp:506` composes PRE_CFG (`:289`) + POST_CFG (`:407`) | **CONFIRMED** | Hand-counted rows: PRE_CFG = 22, POST_CFG = 24, total 46 |
| Emit walk at `ModelInference.hpp:2258-2265` / `:2291-2298`; per-row gate `STAMP_EMIT_CHECK_HAS_##group(name)` | **CONFIRMED** | Gate expression is `if (inf && STAMP_EMIT_CHECK_HAS_##group(name) && n > 0 && ...)` — `ModelInference.hpp:2259` |
| Dispatchers at `StampBoundModelConstRegistry.hpp:742-749`; grouped row ⇒ one shared bit | **CONFIRMED** | `:743` `STAMP_EMIT_CHECK_HAS_inference_cfg(name) → STAMP_HAS(*inf, inference_cfg)` |
| 17 distinct bits set by production producers in `StampHelper.hpp` | **CONFIRMED** | `:250 :268 :295 :320 :325 :334 :350 :354 :356 :375 :385 :391 :401 :409 :413 :419 :421` = 17 |
| 18 wire keys never emit | **CONFIRMED** | `enum StampHasFlagBit` (`:549-588`) allocates **23** bits post-fees-removal (6 group + 7 PRE standalone + 10 POST standalone). 23 − 17 = **6 unset bits**, covering 9 + 5 + 4 = **18 rows** |

**Independent producer sweep (three orthogonal spellings, so a macro-pasted setter cannot hide):**
1. `rg "STAMP_SET\s*\("` across all roots — 17 `inf`-target sites, all in `StampHelper.hpp`; the only other engine-source sites are `NodeModelZoo.hpp:378-478` (`*handle` target = **consume** side) and `ModelInference.hpp:1724` (`r` target = **parse** side).
2. `rg "has_flags"` across engine source — only struct declarations, the macro definitions, and `static_assert`s. **No direct `BITMAP_SET`/`|=` on `has_flags` anywhere.**
3. `rg "MASK_inference_cfg\b|MASK_environment_meta|MASK_overlay_hash|MASK_effective_hash|MASK_scaler_fit_data_hash|MASK_removal_reasons_csv"` across all roots including `tests/` and `tools/` — **zero engine-source hits outside the `#define`s themselves**. The only hits are in `tests/controller_test.cpp` (`:24018 :24022 :24028 :24035 :24061 :28001`).

The `NODE_STATE_FLAG_SET`-style indirection the brief worried about is closed by sweep (3): a token-paste producer would still have to name the `MASK_` constant somewhere in the expansion chain, and none does.

**Empirical cross-check against the wire itself** — 16 stamps on disk, `models/**/*.stamp`:
```
stamp_format_version:  16 × "=1"        (all 16)
overlay_hash:           0
effective_hash:         0
scaler_fit_data_hash:   0
removal_reasons_csv:    0
environment_cpu_model:  0
inference_cfg_*:       16   ← the PRE-.B.3 walker emitted them; see § CORRECTIONS
```

---

## Part 1 — The 18-key table

Legend: **(a)** LIVE DEFECT — a consumer's guarantee is silently void · **(b)** INERT · **(c)** NEEDS-OPERATOR-CALL.

| # | key | consumer file:line | behaviour when absent | class | severity |
|---|---|---|---|---|---|
| 1 | `inference_cfg_ml_tp_pct` | *no value consumer.* **The group bit** `MASK_inference_cfg` is read at `MemHeaders/CfgGateRegistry.hpp:814` (→ every row of `drift_check_from_derived`) and at `ML_Headers/CfgDriftCheckRegistry.hpp:257,261,266,332` and at `ML_Headers/NodeModelZoo.hpp:458` | Bit stays 0 ⇒ `lookup_drift` returns `stamp_has_inference_cfg` = false (`CfgGateRegistry.hpp:197,205`) ⇒ **entire cfg-derived drift walk vacuous**; 4 `FOREACH_CFG_DRIFT_CHECK` rows skip; sr→handle copy at `:458-468` skipped | **(a)** | **CRITICAL** |
| 2 | `inference_cfg_ml_sl_pct` | ″ | ″ | **(a)** | CRITICAL |
| 3 | `inference_cfg_barrier_blend_mode` | ″ | ″ | **(a)** | CRITICAL |
| 4 | `inference_cfg_per_horizon_barrier_blend` | ″ | ″ | **(a)** | CRITICAL |
| 5 | `inference_cfg_bandit_algorithm` | ″ | ″ | **(a)** | CRITICAL |
| 6 | `inference_cfg_thompson_mu_prior` | ″ | ″ | **(a)** | CRITICAL |
| 7 | `inference_cfg_thompson_precision_prior` | ″ | ″ | **(a)** | CRITICAL |
| 8 | `inference_cfg_thompson_precision_obs` | ″ | ″ | **(a)** | CRITICAL |
| 9 | `inference_cfg_thompson_exp3_blend_alpha` | ″ | ″ | **(a)** | CRITICAL |
| 10 | `overlay_hash` | `ML_Headers/FeatureRegistryOverlay.hpp:172` — `if (!STAMP_HAS(*h, overlay_hash)) return;` inside `FeatureOverlay_PostLoadVerify`. Production callers: `CoreFrameworks/EngineCommon.hpp:422`, `CoreFrameworks/EngineSharded/Run.hpp:1933`, `:1996`. Propagated `NodeModelZoo.hpp:428-434` | Silent `return` for **every** handle ⇒ the `.overlay.json` sidecar tamper check never runs. The 3-layer fingerprint guarantee (`FeatureRegistryOverlay.hpp:27` "stamp body's overlay_hash is HMAC-protected") is structurally unreachable — no `StampArgs` field exists to carry it (`StampHelper.hpp:84-133`) | **(a)** | **MED** — real void, **blast radius today = 0** (0 `.overlay.json` on disk; `tools/feature_overlay.py:220-221` only *prints* the values for an operator to paste, and no paste path exists) |
| 11 | `effective_hash` | Only `NodeModelZoo.hpp:435-441` (copy sr→handle). **Nothing reads `handle->effective_hash`** anywhere | Copy skipped; field stays `""`. No behavioural change | **(b)** | LOW |
| 12 | `scaler_fit_data_hash` | **NONE.** Zero references outside the registry row (`:440-442`), the auto-genned struct fields, and tool-owned `[STRADDLE]` tags | Nothing | **(b)** | LOW — **but see the false-comment finding below** |
| 13 | `removal_reasons_csv` | **NONE** | Nothing | **(b)** | LOW |
| 14 | `environment_tf_version` | **NONE** | Nothing | **(b)** | LOW |
| 15 | `environment_pytorch_version` | **NONE** | Nothing | **(b)** | LOW |
| 16 | `environment_cuda_version` | **NONE** | Nothing | **(b)** | LOW |
| 17 | `environment_cpu_model` | **NONE** | Nothing | **(b)** | LOW |
| 18 | `environment_libgomp_version` | **NONE** | Nothing | **(b)** | LOW |

No key classified **(c)**. Every one resolved cleanly to (a) or (b) on code evidence.

---

## Part 2 — the (a) LIVE DEFECTS in full

### D-1 · CRITICAL — the `inference_cfg` group bit voids the entire stamp↔cfg drift gate layer

The 9 keys are individually inert *as values* (nothing reads `sr.inference_cfg_ml_tp_pct`). They are load-bearing **collectively, as the only producer of `MASK_inference_cfg`**. That bit is the sole presence-signal for the whole train→serve cfg-parity apparatus. Full chain, every link cited:

**Link 1 — the bit's only producer is the parser, keyed on a group-member wire key**
`ModelInference.hpp:1757-1763`, the POST_CFG parse walk:
```c
else if (strcmp(key, #name) == 0) { tt::stamp_parse_field(r.name, val, fmt); STAMP_PARSER_SET_HAS_##group(name); }
```
`STAMP_PARSER_SET_HAS_inference_cfg(name) → STAMP_SET(r, inference_cfg)` (`StampBoundModelConstRegistry.hpp:759`). No group-member key in the stamp ⇒ bit never set. `ModelStampResult r{}` zero-inits it (`ModelInference.hpp:1612`).
Note `inference_cfg_bandit_blend_ratio` does **not** rescue this — it is `group = _` (`StampBoundModelConstRegistry.hpp:301`), so it sets `MASK_inference_cfg_bandit_blend_ratio` (bit 6), a **different** bit from `MASK_inference_cfg` (bit 0). `PARSE_STAMP_CFG_TO_DERIVED` (`ModelInference.hpp:1746`) sets only the per-field `r.has_<name>` bytes (`CfgGateRegistry.hpp:643`), never the group bit.

**Link 2 — gate A: the framework drift walker, ALL ~30 cfg-derived rows**
`NodeModelZoo.hpp:304`:
```c
DRIFT_CHECK_FROM_DERIVED(failure_flags, sr, cfg, sr.inference_cfg_drift_count, sr.reason, sizeof(sr.reason));
```
expands (`CfgGateRegistry.hpp:811-819`) passing `STAMP_HAS((sr), inference_cfg)` as `stamp_has_inference_cfg`. Inside `drift_check_from_derived`:
- per-node rows: `cfg_gate::lookup_drift(...)` → `CfgGateRegistry.hpp:197` `default: return stamp_has_inference_cfg;` (and `:194` `return stamp_has_inference_cfg && (expr);`)
- global rows: `:205` / `:202`, identical
- ml-cfg-flag rows: `:568` `const bool _trigger = stamp_has_inference_cfg & _drifted;`
- gate-cfg-flag rows: `:588`, identical

⇒ `_trigger` is **always false for every row**. `sr.inference_cfg_drift_count` stays 0. `NodeModelZoo.hpp:305-307` `if (sr.inference_cfg_drift_count > 0) sr.valid = 0;` — **never fires**. The held-out gate's REFUSE arm (`:311-315`) can never be reached via cfg drift.
**Cohort size voided:** 30 rows carry `STAMP_BOUND_CFG_DERIVED` in `CfgFieldRegistry.hpp` (27 per-node `:665-789`, 3 global `:469,:478,:488`) plus the ML/gate flag rows. Named members include `ml_tp_pct`, `ml_sl_pct`, `ridge_lambda`, `ridge_cost_penalty`, `ridge_min_ic_floor`, `winsor_pct_low/high`, `thompson_mu_prior`, `thompson_precision_prior/obs`, `thompson_exp3_blend_alpha`, `bandit_algorithm`, `bandit_blend_ratio`, `confidence_*`, `risk_degradation_curve`, `risk_*_threshold`, `fee_rate_maker/taker`, `barrier_blend_mode`, `trading_mode`, `gap_acceptable_threshold`.

**Link 3 — gate B: `FOREACH_CFG_DRIFT_CHECK`, 4 of 18 rows, 3 of them REFUSE_STRICT**
Walked at `CoreFrameworks/ModelValidation.hpp:222` inside `NodeModelZoo_ValidateAgainstCfg`; production callers `EngineCommon.hpp:416`, `Run.hpp:1915`, `Run.hpp:1980`. Rows gated on `STAMP_HAS(*h, inference_cfg)`:

| row | severity | file:line |
|---|---|---|
| `confidence_threshold_scale` | **REFUSE_STRICT** (Tier 1) | `CfgDriftCheckRegistry.hpp:255-258` |
| `barrier_gate_enabled` | **REFUSE_STRICT** (Tier 1) | `:259-262` |
| `confidence_hard_block_threshold` | WARN_ALWAYS (Tier 2) | `:264-267` |
| `per_horizon_barrier_blend` | **REFUSE_STRICT** (Tier 1) | `:330-333` |

The handle's bit comes only from `NodeModelZoo.hpp:458` `if (STAMP_HAS(sr, inference_cfg)) { STAMP_SET(*handle, inference_cfg); ... }`. Never set ⇒ these four never evaluate.

**Link 4 — the same guard also gates the value copy.** `NodeModelZoo.hpp:458-468` is the *only* writer of `handle->confidence_threshold_scale`, `handle->barrier_gate_enabled`, `handle->confidence_hard_block_threshold`. So even a forced-true gate would compare `0` vs cfg.

**CAPITAL impact.** A model trained under `ml_tp_pct = 2.0` / `thompson_precision_prior = 1.0` / `barrier_blend_mode = 2` and then served under different values loads **clean**, with no WARN and no REFUSE, in every mode including `held_out_gate_strict=1`. Serving-time barrier distances, bandit posteriors, ridge blending and fee-aware gating all silently diverge from the calibration the model was fit to. This is precisely the failure `FAILURE_MASK_cfg_binding_drift` and the `acknowledge_inference_cfg_drift` operator ack exist to make impossible to hit by accident.

**DETERMINISM impact.** Train→serve parity is unverified for the whole cfg-derived cohort. The `[cfg-drift]` log line an operator would look for is unreachable; `NodeContextDisplayMeta.cfg_drift_tier1_count` / `tier2_count` (`ModelValidation.hpp:256-257`) read 0 not because there is no drift but because nothing was compared. `NODE_STATE_FLAG_CLR(CFG_DRIFT_STRICT_REFUSED)` (`:263`) is a clean bill of health that was never issued.

**Why every guard is green.** `check_meta_registry.py` → GREEN (69/69 registries enrolled, Checks 1-4 pass). `check_identifier_retirement.py` → GREEN (94 identifiers match ledger). `CfgFieldRegistry.hpp:1488-1497` static-asserts cohort coverage ≥ 20 — a **membership** count, blind to reachability. This is Class 51 (vacuously-green guard) sitting on top of Class 58 sub-shape B (gate-reachability): the rows are right and the gate reading them is unreachable.

### D-2 · MED — `overlay_hash`: a tamper-detection guarantee with no producer at all

`FeatureOverlay_PostLoadVerify` (`FeatureRegistryOverlay.hpp:161-229`) is genuinely wired into production at three sites. Its per-handle body opens `if (!STAMP_HAS(*h, overlay_hash)) return;  // legacy stamp; silent skip` (`:172`). The bit's only source is `NodeModelZoo.hpp:428`, gated on the stamp key, which no producer emits. So the "sidecar tampered or wrong sidecar copied next to model file" detection at `:200-208` is unreachable.

**Distinguishing this from the `inference_cfg` case:** this one is a **never-built** capability rather than a **broken** one. `StampArgs` (`StampHelper.hpp:84-133`) has no `overlay_hash` / `effective_hash` field at all — the emit half was never plumbed. `tools/feature_overlay.py:220-221` literally prints `emit these to stamp body as: overlay_hash=<hex>` with no consumer for that instruction. And there are **zero** `.overlay.json` sidecars on disk. Live impact today is nil; the finding is that the guarantee documented at `FeatureRegistryOverlay.hpp:20-30` cannot hold. Correct home is the unwired-capability register (`plans/v5.15-live-readiness/plan_checks/2026-08-16-unwired-capability-register.md`), not a hotfix.

### Comment-truth finding (separate class, worth a line in the ledger)

`ML_Headers/StampBoundModelConstRegistry.hpp:438-439`:
```
/* scaler_fit_data_hash: SHA256 of training data slice used to fit scaler.   */
/* trainer hashes features_train.tobytes(); verifier WARN/REFUSE on mismatch. */
```
**There is no verifier.** Zero references to `scaler_fit_data_hash` outside the registry row, the auto-genned struct fields, and tool-owned `[STRADDLE]` tags. This is the guard-or-tool-existence class from `DOCS/SUBAGENT_ARMING.md` § 2.5 — "highest severity of the family: it doesn't just misinform, it manufactures confidence and stops anyone looking." Suggested correction: `/* scaler_fit_data_hash: RESERVED — no producer and no verifier exist at HEAD. */`. By contrast `:443-444` ("read-only forensic field; no enforcement") for `removal_reasons_csv` is **accurate** and should be left alone.

---

## Part 3 — ADJACENT finding (outside the named 18; same root cause; verify this FIRST)

**The `.B.3` cfg-derived migration has no parse→handle leg.** Exhaustive enumeration of every `handle->` assignment in `NodeModelZoo.hpp` yields exactly 20 targets — `training_poll_interval`, `xgb_*` (8), `build_flags_hash`, `xgb_train_nthread`, `label_*` (3), `scaler_sha256`, `overlay_hash`, `effective_hash`, `training_timestamp_us`, `run_name`, `confidence_threshold_scale`, `barrier_gate_enabled`, `confidence_hard_block_threshold`, `inference_cfg_bandit_blend_ratio`, `model_num_outputs`, `scaler_load_failed`.

**Not one cfg-derived cohort field is among them.** But `ModelHandle` *declares* them all — `STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN()` at `ModelInference.hpp:444` — and `FOREACH_CFG_DRIFT_CHECK` *reads* them. So:

| drift row | reads | actual handle value | cfg default | gate | fires? |
|---|---|---|---|---|---|
| `thompson_precision_prior` (`CfgDriftCheckRegistry.hpp:282-285`, **REFUSE_STRICT**) | `h->thompson_precision_prior` | **0** (never written) | **1.0** (`CfgFieldRegistry.hpp:731`) | `COHORT_GATE_BANDIT_ENABLED` = `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)` (`MlCfgFlagRegistry.hpp:143`), **default 1 since 2026-08-16** (`ControllerConfig.hpp:2012`) | **YES — Tier 1** |
| `thompson_precision_obs` (`:286-289`, **REFUSE_STRICT**) | `h->thompson_precision_obs` | **0** | **1.0** (`CfgFieldRegistry.hpp:734`) | same | **YES — Tier 1** |
| `bandit_blend_ratio` (`:268-271`, WARN) | `h->bandit_blend_ratio` — note this is the **unprefixed** auto-genned field, *not* the `inference_cfg_bandit_blend_ratio` that `NodeModelZoo.hpp:471` populates | **0** | **0.5** (`CfgFieldRegistry.hpp:669`) | same | **YES — Tier 2** |

The `COHORT_GATE_*` macros read `cfg` only (`MlCfgFlagRegistry.hpp:129-144`); they do **not** consult `STAMP_HAS`, so unlike D-1 these rows are reachable — they just compare against a field nothing ever fills. Consequence under `held_out_gate_strict=1`: `tier1_refused_count > 0` → `ModelValidation.hpp:267-275` returns `-1` → at the two hot-swap sites `Run.hpp:1923` / `:1990` that sets `NODE_STATE_FLAG_SET(MODEL_LOAD_FAILED)` and degrades the node. (At the boot site `EngineCommon.hpp:416` the return value is **discarded** — the comment at `:410` says "engine continues (TODO v5.10: free + refuse)" — so boot gets logs + `FAILURE_MASK_cfg_binding_drift` + `CFG_DRIFT_STRICT_REFUSED` but no refusal.)

**This is a falsifiable prediction, and it is the cheapest thing on this page to check:** boot the engine with any loadable model and `grep '\[cfg-drift\]'` on stderr. If lines like `thompson_precision_prior stamp=0 cfg=1` appear, the finding is confirmed by execution rather than by reading. **I did not run this** — I am read-only and could not safely produce a v3 stamp.

Root cause is shared with D-1: `.B.3` moved the cfg-derived cohort onto framework walkers for **emit** (`ModelInference.hpp:2280-2284`) and **parse** (`:1746`) and left both the group-bit producer and the parse→handle propagation behind. Class 58 sub-shape C (registry is SSoT for a format whose consumers duplicate it by hand).

---

## Part 4 — CORRECTIONS TO THE BRIEF

**C-1 (material, changes the framing). The 9 `inference_cfg_*` keys are not "never emitted, therefore inert" — their absence is what makes an entire gate layer vacuous.** The brief's own list treats them as one bullet among three. They are the single highest-severity item on the page. The mechanism is indirect and easy to miss: no consumer reads their *values*, so a value-oriented trace returns "no consumer" and stops. The consumer is the **presence bit** their emission would set.

**C-2 (material, changes the "never" quantifier). All 16 stamps on disk DO carry `inference_cfg_*` keys** — they were emitted by the pre-`.B.3` `INFERENCE_CFG_AUTOPOPULATE` walker (see `models/classification/5.15_testing_horizon_17500/barrier.json.stamp:40-43`, `inference_cfg_ml_tp_pct=0` … ). So the accurate statement is **"never emitted by any stamp the CURRENT emitter can produce"**, not "never emitted". This matters because it changes the timeline of the defect:
- Those 16 are all `stamp_format_version=1`, below `STAMP_FORMAT_VERSION_EPOCH_FLOOR = 3` (`ModelInference.hpp:166`), so they hard-REFUSE at `:1805-1813`.
- **But the epoch-floor check sits at `:1805`, AFTER the parse loop ends at `:1766`.** So for a legacy stamp the parser *does* set `MASK_inference_cfg`, and then `r.valid = 0`. Under `held_out_gate_strict=0` the model still loads (`NodeModelZoo.hpp:317-320` warn-and-continue), and `if (have_sr)` at `:363` still runs the copy block — so `STAMP_HAS(sr, inference_cfg)` is **true**, the handle gets the bit, and the four `FOREACH_CFG_DRIFT_CHECK` rows **do** fire, comparing values parsed out of a stamp the epoch floor just declared untrustworthy.
- Net: there is no configuration in which the drift gates do useful work on a *current-format* stamp. The moment anyone retrains and produces the first v3 stamp, the gates go dark for good.

**C-3 (attribution, not fact). The `inference_cfg` vacuity is already discovered and homed** — it is not a new finding. `tests/controller_test.cpp:15566-15584` documents it verbatim, dated 2026-08-15 / D-421:
> `STAMP_SET(inf, inference_cfg)` below hand-sets the GROUP bit, and NO production emit path does. … **THIS FIXTURE IS WHY THE VACUITY SURVIVED.** Because it manufactures the precondition, the emit→parse→gate chain looks exercised, so a drift gate that can never fire in production stayed green here for a whole release train (Class 51 × Class 12; Class 58 sub-shape B). … ⚠ MUST-TOUCH at the D-421 step-6 fix.

And `plans/v5.15-live-readiness/MASTER.md:60` records "an i-class sweep reports **10 of 24 STAMP gate bits unreachable at production emit** … **The other 9 are PENDING adversarial verification**." My pass **is** that pending verification, and it comes back **confirmed** — with the count now 6 unset bits / 18 rows (was 10 bits before the 2026-08-16 `feature_mask` + `training_timestamp_us` producers landed and the `fees` group was deleted). Per `feedback_match_anomaly_to_decision_log_before_escalating`: this is a logged decision reaching its verification step, not a new alarm.

**C-4 (minor, worth knowing for any fix). The registry's `emit_when` column is dead.** The emit walk at `ModelInference.hpp:2259` / `:2292` gates purely on the group/standalone bit and never evaluates `emit_when`. Its only consumer is `STAMP_MODEL_CONST_AUTOPOPULATE_ONE` (`StampBoundModelConstRegistry.hpp:766-775`), reachable only through the macro quarantined behind `static_assert(false)` at `:691-696` (PARITY-022). So the `inf->has_inference_cfg` text in all 46 rows' column 8 is documentation, not behaviour. Anyone "fixing" a row by editing `emit_when` changes nothing.

**C-5 (minor). `StampBoundModelConstRegistry.hpp:296` carries a live self-report of a dead column**, and it is correct: the `feature_mask` row's `get_value` names `inf->feature_mask_train`, a member that does not exist — it compiles only because AUTOPOPULATE is quarantined. That is the same C-4 deadness, already annotated.

---

## Part 5 — Option matrix

| # | Option | What it does | Robustness | Latency | Design-philosophy fit | Cost |
|---|---|---|---|---|---|---|
| **O1** | **Delete the 9 `inference_cfg_*` rows + re-key the gates onto a live signal** | Remove the orphan rows (fees-group precedent, `StampBoundModelConstRegistry.hpp:303-320`). Replace `stamp_has_inference_cfg` with a signal the cfg-derived parse actually produces — e.g. `r.has_<name>` per row, so each drift row gates on *its own* field's presence | Highest. Per-row presence is strictly more precise than a group bit, and Surface-G forward-compat is preserved per-field | none (boot-time) | H21-clean (names retired by comment, ledger has no entry yet — `check_identifier_retirement` reports these as un-recorded `ADD`s, so deletion is unconstrained). Structural-fix-over-patch. Kills the group-bit concept that caused this | MED — touches `lookup_drift`, `drift_check_from_derived` ×4 X-macros, 4 `FOREACH_CFG_DRIFT_CHECK` rows |
| **O2** | Add a producer: `STAMP_SET(inf, inference_cfg)` in `Stamp_AssembleAndEmit` | One line; the 9 keys emit; the bit sets on parse | **REFUTED — do not do this.** These 9 rows have no producer for their *values* either (`StampInferenceCfgInputs inf = {}` at `StampHelper.hpp:185` zero-inits them). Setting the bit emits **nine zeros into an HMAC-signed body** — bit-for-bit the `fees`-group failure deleted 2026-08-16, whose own comment names it: *"a row retired from its PRODUCER but left in its EMITTER does not go dead, it goes LYING"* (`:315-316`) | none | Violates the exact rule the previous commit codified | LOW cost, **negative value** |
| **O3** | Compile-time structural close | Make an un-produced gate bit a build error: derive the universe from `enum StampHasFlagBit` and `static_assert` that every bit has a setter reachable from `Stamp_AssembleAndEmit` | Highest — closes the class, not the instance. Matches the operator direction already recorded at `MASTER.md:60` ("the STRUCTURAL compile-time close is preferred over a scanner") | none | `feedback_guards_compound_enforcement_is_leverage`; M7 | HIGH — needs a design pass; the scanner shape was already REFUTED at D-421 step 6 |
| **O4** | Delete the 8 (b) rows (`environment_*` ×5, `effective_hash`, `scaler_fit_data_hash`, `removal_reasons_csv`) | Removes 8 never-emitted, never-consumed rows + `MASK_environment_meta` + 3 standalone bits | Tidiness. Removes the surface where a future O2-style "just set the bit" mistake can land | none | `feedback_backwards_compat_not_default_concern`; H21-safe (no ledger entries; `has_flags` bit positions are never persisted per `:553-556`) | LOW |
| **O5** | Keep the 8 (b) rows as declared scaffolding, fix only the false comment | Zero code change; correct `:439` | Lowest | none | Leaves 8 rows one line away from becoming lying rows | TRIVIAL |
| **O6 — NOVEL ALTERNATIVE CONSIDERED**<br>(`feedback_proactive_novel_alternative_consideration`) | **Invert the gate polarity: make ABSENCE the failure, not the skip.** Every one of these gates is written `if (present) check(); else skip;` — the Surface-G forward-compat idiom. That idiom is what converts "the producer vanished" into "an old stamp, nothing to see". Replace it with a **required-key manifest**: the emitter records `stamp_keys_emitted=<count-or-hash>` and the parser REFUSES a stamp whose key set doesn't cover the manifest the current binary demands. A missing key then becomes a loud REFUSE instead of a silent skip | **Strictly the most robust** — it is the only option that would have caught `feature_mask`, `training_timestamp_us`, the `fees` group **and** these 9, at the first load, without anyone auditing anything. Attacks the shared mechanism rather than the four instances | none (boot) | Directly answers Class 58's open methodology half ("the complement is a kind of question nobody asks") — a manifest IS the complement, enumerated from outside the registry. Sister to `check_corpus_membership.py`'s "a LIST, not a count" discipline | **HIGH, and it has a real cost:** it hard-breaks every legacy stamp by design, which is the point but must be an explicit operator decision. Needs a `STAMP_FORMAT_VERSION` bump (H21). `project_no_live_models_dev_test_only` makes the break free today |

## Recommendation

**O1 now (with the O2 refutation on the record), O4 folded in, O6 tabled as the structural successor.** Concretely:

1. **O1** — delete the 9 `inference_cfg_*` rows and re-point the drift gates at a per-field presence signal. This is the only option that closes D-1 without emitting a lie. It also removes the last consumer of `MASK_inference_cfg`, so the group bit and its 3 dispatchers (`:729`, `:743`, `:759`) go with it.
2. **O4** — delete the 8 (b) rows in the same commit. They are the remaining stock of "one `STAMP_SET` away from lying". Fix the `scaler_fit_data_hash` false-verifier comment as part of the deletion rather than separately.
3. **`overlay_hash` / `effective_hash`: do NOT delete.** They differ from the other (b)s — `overlay_hash` has a real, production-wired consumer and a real Python producer, just no bridge. Route to the unwired-capability register with the specific gap named: *`StampArgs` needs an `overlay_hash_hex` / `effective_hash_hex` field and the two `Stamp_AssembleAndEmit` callers need to supply it.*
4. **The ADJACENT finding gets its own leaf** and should be verified by boot-log before anything else on this page is coded — it is the only item with a same-day observable symptom, and if confirmed it is a live-readiness blocker independent of the 18 keys.
5. **O6 tabled** for the structural pass already in flight per `MASTER.md:60`. Do not let O1 close the ticket that O6 is the real answer to.

---

## Part 6 — Where the paired a-class should push hardest

Ranked by how much a successful refutation would change the recommendation.

1. **The ADJACENT finding is the softest load-bearing claim I make.** It rests on an exhaustive enumeration of `handle->` assignments in one file. **Refute vector:** find any *other* writer of the cfg-derived handle fields — a `memcpy` of a struct region, a `*handle = ` whole-struct assignment, an `EnsembleModelZoo` path that populates differently, or a `HotSwap_ShadowLoad_*` copy. I searched `NodeModelZoo.hpp` exhaustively but did **not** exhaustively search `EnsembleHotSwap.hpp` or the ensemble loader for a second propagation path. If one exists, the two Tier-1 false-positives evaporate.
2. **"No production emit path sets `MASK_inference_cfg`" — attack the negative.** My three sweeps (STAMP_SET / has_flags / MASK_*) are orthogonal and I believe them, but a negative is a negative. **Refute vector:** a `#define` that expands to `STAMP_SET` under a name I didn't grep; a `has_flags` write through a reference or a pointer alias (`uint64_t& f = inf.has_flags`); an aggregate initializer `StampInferenceCfgInputs inf = { .has_flags = ... }`. The decisive check is empirical, not textual: **produce a v3 stamp** (run the Train Model panel or `Backtest_RunFullValidation`) and `grep '^inference_cfg_' <new>.stamp`. If a single line appears, D-1 is dead.
3. **Is `NodeModelZoo_ValidateAgainstCfg` genuinely on the live boot path, or only on hot-swap?** I traced `EngineCommon.hpp:416` and confirmed it is gated `if (loaded && cfg.node_model_dir[c][0])` — so a node configured with `core_N_model_path` (single file) rather than `core_N_model_dir` may never reach it. **Refute vector:** if the common production config uses `model_path`, gate B was already unreachable for a reason having nothing to do with the stamp bit, and D-1's severity is carried entirely by gate A.
4. **`overlay_hash` severity.** I called it MED on "blast radius today = 0". **Refute vector:** if the overlay feature is on the near-term roadmap, the correct classification is HIGH-latent, because the first operator to generate a sidecar will get a silent pass they will read as a verified one. Conversely if the feature is abandoned, it is (b) and should be deleted with the other 8, which would simplify the recommendation.
5. **The pre-epoch warn-mode path I surfaced in C-2 and did not pursue.** Under `held_out_gate_strict=0` a `stamp_format_version=1` stamp is parsed in full — including its money fields under the retired binary encoding — and those parsed values are copied onto the handle at `NodeModelZoo.hpp:363-479` and compared at `ModelValidation.hpp:222`, *after* `:1805` declared them un-decodable. **Refute vector:** show that warn-mode with a pre-epoch stamp is unreachable in practice (e.g. an earlier boot gate refuses `held_out_gate_strict=0` for live trading). If it is reachable, that is a separate finding of its own severity and I have under-called it.
6. **My claim that the 8 (b) keys have zero consumers.** Weakest link: I searched engine source + `tests/` + `tools/`. **Refute vector:** a consumer in the GUI reading through a snapshot field rather than the handle directly (e.g. `PerNodeSnap` carrying `environment_cpu_model`), or an operator-facing report generator. I grepped `GUI/` for each key name and found nothing, but I did not walk the snapshot publisher field-by-field.

---

## Files that matter (absolute paths)

- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/StampBoundModelConstRegistry.hpp` — the 46-row registry, bit allocation, emit/parse/populate dispatchers
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/StampHelper.hpp` — `Stamp_AssembleAndEmit`, the sole production producer (17 bits)
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ModelInference.hpp` — emit walk `:2258-2298`, parse walk `:1699-1766`, epoch floor `:1805`, `ModelHandle` `:341+`
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/NodeModelZoo.hpp` — drift-walker call `:304`, sr→handle copy `:363-479`, drift chokepoint `:589-632`
- `/home/caramel/code/FoxML_Trader_v2/MemHeaders/CfgGateRegistry.hpp` — `lookup_drift` `:186-208`, `drift_check_from_derived` `:516-602`, the `DRIFT_CHECK_FROM_DERIVED` wrapper `:811-819`
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/CfgDriftCheckRegistry.hpp` — the 18-row second drift registry
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ModelValidation.hpp` — `NodeModelZoo_ValidateAgainstCfg`
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/FeatureRegistryOverlay.hpp` — the `overlay_hash` consumer
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/CfgFieldRegistry.hpp` — the 30 `STAMP_BOUND_CFG_DERIVED` rows + the coverage static_assert `:1488-1497`
- `/home/caramel/code/FoxML_Trader_v2/tests/controller_test.cpp:15566-15584` — the fixture that manufactured the precondition, already annotated as MUST-TOUCH
- `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/MASTER.md:60` — the D-421 step-6 update recording the 9 pending verifications this report discharges
