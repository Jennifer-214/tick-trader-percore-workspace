---
type: audit-report
audit: registry-fit-audit
scope: codebase-wide
target_ship: v5.15.5.F.4d.1.E.0
engine_head: 61ae3cc (v5.15.5.F.4d.1.D)
date: 2026-05-28
---

# /registry-fit-audit codebase-wide baseline (`.E.0` Phase 1)

## Verdict

**GREEN** — global state of registry discipline is HEALTHY. No registry actively hostile to the upcoming `.E.1` `FOREACH_EXCHANGE` / `FOREACH_SUBACCOUNT_<EXCHANGE>` additions. 52 registries enrolled in `FOREACH_REGISTRY` meta-registry (per H15); meta-registry topology (LEVEL 0/1/2) is sound; per-row PARENT discipline (H19) enforced. The Class 21 anti-pattern (parallel descriptors) was structurally closed at `.F.4` via `CfgFieldDescriptor` + `lives_in_struct` discriminator; Class 27 (cfg-mirror caches) closed structurally via decision-time-data-binding + framework-selection criteria. Codebase is firmly in **late-CONSOLIDATION → approaching-INFLECTION** phase (see Framework-layer inflection assessment below) — adding `FOREACH_EXCHANGE` is justified per the canonical sister-extension shape (3 mature sister registries to extend) but the codebase should NOT add new framework LAYERS beyond exchange + subaccount at `.E.1`.

3 minor YELLOW items (none block `.E.1`):
- 1 empty-placeholder registry (`FOREACH_POSITION_FIELD_SKIP_PERSIST` — kept by deliberate design per v5.15.5.C.5 revert; not stagnation)
- 4 single-row registries (3 legitimate Stage-3 first-canonical seed; 1 worth re-examining: `FOREACH_IC_VARIANT`)
- Shape drift: 5 cfg-flag domain registries split 3@5-col + 2@6-col (`metadata_flags` column added at `.B.2/.B.3` cohort migration; remaining 3 will likely migrate to 6-col uniformly when STAMP_BOUND rows added)

---

## Per-registry verdict table

| Registry | Level | Rows | Consumers | Verdict | Rationale |
|---|---|---|---|---|---|
| FOREACH_REGISTRY | 2 | 52 | 1 (CI tool) | KEEP | Codebase-wide meta-registry; H15 enforcement seed; growing (5 rows added at `.F.4c-.F.4d`). |
| FOREACH_GLOBAL_CFG_FIELD | 1 | 55 | 4 | KEEP | Core cfg framework; auto-flows parser/GUI/render/persist; high leverage. |
| FOREACH_PER_CORE_CFG_FIELD | 1 | 88 | 4 | KEEP | Per-core cfg framework; H17 enforces; struct auto-gen Stage 6 cadence-locked. |
| FOREACH_MANUAL_PER_CORE_FIELD | 1 | 12 | 2 | KEEP | Exemption registry for KIND_STRING/_FILE_PATH/_HEX64; awaiting `.F.4e` consolidation per description. |
| FOREACH_PER_CORE_DOMAIN_BITMAP | 1 | 5 | 2 | KEEP | Meta-registry over 5 cfg-flag domains; clean Class 21 closure shape (MERGE via meta-row rather than parallel registries). |
| FOREACH_PER_CORE_NO_FLAT_FIELD_SYNC | 1 | 1 | 2 | KEEP | Single-row Stage-3 canonical for PER_CORE_MODE_NO_FLAT_FIELD category (`strategy` sister); seeded by recent .F.4d.1.B.4 cfg-field categorization migration; cohort growth expected. |
| FOREACH_METADATA_BIT | 1 | 12 | 1 | KEEP | Per-bit mask declarations for `CfgFieldDescriptor::MetadataFlag`; H16 enforces every bit has derived filter row OR documented exemption. |
| FOREACH_LIFECYCLE_CFG_FLAG | 2 | 3 | 3 | KEEP | Child of `FOREACH_PER_CORE_DOMAIN_BITMAP`; 5-col shape (no STAMP_BOUND rows yet). |
| FOREACH_GATE_CFG_FLAG | 2 | 6 | 4 | KEEP | Sister of LIFECYCLE; 6-col shape (`metadata_flags` added at `.B.3` Step 0.5d.a.0 — 1 row carries STAMP_BOUND_CFG_DERIVED). |
| FOREACH_ML_CFG_FLAG | 2 | 12 | 4 | KEEP | 6-col shape (`metadata_flags` added at `.B.2`; 5 rows carry STAMP_BOUND_CFG_DERIVED). |
| FOREACH_RISK_CFG_FLAG | 2 | 5 | 3 | KEEP | Sister; 5-col (no STAMP_BOUND rows). |
| FOREACH_OPS_CFG_FLAG | 2 | 4 | 3 | KEEP | Sister; 5-col (no STAMP_BOUND rows). |
| FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG | 1 | 24 | 2 | KEEP | Wire-format byte preservation; emit order critical (H9). |
| FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG | 1 | 24 | 2 | KEEP | Sister to PRE_CFG; emit-order discipline. |
| FOREACH_STRATEGY | 1 | 4 | 3 | KEEP | Strategy dispatch; canonical sister for FOREACH_EXCHANGE shape (enum+adapter+impl trio). |
| FOREACH_BANDIT_ALGORITHM | 1 | 5 | 2 | KEEP | Includes multi-col flags + display string + doc; canonical sister for FOREACH_EXCHANGE metadata-col shape. |
| FOREACH_BANDIT_SIDE | 1 | 2 | 1 | KEEP | Buy/exit symmetric meta-X-macro; first canonical of side-symmetry pattern; growth-by-construction at 2 (sides are binary). |
| FOREACH_FAILURE_MODE | 1 | 14 | 1 | KEEP | Bit-flag storage; growing; well-bounded by uint64 storage. |
| FOREACH_OMS_FIELD | 1 | 38 | 2 | KEEP | OMS state field registry; AUTOPOPULATE consumer; high entry count. |
| FOREACH_STAMP_BOUND_MODEL_CONST | 1 | 0 (union wrapper) | 3 | KEEP | Concatenation wrapper of PRE_CFG + POST_CFG; legitimate composition pattern (no rows of its own; not stagnation). |
| FOREACH_STAMP_BOUND_MODEL_CONST_GROUPS | 1 | 37 | 1 | KEEP | Group-anchor field registry; Y3 dispatch. |
| FOREACH_STAMP_BOUND_MODEL_CONST_STANDALONE | 1 | 31 | 2 | KEEP | Standalone-field registry; AUTOPOPULATE. |
| FOREACH_BARRIER_BLEND_MODE | 1 | 5 | 1 | KEEP | Mode enum with multi-flag descriptor cols; canonical for enum-mode-flags pattern. |
| FOREACH_IC_VARIANT | 1 | 1 | 2 | YELLOW: RECONSIDER (low priority) | Single row at `2026-05-09`; comment includes 2 commented-out placeholder rows (`pearson` / `kendall`) that never landed. Either codify growth plan (TECH_DEBT entry tracking pearson + kendall addition) OR fold to direct call in `ConfidenceScore_OneCore_Apply`. NOT blocking; defer to `.F` professionalization sweep. |
| FOREACH_DEGRADATION_CURVE | 1 | 4 | 1 | KEEP | Risk degradation curve enum; OFF/LINEAR/EXP/STEP. |
| FOREACH_RECONCILE_MODE | 1 | 3 | 1 | KEEP | Mode enum 3-state; LOCKED at 3 modes by domain (no future growth expected). |
| FOREACH_REGIME | 1 | 5 | 2 | KEEP | Regime enum with display + strategy mapping; canonical for enum-with-metadata-cols. |
| FOREACH_TARGET | 1 | 11 | 2 | KEEP | ML label enum; training-side; growing. |
| FOREACH_FEATURE | 1 | 40 | 3 | KEEP | ML feature compute fns + metadata; high leverage; train-serve parity surface. |
| FOREACH_SHALT | 1 | 18 | 3 | KEEP | Gate-blocking conditions; growing as gates added. |
| FOREACH_HALT_REASON | 1 | 11 | 3 | KEEP | Kill switch / boot refusal reason codes. |
| FOREACH_LIVE_READINESS_CHECK | 1 | 9 | 1 | KEEP | Boot live-readiness checks; growing per live-trading hardening. |
| FOREACH_LIVES_IN_STRUCT | 1 | 5 | 1 | KEEP | Cross-cfg-file discriminator; canonical sister-Class-21-closure. |
| FOREACH_CORE_STATE_FLAG | 1 | 5 | 1 | KEEP | Core state bit flags; bounded by uint storage. |
| FOREACH_PER_CORE_STATE_FLAG | 1 | 11 | 1 | KEEP | Per-core state bit flags. |
| FOREACH_PER_ARM_FLAG | 1 | 2 | 1 | KEEP | Per-bandit-arm flags; first canonical of arm-flag pattern. |
| FOREACH_EZOO_INIT_FLAG | 1 | 5 | 1 | KEEP | EnsembleModelZoo init flags. |
| FOREACH_SESSION_PHASE | 1 | 4 | 5 | KEEP | Session phase enum; high consumer count = high leverage. |
| FOREACH_CORE_CTX_INIT_FIELD | 1 | 55 | 1 | KEEP | Per-core context init fields; AUTOPOPULATE; very high row count. |
| FOREACH_CORE_CTX_RESET_FIELD | 1 | 15 | 1 | KEEP | Per-core context reset fields. |
| FOREACH_CORE_CTX_SUMMARY_FIELD | 1 | 20 | 1 | KEEP | Per-core context summary fields (TUI/snapshot). |
| FOREACH_DISPLAY_META_FIELD | 1 | 10 | 2 | KEEP | Per-core display metadata. |
| FOREACH_GATE_DIAG_PAIR | 1 | 16 | 3 | KEEP | Gate diagnostic pairs (block/pass counters). |
| FOREACH_SINGLE_ZOO_POST_LOAD | 1 | 1 | 1 | YELLOW: RECONSIDER (low priority) | Single row at `2026-05-09`; existing comment says "first canonical" for post-load setup steps. If `EnsembleModelZoo` sister (FOREACH_ENSEMBLE_POST_LOAD = 11 rows) is the mature pattern, this single-row registry is one missing cohort growth from being merged or accepted as canonical-sister-of-ensemble. Defer to `.F` sweep. |
| FOREACH_ENSEMBLE_POST_LOAD | 1 | 11 | 1 | KEEP | Sister of FOREACH_SINGLE_ZOO_POST_LOAD; mature. |
| FOREACH_OMS_PER_SLOT_FIELD | 1 | 5 | 1 | KEEP | OMS per-slot position fields (SoA arrays). |
| FOREACH_OMS_META_SLOT | 1 | 3 | 1 | KEEP | OMS meta-slot fields (entry/exit tracking). |
| FOREACH_OMS_STATE_FLAG | 1 | 3 | 1 | KEEP | OMS state bit flags. |
| FOREACH_OMS_STATE_MULTI_BIT | 1 | 1 | 1 | KEEP | Single-row first canonical of multi-bit state encoding (K=2..4 states for EVENT_LOG_MODE); growth expected as future multi-bit slots added; deliberate Stage-3 seed per `multi-bit-state-encoding-pattern.md`. |
| FOREACH_POSITION_FIELD | 1 | 9 | 2 | KEEP | Position struct fields (full persistence). |
| FOREACH_POSITION_FIELD_SKIP_PERSIST | 1 | 0 (deliberate empty) | 1 | KEEP | Explicitly empty per v5.15.5.C.5 revert — comment documents retention as future-extension infrastructure; PERSIST_KIND filter machinery (Portfolio_Save/Load) remains intact. NOT stagnation; deliberate placeholder. |
| FOREACH_BACKTEST_METRIC | 1 | 8 | 2 | KEEP | Backtest summary metrics. |
| FOREACH_CALIB_LOG_COL | 1 | 47 | 1 | KEEP | Calibration log CSV columns; high row count. |
| FOREACH_TRADE_LOG_COL | 1 | 13 | 1 | KEEP | Trade log CSV columns. |
| FOREACH_CONFIDENCE_PERSIST_FIELD | 1 | 7 | 1 | KEEP | Confidence persistence fields. |
| FOREACH_CFG_DRIFT_CHECK | 1 | 23 | 2 | KEEP | Stamp body drift check fields (legacy; description says folds into framework at `.B.3`; verify whether folded). |
| FOREACH_CFG_GATE_PER_CORE | 1 | 16 | 2 | KEEP | H18 sidecar override registry (per-row gate_when override); 1st canonical of sidecar pattern. |
| FOREACH_CFG_GATE_GLOBAL | 1 | 3 | 2 | KEEP | Sister to PER_CORE; sidecar. |
| FOREACH_STAMP_BOUND_DERIVED_COHORT | 1 | 0 (meta-walker) | 1 (5 consumer macros via BASE_X) | KEEP | Action-parameterized meta-walker; expands to 4 child-registry FOREACH calls per BASE_X token-paste; cited as canonical of FOREACH_<COHORT>_COHORT pattern per `cfg-derived-consumer-framework.md` v1.2. |
| FOREACH_ARCH_FIELD_DRIFT | 1 | 4 | 2 | KEEP | Architectural field drift check. |
| FOREACH_SLOW_PATH_GATE | 1 | 11 | 1 | KEEP | Slow-path gate registry; canon for cfg-flag eligibility per `cfg-flag-eligibility-criteria.md`. |
| FOREACH_SP_SECTION | 1 | 5 | 1 | KEEP | Slow-path section enum with latency budget annotations. |
| FOREACH_PANEL | 1 | 4 | 4 | KEEP | GUI panel registry; high consumer count. |
| FOREACH_ROLLING_WINDOW | 1 | 4 | 2 | KEEP | Rolling window template variant registry. |

**Counts:** KEEP = 50 / RECONSIDER = 2 / DEPRECATE = 0 / SPLIT = 0 / MERGE = 0.

---

## Findings requiring action before `.E.1`

**NONE BLOCKING.** The codebase is registry-discipline-clean for `.E.1` Foundation introduction of `FOREACH_EXCHANGE` + `FOREACH_SUBACCOUNT_<EXCHANGE>`. Specifically verified:

- **No Class 21 (parallel descriptors) risk** — `FOREACH_PER_CORE_DOMAIN_BITMAP` meta-row pattern is the canonical exchange-cohort-orchestrator shape; FOREACH_EXCHANGE can adopt the same shape if multi-exchange grows beyond 2-3 entries (i.e., subaccount registries could be orchestrated by a `FOREACH_EXCHANGE_SUBACCOUNT_DOMAIN_BITMAP` meta-row if needed; not needed at .E.1 for 1 exchange).
- **No conflicting shape constraints** — sister-pattern slots are mature: `FOREACH_STRATEGY` for enum+adapter+impl trio; `FOREACH_BANDIT_ALGORITHM` for enum+multi-col-flags; `FOREACH_REGIME` for enum+display+secondary-mapping. FOREACH_EXCHANGE's proposed 7-col shape `X(NAME, AdapterType, "id", supports_sub, rate, market_hours_kind, submit_protocol)` per `DOCS/CONTRIBUTING/add-exchange.md` Step 5 is a clean extension of these patterns.
- **No H15/H18/H19 enforcement gap** — both new registries can register cleanly in `FOREACH_REGISTRY` meta at `CoreFrameworks/MetaRegistry.hpp`. `FOREACH_EXCHANGE` = Level 1 standalone; `FOREACH_SUBACCOUNT_<EXCHANGE>` = Level 2 child managed by `FOREACH_EXCHANGE` (proper H19 PARENT topology).

**Advisory (not blocking, queue at `.F` professionalization sweep):**

- `FOREACH_IC_VARIANT` (1 row, 2 commented placeholder lines) — codify growth plan as TECH_DEBT entry OR fold to direct call.
- `FOREACH_SINGLE_ZOO_POST_LOAD` (1 row vs sister FOREACH_ENSEMBLE_POST_LOAD with 11 rows) — re-examine whether single-row is canonical-sister-by-design or worth consolidating dispatch logic.
- `FOREACH_CFG_DRIFT_CHECK` description says "folds into framework at .B.3" — verify whether the fold completed; if so, registry should be DEPRECATED.

---

## Framework-layer inflection assessment

Per `feedback_framework_layer_payoff_diminishing_returns`, codebase is in **late-CONSOLIDATION phase**, approaching the **post-INFLECTION** boundary. Evidence:

1. **52 registries** is high for a single C++ application; the first registry (FOREACH_FEATURE / FOREACH_STRATEGY) eliminated dozens of sites; the most recent additions (FOREACH_BANDIT_SIDE = 2 rows, FOREACH_STAMP_BOUND_DERIVED_COHORT = action-parameterized meta-walker) are eliminating handfuls of sites, not dozens.
2. **The .F.4 sprint codified the framework-selection criteria** (DESIGN_PHILOSOPHY § 11.5 added 2026-05-15; Class 27 first canonical of "registry was wrong; principle is right" — Class 27 cfg-mirror caches were NOT mechanicalized into a `FOREACH_SUBSYSTEM_CFG_CACHE` registry; they were ELIMINATED via decision-time-data-binding). This codification IS the canonical signal of approaching inflection — operator + AI now actively gate "should this be a registry vs principle+sweep+delete?"
3. **Multiple cross-registry meta-walkers landed** at `.B.2/.B.3` (FOREACH_STAMP_BOUND_DERIVED_COHORT, FOREACH_PER_CORE_NO_FLAT_FIELD_SYNC) — these are aggregation/composition over EXISTING registries, not new pattern domains. This is the "consolidation/composition" pattern characteristic of late-CONSOLIDATION.
4. **Recent registry additions are bounded by domain** (FOREACH_BANDIT_SIDE permanently = 2 rows; FOREACH_OMS_STATE_MULTI_BIT = 1 row first canonical; FOREACH_PER_CORE_NO_FLAT_FIELD_SYNC = 1 row first canonical) — these are seeding new pattern shapes, not eliminating wide site duplications.

**Implications for `.E.1` `FOREACH_EXCHANGE` addition:**

- **JUSTIFIED.** Multi-exchange substrate is a NEW domain (not yet existing in codebase); FOREACH_EXCHANGE codifies a wide-leverage pattern (every per-exchange operation flows through the adapter dispatch); 1+ projected applications already (Binance current; .E.5 sub-accounts; .E.6 generalization docs; .E.7 IBKR optional). Sister to FOREACH_STRATEGY shape (enum+impl+behavior cols) which has 4 rows + 3 consumers + high leverage. Not premature.
- **CAUTION on FOREACH_SUBACCOUNT_<EXCHANGE> shape** — per-exchange sub-account topology. The `<EXCHANGE>` token-paste shape (one registry PER exchange) might split inelegantly if exchanges have very different sub-account semantics. Consider whether a single `FOREACH_SUBACCOUNT(X)` row-shape `X(SUBACCOUNT_BINANCE_PROD, EXCHANGE_BINANCE, "prod", ...)` with EXCHANGE-id as discriminator column scales better than N per-exchange registries. The shape decision belongs to `.E.1` plan body — flag for SHAPE audit at that time.
- **DO NOT add new framework LAYERS at `.E.1`** beyond exchange + subaccount. Codebase is past the point where new framework layers carry first-tier ROI; per `feedback_framework_layer_payoff_diminishing_returns`, "first registry eliminates 90 sites = transformative; 7th layer eliminates 6 sites = rounding error."

---

## Canonical sister patterns relevant to FOREACH_EXCHANGE design

Per `canonical-sister-extension-discipline.md` — extend existing sister patterns rather than introducing novel infrastructure:

- **`FOREACH_STRATEGY` (`Strategies/StrategyInterface.hpp`)** — canonical sister for the enum+adapter+impl trio shape. 4 rows × 8-col tuple `X(NAME, "short", "display", StateType, init_fn, build_fn, adapt_fn, exit_fn)`. Same conceptual structure as FOREACH_EXCHANGE (each row = one swappable backend with multi-fn adapter dispatch). EXTEND this shape: `X(EXCHANGE_NAME, AdapterType<F>, "id", supports_sub, rate, market_hours_kind, submit_protocol)`.
- **`FOREACH_BANDIT_ALGORITHM` (`ML_Headers/BanditAlgorithmRegistry.hpp`)** — canonical sister for enum-with-multi-flag-metadata columns. 5 rows × 7-col `X(name, value, apply_fn, exp3_up, thompson_up, drives, doc)`. Use for exchange-metadata cols (supports_sub / rate / market_hours_kind).
- **`FOREACH_PER_CORE_DOMAIN_BITMAP` (`CoreFrameworks/CfgFieldRegistry.hpp`)** — canonical sister for meta-row orchestrating N child registries via token-paste. If multi-exchange grows + per-exchange subaccount registries grow, consider this orchestration shape over per-exchange registry proliferation.
- **`FOREACH_LIVES_IN_STRUCT` (`CoreFrameworks/CfgFieldRegistry.hpp`)** — canonical sister-Class-21-closure for discriminator-column-vs-parallel-registry decision. Cross-cfg-file uses a discriminator enum (STRUCT_CFG / BACKTEST_CFG / etc.) on `FOREACH_GLOBAL_CFG_FIELD` rather than parallel cfg-field registries. FOREACH_SUBACCOUNT might benefit from the same shape (single registry with `exchange_id` discriminator col) instead of `FOREACH_SUBACCOUNT_BINANCE` + `FOREACH_SUBACCOUNT_<X>` proliferation — decision belongs to `.E.1` plan body.
- **`FOREACH_REGIME` (`Strategies/StrategyInterface.hpp`)** — canonical sister for enum+display+secondary-mapping. Use for FOREACH_EXCHANGE's `market_hours_kind` mapping column.
- **`FOREACH_BARRIER_BLEND_MODE` (`ML_Headers/BarrierBlendModeRegistry.hpp`)** — canonical sister for mode-with-bit-flag descriptor columns. Use if FOREACH_EXCHANGE's `submit_protocol` needs flag-based dispatch (WS_API vs REST vs FIX).
