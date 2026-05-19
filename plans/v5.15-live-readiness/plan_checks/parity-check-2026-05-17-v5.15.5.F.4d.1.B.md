# /parity-check report — 2026-05-17 — v5.15.5.F.4d.1.B migration + consumer

## Plan summary

- **Target:** `subplans/2026-05-16-v5.15.5.F.4d.1.B-migration-consumer.md` v1.2 + sidecar v1.1
- **Engine HEAD:** `39b9947` (post-`.A` ship; `feat/v5.15-live-readiness`)
- **Baseline:** 3196 controller_test + 17 depth_recorder_test GREEN
- **Predecessor:** `v5.15.5.F.4d.1.A` LOCAL ship (Path γ+ v2 framework infra)
- **Audit scope:** stamp + cfg + scaler-adjacent (Sections D/E/F + L production-caller class)
- **Preloaded:** wire-format-byte-preservation-discipline, autopopulate-pattern,
  x-macro-registry, struct-padding-determinism; `PARITY_ISSUES.md` ledger
  (PARITY-001..PARITY-025; PARITY-020 + PARITY-022 directly load-bearing).

---

## Top-line verdict: **YELLOW (HIGH findings; structural — not blocking but require triage before `.B` coding)**

`.B` plan body has the right *direction* (single-source-of-truth via FOREACH_METADATA_BIT bit; sidecar-driven cohort gates; legacy registry empty-out) but **5 unenumerated production sites** consume the legacy `FOREACH_STAMP_BOUND_CFG` registry beyond the 3 sites the plan body lists, and the plan's Step 12 sequencing ("empty-out → consumer migrations") cannot be reconciled — emptying the macro before these 5 sites are re-pointed will break the build at struct-field-gen + parser + emit walks. The wire-format byte-preservation rests on these consumer site migrations being identity-preserving against the LEGACY emit shape. Plus the plan loses the existing `STAMP_CFG_AUTOPOPULATE` macro that closes PARITY-020 — `.B`'s new `CFG_DRIFT_AUTOPOPULATE` is a *drift-check* sister, NOT a populate replacement.

---

## Findings

### HIGH-1 — Plan body's "3 active consumer sites" undercount; 5 production sites in `ModelInference.hpp` consume FOREACH_STAMP_BOUND_CFG and are NOT enumerated

**File:line citations of unenumerated sites:**
- `ML_Headers/ModelInference.hpp:1199` — `StampInferenceCfgInputs` **struct-field generation** (declares `has_<name>` + typed `<name>` fields)
- `ML_Headers/ModelInference.hpp:1401` — **verifier parser branches** (`else if (strcmp(key, "<name>") == 0)`)
- `ML_Headers/ModelInference.hpp:1643` — `ModelStampResult` **struct-field generation** (parser-side mirror; `int has_<name>` + typed `<name>`)
- `ML_Headers/ModelInference.hpp:1788` — **wire-format emitter walk** (the canonical body emit — load-bearing for H9 byte preservation)
- `ML_Headers/StampBoundCfgRegistry.hpp:230` (inside `STAMP_CFG_AUTOPOPULATE`) — **production populate walker** referenced by `StampHelper.hpp:156` (the helper called by `BacktestEngine.hpp:1142` and `train_model_worker_fn`)

The plan body § Step 9 enumerates only `CoreModelZoo.hpp:225-247` + `StampHelper.hpp:150` + `ConfidenceScore.hpp:729` and treats `ModelInference.hpp` references as "comment text updates" (§ Step 9 "~8-10 sites; non-functional"). They are **structural consumers**, not comment text. Step 12's `#define FOREACH_STAMP_BOUND_CFG(X)` empty-out would break compilation at these 5 sites (struct fields evaporate; parser branches disappear; emit loop is no-op).

**Recommended action:** Either (a) expand `.B` Step 9 to migrate all 5 ModelInference + StampHelper consumer sites to the Path γ walker before Step 12 empty-out, OR (b) keep the legacy macro non-empty post-`.B` and defer empty-out to a follow-up "consumer-empty-out" sub-ship after framework-side equivalents land for struct gen + parser + emit. Option (b) preserves byte equivalence with lowest risk; option (a) is the documented intent but plan body underestimates scope by ~3-4× LOC.

Cross-ref: `DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md` Class L (production-caller field-population gap class).

### HIGH-2 — `STAMP_CFG_AUTOPOPULATE` (the existing PARITY-020 closure) is NOT preserved by `CFG_DRIFT_AUTOPOPULATE`

The plan body presents `CFG_DRIFT_AUTOPOPULATE` as "sister to STAMP_CFG_AUTOPOPULATE + INFERENCE_CFG_AUTOPOPULATE" (§ Step 8), but the existing `STAMP_CFG_AUTOPOPULATE(inf, cfg)` macro (`StampBoundCfgRegistry.hpp:226`) **populates `inf.has_<name> = 1; inf.<name> = (type)(get_cfg)`** at production emit time. The drift-check macro performs comparison only. `.B` deletes `FOREACH_STAMP_BOUND_CFG` body at Step 12 but does NOT replace `STAMP_CFG_AUTOPOPULATE`. `StampHelper.hpp:156` (`Stamp_AssembleAndEmit`, the PARITY-020 fix call site) then expands to nothing → **every stamp emitted via `Stamp_AssembleAndEmit` post-`.B` lacks all 24 cohort fields**. Wire format silently regresses on every production caller; HMAC chain still computes but body shape strictly shrinks. Re-introduces PARITY-020 (production-caller field-population class) at the framework-migration surface.

**Recommended action:** Add a **`STAMP_CFG_POPULATE_FROM_DERIVED(inf, cfg)`** companion macro to `.B` scope alongside `CFG_DRIFT_AUTOPOPULATE`. The populate walker reuses `tt::cfg_get_field<T>` to read source-row cfg value + writes `inf.has_<name>=1 + inf.<name>=...` via `tt::cfg_save_field<T>` (the second-source from `.A`'s tt:: trio). Then `StampHelper.hpp:156` swaps `STAMP_CFG_AUTOPOPULATE(inf, cfg)` → the new macro. Without this, PARITY-020 re-opens. Cross-ref: `DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md`.

### HIGH-3 — Bitmap-row emit-shape ternary `(BITMAP_IS_SET(...) ? 1 : 0)` is load-bearing for H9 byte equivalence; sidecar's `tt::cfg_emit_synthetic_field<T>` proposes per-type emit that bypasses it

The 4 bitmap rows in legacy `FOREACH_STAMP_BOUND_CFG` (lines 107-108, 110-111, 124-125, 145-146 + new `per_horizon_barrier_blend` per Step 7) emit as `int` "%d" with **explicit ternary normalization** `(BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_X) ? 1 : 0)`. This is per `wire-format-byte-preservation-discipline.md` § 5b (H9) — bitmap-bool storage must serialize as canonical 0/1 ints not raw bitwise-AND result (which is the mask value, not 0/1).

The sidecar's `tt::cfg_emit_synthetic_field<T>` (§ Step 1) emits `bool` via `(idx & 1u) ? 1 : 0` — **synthetic deterministic value**, not the actual cfg value. This is fine for `.A`'s placeholder body, but `.B`'s Step 3 activates the bitmap walker in `StampBoundDerivedFilter.hpp` to emit REAL per-bit values via `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_##name) ? 1 : 0`. **Per-cohort emit dispatch needs to disambiguate:**

- Scalar source rows (FPN<F>, int, double types in `FOREACH_*_CFG_FIELD`) → `tt::cfg_emit_field<T>(d, cfg, ...)` via descriptor offset + type-trait
- Bitmap source rows (5 in `FOREACH_ML_CFG_FLAG` with STAMP_BOUND_CFG_DERIVED) → `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK) ? 1 : 0` emit shape

The plan body treats `tt::cfg_emit_synthetic_field<T>` as the wire-format emit fn (§ Steps 1, 3, sidecar examples) but synthetic ≠ real cfg value. The plan needs an actual emit fn (call it `tt::cfg_emit_field<T>(d, cfg, buf, cap)`) distinct from the synthetic test/invariants helper. Without this distinction, either (a) wire format breaks (synthetic deterministic value goes into stamps) or (b) the bitmap-row dispatch path is silently lost.

**Recommended action:** Split `tt::cfg_emit_synthetic_field<T>` (test-only; landed `.A`-side helper for invariants I1-I5) from a new `tt::cfg_emit_field<T>(d, cfg, buf, cap)` (production emit reading actual cfg value). Add bitmap-emit branch in the per-row callback at the `StampBoundDerivedFilter.hpp` walk site that dispatches on `d.emit_source == BITMAP_BIT` (the existing 7th-col token in `FOREACH_STAMP_BOUND_CFG`) — but the source rows in `FOREACH_*_CFG_FIELD` don't carry that column. Implication: source-row dispatch needs to know "this row's wire-shape is bitmap-bit not scalar" — a 4th DriftGateKind-style sidecar (`FOREACH_EMIT_SHAPE` or sister) OR mechanical via `lives_in_struct == ML_CFG_FLAG_BITMAP` lookup. Plan body does NOT enumerate this dispatch.

Cross-ref: `wire-format-byte-preservation-discipline.md` § 5b; `heterogeneous-registry-pattern.md` Y3 dispatch.

### HIGH-4 — Pre-canonical fix order at Step 6 risks v5.14 stamp parser regression

Step 6 says: "**ADD STAMP_BOUND first (pre-canonical fix; v5.14 stamps stay parseable per Surface G); then ADD STAMP_BOUND_CFG_DERIVED. Two-step migration ensures legacy-stamp back-compat.**" For `ml_buy_threshold` + `bandit_blend_ratio`. But the underlying issue is:

- `ml_buy_threshold` IS already in legacy `FOREACH_STAMP_BOUND_CFG` (line 157 — `(X(ml_buy_threshold, double, "%.17g", 0.0, ..., 1, DIRECT_FIELD))`). So v5.14 stamps already contain `ml_buy_threshold=...` lines. The "pre-canonical fix" framing is misleading — the field IS canonically stamp-bound; only the metadata-bit on the source row is missing. Adding the STAMP_BOUND bit doesn't change v5.14 stamp parseability; it changes which CODE PATHS consume the field.

- Same for `bandit_blend_ratio` (which IS in StampBoundModelConstRegistry.hpp:296-297 POST_CFG manual section — emitted via the model-const PRE/POST split, not via FOREACH_STAMP_BOUND_CFG). Adding STAMP_BOUND_CFG_DERIVED + deleting the manual POST_CFG entry means the field MOVES from the POST_CFG-mirror walk to the derived-filter walk → **emit-order changes**. v5.14 stamps that have `bandit_blend_ratio=...` at the POST_CFG position will now appear at the cfg-section position (between PRE_CFG and POST_CFG). Same byte content per line but **different file offset within canonical body** → HMAC body input bytes differ → HMAC mismatch on v5.14 stamps loaded into post-`.B` engine.

**Recommended action:** Verify with explicit v5.14 fixture round-trip BEFORE Step 6's manual POST_CFG entry deletion. If the POST_CFG → cfg-section migration breaks emit order, either (a) preserve POST_CFG mirror until `.D` fixture lands, OR (b) defer `bandit_blend_ratio` POST_CFG deletion to `.D` paired with fixture regression. Either way, Step 6's "pre-canonical fix" wording understates the actual byte-shift risk. v5.14 fixture (queued for `.D`) must catch this; **`.B` cannot rely on `.D` fixture for verification — fixture lands AFTER `.B` ship close per umbrella sequencing**.

Cross-ref: `wire-format-byte-preservation-discipline.md` § 5; `pre-post-cfg-registry-split-for-emit-order-preservation.md` (load-bearing for canonical wire format).

### HIGH-5 — `gap_acceptable_threshold` NEW global row will introduce a brand-new key in canonical body emit; legacy v5.14 stamps will load with `has_gap_acceptable_threshold=0` (Surface G OK) but POST-`.B` stamps gain a new line → bytewise drift in canonical body

Step 5 adds `gap_acceptable_threshold` to `FOREACH_GLOBAL_CFG_FIELD` with `STAMP_BOUND_CFG_DERIVED` flag. Per `.A`'s `StampBoundDerivedFilter.hpp` walk-order (per-core first, then global), the field appears in the **global tail** of canonical body emit. Legacy stamps lack the key → parser via Surface G falls through with `has_gap_acceptable_threshold=0` (good — no regression on load). But **NEW stamps** emit the line → engines loading those stamps with default cfg compare `0.5` (default per sidecar Step 5 `DBL(0.5, 0.0, 1.0)`) vs stamped `0.5` → drift-count stays zero (good). BUT if operator changes the cfg post-training, drift fires.

The plan body notes this row is "pre-canonical for `v5.15.6.C` AFFECTS_STAMP_PARITY reclassification" — meaning the row's STAMP_BOUND_CFG_DERIVED-only status is temporary; it should arguably be `AFFECTS_STAMP_PARITY` instead (training-only field; engine consumes for boundary purposes only). The TWO bit choices have different semantics: STAMP_BOUND_CFG_DERIVED triggers drift-check at model load (engine must match training value); AFFECTS_STAMP_PARITY means training stamps it for forensics but engine doesn't compare.

**Recommended action:** Clarify intent in `.B` plan body: if `gap_acceptable_threshold` is training-only-not-engine-consumed, STAMP_BOUND_CFG_DERIVED is the wrong flag — should be AFFECTS_STAMP_PARITY only. The "future reclassification at `v5.15.6.C`" comment-tag suggests this is known but the field still ships with the wrong flag at `.B`. Either (a) ship with AFFECTS_STAMP_PARITY at `.B` and skip the `v5.15.6.C` reclassification entirely, OR (b) document that the engine consumer for this field IS the boundary check that triggers drift (verify in code grep). Currently `.B`'s plan body ships with semantic ambiguity. Cross-ref: `cfg-flag-eligibility-criteria.md` (5-criteria framework + cohort audit).

### MED-1 — Layer 2 locale-pin coverage at `tt::cfg_emit_synthetic_field<T>` is unverified

The sidecar (§ Step 1) shows `tt::cfg_emit_synthetic_field<T>` using `snprintf(buf, cap, "%s=%.17g\n", ...)` for FPN/double — fine for shape, but per H9 the locale pin (LC_NUMERIC=C; precedent `ModelInference.hpp:1697`) is asserted **at the caller**, not the helper. The `.A`-shipped `StampBoundDerivedFilter.hpp:45-47` does pin (newlocale + uselocale). But IF the new `tt::cfg_emit_field<T>` (per HIGH-3) is called from OTHER sites (e.g., `CFG_DRIFT_AUTOPOPULATE` may emit via `snprintf` for debug strings; `Stamp_AssembleAndEmit` populate path; future consumers), each new caller needs its own locale pin OR the helper should pin internally. Plan body does not specify.

**Recommended action:** Either (a) `tt::cfg_emit_field<T>` pins LC_NUMERIC=C internally (thread-local; cheap) — preferred for safety, mirror H9 pattern; OR (b) add explicit caller-side pin requirement to the docblock + an `assert(LC_NUMERIC pinned)` debug check. Caller-side pinning is fragile (silent bytewise drift if a caller forgets); helper-side pinning is safer per locale-pin precedent at all 4 emit sites today. Cross-ref: `wire-format-byte-preservation-discipline.md` Layer 2.

### MED-2 — `CFG_DRIFT_AUTOPOPULATE` macro signature change: `(failure_flags, *handle, cfg)` v1.0 → `(failure_flags, handle, cfg, drift_count_ref)` v1.1 — Step 9 site migration ambiguity

The plan body § Step 8 (line 265) defines `CFG_DRIFT_AUTOPOPULATE(failure_flags, handle, cfg)` (3-arg). The sidecar v1.1 (§ Step 8 line 293) defines it `(failure_flags, handle, cfg, drift_count_ref)` (4-arg). Step 9 active site migrations at `CoreModelZoo.hpp:225-247` need a specific call signature. The legacy walker increments `sr.inference_cfg_drift_count++` inside the X-macro body (line 235). The β4 callback (per sidecar line 286-290) increments `*ctx->drift_count` via the 4-arg explicit `drift_count_ref` parameter. v1.0 plan body and v1.1 sidecar are out of sync; the body residual cleanup note at top of plan body says "lines 247, 289, 292: concrete CFG_DRIFT_AUTOPOPULATE code sample uses SUPERSEDED walker fn" — but doesn't note this arity drift.

**Recommended action:** Lock the macro signature to 4-arg (`drift_count_ref` explicit) at update-step cleanup; the legacy walker semantics require the count increment; making it explicit prevents Class 18 mirror at consumer sites. Verify CoreModelZoo.hpp:225-247 call site post-migration matches.

### MED-3 — Layer 5b structural invariants I1-I7 verify SHAPE, not BYTES; cohort row activation may pass I1-I7 while breaking v5.14 stamp HMAC chain

The plan body § "Verification gate" "`.B`-specific" claims "Invariant I1-I7 all pass at populated body case" + "v5.14 stamps continue loading byte-identical". I1-I7 (per `.A`'s `wire_format_invariants.hpp`) verify line count = popcount, kv format, no comma decimals, row presence, per-core-before-global ORDER — but **NOT byte-for-byte equality against a fixture**. The plan body acknowledges: "Layer 4 verification at `.D` confirms; `.B` invariants verify shape." This means `.B` ships with NO byte-level v5.14 round-trip protection; **the v5.14 stamp fixture lands at `.D`** (per umbrella scope), but `.B`'s 24-row cohort migration is the wide-blast-radius change that most risks byte-shape regression.

**Recommended action:** Land a minimal byte-equivalence canary test at `.B` (not the full v5.14 fixture; a synthetic minimal-cohort stamp emit → re-parse → re-emit round-trip with bytewise assert). Cost: ~30 min; closes a 1-ship-cycle gap where structural shape verification passes but byte drift slips through. Or accept the gap with explicit rollback discipline if `.D` fixture catches a `.B`-introduced regression (~revert `.B` + re-do; per-Phase mid-flight tags help bound rollback cost).

### MED-4 — `winsor_pct_low` / `winsor_pct_high` two-bit transition (STAMP_BOUND + STAMP_BOUND_CFG_DERIVED) may emit twice

Step 4's Winsor cohort migration adds `STAMP_BOUND_CFG_DERIVED` alongside existing `STAMP_BOUND` bit. Post-migration, BOTH bits are set on the source row. The legacy walker (FOREACH_STAMP_BOUND_CFG body at line 136+139) emits `winsor_pct_low=...` + `winsor_pct_high=...` lines if the legacy registry is still non-empty (pre-Step 12). The new derived-filter walker emits them via `StampBoundDerivedFilter.hpp`. If both walkers fire during `.B` mid-flight Steps 4-11 (before Step 12 empty-out), the canonical body contains **two copies of each Winsor line** → bytewise drift, HMAC mismatch.

**Recommended action:** Reorder steps: Step 12 (legacy empty-out) must happen BEFORE the derived-filter walker is exercised at any production site. OR the new walker must run at a DIFFERENT body-position than the legacy walker (e.g., legacy emits at the existing cfg-section; new walker emits at a `.B`-specific section) — but that's emit-order divergence. Simpler: gate the derived walker with `#ifdef` until Step 12 lands, OR re-sequence the implementation steps to: 1, 2, 3, **12** (legacy empty), 4-11 (cohort migration; walker is now sole source). Cross-ref: x-macro-registry-with-presence-dispatch.md.

### LOW-1 — Sidecar test verification gate misses parser branch (`ModelInference.hpp:1401`)

The plan body's test enumeration at "Test expectations" lists tests for emit + drift check + populate but **not parser branches**. With 24-row migration, every stamp-bound field has parser branch at `ModelInference.hpp:1401`. If a row migrates out of the legacy registry without a corresponding parser-side replacement, the verifier will skip the key on parse (no `else if (strcmp(key, "<name>") == 0)`) → `r.has_<name>` stays 0 → drift check skips (Surface G safe; no false-fire) BUT also no protection.

**Recommended action:** Add to `.B` test plan: post-migration verifier parser test that round-trips a stamp with all 24 cohort fields → re-parses → asserts `r.has_<field>==1` for every cohort row. Closes Section L production-caller class for the parser surface.

### DOCUMENT-ONLY — `.A.7` retroactive POST_CFG entries' deletion may have semantic consequence

The 4 retroactive `.A.7` cohort fields (`ml_tp_pct`, `ml_sl_pct`, `barrier_blend_mode`, `per_horizon_barrier_blend`) currently live in `StampBoundModelConstRegistry.hpp` POST_CFG section, named `inference_cfg_<field>` (line 286 + sister entries). The plan body Step 7 "DELETE corresponding manual POST_CFG entry" deletes the `inference_cfg_<field>` mirror but adds the field at source-row level (cfg side). The downstream consumer at `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp` (the `INFERENCE_CFG_AUTOPOPULATE` registry per `StampHelper.hpp:159+`) may still expect the cfg-derived `inference_cfg_<field>` shape. If `INFERENCE_CFG_AUTOPOPULATE` reads source rows differently than the derived-filter walker, parity drifts.

**Recommended action:** Verify CfgDerivedInferenceCfgRegistry.hpp's view of the 4 `.A.7` cohort fields post-deletion; ensure either (a) the registry-driven INFERENCE_CFG_AUTOPOPULATE continues to populate `inf->inference_cfg_<field>` correctly via the SOURCE row at FOREACH_PER_CORE_CFG_FIELD (not the deleted POST_CFG manual entry), OR (b) the inference_cfg_<field> mirror lands in the derived-filter walker output. Cross-ref: `PARITY-024` (per-arm trained TP/SL barriers stamped but not consumed at serving) — directly related.

---

## Cross-checks against existing protections

| Protection | Status | Notes |
|---|---|---|
| FEATURE_REGISTRY_HASH | INTACT | not touched by `.B`; mask infra unchanged |
| Snapshot tests for compute fns | INTACT | not touched |
| Scaler `feature_registry_hash` binding | INTACT | not touched |
| Stamp body `scaler_sha256` | INTACT | not touched |
| Stamp body `engine_version` | INTACT | not touched |
| `STAMP_CFG_AUTOPOPULATE` (PARITY-020 closure) | **AT RISK** per HIGH-2 | empty-out Step 12 silently removes the macro's body content |
| `STAMP_MODEL_CONST_AUTOPOPULATE` quarantine (PARITY-022) | INTACT | model-const path unchanged |
| H9 wire-format-byte-preservation | **AT RISK** per HIGH-3 + HIGH-4 + MED-3 + MED-4 | bitmap-emit shape; v5.14 round-trip not yet protected |

---

## Suggested ship sequence

- **Minimum `.B` scope addition:** add `STAMP_CFG_POPULATE_FROM_DERIVED` macro + migrate 5 ModelInference + StampHelper sites + lock CFG_DRIFT_AUTOPOPULATE to 4-arg sig + clarify `gap_acceptable_threshold` flag intent (HIGH-1, HIGH-2, MED-2, HIGH-5)
- **Strongly recommend before `.B`:** add a minimal byte-equivalence canary test (MED-3); reorder Steps 4-12 so legacy empty-out (Step 12) precedes cohort migration walks at production sites (MED-4); split synthetic vs production emit fn (HIGH-3)
- **Defer to `.D`:** v5.14 stamp fixture full round-trip (already queued); paired bandit_blend_ratio POST_CFG → derived-filter emit-order change verification (HIGH-4)

---

## NOT a bug (verified-safe items)

- **Bandit/Thompson cohort fields** (`bandit_algorithm`, `thompson_mu_prior`, etc.) — `.F.4d` Thread B landed these in `FOREACH_PER_CORE_CFG_FIELD`; `.B` only adds STAMP_BOUND_CFG_DERIVED metadata bit; source-row infrastructure is settled.
- **Soft-risk degradation cohort** (`risk_*` 4 fields) — same shape; bit-add only.
- **β4 cohort gate dispatch table** (`MemHeaders/CfgDriftGate.hpp`) — well-formed per H20 Pattern 1; FOREACH_REGISTRY enrollment correct; branchless table dispatch sound.
- **Winsor cfg parse-time validation** (Step 10) — moves compound predicate from emit-time to parse-time; standard pattern; no parity surface impact (parse-time reject is operator-visible).
- **FOREACH_ML_CFG_FLAG 5→6 sig migration** (Step 2) — mechanical X-macro extension; no parity impact.

---

## Auto-write to PARITY_ISSUES.md (next available ID = PARITY-026)

Pending operator review. Recommend opening:

- **PARITY-026** — `.F.4d.1.B` plan body undercount of FOREACH_STAMP_BOUND_CFG production consumers (HIGH-1)
- **PARITY-027** — STAMP_CFG_AUTOPOPULATE production-caller field-population reopen risk at `.B` legacy empty-out (HIGH-2; sister to PARITY-020 closed)
- **PARITY-028** — Bitmap source-row emit shape needs explicit DriftGateKind-sister dispatch in derived-filter walker (HIGH-3)
- **PARITY-029** — `.B` ships before v5.14 byte-equivalence fixture (`.D`); minimal canary recommended (MED-3)

Per CLAUDE.local.md auto-write contract, write these to `DOCS/PARITY_ISSUES.md` if `.B` plan body is updated to address but ships with residual gaps; OR write as FIXED if `.B` v1.3 closes all four.

---

**End of report.** Verdict YELLOW pending triage of HIGH-1..HIGH-5 + MED-2/MED-3/MED-4 at `.B` update step. The β4 dispatch table + sidecar override pattern are well-formed; the parity risks are mostly at the legacy-consumer-migration surface (which the plan underestimates by ~5 sites) and the emit-shape distinction (synthetic vs production). None are blocking for the *direction* of `.B`; all are addressable with mechanical fixes at update.
