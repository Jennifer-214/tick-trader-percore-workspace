# /parity-check report — 2026-05-17 — v5.15.5.F.4d.1.B.3 (Legacy empty-out) plan body

**Plan body audited:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.2 DRAFT (435 lines)
**Engine HEAD:** `9b62a72` (v5.15.5.F.4d.1.B.2 ship close)
**Auditor scope:** `current` per `audit-scope-taxonomy.md` — plan body + 5 production walker sites + framework template fns + stamp emit/parse paths
**DESIGN_SPECS preloaded:** `wire-format-byte-preservation-discipline.md` (Layer 5b structural-invariants revised 2026-05-16) · `autopopulate-pattern-for-production-caller-class.md` (3 active applications) · `x-macro-registry-with-presence-dispatch.md` (Y3 dispatch + derived filter sister pattern) · `pre-post-cfg-registry-split-for-emit-order-preservation.md`
**Cross-check baseline:** Post-v5.15.5.F.4d.1.B.2 protections inventory + PARITY_ISSUES.md PARITY-001..025

---

## Audit verdict: **YELLOW** — proceed with 3 HIGH plan amendments + 4 MED clarifications + 1 CRIT structural blocker
that fully resolves before pre-coding tag

5 CRIT findings — 1 ship-blocker (CRIT-1 wire-byte order DISCONTINUITY undocumented as STRICT-only failure mode), 4 false-positive resolved by cross-ref to .B.2 ship work (already protected). 3 HIGH — Layer 5b invariants generator absent at HEAD; framework byte-order vs legacy ordering documented mismatch; Decision E option matrix structurally incomplete. 4 MED — fixture file missing at HEAD; bash CLI emit (`tools/stamp_model.sh`) not in scope; populate_stamp_cfg_from_derived caller plumbing under-specified at Step 1.6.4; bandit_algorithm gate semantic divergence under Decision E.

**Going-forward action:** Decision E triage with Caramel FIRST (controls plan reshape). Then CRIT-1 + HIGH-1 + HIGH-2 + HIGH-3 amendments to v1.2 → v1.3 BEFORE pre-coding tag fires (Step 6 of pickup workflow).

---

## Findings by severity

### CRIT

#### CRIT-1 — Wire-byte order DISCONTINUITY across stamp_format_version 1 → 2 is INTENDED but plan Step 5 STRICT/LENIENT decision misframes the failure-mode contract

**File:line citations:**
- Legacy emit (current production): `ML_Headers/StampBoundCfgRegistry.hpp:99-178` — `FOREACH_STAMP_BOUND_CFG` 25-row macro body, hand-crafted order (ridge group → composite group → winsor → exit_blender_mode → softrisk group → ml_buy_threshold → gap_acceptable_threshold → bandit/thompson group → trading_mode)
- Framework walker (target): `MemHeaders/CfgGateRegistry.hpp:258-308` — `populate_stamp_cfg_from_derived<F>` walks PER_CORE first → GLOBAL second → ML_CFG_FLAG third in master-registry declaration order
- Plan Step 1.6.4: `2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md:220` — "Wire byte order changes from legacy hand-crafted order to master-registry declaration order. THIS IS THE WIRE-FORMAT-CHANGING STEP — couples with Step 1.6.7 stamp_format_version bump."
- Plan Step 5 (decision): `:251-254` — "STRICT (refuse v1 stamps) vs LENIENT (warn + skip cfg drift)"

**Observed vs expected:**

The plan correctly identifies that the framework walker produces a DIFFERENT byte order than legacy (causing the stamp_format_version=1 → 2 bump). But the per-byte enumeration of the change is NOT in the plan body. Concrete diff:

**Legacy v1 byte order (FOREACH_STAMP_BOUND_CFG):**
```
ridge_within_horizon=...\n        # row 1 (ml_cfg_flags BITMAP_BIT)
ridge_across_horizons=...\n        # row 2 (ml_cfg_flags BITMAP_BIT)
ridge_lambda=...\n                 # row 3 (per-core scalar)
ridge_cost_penalty=...\n           # row 4
ridge_min_ic_floor=...\n           # row 5
confidence_composite_enabled=...\n # row 6 (ml_cfg_flags BITMAP_BIT)
confidence_freshness_tau_secs=...\n # row 7 (per-core scalar)
confidence_capacity_target_dollars=...\n  # row 8
confidence_capacity_kappa=...\n    # row 9
confidence_rmse_baseline=...\n     # row 10
winsor_pct_low=...\n               # row 11
winsor_pct_high=...\n              # row 12
exit_blender_mode=...\n            # row 13 (ml_cfg_flags BITMAP_BIT)
risk_degradation_curve=...\n       # row 14
risk_full_size_threshold=...\n     # row 15
risk_min_size_threshold=...\n      # row 16
risk_min_size_pct=...\n            # row 17
ml_buy_threshold=...\n             # row 18
gap_acceptable_threshold=...\n     # row 19
bandit_algorithm=...\n             # row 20
thompson_mu_prior=...\n            # row 21
thompson_precision_prior=...\n     # row 22
thompson_precision_obs=...\n       # row 23
thompson_exp3_blend_alpha=...\n    # row 24
trading_mode=...\n                 # row 25
```

**Framework v2 byte order (populate_stamp_cfg_from_derived: per-core first, then global, then ML_CFG_FLAG):**
```
ml_buy_threshold=...\n             # was row 18 legacy
ridge_lambda=...\n                 # was row 3
ridge_cost_penalty=...\n           # was row 4
ridge_min_ic_floor=...\n           # was row 5
winsor_pct_low=...\n               # was row 11
winsor_pct_high=...\n              # was row 12
confidence_freshness_tau_secs=...\n # was row 7
confidence_capacity_target_dollars=...\n  # was row 8
confidence_capacity_kappa=...\n    # was row 9
confidence_rmse_baseline=...\n     # was row 10
thompson_mu_prior=...\n            # was row 21
thompson_precision_prior=...\n     # was row 22
thompson_precision_obs=...\n       # was row 23
bandit_algorithm=...\n             # was row 20
thompson_exp3_blend_alpha=...\n    # was row 24
risk_degradation_curve=...\n       # was row 14
risk_full_size_threshold=...\n     # was row 15
risk_min_size_threshold=...\n      # was row 16
risk_min_size_pct=...\n            # was row 17
trading_mode=...\n                 # was row 25 (now in GLOBAL block)
gap_acceptable_threshold=...\n     # was row 19 (now in GLOBAL block)
confidence_composite_enabled=...\n # was row 6 (now in ML_CFG_FLAG block)
ridge_within_horizon=...\n         # was row 1
ridge_across_horizons=...\n        # was row 2
exit_blender_mode=...\n            # was row 13
```

**ALL 25 rows reorder.** No two stamps with the same field values produce the same canonical body bytes across v1 → v2. HMAC chain is fully broken (intentionally) for ALL legacy stamps, NOT just the 5 prefixed-only fields.

**Per `wire-format-byte-preservation-discipline.md` Layer 4 + Layer 5 + 6:** STRICT v1 stamp refusal is the structurally-correct path — this is exactly the "BREAKING change → version bump" case that v(N) → v(N+1) is reserved for per § "Schema versioning every change" anti-pattern note. LENIENT mode would silently load v1 stamps without cfg drift check, which is `Surface G discipline back-compat` precedent BUT silently disables HMAC chain integrity for all 25 cfg fields — operator visibility is degraded.

**Recommended fix (CRIT-1, blocker):** Plan Step 5 currently surfaces STRICT/LENIENT as an open decision. Per parity discipline + wire-format spec § Layer 4 (round-trip HMAC test must pass; failure forces deliberate update), the auto-pick is STRICT. Plan body should:
1. Auto-pick STRICT per `feedback_motivated_collaborator_for_caramel` + `feedback_no_defer_for_effort` — operator workflow (regenerate stamps post-`.B.3` ship) is well-documented in `Stamp_AssembleAndEmit` + `tools/stamp_model.sh` path; LENIENT mode silently disables HMAC chain integrity which is more costly than the regen flow.
2. Add explicit "BREAKING change" tag to Step 1.6.7.2 (bumping CURRENT 1 → 2 IS a breaking change — clarify in version-bump rationale).
3. Plan body MUST enumerate the byte-order diff (the 25-row reshuffling above) so future code archaeology can find the SHA-256 baseline regeneration justification without re-deriving it.
4. Couple with FEATURE_LOOKUP entry (already in scope per plan line 394-395): "**Gotchas: ALL v1 stamps must be regenerated on `.B.3+` engine; no field values change but byte order does.**" Add OPERATOR ACTION header to FEATURE_LOOKUP entry per the `tick-trader-percore-workspace/FEATURE_LOOKUP.md` discipline.

**Effort estimate:** 20 min plan body amendment + 10 min FEATURE_LOOKUP draft.

**Cross-ref existing protection:** No protection at HEAD — the byte-order diff is intentional and NEW at `.B.3`. PARITY_ISSUES.md has no matching entry (this is a deliberate wire format change paired with the version bump; not a bug to log).

---

### HIGH

#### HIGH-1 — Layer 5b structural-invariant generator (`DERIVED_FILTER_DECLARE_WIRE_FORMAT_TWO_SOURCE`) DOES NOT EXIST at HEAD; plan Step 4 CI Checks 9-12 don't cover canonical-body invariant testing

**File:line citations:**
- DESIGN_SPECS Layer 5b spec: `tick-trader-percore-workspace/DESIGN_SPECS/wire-format-byte-preservation-discipline.md:194-275` — describes the framework macro `DERIVED_FILTER_DECLARE_WIRE_FORMAT_TWO_SOURCE(NAME, SOURCE_FOREACH, METADATA_BIT, BITMAP_SOURCE, BITMAP_FIELD)` + `STAMP_BOUND_CFG_run_generic_invariants()` runner with 5 invariants (I1 line-count vs flagged-count, I2 `<name>=<value>\n` pattern, I3 no comma decimals, I4 per-row name appears EXACTLY when bit set, I5 per-core descriptors emit before global)
- Search verification (no hits): `rg "DERIVED_FILTER_DECLARE_WIRE_FORMAT|run_generic_invariants" CoreFrameworks/ MemHeaders/ ML_Headers/` returns ZERO results in the engine
- Plan Step 4 CI Checks 9-12 (`:246-249`) covers metadata-bit coverage (every flagged source row has a derived filter consumer) but does NOT add the canonical-body invariant runner test

**Observed vs expected:**

DESIGN_SPECS § Layer 5b says: *"first canonical implementation at v5.15.5.F.4d.1.A"*. But searching the engine for the framework macro returns zero hits. The DESIGN_SPECS spec is published (Stage 3 ACTIVE per CLAUDE.local.md) but the engine implementation was NOT shipped at `.A`. This is a documentation-vs-code drift surface that affects `.B.3` because:

(a) `.B.3` is the FIRST ship that produces non-zero canonical body bytes from the framework walker (the v(N) → v(N+1) wire-format bump). Without Layer 5b structural invariants, ALL 5 drift vectors (walker skip bug, format-string drift, locale leak, filter logic inversion, per-core-before-global regression) can land silently at `.B.3` and only surface much later (when an operator notices stamps not loading right).

(b) Plan Step 1.6.4 says "Wire byte order changes from legacy hand-crafted order to master-registry declaration order" but provides NO automated verification that the order matches the framework walker's actual emit. Per DESIGN_SPECS Layer 4 (round-trip HMAC test) — this is the obvious gap.

(c) DESIGN_SPECS § Layer 5b describes the discipline as "first application at `.A`" — which never happened. This is BOTH a DESIGN_SPEC drift gap (the description is aspirational, not codified) AND a plan body gap (`.B.3` should land the Layer 5b implementation alongside the legacy empty-out OR explicitly defer the discipline with rationale).

**Recommended fix:** Plan body amendment v1.2 → v1.3, options:

Option (a): Add Step 1.7 "Layer 5b structural-invariant framework implementation" — implement `DERIVED_FILTER_DECLARE_WIRE_FORMAT_TWO_SOURCE` macro per DESIGN_SPECS spec + 5 invariant stubs + the `STAMP_BOUND_CFG_run_generic_invariants()` runner. ~3-4h. Auto-picks per `feedback_motivated_collaborator_for_caramel` — Layer 5b is the documented Class 18 mirror close at the wire-format anti-regression layer; deferring it leaves canonical-body shape unprotected at the moment of the highest-risk byte change.

Option (b): Defer Layer 5b implementation to `.B.4` (would need a NEW sub-ship) — `.B.3` lands the wire-format change without the structural-invariants safety net. Per `feedback_no_defer_for_effort` + `feedback_consult_on_audit_findings`, document explicit rationale (e.g., "v1 → v2 transition needs to ship before paper-test; Layer 5b is a structural fix that lands at `.B.4` before any subsequent v2 → v3 bump"). Add explicit TECH_DEBT entry + new sub-ship target.

Option (c): Amend DESIGN_SPECS § Layer 5b to clarify status (Stage 2 DRAFT, not Stage 3 ACTIVE), and target Layer 5b first canonical for a future ship after `.B.3` proves the v1 → v2 bump procedure. Couples with plan body Step 6 DESIGN_SPECS spec-body cleanup.

**Auto-pick recommendation:** option (a). The v1 → v2 wire-format bump is the canonical moment for Layer 5b's first application (DESIGN_SPECS literally says "first application at v5.15.5.F.4d.1.A" — but that didn't happen at `.A`, and `.B.3` is the *real* first non-zero canonical-body emit moment). Folding Layer 5b implementation INTO `.B.3` is structurally-correct + sister discipline; deferring forces a follow-up ship for the same surface.

**Effort estimate:** ~3-4h implementation; Layer 5b structural invariants spec at DESIGN_SPECS § Layer 5b is detailed enough to implement directly. Plan body amendment to add Step 1.7: ~20-30 min.

**Cross-ref existing protection:** Layer 4 round-trip HMAC test would catch this only if a v1 fixture exists (HIGH-2 finding below) AND `.B.3` adds a round-trip test against v2 emit. Plan Step 5 doesn't enumerate this.

---

#### HIGH-2 — `tests/fixtures/v5_14_stamp_canonical.bin` referenced in plan Step 5 does NOT exist at HEAD; fixture must be created BEFORE Step 1.6.7.3 v1 stamp failure-mode test can land

**File:line citations:**
- Plan Step 5 (`:251-254`): "Fixture file: `tests/fixtures/v5_14_stamp_canonical.bin` (committed if not already)" + "Pre-migration v5.14 stamps load + FAIL with `stamp_format_version=1 < MAX_SUPPORTED=2` operator-visible error"
- Plan Step 1.6.7.3 (`:230`): "synthesize v1 stamp with old prefixed wire keys; load on `.B.3` engine; verify operator-visible error references `stamp_format_version` mismatch"
- Engine HEAD verification: `ls tests/fixtures/` returns `No such file or directory`

**Observed vs expected:**

Plan body assumes the fixture exists ("committed if not already"). Verification confirms: no `tests/fixtures/` directory exists; no v5.14 canonical stamp fixture is in the codebase. The fixture must be CREATED at this ship — not just "committed if not already".

The two distinct test fixtures needed at `.B.3`:

1. **v1 stamp fixture (legacy format)** — synthesized canonical body bytes from `.B.2` engine emitting a stamp under known cfg values, captured pre-Step-1.6.4-migration. Used by Step 1.6.7.3 v1 stamp failure-mode test (STRICT mode refusal verification). Also needed for round-trip HMAC test per `wire-format-byte-preservation-discipline.md` Layer 4.

2. **v2 stamp fixture (framework format)** — synthesized canonical body bytes from `.B.3` engine post-Step-1.6.4-migration. Used by Layer 5 snapshot test (FNV-1a-64 hash; locked at `.B.3` close per `wire-format-byte-preservation-discipline.md` Layer 5). Verifies future code changes don't silently reorder rows.

Plan body Step 5 mentions only (1). (2) is missing.

**Per `wire-format-byte-preservation-discipline.md` Layer 4 + 5:** BOTH fixtures are LOAD-BEARING for the v(N) → v(N+1) bump procedure. Without (2), future PRs that re-reorder master-registry rows would land silently at `.C` / `.D` / future ships without anyone noticing.

**Recommended fix:** Plan body Step 5 amendment:

1. **Add explicit "fixture creation procedure" sub-step BEFORE Step 1.6.7.3 v1 fixture failure-mode test.** Procedure: (a) on `.B.2` engine + known synthetic cfg, build `engine` binary + run stamp-emit harness on a synthetic `StampInferenceCfgInputs` populated via AUTOPOPULATE; (b) capture canonical body bytes into `tests/fixtures/v5_14_stamp_canonical.bin`; (c) commit fixture with the same commit that lands `.B.3` initial work.
2. **Add Step 5b — v2 stamp fixture + Layer 5 FNV-1a-64 snapshot hash lock.** After `.B.3` framework walker shipped, synthesize a v2 stamp + commit + lock hash in a test file (mirror of v5.14.8.A.7's "registry canonical body output hash unchanged" test pattern).
3. **Add explicit Layer 4 + Layer 5 test coverage in Step 9 build-verify section.** Tests should assert: (a) v1 fixture's HMAC verifies against legacy v1 emit at `.B.2` engine (regression-anchor); (b) v2 fixture loads + parses correctly on `.B.3` engine; (c) v2 fixture's Layer 5 FNV-1a-64 hash matches locked constant.

**Effort estimate:** ~1-2h fixture synthesis + 30 min plan body amendment. Fixture creation is mechanical once the harness exists (`tools/stamp_model.sh` may already cover the bash CLI emit case — see MED-1 below).

**Cross-ref existing protection:** Plan body mentions the `.B.2` Discovery 6 "Decision D mechanism 1 wire format change" via Decision D pickup — but the fixture-creation procedure for the bump is not enumerated. PARITY_ISSUES.md has no matching entry.

---

#### HIGH-3 — Decision E (CfgDriftCheck consolidation) option matrix is STRUCTURALLY INCOMPLETE — semantic divergence at bandit_algorithm gate is documented but the operator-visible drift-detection-shift is under-specified for option E.3

**File:line citations:**
- Plan Decision E option matrix (`:99-105`):
  - E.1: leave CfgDriftCheckRegistry separate; FULL CLOSURE deferred
  - E.2: migrate to shared `COHORT_GATE_*` macros where alignment exists; preserve distinct semantic at bandit boundary
  - E.3: migrate to framework consumer via DRIFT_CHECK_FROM_DERIVED; delete CfgDriftCheckRegistry entirely; "Drift-check semantic at bandit boundary SHIFTS from `BITMAP_IS_SET(BANDIT_ENABLED)` → `bandit_algorithm != 0`"
- Plan recommendation (`:108`): "**Recommendation per `feedback_proportionate_response_to_audit_findings`:** (E.2) is the proportionate response"
- `MlCfgFlagRegistry.hpp:115` (post-`.B.2`): `#define COHORT_GATE_BANDIT_THOMPSON       (cfg.bandit_algorithm != 0)`
- `CfgDriftCheckRegistry.hpp:194-322`: 18 entries; bandit-cohort rows use `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)` for `gate_when`

**Observed vs expected:**

The option matrix documents the *gate-predicate* shift accurately but does NOT enumerate the OBSERVABLE drift-detection behavior change:

**Pre-`.B.3` semantic (CfgDriftCheckRegistry option E.1 / E.2 partial close):**
- `cfg.bandit_enabled` flag is the gate. If operator has `cfg.ml_cfg_flags |= MASK_ML_CFG_BANDIT_ENABLED` set, drift-check runs on bandit-cohort rows. If the operator unsets the flag (disables bandit feature), drift-check skips bandit rows regardless of `cfg.bandit_algorithm` value.

**Post-`.B.3` E.3 semantic:**
- `cfg.bandit_algorithm != 0` is the gate. Drift-check now runs on bandit-cohort rows ANY TIME `cfg.bandit_algorithm` is non-zero, even if `cfg.bandit_enabled` is unset.

**Observable behavior shift:** an operator who has `cfg.bandit_algorithm = 1` (any Thompson-class) but has set `cfg.bandit_enabled = 0` (disabled the bandit feature) would, post-E.3:
- Previously: no drift check on bandit rows (gate predicate false).
- Now: drift check runs on bandit rows (gate predicate true).

This is operator-visible IF stamps lack bandit-rows AND cfg has non-zero bandit_algorithm. v5.14.10.B+ stamps populated all bandit-cohort rows via AUTOPOPULATE when `bandit_algorithm != 0`, but the cohort-gate predicate at emit/parse time uses the LEGACY semantic — meaning stamps DO populate bandit rows. The drift-check semantic shift could surface false-positive drift detections on legacy stamps where `bandit_enabled=0` + `bandit_algorithm != 0` (operator disabled the feature but left the algorithm enum set).

**Coupled to `.B.3` other Decision D semantic shift:** plan Decision D mechanism 1 also moves 4 thompson rows + bandit_algorithm row into the canonical FOREACH_STAMP_BOUND_CFG_DERIVED-driven emit path. Per `MlCfgFlagRegistry.hpp:115` the cohort gate is `cfg.bandit_algorithm != 0` (already consistent with COHORT_GATE_BANDIT_THOMPSON). But CfgDriftCheck's drift check used the bandit_enabled flag. E.3 would unify these to the algorithm-based gate.

**Recommended fix:** Plan Decision E amendment v1.2 → v1.3:

1. **Add explicit operator-visible behavior table to Decision E.** Surface the diff above as a 2-row table (legacy vs E.3) showing the specific cfg state where drift-check behavior changes.
2. **Cross-reference to PARITY-013** (`PARITY_ISSUES.md:552`): "`cfg.bandit_algorithm` not stamp-bound; train↔serve algorithm drift undetected" — closed at v5.14.10.B by stamp-binding bandit_algorithm. E.3's semantic shift is the SAME class as PARITY-013's fix — gate predicate should match what is stamp-bound, not what gates emit.
3. **Re-evaluate auto-pick:** Per `feedback_proportionate_response_to_audit_findings`, the recommendation is option E.2 (partial close). But E.2 *preserves* a documented semantic divergence — i.e. CfgDriftCheckRegistry uses BITMAP_IS_SET(BANDIT_ENABLED) for gate_when while everything else uses COHORT_GATE_BANDIT_THOMPSON. This means future contributors adding a new bandit-cohort field have to remember TWO different gate predicates for emit vs drift-check, which is exactly the Class 18 mirror this ship is trying to close.
4. **Surface to Caramel inline with the 2-row table.** Option E.3's "operator-visible behavior shift" is potentially a *correct* fix (the semantic should be unified per PARITY-013 reasoning). Surface for triage with full proportionate-response menu (A inline merge / B accept rationale / C fold / D architect / E NO-FOLD first-of-kind) per `feedback_proportionate_response_to_audit_findings`.

**Effort estimate:** Decision E plan body amendment + Caramel triage: ~30-60 min.

**Cross-ref existing protection:** PARITY-013 (CLOSED at v5.14.10.B) closed bandit_algorithm stamping but did not address the drift-check gate semantic divergence — a sister class. Decision E.3 (or E.2 with semantic-divergence-documented-as-tech-debt) is the close.

---

### MED

#### MED-1 — Bash CLI emit (`tools/stamp_model.sh`) not in scope at plan body; cross-process byte-equivalence with C++ canonical body emit must be verified at v1 → v2 transition

**File:line citations:**
- Plan body NO mention of `tools/stamp_model.sh`
- DESIGN_SPECS `wire-format-byte-preservation-discipline.md:414`: `FoxML_Trader_v2 tools/stamp_model.sh — bash CLI emit (must produce identical bytes to C++ emit)`
- Engine HEAD verification: `tools/stamp_model.sh` exists (bash CLI for emitting stamps from training-time workflows)

**Observed vs expected:**

Wire-format byte-preservation discipline § "Apply when" point 4: "Multiple producers (bash CLI + C++ tool) must produce identical bytes." `tools/stamp_model.sh` is the bash producer; `populate_stamp_cfg_from_derived<F>` is the C++ producer. At v1 → v2 transition both must produce v2-format bytes; the bash script needs updating in lockstep.

Plan body Steps 1-9 do NOT mention `tools/stamp_model.sh`. If bash script keeps emitting v1 byte order while C++ engine emits v2, training-time stamps via the bash CLI fail HMAC verification post-`.B.3`.

**Recommended fix:** Add Step 1.6.8 to plan body — "tools/stamp_model.sh wire-format alignment with `populate_stamp_cfg_from_derived` walker. Bash script emits v2 byte order matching framework walker; cross-producer byte-equivalence test added to Step 9 build-verify."

**Effort estimate:** ~30-60 min bash script update; ~30 min cross-producer test.

**Cross-ref existing protection:** None — bash script was last touched in unknown sprint; needs verification. Layer 4 round-trip HMAC test against bash-emitted v1 stamps from training pipeline would catch divergence at boot but plan does not enumerate this.

---

#### MED-2 — Step 1.6.4 caller plumbing for `populate_stamp_cfg_from_derived<F>(canonical + n, sizeof(canonical) - n, *cfg_ptr)` is under-specified — `cfg_ptr` must be threaded through `stamp_write_for_model` signature

**File:line citations:**
- Plan Step 1.6.4 (`:220`): "Replace `FOREACH_STAMP_BOUND_CFG(X)` walker with `cfg_derived::populate_stamp_cfg_from_derived<F>(canonical + n, sizeof(canonical) - n, *cfg_ptr)` call (where cfg_ptr is passed via existing inf parameter chain OR added as new param)"
- Engine HEAD `ML_Headers/ModelInference.hpp:1788` (current): `FOREACH_STAMP_BOUND_CFG(X)` at canonical body emit — operates on `inf->name` (data already populated into struct fields) NOT `cfg.name` directly
- Framework walker at `MemHeaders/CfgGateRegistry.hpp:259`: `populate_stamp_cfg_from_derived<F>(char* buf, size_t cap, const ControllerConfig<F>& cfg)` — reads `cfg.name` directly, NOT inf struct fields

**Observed vs expected:**

The legacy walker at `ModelInference.hpp:1788` emits FROM `inf->name` (struct fields populated by AUTOPOPULATE at production caller). The framework walker reads cfg directly. At Step 1.6.4 migration, the caller chain at `stamp_write_for_model` must thread `cfg_ptr` through — the function signature currently does NOT accept a ControllerConfig parameter.

Plan says "OR added as new param" but doesn't enumerate the choice. Two paths:

(a) **Add `const ControllerConfig<F>* cfg_ptr` parameter to `stamp_write_for_model`** — breaks ABI of every production caller (5+ sites). Sister to PARITY-020 close pattern (extending function signature).

(b) **Pre-extract canonical bytes via `populate_stamp_cfg_from_derived` at AUTOPOPULATE call site + pass pre-computed bytes via inf struct extension** — preserves `stamp_write_for_model` ABI; adds complexity to `Stamp_AssembleAndEmit`.

(c) **Reverse the dependency: have `populate_stamp_cfg_from_derived` accept `StampInferenceCfgInputs` instead of cfg** — but the framework walker's whole point is to read cfg directly to close Class 27 (scalar cfg-mirror cache).

**Recommended fix:** Plan body Step 1.6.4 amendment to specify path (a) explicitly. ABI break is acceptable here per `feedback_no_defer_for_effort` — passing cfg through is the structurally correct shape and the framework walker's design intent. Auto-pick (a). Add commentary to plan body: "All production callers of `stamp_write_for_model` (current: `Stamp_AssembleAndEmit`, BacktestEngine, BacktestPanels) must pass `&cfg` as new parameter; ABI break confined to this ship."

**Effort estimate:** ~30 min plan body amendment + ~1h ABI extension coding.

**Cross-ref existing protection:** `Stamp_AssembleAndEmit<F>` (sister-call helper at v5.15.3.B.1) already takes `cfg` — its callers are the right pattern. Just thread `cfg` through `stamp_write_for_model`.

---

#### MED-3 — Plan body Step 1.6.2 says "DELETE 5 prefixed POST_CFG entries at StampBoundModelConstRegistry.hpp:454-465 + bandit/thompson 4 at :469-483 if also unifiable" — the conditional scope clarification is under-specified

**File:line citations:**
- Plan Step 1.6.2 (`:206-213`)
- Engine HEAD `StampBoundModelConstRegistry.hpp:454-483`: 9 POST_CFG prefixed entries actually present (4 per-horizon + 5 thompson; per the v5.15.5.A.7 ship)

**Observed vs expected:**

Plan body says:
> DELETE 5 prefixed POST_CFG entries at `StampBoundModelConstRegistry.hpp:454-465` + bandit/thompson 4 at `:469-483` if also unifiable (Decision D scope clarification: 4 thompson rows already cohort-migrated at `.B.2`; need to verify whether their POST_CFG mirror entries need deletion at `.B.3` to avoid double-emit)

Reading the HEAD state:
- Lines 454-465: 4 per-horizon barrier entries — `inference_cfg_ml_tp_pct`, `inference_cfg_ml_sl_pct`, `inference_cfg_barrier_blend_mode`, `inference_cfg_per_horizon_barrier_blend`
- Lines 469-483: 5 bandit/thompson entries — `inference_cfg_bandit_algorithm`, `inference_cfg_thompson_mu_prior`, `inference_cfg_thompson_precision_prior`, `inference_cfg_thompson_precision_obs`, `inference_cfg_thompson_exp3_blend_alpha`

Plan's "5 prefixed" + "bandit/thompson 4" = 9 total — but lines 469-483 contain 5 entries (5 bandit/thompson rows added at `.F.4d` PARITY-026 close), not 4.

If `.B.2` cohort-migrated the underlying bandit/thompson rows to STAMP_BOUND_CFG_DERIVED (matches our HEAD examination — bandit_algorithm + thompson_mu_prior + thompson_precision_prior + thompson_precision_obs + thompson_exp3_blend_alpha = 5 rows all flagged), then framework walker emits unprefixed `bandit_algorithm=N`, `thompson_mu_prior=N`, etc. PRESERVING the 5 prefixed POST_CFG entries would cause double-emit: both `bandit_algorithm=N` AND `inference_cfg_bandit_algorithm=N` in the canonical body.

**Recommended fix:** Plan body Step 1.6.2 amendment to:
1. Reconcile the count: 4 per-horizon + 5 bandit/thompson = 9 total prefixed POST_CFG entries that need DELETION (not "5 + 4" or "5 + 4 if unifiable" — all 9 are double-emit hazards).
2. Remove the "if also unifiable" conditional — all 9 entries WILL double-emit post-Step-1.6.4 framework walker activation. Deletion is required, not optional.
3. Explicit deletion procedure: delete lines 454-483 of `StampBoundModelConstRegistry.hpp` + bump `STAMP_BIT_COUNT` constant if necessary (per the `STAMP_BIT_COUNT` allocation comments at `:514-517`).
4. Verify Layer 5b structural-invariant runner (per HIGH-1) detects double-emit via I4 (per-row name appears EXACTLY when bit set; if both prefixed + unprefixed emit, both names appear which the framework can detect).

**Effort estimate:** ~15 min plan body amendment.

**Cross-ref existing protection:** None — without Step 1.6.2 amendment, the double-emit hazard is silent.

---

#### MED-4 — Step 0.5b struct-gen extension scope under-specifies: `FOREACH_GLOBAL_CFG_FIELD` doesn't auto-gen struct fields per `.B.2` Discovery 8, but PerCoreCfg<F> H17 auto-gen mechanism details not fully audited at HEAD

**File:line citations:**
- Plan Decision A (`:39-49`) + Step 0.5b (`:189`)
- HEAD evidence at `ControllerConfig.hpp:889` (manual decl); `:1729` (manual default); `:2555` (manual parser)
- HEAD evidence at `CfgFieldRegistry.hpp:399`: "(FOREACH_GLOBAL_CFG_FIELD doesn't auto-gen struct fields — manual decl/default/parser cleanup deferred to .B.3 with cfg-storage-discipline amendment)"

**Observed vs expected:**

The plan body says "extend FOREACH_GLOBAL_CFG_FIELD struct-gen via sister mechanism to per-core" without enumerating the H17 PerCoreCfg<F> auto-gen mechanism. Per CLAUDE.md H17: `PerCoreCfg<F>` body = X-macro only (CI Check 2 since `.F.4c`). The plan does not verify whether:

(a) The PerCoreCfg<F> auto-gen mechanism is purely X-macro expanding fields, OR
(b) It includes per-Kind dispatch (FPN<F> vs int vs bool field decl), OR  
(c) It honors `lives_in_struct` discriminator (since master registry rows tag `STRUCT_CFG` vs other cfg structs).

For `gap_acceptable_threshold`: master registry row (`CfgFieldRegistry.hpp:403`) does NOT have `lives_in_struct` column populated (global registry's row sig is 8-col, while per-core's 13-col includes the column at the end). Plan needs to enumerate which `ControllerConfig<F>` field shape `gap_acceptable_threshold` ends up with — should be `FPN<F>` matching legacy manual decl.

**Recommended fix:** Plan body Decision A or Step 0.5b expansion to enumerate:
1. The exact X-macro pattern used by PerCoreCfg<F> auto-gen (cite file:line at HEAD).
2. The Kind-to-field-type mapping (KIND_DOUBLE in global registry → FPN<F> in struct OR double in struct? Per legacy manual decl at `ControllerConfig.hpp:889` it's `FPN<F>`).
3. The sister mechanism for `ControllerConfig<F>` struct body extension (e.g., add a `FOREACH_GLOBAL_CFG_FIELD(X_GEN_CTRL_CONFIG_FIELD)` macro that emits one field declaration per row).
4. Default-init mechanism (line `:1729` `FPN_FromDouble<F>(0.05)` — extracted from master registry's `payload` column).

**Effort estimate:** ~30-45 min plan body amendment + ~30 min audit of PerCoreCfg<F> auto-gen pattern at HEAD.

**Cross-ref existing protection:** Plan body's Decision A "Alternative reconsidered" note ("if struct-gen extension surfaces unexpected dependencies, fall back to (b)") is the right shape; amendment formalizes the dependency audit.

---

### LOW

#### LOW-1 — Plan body line 132 says "ZERO production consumers after Step 1.6.X migrations" but doesn't enumerate the comments/historical refs in MlCfgFlagRegistry.hpp:97 + StampBoundModelConstRegistry.hpp + CfgDriftCheckRegistry.hpp that reference FOREACH_STAMP_BOUND_CFG by name (deletion-of-comments / DESIGN_SPECS-update)

**File:line citations:** plan body `:132` + 14+ comment references at grep `"FOREACH_STAMP_BOUND_CFG"` from initial scan

**Observed vs expected:** Comments/cross-refs to `FOREACH_STAMP_BOUND_CFG` survive post-Step-2 deletion of the macro body. These are bookkeeping; if not updated they cause grep-noise + future-archaeology confusion.

**Recommended fix:** Add Step 2.5 plan body item — "Update comments + DESIGN_SPECS cross-refs to point to new framework registry (FOREACH_*_CFG_FIELD with STAMP_BOUND_CFG_DERIVED filter); ~20 mechanical comment updates per the grep results."

**Effort estimate:** ~20-30 min mechanical.

**Cross-ref:** `/dust` would catch these at post-ship audit; including in plan body keeps the migration tidy.

---

#### LOW-2 — Plan body Step 7 mentions "Original `.B` plan body (SUPERSEDED at `.B.1` split) lines 114/234/247/260-265/642/827 + sidecar 247/289/292/558 mechanical cleanup" — assumes file existence

**File:line citations:** plan body `:262-263`

**Observed vs expected:** The `.B` original plan body at `plans/v5.15-live-readiness/subplans/...-B-(original)*.md` may not exist or may have been deleted at the `.B.1` split. Plan body should verify.

**Recommended fix:** plan body Step 7 amendment: "(if file exists) ... mechanical cleanup; otherwise skip with note in postmortem."

**Effort estimate:** ~5 min plan body amendment.

---

### DOCUMENT-ONLY

#### DOC-1 — Schema versioning at `stamp_format_version` is sub-section of MODEL_FORMAT_VERSION schema; future bumps now precedented by `.B.3`

Per plan Step 1.6.7.4 DESIGN_SPECS amendment (target spec: `wire-format-byte-preservation-discipline.md`), `.B.3` is the FIRST canonical wire-format version bump in engine history. After ship, the procedure is documented for future bumps (e.g., adding/removing a STAMP_BOUND_CFG_DERIVED-flagged field → bump v2 → v3).

This is informational, not actionable at `.B.3`. Mention here for posterity.

---

## Cross-cutting concerns

### CC-1 — DESIGN_SPECS `wire-format-byte-preservation-discipline.md` § Layer 5b is ASPIRATIONAL, not codified
Description: spec claims "first canonical implementation at v5.15.5.F.4d.1.A" but engine search returns ZERO hits. This affects HIGH-1 (Layer 5b implementation missing) + LOW-1 (stale cross-ref). Single fix: amend spec status + ship Layer 5b implementation at `.B.3` per HIGH-1 option (a).

### CC-2 — Five out of nine prefixed POST_CFG entries at `StampBoundModelConstRegistry.hpp:454-483` plus their unprefixed sisters are DOUBLE-EMIT hazards post-Step-1.6.4 framework walker activation
Description: per MED-3, the conditional scope under-specifies the deletion procedure. All 9 entries must be deleted to prevent double-emit. Single fix per MED-3.

### CC-3 — Fixture file procedure missing covers both v1 (HIGH-2.1) + v2 (HIGH-2.2); needs sequenced creation: v1 fixture at `.B.2` engine pre-coding tag, v2 fixture at `.B.3` engine post-Step-1.6.4 migration
Description: per HIGH-2, fixture creation procedure is the load-bearing detail. Without it, the v(N) → v(N+1) bump procedure cannot be codified as the canonical DESIGN_SPECS § "Procedure for wire-format changes during framework refactoring".

---

## Behavior matrix (verify framework walker + legacy walker agree on canonical body field values for default cfg)

| Cfg state | Legacy walker output | Framework walker output | Bytewise identical? | Failure mode |
|---|---|---|---|---|
| All defaults (cfg=0 / FPN(0.0) per legacy default_val) | 25 rows, hand-crafted order | 25 rows, master-registry order + ML_CFG_FLAG block | **NO — row order differs (CRIT-1)** | v1 → v2 bump REQUIRED |
| All Ridge cohort active (RIDGE_WITHIN_HORIZON | RIDGE_ACROSS_HORIZONS set, ridge_lambda etc. non-zero) | Same 25 rows but Ridge gate predicates emit | Same 25 rows but in master-registry order | **NO — row order differs** | bump REQUIRED |
| Bandit Thompson active (bandit_algorithm=1 + thompson_mu_prior etc.) | bandit_algorithm + thompson_* rows emit per legacy gate | Same rows emit per COHORT_GATE_BANDIT_THOMPSON gate | gate predicate semantic identical (`bandit_algorithm != 0`) | Field values identical; ORDER differs |
| Thompson BLENDED state-4 (bandit_algorithm=4 + thompson_exp3_blend_alpha set) | Per legacy `COHORT_GATE_BANDIT_BLEND_STATE_4` | Same gate predicate (extracted from `.B.2` cohort macro) | Field values identical; ORDER differs |
| Composite confidence active (CONFIDENCE_COMPOSITE_ENABLED set + confidence_freshness_tau_secs etc. non-zero) | Per legacy `COHORT_GATE_COMPOSITE_CONFIDENCE` | Same gate predicate (extracted) | Field values identical; ORDER differs |

**Conclusion:** All 25 canonical body rows have identical field VALUES between legacy + framework walkers (the `.B.2` cohort-gate macro extraction is the source of truth for matching semantics). The byte ORDER differs across ALL rows (CRIT-1). HMAC chain breaks for ALL legacy v1 stamps on `.B.3+` engine — this is INTENDED + the stamp_format_version=1 → 2 bump's purpose.

---

## Suggested ship sequence

Per HIGH-1 recommendation (folding Layer 5b structural-invariants framework implementation INTO `.B.3` per "first non-zero canonical body emit" rationale):

- **v5.15.5.F.4d.1.B.3 (this ship)** — Legacy empty-out + Layer 5b structural-invariants implementation + STRICT v1 stamp refusal + fixture creation + v2 hash lock
- **v5.15.5.F.4d.1.C (next ship)** — Sidecar override + bit-packed inventory (per CLAUDE.local.md sprint state)
- **v5.15.5.F.4d.1.D (after .C)** — CI verification + fixture regression sweep
- **v5.15.5.F.4d.1 umbrella close**

If HIGH-1 option (b) deferred Layer 5b to `.B.4`:
- v5.15.5.F.4d.1.B.3 — Legacy empty-out + STRICT v1 stamp refusal + fixture creation + v2 hash lock (NO Layer 5b)
- v5.15.5.F.4d.1.B.4 (NEW) — Layer 5b structural-invariants framework implementation (~3-4h focused)
- ... then .C, .D, etc.

**Auto-pick:** option (a) — fold Layer 5b INTO `.B.3`. Per `feedback_motivated_collaborator_for_caramel` + `feedback_no_defer_for_effort`. The `.B.3` ship is the canonical Layer 5b first-application moment.

---

## NOT a bug (verified-safe items)

- **AUTOPOPULATE preserves PARITY-020 (CLOSED v5.15.3.B.1) close.** Plan Step 1.5 swap of INFERENCE_CFG_AUTOPOPULATE → INFERENCE_CFG_POPULATE_FROM_DERIVED preserves the helper-based production-caller class extinction; future stamp emit callers continue to auto-flow.
- **PARITY-013 (CLOSED v5.14.10.B) close holds.** bandit_algorithm + 4 thompson fields remain stamp-bound through framework walker; field values are byte-identical to legacy.
- **PARITY-022 quarantine respected.** Plan body does not propose reviving STAMP_MODEL_CONST_AUTOPOPULATE.
- **PARITY-024 (CLOSED v5.15.5.A.7) close held by Decision D mechanism 1.** 5 prefixed-only fields (`inference_cfg_ml_tp_pct` etc.) collapse to unprefixed canonical names while preserving training-time barrier semantic — single source of truth at framework walker.
- **Locale pinning at `stamp_write_for_model` (`ML_Headers/ModelInference.hpp:1683+` per audit walk-back).** Plan Step 1.6.4 framework walker migration does not alter the `uselocale(LC_NUMERIC_MASK, "C", 0)` discipline — still applied at caller scope. No locale-leak risk.
- **MODEL_FORMAT_VERSION (5) separate from stamp_format_version (bumping 1 → 2).** Plan body correctly distinguishes the two version axes per existing engine convention (`ModelInference.hpp:1716-1717`).

---

## Cross-references to existing PARITY_ISSUES.md ledger

| New finding | Existing ID | Verdict |
|---|---|---|
| CRIT-1 byte order discontinuity v1→v2 | (no existing) | NEW — but intentional + paired with version bump, not a bug to assign PARITY-NNN |
| HIGH-1 Layer 5b absent | (no existing) | NEW — assign **PARITY-026** if implementation deferred per option (b) |
| HIGH-2 fixture missing | (no existing) | NEW — load-bearing for v(N)→v(N+1) procedure; assign **PARITY-027** if fixture creation deferred |
| HIGH-3 Decision E gate semantic | PARITY-013 (CLOSED) | SISTER — extending CLOSED finding's discipline; no new ID needed unless E.1 picked (deferred close = NEW ID for deferred CfgDriftCheck consolidation) |
| MED-1 bash CLI alignment | (no existing) | NEW IF deferred — assign **PARITY-028** for cross-producer byte-equivalence |
| MED-2 cfg_ptr plumbing | (no existing) | NEW — covered at Step 1.6.4 amendment, no PARITY ledger entry needed if amendment lands |
| MED-3 double-emit hazard | (no existing) | NEW — coding-time hazard, no ledger entry needed if Step 1.6.2 amendment lands |
| MED-4 struct-gen scope | TECH_DEBT-093 (in plan body Step 1.6.1) | SISTER — Step 0.5b under-specifies; no ledger entry needed if Step 0.5b amendment lands |

**Auto-write to PARITY_ISSUES.md per CLAUDE.local.md auto-write contract:** if operator chooses to defer HIGH-1 OR HIGH-2 OR MED-1, allocate the cited NEW PARITY-NNN entries during plan body amendment. If all are folded INTO `.B.3`, no ledger entries needed.

---

## Files-changed verification log

- `tests/fixtures/` directory: **MISSING at HEAD** — fixture procedure NEW
- `DERIVED_FILTER_DECLARE_WIRE_FORMAT_TWO_SOURCE` macro: **MISSING at HEAD** — Layer 5b implementation NEW
- `populate_stamp_cfg_from_derived<F>`: PRESENT at `MemHeaders/CfgGateRegistry.hpp:259-308`
- `drift_check_from_derived<F>`: PRESENT at `MemHeaders/CfgGateRegistry.hpp:315-360` — plan Step 0.5a extends with `reason_buf` args
- `populate_inference_cfg_from_derived<F>`: PRESENT at same file, function near line 220
- `FOREACH_STAMP_BOUND_CFG`: PRESENT (legacy; 25 rows at `StampBoundCfgRegistry.hpp:99-179`) — deletion target Step 2
- `FOREACH_CFG_DERIVED_INFERENCE_CFG`: PRESENT (legacy; `CfgDerivedInferenceCfgRegistry.hpp`) — deletion target Step 2
- `FOREACH_CFG_DRIFT_CHECK`: PRESENT (18 entries; `CfgDriftCheckRegistry.hpp:194-322`) — Decision E target
- Master registry `STAMP_BOUND_CFG_DERIVED` flagged scalar rows: **21** (2 global + 19 per-core) + 4 ML_CFG_FLAG bitmap rows = **25 total** (matches legacy registry count; framework walker semantically equivalent for cohort fields)

---

## End of report

**Auditor recommendation summary:**
- **GREEN-blocking action:** 1 CRIT (auto-pick STRICT mode + enumerate byte order diff) + 3 HIGH (Layer 5b implementation OR defer + fixture procedure + Decision E triage) before pre-coding tag fires
- **YELLOW-blocking action:** 4 MED clarifications + 2 LOW polish items at plan body amendment
- **Path to GREEN:** v1.2 → v1.3 plan body amendment, ~3-4h focused (most of which is HIGH-1 Layer 5b implementation discussion + Decision E Caramel triage)
- **Path to YELLOW after triage:** all amendments land in v1.3; pre-coding tag fires; coding proceeds

**Convergent with sister audits expected:**
- `/dod-audit` likely surfaces same MED-3 + MED-4 (DESIGN_SPECS pattern application gaps)
- `/anti-spaghetti` likely surfaces same HIGH-3 (CfgDriftCheck parallel-infrastructure with framework consumer)
- `/trace-deps` likely surfaces same MED-2 (cfg_ptr threading is dependency-chain)
- `/readiness` likely surfaces same HIGH-2 (fixture missing — readiness Check 9 + 18)
