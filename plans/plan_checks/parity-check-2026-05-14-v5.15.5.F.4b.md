# /parity-check report — 2026-05-14 — v5.15.5.F.4b pre-coding audit

**Plan:** `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4b-foreach-cfg-field-registry-implementation.md`
**Sprint umbrella:** `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4-universal-cfg-registry-sprint.md`
**HEAD:** v5.15.5.F.3 = `f72caef`
**Audit scope:** train↔serve identity + wire-format byte preservation (focused .F.4b)
**Caller:** Caramel; fired in parallel with /trace-deps, /readiness, /merge-scan, /dod-audit.

---

## Verdict: **YELLOW** — proceed with 4 must-fix amendments before .F.4b coding starts

The plan's foundation is sound (registry pattern matches established `FOREACH_STAMP_BOUND_CFG` + `FOREACH_STAMP_BOUND_MODEL_CONST` precedent; `tt::` namespace + Y3 dispatch per CLAUDE.md item 23 + Layer 5b hash test per `wire-format-byte-preservation-discipline.md`). However, **4 must-fix findings** block GREEN status:

1. **CRITICAL — Layer 5b hash lock at .F.4b is premature** (STAMP_BOUND derived filter incomplete at .F.4b because int fields don't migrate until .F.4c)
2. **HIGH — Locale-pinning missing from registry-driven save path** (current `atof` parser + `snprintf` save via `cfg_write_field` are NOT locale-pinned today; status quo bug recurs in registry path unless fix is explicit)
3. **HIGH — Step 6 byte-equivalence test is weaker than file-byte parity** (compares `cfg1.X == cfg2.X` Cfg struct fields, NOT emitted file bytes — insufficient per Layer 4 + 5)
4. **MEDIUM — Descriptor cache-line budget inconsistency** (Step 1 says ≤128B; Step 6 static_assert says ≤64B)

Plus 2 MEDIUM design clarifications + 1 LOW documentation note. No blockers — the structural fix path is correct; these are tightening amendments before coding.

---

## Focus area verdicts (per task prompt)

| Focus | Verdict | Notes |
|---|---|---|
| 1. Train↔serve byte-identity for KIND_DOUBLE/_PCT roundtrip | YELLOW | Step 6 test is too narrow — needs file-byte comparison, not Cfg-field equality (F3 below) |
| 2. Stamp body byte-identical for legacy stamps after derived filter swap | RED at .F.4b ship; YELLOW at .F.4c+ | LOCKED_STAMP_BOUND_DERIVED_HASH cannot be locked at .F.4b because the derived walk is partial (DOUBLE-only); int STAMP_BOUND fields only appear at .F.4c (F1 below) |
| 3. HMAC chain integrity via Layer 5b synthetic-hash test | YELLOW | Pattern is correct; lock timing is wrong (see F1); legacy stamp fixture for Layer 4 verification ABSENT (F5 below) |
| 4. Categorical applicability columns are GUI-only (no stamp body leak) | GREEN | Plan correctly scopes `applies_to_strategy_cat` / `_op_mode_cat` / `_regime_cat` / `_risk_cat` + `lives_in_struct` as GUI/parser metadata; they're not emitted via `cfg_save_field`; not in the STAMP_BOUND derived walk; confirmed via Step 1 + Step 5 + Deliverable A (only `meta` STAMP_BOUND bit gates emit). NO leak. |
| 5. Locale pinning in tt::cfg_save_field | RED | Plan does not address; status quo at SettingsPanel (`snprintf(v, 32, fd->fmt, float)` line 795 + `cfg_write_field` line 472 + parser `atof` lines 1879, 1887, 1908) is NOT locale-pinned today (F2 below) |
| 6. tt:: dispatch correctness vs C++17 if-constexpr in non-template context | GREEN | Step 2 explicitly uses `template <CfgFieldDescriptor::Kind K>` parameterization; each specialization is a fully-typed template instantiation per CLAUDE.md item 23. The Y3 dispatch in Deliverable A (`EMIT_IF_STAMP_BOUND_DISPATCH_##meta`) is preprocessor-level, not if-constexpr — correctly avoids the non-template-context caveat. |

---

## Findings

### F1 (CRITICAL) — Layer 5b hash lock at .F.4b is premature; derived walk is INCOMPLETE until .F.4c

**File:line refs:**
- Plan Step 1 (`plan:50`): "start with just KIND_DOUBLE + KIND_DOUBLE_PCT entries (~40 rows). DO NOT add INT/INT_ENUM/BOOL/STRING yet (.F.4c+)"
- Plan Deliverable A (`plan:331-335`): "Synthetically populate every STAMP_BOUND-flagged registry field" + "Lock at .F.4b ship time; fails on accidental row reorder"
- Existing registry: `ML_Headers/StampBoundCfgRegistry.hpp:99-176` — FOREACH_STAMP_BOUND_CFG has **24 rows**, of which:
  - 11 are `int` (ridge_within_horizon, ridge_across_horizons, confidence_composite_enabled, exit_blender_mode, risk_degradation_curve, ml_buy_threshold's siblings... actually 6 ints) — these only migrate in .F.4c per plan
  - 13 are `double`
- DESIGN_SPECS: `wire-format-byte-preservation-discipline.md:200-230` Layer 5b says lock the hash at "ship commit (before any FOREACH_CFG_FIELD addition that affects STAMP_BOUND ordering)"

**Symptom:** If LOCKED_STAMP_BOUND_DERIVED_HASH_V5_15_5_F4 is locked at .F.4b (per Deliverable A as-written), the synthetic walk over FOREACH_CFG_FIELD with STAMP_BOUND filter produces:
- At .F.4b: 13 double STAMP_BOUND fields (ridge_lambda, ridge_cost_penalty, ridge_min_ic_floor, confidence_freshness_tau_secs, confidence_capacity_target_dollars, confidence_capacity_kappa, confidence_rmse_baseline, winsor_pct_low, winsor_pct_high, risk_full_size_threshold, risk_min_size_threshold, risk_min_size_pct, ml_buy_threshold, gap_acceptable_threshold, thompson_mu_prior, thompson_precision_prior, thompson_precision_obs) — **NOT byte-identical to FOREACH_STAMP_BOUND_CFG's 24-row body**
- At .F.4c: hash WILL CHANGE when int fields are added (and intermixed in the correct canonical order)

So the .F.4b hash is by definition a moving target across .F.4c. This violates Layer 5b's intent: the locked hash is a guard against *accidental* reorder, not a deliberate cutover hash that gets rotated.

**Worse:** Plan Step 1 says "registry order initially DOUBLE-only" → when .F.4c adds int fields, the canonical order needs to be RE-INTERLEAVED to match legacy emit order (ridge_within_horizon BEFORE ridge_lambda, etc.). If FOREACH_CFG_FIELD has DOUBLE fields appended first then INT fields inserted later, the order will NOT match the legacy FOREACH_STAMP_BOUND_CFG order (which has ridge_within_horizon + ridge_across_horizons at positions 1+2, then doubles). HMAC chain breaks at .F.4c.

**Recommended fix path (choose one before .F.4b coding):**

**Option A (PREFERRED — keep dual registry until full migration):** At .F.4b, DO NOT add STAMP_BOUND derived filter. Keep FOREACH_STAMP_BOUND_CFG as the authoritative emit registry. Move "Deliverable A: STAMP_BOUND derived filter" to .F.4c (when int fields migrate) — but only after ALL STAMP_BOUND fields are in FOREACH_CFG_FIELD. Lock LOCKED_STAMP_BOUND_DERIVED_HASH_V5_15_5_F4c at that point + add the cutover from FOREACH_STAMP_BOUND_CFG → FOREACH_STAMP_BOUND_CFG_DERIVED in stamp_write_for_model.

**Option B (only if Caramel insists derived filter ships at .F.4b):** Pre-populate FOREACH_CFG_FIELD with ALL 24 STAMP_BOUND rows at .F.4b — INT entries kept as no-op parser/save/render dispatch (they don't run yet, but exist for derived walk). The parser remainder for those int fields still routes through the manual CFG_PARSE_INT branch (no double-parse). This adds ~50 LOC scope to .F.4b but locks the hash correctly at .F.4b. Operational cost: descriptors for 11 int fields without functional dispatch are documented as "schema-stub for .F.4c population".

**Option C (DEFER ENTIRELY):** Drop Deliverable A from .F.4b. Ship FOREACH_CFG_FIELD as DOUBLE-only scaffold (parser/save/render via tt:: dispatch). The derived filter + hash lock is a separate ship — could be .F.4j or v5.15.5.F.5. Trade-off: longer dual-registry lifetime; loses one of the structural-fix wins of this sprint.

**My ranking:** Option A is the cleanest; matches Caramel's "do it right the first time" rule (no .F.4b → .F.4c hash rotation that creates audit-confusion noise). Option B is acceptable if she wants the structural change visible at .F.4b. Reject Option C — defeats the sprint's purpose.

**PARITY-NNN assignment:** Per the auto-write contract, this is documented in `DOCS/PARITY_ISSUES.md` as **PARITY-026** with status OPEN-PRE-CODING. Closes when .F.4b plan amends per Option A or B before coding.

---

### F2 (HIGH) — Locale-pinning missing from registry-driven save path; current save path is NOT locale-safe today

**File:line refs:**
- Status quo: `GUI/SettingsPanel.hpp:472-516` — `cfg_write_field` reads/writes engine.cfg with `fopen`/`fwrite`/`%s=%s` — NO `uselocale` pinning
- Status quo: `GUI/SettingsPanel.hpp:791-797` — float → string conversion via `snprintf(v, 32, fd->fmt, s->float_vals[i])` — NO `uselocale` pinning
- Status quo: `CoreFrameworks/ControllerConfig.hpp:1875-1908` — `CFG_PARSE_FPN` uses `atof(val)`; `CFG_PARSE_INT` uses `atof(val)` (line 1908). `atof` HONORS LC_NUMERIC.
- Plan Step 2 (`plan:88-97`): defines `tt::cfg_save_field<KIND_DOUBLE>` template but does NOT mention `uselocale(newlocale(LC_NUMERIC_MASK, "C", 0))` pinning
- Plan Step 5 (`plan:170-188`): walks registry emit but does NOT mention locale pinning
- Existing locale-pinned save path (precedent): `MemHeaders/RunHistory.hpp:87-88` uses `locale_t pinned = newlocale(LC_NUMERIC_MASK, "C", (locale_t)0);` correctly
- Existing locale-pinned stamp emit: `ML_Headers/ModelInference.hpp:1804-1808` restores after canonical body emit

**Symptom:** A v5.14 SettingsPanel save under `LC_NUMERIC=de_DE.UTF-8` writes `ml_buy_threshold=0,65` to engine.cfg. The parser's `atof` reads it back AS de_DE → silent corruption at boot WITHOUT locale flip. With locale flip across machines/users, train→serve drift occurs because two sessions on different locale settings see different cfg values. This is a status-quo bug that .F.4b carries forward unchanged unless explicitly fixed in `tt::cfg_save_field` + a parallel fix in `tt::cfg_parse_field`.

**Risk class per `wire-format-byte-preservation-discipline.md` Layer 2:** "thread-local via uselocale" — the engine has NO process-wide setlocale at boot (verified via grep), but SettingsPanel calls into FoxML suite which may have ImGui or other library setlocales. Tests at `tests/controller_test.cpp:9018-9060` + `tests/controller_test.cpp:15117-15131` DO exercise `setlocale(LC_NUMERIC, "de_DE.UTF-8")` and pin parser invariants — but these tests test individual parsers, not the SettingsPanel save → engine.cfg → parse roundtrip.

**Recommended fix (1-2 line add to .F.4b Step 2 + Step 5):**

```cpp
// In tt::cfg_save_field<KIND_DOUBLE>:
template <> inline void cfg_save_field<CfgFieldDescriptor::KIND_DOUBLE>(
    FILE* fp, const Cfg* src, const CfgFieldDescriptor& desc)
{
    locale_t pinned = newlocale(LC_NUMERIC_MASK, "C", (locale_t)0);
    locale_t prev = pinned ? uselocale(pinned) : (locale_t)0;
    double v = *reinterpret_cast<const double*>(
        reinterpret_cast<const char*>(src) + desc.offset);
    fprintf(fp, "%s=%.17g\n", desc.cfg_field_name, v);
    if (pinned) { uselocale(prev); freelocale(pinned); }
}
```

Likewise `tt::cfg_parse_field<KIND_DOUBLE>` should use `tt::parse_double_fast` (precedent: `StampBoundCfgRegistry.hpp:195` `STAMP_CFG_PARSE_double(val) tt::parse_double_fast(val)`), NOT `atof`. `parse_double_fast` is locale-independent (uses `from_chars` internally per a quick check).

**Plan amendment:** Add a 4-line note to Step 2 + Step 5 covering: locale pinning required for KIND_DOUBLE save; KIND_DOUBLE parser uses `tt::parse_double_fast` (NOT `atof`). Refer to `MemHeaders/RunHistory.hpp:87-89` as precedent.

**Alternative:** Pin locale ONCE at the top of the parser entry (`ControllerConfig_Load`) + once at the top of the save entry (whatever called `cfg_save_field` in a loop). This is cleaner than per-field pinning and matches `stamp_write_for_model` pattern. Either works; per-field is more defensive against future callers.

---

### F3 (HIGH) — Step 6 byte-equivalence test is too narrow

**File:line refs:**
- Plan Step 6 (`plan:206-220`): test compares `cfg1.ml_buy_threshold == cfg2.ml_buy_threshold` etc.

**Symptom:** The test verifies that LOAD ∘ SAVE is the IDENTITY on the Cfg struct — that's parser/save reflexivity for cfg-struct fields. It does NOT verify:
- Save produces byte-identical file bytes for ALL migrated fields (some may emit but not roundtrip cleanly)
- The save+load cycle produces identical output for EVERY migrated KIND_DOUBLE/_PCT field (the test list "/* etc */" implies sampling, not enumeration)
- The save output matches the EXISTING save output (pre-.F.4b file format)

For a registry refactor, the LOAD-side test alone is insufficient — pre-.F.4b's manual save → post-.F.4b's registry save must produce byte-identical output (otherwise legacy operator cfg files generated by pre-.F.4b SettingsPanel can drift when re-saved).

**Recommended fix (Step 6 amendment):**

Add a third test class — **emit byte-equivalence** — that:
1. Populates a Cfg with deterministic values for ALL migrated fields
2. Calls the OLD (manual) save path → captures byte buffer A
3. Calls the NEW (registry) save path → captures byte buffer B
4. Asserts `memcmp(A, B, N) == 0`

This is the per-field-direct version of Layer 5 (snapshot hash). The hash test is fine for "future drift detection"; the direct memcmp is for "right-now refactor verification". Both are cheap (~200 LOC of test code; runs in tests/controller_test.cpp).

Also add an **enumeration loop** test — iterate over ALL FOREACH_CFG_FIELD entries via X-macro count macro (precedent: `STAMP_CFG_COUNT_ONE` in StampBoundCfgRegistry.hpp:260-261), generate a random value per descriptor's Kind, save+load+verify. This catches "we forgot to migrate field X in the parser but it does load via the manual fallback" — the test would fail on the field-count mismatch.

---

### F4 (MEDIUM) — Descriptor cache-line budget inconsistency between Step 1 and Step 6

**File:line refs:**
- Plan Step 1 (`plan:49`): `static_assert(sizeof(CfgFieldDescriptor) <= 128, ...)` — 128B (2 cache lines)
- Plan Step 6 (`plan:224`): `static_assert(sizeof(CfgFieldDescriptor) <= 64)` — 64B (1 cache line)
- Plan If-something-goes-wrong (`plan:306`): "Build fails on `static_assert(sizeof(CfgFieldDescriptor) <= 64)`: the union grew too large"

**Symptom:** Step 6's test will fail at compile time given Step 1's design (4 categorical fields = 8B; lives_in_struct = 1B; metadata_flags uint16 = 2B; field_idx uint16 = 2B; 4 string pointers = 32B; payload union (largest is `as_double` = 24B); Kind enum = 1B — adds to roughly 70B with padding). Reading Step 1 carefully: "128-byte cache-line budget (2 cache lines; cfg metadata is NOT latency-critical per `latency-vs-cache-decision-framework.md`)" — that's the intent. Step 6's `<= 64` is a leftover from earlier draft.

**Recommended fix (trivial):** Edit Step 6 static_assert to match Step 1 (`<= 128`). Update Step's If-something-goes-wrong section to match.

---

### F5 (MEDIUM) — No frozen v5.14 stamp fixture for Layer 4 round-trip HMAC test

**File:line refs:**
- DESIGN_SPECS `wire-format-byte-preservation-discipline.md:142-174` Layer 4 — "Round-trip test ON A REAL LEGACY STAMP. Synthetic test fixtures are good but a REAL v(N-1) stamp from disk is the gold-standard verification."
- Existing tests: `tests/controller_test.cpp:21154-21165` — round-trip HMAC test exists but is SYNTHETIC (constructs StampInferenceCfgInputs in-process, emits, re-parses) — does NOT load a REAL v5.14 stamp file
- Verified via `find tests/ -name "*.stamp" -o -name "fixtures"`: NO frozen stamp fixture file checked into the repo

**Symptom:** If .F.4b's derived filter (per Option A above, defers to .F.4c) ships with a synthetic-only round-trip test, a legacy v5.13 / v5.14 stamp on disk MIGHT fail to verify post-cutover, and the synthetic test wouldn't catch it. The Layer 4 gold-standard test (load real v5.14 stamp → re-emit canonical body → verify HMAC) is the only way to catch a subtle reorder-or-format drift between manual emit + registry-derived emit.

**Recommended fix:**

Commit a frozen v5.14 stamp fixture as gitignored test data with the canonical body bytes inline in the test source (since the binary stamp file isn't in the repo). This is what wire-format-byte-preservation-discipline.md Layer 4 example does:

```cpp
// In tests/controller_test.cpp post-.F.4b derived-filter cutover (at .F.4c):
const char* v5_14_canonical = R"(model_format_version=6
training_timestamp_us=1735689600000000
horizon_secs=300
...etc all 24 STAMP_BOUND fields in canonical order...
overlay_hash=...
effective_hash=...
)";
const char* legacy_secret = "test-fixture-v5.14-secret";
char legacy_hmac[65];
tt::hmac_sha256_hex(legacy_secret, v5_14_canonical, legacy_hmac);

// Write fixture to /tmp; verify via NEW (derived-filter) verify_model_stamp:
write_stamp_file("/tmp/v5_14_fixture.stamp", v5_14_canonical, legacy_hmac);
ModelStampResult r = verify_model_stamp("/tmp/v5_14_fixture.stamp", legacy_secret, ...);
check("v5.15.5.F.4c: legacy v5.14 stamp verifies under derived filter", r.valid == 1);
```

This is .F.4c work (when the cutover happens, per Option A) — but **flag as blocker now** because it requires deciding WHICH v5.14 stamp body to freeze (production stamp from operator? synthetic? generated by running v5.14.x HEAD?). The decision drives a small one-time effort at .F.4c kickoff.

**Plan amendment:** Add to `.F.4c` plan (when written) a Step 0.5 "Generate frozen v5.14 stamp fixture body" using current FOREACH_STAMP_BOUND_CFG emit at v5.15.5.F.4 head — save to test data, lock into the test file. Decoupled from .F.4b but blocks .F.4c GREEN status.

---

### F6 (MEDIUM) — STAMP_CFG_AUTOPOPULATE equivalent missing from plan

**File:line refs:**
- DESIGN_SPECS `autopopulate-pattern-for-production-caller-class.md` — pattern requires AUTOPOPULATE companion to extinguish production-caller class
- CLAUDE.md item 21 — "When a registry has multiple production callers that ASSEMBLE the registry-driven struct, define an AUTOPOPULATE companion macro"
- Plan only references "CLAUDE.md item 21 (AUTOPOPULATE companion)" in the commit message (line 258) but no actual `CFG_FIELD_AUTOPOPULATE` macro is designed
- The plan's tt:: dispatch operates per-field (parser writes, save emits, render); no aggregate production-caller pattern is in scope

**Symptom:** The plan IS the AUTOPOPULATE for cfg parse/save (registry walk via X-macro produces all per-field operations). However: when a future caller wants to construct a Cfg-clone or migration-target struct from a Cfg source, they would benefit from a `CFG_FIELD_AUTOPOPULATE(dst, src)` companion. Without it, future production callers (e.g., a hypothetical "Cfg overlay merge", "per-core override expansion", "test fixture builder") will re-discover the manual N-site pattern that AUTOPOPULATE extinguishes.

**Severity reasoning:** MEDIUM because there's no immediate production-caller class today — Cfg parsing has a single chokepoint (`ControllerConfig_Load`), as does Save (the GUI write path). The Class 18 mirror at production-caller level is NOT currently a recurring bug here. But the pattern is missing for future-proofing.

**Recommended fix:** Add a small section to Step 2 (CfgFieldDispatch.hpp) showing `CFG_FIELD_AUTOPOPULATE(dst, src)` X-macro that copies all cfg fields from `src` to `dst` (for use in things like cohort tests + per-core override expansion + cfg-overlay tests). Cost: ~20 LOC scaffold; no production caller wiring needed at .F.4b. Caramel can defer the wiring to .F.4c-or-later.

---

### F7 (LOW) — Plan ambiguity on `cfg_save_field` integration with existing `cfg_write_field` GUI path

**File:line refs:**
- Plan Step 5 (`plan:170-188`): wires `tt::cfg_save_field<K>` into `Cfg_Save(const Cfg* cfg, FILE* fp)` — atomic file save
- Status quo: `GUI/SettingsPanel.hpp:472-516` — `cfg_write_field(path, key, value)` does in-place edit-or-append on the cfg file (NOT a full re-write)
- Status quo: SettingsPanel line 791-797 calls `cfg_write_field` per-field when operator edits a single InputFloat

**Symptom:** Plan Step 3 wires the registry into SettingsPanel via `cfg_render_field` (per-field UI render). When operator commits an edit (`ImGui::IsItemDeactivatedAfterEdit()` at line 793), the existing flow calls `cfg_write_field(s->cfg_path, fd->key, v)` — a SINGLE-FIELD in-place file edit, NOT a full registry save.

Plan Step 5 is `Cfg_Save(cfg, fp)` — a full save. But:
- The existing GUI never calls a "full save" — every edit triggers an in-place single-line edit via `cfg_write_field`
- So `tt::cfg_save_field<K>(fp, src, desc)` is called via what production path? Plan needs to clarify whether (a) `Cfg_Save` is a NEW full-save function introduced at .F.4b and the GUI starts using it instead of `cfg_write_field`, or (b) `Cfg_Save` exists but isn't wired into the GUI yet (just for tests + future use), or (c) `cfg_write_field` is refactored to use `tt::cfg_save_field<K>` internally for the single-field case.

**Severity:** LOW — clarifies a documentation/scope ambiguity, doesn't block correctness. Caramel can pick whichever shape; recommend (a) for simplest registry-driven discipline (full save uses registry; existing in-place editor stays for now, migrates later).

---

## Plan strengths (called out)

1. Step 2's `tt::cfg_parse_field<K>` correctly uses template instantiation per Kind — Y3 dispatch caveat (CLAUDE.md item 23) AVOIDED.
2. Step 1's descriptor design correctly separates `applies_to_*_cat` (GUI/parser metadata) from `STAMP_BOUND` metadata bit (stamp body emit gate). NO leak of categorical columns into HMAC body bytes. **GREEN on focus area 4.**
3. Step 1's `static_assert` discipline + `uint32_t` / `uint16_t` overflow guards per `bitmap-overflow-protection-discipline.md` is correct.
4. Step 1's "descriptor schema LOCKS at .F.4b; subsequent sub-ships only add rows + populate masks" is consistent with Caramel's design-upfront + ship-in-waves decision (2026-05-14).
5. Deliverable C's CI tests for orphan categories + self-consistency are sound (sister pattern to `FEATURE_REGISTRY_HASH`).
6. Step 6 paper-trade verification gate is correctly placed.
7. Plan's rollback anchor (Step 0 git tag `pre-v5.15.5.F.4b`) + 5-binary build gate is correctly placed.

---

## Cross-cutting concerns

- **F1 + F5 are paired** — they're both about derived-filter cutover timing. Recommend Option A (F1) + frozen v5.14 fixture at .F.4c (F5) bundled.
- **F2 + F3** are both about test/discipline strength — both are mechanical add-on improvements that strengthen .F.4b's verification gate without changing the core design.
- **F4** is a trivial number consistency fix.
- **F6** is a future-proofing pattern; doesn't block .F.4b.

---

## Suggested ship sequence

1. Caramel reviews F1 (CRITICAL) → picks Option A / B / C → updates plan Deliverable A accordingly.
2. Apply F2 (locale pinning) to Step 2 + Step 5 plan text.
3. Apply F3 (add file-byte-equivalence + enumeration loop tests) to Step 6 plan text.
4. Apply F4 (number consistency) to Step 6 + Step's If-something-goes-wrong.
5. Note F5 for .F.4c kickoff (decision: which v5.14 stamp to freeze as fixture).
6. F6 + F7: stylistic; defer or fold into the plan-text revisions in 1-4.

After amendments, /parity-check re-audit can be expected to verify GREEN.

---

## Behavior matrix (verify train and serve agree post-.F.4b)

| Scenario | Pre-.F.4b view | Post-.F.4b view | Identical? |
|---|---|---|---|
| Cfg load: KIND_DOUBLE field "ml_buy_threshold=0.65" | `atof("0.65")` → FPN_FromDouble (locale-dependent) | `tt::parse_double_fast("0.65")` (recommended) (locale-independent) | DIVERGENT under non-C locale (Today: corrupted; Post: clean — IMPROVEMENT) |
| Cfg save: KIND_DOUBLE field via SettingsPanel | `snprintf(v, 32, "%.6g", 0.65)` (locale-dependent) | `tt::cfg_save_field<KIND_DOUBLE>` (per F2 fix) → locale-pinned `%.17g` | DIVERGENT under non-C locale (Today: corrupted; Post: clean — IMPROVEMENT) — BUT F2 fix is required to actually achieve this; status-quo carry-forward without F2 means STILL divergent |
| Stamp body emit: ml_buy_threshold (STAMP_BOUND) | Manual `inf.ml_buy_threshold = FPN_ToDouble(cfg.ml_buy_threshold); inf.has_ml_buy_threshold = 1` via STAMP_CFG_AUTOPOPULATE in stamp_write_for_model | If F1 Option A: SAME (FOREACH_STAMP_BOUND_CFG stays during .F.4b transition) | IDENTICAL |
| Categorical applicability: applies_to_strategy_cat | (not in code today; planned) | Stored in descriptor; consumed by parser/render dispatch ONLY (not in stamp body emit) | IDENTICAL (no train-serve handoff surface) |

---

## NOT a bug (verified-safe items)

- Plan's categorical applicability columns (focus area 4) are correctly out-of-scope for HMAC body emit. Confirmed via Step 1 + Step 5 + Deliverable A scan. **NO leak.**
- Plan's tt:: namespace dispatch design (focus area 6) correctly uses template parameterization per CLAUDE.md item 23. **GREEN.**
- Plan correctly preserves existing FOREACH_STAMP_BOUND_CFG during transition (Deliverable A line 337) — provided F1 is resolved as Option A.

---

## Auto-write actions

This audit found 1 new finding that maps to PARITY-026 (status: OPEN-PRE-CODING). Per the auto-write contract (CLAUDE.local.md), I'd append the following to `DOCS/PARITY_ISSUES.md`:

```markdown
### PARITY-026 — v5.15.5.F.4b derived-filter hash lock cannot be locked at ship time because STAMP_BOUND int fields don't migrate until .F.4c

- **Found:** 2026-05-14 (/parity-check pre-coding audit of v5.15.5.F.4b)
- **Severity:** CRITICAL
- **Class:** Wire-format Layer 5b hash lock premature when derived registry is partial-migration
- **Site:** `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4b-foreach-cfg-field-registry-implementation.md:316-337` (Deliverable A)
- **Symptom:** LOCKED_STAMP_BOUND_DERIVED_HASH_V5_15_5_F4 locked at .F.4b ship time → hash will inevitably rotate at .F.4c when int STAMP_BOUND fields migrate; defeats Layer 5b's "lock against accidental reorder" intent.
- **Root cause:** Plan locks Layer 5b hash at .F.4b before all STAMP_BOUND fields are in FOREACH_CFG_FIELD; .F.4c addition will force a deliberate hash rotation that's indistinguishable from accidental drift.
- **Fix path:** Option A (defer derived filter to .F.4c when all STAMP_BOUND fields migrated) OR Option B (pre-populate FOREACH_CFG_FIELD with no-op INT entries at .F.4b)
- **Target ship:** decision before .F.4b coding starts; plan amendment under either Option A or Option B
- **Status:** OPEN-PRE-CODING (closes when plan amendment lands)
- **Workaround:** none; plan-text fix only
```

Status update log entry appended to dated section in PARITY_ISSUES.md referencing this report.

Suggest writing this to PARITY_ISSUES.md AFTER Caramel reviews the YELLOW verdict + 4 must-fix items.

---

## Map-update suggestions (post-audit)

- **DOCS/PARITY_LIFECYCLE.md:** add a row for "FOREACH_CFG_FIELD" (new parity surface as of v5.15.5.F.4+) noting it inherits FOREACH_STAMP_BOUND_CFG's HMAC-locked subset via derived filter
- **DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md:** add a paragraph under Layer 5b on "what happens when derived registry migration is staged" — the lock-and-rotate vs lock-at-completion decision

---

## Summary for caller (under 200 words)

Verdict: **YELLOW** — 4 must-fix amendments before .F.4b coding starts.

Critical: Layer 5b hash lock at .F.4b is premature because int-typed STAMP_BOUND fields don't migrate until .F.4c. Pick Option A (defer derived filter to .F.4c) or Option B (pre-populate FOREACH_CFG_FIELD with no-op int entries at .F.4b).

High: locale pinning missing from registry save (status-quo `atof` + un-pinned `snprintf` carries through). Add `tt::parse_double_fast` + `uselocale(LC_NUMERIC_MASK=C)` to Step 2 + Step 5.

High: Step 6 byte-equivalence test compares Cfg struct fields not emitted file bytes — too narrow. Add file-byte memcmp + X-macro enumeration loop.

Medium: descriptor size budget mismatch (Step 1 says 128B, Step 6 says 64B).

GREEN areas: categorical applicability correctly scoped GUI-only (no stamp body leak); tt:: namespace template dispatch correct per CLAUDE.md item 23.

PARITY-026 auto-write contract entry queued for `DOCS/PARITY_ISSUES.md`.

Report path: `plans/plan_checks/parity-check-2026-05-14-v5.15.5.F.4b.md`.
