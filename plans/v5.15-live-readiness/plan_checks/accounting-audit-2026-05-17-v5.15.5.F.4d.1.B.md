# /accounting-audit findings — 2026-05-17 v5.15.5.F.4d.1.B (wire-format + HMAC chain)

**Scope:** `.B` plan body + sidecar — 24-row STAMP_BOUND_CFG cohort migration + FOREACH_ML_CFG_FLAG 5→6 sig + `tt::cfg_emit_synthetic_field<T>` + β4 FOREACH_DRIFT_GATE + Winsor parse-time validation + CFG_DRIFT_AUTOPOPULATE + 12+ consumer migration sites.
**Engine HEAD:** `39b9947` (`.A` shipped LOCALLY; not yet pushed).

## Summary

- **CRITICAL:** 2
- **HIGH:** 4
- **MEDIUM:** 3
- **LOW:** 2

**Top-line verdict: RED.** Two CRITICAL hazards that would silently break the production HMAC chain at `.B` ship close. Both are gaps between the plan's enumerated consumer migration sites and the actual production wire-format emit path. Triage REQUIRED before tagging `pre-v5.15.5.F.4d.1.B`.

## Findings

### [CRITICAL-1] Production HMAC canonical body emit site NOT enumerated in `.B` consumer migrations (`ML_Headers/ModelInference.hpp:1782-1789` + `:1396-1402`)
- **Severity:** CRITICAL
- **Category:** 7 (Backtest ↔ live accounting parity — wire format), 3 (cross-path consistency)
- **Class:** Class 18 mirror — incomplete migration would leave production emit reading from emptied registry
- **Details:** `.B` Step 12 empties `FOREACH_STAMP_BOUND_CFG(X)`. Plan body § Item 9 enumerates THREE active consumer sites (`CoreModelZoo.hpp:225-247` drift loop / `StampHelper.hpp:150` populate comment / `ConfidenceScore.hpp:729` COUNT). It does NOT enumerate the PRODUCTION HMAC-signed canonical body emit at `ModelInference.hpp:1782-1789` (`stamp_write_for_model`) or the PARSER X-macro walk at `ModelInference.hpp:1396-1402` (`verify_model_stamp`). Plus the ModelStampResult + StampInferenceCfgInputs struct-gen walks at `ModelInference.hpp:1196-1200` + `:1638-1644`. Emptying `FOREACH_STAMP_BOUND_CFG` at Step 12 silently empties the production wire-format emit → every new stamp written would lose all 24 cohort fields → load-time drift checks would fire spuriously on every model → operator-visible HMAC parity failure if model trained pre-`.B` vs loaded post-`.B`.
- **Recommended fix:** Plan body § Item 9 + sidecar § Step 9 MUST add 4 sites: (a) struct-gen walks at `ModelInference.hpp:1196-1200` + `:1638-1644` (replace with `FOREACH_CFG_FIELD` walk filtered on `STAMP_BOUND_CFG_DERIVED`; OR keep struct-gen sourcing legacy registry until `.F.4f` umbrella close), (b) parser walk at `:1396-1402` (migrate to walker), (c) emit walk at `:1782-1789` (CRITICAL — this is the wire-format byte producer; must use framework walker with EXACT same field ORDER + format strings + ternary normalization). Sequencing: production emit migration MUST land BEFORE Step 12 empties the legacy registry, not after. Mid-flight tag between is mandatory.
- **DESIGN_SPEC:** `wire-format-byte-preservation-discipline.md` § Layer 5b; `autopopulate-pattern-for-production-caller-class.md`

### [CRITICAL-2] Winsor parse-time validation REJECTS DEFAULT cfg (`.B` Step 10 + sidecar § Step 10)
- **Severity:** CRITICAL
- **Category:** 4 (H4 / FPN edge case), 1 (cfg-parse robustness)
- **Class:** N/A (new validation logic with off-by-one in predicate)
- **Details:** `.B` plan body Step 10 + sidecar § Step 10 propose: `if (FPN_ToDouble(cfg.winsor_pct_low) <= 0.0 || FPN_ToDouble(cfg.winsor_pct_high) >= 1.0 || ...) reject`. Source row at `CfgFieldRegistry.hpp:569` defines `winsor_pct_low` with `DBL(0.005, 0.0, 0.5)` — `payload_init.lo = 0.0` is the LOWER CLAMP BOUND of the field, valid per cfg-scope-discipline. `cfg.winsor_pct_low` MAY legitimately parse as `0.0` (e.g., user sets `winsor_pct_low=0` to disable lower clip) → `0.0 <= 0.0` is TRUE → parse REJECTED. Similarly `winsor_pct_high` clamp upper bound at `CfgFieldRegistry.hpp:572` is `1.0` → `1.0 >= 1.0` rejected. Existing emit-time predicate at `StampBoundCfgRegistry.hpp:137-141` uses `> 0.0 && < 1.0` for EMIT GATING (skip emit when invalid), NOT for cfg rejection. Q3.G semantic shift (moving from emit-time to parse-time) MUST preserve the emit-gate semantics: invalid bounds SKIP emit (stamp lacks the field; legacy back-compat); they do NOT reject the entire cfg. **Reformulation:** either (a) bounds become parse-warn + emit-skip (low <= 0 OR high >= 1 OR low >= high → WARN + leave field, do NOT emit to stamp), OR (b) ADJUST source row clamp bounds so 0.0 + 1.0 are inadmissible at parse layer (e.g., `DBL(0.005, 1e-9, 0.5)` + `DBL(0.995, 0.5, 1.0 - 1e-9)`) and CHANGE inequality to `<`/`>`. Plan body conflates "valid for emit" with "valid for cfg" — these are different invariants per Surface G discipline.
- **Recommended fix:** Re-spec Step 10. Option (a) preferred — preserves Surface G legacy back-compat; parse accepts, emit gates. Drift-check `gate_when` for Winsor cohort then needs to retain compound predicate OR rely on `has_winsor_pct_low` being unset for invalid configs. Add explicit test: cfg with `winsor_pct_low=0` accepted at parse + no `has_winsor_pct_low` set + drift-check skips + stamp loadable without winsor fields. Charter 12 "moves compound predicate from emit-time to cfg parse boundary" must NOT mean "rejects cfg at boundary". This is the kind of silent-correctness hazard that breaks paper-test parity with no obvious error path.
- **DESIGN_SPEC:** `cfg-flag-eligibility-criteria.md`; `wire-format-byte-preservation-discipline.md` § Surface G

### [HIGH-1] Canonical body field order WILL CHANGE under framework walker (`.B` § Item 3 + § Step 12)
- **Severity:** HIGH
- **Category:** 7 (Backtest ↔ live accounting parity), wire-format byte preservation
- **Class:** Class 18 + H9 wire-format
- **Details:** Production canonical body order at `ModelInference.hpp:1782-1789` is declaration order in `FOREACH_STAMP_BOUND_CFG` — Ridge cohort (5 fields) → Composite (5) → Winsor (2) → Exit_blender_mode (1) → Soft-risk (4) → ml_buy_threshold (1) → gap_acceptable_threshold (1) → Bandit/Thompson (5) → trading_mode (1). New framework walker emits per-core first (`g_per_core_cfg_stamp_bound_cfg_derived_mask`) then global (`g_global_cfg_stamp_bound_cfg_derived_mask`) — order is FIELD_IDX order WITHIN each scope, which depends on declaration position in `FOREACH_PER_CORE_CFG_FIELD` + `FOREACH_GLOBAL_CFG_FIELD`. Per `.B` Item 3, Ridge + Composite + Soft-risk + Bandit/Thompson live per-core; Winsor + ml_buy_threshold + gap_acceptable_threshold + trading_mode live global. NEW canonical order will be per-core fields (5+5+4+5=19) followed by global fields (2+1+1+1=5) → DIFFERENT byte ordering than legacy → HMAC chain BREAKS for any stamp written post-`.B` if a verifier expects v5.14/v5.15.x pre-`.B` order. The `.A` postmortem notes "per-core first, then global (canonical body order)" — but legacy production order is REGISTRY-DECLARATION order, not per-core-vs-global order. They are NOT the same.
- **Recommended fix:** Two paths: (a) ACCEPT byte-order change but stage v5.14 fixture validation at `.D` BEFORE the migration ships (move `.D` fixture work forward OR include in `.B` ship close) + bump stamp_format_version + document drift; (b) REORDER `FOREACH_PER_CORE_CFG_FIELD` and `FOREACH_GLOBAL_CFG_FIELD` source rows OR build framework walker to walk `FOREACH_STAMP_BOUND_CFG` declaration-order until `.D` fixture lands. Path (a) is honest; Path (b) preserves legacy bytes. Plan body claims "Wire format byte-for-byte preserved" (sidecar § Step 4 + plan body H9 row "PRESERVED + EXERCISED") — that claim is FALSE under current framework walker without remediation. Either accept the break (with version bump) or re-add explicit declaration-order preservation to the walker (could enrich `FOREACH_METADATA_BIT` with an ORDER override or add a sidecar position-tag). Operator triage required.
- **DESIGN_SPEC:** `wire-format-byte-preservation-discipline.md` § Layer 5b; H9 invariant

### [HIGH-2] `tt::cfg_emit_synthetic_field<T>` not used in production; sidecar emit format ambiguous (sidecar § Step 1)
- **Severity:** HIGH
- **Category:** 7 (parity), 4 (FPN<F>)
- **Class:** N/A
- **Details:** Sidecar § Step 1 documents `tt::cfg_emit_synthetic_field<T>` with synthetic values `42 + idx`, ternary `(idx & 1u) ? 1 : 0` for bool, `%.17g` for FPN/double. Plan body § Step 1 says this enables "synthetic populate fn in framework's WIRE_FORMAT macro to emit per-type deterministic values" — i.e., for INVARIANT TESTS, not production emit. But `StampBoundDerivedFilter.hpp` is documented as the canonical consumer + currently emits `"%s=stub\n"` placeholder; `.B` Step 1 description says "tt::cfg_emit_synthetic_field<T>` activates real per-type emit". If `StampBoundDerivedFilter.hpp` REPLACES production emit at Step 12 (legacy registry empty-out), then synthetic values `42 + idx` would be written to actual stamps in production — accounting-critical fail. If `StampBoundDerivedFilter.hpp` is test-only and production emit migrates to a SEPARATE walker reading real cfg values, then plan body needs to specify what that separate walker looks like. The sidecar code sample at lines 56-82 ONLY shows synthetic emit — no real-cfg-read variant.
- **Recommended fix:** Clarify in `.B` plan body: production canonical body emit walker (replacing `ModelInference.hpp:1782-1789`) reads REAL cfg values via `tt::cfg_get_field<T>(d, cfg)` + per-type `%.17g`/`%d` snprintf, NOT synthetic. `tt::cfg_emit_synthetic_field<T>` stays test-helper only. `StampBoundDerivedFilter.hpp` needs a SECOND emit fn (real-cfg variant) OR sidecar needs explicit "this is test scaffolding; production emit lives at <X>" note. Without this distinction, Step 12 legacy empty-out leaves production wire format reading the wrong path.
- **DESIGN_SPEC:** `metadata-bit-driven-derived-filter-framework.md` v1.2; H9

### [HIGH-3] `tt::cfg_emit_synthetic_field<T>` FPN<F> branch loses precision via `FPN_ToDouble` round-trip (sidecar § Step 1)
- **Severity:** HIGH (downgrade to MED if test-only — see HIGH-2)
- **Category:** 4 (lossy FPN_ToDouble), 5 (H4)
- **Class:** N/A
- **Details:** Sidecar § Step 1 lines 58-60: `FPN_ToDouble(T::from_double(42.0 + (double)idx))`. `FPN<F=64>` has 64 fractional bits — far more precision than IEEE-754 double (53 bits mantissa). `42.0 + idx` round-trips fine for small integer-ish values, but if future synthetic seeds become non-integer (e.g., `42.0 + 0.1 * idx`), `from_double(42.1)` → `ToDouble` → `42.0999999999...` introduces non-determinism risk for invariant tests that compare bytewise across rebuilds. Format string `%.17g` recovers ~17 digits; for the current `42 + idx` integer test seed the round-trip is exact, BUT this is brittle to future changes. Plus the function uses double-precision arithmetic (`42.0 + (double)idx`) for what should be a deterministic discrete index → H4 spirit-violation (display-only OK but intermediates are double).
- **Recommended fix:** For FPN<F> synthetic seed, use a FPN<F>-native expression: `FPN<F>::from_int(42 + (int)idx)` (if available) OR `FPN<F>(42 + idx)` constructor; emit via `tt::FPN_format_g17(buf, cap, value)` helper if one exists. Avoid the `from_double(42.0 + idx)` chain. Mark in code comment that synthetic seed must round-trip lossless for invariant test stability. If `tt::cfg_emit_synthetic_field<T>` is test-only, lower to MED. Either way, sidecar code sample should NOT canonicalize the `FPN_ToDouble`-based shape.
- **DESIGN_SPEC:** H4; `type-trait-dispatch-via-tt-namespace.md`

### [HIGH-4] Class 27 latent surface — `bandit_blend_ratio` POST_CFG entry DELETION + drift-check framework path (`.B` Step 6 + Step 7)
- **Severity:** HIGH
- **Category:** 1 (Class 27 scalar cfg-mirror), 6 (PortfolioController vs OMS consistency)
- **Class:** Class 27 candidate sibling
- **Details:** `.B` Step 6 deletes manual POST_CFG entry `inference_cfg_bandit_blend_ratio` at `StampBoundModelConstRegistry.hpp:295-297`. The framework "auto-generates equivalent from STAMP_BOUND_CFG_DERIVED bit on source row" (sidecar § Step 6 line 215). The auto-generation produces an `inference_cfg_<name>` mirror in `ModelStampResult` populated from `cfg.<name>` at training time + drift-checked at load. This IS the canonical Class 27 anti-shape if the bandit blend ratio is read elsewhere (OMS, ConfidenceScorer, ThompsonBandit state) by routing through `cfg.bandit_blend_ratio` directly instead of pre-resolving onto the Order/Position object. Plan body does NOT enumerate downstream readers; `/accounting-audit` cannot verify safety without the sweep. Plus `bandit_blend_ratio` is single-core scalar today; if `.F.5` migrates it per-core (originally planned, now absorbed per `.F.4d` Decision 15), reading global `cfg.bandit_blend_ratio` would flatten per-core distinction — exact Class 27 anti-shape.
- **Recommended fix:** `.B` Step 6 should include a Class-27 grep sweep for `cfg.bandit_blend_ratio` reads outside the stamp emit/drift-check paths. If reads exist on subsystem state (OMS / ConfidenceScorer / Order), surface as Class 27 retrofit candidate OR confirm pre-resolution binding. Reference `/accounting-audit` Category 1 + `decision-time-data-binding-pattern.md`. Mitigation if found: pre-resolve onto in-flight object at decision time; or document exemption in `MANUAL_FIELDS_INVENTORY.md` Section C. Sister rationale: 4 retroactive `.A.7` cohort migrations (Step 7) face the same question for `ml_tp_pct`, `ml_sl_pct`, `barrier_blend_mode`, `per_horizon_barrier_blend`.
- **DESIGN_SPEC:** `decision-time-data-binding-pattern.md`; RECURRING_BUG_PATTERNS Class 27

### [MED-1] `.B` cfg-side reads at drift-check time bypass per-core resolution (plan body Step 11 `gate_default<F>` + cohort gates)
- **Severity:** MEDIUM
- **Category:** 2 (per-core indexing), 9 (`static const` hazards — N/A but adjacent)
- **Class:** Class 29 candidate (silent zero from missing pre-resolution) — but slow-path, not hot-path
- **Details:** β4 cohort gate fns (`.B` plan body Step 11 + sidecar § Step 8b) read `cfg->ml_cfg_flags`, `cfg->risk_degradation_curve` directly from a single `ControllerConfig<F>*`. Drift check fires at model load time per `CoreModelZoo.hpp:228`. `ml_cfg_flags` lives in global cfg (single scalar at controller level) — safe single-source. `risk_degradation_curve` per `CfgFieldRegistry.hpp` lives where? If per-core (FOREACH_PER_CORE_CFG_FIELD), the drift-check gate reads core-0's value uniformly — silently flattens per-core distinction at the gate level. Drift check happens at boot per-core (CoreModelZoo per-core model load) so reading from per-core cfg pointer is correct AS LONG AS the cfg* passed in is the per-core cfg, not global. Plan body sidecar § Step 8b line 268 declares `DriftCtx<F>` holding `const ControllerConfig<F>* cfg` — needs explicit assertion that this is the per-core cfg at the call site. Currently the `verify_model_stamp` signature takes a non-per-core cfg pointer — needs verification.
- **Recommended fix:** Audit the cfg* passed to `CFG_DRIFT_AUTOPOPULATE` at each consumer site. If global cfg (single), per-core cohort fields (risk_degradation_curve, bandit/thompson) drift-check uniformly — silent per-core flatten. Fix: pass `&cfg.cores[c]` per-core cfg pointer at consumer sites + adjust gate fn signatures. Alternative: gate fns parameterize on core_id and read `cfg.cores[core_id].<field>`. Test: artificially set `cfg.cores[0].risk_degradation_curve=0`, `cfg.cores[1].risk_degradation_curve=1`, load model trained with curve=1 on core 0 → expect drift check to skip (curve=0 disables gate) NOT fire spuriously.
- **DESIGN_SPEC:** `cfg-scope-discipline.md`; CLAUDE.md item 31 framework discipline

### [MED-2] Ternary normalization deferred to bitmap walker; production emit precedent uses inline ternary (`.B` § Step 3)
- **Severity:** MEDIUM
- **Category:** 7 (parity), wire-format
- **Class:** H9 byte-equivalence
- **Details:** Plan body § Step 3 bitmap walker uses `int value = BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_##name) ? 1 : 0;`. Legacy production emit at `StampBoundCfgRegistry.hpp:107-111` uses same `(BITMAP_IS_SET(...) ? 1 : 0)` ternary. Wire bytes are `"<name>=0\n"` or `"<name>=1\n"` either way → byte-equivalent. GOOD. But verify the test at `controller_test.cpp` round-trip for ridge_within_horizon: stamp written under framework path + read under legacy parser path must produce identical bytes. Step 3 build verify says "invariants I1+I4 verify per-bit presence" — does I1 verify exact byte sequence? `.A` postmortem says I1 is line count, I3 is no-comma-decimals — neither verifies exact byte-for-byte. Need an invariant or test that explicitly compares framework-emitted bytes against legacy-emitted bytes for the same cfg.
- **Recommended fix:** Add Layer 4 byte-comparison test at `.B` Step 13 (don't defer to `.D`): construct ControllerConfig with all 24 cohort fields set; emit canonical body via legacy walker + framework walker side-by-side; `memcmp` must match (modulo field-order question in HIGH-1). This is the fundamental wire-format-byte-preservation test the migration needs. Cheaper at `.B` than at `.D` (smaller diff, easier debug).
- **DESIGN_SPEC:** `wire-format-byte-preservation-discipline.md` § Layer 4

### [MED-3] `.B` Step 12 legacy registry empty-out leaves `STAMP_CFG_AUTOPOPULATE` macro source-empty (`.B` § Step 12 + StampBoundCfgRegistry.hpp:226-232)
- **Severity:** MEDIUM
- **Category:** 1 (Class 27/18 latent), training pipeline
- **Class:** Class 14 (stale macro consumer)
- **Details:** `STAMP_CFG_AUTOPOPULATE` at `StampBoundCfgRegistry.hpp:226-232` walks `FOREACH_STAMP_BOUND_CFG(STAMP_CFG_AUTOPOPULATE_ONE)`. Used at `StampHelper.hpp:156` to populate the `StampInferenceCfgInputs` from cfg at training time. If `FOREACH_STAMP_BOUND_CFG(X)` becomes empty at Step 12, `STAMP_CFG_AUTOPOPULATE(inf, cfg)` becomes a no-op → `inf` stays zero-initialized → emit writes legacy declaration-order walk with all has_*=0 → stamp body has NO cohort fields → all 24 cohort fields LOST from stamps written post-`.B`. Same issue as CRITICAL-1 sister: production training emit path silently empties. Plan body assumes `.B` Step 9 migrates `StampHelper.hpp:150` populate per the comment-text-update list (~8 sites; "non-functional"). The comment IS non-functional — the macro call `STAMP_CFG_AUTOPOPULATE(inf, cfg)` at line 156 is the FUNCTIONAL consumer + needs migration to a framework-walker variant that populates real cfg values, not synthetic.
- **Recommended fix:** Add explicit Step 9 site: `StampHelper.hpp:156` `STAMP_CFG_AUTOPOPULATE(inf, cfg)` call. Either (a) re-define `STAMP_CFG_AUTOPOPULATE` macro to walk the framework's derived filter via `CFG_FIELD_FOR_EACH_SET_BIT` + populate `inf.<field>` from real cfg values, OR (b) replace the call with a new `CFG_DERIVED_AUTOPOPULATE(inf, cfg)` macro that does the framework walk. Keep populate semantics: per cfg field with STAMP_BOUND_CFG_DERIVED bit, evaluate the cohort gate_when predicate, when TRUE set `inf.has_<field>=1` + `inf.<field>=(type)<get_cfg_expr>`. Note: get_cfg_expr varies per field (FPN_ToDouble for FPN<F> sources, BITMAP_IS_SET for bitmap-source, direct read for int). The `tt::cfg_get_field<T>` dispatch from CLAUDE.md item 23 handles this if extended to cover BITMAP_BIT source.
- **DESIGN_SPEC:** `autopopulate-pattern-for-production-caller-class.md`; H13 (`tt::` dispatch)

### [LOW-1] `wf_mean_val=%g` non-cfg metadata uses lossy `%g` not `%.17g` (`ModelInference.hpp:1728`)
- **Severity:** LOW (pre-existing, not introduced by `.B`)
- **Category:** 5 (lossy FPN_ToDouble); 7 (parity)
- **Details:** Pre-existing canonical body emit at `ModelInference.hpp:1724-1733` uses `%g` (6-sig-fig default) for `wf_mean_val`, `held_out_metric`, `gap_threshold` — these are training-time scalars passed in as double. `%.6f` for gap. `%.17g` would be lossless. Pre-`.B` so out of `.B` scope; flag for sister cleanup at `.F.4f` Phase 7.
- **Recommended fix:** Defer to `.F.4f` cleanup ship Phase 7 OR open TECH_DEBT entry. Risk: stamp body produced under different rounding policy compared to header values. Currently bytewise-deterministic per-process (single emit fn) but cross-machine reproducibility weakened.
- **DESIGN_SPEC:** N/A; H9 spirit

### [LOW-2] `wf_mean_val` + `held_out_metric` are double in stamp; backtest accounting parity untested (`StampWriteResult` / `StampInferenceCfgInputs` interface)
- **Severity:** LOW
- **Category:** 4 (H4 — display-only, not accounting)
- **Details:** Training-time scalars passed to stamp emit are double, not FPN<F>. These are statistics over a training window (Sharpe / IC / etc.) — display-only per H4 (not used in accounting calculation). Acceptable per `DESIGN_PHILOSOPHY.md` § 3 H4 row. Flagging only because `.B` reaffirms this surface via emit changes.
- **Recommended fix:** None — display-only data flow. Document in `MANUAL_FIELDS_INVENTORY.md` Section C if not already present.

## Class 27/29 latent surfaces flagged

- **Class 27 candidate:** `bandit_blend_ratio` POST_CFG deletion (HIGH-4). Sister rationale applies to `ml_tp_pct`, `ml_sl_pct`, `barrier_blend_mode`, `per_horizon_barrier_blend` (`.A.7` retroactive cohort, Step 7). Plan body does NOT enumerate downstream readers — needs sweep before ship.
- **Class 29 candidate:** Drift-check cohort gate fns reading per-core fields via global cfg* (MED-1). Needs cfg-pointer-scope verification at consumer migration sites.
- **No Class 27 fn-local static caches** introduced by `.B` (verified — `tt::cfg_emit_synthetic_field<T>` is a function template, no statics).

## Backtest ↔ live parity impact

- `.B` does NOT touch `Backtest_Run` or `BacktestSharded_Run` direct surfaces.
- `.B` DOES touch the stamp emit path, which affects training-time stamp produced by backtest runs. If backtest training emits stamps with NEW canonical order (HIGH-1) + live engine reads them with NEW parser order, parity is preserved within the post-`.B` cohort but BROKEN across the `.B` boundary. v5.14 fixture at `.D` would catch this — but `.D` is two ships away. **Recommendation:** pull v5.14 fixture regression test forward to `.B` Step 13 OR commit to byte-order-changes-OK with stamp_format_version bump.

## Triage recommendations

1. **CRITICAL-1 + CRITICAL-2 must block coding** until plan body updated. CRITICAL-1 is a 4-site consumer enumeration gap + sequencing fix (Step 12 must follow production emit migration). CRITICAL-2 is a one-line predicate sharpening — choose Option (a) preserve emit-gate semantics.
2. **HIGH-1 (canonical body order)** requires explicit operator decision: accept order change + version bump, OR preserve declaration order via walker enrichment, OR reorder source rows. Plan body's "byte-for-byte preserved" claim is currently false.
3. **HIGH-2 + HIGH-3** are sidecar clarification + FPN spelling — mechanical fixes.
4. **HIGH-4 + MED-1 + MED-3** are Class 27/29 sweep work — should land at `.B` Step 13 explicit grep + test additions, not deferred.
5. **MED-2 (Layer 4 byte-comparison test)** is high-value-for-effort — pull into `.B` even though plan body defers to `.D`.

## Verdict: RED

`.B` plan body v1.2 has 2 CRITICAL hazards that would silently break the production HMAC chain at ship close. Triage REQUIRED before tagging `pre-v5.15.5.F.4d.1.B`. Recommend Path γ+ v3 update to `.B` plan body: enumerate all 4 missing wire-format consumer sites + reformulate Winsor predicate + decide canonical body order question + pull v5.14 fixture forward + add Class 27 sweep step. Estimated additional `.B` planning effort: ~2-3h focused.

## Cross-references

- `wire-format-byte-preservation-discipline.md` § Layer 2 + § Layer 4 + § Layer 5b + § Surface G
- `autopopulate-pattern-for-production-caller-class.md`
- `decision-time-data-binding-pattern.md`
- `cfg-scope-discipline.md`
- `cfg-flag-eligibility-criteria.md`
- `metadata-bit-driven-derived-filter-framework.md` v1.2
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 14 + Class 18 + Class 27 + Class 29
- `CLAUDE.md` H4 + H9 + H13 + invariants table
- HEAD verified anchors: `ML_Headers/ModelInference.hpp:1196-1200`, `:1396-1402`, `:1638-1644`, `:1782-1789`; `ML_Headers/StampBoundCfgRegistry.hpp:99-179`, `:226-232`; `ML_Headers/StampHelper.hpp:156`; `CoreFrameworks/CfgFieldRegistry.hpp:569+572`; `CoreFrameworks/StampBoundDerivedFilter.hpp:40-76`

**End of audit.**
