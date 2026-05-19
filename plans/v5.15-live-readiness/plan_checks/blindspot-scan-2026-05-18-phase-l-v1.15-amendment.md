# /blindspot-scan report — Phase L (v1.15 RESTRUCTURED amendment) — 2026-05-18

**Plan:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md`
**Scope:** Phase L (Decision G + Step 1.6.8') v1.15 RE-SYNTHESIS — framework-driven C++ CLI binary `tools/stamp_model_cli.cpp` with **X-macro auto-gen CLI flag table + value-receiver struct + parse dispatch via `tt::cfg_parse_field` + extensibility test pattern + --help auto-gen + exit code parity + kebab→snake deprecation aliases**
**Predecessor audit:** `blindspot-scan-2026-05-18-phase-l-amendment.md` (v1.14 scope; YELLOW; 1 CRIT + 1 LOAD-BEARING-LOUD + 1 GUARDED — all ADDRESSED in v1.15)
**Verdict:** **YELLOW-with-amendments** — 1 SILENT-RISK CRITICAL (B13 cross-walker uniqueness in longopts[]) + 1 SILENT-RISK (B11 plan-body sketch contradicts spec) + 1 SILENT-RISK (B6 `synthetic_value_for_field<T>` STORAGE_T coverage) + 1 SILENT-RISK (B8 X_APPLY_CFG sketch ignores NO_FLAT_FIELD bit) + 1 LOAD-BEARING-LOUD (B11 file-scope vs template-context resolution claim already in spec but NOT applied to plan body sketch)
**Engine HEAD:** `3d27512` (WIP-checkpoint 6)
**Fires after:** Batch 1 + Batch 2 + v1.14 SHAPE + v1.14 blindspot-scan returned GREEN/YELLOW-with-amendments — all those amendments ABSORBED at v1.15 (extends Phase L scope from wire-emit-only to wire-emit + CLI X-macro auto-gen + extensibility test)

---

## Summary

- Pillars fired: 12 (all)
- GUARDED-BY-BUILD: 4 (B5, B6, B7, B10)
- SILENT-RISK: 4 (B6 sub-finding, B8, B11 sketch contradiction, B13)
- LOAD-BEARING-LOUD: 1 (B11 alternative path)
- IRRELEVANT: 1 (B4)
- N-A: 2 (B3, B9)
- **NEW B-pillars (NOT in B1-B12 taxonomy at HEAD):** 1 (B13 cross-walker struct-field uniqueness applied to longopts[] context — already promoted to B13 in v1.0 of taxonomy doc per Step 1.6.3 codification; PHASE L surface NEW)

---

## Per-pillar verdicts

| Pillar | Verdict | Finding | Action |
|---|---|---|---|
| B1 — Type-change cascade | **N-A** (annotated by sister-site Step 1.6.3) | Phase L's CliReceived struct uses STORAGE_T direct from registry (auto-gen via X_GEN_CLI_FIELD) — inherits the same FPN<F>/int/uint8_t/uint32_t/uint64_t/uint16_t/double family that Step 1.6.3 owns. No NEW type-change surface at Phase L. | None |
| B2 — Field-name collision (within-walker) | **GUARDED-BY-BUILD** (verified clean) | Pairwise intersection of PER_CORE × GLOBAL × ML × GATE registries = empty set at HEAD (verified via comm); 4 master cfg registries have NO name collisions. CliReceived struct walks all 4 via X_GEN_CLI_FIELD/X_GEN_CLI_BITMAP without conflict. | None |
| B3 — Transitional state coexistence | **N-A** (annotated by plan) | Phase L doesn't introduce transitional struct growth. CliReceived is a NEW struct (no peak coexistence with legacy). Plan body L5 + TECH_DEBT-110 cover deprecation shim retention bound. | None |
| B4 — Surface G applicability | **IRRELEVANT** | Phase L's `has_<name>` semantic in CliReceived = "operator supplied this flag at command line". Different semantic from cfg-stamp-binding's `has_<name>` = "stamp body contained this key". Both intentional. Documented by sister context in spec at framework-driven-cli-binary-pattern.md:259-279. | None |
| B5 — Compile-time scaling | **GUARDED-BY-BUILD** (estimate annotated) | NEW v1.15 X-macro auto-gen: ~163 cfg-domain rows × ~3 walker sites (CliReceived field-gen + apply-to-cfg + parse-dispatch) + 65 model-const × 2 = ~559 walker expansions. Plus per-row `tt::cfg_parse_field<T>` instantiation for distinct T variants. Estimated +5-12s build time on top of v1.14's deep include chain. Same scale as `controller_test` baseline. ~30s total stamp_model_cli compile. Acceptable. | Annotate in plan body L3 |
| B6 — STORAGE_T variant coverage (tt::cfg_parse_field branches) | **GUARDED-BY-BUILD** | Verified: `tools/check_storage_t_coverage.py` PASS at HEAD; 7 STORAGE_T variants in tt:: family (FPN<F>, double, int, uint16_t, uint32_t, uint64_t, uint8_t). All cfg-derived consumers including L2's parse dispatch inherit coverage. | None |
| **B6 SUB-FINDING — `synthetic_value_for_field<T>` STORAGE_T coverage** | **SILENT-RISK** | NEW helper for L4 extensibility test (`cfg-derived-consumer-framework.md` v1.3 line 282-293). Spec body has `if constexpr (is_FPN_v<T>)`, `is_integral_v<T>`, `is_same_v<T, bool>` — **missing `is_array_v<T>` branch** (for char[N] post-`.F.4e` KIND_STRING) AND **missing `is_floating_point_v<T>` branch** (for raw `double` storage if any future cfg row uses it; currently 1 row at HEAD uses double in PER_CORE per check_storage_t_coverage.py output). At HEAD double DOES appear in PER_CORE registry — extensibility test would compile-fail at first double-typed flagged row. Acceptable in short-term (no STAMP_BOUND_CFG_DERIVED-flagged double rows at HEAD), but per `feedback_motivated_collaborator_for_caramel` discipline: add coverage NOW (the helper is being authored at L4; no cost to make complete). Per pillar B6 detection guard, this should have static_assert in else branch. Spec line 292 says "`/* extend per STORAGE_T set */`" — acknowledges the gap but doesn't close it. | **Plan body amendment L4 + spec amendment**: extend `synthetic_value_for_field<T>` to cover full 7-variant STORAGE_T family + static_assert(unreachable) in else branch. Closes B6 SUB-FINDING. |
| B7 — Include topology cycle | **GUARDED-BY-BUILD (LOAD-BEARING)** | Already addressed at v1.14 audit. v1.15 doesn't extend include surface — same chain via `ModelInference.hpp` + `CfgGateRegistry.hpp`. Deep but no cycle. Plan body L3 annotation recommended (carried from v1.14 finding). | (Carry annotation; closed) |
| **B8 — Type-sensitive consumer at CLI flag → cfg layer (X_APPLY_CFG sketch ignores NO_FLAT_FIELD)** | **SILENT-RISK** | Spec line 308-310 sketch: `if (args.has_##name) cfg.name = args.name;` for FOREACH_PER_CORE_CFG_FIELD. **At HEAD per-core rows with `NO_FLAT_FIELD` bit (e.g., `strategy` per CfgFieldRegistry.hpp:441) DON'T have a `cfg.<name>` scalar** — `ControllerConfig<F>` has no `strategy` field at file scope; the field lives at `cfg.cores[c].strategy` per H17 PerCoreCfg<F> auto-gen + parallel array `core_strategies[16]`. X_APPLY_CFG over FOREACH_PER_CORE_CFG_FIELD without `if constexpr (!((meta) & NO_FLAT_FIELD))` filter will fail to compile. Sister precedent at ControllerConfig.hpp:1447-1454 (`EMIT_PER_CORE_COPY` uses exactly this filter). | **Plan body amendment + spec amendment**: gate X_APPLY_CFG dispatch with `if constexpr (!((meta) & CfgFieldDescriptor::NO_FLAT_FIELD))` (sister to `EMIT_PER_CORE_COPY`). For NO_FLAT_FIELD rows in cfg-derived cohort (none at HEAD have STAMP_BOUND_CFG_DERIVED + NO_FLAT_FIELD overlap by inspection, but future rows might — make compile-time-safe). Closes B8 ahead-of-coding. |
| B9 — Audit claim → evidence chain | **N-A** (verified) | v1.15 amendment cites X-macro auto-gen feasibility — verified via spec body line 213-217: "emit ALL rows; filter at parse time via descriptor metadata bit. Avoids if-constexpr compile-time filter on static array initializers (C++ doesn't support)." Spec body has the verified resolution; plan body sketch (lines 871-878) doesn't propagate it (see B11 below). v1.15's "23 flags → 33 flags" claim verified at bash script grep (33 unique kebab-case flags). | None on claim chain |
| B10 — Struct layout drift (CliReceived padding) | **GUARDED-BY-BUILD** (cosmetic) | CliReceived is a NEW struct populated locally in main(); NOT byte-equivalence input. H12 inapplicable. Mixed-width fields (uint8_t has_*+STORAGE_T) have arbitrary padding; not memcmp'd, hashed, or wire-emitted. Cosmetic. | None |
| **B11 — Plan-body sketch contradicts spec resolution (file-scope filter)** | **SILENT-RISK (LOAD-BEARING)** | The v1.15 plan body's L2 sketch (line 871-878) describes the file-scope filter as: "Trick: emit `__VA_ARGS__` (empty) when filter fails. Or use a helper macro that takes meta + emits row OR nothing. Pattern in existing codebase at SLOT_FIELD_OPTIONAL etc. Concretely: token-paste FILTER_##(meta-test-result) → dispatch via Y3 to EMIT_ROW vs SKIP." But the underlying DESIGN_SPEC (`framework-driven-cli-binary-pattern.md` v1.1 line 213-217) RESOLVED this: **"emit ALL rows; filter at parse time via descriptor metadata bit. Avoids if-constexpr compile-time filter on static array initializers (C++ doesn't support)."** Plan body sketch describes a Y3 dispatch shape that DOESN'T match the spec's chosen approach. Coding from plan body sketch → coder might attempt FILTER_## token-paste (non-trivial, brittle); coding from spec → trivial (emit all; filter at strcmp dispatch time). | **Plan body amendment L2**: replace lines 871-878 sketch with the spec's resolved approach. Either (a) explicitly transclude spec line 213-217 + 216-218 (`X_GEN_LONGOPT_ALL_CFG` unfiltered emit) OR (b) point at spec § 2.5 + delete the contradicting Y3 sketch. **Closes B11.** |
| **B11 ALT — if-constexpr template context** | **GUARDED-BY-BUILD** | All `if constexpr` filter sites in cfg-derived consumer template fns ARE in template scope (per CfgGateRegistry.hpp lines 287-289 — `template <unsigned F, typename InfT>` enclosing). Phase L's `cli_args_dispatch` (spec line 285) is a non-template free function — but doesn't use `if constexpr` filter (uses runtime strcmp); compatible. `apply_cli_args_to_cfg/inf` SHOULD be template-parameterized over <unsigned F> for the FPN<F> branches inside `tt::cfg_*_field<T>` to compile cleanly (already the case in CfgGateRegistry sister fns). | Plan body amendment: spec apply_cli_args_to_cfg as `template <unsigned F> void apply_cli_args_to_cfg(const CliReceived& args, ControllerConfig<F>& cfg)`. Closes B11 ALT. |
| **B12 — Cross-registry row ordering (longopts[] order)** | **N-A** (getopt_long is name-keyed) | getopt_long matches by `option.name` string, NOT by array position. Order in longopts[] is irrelevant for parse correctness. For --help auto-gen ordering, master registry walk order = display order; consistent with engine.cfg.example auto-gen sister at HEAD. Acceptable. | None |
| **B13 — Cross-walker struct-field uniqueness applied to longopts[] (NEW Phase L surface)** | **SILENT-RISK CRITICAL** | At HEAD, `xgb_min_child_weight` + `xgb_seed` + `xgb_train_nthread` appear in BOTH `FOREACH_GLOBAL_CFG_FIELD` AND `FOREACH_STAMP_BOUND_MODEL_CONST` (verified via comm — 3-way overlap). Sister H18 EXCLUSION sidecar at `CfgGateRegistry.hpp:619-622` resolves struct-gen duplicate-member error via `#define name _stamp_result_excluded_<name>` redirect around `STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN()` (ModelInference.hpp:1225-1227 + :1668-1670). **Phase L's longopts[] X-macro auto-gen emits `{#name, required_argument, 0, 0}` from BOTH FOREACH_GLOBAL_CFG_FIELD AND FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG.** Three options for the 3 colliding rows: (a) **duplicate longopts entries** — getopt_long permits duplicates but matches first; operator-visible flag `--xgb_seed` would dispatch ambiguously between cfg-derived path and model-const path (BAD); (b) **EXCLUSION redirect applied to longopts[]** — same trick as struct-gen, but `#name` stringification would emit `"_stamp_result_excluded_xgb_seed"` as the flag string → operator-visible flag rename (`--_stamp_result_excluded_xgb_seed` instead of `--xgb_seed`; BAD for UX); (c) **emit only via MC walker, skip in cfg walker** — requires per-row override at GLOBAL X-macro to suppress 3 specific names. Sister H18 SIDECAR pattern applies but for SPECIFIC OVERRIDE (semantically distinct from struct-gen redirect). | **PRE-CODING BLOCKER amendment to spec + plan body L2**: explicitly call out 3-way collision; document resolution (recommend: option (c) — emit from MC walker, skip in cfg walker via sister SIDECAR pattern FOREACH_LONGOPT_DEDUP_OVERRIDE; OR alternative: emit from cfg walker, skip in MC walker — match whichever walker is canonical owner of the field's stamp-binding semantic). Decision-time data binding pattern says single source of truth — pick ONE walker. **Closes B13 CRITICAL.** |

---

## NEW B-pillar concerns evaluated (per audit prompt)

### #6 — Extensibility test runtime cost
**Verdict: GUARDED-BY-BUILD (acceptable scale).**
At HEAD with ~22 STAMP_BOUND_CFG_DERIVED-flagged rows × ~1ms per stamp emit/parse cycle in extensibility test = ~22ms test runtime. Scales linearly. At 100 rows = ~100ms; at 500 rows = ~500ms. CI tolerable up to ~5000 rows. Acceptable for foreseeable cohort growth. No action needed. Plan body L4 can annotate scaling concern; non-blocking.

### #7 — `synthetic_value_for_field<T>` coverage
**Verdict: SILENT-RISK (see B6 SUB-FINDING above).** Already enumerated.

### #8 — `--help` text byte size
**Verdict: GUARDED-BY-BUILD (acceptable scale).**
163 cfg-domain rows + 65 model-const rows = 228 flags × ~100 chars tooltip = ~23KB help text in worst case. Fits comfortably in stack/stdout buffer (printf to stderr handles in chunks). `fprintf(stderr, ...)` for help-text emit is unbounded by buffer size on POSIX. Acceptable. Plan body L2 can annotate the size estimate; non-blocking.

### #3 — Build time impact
**Verdict: GUARDED-BY-BUILD (already in plan body L3 deep-include note).**
`stamp_model_cli` translation unit pulls deep header chain via `ModelInference.hpp` → ~15-20 transitive headers. v1.14 estimate of +5-15s vs `compare_scalers` baseline holds for v1.15 (X-macro expansion is preprocessor work, not template-instantiation work — minimal additional time). Total scale ~30s; same as `controller_test`. Acceptable.

### #4 — longopts[] ordering vs HMAC chain
**Verdict: N-A (already addressed in v1.15 plan body).**
Phase L's wire emit goes through framework's `populate_stamp_cfg_from_derived` walker (master-registry order) — CLI binary calls framework directly per spec § 5.3, so HMAC chain is structurally identical to engine in-process emit. CLI never bypasses framework for wire emit (this IS Phase L's core structural-fix property). Confirmed at plan body :1208.

### #5 — Macro hoisting / X_GEN_LONGOPT_* naming convention
**Verdict: GUARDED-BY-BUILD (verified clean).**
Per-scope X_GEN_LONGOPT_* macros (X_GEN_LONGOPT_ALL_CFG / X_GEN_LONGOPT_BITMAP / X_GEN_LONGOPT_MC) have DIFFERENT signatures matching their target X-macro arity (13/6/9 cols). No name collisions with HEAD X-macros (verified). Naming convention is consistent with existing `_STAMP_RESULT_<SCOPE>` precedent at CfgGateRegistry.hpp:629-636.

---

## Punch-list (ordered by severity)

1. **(B13 SILENT-RISK CRITICAL)** Spec + Plan body amendment L2: document 3-way (xgb_min_child_weight + xgb_seed + xgb_train_nthread) collision between FOREACH_GLOBAL_CFG_FIELD and FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG at longopts[] auto-gen site. Pick deduplication mechanism: recommend **single-source-of-truth via SIDECAR EXCLUSION** — emit from MC walker (architectural-constant semantic), skip in cfg walker via sparse `FOREACH_LONGOPT_DEDUP_OVERRIDE(X)` sidecar listing the 3 colliding names + `#define name __longopt_skip_##name` redirect bracket. (~10 min plan body amendment; ~15 min coding.) **Closes B13.**

2. **(B11 SILENT-RISK LOAD-BEARING)** Plan body amendment L2: replace lines 871-878 muddled Y3-dispatch sketch with the spec's resolved approach. The spec body at `framework-driven-cli-binary-pattern.md` v1.1 line 213-217 explicitly states the resolution: "emit ALL rows; filter at parse time via descriptor metadata bit. Avoids if-constexpr compile-time filter on static array initializers (C++ doesn't support)." Plan body should DELETE the contradicting FILTER_## token-paste sketch + insert direct reference to spec § 2.5 OR transclude lines 216-218 (`X_GEN_LONGOPT_ALL_CFG` unfiltered emit). (~10 min plan body amendment.) **Closes B11.**

3. **(B8 SILENT-RISK)** Spec amendment + plan body amendment L2: extend `X_APPLY_CFG` sketch (spec line 308-312) with `if constexpr (!((meta) & CfgFieldDescriptor::NO_FLAT_FIELD))` filter, mirroring sister `EMIT_PER_CORE_COPY` at ControllerConfig.hpp:1447-1454. Without this, X_APPLY_CFG expansion over FOREACH_PER_CORE_CFG_FIELD will fail compile for `strategy` row (NO_FLAT_FIELD + MANUAL_PARSER). At HEAD no row overlaps NO_FLAT_FIELD ∩ STAMP_BOUND_CFG_DERIVED, but X_APPLY_CFG operates UNFILTERED over the registry — so the strategy row WILL be processed. (~5 min spec amendment; ~5 min plan body sync.) **Closes B8.**

4. **(B6 SUB-FINDING SILENT-RISK)** Spec amendment (cfg-derived-consumer-framework.md v1.3 line 282-293): extend `synthetic_value_for_field<T>` to cover full 7-variant STORAGE_T family per `tools/check_storage_t_coverage.py` output. Add branches for `std::is_floating_point_v<T>` (raw double; appears in PER_CORE at HEAD) and `std::is_array_v<T>` (char[N] forward-compat for `.F.4e`). Add `static_assert(unreachable, "extend synthetic_value_for_field<T>")` in else branch — same discipline as `tt::cfg_parse_field<T>` BARRIER 3. (~5 min spec amendment.) **Closes B6 SUB-FINDING.**

5. **(B11 ALT GUARDED-BY-BUILD strengthening)** Spec amendment: declare `apply_cli_args_to_cfg` + `apply_cli_args_to_inf` as `template <unsigned F>` so FPN<F> dispatch inside `tt::cfg_*_field<T>` instantiation is template-context-clean. Matches sister `cfg_derived::populate_inference_cfg_from_derived<F, InfT>` precedent. Already implicitly required for `cfg.name = args.name` where name has FPN<F> type, but plan body should spell out the template parameter explicitly. (~3 min spec amendment.) **Closes B11 ALT.**

---

## Recommended next move

**Option (X) — Audit-first plan body + spec amendments (RECOMMENDED).** Apply findings 1-5 to v1.15 plan body Phase L sub-steps L2 + L4 AND to `framework-driven-cli-binary-pattern.md` v1.1 + `cfg-derived-consumer-framework.md` v1.3 before any coding starts. Total effort: ~35-45 min plan body + spec amendment.

Option (Y) — Code with annotations (alternative). Implement CLI binary; surface remaining via compile failures (B8 NO_FLAT_FIELD + B6 STORAGE_T coverage compile-fail loudly; B11 muddled sketch leads to wasted exploration; B13 collision is the only SILENT one — could ship undetected if longopts[] duplicates pass smoke test). Breaks `feedback_plan_right_not_fast` discipline; B13 silently degrades operator UX. **REJECTED for B13 specifically.**

Option (Z) — Defer B13 to next ship. **REJECTED** per `feedback_no_defer_for_effort` — operator workflow continuity for XGBoost-trained models requires `--xgb_seed` etc. to work end-to-end at Phase L ship.

**Inflection check** (per `feedback_iteration_spiral_signals_audit_meta_gap`):
- This is the 2ND `/blindspot-scan` invocation against Phase L (1st was v1.14; v1.15 expanded scope significantly)
- 4 SILENT-RISK pillars surfaced (B13 + B11 + B8 + B6 sub-finding)
- 1 NEW PILLAR-PROMOTION: B13 already promoted to canonical taxonomy at v1.0 codification (Step 1.6.3 surface); v1.15 is 2ND canonical application at longopts[] surface. Confirms B13 generalizes beyond struct-gen.
- NEW B-pillars (B14+): 0 surfaced — taxonomy still covers all findings
- Iteration depth: 2 — recommendation: amend plan body + spec once with findings 1-5; re-fire only if amendment surfaces a new code-state concern

---

## Blocking gaps that MUST resolve before Phase L coding starts

1. **B13 longopts[] cross-walker collision** — explicit deduplication mechanism for 3 xgb_* names. **CRITICAL** because silent UX failure (operator-visible flag ambiguity OR flag rename).
2. **B11 plan body sketch contradicts spec resolution** — plan body amendment so coder doesn't waste cycles attempting FILTER_## token-paste from muddled sketch.

**Non-blocking but strongly recommended:**
- B8 NO_FLAT_FIELD filter in X_APPLY_CFG (compile-fail loudly but wastes rebuild cycle)
- B6 synthetic_value_for_field<T> coverage extension (compile-fail loudly at coding time but unnecessary if pre-fixed)
- B11 ALT template <unsigned F> on apply_cli_args (compile-fail loudly; sister context provides precedent)

---

## Per-finding cross-references

- **B13** — `comm -12 /tmp/mc_names.txt /tmp/global_names.txt` confirms 3-way overlap; sister H18 SIDECAR at `CfgGateRegistry.hpp:619-622`; struct-gen application at `ML_Headers/ModelInference.hpp:1225-1227 + :1668-1670`.
- **B11** — Plan body `subplans/2026-05-17-...-legacy-empty-out.md:871-878` (muddled Y3 sketch) vs spec `DESIGN_SPECS/framework-driven-cli-binary-pattern.md:213-217` (resolved approach).
- **B8** — Sister precedent `CoreFrameworks/ControllerConfig.hpp:1447-1454` (`EMIT_PER_CORE_COPY` uses `if constexpr (!((meta) & NO_FLAT_FIELD))`); NO_FLAT_FIELD row example `CoreFrameworks/CfgFieldRegistry.hpp:441` (strategy).
- **B6 SUB-FINDING** — Spec `cfg-derived-consumer-framework.md:282-293`; current 7-variant coverage verified via `tools/check_storage_t_coverage.py`.
- **B11 ALT** — Sister template context at `MemHeaders/CfgGateRegistry.hpp:287-289` (`template <unsigned F, typename InfT>`).

---

## Implementation-detail audits delta vs v1.14 fire (2026-05-18 earlier)

| Pillar | v1.14 verdict | v1.15 verdict | Delta |
|---|---|---|---|
| B1 | IRRELEVANT | N-A | Same surface; sister-site owns; no delta |
| B2 | IRRELEVANT | GUARDED-BY-BUILD | NEW v1.15 walks all 4 cfg-domain registries; verified clean (empty intersection) |
| B3 | N-A | N-A | Same |
| B4 | IRRELEVANT | IRRELEVANT | Same |
| B5 | GUARDED-BY-BUILD | GUARDED-BY-BUILD | +5-12s build time delta within margin |
| B6 | GUARDED-BY-BUILD | GUARDED-BY-BUILD **+ SUB-FINDING SILENT-RISK** | NEW v1.15: synthetic_value_for_field<T> needs full STORAGE_T coverage |
| B7 | GUARDED-BY-BUILD | GUARDED-BY-BUILD | Same depth; no NEW edges |
| B8 | SILENT-RISK CRIT (flag-set 23→33) — ADDRESSED | **SILENT-RISK NEW (NO_FLAT_FIELD filter)** | v1.14 finding closed by X-macro auto-gen (flags self-extend); v1.15 NEW finding at apply layer |
| B9 | N-A | N-A | Same |
| B10 | IRRELEVANT | GUARDED-BY-BUILD | Same |
| B11 | LOAD-BEARING (CMake 4-line) — ADDRESSED | **SILENT-RISK NEW (sketch contradicts spec)** | v1.14 finding closed; v1.15 NEW finding at plan body sketch coherence |
| B12 | N-A | N-A | Same (framework call inherits master order) |
| B13 | (taxonomy promoted at Step 1.6.3) | **SILENT-RISK CRITICAL NEW (longopts[] collision)** | NEW Phase L surface at v1.15 expanded scope |

**Net change v1.14 → v1.15:** 3 v1.14 amendments ADDRESSED (CLI flag completeness, CMake, build.sh). 4 NEW SILENT-RISK findings introduced by v1.15's expanded X-macro auto-gen scope. Of these, B13 is the only CRITICAL one (silent UX failure path); others are loud-compile-fail or sketch-coherence issues.

---

**Audit fired:** 2026-05-18 against engine HEAD `3d27512` (WIP-checkpoint 6); v1.15 plan body draft as of 2026-05-18 mid-pre-coding. Honors `consult-before-coding` — operator decides next move; this skill never auto-proceeds. Per `feedback_consult_on_audit_findings` + `feedback_audit_own_proposals_with_same_rigor` (4-pillar self-audit: cross-checked DESIGN_SPECS framework-driven-cli-binary-pattern.md + cfg-derived-consumer-framework.md + RECURRING_BUG_PATTERNS Classes 21/14/18/19 + sister H18 SIDECAR precedent + check_storage_t_coverage CI tool + operator-impact verified at bash flag enumeration + novel-alternative considered (longopts dedup via per-walker skip vs SIDECAR-OVERRIDE)).
