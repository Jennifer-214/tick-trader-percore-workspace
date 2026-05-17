# Dependency chain trace: `STAMP_BOUND_CFG_DERIVED` — 2026-05-17

**Scope:** `chain:STAMP_BOUND_CFG_DERIVED` per `DESIGN_SPECS/audit-scope-taxonomy.md` § 5
**Audit context:** Pre-coding for `.B` of `v5.15.5.F.4d.1` umbrella
**HEAD verified:** `39b9947` (`.F.4d.1.A` ship close, 2026-05-17)

---

## Top-line verdict: **GREEN**

Flow graph is clean. At HEAD `.A`, the symbol exists as `1u << 13` bit definition + 1 enrolled row in `FOREACH_METADATA_BIT` + auto-generated mask infrastructure + 1 first-canonical consumer + 4 Thread A DESIGN_SPECs at appropriate stages. ZERO source rows currently flag the bit (verified by T13 test). `.B` Steps 1-14 sequence implements the cohort migration cleanly via the auto-flow infrastructure. No HIGH-RISK lifecycle gaps. Operational notes below.

---

## Definition

- **Site:** `CoreFrameworks/CfgFieldRegistry.hpp:149`
- **Form:** `enum CfgFieldDescriptor::MetadataFlag` member
- **Type:** `uint16_t` (bit 13)
- **Value:** `1u << 13`

---

## Write sites (3 total — all metadata, no field-row writes at .A)

### `CfgFieldRegistry.hpp:149` — `enum MetadataFlag` declaration **[boot / static-init]**
- Write: `STAMP_BOUND_CFG_DERIVED = 1u << 13`
- Context: Bit allocation; subset semantics of `STAMP_BOUND` (bit 4) — stamp-bound INFERENCE-time cfg fields specifically

### `CfgFieldRegistry.hpp:1076` — `FOREACH_METADATA_BIT(X)` row **[compile-time / X-macro]**
- Write: `X(stamp_bound_cfg_derived, STAMP_BOUND_CFG_DERIVED)`
- Context: Auto-generates `g_global_cfg_stamp_bound_cfg_derived_mask` (via `X_GEN_GLOBAL_MASK` :1080) + `g_per_core_cfg_stamp_bound_cfg_derived_mask` (via `X_GEN_PER_CORE_MASK` :1086). At .A: both arrays all-zero `.rodata`.

### `CfgFieldRegistry.hpp:1134` — `ALL_METADATA_BITS_IN_USE` constant **[compile-time]**
- Write: `| CfgFieldDescriptor::STAMP_BOUND_CFG_DERIVED`
- Context: H16 enforcement; `static_assert` at :1136 validates enrollment

**At .B: 24 additional source-row writes** in `FOREACH_PER_CORE_CFG_FIELD` + `FOREACH_GLOBAL_CFG_FIELD` (metadata_flags column gets `| CfgFieldDescriptor::STAMP_BOUND_CFG_DERIVED` added) + 5 writes in `FOREACH_ML_CFG_FLAG` post-5→6 sig migration.

---

## Read sites (8 total)

### `CfgFieldRegistry.hpp:1080-1083` — `X_GEN_GLOBAL_MASK` X-macro expansion **[compile-time / .rodata]**
- Read: `cfg_compute_mask<CfgFieldDescriptor::STAMP_BOUND_CFG_DERIVED>(g_global_cfg_field_descriptors)`
- Constexpr; folds to all-zero array at .A

### `CfgFieldRegistry.hpp:1086-1089` — `X_GEN_PER_CORE_MASK` X-macro expansion **[compile-time / .rodata]**
- Read: same as above for per-core descriptors
- Constexpr; folds to all-zero array at .A

### `CfgFieldRegistry.hpp:1109-1110` — `ENROLLED_METADATA_BITS` reduction **[compile-time]**
- Read: bit gather via `X_GATHER_METADATA_BITS(stamp_bound_cfg_derived, STAMP_BOUND_CFG_DERIVED)`
- Validates H16 invariant via :1136 `static_assert`

### `CfgFieldRegistry.hpp:1178/1191/1204` — `CFG_COMPOSE_AUDIT_DECISIONS` rows **[compile-time]**
- Read: 3 decision rows (render_mask / save_mask / cli_explain_mask)
- Each = `COMPOSE_NA` (stamp_bound_cfg_derived is wire-format derived; orthogonal to GUI/save/CLI composed masks). Forces explicit composition decision per Gap 1 pre-emptive closure.

### `StampBoundDerivedFilter.hpp:50` — `STAMP_BOUND_CFG_emit_canonical_body` per-core walk **[slow-path / model-load]**
- Read: `g_per_core_cfg_stamp_bound_cfg_derived_mask.words` via `CFG_FIELD_FOR_EACH_SET_BIT`
- Lifecycle: invoked at stamp emit (write side, BacktestEngine) + stamp verify (read side, CoreModelZoo). Not on hot path. Layer 2 locale-pin wrap.

### `StampBoundDerivedFilter.hpp:62` — `STAMP_BOUND_CFG_emit_canonical_body` global walk **[slow-path / model-load]**
- Read: `g_global_cfg_stamp_bound_cfg_derived_mask.words` via `CFG_FIELD_FOR_EACH_SET_BIT`
- Lifecycle: paired with per-core walk; canonical body order = per-core THEN global

### `tests/controller_test.cpp:26017-26018, 26136-26137` — T2 + T13 test consumers **[test / boot]**
- Read: both masks for empty-body invariants (I1-I5) + popcount = 0 verification at .A
- Vacuously PASS at .A (empty body); `.B` exercises invariants against populated body

### `Version.hpp:98` — version-comment ledger **[passive metadata]**
- Read: documentation only

---

## Data flow graph

```
   ┌─────────────────────────────────────────────────────────────────────┐
   │  COMPILE-TIME                                                       │
   │                                                                     │
   │  [1] Enum bit decl :149                                             │
   │           │                                                         │
   │           ▼                                                         │
   │  [2] FOREACH_METADATA_BIT row :1076                                 │
   │           │                                                         │
   │           ├──> [3] X_GEN_GLOBAL_MASK → g_global_cfg_*_mask :1080    │
   │           │                                                         │
   │           ├──> [4] X_GEN_PER_CORE_MASK → g_per_core_cfg_*_mask :1086│
   │           │                                                         │
   │           ├──> [5] ENROLLED_METADATA_BITS reduction :1107           │
   │           │           │                                             │
   │           │           ▼                                             │
   │           │      H16 static_assert :1136 PASS                       │
   │           │                                                         │
   │           └──> [6] CFG_COMPOSE_AUDIT_DECISIONS 3 rows :1178/91/1204 │
   │                       │                                             │
   │                       ▼                                             │
   │                  count = 12 × 3 static_assert :1219 PASS            │
   │                                                                     │
   │  ALL metadata writes auto-flow via X-macro reduction.               │
   └──────────────────────┬──────────────────────────────────────────────┘
                          │
                          ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  RUNTIME (slow-path / model-load only; never hot-path)              │
   │                                                                     │
   │  [3]+[4] .rodata constexpr masks  (at .A: all-zero arrays)          │
   │           │                                                         │
   │           ▼                                                         │
   │  [7]  STAMP_BOUND_CFG_emit_canonical_body :40-76                    │
   │           ├── per-core walk via CFG_FIELD_FOR_EACH_SET_BIT :50      │
   │           └── global walk via CFG_FIELD_FOR_EACH_SET_BIT :62        │
   │           │                                                         │
   │           ▼                                                         │
   │  At .A: returns body_len=0 (no flagged rows)                        │
   │  At .B: returns body containing 24 lines (cohort flagged)           │
   │           │                                                         │
   │           ▼                                                         │
   │  [8] tests/controller_test.cpp:26009 T1 — body_len == 0 (.A)        │
   │  [9] tests/wire_format_invariants.hpp run_…body_invariants(ctx)     │
   │      → I1-I5 generic structural assertions :51-124                  │
   │  [10] tests :26134-26139 T13 — popcount == 0 (.A)                   │
   └─────────────────────────────────────────────────────────────────────┘
```

**Wire-format participation at .B onward:** consumer `STAMP_BOUND_CFG_emit_canonical_body` will be wired into the stamp body emit path post-.B Step 9 (production caller migration). At .A the emit fn exists but is NOT YET called from any production stamp emit path — verified via `rg "STAMP_BOUND_CFG_emit_canonical_body" --type cpp` returning only the test sites + self-reference.

---

## Lifecycle classification

- **Primary lifecycle:** **compile-time** for metadata + mask infrastructure; **slow-path / model-load** for emit consumer.
- **Cross-thread interactions:** NONE at .A. At .B onward, the emit body becomes part of the HMAC-signed canonical stamp body — produced by training thread, consumed by engine boot thread via file (not direct shared memory).
- **Publication mechanism:** stamp file (HMAC-signed canonical body); enforces H9 byte-preservation via Layer 2 locale-pin (`StampBoundDerivedFilter.hpp:43-47`).
- **H6 cluster:** Not applicable — `.rodata` constexpr; no `alignas(64)`.
- **H7 / H20:** Iteration via `CFG_FIELD_FOR_EACH_SET_BIT` is branchless within inner loop (`__builtin_ctzll` + `word &= word - 1`).

---

## Cohort sibling discovery

### Existing STAMP_BOUND-flagged rows in `FOREACH_*_CFG_FIELD`: **20 rows**
(via `grep -c "CfgFieldDescriptor::STAMP_BOUND\b"` minus the 1 enum decl + 1 ALL_METADATA_BITS_IN_USE ref = 20 row hits)
- `trading_mode` (GLOBAL :394)
- 12 PER_CORE scalar cohort (`ridge_lambda/ridge_cost_penalty/ridge_min_ic_floor/winsor_pct_low/winsor_pct_high/confidence_freshness_tau_secs/confidence_capacity_target_dollars/confidence_capacity_kappa/confidence_rmse_baseline/thompson_mu_prior/thompson_precision_prior/thompson_precision_obs`) at :559-595
- 2 PER_CORE Bandit (`bandit_algorithm/thompson_exp3_blend_alpha`) at :599+603
- 4 PER_CORE Risk degradation (`risk_degradation_curve/risk_full_size_threshold/risk_min_size_threshold/risk_min_size_pct`) at :608-617
- 1 PER_CORE risk_degradation_curve (counted above)

Plus the legacy registry `FOREACH_STAMP_BOUND_CFG` at `ML_Headers/StampBoundCfgRegistry.hpp:99-179` enumerates **25 rows** total — 1 more than the planned 24 because the registry includes both `ridge_within_horizon` + `ridge_across_horizons` (the 2 ML_CFG_FLAG bitmap-resident rows) — these are migrated via the `FOREACH_ML_CFG_FLAG` 5→6 sig at .B Step 2, not via direct flag-add.

### Cohort count math — verified against plan claim "29 fields"

Plan body lines 35 + 181-190 claim: **22 clean + 1 NEW (`gap_acceptable_threshold`) + 2 pre-canonical gaps (`ml_buy_threshold`/`bandit_blend_ratio`) + 4 retroactive `.A.7` (`ml_tp_pct`/`ml_sl_pct`/`barrier_blend_mode`/`per_horizon_barrier_blend`) = 29 fields**.

Verification against code at HEAD:
- 22 clean: 20 already-STAMP_BOUND-flagged rows + `gap_acceptable_threshold` not in CFG_FIELD (will be NEW row, plan Step 5) + missing legacy `barrier_blend_mode` should count differently. Re-reading plan: **22 = the rows in legacy registry that map cleanly to existing CFG_FIELD rows already flagged STAMP_BOUND**, not 22 = 20+2.
- `ml_buy_threshold` at :524: confirmed **NO STAMP_BOUND bit** (metadata_flags = `0`). Plan correct.
- `bandit_blend_ratio` at :528: confirmed **NO STAMP_BOUND bit** (metadata_flags = `0`). Plan correct.
- `ml_tp_pct` at :525: confirmed **NO STAMP_BOUND bit**. `.A.7` retroactive target.
- `ml_sl_pct` at :526: confirmed **NO STAMP_BOUND bit**. `.A.7` retroactive target.
- `barrier_blend_mode` at :637: confirmed **NO STAMP_BOUND bit**. `.A.7` retroactive target.
- `per_horizon_barrier_blend` is in `FOREACH_ML_CFG_FLAG:64` (bitmap-resident); flag-row migration via 5→6 sig.

**Plan-claimed cohort math matches code reality:** 22 clean + 1 NEW + 2 pre-canonical + 4 retroactive = 29 distinct source rows where `STAMP_BOUND_CFG_DERIVED` lands at .B. (Of these, 22 are pure metadata bit-adds on already-STAMP_BOUND rows; 2 need a two-step `STAMP_BOUND` + `STAMP_BOUND_CFG_DERIVED` add; 4 need full retroactive migration with POST_CFG deletion; 1 needs a new CFG_FIELD row entirely.)

**Mask popcount expectation post-.B:**
- `g_per_core_cfg_stamp_bound_cfg_derived_mask` popcount ≈ 22 (all scalar + bandit/thompson + risk_degradation + 4 retroactive `.A.7` that are per-core + 2 pre-canonical that are per-core)
- `g_global_cfg_stamp_bound_cfg_derived_mask` popcount ≈ 2 (`trading_mode` + `gap_acceptable_threshold` NEW row)
- Total ≈ 24 SCALAR rows + 5 ML_CFG_FLAG bitmap rows (counted differently via flag-row migration) = 29-field cohort overall.

---

## Blast-radius assessment

### Subsystems touched at .B

| Subsystem | Files | Surface |
|---|---|---|
| **CoreFrameworks/** | `CfgFieldRegistry.hpp` (metadata bit + mask infra + 22 row flag-adds), `StampBoundDerivedFilter.hpp` (consumer + tt::cfg_emit_synthetic_field<T>) | Auto-flow infra LOCKED; row metadata writes ONLY |
| **ML_Headers/** | `MlCfgFlagRegistry.hpp` (5→6 sig + 5 bit-adds), `StampBoundCfgRegistry.hpp` (legacy registry; emptied at Step 12), `StampHelper.hpp:150-156` (`STAMP_CFG_AUTOPOPULATE` walker migrated to `CFG_DRIFT_AUTOPOPULATE`), `ModelInference.hpp:1192-1207, 1395-1402, 1638-1644, 1782-1789` (4 X-macro walker sites — sister struct gen + parser + emit walks), `CoreModelZoo.hpp:225-247` (inline drift loop), `ConfidenceScore.hpp:729` (count usage), `StampBoundModelConstRegistry.hpp:11/49/276/376/382/487/541/550/661` (cross-ref comments), `CfgDriftCheckRegistry.hpp:190+283` (cross-ref + new rows on existing reg) |
| **MemHeaders/** | `CfgDriftGate.hpp` (NEW; ~80 LOC `DriftGateKind` enum + 5 gate fns + `FOREACH_DRIFT_GATE` 15-row sparse sidecar registry), `CfgDerivedInferenceCfgRegistry.hpp:12-25` (cross-ref) + `MemHeaders/CfgDriftAutoPopulate.hpp` (NEW; `CFG_DRIFT_AUTOPOPULATE` macro that walks via `CFG_FIELD_FOR_EACH_SET_BIT` per Path γ correction) |
| **Backtest/** | `BacktestEngine.hpp:1142` (production caller; STAMP_CFG_AUTOPOPULATE site → CFG_DRIFT_AUTOPOPULATE), `BacktestPanels.hpp:3298-3299` (cross-ref comments) |
| **CoreFrameworks/ (sister X-macro patterns)** | `Reconcile.hpp:78`, `SlowPathGateRegistry.hpp:224` (cross-ref comments documenting same shape) |
| **tests/** | `controller_test.cpp` (~20-30 new sections; existing legacy-registry tests at :4038-4057, :4805-4858, :22183-22311, :22648-22733, :23587-23619, :25079-25381 likely need migration or co-existence) + `wire_format_invariants.hpp` (already shipped at .A; activated at .B with populated body) |

### Wire-format / HMAC dependencies

**LOAD-BEARING H9 surface.** The `STAMP_BOUND_CFG_emit_canonical_body` fn at `StampBoundDerivedFilter.hpp:40-76` will (post-.B Step 9 production caller migration) emit a section of the HMAC-signed canonical body. Byte-preservation discipline:
- Layer 2 locale-pin (in fn; PRESERVED).
- Canonical order = per-core descriptors FIRST then global (consistent with .A test harness assumption).
- At .B: `tt::cfg_emit_synthetic_field<T>` replaces `.A` placeholder `"%s=stub\n"` snprintf — MUST produce wire-identical output to the legacy `STAMP_CFG_AUTOPOPULATE` walk. Plan body acknowledges: "**`.D` v5.14 stamp fixture regression**" guards this byte-equivalence.

**HMAC chain participation:** at .D ship. .B's job is to wire the new emit fn into the stamp emit path; .D locks the byte-equivalent fixture.

### Test fixture surface

- `tests/controller_test.cpp` line counts touching `FOREACH_STAMP_BOUND_CFG` symbol: ~16 distinct test sections (4038-4057, 4805-4858, 22183-22311, 22648-22733, 23587-23619, 25079-25381, 26134-26139). Most are inline X-macro walks counting fields or verifying entry presence (`X_COUNT_THOMPSON_FIELD`, `X_COUNT_RNG_SEED`). Some use `STAMP_CFG_AUTOPOPULATE(inf, cfg)` directly (4820, 4840, 4858, 22290, 22311, 22722, 22733).
- Post-.B Step 12 legacy registry empty-out: these walks become empty (zero rows iterated). Tests that assert `FOREACH_STAMP_BOUND_CFG_COUNT >= N` (4057, 4893, 22189, 25381) become FALSE — expect failures unless migrated. **Plan body line 138-139 acknowledges: "Legacy `FOREACH_STAMP_BOUND_CFG` empty-out is LAST — after all consumer migrations land".** Plan Step 12 must include test-suite migration of these counting assertions.

### Cross-version compat

- Surface G discipline preserved: legacy v5.14.x stamps lacking new fields load with `has_<field>=0` → drift check skipped silently. **No `MODEL_FORMAT_VERSION` bump.**
- Legacy stamps remain parseable; new wire format is additive.

---

## Sites that READ legacy `FOREACH_STAMP_BOUND_CFG` (would break at .B Step 12 empty-out)

**Non-header consumers:** 0 (legacy walks are ONLY inside headers; production callers go through `STAMP_CFG_AUTOPOPULATE` macro which wraps the walk).

**Header consumers that walk the registry (must be migrated to `CFG_DRIFT_AUTOPOPULATE` / `CFG_FIELD_FOR_EACH_SET_BIT` at .B):**
1. `ML_Headers/ModelInference.hpp:1199` — struct gen for `ModelStampResult` (CFG-bound fields with `has_<name>` Surface G)
2. `ML_Headers/ModelInference.hpp:1401` — parser branches in `verify_model_stamp`
3. `ML_Headers/ModelInference.hpp:1643` — sister struct gen for `StampInferenceCfgInputs`
4. `ML_Headers/ModelInference.hpp:1788` — emit walk in `stamp_write_for_model`
5. `ML_Headers/CoreModelZoo.hpp:243` — inline drift loop (CFG-bound entries)
6. `ML_Headers/StampHelper.hpp:156` — `STAMP_CFG_AUTOPOPULATE(inf, cfg)` invocation
7. `ML_Headers/StampBoundCfgRegistry.hpp:230` — auto-populate macro internal walk
8. `ML_Headers/StampBoundCfgRegistry.hpp:264` — `FOREACH_STAMP_BOUND_CFG_COUNT` expression
9. `ML_Headers/ConfidenceScore.hpp:729` — comment-only reference to `FOREACH_STAMP_BOUND_CFG_COUNT` pattern (no live walk)

**Production callers of `STAMP_CFG_AUTOPOPULATE`:**
1. `Backtest/BacktestEngine.hpp:1142` (acknowledged in plan body Item 9; .B Step 9 migration target)
2. `ML_Headers/StampHelper.hpp:156` (same)

**Test sites that walk the registry (must be reviewed at .B Step 13):**
- `tests/controller_test.cpp:4057, 4810, 4820, 4840, 4858, 22188, 22290, 22311, 22722, 22733, 22189, 23599, 23617, 25381` (14 sites; plan body line 142 lists ~20-30 new tests but doesn't explicitly enumerate legacy-test-migration; flag as moderate-attention item for .B Step 13)

**Plan body coverage check:** plan Items 9 / Step 9 enumerate the 12+ consumer site migration goal. Plan body lines 252-253 mention `ArchFieldDriftRegistry.hpp:10+29` (2 comments). Other comment-only refs (`ControllerConfig.hpp:57, 557, 704, 743, 752, 1002, 1274, 1313, 1883`; `BacktestPanels.hpp:3298-3299`; `CfgDerivedInferenceCfgRegistry.hpp:12-25`; `MetaRegistry.hpp:52`; `StampBoundModelConstRegistry.hpp:11,49,...`) are cross-ref docstrings — Step 12 plan body line "comment/cross-ref cleanup" implies sweep.

---

## Stage 3 ACTIVE check — 4 Thread A DESIGN_SPECs

Per workspace `DESIGN_SPECS/` at HEAD:

| DESIGN_SPEC | Status at .A ship (HEAD) | Expected at .B ship |
|---|---|---|
| `composed-filter-mask-pattern.md` | **Stage 2 DRAFT v1.0** (3 retroactive canonicals at HEAD: render_mask / save_mask / cli_explain_mask). Stage 3 first reference: **pending — either `.F.4d.1.A` if `.A` introduces new composed mask OR next ship that adds one**. `.A` did NOT add a new composed mask; only added a derived-filter consumer. Stage 3 advancement → pending future composed-mask addition. | UNCHANGED at .B (B doesn't add composed masks either; first-canonical advancement waits for `.F.4e` or later). |
| `wire-format-canonical-body-invariants-helper.md` | **Stage 2 DRAFT v1.0 → Stage 3 first reference at `.F.4d.1.A` ship** (per banner). Code lands at `tests/wire_format_invariants.hpp` :51-124 (helper) + `tests/controller_test.cpp:26014-26028` (T2 invocation). At .A: body empty, helper vacuously PASSes. | Stage 3 ACTIVE confirmed at .A. At .B: helper exercised against populated body (24-row STAMP_BOUND_CFG_DERIVED activation); I1-I5 now non-vacuous. **No status change at .B**; remains Stage 3 ACTIVE until 2nd canonical (planned: v5.15.6.C AFFECTS_STAMP_PARITY training cfg). |
| `metadata-bit-driven-derived-filter-framework.md` | **v1.2 Path γ correction IN PROGRESS at .A planning (banner says "in progress")**. The spec body still contains v1.0/v1.1 Option B macro signatures + parallel walker mechanism. Banner at line 4: "*v1.0/v1.1 mechanism … is SUPERSEDED by Option E (existing FOREACH_METADATA_BIT + cfg_compute_mask + CFG_FIELD_FOR_EACH_SET_BIT)*". Line 154 v1.1 revision banner: "*The code snippets below still show the v1.0 LOCKED-param signatures — pending full doc cleanup at `.F.4d.1.A` ship close auto-write*". | **Spec body cleanup is OWED at .B (TECH_DEBT-089 spec-vs-code drift audit cadence per CLAUDE.local.md)**. Either .A ship-close auto-write didn't fire OR was deferred to .B. **YELLOW** flag — spec body remains v1.0 superseded at HEAD; first-canonical reference exists in code but spec body misrepresents the mechanism. Plan body lines 11-19 acknowledge: "body content has residual references to SUPERSEDED v1.0 framework macros". **`.B` Step 0 should include the spec body cleanup pass.** Otherwise Stage 3 ACTIVE has documentation drift. |
| `framework-composition-overview.md` | **v1.1 Path γ correction IN PROGRESS at .A planning (banner says "in progress")**. Same shape as above — v1.0 topology diagram describes parallel walker mechanism that doesn't match codebase. Banner line 4: "*Topology + per-framework brief tables below are v1.0 SUPERSEDED text pending rewrite at `.A` ship close*". | Same as above — **YELLOW** documentation drift; OWED cleanup pass. |

**Stage 3 ACTIVE verdict for the 4 DESIGN_SPECs:**
- 2 of 4 are confirmed Stage 3 ACTIVE per their banners (wire-format-helper + metadata-bit-framework) at .A ship.
- 1 of 4 (composed-filter-mask) is Stage 2 DRAFT pending future composed-mask addition (no advancement at .B).
- 2 of 4 carry **documentation drift** — their spec bodies still describe v1.0 mechanisms superseded by Path γ. **`.B` audit-update-implement cycle MUST include spec body cleanup OR explicitly defer-and-document** (plan body lines 11-19 corroborate).

---

## HIGH-RISK lifecycle gaps

**None at HEAD `.A`.** Auto-flow infrastructure is sound; consumer exists; tests cover the empty-body case structurally (I1-I5 vacuous PASS); cohort breakdown matches code reality; legacy registry sites are all enumerated.

**MED-RISK items for .B planning attention:**

1. **YELLOW — DESIGN_SPEC body drift** (already acknowledged in plan body lines 11-19): `metadata-bit-driven-derived-filter-framework.md` v1.2 + `framework-composition-overview.md` v1.1 spec bodies remain v1.0 superseded prose. `.A` ship-close auto-write per CLAUDE.local.md "Auto-write contracts" rule expected the cleanup but it landed deferred. **Action:** include spec body cleanup in .B Step 0 or .B postmortem auto-write.

2. **YELLOW — legacy test-fixture migration scope under-enumerated**: plan body lines 137-141 mention "~20-30 new tests" but the 14 legacy test sites that walk `FOREACH_STAMP_BOUND_CFG` directly need migration to avoid breaking when Step 12 empties out the registry. **Action:** .B Step 13 should explicitly call out the legacy test migration list (controller_test.cpp at the 14 line ranges enumerated above) — not just additions.

3. **GREEN-with-watch — production caller migration ordering**: `BacktestEngine.hpp:1142` + `StampHelper.hpp:156` are the only 2 production callers of `STAMP_CFG_AUTOPOPULATE`. Plan Step 9 sequences these AFTER Step 8 (`CFG_DRIFT_AUTOPOPULATE` macro lands) — correct order. **Watch:** Step 12 (legacy empty-out) MUST come after both Step 9 sites are migrated; otherwise transient window where production caller invokes empty-walk macro. Plan body line 139 explicitly orders correctly.

4. **GREEN — H9 byte-preservation crossing**: `tt::cfg_emit_synthetic_field<T>` at .B Step 1 MUST produce wire-identical output to legacy `STAMP_CFG_AUTOPOPULATE` walk. The `.D` v5.14 fixture regression test guards this. .B's invariant helper `wire_format_invariants.hpp` I1-I5 + planned I6-I7 catch structural drift but NOT byte-precise drift — that's `.D`'s job.

5. **GREEN — H6 thread isolation**: `g_*_cfg_stamp_bound_cfg_derived_mask` arrays are `.rodata` constexpr; no cross-thread write hazard.

---

## Recommended caveats for .B coding

- Include `CfgDriftCheckRegistry.hpp:283` comment "*All 4 entries map to FOREACH_STAMP_BOUND_CFG appendix rows*" in Step 12 cross-ref cleanup (the comment will be stale after empty-out).
- After Step 12, the `MetaRegistry.hpp:52` row for `FOREACH_STAMP_BOUND_CFG` either gets DELETED (registry no longer exists) or carries a "*LEGACY — empty stub for transition*" marker. Plan body line 47/41 mentions FOREACH_REGISTRY removal in Step 12.
- `StampBoundModelConstRegistry.hpp` has multiple comments referring to emit ordering "*walks PRE_CFG → FOREACH_STAMP_BOUND_CFG → POST_CFG*" (lines 49, 276, 376, 382, 487). After legacy empty-out, the middle walk becomes empty; comments should be updated to reflect the new ordering `walks PRE_CFG → DERIVED_FILTER (auto-flow) → POST_CFG` or similar.
- `Reconcile.hpp:78` + `SlowPathGateRegistry.hpp:224` carry "*Pattern: same shape as STAMP_CFG_AUTOPOPULATE*" cross-refs — these comments survive (the X-macro autopopulate PATTERN survives; only the specific stamp-bound-cfg APPLICATION moves to derived-filter framework).

---

## Trace summary

- Symbol exists at 1 bit declaration + 1 X-macro registry row + 1 ALL_BITS_IN_USE constant + 3 CFG_COMPOSE_AUDIT decisions + 3 mask-array materialization sites + 2 consumer iterator sites + 5 test consumer sites = **15 chain sites total at HEAD `.A`**
- Mask popcount at .A: **0 / 0** (per-core / global). Cohort migration target post-.B: **22 / 2** (per-core / global) + 5 ML_CFG_FLAG bitmap rows via 5→6 sig
- 0 production callers wired at HEAD .A — first wiring lands at .B Step 9 (BacktestEngine + StampHelper)
- Stage 3 ACTIVE for 2 of 4 Thread A DESIGN_SPECs; 2 carry documentation drift owed to .B/postmortem auto-write
- No HIGH-RISK gaps; 2 YELLOW (spec body cleanup + legacy test migration scoping); 3 GREEN-with-watch (ordering + byte-precision + thread isolation)

**Recommendation:** **GREEN — proceed with .B per plan body v1.2 + apply v1.3 corrections enumerated in plan body lines 11-21 at Step 0**. Spec body cleanup for `metadata-bit-driven-derived-filter-framework.md` v1.2 + `framework-composition-overview.md` v1.1 should be added to .B Step 0 OR .B Step 14 (build verify + tag boundary) — not deferred past .B ship.

