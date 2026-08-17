---
type: agent-report
agent_class: a-class
date: 2026-08-17
engine_head: a160123
directive: "REFUTE the claim that PER-GROUP -> PER-KEY emit gating leaves the model-stamp canonical wire body byte-identical"
verdict: REFUTED
status: verbatim-at-receipt
---

> Saved VERBATIM at receipt. Orchestrator wrote the file; the agent was read-only.
> Orchestrator verification notes are in `README.md`, NOT inline — the report is unedited.
> Probe binaries this agent left at `~/.cache/foxml_audit/` are outside the repo and
> outside `/tmp`; they survive reboot and are re-runnable.

---

## A-CLASS VERDICT — `REFUTED`

**Directive:** refute "PER-GROUP → PER-KEY emit gating leaves the model-stamp canonical wire body byte-identical."
**Roots covered:** `CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/ *.cpp` (named explicitly per Landmine 19).
**Method:** preprocessor expansion of the registry (not eyeball) + two compiled probes that run the real `tt::Stamp_AssembleAndEmit<64>` production path. Probe binaries + emitted stamps kept at `/home/caramel/.cache/foxml_audit/` (outside `/tmp`, survives reboot) — re-runnable.

---

## 1. The refutation: the row, the input, the measured bytes

**Row:** `inference_cfg_bandit_blend_ratio` — `/home/caramel/code/FoxML_Trader_v2/ML_Headers/StampBoundModelConstRegistry.hpp:301-302`
**Producer:** `/home/caramel/code/FoxML_Trader_v2/ML_Headers/StampHelper.hpp:249-251`

```c++
if (BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)) {
    STAMP_SET(inf, inference_cfg_bandit_blend_ratio);
}
```

**The bit is set. The value is never assigned.** `StampInferenceCfgInputs inf = {}` (`StampHelper.hpp:185`) zero-inits it, so the emitted line is permanently `inference_cfg_bandit_blend_ratio=0`.

**Caller input that fires it:** the *default* config. `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerConfig.hpp:2012` — `/*bandit_enabled*/ 1` (flipped 0→1 on 2026-08-16). Every production stamp at HEAD carries the line.

**Measured** (probe A = default cfg; probe B = same but bandit bit cleared, which is byte-for-byte the body a value-assignment-site per-key gate produces, since no assignment site exists):

```
1423 probe_model.bin.stamp        <- has the line
1388 probe_model2.bin.stamp       <- doesn't
  35 bytes delta  ("inference_cfg_bandit_blend_ratio=0\n")
signature=d21ee1d718f027c5769c9907b74d16241c68e0fcf61da918965bc596e34a0b88
signature=9046d28a1ec61eb0ab58fb719e05b3ceff777688b43f918433e6dd2c49702b67
```

Different body, different HMAC. **Not "probably" — measured.**

### The dilemma the claim sits on

The claim's parenthetical *"each per-key bit gets set wherever the group bit was set"* is the only implementation under which bytes are identical — and that implementation **is a no-op**. It re-encodes the same reachability with more bits and prevents nothing: the `fees` defect was *bit set, value not assigned*, and copying the bit-set to each key reproduces exactly that. The only per-key gating with teeth is **bit set at the value-assignment site**, and that one drops the row above. So:

- Byte-identical ⟹ the change does not do what it is being proposed to do.
- Does what it is proposed to do ⟹ bytes change.

There is no third branch. The claim is refuted as stated.

---

## 2. THE LIVE CRITICAL — the `fees` twin the E.1.2 sweep missed

This is the finding that outranks the gating question, and the orchestrator should read it before anything else.

Real production body, default cfg, default `StampArgs`, emitted by the probe:

```
11  inference_cfg_bandit_blend_ratio=0                 <- model-const half, LIE
...
31  bandit_blend_ratio=0.29999999999999999             <- cfg-derived half, TRUTH
```

**Both lines are in the same HMAC-signed model-identity document.** Two contradictory claims about the same quantity, one of them a hardcoded zero.

This is *structurally identical* to the `fees` defect deleted at commit `f90b696` — same cause, same file, **three lines above the deletion**:

- `bandit_blend_ratio` was migrated to the cfg-derived emit half — `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/CfgFieldRegistry.hpp:669` carries `STAMP_BOUND | STAMP_BOUND_CFG_DERIVED` and its own doc-string says *"was standalone inference_cfg_bandit_blend_ratio at StampBoundModelConstRegistry.hpp:296; framework walker emits unprefixed"*.
- Its gate is unconditional: `FOREACH_CFG_GATE_GLOBAL` has **zero entries** (`MemHeaders/CfgGateRegistry.hpp:113-117`), so `lookup_populate` returns the `true` default (`:165`) — the truthful line emits on every stamp.
- The model-const row's producer went with the migration; only the `STAMP_SET` was left behind.

`StampHelper.hpp:227-229` — written *during* the D-421 fix — asserts this row is legitimate: *"The bandit_blend_ratio prefixed has-flag controls the emission of the `inference_cfg_bandit_blend_ratio=X` wire key."* There is no `=X`. There is only `=0`. That comment is the reason the sibling survived the sweep that killed `fees`.

**Class 58 sub-shape A′** (sibling asymmetry — two structurally identical rows, one swept, one not) per `DOCS/RECURRING_BUG_PATTERNS.md:101`. The blast radius is wider than `fees`: `NodeModelZoo.hpp:469-472` copies the zero onto the handle, and `Backtest/BacktestPanels.hpp:2309-2311` prints it to the operator as the model's training-time blend ratio.

**Why the test suite is green on it:** `tests/controller_test.cpp:15594-15598` hand-assigns the value the production path never assigns, then asserts the round-trip at `:15636-15637`. Class 58 sub-shape B — and the D-421 comment 20 lines above (`:15577-15584`) names that exact pattern for the *sibling* bit while this one sits inside it.

---

## 3. The cascade the change would introduce (blast radius)

The group bits are **not** emit-gate-only. They are load-bearing at 15+ consumer sites, and `inference_cfg` in particular is the master gate for the entire cfg-derived drift check:

- `/home/caramel/code/FoxML_Trader_v2/MemHeaders/CfgGateRegistry.hpp:814` — `DRIFT_CHECK_FROM_DERIVED` passes `STAMP_HAS((handle), inference_cfg)` as `stamp_has_inference_cfg`.
- `MemHeaders/CfgGateRegistry.hpp:187-208` — `lookup_drift` returns `stamp_has_inference_cfg && (expr)`, **default `stamp_has_inference_cfg`**, for every row.
- `MemHeaders/CfgGateRegistry.hpp:568, :588` — the ML_CFG_FLAG / GATE_CFG_FLAG drift walkers use it as a bare `&` conjunct.
- Plus 4 rows in `ML_Headers/CfgDriftCheckRegistry.hpp:257, :261, :266, :332`.
- Handle propagation gated on group bits: `ML_Headers/NodeModelZoo.hpp:383` (8 xgb fields), `:409` (label_params), `:417` (scaler), `:458` (inference_cfg), `:2182`, `:2276`, `:2423`.

**Already-live Class 51 (vacuously-green guard, sub-shape B — gate unreachable):** `MASK_inference_cfg` is set on the handle only if the parser saw one of the 9 `inference_cfg_*` POST_CFG keys (`StampBoundModelConstRegistry.hpp:472-501` via `STAMP_PARSER_SET_HAS_inference_cfg`). The probe body confirms **production emits none of them** — lines 11-50 contain zero `inference_cfg_*` keys except the standalone. So `stamp_has_inference_cfg` is always false and **the entire cfg-derived drift check is dead in production at HEAD.**

Today that vacuity is *contingent* — a stamp carrying `inference_cfg_ml_tp_pct=` would flip the bit on and the check would come alive. Per-key gating deletes the group bit's only producer on both the emit and parse sides, making `STAMP_HAS(handle, inference_cfg)` **permanently, structurally false**. The change converts a repairable vacuity into an unrepairable one, silently, while everything keeps compiling and keeps reporting "no drift". *That* is the cascade, and it is not mentioned anywhere in the recommendation.

---

## 4. Per-attack-line verdicts

| # | Attack line | Verdict | Evidence |
|---|---|---|---|
| 1 | Grouped row with group bit set but value unassigned | **NOT-REAL for grouped rows; REAL for a standalone** | All 15 emitting grouped rows are fully assigned: `xgb_hyperparams` 8/8 (`StampHelper.hpp:335-346`), `label_params` 3/3 (`:376-378`), `scaler` 2/2 (`:392-396`), `grid_member` 2/2 (`:386-387`). The `fees` shape survives at the **standalone** `inference_cfg_bandit_blend_ratio` (`:249-251`) — which per-group→per-key gating does not even touch. |
| 2 | Conditional producers / `grid_member` always-set | **NOT-REAL** | `grid_member` is unconditional (`:385`) and assigns both members from `StampArgs` defaults `count=1, idx=0` (`StampHelper.hpp:102-103`). Probe lines 23-24 confirm `grid_member_count=1` / `grid_member_idx=0`. |
| 3 | `emit_when` names a bit no producer sets | **REAL — worse than stated** | Column 8 is **dead text**: the emit walk (`ModelInference.hpp:2258-2263`) expands only `#name`, `fmt`, `inf->name` and `STAMP_EMIT_CHECK_HAS_##group(name)`; `emit_when` is never expanded. Verified: `inf->has_bandit` / `inf->has_grid_member_count` / `inf->has_scaler` are **not members** of `StampInferenceCfgInputs` — grep across all roots finds them only in the registry and in unrelated `FeatureStandardizer`. Keying per-key gating off column 8 does not silently drop keys; it **fails to compile**. |
| 4 | Ordering, incl. the PRE→cfg→POST boundary | **NOT-REAL** | The gate is a per-row `if` inside a sequential FOREACH; the predicate cannot reorder. Probe body confirms canonical order preserved (lines 11-27 PRE, 28-47 cfg-derived, 48-50 POST). *Residual risk:* per-key gating needs 46 bits vs today's 23 (`STAMP_BIT_COUNT`), which invites a registry/enum reshuffle — that would reorder. `has_flags` is 64-bit; 46 leaves 18 bits and the registry gained 9 rows in two ships. |
| 5 | Switching the walk to the `get_value` column | **REAL and hard** | Two rows break. (a) `feature_mask` get_value is `inf->feature_mask_train` (`StampBoundModelConstRegistry.hpp:380`) — **no such member exists anywhere** (grep across all roots: registry line + comments only). Compile error. (b) `inference_cfg_bandit_blend_ratio` get_value is `inf->bandit_blend_ratio` (`:302`) — that member **does exist and compiles**, but I measured it: `sizeof(inf.bandit_blend_ratio)==16`, type `FPN_Binary<64>`; `sizeof(inf.inference_cfg_bandit_blend_ratio)==8`, type `double`. Passing a 16-byte class type to `%g` through varargs → garbage bytes in a signed body. `training_timestamp_us`'s `(unsigned long)` cast is byte-neutral on LP64 only. |
| 6 | The signing boundary | **NOT-REAL — nothing wider is signed** | Emit: `tt::hmac_sha256_hex(effective_secret, canonical, sig)` over the NUL-terminated body (`ModelInference.hpp:2319`), then `fputs(canonical)` + `fprintf("signature=%s\n")` (`:2337-2338`). Verify: the body is re-accumulated **from the raw file lines** up to `signature=` (`:1662-1668`), not reconstructed from parsed fields. No length, count, or trailing byte is signed. **Consequence: existing stamps are unaffected by an emit-gate change — a dropped line costs exactly that line's bytes and nothing else.** This is the one place the claim is fully correct, and it is the reason the defect is survivable. |

---

## 5. Correcting the supplied frame (re-cascade signal — minor)

Two premises in the spawn kit are off and should not be carried into the plan body:

- **"28 keys that emit today"** is a *maximum over caller inputs*, not a set. With default `StampArgs` the measured count is **20** model-const keys (probe lines 11-27 = 17 PRE, 48-50 = 3 POST). The other 8 need `horizon_ticks>0`, a scaler SHA, a run name, `req_num_outputs>0`, and `req_role` — five independent caller conditions (`StampHelper.hpp:360, :390, :400, :408, :412`). Any byte-equivalence argument must quantify over the input space, not one row of it.
- **Registry line numbers**: `_PRE_CFG` is at `:289` and `_POST_CFG` at `:407` as given, but the row split is **22 PRE / 24 POST**, not 26/20 as the file's own comments claim (`:288`, `:1455`, `:2071` all say "26 entries"). Mechanically re-derived via preprocessor expansion.

---

## 6. The simpler, safer option the recommendation ignored

Per-key gating is the wrong instrument. The defect class is **"presence bit set without the value being written"** — a *co-location* failure, not a *granularity* failure. Widening the bitmap does not couple the two; it just makes the uncoupling finer-grained. `feedback_structural_fix_over_belt_and_suspenders` applies: prefer the fix that removes a category error over the one that adds a layer.

**Alternative A — make the pair atomic (recommended).** One macro that cannot express the defect:

```
STAMP_EMIT(inf, <name>, <value>)   // sets the bit AND writes the field; no other way to set a bit
```

Then `STAMP_SET` becomes private to the parser/handle-copy paths. `inference_cfg_bandit_blend_ratio` would not compile without a value, which is exactly the RED you want. This is byte-neutral by construction for every row that *does* assign, and it forces the 1 row that does not to be resolved deliberately (deleted, or genuinely populated) rather than silently preserved.

**Alternative B — the cheaper, more targeted fix, and the one that closes the actual CRITICAL.** Delete the `inference_cfg_bandit_blend_ratio` row exactly the way `fees` was deleted at `f90b696`: the truthful `bandit_blend_ratio` line is already in every stamp (probe line 31), the epoch floor `STAMP_FORMAT_VERSION_EPOCH_FLOOR` refuses pre-epoch stamps, the parser tolerates unknown keys, and no live models exist (`project_no_live_models_dev_test_only`). Same H21 disposition, same reasoning, already written down at `StampBoundModelConstRegistry.hpp:303-320`. **This changes bytes deliberately, with a SOFT bump — which is the honest way to get the 35 bytes out.**

**Alternative C — CI, not convention.** The recurrence is now 2/2 at the same surface (`fees`, then `bandit_blend_ratio`) *despite* a codified fix and a same-day comment. That is the M7 escalation trigger. A mechanical check — *"every `STAMP_SET(inf, X)` in an emit-assembly function has an assignment to a row gated by X in the same basic block"* — is a ~40-line AST/regex tool and catches the whole class forever. `feedback_guards_compound_enforcement_is_leverage`.

**Ordering:** C (guard) → B (close the CRITICAL) → A (structural, if the class recurs a third time). Per-key gating: **do not ship**, it is orthogonal to the defect and drags the drift-gate cascade in §3 with it.

---

## 7. Falsifying test spec (implementable as written)

**Harness already exists** — extend, don't build new: `tests/controller_test.cpp:28483-28542` already calls `tt::Stamp_AssembleAndEmit<64>` with `ControllerConfig_Default<64>()` and asserts on a real emitted stamp.

**Test 1 — value-not-just-presence (catches the CRITICAL now; this is the one that fails at HEAD).** Same block, `ControllerConfig_Default<64>()`, `cfg.bandit_blend_ratio = FPN_FromDouble<64>(0.42)`, bandit bit left at its default 1. Emit, `verify_model_stamp`, then assert:
```
STAMP_HAS(vr, inference_cfg_bandit_blend_ratio) == 1
&& fabs(vr.inference_cfg_bandit_blend_ratio - 0.42) < 1e-9
```
**Expected at HEAD: FAIL** (parses `0`). This is the presence-vs-value discipline the `training_timestamp_us` test at `:28517-28522` already articulates in prose — apply it to its own sibling. Generalize: for every row in `FOREACH_STAMP_BOUND_MODEL_CONST` whose gate is set on the default path, set a **distinctive non-default** value in cfg/args and assert the round-trip carries *that* value. A row with no path from any input to a distinctive output is a row with no producer.

**Test 2 — byte-equivalence gate for the gating change itself.** Golden-body harness, `LC_NUMERIC=C` (already pinned at `ModelInference.hpp:2185-2187`):
- *Inputs:* the cross-product of the five caller conditions — `{horizon_ticks ∈ {0, 20}} × {scaler_sha256_hex ∈ {"", "ab…"}} × {run_name ∈ {"", "r1"}} × {req_num_outputs ∈ {0, 3}} × {req_role ∈ {"", "barrier"}}`, each × `{bandit_enabled ∈ {0,1}}` = 64 cases. This is the set the "28 keys" claim quantifies over; anything less does not test it.
- *Artifact:* the canonical body **with the volatile lines masked** — `model_sha256`, `trained_on`, `training_timestamp_us`, `signature` (the first three are input- or clock-derived; `training_timestamp_us` is `CLOCK_REALTIME` at emit per `StampHelper.hpp:315-321`). Everything else is deterministic; the probe confirms it.
- *Comparison:* `memcmp` of masked body pre-change vs post-change, per case. Pass = 0 diff in all 64. A single differing case = the claim is false for that input, and the diff names the row.
- *Second assertion, non-negotiable:* also `memcmp` the **line count** and assert `strstr(body, "=\n") == NULL` — a value-less key is a lie even when the byte count happens to match.

**Test 3 — non-vacuity self-defense (Class 51).** The gate under test must be shown to be *reachable*. Assert `STAMP_HAS(vr, inference_cfg) == 1` for at least one production-path emit. **Expected at HEAD: FAIL** — which is the point: it pins §3's dead drift check and prevents per-key gating from freezing it dead. Any per-key implementation must keep this test passable, or it must delete the drift check honestly rather than leave it compiled and green.

---

## 8. Stale comments surfaced (SUBAGENT_ARMING § 2.5 — code is truth)

Each is a checkable claim, verified false, load-bearing for *this* decision:

1. `ML_Headers/StampBoundModelConstRegistry.hpp:242` — `inference_cfg` group doc lists `confidence_threshold_scale, barrier_gate_enabled, confidence_hard_block_threshold, held_out_fraction`. All four were deleted from the group at `:290-299`. The group's actual 9 members are `inference_cfg_ml_tp_pct` … `inference_cfg_thompson_exp3_blend_alpha` (`:472-501`). **Anyone sizing this change from that line gets the wrong member set.** Suggested: `"inference cfg fields (9): ml_tp_pct, ml_sl_pct, barrier_blend_mode, per_horizon_barrier_blend, bandit_algorithm, thompson_{mu_prior,precision_prior,precision_obs,exp3_blend_alpha} — NO PRODUCER sets this bit; see the vacuity note"`.
2. `ML_Headers/StampHelper.hpp:227-229` — asserts the bandit row emits `=X`. It emits `=0`. This comment is *why* the sweep missed it. Replace with the `fees`-style retirement note.
3. `ML_Headers/ModelInference.hpp:1447-1451` — "13 bits used today", "6 group bits (inference_cfg, scaler, **fees**, …)". `fees` was removed 2026-08-16; `STAMP_BIT_COUNT` is **23**.
4. `ML_Headers/ModelInference.hpp:1455` and `:2071` — "26 entries". Actual **46** (22 PRE + 24 POST, preprocessor-derived).
5. `ML_Headers/StampBoundModelConstRegistry.hpp:244` — "xgb hyperparams (9): … train_nthread". The group has **8**; `xgb_train_nthread` is standalone (`:390`).
6. `CoreFrameworks/ControllerConfig.hpp:2000` — "ml_cfg_flags defaults: all 7 flags off". `bandit_enabled` is `1` twelve lines below (`:2012`), and the registry has 9+ rows.
7. `ML_Headers/ModelInference.hpp:2206-2209` — "SOFT bump 1 → 2". Emitted value is `stamp_format_version=3` (probe line 10).

Item 1 is the highest severity of the set: it is a *quantifier + member-set* claim on the exact registry the proposed change edits, and it is wrong in every member.

---

## 9. Bottom line

**REFUTED.** Byte-identity holds only for a per-key conversion that is a no-op; the useful conversion drops `inference_cfg_bandit_blend_ratio=0` — 35 bytes, different HMAC, on the **default** config, measured. More importantly, the audit found the thing the proposal was meant to prevent **already shipping**: a signed model-identity document that states the bandit blend ratio twice, once truthfully and once as zero, three lines from where its identical twin was deleted yesterday. Close that (§6 Alternative B) behind a mechanical guard (§6 Alternative C) before touching gate granularity — and if per-key gating is pursued anyway, it must first answer for the `inference_cfg` drift gate it would freeze permanently dead (§3).
