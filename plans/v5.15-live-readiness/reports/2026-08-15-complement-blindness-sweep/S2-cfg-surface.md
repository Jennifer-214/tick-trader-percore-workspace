---
type: agent-report
status: FROZEN — verbatim agent output
directive: S-2 — complement-blindness sweep, shard 2/5: the CFG surface
agent_class: i-class
delivered: 2026-08-15
ground: engine HEAD 7240f3d, branch feat/v5.15-live-readiness
headline: F-1 — FOREACH_GLOBAL_CFG_FIELD is a COVERAGE registry (struct-gen additive, not exclusive) whose complement is 32 live global cfg keys with no row; 30 are determinism-bearing FPN_Binary fields parsed by raw atof with no malformed-capture, and 2 (regime_vol_spike_ratio, regime_model_weight) are read by Regime_Classify on the live sharded slow path. All 8 landed guards are green and blind to every one of them
operator_decision_owed: OQ-1 (the 32 keys — (a) migrate the 30 FPN/INT rows into FOREACH_GLOBAL_CFG_FIELD, (b) add a global exemption registry with a mandatory rationale column mirroring FOREACH_MANUAL_PER_NODE_FIELD, or (c) refuse-boot on unknown global keys, which requires (a) or (b) first) · OQ-2 (derive the H16 domain by enum-parse, retiring the structurally-blind ALL_METADATA_BITS_IN_USE hand-mirror) · OQ-5 (reason column on the exempt side — now 2-for-2 as a real-finding predictor)
sister_reports: S1-capital-wire-persist.md · S3-stamp-hmac-ml.md · S4-nodectx-state-bitflags.md · S5-emit-display-and-set-closure.md
saved_at: step-1 close-out, NOT at receipt — recovered VERBATIM from the session transcript
  (subagents/agent-<id>.jsonl final assistant message). Sisters S1/S3/S5 were saved at receipt;
  these two were missed, which is itself the save-agent-reports-verbatim discipline failing on the
  two shards that finished while the orchestrator was mid-implementation. Recovery method verified
  against S1 first (extract diffs from the saved copy by exactly the frontmatter block + one
  trailing-space normalization), so the body below is the agent's output, not a reconstruction.
---

# S-2 — COMPLEMENT-BLINDNESS sweep, shard 2/5: the CFG surface

**Ground:** engine `/home/caramel/code/FoxML_Trader_v2`, HEAD `7240f3d` (verified `git log --oneline -1`), branch `feat/v5.15-live-readiness`. Read-only pass; nothing edited, nothing in E.1.2 scope touched.
**Method:** the `i-class-nodecontext-partition.md` methodology — classify each registry SOURCE-OF-TRUTH vs COVERAGE, identify the *authoritative domain from the source*, enumerate every guard as rows-forward vs domain-complement, then **compute the complement mechanically** where none exists.

**Mechanical tools RUN (all at HEAD, RC captured directly per Class-57):**

| Tool | RC | Verdict |
|---|---|---|
| `tools/check_per_node_registry_integrity.py` | **0** | Checks 1-11 PASS (6 INFO, 8 PENDING) |
| `tools/check_cfg_key_prefix_drift.py` | **0** | CLEAN |
| `tools/check_cfg_gate_caller_coverage.py` | **0** | 6/6 callers gated or exempt |
| `tools/scan_class_44_cfg_orphan.py` | **0** | 5 known-pending (#9) dead-path orphans, 0 new |
| `tools/check_meta_registry.py` | **0** | 68/68 enrolled; H15/H19 clean |
| `tools/check_cfg_duplicate_keys.py` | **0** | GREEN across 2 cfg files |
| `tools/check_identifier_retirement.py` | **0** | 47 wire ids match ledger |
| `tools/calls_graph_diff.sh` | **0** | CLEAN — no strategy/regime orphans |

**Every landed guard is green. Every finding below is invisible to all eight of them** — that is the point of the sweep.

---

## 0. HEADLINE

**The shard's payload is F-1:** `FOREACH_GLOBAL_CFG_FIELD` is a **COVERAGE** registry (its struct-gen is *additive*, not *exclusive*) whose complement is **32 live global cfg keys with no row**, of which **30 are determinism-bearing `FPN_Binary<F>` fields parsed by raw `atof` with no malformed-capture** — the exact class `CFG_FAULT_FEATURE_MALFORMED` was built for. Two of them (`regime_vol_spike_ratio`, `regime_model_weight`) are read by `Regime_Classify` on the **live sharded slow path**, and they are the 2 leftovers of a 6-member regime cohort whose other 4 migrated.

**The directive's false-positive guard fires correctly and completely on the PER-NODE side** (§ 1, verdict table): `check_per_node_registry_integrity.py` Check 2 enforces `PerNodeCfg<F>` is X-macro-only, so the registry IS the source there and there is genuinely no gap. **The same guard does not exist for `ControllerConfig<F>`** — that asymmetry is where the whole payload lives.

**The bitmap bit-accounting is CLEAN** (§ 2) — and cleanly so, for a structural reason worth stating.

---

## 1. PER-REGISTRY VERDICT TABLE

| # | Registry | file:line | Kind / generation direction | Authoritative domain | Complement check exists? | Complement contents |
|---|---|---|---|---|---|---|
| 1 | `FOREACH_GLOBAL_CFG_FIELD` (59 rows) | `CoreFrameworks/CfgFieldRegistry.hpp:336` | **COVERAGE.** Registry→struct exists (`ControllerConfig.hpp:1411`) but is **ADDITIVE, not exclusive** — manual scalars coexist (`ControllerConfig.hpp:462,463,538,604,665,892`) | the set of global keys `ControllerConfig_Load` accepts (`ControllerConfig.hpp:2440-3627`) | **NO.** No check asserts `ControllerConfig<F>`'s body is X-macro-only (`check_per_node_registry_integrity.py:701` Check 2 covers `PerNodeCfg<F>` only; `:716` Check 3 covers only `node_*[16]` arrays) | **32 keys — see § 3 F-1** |
| 2 | `FOREACH_PER_NODE_CFG_FIELD` (88 rows) | `CfgFieldRegistry.hpp:581` | **SOURCE-OF-TRUTH.** `PerNodeCfg<F>` generated at `ControllerConfig.hpp:354`; body **exclusively** X-macro | n/a — registry defines the domain | **Structural.** `check_per_node_registry_integrity.py:708/714` Check 2 FAILS on any manual field; `ControllerConfig.hpp:392-396` payload-byte `static_assert` is a second barrier | **∅ — N/A, no gap.** Directive's H17 guard verified, not assumed |
| 3 | `FOREACH_MANUAL_PER_NODE_FIELD` (12 rows) | `CfgFieldRegistry.hpp:914` | **COVERAGE** over the per-node exemptions | the `node_*[16]` parallel arrays on `ControllerConfig<F>` | **YES — bidirectional.** Check 3 (`:736`) fails on stray decls; Check 4 (`:745`) syncs against `DOCS/MANUAL_FIELDS_INVENTORY.md` | **∅.** All 12 carry a stated rationale column. **Genuinely clean** |
| 4 | `FOREACH_PER_NODE_DOMAIN_BITMAP` (5 rows) | `CfgFieldRegistry.hpp:973` | **SOURCE-OF-TRUTH** for the 5 bitmap fields; drives struct decl + overflow asserts (`:987`, `:995`, invoked `:1004`) | n/a | Check 2 asserts `PerNodeCfg<F>` contains only this + registry #2 | **∅.** All 5 domains bound, all 5 overflow-asserted. **Clean** |
| 5 | `FOREACH_PER_NODE_NO_FLAT_FIELD_SYNC` (1 row) | `CfgFieldRegistry.hpp:1051` | **COVERAGE** over `NO_FLAT_FIELD`-tagged rows | rows in #2 carrying `NO_FLAT_FIELD` (bit 12) | **YES.** Check 7 per `CfgFieldRegistry.hpp:1081-1083` | **∅ — computed this session.** Exactly one row carries `NO_FLAT_FIELD` (`strategy`, `:796`); exactly one sync row. **Clean** |
| 6 | `FOREACH_PER_NODE_ARRAY_OVERRIDE` (2 rows) | `CfgFieldRegistry.hpp:1100` | **COVERAGE** over TRANSITIONAL arrays needing a `nodes[c]` merge | the TRANSITIONAL subset of #3 | **NO** | **1 member — see § 3 F-5** (`node_time_exit_ticks`) |
| 7 | `FOREACH_METADATA_BIT` (14 rows) | `CfgFieldRegistry.hpp:1429` | **COVERAGE** over `CfgFieldDescriptor::MetadataFlag` bits (H16) | the enum body at `CfgFieldRegistry.hpp:154-189` | **A complement check EXISTS** (`:1560`) — **but its domain side is a HAND-MIRROR.** See § 3 F-2 | **∅ today** (15 bits, 14 enrolled + 1 exempted with rationale `:1535`) — **but the check is structurally blind** |
| 8 | `FOREACH_LIFECYCLE_CFG_FLAG` (3 rows / 8 bits) | `CoreFrameworks/LifecycleCfgFlagRegistry.hpp:38` | **SOURCE-OF-TRUTH** over its own bit space | n/a | overflow `static_assert:53` + meta assert `CfgFieldRegistry.hpp:1004` | **∅ — see § 2.** Clean |
| 9 | `FOREACH_GATE_CFG_FLAG` (6 rows / 8 bits) | `CoreFrameworks/GateCfgFlagRegistry.hpp:40` | **SOURCE-OF-TRUTH** | n/a | `static_assert:58` + meta | **∅ — see § 2.** Clean |
| 10 | `FOREACH_ML_CFG_FLAG` (12 rows / 16 bits) | `ML_Headers/MlCfgFlagRegistry.hpp:64` | **SOURCE-OF-TRUTH** for bits; **but its own AUTOPOPULATE companion is a 7-of-12 mirror** | n/a for bits | `static_assert:88` + meta | bit space **∅**; **companion complement = 5 rows — § 3 F-3** |
| 11 | `FOREACH_RISK_CFG_FLAG` (5 rows / 8 bits) | `CoreFrameworks/RiskCfgFlagRegistry.hpp:38` | **SOURCE-OF-TRUTH** | n/a | `static_assert:52` + meta | **∅.** AUTOPOPULATE covers 5/5 (`:60-69`). Clean |
| 12 | `FOREACH_OPS_CFG_FLAG` (4 rows / 8 bits) | `CoreFrameworks/OpsCfgFlagRegistry.hpp:37` | **SOURCE-OF-TRUTH** | n/a | `static_assert:50` + meta | **∅.** AUTOPOPULATE deliberately RETIRED with rationale (`:58-71`) → direct `= 0`. Clean, and the *right* resolution |
| 13 | `FOREACH_CFG_GATE_PER_NODE` (16 rows) | `MemHeaders/CfgGateRegistry.hpp:87` | **SPARSE SIDECAR (H18)** — partial function; absence = documented default `true` (`:40-47`, `:165`) | rows carrying `STAMP_BOUND_CFG_DERIVED` | rows-forward only (claimed `:135`) | 11 rows fall through to default. **Correct by design** — but see § 3 F-4 for the *global* sister |
| 14 | `FOREACH_CFG_GATE_GLOBAL` (**0 rows**) | `MemHeaders/CfgGateRegistry.hpp:113` | **SPARSE SIDECAR** — deliberately empty (`:61`) | the 3 global `STAMP_BOUND_CFG_DERIVED` rows | **NO** | **3 rows; its own accounting note is wrong about all 3 — § 3 F-4** |
| 15 | `FOREACH_SLOW_PATH_GATE` (11 rows / 16 bits) | `CoreFrameworks/SlowPathGateRegistry.hpp:43` | **SOURCE-OF-TRUTH** — defines its own gate set; each row's predicate is self-contained | n/a — a gate exists because a consumer wants it | overflow assert on `SlowPathGateState.flags` (`uint16_t`, `:184-186`) | **∅ — N/A.** Not a coverage registry; there is no external "set of gates that must exist". **Clean** |

**Clean registries, stated explicitly:** #2, #3, #4, #5, #8, #9, #11, #12, #15 — nine of fifteen have no complement gap, and #2/#5/#12 are clean for *good structural reasons* worth preserving (exclusive struct-gen / bidirectional CI / a companion deliberately retired rather than left stale).

---

## 2. THE BITMAP BIT-ACCOUNTING (the directive's sub-question)

| Bitmap | Storage | file:line | Bits declared | Bits used | Remainder | Accounted by |
|---|---|---|---|---|---|---|
| `lifecycle_cfg_flags` | `uint8_t` = **8** | `CfgFieldRegistry.hpp:975` | 3 | 0-2 | **5** | never generated — see below |
| `gate_cfg_flags` | `uint8_t` = **8** | `:976` | 6 | 0-5 | **2** | same |
| `ml_cfg_flags` | `uint16_t` = **16** | `:977` | 12 | 0-11 | **4** | same |
| `risk_cfg_flags` | `uint8_t` = **8** | `:978` | 5 | 0-4 | **3** | same |
| `ops_cfg_flags` | `uint8_t` = **8** | `:979` | 4 | 0-3 | **4** | same |
| `SlowPathGateState.flags` | `uint16_t` = **16** | `CoreFrameworks/SlowPathGateRegistry.hpp:184-186` | 11 | 0-10 | **5** | same |

### The remainder is accounted for STRUCTURALLY, not by tombstones — and that is the correct answer

**No `RESERVED` tombstone is needed, because an undeclared bit is unreachable by construction.** The bit ordinal is *generated from* the enum position, and the mask is *generated from* the ordinal:

```cpp
enum LifecycleCfgFlag { FOREACH_LIFECYCLE_CFG_FLAG(X_GEN_LIFECYCLE_CFG_BIT) LIFECYCLE_CFG_COUNT };
static constexpr uint8_t MASK_LIFECYCLE_CFG_##name = (uint8_t)(1u << LIFECYCLE_CFG_##name);
```
— `LifecycleCfgFlagRegistry.hpp:46-51` + `:59-61` (same shape at `GateCfgFlagRegistry.hpp:51-67`, `MlCfgFlagRegistry.hpp:81-97`, `RiskCfgFlagRegistry.hpp:45-58`, `OpsCfgFlagRegistry.hpp:43-56`).

**I verified the "no other writer" premise mechanically rather than assuming it.** Enumerating *every* write to the five words across `CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ Backtest/ GUI/`, the complete writer set is:

1. registry-generated set/clear inside the parser walkers — `ControllerConfig.hpp:2873,2874,2886,2887,2898,2899,2909,2910,2920,2921` (all `MASK_<DOMAIN>_CFG_##name`, token-pasted from a row);
2. whole-word per-node copies — `ControllerConfig.hpp:1809-1813`;
3. one whole-word zero — `ControllerConfig.hpp:2020`;
4. the four AUTOPOPULATE macros, which build only from `MASK_*`.

**A grep for a literal or hand-rolled bit constant ORed into any of these words returns ZERO hits.** Bits ≥ `COUNT` are provably always 0.

### H21 verdict on the positional ordinals: SAFE, and here is the proof

The ordinal is positional, so deleting or reordering a row renumbers every subsequent bit. That is a Knight-Capital hazard **only if the raw word is persisted or wire-emitted by value.** It is not:

- every consumer decodes first — `ShardedSnapshot.hpp:144,218,235,244,367,899` are all `BITMAP_IS_SET(word, MASK_*) ? 1 : 0`, i.e. the *decoded bit* crosses the boundary, never the word;
- the stamp path emits by NAME — `MemHeaders/CfgGateRegistry.hpp:381-383` (`inf.legacy_field = _bit_val`) keys on the `legacy_field` column, not the ordinal;
- `check_identifier_retirement.py` RC=0 over 47 wire identifiers; none of the five words is one.

**So the bit ordinals are runtime-only and reclaimable.** This is a genuinely clean result and the *reason* it is clean (generation direction, verified writer set) is what makes it durable rather than lucky.

---

## 3. FINDINGS — ranked by blast radius

### F-1 (HIGH) — `FOREACH_GLOBAL_CFG_FIELD`'s complement: 32 live global keys with no row; 30 are determinism-bearing and parsed by unguarded `atof`

**The domain.** `ControllerConfig_Load` (`ControllerConfig.hpp:2440-3627`) accepts a key three ways: the registry walker (`:2549-2553`), the `CFG_PARSE_*` table macros (`:2577-2620`), and inline `strcmp` branches. Only the first is registry-backed.

**The complement, computed this session** (parse-macro invocations + `strcmp(key,…)` literals minus all registry key sets, enum-value strings excluded):

**26 × `CFG_PARSE_FPN` — determinism-bearing `FPN_Binary<F>`, no row:**
`r2_threshold` `:2623` · `slope_scale_buy` `:2624` · `max_shift` `:2625` · `vol_mult_min` `:2628` · `vol_mult_max` `:2629` · `filter_scale` `:2630` · `momentum_r2_min` `:2635` · `ror_tp_bonus` `:2636` · `momentum_tp_r2_min` `:2637` · `momentum_sl_r2_max` `:2638` · `squeeze_decay` `:2639` · `offset_adapt_scale` `:2640` · `stddev_adapt_scale` `:2641` · `vol_adapt_scale` `:2642` · `breakout_min` `:2643` · `regime_volatile_stddev` `:2647` · `regime_vol_spike_ratio` `:2648` · `spike_threshold` `:2658` · `spike_spacing_reduction` `:2659` · `min_book_imbalance` `:2944` · `vol_scale_min` `:2945` · `vol_scale_max` `:2946` · `no_trade_band_mult` `:2947` · `regime_model_weight` `:2949` · `danger_warn_stddevs` `:2952` · `danger_crash_stddevs` `:2953`

**4 × `CFG_PARSE_FPN_POS`:** `offset_stddev_min` `:2828` · `offset_stddev_max` `:2829` · `xgb_subsample` `:3003` · `xgb_colsample_bytree` `:3004`
**2 × `CFG_PARSE_INT`:** `auto_kill_on_drift` `:3167` · `prediction_normalize` `:3219`
**22 × inline `strcmp`** (strings/enums/aliases; the string cohort is legitimately blocked on `.F.4e` KIND_STRING): `auto_stamp_secret` `:3139` · `calibration_log_path` `:2808` · `ensemble_bandit_eta` `:3034` · `ensemble_blend_mode` `:3021` · `ensemble_trade_reward_mult` `:3065` · `exit_bandit_lr` `:3051` · `exit_signal_model_dir` `:2802` · `gate_ema_alpha` `:3454` · `health_log_path` `:3147` · `held_out_stamp_secret` `:3132` · `horizon_list` `:3109` · `ml_model_path` `:3432` · `notify_command` `:2964` · `oms_bench_enabled` `:3426` · `oms_event_log_mode` `:3415` · `peak_model_path` `:3442` · `reconcile_dry_run` `:3169` (DEPRECATED shim, stated) · `regime_model_path` `:3437` · `risk_scale_by_confidence` `:2701` (DEPRECATED shim, stated) · `use_real_money` `:2931` (alias, stated: *"there is NO cfg field"*) · `valley_model_path` `:3447` · `xgb_tree_method` `:3006`

**The bound I applied to my own finding — and it holds:**

```
CFG_PARSE_PCT   total = 21   UNREGISTERED = 0
```

**Every percent/money-shaped manually-parsed key has a registry row.** So **no capital field escapes the D-254 no-margin sweep** — `CFG_FAULT_CAPITAL_MALFORMED` / `CFG_FAULT_CAPITAL_OUT_OF_RANGE` (`CfgFieldRegistry.hpp:256-257`) fire only for `CAPITAL_BOUND_*`-tagged rows, and the complement contains none. That is a real, load-bearing negative result and it caps this finding at HIGH-not-CRITICAL.

**But the sister fault is NOT covered.** `CFG_FAULT_FEATURE_MALFORMED = 1u << 3` exists precisely for *"a non-capital FEATURE field (FPN/float regime/ema/rolling/ML threshold) was MALFORMED — determinism-bearing, refuse-don't-coerce (C1/C2)"* (`CfgFieldRegistry.hpp:259`). It is raised only inside `tt::cfg_parse_field`, which the walkers reach via `&cfg.cfg_load_fault_flags` (`ControllerConfig.hpp:2550`, `:2568`). The table macro does not:

```cpp
#define CFG_PARSE_FPN(name)                                                    \
  if (strcmp(key, #name) == 0) {                                               \
    cfg.name = FPN_FromDouble<F>(atof(val));                                   \
    continue;                                                                  \
  }
```
— `CoreFrameworks/ControllerConfig.hpp:2577-2581`

**No fault pointer, no clamp, no malformed detection.** `atof("banana")` → `0.0`; `atof("1,5")` → `1.0`. Both silent. The guard the codebase built for this exact class cannot see these 30 fields because it is rows-forward over a registry they have no row in.

**Live sharded-path reach (this is not a dead-code finding):**

```cpp
new_regime = Regime_Classify(&state->nodes[slot].regime_state, &sig, &resolved_cfg);
```
— `CoreFrameworks/ControllerEventLoop.hpp:2829-2830` (the sharded slow path)

`Regime_Classify` (`Strategies/RegimeDetector.hpp:745-747`, takes `const ControllerConfig<F>*`) reads `cfg->regime_model_weight` `:803` and `cfg->regime_vol_spike_ratio` `:811`. `calls_graph_diff.sh` RC=0 confirms the regime path is live, not orphaned. `min_book_imbalance` likewise gates entries at `ControllerEventLoop.hpp:2419-2443`; `spike_threshold` at `:3337-3342`.

**The cohort-incompleteness that makes this predictive** (M9 / `feedback_enumerate_set_before_categorical_claim`) — of the 6 regime-detection knobs:

| Field | Registry status |
|---|---|
| `regime_crossover_threshold` | PER_NODE row |
| `regime_slope_threshold` | PER_NODE row |
| `regime_strong_crossover` | PER_NODE row |
| `regime_r2_threshold` | PER_NODE row |
| `regime_hysteresis` | PER_NODE row |
| **`regime_vol_spike_ratio`** | **NO ROW** |
| **`regime_volatile_stddev`** | **NO ROW** |
| **`regime_model_weight`** | **NO ROW** |

Five migrated; three did not, **with no stated reason at any of the three sites.** That is the § C.1 `drift_history` correlation reproduced exactly: *the members with no stated exclusion reason are the members that turn out to be the finding.*

**Second-order H22 consequence:** an unregistered global cannot be per-node-overridden, because the `node_N_` override surface is registry-generated. `node_0_regime_vol_spike_ratio=` is **unexpressible** — and, correctly, it hard-refuses boot (`ControllerConfig.hpp:3479-3482`, `CFG_FAULT_UNKNOWN_KEY`).

**The asymmetry that frames the whole finding:**
- **PER-NODE key space:** an unrecognized `node_*`/`core_*` key sets `CFG_FAULT_UNKNOWN_KEY` and **REFUSES BOOT** (`ControllerConfig.hpp:3474-3483`).
- **GLOBAL key space:** an unrecognized key is **silently ignored.** The code says so: *"the broader global-unknown refuse waits on the multi-parser unification (N1, task #10)"* (`ControllerConfig.hpp:3470-3471`).

The complement lives entirely on the unguarded side. This is the `node_3_stop_loss_pct` live precedent's global-side twin.

---

### F-2 (HIGH for guard correctness; ∅ drift today) — the H16 complement check reads its DOMAIN from a hand-maintained mirror

This is the sharpest instance of the meta-pattern on my shard, because the check has the **right shape** and is still blind.

```cpp
inline constexpr uint16_t ENROLLED_METADATA_BITS = (0u FOREACH_METADATA_BIT(X_GATHER_METADATA_BITS));
inline constexpr uint16_t EXEMPT_FROM_FOREACH_METADATA_BIT = CfgFieldDescriptor::NO_FLAT_FIELD;
// All metadata bits in use (update when new bit added to MetadataFlag enum):
inline constexpr uint16_t ALL_METADATA_BITS_IN_USE = ... ;   // 15 hand-written ORs
static_assert((ALL_METADATA_BITS_IN_USE & ~(ENROLLED_METADATA_BITS | EXEMPT_FROM_FOREACH_METADATA_BIT)) == 0u, ...);
```
— `CoreFrameworks/CfgFieldRegistry.hpp:1530-1566`

`ENROLLED` is *derived* from the registry. `EXEMPT` is hand-written but tiny and self-documenting (`:1534-1539`). **`ALL_METADATA_BITS_IN_USE` — the domain side — is a 15-line manual mirror of the enum, and its own comment (`:1541`) admits it: *"update when new bit added to MetadataFlag enum."*** Add a 16th bit and forget the mirror, and the assert stays **vacuously green** (Class-51 shape at a complement check).

**Verified: no drift today.** The enum (`:154-189`) declares bits 1-15 plus the `HAS_SIDE_EFFECT` alias (`:188`, `= MANUAL_PARSER`) plus bit 0 RESERVED (`:155`); `ALL_METADATA_BITS_IN_USE` lists exactly those 15. And `ALL_METADATA_BITS_IN_USE` has **exactly one consumer** — the `static_assert` itself. Nothing cross-checks it against the enum body.

C++ has no enum reflection, so a compile-time derivation isn't available — but a **Python text-parse of the enum body is**, and it is precisely what `check_meta_registry.py:84` already does for registry `#define`s. The closure is a known-shape extension, not new infrastructure (`feedback_audit_canonical_sister_before_new_infra`).

**Two riders at the same site:**
- **F-2a (LOW, doc):** `H16` in `CLAUDE.md` names `FOREACH_DERIVED_FILTER` as the enforcing registry. **That registry does not exist** — `check_meta_registry.py` finds 68 `FOREACH_*` and none is it; the only hits are in `DESIGN_SPECS/`. The spec itself already recorded the correction (*"Non-existent `FOREACH_DERIVED_FILTER` Level-1 references in spec body REMOVED … `FOREACH_METADATA_BIT` IS the canonical metadata-bit registry"* — `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md:15`) but **`CLAUDE.md`'s H16 row was never updated.** Likewise H16 cites CI check `test_metadata_bit_to_derived_filter_coverage`, which returns zero hits anywhere — the real enforcement is the `static_assert` at `:1560`. Same shape as the D-304 `test_meta_registry_coverage` name-fix already recorded in H15.
- **F-2b (LOW):** `FOREACH_METADATA_BIT:1439` enrolls bit 10 under the **retired alias** `has_side_effect`/`HAS_SIDE_EFFECT`, not `MANUAL_PARSER`. The alias carries *"Alias retained for 1 ship transition; remove at v5.15.5.F.4d codification"* (`:184-187`) — we are at `.E.1.2`, long past. Removing the alias per its own instruction would break the registry row, the generated `g_{global,per_node}_cfg_has_side_effect_mask` symbols (consumed at `tests/controller_test.cpp:1623-1624`, `:28980`, `:28999`), and 14 rows of `CFG_COMPOSE_AUDIT_DECISIONS` (`:1600`, `:1615`, `:1630`).
- **F-2c (LOW, H15 blind spot):** `CFG_COMPOSE_AUDIT_DECISIONS` (`CfgFieldRegistry.hpp:1589`) is a real X-macro coverage registry over (enrolled bits × composed masks), but its name does not start with `FOREACH_`, so `check_meta_registry.py:84`'s pattern `^#define\s+(FOREACH_\w+)\s*\(\s*\w+\s*\)` **cannot see it** and H15 does not apply. Its header comment says *"12 enrolled bits × 3 composed masks = 42 cells"* (`:1586`) — 42 is right, 12 is stale (14 enrolled).

---

### F-3 (MED) — `ML_CFG_FLAG_AUTOPOPULATE_FROM_SEPTUPLE` is a 7-of-12 hand mirror, and it CLOBBERS

```cpp
#define ML_CFG_FLAG_AUTOPOPULATE_FROM_SEPTUPLE(target_flags, _confidence, _composite, _bandit, _exit_bandit, _use_exit_model, _vol_scaling, _lazy_rebuild) \
    do { uint16_t _new_flags = 0; ... (target_flags) = _new_flags; } while (0)
```
— `ML_Headers/MlCfgFlagRegistry.hpp:143-154`, invoked in production at `CoreFrameworks/ControllerConfig.hpp:1997-2004`

The registry has **12** rows (`:64-76`); the companion covers the **first 7**. The five uncovered rows — `RIDGE_WITHIN_HORIZON`, `RIDGE_ACROSS_HORIZONS`, `EXIT_BLENDER_MODE`, `RIDGE_ONLINE_CORR`, `PER_HORIZON_BARRIER_BLEND` (`:72-76`) — have **no line in the companion at all**, and the final statement is an **assignment**, not an OR, so their default is *clobbered to 0* rather than *declared*.

**Not a live bug today** (all five happen to want OFF) but the mechanism **cannot express a default-ON for them** — and its sister registry needed exactly that: `RISK_CFG_FLAG_AUTOPOPULATE_FROM_QUINTUPLE` sets `kill_switch_enabled=1` and `mtm_kill_switch_enabled=1` (`ControllerConfig.hpp:2008-2013`), both safety-critical. A future safety-critical ML flag added at row 13 would silently default OFF.

**Two independent tells that the codebase already knows this shape is wrong:**
1. `OPS_CFG_FLAG_AUTOPOPULATE_FROM_PAIR` was **RETIRED for precisely this reason** — *"Cohort growth to 4 entries … makes the FROM_PAIR shape inadequate"* (`OpsCfgFlagRegistry.hpp:58-71`) — and replaced with direct `= 0`. The ML companion grew 7→12 and was never revisited.
2. The call-site comment still reads *"ml_cfg_flags defaults: all 7 flags off"* (`ControllerConfig.hpp:1996`), and the file header still says *"7 entries"* / *"all 7 entries below pass all 5 criteria"* three times (`MlCfgFlagRegistry.hpp:15,38,40`). Per SUBAGENT_ARMING § 2.5 the code is truth: it is 12.

Sibling companions verified complete: LIFECYCLE 3/3 (`LifecycleCfgFlagRegistry.hpp:74-81`), GATE 6/6 (`GateCfgFlagRegistry.hpp:74-84`), RISK 5/5 (`RiskCfgFlagRegistry.hpp:60-69`). **ML is the lone non-conformer** — enumerated, not assumed.

---

### F-4 (MED) — `FOREACH_CFG_GATE_GLOBAL`'s empty-set justification is wrong about all three of its members

The registry is deliberately empty and that is *architecturally* fine — the H18 sidecar default is `return true` (`MemHeaders/CfgGateRegistry.hpp:165`, `:173`; documented `:40-47`). The defect is the **accounting note**, which is the only thing standing in for a complement check:

```
/* No entries at .B.2: trading_mode + ml_buy_threshold both use default always-emit gate
 * (matching legacy emit_when = 1 for these rows). gap_acceptable_threshold migration
 * deferred to .B.3 per coding-time discovery (FOREACH_GLOBAL_CFG_FIELD doesn't auto-gen
 * struct fields; manual cfg storage cleanup is .B.3 scope). */
```
— `MemHeaders/CfgGateRegistry.hpp:114-117`

Computed complement at HEAD — global rows carrying `STAMP_BOUND_CFG_DERIVED` = **`trading_mode`, `gap_acceptable_threshold`, `held_out_fraction`**. Against the note:

| Member | Note says | Reality at HEAD |
|---|---|---|
| `trading_mode` | default always-emit | ✅ correct |
| `ml_buy_threshold` | "uses default always-emit gate" | ❌ **not a global row** — it is a `FOREACH_PER_NODE_CFG_FIELD` row. Migrated between registries; note never followed |
| `gap_acceptable_threshold` | "deferred to .B.3" | ❌ **expired deferral on a false premise.** We are at `.E.1.2`. The stated blocker — *"FOREACH_GLOBAL_CFG_FIELD doesn't auto-gen struct fields"* — is now FALSE: `ControllerConfig.hpp:1411` does exactly that |
| **`held_out_fraction`** | — | ❌ **NOT NAMED AT ALL.** Added later ("Phase F HIGH-1", per `CfgFieldRegistry.hpp:1475`); nothing re-derived the set |

**`held_out_fraction` is this shard's `drift_history`** — the one member of an exclusion set with no stated reason anywhere. Its behavioural consequence today is benign (always-emit is almost certainly right for a held-out split fraction), but the *set* was never re-enumerated after it joined. Textbook M9.

**Related, and correctly documented — no finding:** six `STAMP_BOUND_CFG_DERIVED` rows live in `FOREACH_ML_CFG_FLAG` / `FOREACH_GATE_CFG_FLAG` and are **structurally ungate-able** (`lookup_populate` switches on `FIELD_IDX_{PER_NODE,GLOBAL}_*`, which bitmap rows do not have). The walkers state it: *"No gate lookup (the bit IS the value; absence = 0)"* — `MemHeaders/CfgGateRegistry.hpp:377`, `:388-393`. Excluded-with-stated-reason. Clean.

**Also clean:** the per-node sidecar's rows-forward direction — computed `gate rows with NO flagged source row = ∅` (all 16 reference a real `STAMP_BOUND_CFG_DERIVED` per-node row).

---

### F-5 (MED) — `FOREACH_PER_NODE_ARRAY_OVERRIDE` covers 2 of 3; the third merges by ad-hoc inline last-wins, and its rationale contradicts its consumer

Registry (`CfgFieldRegistry.hpp:1100-1103`) has `risk_pct ← node_risk_pct` and `max_drawdown_pct ← node_max_drawdown_pct`. Its purpose is explicit: close *"the dual-source-storage hazard, D-273/B"* so *"nodes[c] is the ONE authoritative per-node read"* (`:1114-1120`).

Complement over the TRANSITIONAL arrays in `FOREACH_MANUAL_PER_NODE_FIELD`:

| Array | Route | file:line |
|---|---|---|
| `node_risk_pct` | `ARRAY_OVERRIDE` | `:1102` |
| `node_max_drawdown_pct` | `ARRAY_OVERRIDE` | `:1103` |
| `node_strategies` | `NO_FLAT_FIELD_SYNC` | `:1053` |
| `node_overrides` | `ResolveForCore` (retires WIP2f) | `:932` |
| **`node_time_exit_ticks`** | **NONE** | `:929` |

`node_time_exit_ticks` is parsed (`ControllerConfig.hpp:3264`) and is **live** — but resolves via a hand-written last-wins at its single consumer instead of the sidecar:

```cpp
uint32_t max_hold = cfg.node_time_exit_ticks[node_id];
if (max_hold == 0) max_hold = cfg.nodes[node_id].max_hold_ticks;
```
— `CoreFrameworks/ControllerEventLoop.hpp:3764-3765`

**Not inert** — the operator's value IS honored, and the read is properly `node_id`-indexed (H22-clean, not Class 26). Two real defects:

1. **The registry rationale is FALSE at the consumer.** `CfgFieldRegistry.hpp:929` says *"nodes[c].max_hold_ticks authoritative"*; the code makes the **legacy array** authoritative whenever nonzero. Per SUBAGENT_ARMING § 2.5, code is truth — this comment actively misleads anyone auditing the WIP2g array deletion.
2. **The D-273/B dual-source hazard the sidecar closed for two capital arrays remains open for the third**, in a different mechanism, with the sidecar's own `CRITICAL ORDER` warning (`:1130-1132` — *"applied BEFORE the walker, the override is silently dropped … = re-arms the founding bug"*) not applying to it.

This is *not* the `node_overrides` shape Check 6 already flags (`fee_floor_mult` / `partial_exit_pct` / `tp2_mult`, per the tool's INFO warning); Check 6 matches `cfg.X + cfg.node_overrides[c].X`, which the parallel-array form does not present.

---

### F-6 (MED) — `tui_render_interval`: operator-settable, present in 9 cfg files, **parsed by nothing**

The one *genuinely unaccounted, provably inert* key found this session — the live precedent's exact shape.

Computed the complement `engine.cfg keys − (all registry keys ∪ CFG_PARSE_* ∪ strcmp keys ∪ per-node suffixes)` → 9 unrecognized. Eight resolve to a **second, entirely separate parser over the same file** at `DataStream/BinanceCrypto.hpp:1031-1046` (`symbol`, `use_testnet`, `use_binance_us`, `poll_timeout_ms`, `reconnect_delay`, `wind_down_minutes`, `tui_enabled`, `log_file`) — homed under the "multi-parser unification (N1, task #10)" the `ControllerConfig.hpp:3470-3471` comment names.

**`tui_render_interval` resolves to nothing.** It appears at `engine.cfg:183`, `engine.cfg.example:314`, `backtest.cfg:178`, `engine_sharded.cfg:280`, and `models/classification/test_case_{01..05}/engine.cfg:178` — nine files, all with the explanatory comment `# render every N ticks (higher = less terminal thrash)` — and a codebase-wide search finds **no reader, no parser, no struct field.** The operator sets it; it does nothing; nothing warns.

**Related, and it straddles the emit/display shard — flagging, not chasing:** `session_asian_mult` / `session_european_mult` / `session_us_mult` / `session_overnight_mult` are rendered as editable GUI controls at `GUI/SettingsPanel.hpp:447-452` and documented at `engine.cfg.example:395-398`, but `ControllerConfig_Load` does not parse them; the values consumed at `CoreFrameworks/PortfolioController.hpp:1603-1613` come from `ctrl->config.session_*_mult` on a **different struct with a different parser**, on the path `scan_class_44_cfg_orphan.py` reports as dead (`MASK_OPS_CFG_SESSION_FILTER_ENABLED` dead-read at `PortfolioController.hpp:1597`, `:1899`). **Overlap:** `SettingsPanel.hpp`'s descriptor table is a *third* parallel cfg surface and belongs to the emit/display shard — I am naming it, not auditing it.

---

### F-7 (LOW) — every registry row-count stated in prose is stale

Actual vs stated, HEAD `7240f3d`:

| Registry | Actual | `MetaRegistry.hpp` | Other prose |
|---|---|---|---|
| `FOREACH_GLOBAL_CFG_FIELD` | **59** | 47 (`:38`) | 47 (`CfgFieldRegistry.hpp:335`); 48 (`ControllerConfig.hpp:1394`); "~47" (`CfgFieldRegistry.hpp:10`) |
| `FOREACH_PER_NODE_CFG_FIELD` | **88** | 93 (`:39`) | "~79" (`CfgFieldRegistry.hpp:10`, `:29-33`, `:298`) |
| `FOREACH_ML_CFG_FLAG` | **12** | — | "7 entries" ×3 (`MlCfgFlagRegistry.hpp:15,38,40`); "all 7 flags off" (`ControllerConfig.hpp:1996`) |

Pure `feedback_name_members_never_tallies_in_docs` — a tally is stale on the commit that writes it and fails silently. Worth a `[DERIVED]`-block re-derive fence rather than hand-correction. **Note the 88 is not un-anchored:** `check_per_node_registry_integrity.py` Check 1 re-derives it (`Check 1 PASS: 88 per-node cfg fields`), so the *code* side is self-checking; only the prose drifted.

---

## 4. HAZARDS

- **HAZ-1 (blocks a naive guard, high confidence).** Any struct↔registry coverage guard written for the cfg surface **must branch on which struct it is auditing.** `PerNodeCfg<F>` is exclusively generated (Check 2 enforces) → complement is vacuous; `ControllerConfig<F>` is additively generated → complement is 32. A guard that treats them symmetrically reports 32 false positives on `PerNodeCfg<F>`'s siblings or, worse, "closes" the global side by allowlisting all 32.
- **HAZ-2 (the domain-mirror trap generalizes).** F-2's shape — *a complement check whose domain side is hand-written* — is the thing to sweep for codebase-wide, not just here. Any `ALL_*_IN_USE` / `EXPECTED_*` / `KNOWN_*` constant enumerating a domain the compiler could not derive is a candidate. It looks exactly like a real complement check in review.
- **HAZ-3 (guard-set blindness compounds).** Three independent guards over the cfg surface all take their domain from `FOREACH_{GLOBAL,PER_NODE}_CFG_FIELD` and therefore share one blind spot: the `FEATURE_MALFORMED` fault (rows-forward via `tt::cfg_parse_field`), `check_per_node_registry_integrity.py` Check 10 UNINDEXED-GLOBAL (scan set built from *per-node-migrated* fields — `:454-457`), and Check 11 flat-write (`:891`, "88 per-node fields tracked"). **A field with no row is invisible to all three.** Adding a fourth rows-forward guard buys nothing.
- **HAZ-4 (the exemption registry is per-axis, not universal).** `FOREACH_MANUAL_PER_NODE_FIELD` gives the *per-node* string/transitional exemptions a home with a mandatory rationale column and bidirectional CI (Checks 3+4). **There is no global sister.** The 22 global `strcmp` keys — including the `.F.4e`-blocked string cohort, which is *exactly* the same excuse the per-node registry documents per-row — have no such home. That is why F-1's members carry no stated reason: there is nowhere to state one.
- **HAZ-5 (H16's citation chain is broken in the always-loaded doc).** `CLAUDE.md`'s H16 row names a registry and a CI check that both do not exist (F-2a). A future agent following H16 literally will look for `FOREACH_DERIVED_FILTER`, not find it, and either conclude the invariant is unenforced or build a duplicate. `DESIGN_SPECS` already recorded the correction; `CLAUDE.md` did not receive it.
- **HAZ-6 (expired deferrals do not self-report).** F-4's `gap_acceptable_threshold` deferral is pinned to a premise that has since become false, and F-2b's alias is past its own stated removal ship. Neither is tracked anywhere a tool reads. `feedback_no_unhomed_debt_code_smell` — an in-comment "deferred to .B.3" is unhomed debt.

---

## 5. SPOTS MOST WORTH AN ADVERSARIAL REFUTE (for the paired a-class)

1. **F-1's severity — attack from both sides.** *(a) Refute the finding:* argue all 30 unregistered FPN fields are strategy-tuning knobs where a coerced `0.0` is a *conservative* value (tighter gate, no trade) rather than a capital risk, so `atof`'s silence is tolerable; and that `CFG_PARSE_PCT`'s clean 0-unregistered result proves the boundary was drawn deliberately, not accidentally. *(b) Refute my hedge:* pick the worst member and price it — I flagged `min_book_imbalance` (`ControllerEventLoop.hpp:2419-2443`) where `0` **disables the gate entirely** ("`cfg.min_book_imbalance==0` disables the gate"), so a typo'd value silently *removes* a live entry filter. That is coerce-to-permissive, not coerce-to-conservative. **Enumerate all 30 by their zero-semantics** — I did not, and it is the discriminator between MED and HIGH. This is where I am least certain.
2. **My "no capital field escapes" claim (F-1's bound).** I established it from `CFG_PARSE_PCT total=21 / UNREGISTERED=0`. **Try to break it three ways:** (i) is `CFG_PARSE_PCT` really the *only* money-typed parse macro at HEAD? — `CFG_PARSE_MONEY` / `CFG_PARSE_MONEY_POS` were deleted (`ControllerConfig.hpp:2583-2588`), verify no third route exists; (ii) can a `CFG_PARSE_FPN` field reach a money path via a `Money_FromBinary` seam (H4 crossing)? `ror_tp_bonus` and `momentum_tp_r2_min` are the ones to chase; (iii) is `Money_FromString` (`:2594`) itself malformed-safe, or does it share `atof`'s silence? If (iii) fails, the finding escalates to touch capital after all.
3. **F-2's "no drift today".** I verified 15 enum bits against 15 mirror entries by reading `CfgFieldRegistry.hpp:154-189` and `:1542-1557`. **Re-derive it independently** — parse the enum body with a script rather than by eye, and specifically check whether bit 0 (`RESERVED`, `:155`) should be in `ALL_METADATA_BITS_IN_USE` or whether "RESERVED but not in-use" is itself an unstated third category the assert cannot express.
4. **F-3's "not a live bug".** I claimed the 5 uncovered ML rows want OFF today so the clobber is benign. **Refute by finding a path where `cfg.ml_cfg_flags` is written before `ControllerConfig.hpp:1997`** — I enumerated writers and found only `:1809-1813` (per-node copy, after) and the parser walkers `:2898-2899` (after Load). If any default-setting code runs *before* `:1997`, the assignment silently discards it. Also check whether `PER_HORIZON_BARRIER_BLEND` (`.A.5`, carries `STAMP_BOUND_CFG_DERIVED`) has a stamp-parity expectation that a clobbered default would break.
5. **F-6's `tui_render_interval` = truly inert.** I searched the engine tree and found no reader. **Try to break it:** is there a `foxml_suite` / GUI / tools-side reader outside the dirs I scanned? Does any *other* config loader (backtest cfg parser, `controller.cfg`, `engine_sharded.cfg`) consume it? Note `backtest.cfg:178` carries it too — if the backtest parser reads it, my "parsed by nothing" claim is wrong and the finding collapses to a `.example` hygiene item.
6. **F-5's H22-clean assessment.** I called `cfg.node_time_exit_ticks[node_id]` per-shard-pure because it is node-indexed. **Probe the WIP2g deletion path:** when the TRANSITIONAL arrays retire, does anything guarantee `nodes[c].max_hold_ticks` receives the array's value first? The `ARRAY_OVERRIDE` sidecar exists precisely to make that migration safe for its two members; `node_time_exit_ticks` has no such mechanism, so its retirement is a *manual* step nothing enforces — and the sidecar's own `CRITICAL ORDER` note says getting this wrong "re-arms the founding bug".
7. **The clean bitmap verdict (§ 2) — attack its generality.** I proved the writer set is `MASK_*`-only for the 5 cfg-flag words *at HEAD*, and that ordinals are never wire-visible. Per `feedback_dont_generalize_substrate_before_input_space_known`, that is a fact about these 5 words today, **not** about `SlowPathGateState.flags`, `node_state_flags`, `PerNodeStateFlags`, or the OMS bitmaps — which belong to the state-bitflag shard. If any of *those* is persisted by raw word, the positional-ordinal H21 hazard is live there even though it is dead here. **Worth an explicit cross-shard handoff rather than an assumption.**
8. **The whole shard's framing.** I classified 9 of 15 registries as having no gap. **Refute the classification, not the contents:** specifically challenge #15 `FOREACH_SLOW_PATH_GATE` — I called it SOURCE-OF-TRUTH ("a gate exists because a consumer wants it"), but one could argue its authoritative domain is *"every cfg flag whose read sits on the slow path"*, in which case there IS a complement (e.g. `MASK_LIFECYCLE_CFG_PARTIAL_EXIT_ENABLED` is read on the slow path with no cached gate row). If that framing wins, #15 moves to COVERAGE and gains a computable complement.

---

## 6. OPEN QUESTIONS (for Caramel)

- **OQ-1 (the shard's real decision).** F-1's 32 keys: (a) migrate the 30 FPN/INT rows into `FOREACH_GLOBAL_CFG_FIELD` (they need no new KIND — `KIND_DOUBLE` covers them; this also gives them GUI/tooltip/clamp/`WARN_ON_CLAMP` for free and retires 30 `CFG_PARSE_FPN` lines); (b) leave them and add a *global* exemption registry with a mandatory rationale column, mirroring `FOREACH_MANUAL_PER_NODE_FIELD` (closes HAZ-4, makes the complement visible without moving anything); or (c) close the class at the root by making unknown **global** keys refuse boot the way unknown `node_*` keys already do (`ControllerConfig.hpp:3474-3483`) — which requires (a) or (b) first, or boot breaks on the 32.
- **OQ-2.** Should the H16 domain be derived by a Python enum-parse (extending `check_meta_registry.py`'s existing `#define` scan to enum bodies), retiring the `ALL_METADATA_BITS_IN_USE` mirror? This is the single highest-leverage guard fix on the shard — it converts a structurally-blind check into a real one.
- **OQ-3.** F-3: extend `ML_CFG_FLAG_AUTOPOPULATE_FROM_SEPTUPLE` to 12 args, or **retire it** the way `OPS_CFG_FLAG_AUTOPOPULATE_FROM_PAIR` was retired (`OpsCfgFlagRegistry.hpp:58-71`) in favour of a registry-walked default-emit? The OPS precedent argues retire; but RISK genuinely needs default-ON expressiveness, so a walked `EMIT_<DOMAIN>_CFG_FLAG_DEFAULT` with a per-row default column would serve all five domains uniformly.
- **OQ-4.** F-4/HAZ-6: should an in-comment deferral ("deferred to .B.3") be mechanically detectable — i.e. does the sprint want a `[DEFERRED]_[<ship>]` tag in the in-code tag grammar so `check_code_tag_blocks.py` can flag one whose ship has closed?
- **OQ-5.** Does the exempt-side of the cfg partition want a **reason column** (`STRING_PENDING_F4E` / `DEPRECATED_SHIM` / `ALIAS_NO_FIELD` / `SECOND_PARSER` / `TRANSITIONAL`)? Repeating the § C.1 correlation from the NodeContext pass: on this shard, `held_out_fraction` (F-4) and `tui_render_interval` (F-6) were the two members with **no stated reason anywhere**, and they were the two real findings. That correlation is now 2-for-2 across two independent surfaces — it is the argument for the column.

---

**Key files (absolute):**
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/CfgFieldRegistry.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerConfig.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/MetaRegistry.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/LifecycleCfgFlagRegistry.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/GateCfgFlagRegistry.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/RiskCfgFlagRegistry.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/OpsCfgFlagRegistry.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/SlowPathGateRegistry.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/ML_Headers/MlCfgFlagRegistry.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/MemHeaders/CfgGateRegistry.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/Strategies/RegimeDetector.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/Strategies/MeanReversion.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerEventLoop.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/DataStream/BinanceCrypto.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/GUI/SettingsPanel.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/engine.cfg` ·
`/home/caramel/code/tick-trader-percore-workspace/tools/check_per_node_registry_integrity.py` ·
`/home/caramel/code/tick-trader-percore-workspace/tools/check_meta_registry.py` ·
`/home/caramel/code/tick-trader-percore-workspace/tools/scan_class_44_cfg_orphan.py` ·
`/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/reports/2026-08-15-ui-consolidation/i-class-nodecontext-partition.md`