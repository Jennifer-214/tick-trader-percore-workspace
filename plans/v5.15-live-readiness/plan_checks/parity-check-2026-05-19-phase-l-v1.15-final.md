# /parity-check report — 2026-05-19 — Phase L v1.15 RE-FIRE (final)

**Scope:** Re-fire against v1.15 final state of plan body. Predecessor was v1.14; v1.15 substantially expanded Phase L scope (X-macro auto-gen CLI flag table + extensibility test pattern + DESIGN_SPEC v1.0→v1.1).

**Plan body:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.15 (1337 lines)
**Phase L spec:** `tick-trader-percore-workspace/DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md` v1.1 (Stage 2 DRAFT)
**Sister spec:** `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/cfg-derived-consumer-framework.md` v1.3 (Stage 3 ACTIVE)
**Wire-format spec:** `tick-trader-percore-workspace/DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` Layers 1-7
**Engine HEAD:** `73dedf3` (4 doc-system commits ahead of pre-coding anchor `3d27512`; source files untouched)
**Version pinned at HEAD:** `5.15.5.F.4d.1.B.2`

**Audit baseline:** prior `/parity-check-2026-05-18-phase-l-amendment.md` against v1.14 + `/blindspot-scan-2026-05-18-phase-l-v1.15-amendment.md` v1.15 amendment review.

---

## Verdict: YELLOW (1 MED + 4 LOW + 0 NEW CRITICAL/HIGH)

v1.15 closes the v1.14 audit punch-list comprehensively. The X-macro auto-gen scope at CLI INTERFACE LAYER + extensibility test pattern are SOUND structural additions; Decision F SOFT compat for the 15-key scope is correctly framed; B13 cross-walker collision resolution reuses the existing `FOREACH_STAMP_RESULT_FIELD_EXCLUSION` sidecar (verified at HEAD). Wire-format byte preservation under SOFT bump is correctly understood. No NEW CRITICAL or HIGH findings surfaced.

Residual findings are bookkeeping-class: stale line citation, two annotation gaps, version-mismatch annotation suggestion, and one observability nit. Coding can proceed if Caramel is OK accepting the bookkeeping at code time (operator triage).

---

## Findings by severity

### CRITICAL — none

### HIGH — none

### MEDIUM-1 — Stale `FOREACH_STAMP_RESULT_FIELD_EXCLUSION` line citation (B13 resolution)

**Cite (plan body line 865):** "reuse existing `FOREACH_STAMP_RESULT_FIELD_EXCLUSION` sidecar at `MemHeaders/CfgGateRegistry.hpp:512-515`"
**Cite (Phase L spec, NEW v1.1 B13 paragraph):** same `:512-515` cite

**Verified at HEAD (`MemHeaders/CfgGateRegistry.hpp:619-622`):**
```cpp
#define FOREACH_STAMP_RESULT_FIELD_EXCLUSION(X) \
    X(xgb_min_child_weight) \
    X(xgb_seed)             \
    X(xgb_train_nthread)
```

The sidecar exists with the 3 collision names; B13 resolution mechanism is sound. But the cited line range `:512-515` is ~107 lines off from actual `:619-622`. Same stale cite appears in TWO places (plan body line 865 + spec v1.1 § Step 2.5 B13 paragraph). Likely propagated from a session where a prior version had different line numbers.

**Impact:** documentation drift; coding-time grep will resolve correctly (full token name unique); minor risk of future mis-reading if cite is treated as ground truth.

**Recommended fix:** at L2 coding-time, update both cites to `:619-622` (or omit the specific line numbers and rely on the macro-name identifier which is stable). Sister: `feedback_categorical_triggers_over_hardcoded_refs` (this is exactly the hardcoded-ref-drift pattern).

**Severity rationale:** MEDIUM (not LOW) because the cite is referenced from two cross-linked locations (plan body + spec) — the duplication amplifies the drift surface. Trivial fix.

### LOW-1 — B13 longopts[] dispatch mechanism comparison is sound but Phase L spec has a typo branch label

**Cite (Phase L spec, NEW v1.1 § Step 2.5 immediately after the longopts[] sketch, lines ~395-410):** describes the `_LONGOPT_OVERRIDE_<name>` redirect bracket pattern; plan body lines 871-878 mirror.

**Verification:** Existing sister pattern at `MemHeaders/CfgGateRegistry.hpp:606-617` describes `_stamp_result_excluded_<name>` redirect-to-dead-field pattern at the struct-gen layer. The longopts[] proposal in Phase L is consistent (same sidecar; sister redirect bracket discipline). Wire emit byte equivalence at runtime is unaffected — both walkers reach the same set of names.

**One minor finding:** in plan body lines 871-878 the macro sketch uses `X_GEN_LONGOPT_ALL_CFG(...)` for the cfg walker — but the immediately-prior comment at line 870 says "Cfg walker (`X_GEN_LONGOPT_ALL_CFG`) wraps each row with `#define/#undef` redirect bracket". The example code below it doesn't actually show the redirect — it just shows the unsuffixed body, then 3 `_LONGOPT_OVERRIDE_*` empty redirect macros below. The Y3 dispatch hookup ("default body emits longopts entry") is documented in the trailing comment line 879 but not wired in the code sketch. At L2 coding-time, the code MUST actually wire the Y3 dispatch (per Phase L spec § B13 ¶6).

**Impact:** zero impact at coding time (the operator/coder reads the sketch as illustrative; spec body has the canonical pattern at § Step 2.5). Cosmetic in the plan body.

**Recommended fix:** at L2 coding-time, follow Phase L spec § Step 2.5 § B13 pattern body verbatim; plan body sketch is illustrative-not-canonical.

### LOW-2 — Row-ordering annotation at Step 1.6.4 covers v2-shape regression-lock but doesn't explicitly cover MC walker interleaving

**Cite (plan body lines 725-727 Step 1.6.4 amendment + lines 1807/1823/1837 in ModelInference.hpp):**

At HEAD canonical body shape is:
```
PRE_CFG → FOREACH_STAMP_BOUND_CFG → POST_CFG
(line 1807)     (line 1823)         (line 1837)
```

After Step 1.6.4 + Step 2:
```
PRE_CFG → cfg_derived::populate_stamp_cfg_from_derived(canonical+n, ...) → POST_CFG
```

The framework body at `CfgGateRegistry.hpp:342-406` walks `FOREACH_STAMP_BOUND_DERIVED_COHORT(X_STAMP_CFG_POPULATE)` which expands to `PER_CORE → GLOBAL → ML_CFG_FLAG → GATE_CFG_FLAG`.

Plan body Step 1.6.4 annotation (lines 725) covers v1↔v2 wire-key shape change AND row-ordering inside the cfg cohort. Implicitly correct: PRE_CFG (line 1807) → cfg cohort (replaces 1823) → POST_CFG (line 1837) preserves the PRE/POST sandwich. However the annotation doesn't EXPLICITLY call out that POST_CFG-emitted XGB names (xgb_min_child_weight, xgb_seed, xgb_train_nthread) emit AFTER cfg cohort while master-cfg-registry has same-named rows that DON'T emit (because B13 sidecar redirects them to noop at struct/walker layer, not at emit-walker layer in cfg_derived::populate_stamp_cfg_from_derived).

**Verification of the runtime behavior:** the cfg cohort walker filter `((meta) & STAMP_BOUND_CFG_DERIVED) != 0` — verify at coding time that `xgb_*` rows in master GLOBAL registry (verified at `CfgFieldRegistry.hpp:321-327`) do NOT have STAMP_BOUND_CFG_DERIVED bit set. If they DO, cfg walker WILL emit them → POST_CFG MC walker emits ALSO → duplicate wire key emit → Class 31 instance reborn.

```bash
$ rg -n "xgb_min_child_weight" /home/caramel/code/FoxML_Trader_v2/CoreFrameworks/CfgFieldRegistry.hpp
321:    X(int,                  KIND_INT,        xgb_min_child_weight,        "Min Child Weight",     "ML Hyperparams",  CfgFieldDescriptor::IS_BOOT_ONLY | CfgFieldDescriptor::WARN_ON_CLAMP, ...
324:    X(int,                  KIND_INT,        xgb_seed, ...
327:    X(int,                  KIND_INT,        xgb_train_nthread, ...
```

CONFIRMED: at HEAD, the 3 collision names have metadata `IS_BOOT_ONLY | WARN_ON_CLAMP` only — **NO STAMP_BOUND_CFG_DERIVED bit**. So the cfg walker filter naturally excludes them; POST_CFG walker is solely authoritative. Safe at HEAD.

**Coding-time gotcha (LOW for ANY future ship):** if a future ship adds STAMP_BOUND_CFG_DERIVED bit to any of the 3 collision names, the cfg walker WILL emit it (then POST_CFG MC walker emits SAME name → duplicate wire emit → Class 31 instance). Currently SAFE; future-risk surfaced. B13 sidecar covers struct-gen + longopts[] but NOT emit-walker.

**Recommended fix:** add an explicit Phase L pre-coding note (or coding-time check) — if any of the 3 collision names ever get STAMP_BOUND_CFG_DERIVED bit added, the cfg walker filter at `cfg_derived::populate_stamp_cfg_from_derived` MUST be extended with same `FOREACH_STAMP_RESULT_FIELD_EXCLUSION` sidecar redirect; OR a Layer 5b invariant test that asserts wire body line names UNIQUE (catches duplicate-key emit). Defer to TECH_DEBT or add to L4 extensibility test scope.

**Severity rationale:** LOW (not MEDIUM) because at HEAD the cfg walker filter naturally excludes; only triggers on a future regression that requires deliberate flag-add to one of 3 specific rows.

### LOW-3 — Decision F SOFT compat language framed at 15-key scope; consistent across plan body

**Cite (plan body lines 200, 348, 624, 1198, 1232 — multiple sites + Decision D v1.6 scope at lines 96-110 + Decision F at 192-202):**

Decision D scope (15 entries): 9 thompson + bandit_blend_ratio + 5 model-state cohort
Decision F SOFT compat scope: parser back-compat for 15 legacy prefixed wire keys

Plan body has reconciled v1.11 amendment 9→15 alignment across:
- Decision F itself (line 200)
- Operator migration impact (line 348)
- Step 1.6.2 wire-key change list (line 624)
- Step 1.6.7.4 parser back-compat (line 791)
- Phase G sequencing (line 1197-1198)
- Verification gate (line 1232)
- FEATURE_LOOKUP entry (line 1284)

**All 15 sites use "15 legacy prefixed wire keys" or equivalent.** v1.11 alignment is comprehensive.

**Minor gap:** Decision F's `Verdict: F.2 CHOSEN` table at line 199 still says "Parser dual-recognition + emit v2 only" (correct). But the v1.6 scope expansion DOC didn't include reference to bash script line 244 emit at `tools/stamp_model.sh` (`inference_cfg_freshness_tau=`) — verified at HEAD: bash STILL emits `inference_cfg_freshness_tau` (line 244 of bash) but engine no longer parses or emits the field (orphan since v5.14.9.D). Engine `ModelInference.hpp` line 356 comment shows `held_out_fraction` is parser-side-only.

**Impact:** under Phase L, bash deprecation shim (Step L5) replaces bash with `exec build/stamp_model_cli "$@"`. The CLI binary calls framework directly. The bash orphan emit (`inference_cfg_freshness_tau`) IS NOT a concern post-Phase-L because bash content is no longer the emit path. Phase L makes the bash orphan an irrelevant artifact (bash body deleted; only `exec` shim remains).

**Recommended fix:** none material — Phase L STRUCTURALLY resolves the orphan via shim. Documentation note at L5 deprecation shim: "bash orphan `inference_cfg_freshness_tau` at line 244 disappears with bash body deletion; engine never emitted; CLI inherits framework canonical body which never emits."

### LOW-4 — Locale pin defense-in-depth claim correctness verified; observability note

**Cite (plan body line 969 + Phase L spec § "Locale handling in CLI binary"):**

> Defense-in-depth: pin LC_NUMERIC=C in main() before any framework call (framework already pins internally; redundant pin is cheap + protects against any non-framework code paths).

**Verified at framework layer (`MemHeaders/CfgGateRegistry.hpp:342-406` `populate_stamp_cfg_from_derived` calls `tt::cfg_emit_field` which DOES inner-locale pin per spec):**

The framework's per-row `tt::cfg_emit_field` at `CfgFieldDispatch.hpp:332-359` does inner `uselocale(LC_NUMERIC=C)` per row. Outer locale pin at `stamp_write_for_model` (`ModelInference.hpp:~1700`) provides outer pin. Plan body Step 1.6.4.a annotation (lines 727) accurately notes this as "redundant but not a correctness hazard" + TECH_DEBT-103 tracks optimization.

CLI binary main() adding a 3rd-layer outer pin = triple-redundant but still correct. Not a correctness hazard. NOT a performance issue at CLI runtime (boot-time, not hot-path).

**Observability nit:** Phase L spec § "Locale handling in CLI binary" doesn't note that the framework's per-row pin (inner-most layer) is the LOAD-BEARING pin for byte equivalence — outer pins are belt-and-suspenders. If at some future ship someone removes the inner pin for "optimization" (TECH_DEBT-103's eventual closure should NOT remove all pins; should add an inner-no-pin variant for use under outer-pin context — see TECH_DEBT-103 description). Phase L spec could add 1 line clarifying this nuance.

**Recommended fix:** at coding time, add to Phase L spec § Locale handling: "Inner locale pin at `tt::cfg_emit_field` is the LOAD-BEARING byte-equivalence guarantee; outer pins (caller + main()) are defense-in-depth. TECH_DEBT-103 eventual closure must preserve at least one pin in the emit call chain."

**Severity rationale:** LOW (not MEDIUM) because TECH_DEBT-103 explicitly tracks the optimization path; coding-time spec body cross-references. Documentation completeness only.

---

## Cross-cutting concerns

### Class 31 detection at code-time

Phase L L4 verification adds extensibility test (X-macro walker validates all flagged rows) + Layer 5b CLI emit invariants test. Both compose to catch most Class 31 instances at test-time. NEW DESIGN_SPEC section "Audit detection" in Phase L spec v1.1 captures grep signatures.

**Sister discipline:** the bash deprecation shim ensures NO new bash scripts emit wire format (per TECH_DEBT-106 NARROW scope post-Phase-L). Combined with extensibility test, the detection mesh is sound.

### Wire-format byte preservation chain (Layer 1-5b)

Verified at code-level:
- Layer 1 (struct padding determinism): preserved — STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN unconditional struct-gen has `_padding`-equivalent via `uint8_t has_<name>; STORAGE_T name;` shape (cite: `CfgGateRegistry.hpp:629-636`)
- Layer 2 (locale pin): preserved — `tt::cfg_emit_field` inner pin (cite: `CfgFieldDispatch.hpp:332-359`)
- Layer 3 (atomic write): unaffected by Phase L (framework owns `stamp_write_for_model`'s atomic write)
- Layer 4 (round-trip): Phase L L4 round-trip test verifies
- Layer 5 (HMAC chain): preserved — CLI calls `stamp_write_for_model` directly; same HMAC code path as engine
- Layer 5b (structural invariants I1-I5): Phase L L4 extends `wire_format_invariants.hpp` to CLI emit path (cite plan body line 994)

### Decision F SOFT compat semantic

Verified at code-level: parser at `ModelInference.hpp:1377-1383` reads `stamp_format_version` and stores; no STRICT-mode refuse at HEAD. Plan body Step 1.6.7.2 adds RELAXED parser bounds check accepting v1 + v2. Step 1.6.7.4 parser back-compat for 15 legacy prefixed keys lands in SAME COMMIT as Step 1.6.4 + Step 1.6.7.3 per Phase F BUILD-FORCED sequencing (cite line 1189).

### B12 row-order parity at Step 1.6.4

Plan body lines 725 annotation. Master FOREACH_PER_CORE_CFG_FIELD declaration order DIFFERS from legacy FOREACH_STAMP_BOUND_CFG body order. Annotated as INTENTIONAL under SOFT-bump. Layer 5b invariants tolerate the diff (I1 line-count + I4 per-row name presence + I5 per-core-before-global preserved; I2/I3 unaffected). Step 1.6.7.5 v1 LOAD test verifies v1 parser acceptance; Step 1.7 Layer 5b invariants verifies v2 shape.

**Verification:** Decision F (F.2) parser dual-recognition + emit-v2-only structurally guarantees that v1 stamps load on `.B.3+` engine. Cross-ref `wire-format-byte-preservation-discipline.md` Layer 6 Surface G + Layer 5b structural invariants.

---

## Behavior matrix (train and serve agree for default cfg under Phase L)

| Scenario | Trainer view (CLI binary) | Engine view (in-process emit) | Identical? |
|---|---|---|---|
| v2 stamp, default cfg | `stamp_model_cli` → framework `stamp_write_for_model` → `cfg_derived::populate_stamp_cfg_from_derived` | `Stamp_AssembleAndEmit` → `stamp_write_for_model` → same framework | **YES (bytewise identical)** — same code path |
| v2 stamp, custom cfg via CLI flag | CLI flag → CliReceived struct → apply_cli_args_to_cfg → framework | engine.cfg → ControllerConfig parser → framework | **YES** — both produce ControllerConfig<F> with same values; same framework path downstream |
| v1 stamp load on `.B.3+` engine | n/a (CLI emits v2 only) | parser dual-recognition layer (Step 1.6.7.4) accepts legacy prefixed keys | **YES** — back-compat parser populates same struct fields |
| Cfg drift check after stamp load | n/a | drift_check_from_derived walks framework cohort | **YES** — same framework |
| Extensibility test (new STAMP_BOUND_CFG_DERIVED row added) | X-macro walker auto-validates | engine has same flagged set | **YES** — registry single source of truth |
| Round-trip byte-identity | CLI emit | engine in-process emit | **YES (verified by Phase L L4 byte-identity test)** |

All scenarios agree by construction post-Phase-L. The CLI binary is a thin wrapper over the same framework API the engine uses.

---

## NOT a bug (verified-safe items)

### Phase L CLI binary locale pinning is triple-layered but not a correctness hazard

CLI main() pin + caller `stamp_write_for_model` outer pin + per-row `tt::cfg_emit_field` inner pin. Triple-redundant. Inner pin is LOAD-BEARING; outer pins are belt-and-suspenders. Triple pin doesn't change byte equivalence; not a correctness regression. TECH_DEBT-103 future optimization should preserve at least one pin in chain.

### B13 cross-walker collision resolution mechanism is sound

`FOREACH_STAMP_RESULT_FIELD_EXCLUSION` sidecar at `CfgGateRegistry.hpp:619-622` provides 3 exclusion names. Sister redirect bracket pattern at struct-gen layer (cite line :606-617 file comment) provides precedent for longopts[] sister application. Phase L spec § Step 2.5 § B13 documents the canonical pattern body.

### v1↔v2 wire-format row-ordering diff is INTENTIONAL under SOFT bump

Plan body Step 1.6.4 annotation explicit; Decision F SOFT compat covers; Layer 5b invariants I1-I5 tolerate reorder (no I-invariant asserts row order across master-registry rows; I5 only asserts per-core-before-global which is preserved by FOREACH_STAMP_BOUND_DERIVED_COHORT meta-walker expansion order).

### Phase L preserves all 6+ previous cross-tool sync events' surface

`tools/stamp_model.sh` has tracked 6+ sync events. Phase L `tools/stamp_model_cli.cpp` calls framework directly; every future cfg field add = 1 row in master registry; CLI inherits for free. The 6+ recurrence count drops to 0 by construction post-Phase-L (no mirror; drift impossible).

### Step 1.6.7.4 parser back-compat for 15 legacy keys lives in SAME COMMIT as wire-format-changing steps

Step 1.6.4 (canonical body emit) + Step 1.6.7.3 (version bump 1→2) + Step 1.6.7.4 (parser back-compat) all in SAME COMMIT per Phase F BUILD-FORCED sequencing (cite plan body line 1189). Prevents version-label-with-wrong-keys hazard.

---

## Verification gate (re-fire of v1.14 punch list)

| v1.14 finding (closed in v1.15) | Verdict |
|---|---|
| CRIT-1 9-flag XGBoost gap → Class 21 at CLI INTERFACE LAYER | **CLOSED v1.15** — X-macro auto-gen of longopts[] + value-receiver + parse dispatch via existing tt::cfg_parse_field<T>; sister to engine's emit walker. Adding new cfg field = 1 row in master → CLI flag auto-appears |
| CRIT-2 CMake 4-line target pattern | **CLOSED v1.15** — Step L3 + Phase L spec § Step 3; matches `tools/compare_scalers.cpp` precedent at `CMakeLists.txt:248-251` |
| HIGH-2 forward-refs in 3 sister specs | **CLOSED v1.15** — Step L6 cross-ref updates landed at v1.14; reaffirmed at v1.15 |
| HIGH-3 stale FPN.hpp → FixedPoint64.hpp | **CLOSED v1.15** — Phase L spec v1.1 stale include path fixed at line 142 |
| MED-1 4 stale doc sites | **CLOSED v1.15** — comment-only refs explicitly out of Phase L scope per plan body line 1021 |
| MED-2 README catalog | **CLOSED v1.15** — `DESIGN_SPECS/README.md` Framework discipline patterns subsection entry per plan body line 284 |
| Extensibility test recurrence vector (NEW v1.15) | **CLOSED v1.15** — X-macro walker validates all flagged rows; sister codification at cfg-derived-consumer-framework.md v1.3 § Extensibility test pattern |

7-of-7 closed.

---

## Suggested ship sequence

Phase L coding can proceed immediately post-greenlight. Coding-time amendments (MED-1 line cite + LOW-1 sketch consistency + LOW-3 spec body locale clarification) accumulate at L1 (DESIGN_SPEC amendment) + L2 (CLI binary) without blocking.

Phase L BUILD-FORCED sequencing (plan body lines 1167-1213) is sound. v1.14 SAME-COMMIT discipline (Step 1.6.4 + 1.6.7.3 + 1.6.7.4 + Phase L) reaffirmed at Phase H + Phase L.

**Pre-coding gate verdict:** GREEN-WITH-AMENDMENTS — Caramel can sign off greenlight. 5 findings (1 MED + 4 LOW) are all bookkeeping-class; no structural-blocking findings.

---

## Cross-references

- v1.14 audit predecessor: `parity-check-2026-05-18-phase-l-amendment.md`
- v1.15 blindspot audit: `blindspot-scan-2026-05-18-phase-l-v1.15-amendment.md`
- Pattern v1.1 spec: `tick-trader-percore-workspace/DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md`
- Sister spec v1.3: `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/cfg-derived-consumer-framework.md`
- Wire-format discipline: `tick-trader-percore-workspace/DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` Layer 7 (cross-tool emit-site enumeration)
- M4 taxonomy: `tick-trader-percore-workspace/DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` Pillar B13 (cross-walker collision resolution)
- Plan body: `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.15

---

**End of report.**

Verdict: **YELLOW** — 1 MED (stale line cite) + 4 LOW (sketch consistency / row-order future-risk / orphan note / locale observability). 7-of-7 v1.14 findings closed. NO new CRITICAL or HIGH findings. Coding-ready pending operator greenlight.
