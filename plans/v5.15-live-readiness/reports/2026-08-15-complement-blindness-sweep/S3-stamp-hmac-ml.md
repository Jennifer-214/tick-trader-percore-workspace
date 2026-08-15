---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: S-3 — complement-blindness sweep, shard 3/5: the STAMP / HMAC + ML family
agent_class: i-class
delivered: 2026-08-15
ground: engine HEAD 7240f3d, branch feat/v5.15-live-readiness
headline: S-1 CRITICAL — the cfg-derived stamp↔runtime drift check is unconditionally vacuous for every stamp the engine can accept; 36 STAMP_BOUND_CFG_DERIVED fields are emitted, parsed, and never compared, because the gate reads a group bit with no emit-side producer
orchestrator_verification: "CONFIRMED INDEPENDENTLY 2026-08-15. Tree-wide grep for STAMP_SET(..., inference_cfg) returns exactly 3 sites: NodeModelZoo.hpp:459 (CIRCULAR — gated on STAMP_HAS(sr, inference_cfg) at :458, so it propagates the bit from a stamp that already had it and never originates it), StampBoundModelConstRegistry.hpp:715 (the QUARANTINED AUTOPOPULATE dispatcher), and :747 (the PARSER macro). Stamp_AssembleAndEmit references inference_cfg only in comments and for the DIFFERENT standalone bit inference_cfg_bandit_blend_ratio (:236). No origination site exists."
operator_decision_owed: OQ-1 (S-1 remediation — (a) gate per-field on handle.has_<name>, no wire change but may surface latent real drift as new boot REFUSEs; (b) set the group bit at emit, H9/H21 wire bump; (c) retire the bit + the 9 dead rows, H21 tombstone)
sister_reports: S1-capital-wire-persist.md · S2-cfg-surface.md · S4-nodectx-state-bitflags.md · S5-emit-display-and-set-closure.md
---

# S-3 — COMPLEMENT-BLINDNESS sweep, shard 3/5: the STAMP / HMAC + ML registry family

**Ground:** engine `/home/caramel/code/FoxML_Trader_v2`, HEAD `7240f3d` (verified `git rev-parse`), branch `feat/v5.15-live-readiness`. Read-only pass; nothing built, nothing edited.
**Scope:** the 16 registries at `CoreFrameworks/MetaRegistry.hpp:53,54,63,64,65,70,71,72,73,76,77,91,92,107,110,111`.

**Headline:** the shard is *not* clean. The single highest-value find is **not** a missing registry row — it is a **severed producer** that makes the entire cfg-derived stamp↔runtime drift check **unconditionally vacuous for every stamp the engine is capable of accepting**. All 36 `STAMP_BOUND_CFG_DERIVED` cohort members are emitted into the HMAC body, parsed back, and then compared behind a gate that is provably always `false`. That is the determinism hole the shard brief predicted, in its worst form: the fingerprint matches, the data is present on both sides, and the comparison silently never runs.

---

## 0. Method

Complements were computed mechanically (script under the session scratchpad; re-derivable), then every claim was re-verified by targeted read. Registry bodies were extracted by brace-balanced `X(...)` parsing with comment-stripping, so continuation-backslash and comment-embedded `X(` do not produce phantom rows.

**Corroboration discipline applied:** my first complement (`STAMP_BOUND_CFG_DERIVED` cohort vs `FOREACH_CFG_DRIFT_CHECK`) returned "21 uncovered". I did **not** report it — I checked for a sister path first and found `drift_check_from_derived` (`MemHeaders/CfgGateRegistry.hpp:516-602`), which walks the whole cohort by construction. **That first complement was a false positive and is withdrawn.** Chasing *why* it was a false positive is what surfaced S-1. Recording this because it is the methodological point: the complement is the *start* of the investigation, not the finding.

**Mechanical tools:** `tools/check_meta_registry.py` was attempted; the invocation was blocked by the repo's own `block_pipe_rc_read.sh` guard (Class-57 pipe-swallow protection) — I did not retry with a rewritten pipeline because H15/H19 enrollment is not the axis of this shard and all 16 registries are visibly enrolled at `MetaRegistry.hpp`. **Flagging as an un-run tool, not a green one.**

---

## 1. Per-registry verdict table

| # | Registry | Kind / generation direction | Authoritative domain | Complement check exists? | Verdict |
|---|---|---|---|---|---|
| 1 | `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG` (`ML_Headers/StampBoundModelConstRegistry.hpp:290`) | **SOURCE-OF-TRUTH.** 24 rows generate struct fields on 3 structs, parser, emitter, has-bits. Struct is generated FROM registry (`ModelInference.hpp:1456-1459`) → ⚠ false-positive guard applies | its own | rows-forward only | **CLEAN as a registry.** But see S-7 — 9 of its sibling POST_CFG rows are dead at emit |
| 2 | `FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG` (`:395`) | **SOURCE-OF-TRUTH**, 24 rows, same shape | its own | rows-forward only | **S-7** — 9 rows unreachable at emit |
| 3 | `FOREACH_STAMP_BOUND_MODEL_CONST` (`:494`) | **SOURCE-OF-TRUTH** — pure union macro of 1+2 (48 rows) | n/a | `..._COUNT >= 25` (`tests/controller_test.cpp:23692`) — floor, vacuous at 48 | **CLEAN** (union is structural) |
| 4 | `FOREACH_STAMP_BOUND_MODEL_CONST_GROUPS` (`:241`) | **COVERAGE** — must cover every `group` token used in registries 1+2 | the `group` column of the 48 rows | `GROUP_COUNT >= 6` (`controller_test.cpp:23696-23697`) — rows-forward floor | **⚠ GAP — S-4.** `environment_meta` is used by 5 rows, has **no** GROUPS row |
| 5 | `FOREACH_STAMP_BOUND_MODEL_CONST_STANDALONE` (`:260`) | **COVERAGE** — nominally covers every row with `group == "_"` | the 17 rows with `group == "_"` | `standalone_count >= 7` (`controller_test.cpp:23706-23707`) — rows-forward floor | **⚠ GAP — S-5.** Covers 6 of 17 real; 1 phantom row (`bandit`). Registry is superseded-but-not-retired |
| 6 | `FOREACH_STAMP_RESULT_FIELD_EXCLUSION` (`MemHeaders/CfgGateRegistry.hpp:748`) | **COVERAGE (collision, not partition)** — see § 2 | cross-walker name intersection | **YES — genuine bidirectional complement**, `tools/check_struct_field_uniqueness.py:163,175,188` | **CLEAN — 3/3 exact, zero drift both directions.** But NOT the prior art the new guard needs (§ 2) |
| 7 | `FOREACH_STAMP_BOUND_DERIVED_COHORT` (`CfgGateRegistry.hpp:285`) | **SOURCE-OF-TRUTH meta-walker.** Expands all 4 cfg registries unconditionally; a consumer *cannot* skip one (missing `X_<base>_<SCOPE>` = preprocessor error) | n/a | drift-impossible **by construction** | **CLEAN — and genuinely excellent.** The right pattern. Its *gate*, however, is the S-1 defect |
| 8 | `FOREACH_CFG_DRIFT_CHECK` (`ML_Headers/CfgDriftCheckRegistry.hpp:214`) | **COVERAGE**, 23 rows. Domain = stamp-recorded values with a runtime counterpart NOT already covered by the cohort walker | 8 CROSS_BINARY (MODEL_CONST-sourced) + 15 overlapping the cohort | none | **⚠ S-2** — 4 rows gated on a never-set bit → dead. Plus stale doc citing deleted `FOREACH_STAMP_BOUND_CFG` (`:209-212`) |
| 9 | `FOREACH_ARCH_FIELD_DRIFT` (`MemHeaders/ArchFieldDriftRegistry.hpp:68`) | **COVERAGE**, 4 rows — non-cfg-bound architectural drift | stamp-recorded architectural hashes with a runtime counterpart | none | **CLEAN** for its 4. `feature_hash`/`label_hash`/`build_flags`/`scaler_binding` all bind to real runtime fns |
| 10 | `FOREACH_FEATURE` (`ML_Headers/FeatureRegistry.hpp:524`) | **SOURCE-OF-TRUTH.** 40 rows, all `FEATURE_ENABLED`; generates the `FeatureId` enum, `FEATURE_NAMES/VERSIONS`, the enabled bitmap, `FEATURE_REGISTRY_HASH`, and both `Features_PackAll` packers | its own | `NUM_REGISTERED_FEATURES <= 64` (`:583`); array-size asserts (`:625-630`) are all registry-derived → structurally tautological | **Registry CLEAN. ⚠ S-3 lives at its consumer** — `MODEL_NUM_FEATURES=34` is decoupled from it with no assert |
| 11 | `FOREACH_TARGET` (`Backtest/LabelFunctions.hpp`) | **SOURCE-OF-TRUTH.** 11 rows → LABEL enum + `Label_*` leaves + `label_table` + `LABEL_REGISTRY_HASH` | its own | hash-pinned; `ARCH_FIELD_DRIFT` row `label_hash` enforces train↔serve identity | **CLEAN** |
| 12 | `FOREACH_SINGLE_ZOO_POST_LOAD` (`ML_Headers/NodeModelZoo.hpp:3451`) | **SOURCE-OF-TRUTH** dispatch list, 1 row | its own | `FOREACH_SINGLE_ZOO_POST_LOAD_COUNT 1` (`:3460`) is a **hand-maintained literal** ("Update when adding entries") | **CLEAN** (S-12, cosmetic mirror) |
| 13 | `FOREACH_ENSEMBLE_POST_LOAD` (`:3343`) | **SOURCE-OF-TRUTH** dispatch list, 5+ rows | its own | compile-time inclusion at all consumer sites | **CLEAN** |
| 14 | `FOREACH_IC_VARIANT` (`ML_Headers/ICVariantRegistry.hpp:56`) | **COVERAGE** — domain is the cfg-admissible value range, not itself | `confidence_ic_variant` range `INT(0, 0, 4)` (`CoreFrameworks/CfgFieldRegistry.hpp:683`) | none | **⚠ GAP — S-6.** Registry defines **1** of 5 admissible values; 1-4 → silent `0.0` |
| 15 | `FOREACH_DEGRADATION_CURVE` (`ML_Headers/ConfidenceScore.hpp:1071`) | **SOURCE-OF-TRUTH** enum + dispatch table, 4 rows (OFF/LINEAR/EXP/STEP) | its own | generates its own enum | **CLEAN.** Note cfg range `INT(0,0,2)` (`CfgFieldRegistry.hpp:747`) makes `STEP=3` cfg-unreachable — documented "(debug)", benign |
| 16 | `FOREACH_BARRIER_BLEND_MODE` (`ML_Headers/BarrierBlendModeRegistry.hpp:97`) | **SOURCE-OF-TRUTH** enum + flag composition, 5 rows | its own | generates its own enum | **CLEAN** as a registry. ⚠ S-10: cfg range `INT(0,0,3)` (`CfgFieldRegistry.hpp:776`) makes row 4 `BOTH_DOMINANT_DRIVES` unreachable, and the field is STAMP_BOUND + EXACT-drift-checked |

---

## 2. `FOREACH_STAMP_RESULT_FIELD_EXCLUSION` as prior art — **ENFORCED, but the WRONG SHAPE**

This materially changes the new guard's design, so stating it precisely.

**It is genuinely enforced.** `tools/check_struct_field_uniqueness.py` is a real check with teeth: it returns `1` on an unregistered collision (`:176-185`) and — importantly — **also warns on a stale sidecar entry** (`:188-192`). It is **bidirectional**. Current state is exactly clean: 3 collisions (`xgb_min_child_weight`, `xgb_seed`, `xgb_train_nthread`), 3 sidecar rows, **zero drift in either direction** (verified mechanically this session).

**But it is not a partition guard, and it never reads `ModelStampResult`.** Its domain is `MASTER_REGISTRIES ∩ OTHER_STRUCT_REGISTRIES` (`:163`) — a **name collision between two generating walkers**. The invariant it enforces is *"every name generated twice is registered"*, not *"every struct field is either covered or explicitly excluded"*. The struct body is never parsed.

**And a partition guard over `ModelStampResult` would be a category error anyway.** `ModelStampResult` (`ML_Headers/ModelInference.hpp:1417-1497`) is **generated FROM the registries** — `FOREACH_STAMP_BOUND_MODEL_CONST(X)` at `:1458` and `STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN()` at `:1481`. This is precisely the **⚠ FALSE-POSITIVE GUARD** the brief names: registry → struct, so coverage is structural and there is no complement to compute. The only manually-declared members are the 11 runtime-verdict fields at `:1424-1452`, and they carry an explicit stated exclusion — the section header literally reads `// === Runtime-only fields (NOT in registry) ===` (`:1423`).

**Recommendation.** Do **not** extend `FOREACH_STAMP_RESULT_FIELD_EXCLUSION` — it answers a different question, and its parent struct is generation-direction-inverted relative to `NodeContext`. **Do** copy two things from it:

1. **The bidirectional check** (`check_struct_field_uniqueness.py:188-192`). The `NodeContext` partition guard should flag a stale exempt-row as loudly as a missing one — otherwise the exempt list rots into an ever-growing allowlist that silences real findings. This is the direct answer to prior-art **OQ-3**: the exclusion registry that already exists is bidirectional, and that is the property worth inheriting.
2. **The explicit `#define`/`#undef` redirect bracket** at the struct site (`ModelInference.hpp:1478-1484`) — the exclusion is visible *at the point of use*, not only in a distant sidecar.

The honest summary: this is prior art for **"a sidecar plus a bidirectional CI tool"**, and it is in good health. It is **not** prior art for **"struct fields == covered ∪ excluded"**, which remains genuinely un-landed (consistent with prior-art OPEN-3).

---

## 3. Unaccounted items, ranked by blast radius

### S-1 — **CRITICAL.** The cfg-derived drift check is unconditionally vacuous for every acceptable stamp

All 36 `STAMP_BOUND_CFG_DERIVED` cohort members — including `thompson_mu_prior`, `thompson_precision_prior/obs`, `ridge_lambda`, `ml_tp_pct`, `ml_sl_pct`, `confidence_threshold_scale`, `bandit_algorithm`, `barrier_blend_mode`, `trading_mode` — are stamped, parsed, and then **never compared**.

The chain, five verified links:

1. **The gate.** Every cfg-derived drift decision routes through `cfg_gate::lookup_drift`, which returns `stamp_has_inference_cfg && (expr)` for cohort rows and bare `stamp_has_inference_cfg` for all others:
   ```cpp
   case FIELD_IDX_PER_NODE_##name: return stamp_has_inference_cfg && (expr);
   ...
   default: return stamp_has_inference_cfg;
   ```
   — `MemHeaders/CfgGateRegistry.hpp:194,197` (and `:202,205` for global). The two bitmap walkers gate identically: `const bool _trigger = stamp_has_inference_cfg & _drifted;` — `:568` (ML_CFG_FLAG) and `:588` (GATE_CFG_FLAG).

2. **The argument.** `stamp_has_inference_cfg` is supplied as `STAMP_HAS((handle), inference_cfg)` — `CfgGateRegistry.hpp:814`. That is the **`inference_cfg` GROUP bit** (`MASK_inference_cfg`, `StampBoundModelConstRegistry.hpp:580`), not any per-field flag.

3. **The bit has no production producer on the emit side.** `STAMP_SET(inf, inference_cfg)` appears **nowhere** in production code. Exhaustive search returns only: the parser dispatcher (`StampBoundModelConstRegistry.hpp:747`), the **quarantined** AUTOPOPULATE dispatcher (`:715` — whose entry macro is `static_assert(false, ...)` at `:677-682` with zero callers), the load-side propagation (`NodeModelZoo.hpp:459`), and tests. **`Stamp_AssembleAndEmit` — the single canonical emit path (`ML_Headers/StampHelper.hpp:179`) — never sets it.** It sets 16 other bits (`:236,239,251,256,265,281,285,287,306,316,322,332,340,344,350,352`); the `inference_cfg` group is not among them. The cohort populator `populate_inference_cfg_from_derived` sets only the **per-field** `inf.has_##name` (`CfgGateRegistry.hpp:365,372,382,391`), never the group bit.

4. **Therefore no `inference_cfg_*` key is ever emitted.** The 9 `inference_cfg`-group POST_CFG rows are emit-gated on `STAMP_EMIT_CHECK_HAS_inference_cfg` (`ModelInference.hpp:2292` walking `:2297`), which reads that unset bit. Consequently the parser's `STAMP_PARSER_SET_HAS_inference_cfg` (`:1760` walking `:1762`) never fires, and `sr.has_flags` never acquires `MASK_inference_cfg`.

5. **Therefore the call is a no-op.** `DRIFT_CHECK_FROM_DERIVED(failure_flags, sr, cfg, sr.inference_cfg_drift_count, sr.reason, sizeof(sr.reason))` — `ML_Headers/NodeModelZoo.hpp:304` — runs with `stamp_has_inference_cfg == false`, so every one of the 36 rows evaluates `_trigger == false`. `sr.inference_cfg_drift_count` can never increment, so the refusal at `NodeModelZoo.hpp:305-307` (`sr.valid = 0`) is unreachable.

**Why it is TOTAL, not merely usual.** The `inference_cfg_`-prefixed keys are the **v1 legacy-prefix era** (`ModelInference.hpp:159`). The parser hard-refuses any stamp below the decimal epoch floor — `STAMP_FORMAT_VERSION_EPOCH_FLOOR = 3` (`:166`), enforced at `:1805-1811` under `MONEY_ENCODING_EPOCH != 0u`. `MONEY_ENCODING_EPOCH = is_fp_decimal_v<EngineMoneyT> ? 1u : 0u` (`FixedPoint/FixedPointN.hpp:300`), and post-Ship-B `Money` is decimal → **epoch = 1 → the floor is live**. So the only stamps that could ever set the bit are exactly the stamps the engine now refuses. There is **no reachable production path** that sets it.

**Root cause (and why this is the same meta-pattern in a new guise).** The `.B.3` SOFT bump moved the cfg-derived wire keys from `inference_cfg_<name>` to unprefixed `<name>`, and moved presence-tracking from one group bit to per-field `has_<name>` flags. The **producer** of the group bit was retired with the prefix; the **gate** still consumes it. The per-field flags that *are* correctly maintained are never consulted by the drift gate. Nothing detected this because every guard in the neighbourhood is rows-forward: the registries are all complete and correct, the meta-walker genuinely cannot skip a registry, `check_meta_registry` is about enrollment, and the count-locks are floors. **A registry guard proves the rows are right; it cannot prove the walker's gate is reachable.**

**Blast radius:** train↔serve parity. An operator who retrains under one `thompson_mu_prior` / `ridge_lambda` / `ml_tp_pct` and serves under another gets **no WARN, no Tier-1 REFUSE even in strict mode, and a clean stamp verification**. Capital-bearing, silent, and exactly the "fingerprint matches while semantics drifted" failure the brief names.

### S-2 — **HIGH.** Four `FOREACH_CFG_DRIFT_CHECK` rows are dead by the same mechanism

Because `STAMP_HAS(sr, inference_cfg)` is false, the guarded block at `ML_Headers/NodeModelZoo.hpp:458-468` never executes. So `STAMP_SET(*handle, inference_cfg)` (`:459`) never fires and `handle->confidence_threshold_scale` / `barrier_gate_enabled` / `confidence_hard_block_threshold` (`:460-465`) stay at `Model_Init` zero. Consequently the four `FOREACH_CFG_DRIFT_CHECK` rows whose `gate_when` is `STAMP_HAS(*h, inference_cfg)` — `confidence_threshold_scale` (`CfgDriftCheckRegistry.hpp:257`), `barrier_gate_enabled` (`:261`), `confidence_hard_block_threshold` (`:266`), `per_horizon_barrier_blend` (`:332`) — never evaluate at the `ModelValidation.hpp:222` walker either. **Both drift surfaces are substantially dead, from one severed producer.**

### S-3 — **MED-HIGH.** Every stamp records a feature width that understates reality by 6, and the check that would catch it compares the constant to itself

`inf.expected_num_features = (int)MODEL_NUM_FEATURES` — `ML_Headers/StampHelper.hpp:351`. `MODEL_NUM_FEATURES` is `34` (`ML_Headers/ModelInference.hpp:117`), the terminal sentinel of the **retired** `FEAT_*` index scheme, and it is **frozen deliberately** — the frozen packer's own note says *"Frozen at 34 features by design — the equivalence pins the legacy range"* (`:1395-1396`).

The **live** vector is defined by `FOREACH_FEATURE`: **40 rows, all `FEATURE_ENABLED`** (`ML_Headers/FeatureRegistry.hpp:524`, verified mechanically). The production path passes the *runtime* count, not the constant: `int n = Features_PackAll(&ctx, feat_buf); ... Model_Predict(&ctrl->regime_model, feat_buf, n)` — `CoreFrameworks/PortfolioController.hpp:1799,1803` (and `:1969,1980`). `Model_Predict` builds the DMatrix from the caller's `num_features` (`ModelInference.hpp:894,902`), so inference genuinely runs at 40.

**No `static_assert` binds `MODEL_NUM_FEATURES` to `NUM_REGISTERED_FEATURES`** (searched; none). And the verification loop is self-referential: `BacktestPanels.hpp:6339-6340` writes `expected_num_features = MODEL_NUM_FEATURES` into `expected.cfg`, and `NodeModelZoo_VerifyExpected` (`NodeModelZoo.hpp:870,907`) parses it back and compares — **34 against 34, forever**. Vacuously green (Class-51).

**Nuance that keeps this MED-HIGH rather than CRITICAL:** the *identity* gate is sound — `feature_hash` (`ArchFieldDriftRegistry.hpp:71-72`) compares `FEATURE_REGISTRY_HASH()`, which is FNV over the real 40 names+versions, so an actual feature-set change *is* caught. The defect is that the **declared width in the lineage is wrong**, and its guard cannot notice.

### S-4 — **MED.** `environment_meta`: a group in active use with no GROUPS row

`FOREACH_STAMP_BOUND_MODEL_CONST_GROUPS` (`StampBoundModelConstRegistry.hpp:241-247`) has **6** rows. **7** distinct group tokens are actually used by the 48 registry rows; `environment_meta` (used by 5 rows, `:437,440,443,446,449`) has **no GROUPS row**. This is the textbook complement-blindness shape and the closest sibling in this shard to the `drift_history` founding instance.

Mitigating: the *consumers* are all complete — the enum bit exists (`:545`), `MASK_environment_meta` exists (`:601`), and all three token-paste dispatchers are defined (`:722,737,753`). I verified mechanically that **bits ↔ (used groups + standalone rows) is an exact 24 ↔ 24 match with zero gaps either way**, and MASK ↔ bit likewise 24 ↔ 24. So nothing is currently broken.

What *is* broken is the guard: `FOREACH_STAMP_BOUND_MODEL_CONST_GROUP_COUNT >= 6` (`tests/controller_test.cpp:23696-23697`) passes at **exactly the stale value**. The floor sits precisely where the missing row would have raised it. The in-file comment `"Allocation: groups first (6 bits), then standalones (7 bits) = 13 total"` (`:522`) is stale against the real 7 + 17 = 24.

### S-5 — **MED.** `FOREACH_STAMP_BOUND_MODEL_CONST_STANDALONE` is superseded, incomplete, and carries a phantom row

17 registry rows carry `group == "_"`; the STANDALONE registry has **7** rows covering **6** of them. Missing: `expected_num_classes`, `expected_role`, `expected_num_features`, `expected_feature_format_version`, `overlay_hash`, `effective_hash`, `training_timestamp_us`, `run_name`, `scaler_fit_data_hash`, `removal_reasons_csv`, `inference_cfg_bandit_blend_ratio` (11). Its `bandit` row (`:261`) matches **no** registry row name — the real row is `inference_cfg_bandit_blend_ratio` (`:302`), the bit is `STAMP_BIT_inference_cfg_bandit_blend_ratio` (`:548`). This is the **same name-trap shape** as the prior-art `node_kill_tripped` BIT-row finding (U-1).

The registry is **dead**: its only consumers are its own definition, the `MetaRegistry` enrollment row (`MetaRegistry.hpp:65`), and the count test. The file itself documents the supersession — *"Standalone has_* names use the entry's full canonical name (mechanical derivation; **no STANDALONE list dispatch**) ... Eliminates 2-site STANDALONE dispatch maintenance"* (`:530-534`) — directly contradicting its own instruction block at `:253-258` which still says adding a standalone requires a row here. Per H21 dead-code discipline this should be **removed**, not repaired.

### S-6 — **MED.** `confidence_ic_variant` admits 5 values; the registry defines 1; the other 4 silently yield IC = 0.0

`confidence_ic_variant` carries range `INT(0, 0, 4)` (`CoreFrameworks/CfgFieldRegistry.hpp:683`). `FOREACH_IC_VARIANT` defines exactly **one** row, `id=0` spearman (`ML_Headers/ICVariantRegistry.hpp:56-61`); rows 1 and 2 are commented-out placeholders. The dispatcher falls through to `default: return 0.0;` (`:99`) — commented *"unknown variant → safe"*. The value flows cfg → `ControllerEventLoop.hpp:1880` → `ConfidenceScorer_ComputeICVariant` → `IC_VARIANT_COMPUTE` (`ConfidenceScore.hpp:867-871`) with **no validation anywhere**.

So an operator setting `confidence_ic_variant=1..4` — a range the cfg descriptor presents as valid — gets a permanently-zero information coefficient with no warning. IC feeds confidence gating and the drift detector, so this degrades an ML risk control silently. "Safe" is the wrong default here: a cfg-admissible value with no registry row should REFUSE at boot, not return a plausible-looking zero.

### S-7 — **MED.** Nine POST_CFG rows are unreachable at emit — including the five added to *close* a parity gap

The 9 `inference_cfg`-group rows (`StampBoundModelConstRegistry.hpp:460,463,466,469,475,478,481,484,487`) can never emit (S-1 link 4). Five of them are the **PARITY-026 closure rows** added at `.F.4d` explicitly because *"4 STAMP_BOUND bandit/thompson fields since v5.14.10.B were missing POST_CFG entries"* (`:472-474`). They were added correctly and are structurally unreachable. The semantics are in fact carried by the unprefixed cfg-derived path, so **no wire data is lost** — but PARITY-026 should not be considered closed by these rows, and they are dead code under H21.

### S-8 — **LOW-MED.** The one genuinely-good complement tool is not in the mechanical gate

`check_struct_field_uniqueness.py` is `SKILL-WIRED | readiness` per `DOCS/TOOLS.md:109`. It does **not** appear in `.githooks/pre-commit` or `tools/check_session_docs.sh` (searched both). It runs only when a human fires `/readiness` Check 40. Per M7 / *guards compound*, the best-shaped guard in this shard has the weakest firing discipline.

### S-9 — **LOW.** A tautological test

`check("... total walk count matches FOREACH_STAMP_BOUND_MODEL_CONST_COUNT", (include_count + skip_handle_count) == FOREACH_STAMP_BOUND_MODEL_CONST_COUNT)` — `tests/controller_test.cpp:23749-23750`. Both sides are the same macro walk over the same registry; every row contributes exactly +1 to one counter and +1 to COUNT. It cannot fail. Class-51.

### S-10 — **LOW.** `BOTH_DOMINANT_DRIVES` is cfg-unreachable but drift-checked EXACT

`FOREACH_BARRIER_BLEND_MODE` defines 5 modes, `MODE_BARRIER_BLEND_BOTH_DOMINANT_DRIVES = 4` (`BarrierBlendModeRegistry.hpp:102,109-111`), but `barrier_blend_mode` carries `INT(0, 0, 3)` with `WARN_ON_CLAMP` (`CfgFieldRegistry.hpp:776`). Mode 4 is operator-unreachable, while the field is STAMP_BOUND and drift-checked `EXACT` (`CfgDriftCheckRegistry.hpp:326-329`). Either the range or the row is wrong.

### S-11 — **LOW (doc).** Stale comments that actively mislead a guard author

Per SUBAGENT_ARMING § 2.5, code is truth:
- `CfgDriftCheckRegistry.hpp:209-212` — *"The stamp body itself is defined by FOREACH_STAMP_BOUND_CFG; adding a new drift entry here requires the corresponding stamp-binding row in StampBoundCfgRegistry.hpp"*. That registry and file were **deleted at `.B.3`** (`MetaRegistry.hpp:52`). This instruction now sends an author to a nonexistent file — and is arguably a contributing cause of S-1.
- `ModelInference.hpp:1447-1451` — *"13 bits used today ... 6 group bits ... + 7 standalone bits"*. Actual: 24 bits, 7 groups, 17 standalone.
- `StampBoundModelConstRegistry.hpp:522` — same stale 6+7=13.
- `ModelInference.hpp:1455` and `:1487-1489` — *"26 entries"* / *"6 entries"*. Actual: 48 union, 24 POST_CFG.
- `StampBoundModelConstRegistry.hpp:290` — *"26 entries today"* for PRE_CFG. Actual: 24.
- `ICVariantRegistry.hpp:91,94` reference `scorer_ptr->active_ic_variant` / `cs->active_ic_variant`; no such field exists (searched — comment-only).

### S-12 — **LOW.** `#define FOREACH_SINGLE_ZOO_POST_LOAD_COUNT 1` (`NodeModelZoo.hpp:3460`) is a hand-maintained literal with an explicit "Update when adding entries" instruction — a Class-18 mirror where a `+1` reduction (as used by every sibling registry) would auto-flow.

---

## 4. HAZARDS

- **HAZ-1 (the shard's core lesson).** Every guard in this family is **rows-forward**, and the one real hole was not a missing row at all — it was a **gate whose producer was retired underneath it**. A struct↔registry partition guard, however good, would **not** have caught S-1. The generalized complement this shard argues for is: *for every registry-driven consumer, is its gate expression reachable?* Suggested mechanical form: assert that every `STAMP_BIT_*` group bit has **at least one non-test, non-parser production writer**. That single check catches S-1, S-7, and the `environment_meta`/`feature_mask`/`overlay_hash`/`effective_hash`/`training_timestamp_us`/`scaler_fit_data_hash`/`removal_reasons_csv` emit-side gaps in one sweep.
- **HAZ-2 (a locked hash proves the wrong thing — explicitly, as the brief asked).** The stamp's HMAC (`ModelInference.hpp:2319`) is computed over the canonical body **as assembled**. It proves *the bytes that were written were not altered*. It has **zero** power to prove *the right fields were enrolled*, and in S-1 it signs a body whose drift check will never run. Likewise `FEATURE_REGISTRY_HASH` proves feature-set identity but says nothing about the declared width (S-3), and `check_meta_registry.py` proves enrollment but nothing about reachability. **Three orthogonal green signals, all blind to the same hole.**
- **HAZ-3 (floors sitting exactly at the stale value).** `GROUP_COUNT >= 6` and `standalone_count >= 7` (`controller_test.cpp:23697,23707`) each pass at precisely the value a missing row leaves behind. A `>=` floor chosen "so future growth doesn't break the test" (`:23685-23686`) is, at the boundary, indistinguishable from no test.
- **HAZ-4 (fixing S-1 is a wire-format decision, not a patch).** Re-pointing the gate has three candidate shapes with different consequences: (a) gate per-field on `handle.has_<name>` — no wire change, drift starts firing immediately, and **may surface a backlog of real drift on existing models**; (b) set `STAMP_SET(inf, inference_cfg)` in `Stamp_AssembleAndEmit` — changes which keys emit, therefore changes the HMAC body → H9/H21 bump; (c) retire the group bit and the 9 dead rows entirely → H21 tombstone discipline. **This needs Caramel's decision; I make no recommendation on which.** Note (a) is the only one that does not touch the wire — but it is also the one that could turn a silent pass into a boot REFUSE on a model that loads fine today.
- **HAZ-5 (un-run tool).** `check_meta_registry.py` did not execute this session (blocked by the pipe-rc guard). H15/H19 status for this shard is **asserted from reading `MetaRegistry.hpp`, not tool-verified**. Re-run it with `cmd > log 2>&1; RC=$?`.
- **HAZ-6 (straddling — named, not chased).** `NodeModelZoo_VerifyExpected` (`NodeModelZoo.hpp:820+`) is a **second, hand-rolled 9-key parser** over a separate `expected.cfg` file, with its own manual `strcmp` if-else chain (`:895-908`). It parses `expected_poll_interval`, a key no stamp emitter writes. This is a parallel cfg-verification surface with no registry behind it — **sibling shard's territory (cfg surface); flagging, not pursuing.**

---

## 5. Spots most worth an adversarial refute (for the paired a-class)

1. **S-1 is the whole report — attack it hardest.** The chain is five links, each individually cited, but it is a *negative existence* claim ("no production writer of `MASK_inference_cfg` on the emit side"). **Try to break it by finding a writer I missed:** a `memcpy`/aggregate-initialization of a `StampInferenceCfgInputs` from a source that already has the bit; a `has_flags` write through a differently-named alias; a test-only helper that production links; a path where `sr` is copied from a `ModelHandle` that got the bit elsewhere. I searched for `STAMP_SET(..., inference_cfg)`, `MASK_inference_cfg`, and direct `.has_flags |=` / `->has_flags =` and found none in production — **but a negative is exactly what a grep is worst at.** The decisive confirmation is a preprocessor expansion of `Stamp_AssembleAndEmit` (`clang++ -E`), which I did **not** run (read-only fence). **Recommend the orchestrator run it before acting.**
2. **The "TOTAL, not merely usual" strengthener.** I argued the epoch floor (`ModelInference.hpp:1805-1811`, floor=3 at `:166`) makes it impossible for *any* acceptable stamp to set the bit. **Refute by finding a load path that bypasses `verify_model_stamp`'s check 0c** — a backtest/test loader, a hot-swap path, or a build where `MONEY_ENCODING_EPOCH == 0` (`FixedPoint/FixedPointN.hpp:300` — is `EngineMoneyT` ever bound to a binary type in any build config?). If such a path exists, the finding weakens from "provably total" to "total in production, evadable in backtest" — still severe, but differently scoped.
3. **S-3's severity hinges on what the trainer actually packs.** I proved the *engine* serves 40 (`PortfolioController.hpp:1799-1803`) and *stamps* 34 (`StampHelper.hpp:351`). I did **not** verify the Python/training side's column count. **If the trainer also packs 40, the stamp field is simply a wrong label (MED).** If the trainer packs 34, there is a live train↔serve width mismatch and this jumps to CRITICAL. Worth resolving explicitly — it is the difference between a documentation defect and a silent prediction-corruption bug.
4. **My S-4 "benign" call.** I cleared `environment_meta` as harmless because bits/masks/dispatchers are all complete (verified 24↔24 both directions). **Probe the emit side instead:** `STAMP_SET(inf, environment_meta)` is *also* absent from `Stamp_AssembleAndEmit` — so the 5 environment fields never emit either. If that is deliberate (they are documented "informational; no enforcement", `:436`) it is fine; if not, S-4 merges into S-7 and the dead-row count rises from 9 to 14. Same question for `feature_mask`, `overlay_hash`, `effective_hash`, `training_timestamp_us`, `scaler_fit_data_hash`, `removal_reasons_csv` — **I did not individually adjudicate those seven**, and `training_timestamp_us` in particular is claimed to drive the stale-model gate (`:418`), which would make its absence a second dead risk control.
5. **The withdrawn first complement.** I computed "21 of 36 cohort members lack a `FOREACH_CFG_DRIFT_CHECK` row" and withdrew it after finding `drift_check_from_derived`. **Verify I withdrew it correctly** — is `NodeModelZoo.hpp:304` genuinely the only production drift entry point for the cohort, and does `ModelValidation.hpp:222`'s walker really not double-count the 15 overlapping fields? If both walkers *do* fire on the same field in some configuration, there is a double-WARN / double-count issue I dismissed too fast.
6. **S-6's "silent 0.0" framing.** I claimed no validation of `confidence_ic_variant`. **Refute by finding a boot-time range check** (a `LiveReadiness` row, a cfg-clamp with a hard refusal, a GUI constraint). `WARN_ON_CLAMP` is set on the descriptor but the range is `0..4`, so no clamp fires for 1-4. If some other layer rejects >0, this drops to LOW.
7. **Generality of the "gate reachability" check I propose in HAZ-1.** Per *don't generalize a substrate before its input space is known*: I derived it from one instance. **Before it becomes a CI tool, enumerate the other gate-bearing registries** (`FOREACH_SLOW_PATH_GATE`, `FOREACH_FAILURE_MODE`, the `COHORT_GATE_*` family at `MlCfgFlagRegistry.hpp`) and check whether "every gate bit has a production writer" is even the right invariant there, or whether it produces false positives on legitimately-conditional bits.

---

## 6. Open questions for Caramel

- **OQ-1 (blocking):** S-1 remediation shape — (a) gate per-field on `handle.has_<name>` (no wire change; may surface latent real drift as new boot REFUSEs), (b) set the group bit at emit (wire/HMAC bump per H9/H21), or (c) retire the group bit + the 9 dead rows (H21 tombstone). **I make no recommendation.**
- **OQ-2:** Is `expected_num_features` meant to record the *legacy equivalence range* (34, current behaviour) or the *actual served width* (40)? If the latter, bind it to `NUM_REGISTERED_FEATURES` and add the missing `static_assert`.
- **OQ-3:** `confidence_ic_variant` — narrow the cfg range to `INT(0,0,0)` until variants land, or add a boot REFUSE for any value without a registry row? Same question for `barrier_blend_mode` mode 4 (S-10), in the opposite direction.
- **OQ-4:** Retire `FOREACH_STAMP_BOUND_MODEL_CONST_STANDALONE` outright (S-5)? It is superseded by mechanical derivation, 65% incomplete, carries a phantom row, and its only live consumer is a floor test.
- **OQ-5:** Should `check_struct_field_uniqueness.py` move from `/readiness`-only into `check_session_docs.sh` / pre-commit (S-8)?

---

**Key files:** `/home/caramel/code/FoxML_Trader_v2/ML_Headers/StampBoundModelConstRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ModelInference.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/StampHelper.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/NodeModelZoo.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/CfgDriftCheckRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/FeatureRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ICVariantRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/BarrierBlendModeRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ConfidenceScore.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/CfgGateRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/ArchFieldDriftRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/MetaRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/CfgFieldRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ModelValidation.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/PortfolioController.hpp` · `/home/caramel/code/FoxML_Trader_v2/Backtest/LabelFunctions.hpp` · `/home/caramel/code/FoxML_Trader_v2/Backtest/BacktestPanels.hpp` · `/home/caramel/code/FoxML_Trader_v2/FixedPoint/FixedPointN.hpp` · `/home/caramel/code/tick-trader-percore-workspace/tools/check_struct_field_uniqueness.py` · `/home/caramel/code/tick-trader-percore-workspace/tests/controller_test.cpp`
