---
type: plan-check
audit_kind: queued-subplan-cohesion
sprint: v5.15-live-readiness
audit_date: 2026-05-24
engine_head: 56a689620bb48559597f8b51032b3b43cc499952
branch: feat/v5.15-live-readiness
verdict: YELLOW (cohesion gaps; ROADMAP authoritative but several queued bodies STALE; .B.4 plan body MISSING; MASTER stops at v5.15.4)
---

# /plan-check — v5.15-live-readiness queued sub-plans — 2026-05-24

## Plan summary

- **Master:** `plans/v5.15-live-readiness/MASTER.md` (stops at v5.15.4; v5.15.5.X catch-up section appended but does NOT enumerate Phase F/G/H/K work)
- **Authoritative ship pipeline:** `plans/v5.15-live-readiness/ROADMAP-2026-05-17-to-paper-test.md` (Phases A-E, refreshed 2026-05-24 to add `.B.4` row + cadence row)
- **Queued sub-plans audited:**
  - `subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` (IN-FLIGHT; v1.17 DRAFT)
  - `subplans/2026-05-16-v5.15.5.F.4d.1.C-sidecar-bitpacked.md` (DRAFT v1.2)
  - `subplans/2026-05-16-v5.15.5.F.4d.1.D-ci-fixture.md` (DRAFT v1.2)
  - `subplans/2026-05-14-v5.15.5.F.4e-string-filepath-gui-metadata.md` (STALE BANNER; explicit re-plan deferred to pre-coding gate)
  - `subplans/2026-05-16-v5.15.5.F.4f-cleanup-tech-debt-076-080.md` (STUB; pre-coding placeholder)
  - `plans/_future/2026-05-14-v5.15.6-master-cfg-surface-unification-followon.md` (PLANNED stub)
- **Critical-path (per ROADMAP):** `.B.3` → `.B.4` (NEW; plan body MISSING) → `.C` → `.D` → `.F.4d.1` umbrella → `.F.4e` → `.F.4f` → `.F.5.A/B/C` → `v5.15.6.A/B`
- **Status:** **YELLOW** — sprint can progress, but 4 cohesion gaps must be addressed before coding `.B.4`/`.C`/`.D` lands.

---

## Per-sub-plan readiness verdicts

| Sub-plan | Verdict | Template compliance | End goal | Sister-registry inspection | Audit-driven discipline | Critical fixes |
|---|---|---|---|---|---|---|
| `.B.3` (in-flight) | YELLOW | PARTIAL — body massively expanded (v1.0→v1.17); template sections diffused across decision blocks not section headers | IMPLICIT (in Status block; not section header) | PRESENT (12 sister-extension verdicts cited) | EXTENSIVE (6 audit reports + 2 RE-SWEEP rounds) | Plan body 187KB; iteration-spiral inflection reached but body bloat impedes cold-pickup |
| `.C` (sidecar+bitpack) | YELLOW | PARTIAL — has Scope/DOD/Anti-patterns/Verification gate; MISSING "Canonical sister registries considered" section heading; "Bug classes closed" implicit (Class 21+23 cited inline); MISSING "End goal" section heading; MISSING "Ship end goal + acceptance criteria" per `feedback_plans_have_explicit_end_goal` | IMPLICIT in "Sub-ship role" prose | PRESENT (sister to `.B.1`'s FOREACH_CFG_GATE cited; merging w/ DriftCheck sister enumerated) | DEFERRED ("Pre-coding audit gate next") | Add explicit "End goal" + "Canonical sister registries considered" section headers; verify Approach A struct-gen lands at `.B.3` so `.C` consumer code (`drift_ovr_*` accessors) matches |
| `.D` (CI+fixture) | YELLOW | PARTIAL — has Scope/Anti-patterns/Verification gate; MISSING "End goal" section heading; MISSING "Canonical sister registries considered" section heading (sister CI tools listed at end though); references body cleanup pending at `.D` update step | IMPLICIT in "Sub-ship role" prose | IMPLICIT (sister tools cited; not under standard heading) | DEFERRED | Has body-residual cleanup note from Path γ+ v2 ("apply at `.D` update step"); fixture acquisition still operator-blocking step |
| `.F.4e` (KIND_STRING+GUI metadata) | RED | STALE BANNER (2026-05-17) explicitly says "re-plan body fully at `.F.4e` pre-coding gate"; ALL code samples 1+ amendment generations behind canonical Path γ shape; v1.0 status pre-`.F.4b` Class 23 lock | NOT EXPLICIT — `feedback_plans_have_explicit_end_goal` violation | NOT EXPLICIT | NOT MENTIONED | Plan body MUST BE REWRITTEN per stale banner before pre-coding gate fires; effort estimate (500 LOC) likely wildly wrong given Path γ collapse (~150→30 LOC per derived-filter app) |
| `.F.4f` (cleanup TD-076..080) | YELLOW | STUB — has Phase-by-phase scope + sub-ship boundaries + verification gate; MISSING "End goal" section heading; MISSING "Canonical sister registries considered" section heading; MISSING "design space" decision blocks per `future-oriented-plan-template`; sub-ship boundaries tentative | IMPLICIT in "Why this ship exists" prose | NOT EXPLICIT (sister CI tools / sister DESIGN_SPECS / Class 25 sweep predecessor cited inline) | PLANNED ("Pre-coding triggers" section requires `/precoding-audit-gate` before STUB→ACTIVE) | Plan body needs FULL expansion per its own "Pre-coding triggers" section (currently a STUB by author's intent) |
| `v5.15.6.A/B/C` (future) | YELLOW | PLANNED stub with sub-ship table; references `.F.4i` as canonical template; references TECH_DEBT-050/051/052; MISSING explicit "End goal" header (goal in prose); MISSING "Canonical sister registries considered" section header | IMPLICIT | IMPLICIT (`.F.4i` cited as template) | "SUGGESTED" not mandated | Defers full body to "Sprint kickoff" per design; acceptable for a future-bucket placeholder |
| `.B.4` (train-serve EngineCommon extract) | **RED** | **PLAN BODY DOES NOT EXIST** — ROADMAP row added 2026-05-24 with description but `subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md` is NOT on disk | n/a | n/a | n/a | **HIGHEST-PRIORITY GAP** — Caramel must draft plan body BEFORE coding the EngineCommon extract closes 4 CRIT + 3 HIGH |

---

## Cross-plan integration findings

### 1. DEPENDENCY EDGE MISMATCH — `.C` + `.D` plan bodies claim wrong predecessor

- `.C` v1.2 line 6: **Predecessor sub-ship: `v5.15.5.F.4d.1.B`** ← refers to OBSOLETE single-B ship; actual predecessor per ROADMAP + IN-FLIGHT state is `.B.3` (which was split from `.B` into `.B.1` + `.B.2` + `.B.3` + `.B.4`).
- `.D` v1.2 line 6: **Predecessor sub-ship: `v5.15.5.F.4d.1.C`** ← correct shape but assumes `.C` is the immediate predecessor; ROADMAP now inserts `.B.4` between `.B.3` and `.C`. `.D`'s predecessor is correct (`.C`) but `.C` itself has wrong predecessor → cascade.
- `.C` Step 0 expected baseline: `~3222 controller_test` ← current HEAD post-`.B.3` Phase F WIP-checkpoint 8 is `3230` per WIP commit body. Stale baseline by ~8 tests.
- `.D` Step 0 expected baseline: `~3237 controller_test` ← will drift further after `.B.4` lands.

**FIX:** Amend `.C` predecessor to `v5.15.5.F.4d.1.B.4` (or `.B.3` if `.B.4` is folded back). Re-baseline both Step 0 test-count expectations at coding time.

### 2. STAMP_BOUND_CFG / FOREACH_DERIVED_FILTER REFERENCE DRIFT — `.D` body residual cleanup outstanding

- `.D` Status block (lines 10-14) lists explicit "body residual cleanup notes" — references to `EXEMPT_FROM_DERIVED_FILTER` and `FOREACH_DERIVED_FILTER roster` that are Path γ-pre-canonical-redirect terms. Path γ correction (`.F.4d.1.A`) replaced these with `FOREACH_METADATA_BIT` infrastructure. `.D` author flagged "~10 min mechanical cleanup at `.D` update step" but the cleanup HAS NOT happened yet. Stale-claim audit risk.

### 3. .F.4e SCOPE MASSIVELY STALE — Step 3 framework apps superseded

- `.F.4e` Step 3 (GUI metadata derived filters) was written against v1.0 `DERIVED_FILTER_DECLARE_GUI_BY_GROUP` family + `DerivedFilterRoster.hpp` + `FOREACH_DERIVED_FILTER` parallel walker — ALL SUPERSEDED by Path γ correction at `.F.4d.1.A` (canonical mechanism is `FOREACH_METADATA_BIT` + `cfg_compute_mask` + `CFG_FIELD_FOR_EACH_SET_BIT`).
- Step 3a (FAILURE_MODE GUI Class-18 closure) describes "Option 1 vs Option 2 framework extension" mechanism that may not exist in current code post-Path γ.
- Author flagged this — plan body status says "STALE — re-plan body at `.F.4e` pre-coding gate per Path γ correction". Acceptable IF re-plan happens BEFORE coding. **Risk:** if forgotten, code lands against superseded mechanism.
- Effort estimate (500 LOC; "100 LOC for Step 1 tt:: specs + 150 LOC for Step 3 GUI metadata") almost certainly WRONG post-collapse (~150→30 LOC for Step 3 per stale banner own estimate).

### 4. POST-`.B.4` CADENCE NOT INTEGRATED INTO MASTER

- `ROADMAP-2026-05-17-to-paper-test.md` row 67-71 documents `.F.4d.1.B.4-followup` rolling 6-layer asymmetry sweep cadence — sub-ship absorption rules ("may absorb into `.F.5.X` or spawn `.F.4d.1.B.5+`").
- **MASTER.md does NOT reference this cadence at all** — MASTER stops at v5.15.4. The v5.15.5 series catch-up section (lines 292-322) mentions `.A`/`.B.1`/`.B.2`/`.B.3` but says nothing about `.B.4` or the 6-layer sweep.
- **Cohesion risk:** future operator/Claude reading MASTER for sprint authority will miss the cadence + `.B.4` work; ROADMAP is the de-facto authority but ROADMAP is currently a sidecar, not the master.

### 5. `.B.4` SCOPE SIZING — audit-driven but no plan body

- ROADMAP `.B.4` row describes: closes 4 CRIT (PARITY-026/027/028/029) + 3 HIGH (PARITY-030/031 + B2 OneCore arch mirror); M5 meta-discipline codification + NEW DESIGN_SPECS + NEW skill + NEW `/readiness` Check 40.
- 6 PARITY entries (026-031) AND 6 TECH_DEBT entries (119-124) auto-written to ledgers per audit findings — VERIFIED on disk in workspace `DOCS/PARITY_ISSUES.md` + `DOCS/TECH_DEBT.md`.
- TECH_DEBT-119 status: `OPEN (in-flight at .B.4 start)` — properly opened but **NO PLAN BODY EXISTS to describe the implementation, decision space, sister-registry consideration, or acceptance criteria.**
- **THIS IS THE LARGEST COHESION GAP.** `.B.4` is described in ROADMAP + audit synthesis + ledger entries + cadence doc — but the plan body that orchestrates them is missing.

### 6. STAMP BODY ORDER CONFLICTS — none surfaced

- `.B.3` deletes 15 prefixed POST_CFG entries + bumps `stamp_format_version` 1→2 SOFT (verified shipped at WIP-8). `.C`/`.D`/`.F.4e`/`.F.4f` do NOT touch stamp body order. No conflict.

### 7. CFG FIELD NAME CONFLICTS — none surfaced

- `.F.4e` adds ~30 KIND_STRING/KIND_FILE_PATH rows; `.F.4f` deletes 89 flat per-core fields. Different namespaces; no collision.
- `.B.3` Phase K (47-globals registry-default sweep) — no plan claims new global cfg fields that would collide.

### 8. ARCHITECTURAL INVARIANT BREACHES — none surfaced

- Each plan body's H1-H20 audit table (where present) shows PRESERVED. Hot path UNTOUCHED claims hold across all queued plans.

### 9. SISTER-REGISTRY INSPECTION COMPLIANCE

- `.B.3` v1.17: PRESENT + 12 sister verdicts documented (canonical sister-extension-discipline first canonical).
- `.C`: PARTIAL — discusses sister `.B.1` FOREACH_CFG_GATE + DriftCheck inline; no dedicated "Canonical sister registries considered" section header.
- `.D`: PARTIAL — sister CI tools listed at end; no dedicated section header.
- `.F.4e`: NONE (stale; will need under re-plan).
- `.F.4f`: PARTIAL — sister discipline (`cfg-scope-discipline.md` + Class 25 sweep predecessor) cited but no dedicated section header.
- `v5.15.6.X`: PARTIAL — sister `.F.4i` template cited.
- **READINESS Check 29 strict reading:** several queued plans would FAIL Check 29 if it were enforced today. Per `feedback_plans_cite_sister_registry_inspection`, ship-blocker if missing → all queued plans need amendment before coding.

### 10. END-GOAL SECTION COMPLIANCE

- **Per `feedback_plans_have_explicit_end_goal`:** every sub-plan body MUST include explicit "End goal" + acceptance criteria + tie-back to sprint MASTER goal.
- Verified by grep: **NONE of `.C`, `.D`, `.F.4e`, `.F.4f`, `v5.15.6.X` have explicit "End goal" or "Ship end goal" section headers.**
- Implicit goals scattered in prose (Why-this-ship-exists / Sub-ship role / Status blocks) — discoverable but not auditable.
- Same applies to MASTER itself — no explicit "Sprint end goal" section header; goal in opening paragraph.

---

## Honest gap list

### Missing plans
1. **`.B.4` plan body MISSING** — highest priority; ROADMAP + audit + ledger entries reference it; no actual plan body file. Path: `subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md`.
2. **MASTER amendment** to cover v5.15.5.F.4d.1.B/C/D + .B.4 + Phase F + Phase K + post-`.B.4` cadence. MASTER currently stops at v5.15.4 with a catch-up index for v5.15.5 that lists only `.A`/`.B.1`/`.B.2`/`.B.3`.

### Plans that should be expanded
3. **`.F.4e`** — explicit re-plan flagged by author; must happen before coding. Effort estimate (~500 LOC) needs re-derivation post-Path γ collapse.
4. **`.F.4f`** — STUB pending pre-coding triggers; needs full body draft per its own "Pre-coding triggers" section (full Phase body expansion + sub-ship boundary finalization + per-phase verification gate detail).

### Plans that should be amended (template compliance)
5. **`.C`, `.D`, `.F.4f`, `v5.15.6.X`** — add explicit "End goal" + "Canonical sister registries considered" section headers per `feedback_plans_have_explicit_end_goal` + `/readiness` Check 29-30. Mechanical edit; ~5-10 min each.
6. **`.C` + `.D`** — refresh predecessor metadata to reflect actual ship sequence post-`.B.4` insertion; rebaseline Step 0 test counts.

### Plans that should be consolidated/split
7. **`.B.3` body bloat** — at 187KB + v1.17 amendments, plan body has become a journal of audit rounds rather than a steerable spec. Future cold-pickup may struggle. Consider folding closed-decision blocks into postmortem at ship close + leaving only OPEN-DECISION blocks in remaining body.
8. **`v5.15.6.X` stub** — at sprint kickoff (post-`.F.5.C` close), expand into 3 cold-pickup-ready sub-plans per its own kickoff checklist.

### Stale claims surfaced
9. `.D` "body residual cleanup" notes (Path γ+ v2 lines 10-14) — pending cleanup task not yet executed.
10. `.F.4e` STALE BANNER — code samples deprecated; re-plan required.
11. `.C` line 6 + `.D` indirectly — predecessor sub-ship metadata stale (refers to `.B` rather than `.B.3` / `.B.4`).

---

## Recommendations

### Must fix before coding `.B.4`
- **Draft `.B.4` plan body** per `future-oriented-plan-template.md` shape — `subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md`. Required sections: End goal + design space (boundary-stable extract vs in-place mirror vs deferred) + Canonical sister registries (cite STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN cohort + EngineCommon precedents) + Bug classes closed (Class 18 mirror; F7 reopened) + DESIGN_SPECs landed (`train-serve-execution-layer-parity.md` + `shared-helper-extract-for-train-serve-mirror-close.md` from DRAFT v0.1) + Verification gate (PARITY-026..031 closed; B2 arch mirror closed; 4 CRIT + 3 HIGH ledger updates) + TECH_DEBT auto-write (-119..-124 status moves) + Pre-coding triggers (full `/precoding-audit-gate` + `/blindspot-scan`).
- **Amend MASTER** to add v5.15.5.X catch-up rows for `.B.4` + Phase F + Phase K + 6-layer asymmetry cadence; OR formally promote ROADMAP to be the sprint-authoritative pipeline doc with MASTER as historical record.

### Must fix before coding `.C` / `.D` / `.F.4e` / `.F.4f`
- `.C` + `.D`: refresh predecessor metadata + Step 0 test baselines.
- `.D`: execute the pending body-residual cleanup (Path γ+ v2 notes lines 10-14).
- `.F.4e`: full re-plan per stale-banner directive; do NOT code against the v1.0 body.
- `.F.4f`: full Phase body expansion per its own pre-coding triggers.

### Worth fixing during coding
- Add explicit "End goal" + "Canonical sister registries considered" section headers to `.C`/`.D`/`.F.4f`/`v5.15.6.X` for `/readiness` Check 29-30 compliance.
- `.B.3` body cleanup at ship close: fold closed-decision blocks into postmortem.

### Acceptable risk (don't block)
- `v5.15.6.X` template-compliance defer to sprint kickoff — acceptable for future-bucket placeholder.
- ROADMAP-as-authority pattern OK if MASTER gets a "see ROADMAP" pointer; current sprint can finish without MASTER full amendment if ROADMAP is operator-authoritative.

---

## Verdict: YELLOW

- **GREEN-class** items: stamp body order coherent across all plans; cfg field name spaces don't collide; H1-H20 audit tables consistent; sister-registry inspection PRESENT (most plans) per Check 29 spirit; audit-driven discipline embedded in `.B.3` + planned for downstream.
- **YELLOW-class** items: predecessor metadata stale on `.C` / `.D`; baseline test counts stale; `.F.4e` re-plan pending; `.F.4f` STUB → ACTIVE promotion pending; explicit "End goal" + "Canonical sister registries considered" section-header compliance MISSING in 5 of 7 queued plans.
- **RED-class items:** `.B.4` plan body **DOES NOT EXIST** on disk despite ROADMAP row + 6 PARITY + 6 TECH_DEBT entries written + audit synthesis captured + cadence doc planned. Highest-priority gap.

Sprint can proceed if `.B.4` plan body is drafted next + `.C`/`.D` predecessor metadata refreshed before coding lands. The audit pipeline + framework discipline is healthy; the documentation lattice has a single load-bearing gap (`.B.4` body) plus minor template-compliance drift across the queue.

**Next step:** Caramel drafts `.B.4` plan body, then amends MASTER (or formally moves ROADMAP into MASTER), then `.C`/`.D`/`.F.4e`/`.F.4f` get mechanical refresh + section-header additions in batch.
