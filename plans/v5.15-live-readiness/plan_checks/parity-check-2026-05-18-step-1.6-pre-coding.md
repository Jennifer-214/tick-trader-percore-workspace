# /parity-check report — 2026-05-18 — Step 1.6.X pre-coding (v5.15.5.F.4d.1.B.3 v1.10)

## Plan summary

- **HEAD:** `a406120` (`v5.15.5.F.4d.1.B.3 WIP-checkpoint 2`)
- **Tests:** 4093 PASS / 0 FAIL (per session header)
- **Audit scope:** module:wire-format — focused on Step 1.6.3 + 1.6.4 + 1.6.6.b + 1.6.7 (the SOFT bump) + 1.6.8 cross-tool migration
- **Cross-check baseline:** Layer 7 cross-tool emit discipline (NEW v1.10), Layer 5b structural invariants (live at HEAD), Surface G back-compat (live), post-v5.14.8.A.merged HMAC chain protections
- **Plan file:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.10 (862 lines)
- **Wire-format spec referenced:** `DESIGN_SPECS/wire-format-byte-preservation-discipline.md` (Layers 1-7)

## Stage 0 — DESIGN_PHILOSOPHY preload + DESIGN_SPECS used

Loaded (per skill spec):
- `wire-format-byte-preservation-discipline.md` (all 7 Layers) — primary
- `autopopulate-pattern-for-production-caller-class.md` — Section L production-caller class
- `x-macro-registry-with-presence-dispatch.md` — registry shape
- `pre-post-cfg-registry-split-for-emit-order-preservation.md` — emit ordering
- `metadata-bit-driven-derived-filter-framework.md` § Option E — DERIVED filter framework canonical
- DESIGN_PHILOSOPHY § 5 (Determinism family) — train-serve, wire format, locale pin

---

## Per-focus-area verdicts

| # | Focus area | Verdict | Severity |
|---|---|---|---|
| 1 | Step 1.6.3 — ModelStampResult + StampInferenceCfgInputs struct-gen migration | **GREEN** | — |
| 2 | Step 1.6.4 — Production canonical body emit migration | **YELLOW** | MEDIUM |
| 3 | Step 1.6.6.a — 4 CfgDriftCheck row substitutions to COHORT_GATE_* | **GREEN** | — |
| 4 | Step 1.6.6.b — 15-row STAMP-side rename | **GREEN** | — |
| 5 | Step 1.6.7 — stamp_format_version SOFT bump 1→2 (6 sub-steps) | **YELLOW** | MEDIUM |
| 6 | Step 1.6.8 — stamp_model.sh Layer 7 first canonical | **GREEN** | — |
| 7 | Cross-tool emit-site enumeration (Layer 7 codebase scan) | **GREEN** | — |

---

## Findings by severity

### CRITICAL

(none)

### HIGH

(none — all wire-format-changing edges have plan-body coverage)

### MEDIUM

**MEDIUM-1 — Step 1.6.4 type-migration at struct surface for `inf.<name>` consumers (Approach A unconditional struct-gen).**

- Site: `ModelInference.hpp:1206-1209` (ModelStampResult side) + `:1650-1653` (StampInferenceCfgInputs side)
- Symptom: legacy struct-gen via `FOREACH_STAMP_BOUND_CFG` emits e.g. `double ridge_lambda;` (per registry column at `StampBoundCfgRegistry.hpp:112`). Approach A unconditional struct-gen walks `FOREACH_PER_CORE_CFG_FIELD` filtered by `STAMP_BOUND_CFG_DERIVED` and emits `STORAGE_T <name>;` per `EMIT_PER_CORE_CFG_STRUCT_FIELD` (line 699 of CfgFieldRegistry.hpp). STORAGE_T for these rows is `FPN<F>` per the master registry (CfgFieldRegistry.hpp:576+). After migration, `inf.ridge_lambda` becomes `FPN<F>` (not `double`).
- Wire-format impact: **NONE** — `tt::cfg_emit_field<FPN<F>>` (CfgFieldDispatch.hpp:337-339) auto-handles `is_FPN_v<T>` by emitting via `FPN_ToDouble(src)` + `"%.17g"` (lossless double round-trip). This matches legacy `FOREACH_STAMP_BOUND_CFG` walker's `FPN_ToDouble(cfg.ridge_lambda)` + `"%.17g"` discipline byte-for-byte for the cohort fields.
- Consumer impact: any existing code that reads `inf.ridge_lambda` (or sister stamp-bound-cfg fields) as `double` will fail to compile after struct-gen migration. `/trace-deps chain:ridge_lambda` would catch. Grep at HEAD shows ZERO production consumers reading these fields as `double` directly — only test fixtures (verified via `rg "sr\.ridge_lambda|sr\.thompson_mu_prior|sr\.bandit_blend_ratio" ML_Headers/ Backtest/`). Plan body Step 1.6.2 already enumerates 80 test fixture renames; the type-change would surface during test fixture migration if not handled.
- Cross-ref existing protection: `tt::cfg_drift_compare<T>` and `tt::cfg_populate_inf_field<SrcT, DstT, HasT>` (CfgFieldDispatch.hpp:382-388 comment block) ALREADY handle FPN↔double via FPN_ToDouble (the framework was designed for this asymmetry). DriftCheckRegistry rows ALREADY do `FPN_ToDouble(cfg.ridge_lambda)` for the comparison value, so post-rename the H STAMP-side `h->ridge_lambda` will be `FPN<F>` and the CFG-side will still be `FPN_ToDouble(cfg.ridge_lambda)` — TYPE MISMATCH in the comparison. Plan body Step 1.6.6.b rename ONLY changes the field name; doesn't address the post-rename type at handle side.
- **Recommended fix:** at coding time for Step 1.6.3 + 1.6.6.b, verify `cfg_drift_compare<FPN<F>, double>` or equivalent works. Either:
  - (a) CoreModelZoo handle assignment converts `sr.ridge_lambda` (FPN<F>) → `handle->ridge_lambda` (define handle field as FPN<F>) — natural
  - (b) Or refactor `CfgDriftCheckRegistry.hpp` post-rename rows to use `FPN_ToDouble(h->ridge_lambda)` to keep comparison double-against-double — but this LOSES FPN precision benefit
- Verdict: plan body Step 1.6.6.b should include sub-step "verify handle struct field types match post-Approach-A struct types OR add FPN_ToDouble wrap at gate expr". **Capture as plan body annotation, not a blocker.** Pattern: `feedback_recheck_designspecs_on_pushback` — this is a type-binding mirror surface that auto-flows the wrong way if not explicitly handled.

**MEDIUM-2 — Step 1.6.4.a byte-identity assertion: fixture is _expected canonical body_, not _saved bytes from .B.2 walker_.**

- Site: plan body Step 1.6.4.a sub-step says "Add explicit byte-identity assertion at Step 1.6.4 test fixture that verifies canonical body output bytes EXACTLY match expected (compile-time string literal of canonical body emitted by framework walker for known cfg state)."
- Risk: the "expected" string literal in the test fixture is hand-written by the developer — it embodies the v2 wire format intent (master-registry order, unprefixed keys, %.17g floats). It does NOT verify that the framework walker's output matches the legacy `.B.2` walker's output (which would be the v1 wire format with `inference_cfg_*` prefixes + FOREACH_STAMP_BOUND_CFG row order). The plan body has previously been explicit (Decision F.2) that wire bytes intentionally differ for v2.
- Wire-format impact: the byte-identity assertion catches REGRESSION (v2 walker output changes accidentally after migration), but doesn't catch the migration itself producing incorrect v2 bytes. Layer 5b structural invariants (`I1-I5` at `tests/wire_format_invariants.hpp`) provide the structural check (line count == popcount, no comma decimals, per-core before global) — already in place at HEAD.
- Recommended: plan body Step 1.6.4.a wording change — emphasize this is a **REGRESSION lock**, not a v1↔v2 byte equivalence lock. Make explicit that the fixture string is "expected v2 canonical body" + cross-reference Step 1.6.7.5 (v1 LOAD test) as the v1 back-compat verification.
- Verdict: 1-line wording clarification; not a coding-time blocker.

**MEDIUM-3 — Step 1.6.7 ordering hazard between sub-steps 1.6.7.1-1.6.7.5 vs Step 1.6.4 production walker migration.**

- Per plan body Step 1.6.7 sub-step ordering (v1.3 reordering): 1.6.7.0 (DESIGN_SPEC procedure DRAFT) → 1.6.7.1 (extract literal to STAMP_FORMAT_VERSION_CURRENT) → 1.6.7.2 (MAX_SUPPORTED parser bounds) → 1.6.7.3 (bump CURRENT 1→2) → 1.6.7.4 (parser back-compat for 15 legacy keys) → 1.6.7.5 (v1 LOAD test) → 1.6.7.6 (TECH_DEBT-101 entry).
- Concern: at Step 1.6.7.3 (bump CURRENT 1→2), the EMIT walker is still emitting v1 wire bytes (Step 1.6.4 not landed yet per Steps-sequencing matrix). Engine emits stamps marked `stamp_format_version=2` BUT containing v1 wire keys (prefixed `inference_cfg_*`). Any stamp written between Step 1.6.7.3 landing and Step 1.6.4 landing is structurally malformed (version label v2, content shape v1).
- Mitigation in plan: Steps sequencing matrix at line 722+ shows Step 1.6.4 BLOCKS-AFTER Step 1.6.3 + Step 0.5b, and Step 1.6.7 sequenced AFTER Step 1.6.4 per "BUILD-FORCED" claim — verify build-forcing is real. **Action:** verify at coding time Step 1.6.7.3 lands AFTER Step 1.6.4 (production walker migration). If not BUILD-FORCED, plan body sub-step ordering can produce malformed transient stamps during a partial coding session.
- Recommended: plan body Step 1.6.7 add explicit sub-statement: "Step 1.6.7.3 (version bump) MUST land in same commit as or AFTER Step 1.6.4 (canonical body emit migration). Single-commit verification: build/test stamp emission between 1.6.7.3 and 1.6.4 produces consistent v2 (matched version label + unprefixed keys)."
- Verdict: ordering hazard is real but mitigated by COMMIT-TIME single-commit landing. Annotate plan body for explicitness.

**MEDIUM-4 — Step 1.6.7.4 parser back-compat closed-set X-macro: KEY COUNT MISMATCH between plan body and Decision D scope.**

- Plan body has multiple statements about the count:
  - Decision F (F.2) line 138: "closed set of 9 legacy prefixed keys; not recurring registry"
  - Step 1.6.7.4 line 540: "Parser back-compat layer for 9 legacy prefixed wire keys"
  - Decision D line 89: "DELETE 15 prefixed POST_CFG entries (scope EXPANDED 5 → 9 → 10 → 15)"
  - Step 1.6.2 line 409: "Wire-key change: 15 keys total"
  - Step 1.6.7.5 fixture pseudocode line 559-567: enumerates 9 keys (`bandit_algorithm`, `thompson_mu_prior/precision_prior/precision_obs/exp3_blend_alpha`, `ml_tp_pct/sl_pct/barrier_blend_mode/per_horizon_barrier_blend`) — but Decision D's 15-entry scope includes 5 additional fields from `.B.3` v1.6 expansion (confidence_threshold_scale, barrier_gate_enabled, confidence_hard_block_threshold, fee_rate_maker, fee_rate_taker) which are LEGITIMATE v1 wire-key shapes too.
- Wire-format impact: if parser back-compat layer enumerates only 9 keys (as Decision F text + Step 1.6.7.5 fixture suggest), the 5 additional fields' v1 wire keys (`inference_cfg_confidence_threshold_scale=` etc.) will be UNKNOWN KEYS to the back-compat parser. They fall through to "unknown key, silently ignored" per Surface G discipline → drift check sees has_<field>=0 → reads cfg default → drift fires falsely OR drift check skipped (gate uses STAMP_HAS group bit).
- Verification: open the v1 stamp written by `.B.2` engine. Per HEAD `StampBoundModelConstRegistry.hpp:281-302` (POST_CFG entries), the `.B.2` walker emits ALL 15 prefixed keys (including the 5 v1.6-expansion candidates: `inference_cfg_confidence_threshold_scale=`, `inference_cfg_barrier_gate_enabled=`, `inference_cfg_confidence_hard_block_threshold=`, `inference_cfg_fee_rate_maker=`, `inference_cfg_fee_rate_taker=`). v1 stamps therefore CONTAIN these 5 keys; the back-compat parser MUST recognize them.
- Recommended fix: Step 1.6.7.4 X-macro `FOREACH_LEGACY_PREFIXED_KEY` MUST enumerate ALL 15 keys (matching Decision D scope), not 9. Plan body update needed at Step 1.6.7.4 line 540 + Step 1.6.7.5 fixture enumeration (line 559-567 currently shows only 9 keys; add the missing 5 to make the fixture realistic). Decision F (F.2) line 138 likewise — change "9 legacy prefixed keys" → "15 legacy prefixed keys".
- Verdict: **plan body wording mismatch — landed by Decision D scope expansion to 15, but Decision F + Step 1.6.7 sub-steps still reference earlier 9-count.** Easy fix; capture as plan body amendment before coding.

### LOW

**LOW-1 — Step 1.6.6.b post-rename type-binding annotation needed for handle vs cfg-side asymmetry.**

- Related to MEDIUM-1 above. Plan body Step 1.6.6.b enumerates the 15 STAMP-side field rename lines (CfgDriftCheckRegistry.hpp:236-311) but does not annotate the corresponding handle field type post-migration. The CFG-side gate expressions retain `FPN_ToDouble(cfg.<field>)` which is correct (Layer 3 fmt discipline preserves wire bytes). The STAMP-side `h-><field>` direct access requires handle struct field type to match struct-gen output. If Approach A produces `FPN<F> ridge_lambda;` on the handle, the comparison is `cfg_drift_compare<FPN<F>>(h->ridge_lambda, FPN_ToDouble(cfg.ridge_lambda))` — TYPE MISMATCH on the second arg.
- Mitigation: `cfg_drift_compare` may auto-promote (compiler implicit double→FPN<F>). Verify at coding time + add explicit FPN_ToDouble wrap on STAMP-side handle access in CfgDriftCheckRegistry rows to preserve double-against-double comparison semantics: `FPN_ToDouble(h->ridge_lambda)` instead of `h->ridge_lambda`. **OR** leave as-is and let cfg_drift_compare promote — verify EPS_DEFAULT semantics preserved.
- Verdict: documentation-only annotation in plan body Step 1.6.6.b; coding-time decision.

**LOW-2 — Step 1.6.8 Class B (line 221 stamp_format_version=1→2 literal bump) needs verification that engine's STAMP_FORMAT_VERSION_CURRENT change in same commit.**

- Plan body Step 1.6.8 Class B notes cross-reference comments at both sites (`tools/stamp_model.sh:221` + `ML_Headers/ModelInference.hpp` STAMP_FORMAT_VERSION_CURRENT). Verification at HEAD: ModelInference.hpp:1757 emits `"stamp_format_version=1\n"` as a hardcoded literal currently — Step 1.6.7.1 will extract to a constant. Step 1.6.7.3 bumps to 2. Step 1.6.8 Class B bumps the bash literal.
- Risk: if Step 1.6.7.3 lands in commit A but Step 1.6.8 Class B lands in commit B, between A and B the bash CLI emits v1 stamps that read on v2 engine (back-compat parser handles legacy wire keys, so loads). After commit B, bash CLI emits v2 stamps. Asymmetric — bash CLI is one ship behind. Plan body ship-close instructions should mandate single-commit landing per Layer 7 sync discipline.
- Verdict: enforce single-commit landing for Step 1.6.7.3 + Step 1.6.8 Class B. Already implied by Layer 7's "wire-format ship-close checklist" but call it out in plan body Step 1.6.8.

**LOW-3 — Plan body fixture (Step 1.6.7.5) doesn't include 5 v1.6-expansion keys.**

- Same shape as MEDIUM-4. The plan body's pseudo-fixture string literal at line 552-569 omits 5 of the 15 keys. As a non-blocking issue: if Caramel uses the plan body fixture as-is for coding, the v1 LOAD test misses validation for confidence_threshold_scale, barrier_gate_enabled, confidence_hard_block_threshold, fee_rate_maker, fee_rate_taker round-trip.
- Recommended: plan body Step 1.6.7.5 fixture pseudocode add the missing 5 keys before coding.

### DOCUMENT-ONLY

**DOC-1 — Layer 7 first canonical reference works as designed.**

The Layer 7 cross-tool emit-site enumeration discipline (NEW at v1.10 per Meta-gap M2) is correctly applied in Step 1.6.8 expansion. All 4 classes (A migrate / B version literal bump / C orphan delete / D preserve-with-comment) are enumerated with per-site disposition + cross-reference comments + Layer 7 first canonical reference at Step 1.6.8. Cross-grep `tools/` from this audit confirms ALL stamp_format_version + inference_cfg_* literals in tools/stamp_model.sh are captured by the plan body's per-class enumeration (no additional sites). Cross-grep beyond tools/ (e.g., `engine.cfg.example:784`, comment-only refs in 7 files) is acceptable per Layer 7 § per-site disposition "PRESERVE WITH CROSS-REF COMMENT" — historical refs, not consumer/emit code.

---

## Cross-cutting concerns

### Single-cut fix: parser back-compat key-count alignment

MEDIUM-4 + LOW-3 are the same finding at two places — fix once at plan body Step 1.6.7.4 + Step 1.6.7.5 fixture (and Decision F (F.2) wording) to align with Decision D 15-entry scope. ~3-line plan body update; closes both.

### Single-cut fix: type-binding annotation across Step 1.6.3 + 1.6.6.b

MEDIUM-1 + LOW-1 are paired (struct-side type-change ↔ drift-check-side type-binding). Both fix at coding-time verification step within Step 1.6.3 / 1.6.6.b: build verify after struct-gen migration + before drift-check rename catches the type mismatch via cfg_drift_compare template instantiation. Already covered by plan body's claim of "build verify after each field" in the cohort migration procedure (line 449-462). Verify in postmortem that this caught any drift-comparison type issues.

---

## Behavior matrix (verify train and serve agree for default cfg)

| Scenario | Trainer view (v1 fixture / .B.2 emit) | Engine view (.B.3+ parser) | Identical wire bytes? |
|---|---|---|---|
| v1 stamp loads on .B.3 engine | Hand-written canonical body with 15 prefixed `inference_cfg_*` keys (from fixture; or actual .B.2 emit) | Parser back-compat layer (Step 1.6.7.4) maps prefixed key → unprefixed struct field | n/a (v1 wire bytes preserved; engine maps internally) — verified by Step 1.6.7.5 LOAD test |
| .B.3+ engine emits v2 stamp | (none — fresh stamp) | Framework walker `populate_stamp_cfg_from_derived` emits unprefixed keys in master-registry order, %.17g floats, locale-pinned | v2 canonical bytes; LOCKED via Layer 5b structural invariants I1-I5 |
| Mixed v1 + v2 stamps load on .B.3+ engine | Both load via Surface G + back-compat parser | Engine processes identically (drift check fires correctly for each) | n/a (intentional asymmetry; SOFT bump per Decision F.2) |
| HMAC chain for v1 stamp on .B.3+ engine | HMAC computed over v1 canonical body bytes (the pre-rename emit) | Engine doesn't re-emit; HMAC verification uses original v1 bytes | YES — HMAC verified against original v1 bytes, NOT re-emitted v2 |
| HMAC chain for v2 stamp on .B.3+ engine | Engine emits v2 canonical body bytes + HMAC | Engine re-emits via same walker for verification; bytes identical | YES — locked via Layer 5b I1-I5 invariants |

**Verdict on HMAC chain:** GREEN. SOFT bump preserves HMAC chain for legacy v1 stamps (engine doesn't re-emit; original bytes verified). New v2 emit is byte-deterministic per Layer 3 + Layer 5b. No HMAC drift risk.

---

## HMAC chain risk assessment per Step

| Step | HMAC chain risk | Mitigation |
|---|---|---|
| 1.6.3 (struct-gen) | NONE — struct-gen doesn't touch emit/parse | n/a |
| 1.6.4 (emit walker migration) | LOW — wire bytes intentionally change for v2; v1 HMAC unaffected (engine doesn't re-emit v1) | Layer 5b structural invariants I1-I5 at HEAD; Step 1.6.4.a byte-identity assertion REGRESSION LOCK |
| 1.6.6.a (4 COHORT_GATE substitutions) | NONE — substitutes the gate predicate; comparison value + STAMP-side handle access UNCHANGED at line 272 etc. | byte-equivalent predicate semantic preserved |
| 1.6.6.b (15 STAMP-side renames) | LOW — handle field type may shift FPN<F> vs double (MEDIUM-1) but cfg_drift_compare auto-handles | verify at coding time + cfg_drift_compare<T> template instantiation |
| 1.6.7.1-3 (literal extract + bump) | NONE — version label is on the wire, doesn't affect HMAC (HMAC over body MINUS sig line) | sister to existing v5.9 stamp_format_version pattern |
| 1.6.7.4 (parser back-compat 15 keys) | NONE — parser-only addition; doesn't affect emit | closed-set X-macro; TECH_DEBT-101 deprecation tracked |
| 1.6.7.5 (v1 LOAD test) | NONE — test only | self-contained fixture per Layer 4 round-trip discipline |
| 1.6.8 (stamp_model.sh migration) | NONE — bash CLI emits v2 bytes matching engine v2 emit | Layer 7 cross-tool sync discipline; reciprocal cross-ref comments |

**Overall HMAC chain verdict:** GREEN. SOFT bump path preserves HMAC chain across v1 stamps continuously. v2 emit is byte-deterministic via Layers 1-5b.

---

## NOT a bug (verified-safe items)

- **Master cfg field type vs FOREACH_STAMP_BOUND_CFG type asymmetry** — `tt::cfg_emit_field<FPN<F>>` handles FPN→double via `FPN_ToDouble(src)` + `"%.17g"` matching legacy walker bytewise. CfgFieldDispatch.hpp:337-339 confirmed.
- **bandit_algorithm integer format (`%d` vs `%lld`)** — for `int` values, both produce identical decimal strings. Verified at all consumer sites.
- **trading_mode uint8_t vs int storage** — legacy walker emits via `(int)cfg.trading_mode` + `"%d"`; framework walker emits via `static_cast<unsigned long long>(src)` + `"%llu"` for uint8_t. For values 0-2 (valid trading_mode range per range BOOL), both produce `"0"` / `"1"` / `"2"` — identical wire bytes.
- **bitmap-flag emit via ternary normalization (BITMAP_BIT rows)** — both legacy walker and framework `X_STAMP_CFG_POPULATE_ML_CFG_FLAG` walker normalize via `BITMAP_IS_SET(...) ? 1 : 0` + `"%d"` / `"%s=%d\n"`. Bytewise identical.
- **Cross-tool emit-site enumeration scope** — `rg "stamp_format_version=|inference_cfg_" tools/` covers only `tools/stamp_model.sh`. No other tool emit sites found at HEAD.
- **Layer 5b structural invariants (I1-I5) at HEAD** — `tests/wire_format_invariants.hpp` already supports dual-mask context (per_core + global masks); ready for Step 1.7 invocation.

---

## Suggested plan body amendments (before coding)

| # | Amendment | Section | Effort |
|---|---|---|---|
| 1 | Align Decision F (F.2) + Step 1.6.7.4 + Step 1.6.7.5 fixture to 15-key scope (MEDIUM-4 + LOW-3) | Decision F line 138, Step 1.6.7.4 line 540, Step 1.6.7.5 fixture line 552-569 | ~5 min |
| 2 | Step 1.6.4.a wording clarification (regression-lock semantic; MEDIUM-2) | Step 1.6.4.a line 504 | ~2 min |
| 3 | Step 1.6.7.3 + Step 1.6.4 single-commit landing requirement (MEDIUM-3) | Step 1.6.7.3 line 539 | ~2 min |
| 4 | Step 1.6.6.b post-rename type-binding annotation (MEDIUM-1 + LOW-1) | Step 1.6.6.b line 514+ | ~5 min |
| 5 | Step 1.6.8 single-commit landing for engine + bash literal bump (LOW-2) | Step 1.6.8 line 600+ | ~2 min |

Total amendment effort: ~15 min plan body update.

---

## PARITY_ISSUES.md auto-write (per skill spec)

No NEW `PARITY-NNN` entries warranted. All findings are plan-body wording issues (resolvable pre-coding) or type-binding annotations (resolvable at coding-time via existing build-verify cadence). Existing PARITY ledger entries unchanged.

---

## Inflection assessment at v1.10 pre-coding

Per `feedback_iteration_spiral_signals_audit_meta_gap`:

This audit found:
- 4 MEDIUM (M-1: type asymmetry annotation; M-2: regression-lock semantic; M-3: ordering hazard; M-4: key-count mismatch)
- 3 LOW (type-binding annotation, single-commit landing, fixture key-count parallel)
- 1 DOCUMENT-ONLY (Layer 7 application works correctly)
- 0 CRITICAL / HIGH

The findings are **detail-level plan-body refinements** (wording mismatches, sub-step ordering callouts, type-binding annotations) — NOT structural gaps and NOT systemic.

**Inflection signal:** Layer 7 + Layer 5b + Surface G work correctly at HEAD. The framework infrastructure protections are sufficient. The remaining findings are pre-coding plan-body refinements (15-min update) + coding-time build-verify catches (already part of plan body procedure).

This audit confirms: **Step 1.6.X migrations are wire-format-safe** under the planned SOFT bump + 15-key back-compat layer + Layer 5b structural invariants + Layer 7 cross-tool sync. The 4 MEDIUM findings are LOAD-BEARING for plan body accuracy but do NOT introduce wire-format drift; they're documentation hygiene.

**Verdict for v1.10 plan body progression to ACTIVE coding:** GREEN-on-amendment (5 plan body amendments above resolve all MEDIUM + LOW; coding can start after operator triage).
