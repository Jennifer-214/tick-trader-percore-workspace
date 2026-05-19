# /dod-audit report — Phase L amendment (`framework-driven-cli-binary-pattern.md` + `.B.3` v1.14 plan body) — 2026-05-18

**Scope:** plan-mode + new-DESIGN_SPEC structural validation
**Plan body:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` (v1.14)
**New spec:** `DESIGN_SPECS/framework-driven-cli-binary-pattern.md` (Stage 2 DRAFT v1.0)
**Sprint:** v5.15.5.F.4d.1.B.3 (in-flight; Phase L pre-coding)
**Stage 0 DESIGN_PHILOSOPHY preload context:** § 1.5 (Framework discipline meta-principle) + § 7 (Structural-fix family) + § 11 (audit-driven pre-coding gate)

---

## Catalog ingested

- **80 DESIGN_SPECS in catalog** (per `ls DESIGN_SPECS/*.md | wc -l` snapshot 2026-05-18)
- **NEW pattern added (audit subject):** `framework-driven-cli-binary-pattern.md` Stage 2 DRAFT v1.0 (454 lines)
- **Sister specs referenced (verified present):**
  - `wire-format-byte-preservation-discipline.md` (Layer 7 amendment present — cross-ref landed)
  - `canonical-sister-extension-discipline.md` (parent discipline)
  - `cfg-derived-consumer-framework.md` (composes — CLI is new consumer)
  - `autopopulate-pattern-for-production-caller-class.md` (composes — framework API inherits)
  - `meta-registry-pattern-for-codebase-registry-discipline.md` (composes — N/A unless CLI owns registry)
  - `structural-fix-preferred-decision-framework.md` (recurrence-count gating)
  - `pattern-codification-lifecycle.md` (stage progression)
  - `feedback_*` memories (4 cited: motivated-collaborator / no-defer / audit-canonical-sister / structural-fix-for-recurring-class)

---

## Per-focus-area verdict summary

| Focus area | Verdict | Severity-blocking? |
|---|---|---|
| 1. New DESIGN_SPEC structural validity | **YELLOW** | Non-blocking but Stage 2 lifecycle gap |
| 2. Phase L applies relevant DESIGN_SPECs correctly | **GREEN** | None |
| 3. DESIGN_SPECs catalog cross-references | **YELLOW** | Forward-ref + catalog entry gaps |
| 4. Pattern lifecycle staging | **GREEN** | Stage 1→7 progression coherent |
| 5. Hard invariants alignment (H1-H20) | **GREEN** | All applicable invariants respected |

**Overall verdict: YELLOW** — 2 non-blocking structural gaps in new spec; 1 catalog gap. NO RED findings; NO ship-blockers; Phase L coding can proceed after spec amendments below.

---

## Findings (severity-ordered)

### HIGH — H-1: New DESIGN_SPEC missing `## Audit detection` section (Stage 2 lifecycle requirement)

- **Surface:** `DESIGN_SPECS/framework-driven-cli-binary-pattern.md` (entire spec; no `## Audit detection` heading present per `grep -n "^## " | wc -l` = 16 section count vs Stage 2 requirement)
- **Pattern:** `pattern-codification-lifecycle.md` § Stage 2 line 71 — "**`## Audit detection` section** — symptoms that `/dod-audit` (or similar tooling) can grep for; enables auto-discovery + future enforcement"
- **Symptom:** Stage 2 lifecycle explicitly mandates `## Audit detection` section so that future `/dod-audit` runs can auto-detect this pattern's violations. Sister Stage 2 specs (`branchless-math-kernel-pattern.md:278` + `struct-padding-determinism-pattern.md:257`) both have this section. New spec has Problem statement / Design space / Pattern shape / Trade-offs / Reference implementations / Lessons / Patterns-NOT-used / Lifecycle / Cross-references — but NO Audit detection section.
- **Suggested fix:** add `## Audit detection` section between "## Lessons / gotchas" and "## Patterns NOT used here". Grep signatures should target:
  - `tools/*.sh` files emitting wire-format key=value lines AND mirroring `FOREACH_PER_CORE_CFG_FIELD` or related registries
  - bash scripts with `stamp_format_version=` or `hmac_*=` literals (cross-tool wire-format emit sites)
  - bash scripts with hardcoded wire-key emits matching pattern `<key>=<value>` where `<key>` exists in `FOREACH_*_CFG_FIELD`
  - Recurrence count signal: bash script header documenting ≥3 cross-tool sync events
- **Effort estimate:** ~10-20 min (add ~30-50 line section per sister-spec template)
- **Why HIGH:** Stage 2 spec is gated on this section per the lifecycle doc; without it the spec is technically Stage 2 INCOMPLETE; future audits can't auto-detect new applications of the pattern.

### HIGH — H-2: Forward references to new spec are NOT YET LANDED in sister specs

- **Surface:** sister specs that should cross-ref the new pattern
- **Pattern:** `pattern-codification-lifecycle.md` § Stage 2 (DRAFT) + § Stage 3 (first canonical) — sister specs should be amended to forward-ref the new spec when its concern overlaps
- **Symptom:** verified via grep `framework-driven-cli\|framework_driven_cli` across `DESIGN_SPECS/*.md`:
  - **Landed (1):** `wire-format-byte-preservation-discipline.md:352, 357` Layer 7 amendment correctly forward-refs `framework-driven-cli-binary-pattern.md` (GREEN)
  - **Missing (3 sister specs that should forward-ref but don't):**
    - `canonical-sister-extension-discipline.md` — spec body says "Parent discipline" and "this pattern WAS proposed via the discipline's audit" but the canonical-sister discipline itself has NO note pointing forward to framework-driven-cli-binary-pattern as a canonical-sister-discipline application
    - `cfg-derived-consumer-framework.md` — spec body says CLI is "new consumer of the framework" but the framework doc itself has no note about CLI binaries as a consumer class
    - `structural-fix-preferred-decision-framework.md` — spec body cites § Step 2 + 4× threshold but the framework doc has no example pointer to framework-driven-cli-binary-pattern as a canonical structural-fix application
- **Suggested fix:** at v1.14 amendment land time, add forward-ref notes in each of the 3 sister specs (single sentence each pointing to `framework-driven-cli-binary-pattern.md`). Alternative: defer to Stage 4 (subsequent applications) when 2nd canonical lands, per lifecycle pragmatism — but ship close should land at least the canonical-sister-extension + cfg-derived-consumer cross-refs since they're MOST load-bearing for future readers tracing pattern relationships.
- **Effort estimate:** ~15-20 min (3 single-sentence amendments)
- **Why HIGH:** without forward-refs, future readers of the sister specs won't discover this pattern when their work matches its trigger conditions. Cross-reference symmetry is a Stage 2+ lifecycle norm.

### MEDIUM — M-1: DESIGN_SPECS/README.md catalog entry not yet added for new spec

- **Surface:** `DESIGN_SPECS/README.md` — verified via grep `framework-driven\|cross-tool` → no entry exists for the new spec in catalog
- **Pattern:** `pattern-codification-lifecycle.md` § Stage 2 + `feedback_new_plans_use_future_oriented_template.md` (per `future-oriented-plan-template.md` Step 6 deliverable: "DESIGN_SPECs landed-amended")
- **Symptom:** README.md catalog at line 79 lists 57+ patterns in sub-sections "Framework discipline patterns (CLAUDE.md item 31 + DESIGN_PHILOSOPHY § 1.5)" at line 163 — appropriate home for the new spec but the entry is absent
- **Suggested fix:** add bullet entry to README.md under "Framework discipline patterns" section:
  ```
  - `framework-driven-cli-binary-pattern.md` — framework-driven CLI binary
    pattern (thin C++ wrapper over engine framework API); replaces bash
    scripts that mirror engine wire emit logic. Closes Class 18 / 19 / 21
    / 22 at cross-tool surface for framework-driven workflow tools.
    First canonical: `tools/stamp_model_cli.cpp` at v5.15.5.F.4d.1.B.3
    Phase L.
  ```
- **Effort estimate:** ~5 min
- **Why MEDIUM (not HIGH):** README catalog is for discovery; not a Stage 2 lifecycle requirement. But the auto-write contract (CLAUDE.local.md "DESIGN_SPECs landed-amended") implies the catalog amendment is part of "landed".

### MEDIUM — M-2: Pattern lifecycle Stage 5 promotion criteria — 2nd canonical projection could be sharper

- **Surface:** `DESIGN_SPECS/framework-driven-cli-binary-pattern.md` § Pattern lifecycle Stage 4-5 (lines 422-426)
- **Pattern:** `pattern-codification-lifecycle.md` Stage 5 — CLAUDE.md item promotion gated on ≥2 canonical applications
- **Symptom:** Stage 4 lists "future ships with cross-tool wire-format surfaces apply this pattern per the spec" but the `## Reference implementations` § Future application candidates table at lines 329-337 marks most candidates as "NO — diagnostic concern" or "MAYBE — if recurrence accumulates". Only 2 entries marked YES (Schema migration CLI; Per-core override emission CLI) — both gated on "if recurrence count ≥ 3". The spec is honest about this scarcity; HOWEVER it should be EXPLICIT that Stage 5 CLAUDE.md promotion is LOW-PROBABILITY in the near term unless a non-stamp surface accumulates recurrence.
- **Suggested fix:** amend Stage 5 entry to add: "Stage 5 promotion may take multiple ship cycles; this pattern is structurally rare (cross-tool wire-format mirror) and most cross-tool surfaces are diagnostic. If 2nd canonical doesn't materialize within 4-6 ships, consider promoting to CLAUDE.md anyway based on the singular structural-fix value at the stamp surface."
- **Effort estimate:** ~5 min
- **Why MEDIUM:** doesn't block the ship; lifecycle progression is honest. Optional sharpening.

### LOW — L-1: Stage 2 DRAFT version literal v1.0 marker placement

- **Surface:** `DESIGN_SPECS/framework-driven-cli-binary-pattern.md:4` — "Status: **Stage 2 DRAFT v1.0**"
- **Pattern:** Standard convention check — Stage 2 marker present? YES. Stage 3 forward-ref present? YES (Reference implementations § Stage 3 first canonical line 312-318). Stage 4-7 lifecycle present? YES (lines 415-431).
- **Symptom:** Stage 2 DRAFT marker correctly placed in frontmatter. Version literal "v1.0" is appropriate for first draft. Stage 3 canonical reference clear ("Stage 3 first canonical reference = `tools/stamp_model_cli.cpp` at `.B.3` ship close"). NO gaps.
- **Verdict:** CLEAN — Stage 2 DRAFT discipline correctly applied; literal not stale.

---

## Plan body cross-validation (Phase L scope)

### CLEAN — Phase L plan body claims verified against pattern spec

| Plan claim | Spec verification | Verdict |
|---|---|---|
| L1 lands NEW DESIGN_SPEC at workspace (`v1.0 DRAFT`) | Spec at workspace DESIGN_SPECS/; Stage 2 DRAFT v1.0 marker present | **CONFIRMED** |
| L2 = `tools/stamp_model_cli.cpp` ~150-200 LOC thin wrapper | Spec § Pattern Step 2 template body matches; 150-200 LOC range matches | **CONFIRMED** |
| L2 uses `stamp_write_for_model` framework API | API exists at `ML_Headers/ModelInference.hpp:1688` (verified via grep) | **CONFIRMED** |
| L2 CLI flag interface matches bash for operator continuity | Spec § Lessons "CLI flag interface naming continuity" + plan body Decision G citation; existing bash `tools/stamp_model.sh` flag inventory present | **CONFIRMED** |
| L3 build system: CMake `add_executable` + build.sh | Spec § Build system integration; sister precedent `tools/compare_scalers.cpp` (verified at `tools/` ls) | **CONFIRMED** |
| L4 verification: round-trip test + canonical body byte-identical | Spec § Step 5 verification template body; matches Decision F SOFT compat + Layer 5b discipline | **CONFIRMED** |
| L5 deprecation shim = 1-line `exec` redirect | Spec § Deprecation shim discipline + § Step 4; matches Decision F SOFT compat pattern | **CONFIRMED** |
| Phase L closes Class 18 + 19 + 21 + 22 at cross-tool surface | All 4 classes verified at `RECURRING_BUG_PATTERNS.md`:1106 / 1291 / 1371 / 1407; spec § Closes (cross-tool surface) line 18 cites all 4; closure mechanism is structural (CLI uses framework, no mirror possible) | **CONFIRMED** |
| Phase L composes with `cfg-derived-consumer-framework.md` (CLI = new consumer) | Spec line 9 "Composes with: `cfg-derived-consumer-framework.md` v1.2 (this pattern IS a new consumer of the framework — CLI is THIN wrapper over `populate_stamp_cfg_from_derived` + sister framework APIs)" | **CONFIRMED** |
| Phase L MUST land in same commit as Step 1.6.7.3 (version bump 1→2) | Plan body line 836 + 1003 — Layer 7 § Cross-tool version literal sync discipline; matches spec § Build system "Same compile flags + dependencies" | **CONFIRMED** |
| Phase L closes Layer 7 discipline AT THIS surface (still applies for non-framework surfaces) | `wire-format-byte-preservation-discipline.md:352-359` (Layer 7 amendment correctly explains framework-driven pattern OBVIATES Layer 7 at framework-driven surfaces only) | **CONFIRMED** |
| Stage 3 first canonical = `tools/stamp_model_cli.cpp` at this ship | Spec § Pattern lifecycle Stage 3 line 421; plan body Step L1-L6 sequence; ship tag `v5.15.5.F.4d.1.B.3` | **CONFIRMED** |
| TECH_DEBT-110 NEW = bash shim deletion target | Plan body line 1076-1078 (TECH_DEBT-110 entry with rationale + trigger); spec § Step 4 "≥1 ship cycle" matches | **CONFIRMED** |

---

## Hard invariants check (CLAUDE.md H1-H20 applicable to Phase L)

| Invariant | Applicability | Verification |
|---|---|---|
| H1 (no malloc/new/std::vector/std::string in framework code) | CLI is OFFLINE TOOL (not hot/slow path); std::string acceptable in main() for CLI parsing per H1 scope ("anywhere" applies to engine code paths; CLI tools have historically used getopt + char* per `tools/compare_scalers.cpp` precedent). Spec template § Step 2 uses `getopt_long` + `const char*` style — H1 conservative even though CLI is offline. | **GREEN** |
| H7 (hot path branchless) | N/A; CLI is offline | **N/A** |
| H8 (hot path p99 ≤500ns; slow path p99 ≤100μs) | N/A; CLI is offline | **N/A** |
| H9 (wire-format byte preservation) | CLI inherits via framework call (`stamp_write_for_model` does internal `LC_NUMERIC=C` pin + `%.17g` format); spec § Locale handling + § Build dependency confirm byte preservation by construction | **GREEN** |
| H10 (AVX-512 scalar fallback bytewise identical) | N/A; CLI doesn't dispatch SIMD | **N/A** |
| H13 (NO type-erased `*reinterpret_cast<T*>`) | CLI inherits framework's safe `tt::` dispatch via `stamp_write_for_model`; spec template § Step 2 uses typed `cfg.ridge_lambda = FPN_FromDouble<64>(...)` style — no reinterpret_cast | **GREEN** |
| H15-H19 (registry discipline) | CLI does NOT introduce new registries; H15 meta-registry enrollment N/A unless future evolution adds a registry | **N/A** |
| H20 (Branchless dispatch for SP/HP data-dependent code) | N/A; CLI is offline (decision-time data binding occurs in main(); not perf-sensitive) | **N/A** |

**Hard invariants verdict: GREEN** — all applicable invariants respected; no hot-path overhead introduced by Phase L; CLI surface is genuinely offline.

---

## Recommendations

### Address now (pre-Phase-L coding amendments to new spec)

1. **Add `## Audit detection` section** to `framework-driven-cli-binary-pattern.md` (HIGH H-1). Grep signatures for bash files mirroring `FOREACH_*_CFG_FIELD` wire emit. Sister-spec template available at `branchless-math-kernel-pattern.md:278+` for shape.

2. **Add forward-ref notes in 3 sister specs** (HIGH H-2): canonical-sister-extension-discipline + cfg-derived-consumer-framework + structural-fix-preferred-decision-framework. Single-sentence amendments each.

3. **Add README.md catalog entry** (MEDIUM M-1) under "Framework discipline patterns" subsection.

### Address during current ship (folded into Phase L step list)

4. (Optional sharpen) Amend Stage 5 promotion criteria language (MEDIUM M-2) — non-blocking.

### Defer with TECH_DEBT entry

None proposed. All findings are <30 min total amendment effort.

### CLEAN — no action

- Pattern lifecycle Stage progression (1→7) coherent
- Hard invariants compliance
- Cross-references to bug classes (18/19/21/22) all verified at source
- Reference implementations + sister C++ tool precedent (compare_scalers.cpp) verified
- Phase L plan body claims all match new spec body
- Decoupling roadmap positioning correctly cited (FOREACH_CLI_MODE precedent)

---

## Overall verdict: YELLOW

**Reasoning:**
- 2 HIGH non-blocking structural gaps (Audit detection section + sister-spec forward-refs)
- 1 MEDIUM catalog gap (README entry)
- 1 MEDIUM optional sharpening (Stage 5 promotion criteria)
- 0 CRITICAL findings; 0 RED findings; 0 ship-blockers
- All applicable hard invariants (H1-H20) respected
- Plan body claims all verified against pattern spec
- Pattern lifecycle Stage 2 correctly applied (with H-1 gap)

**Pre-coding amendment work: ~30-40 min total** (3 small amendments to new spec + 3 sister-spec forward-refs + README entry).

Phase L coding can proceed after these amendments land — they don't require waiting for Phase L code to verify (these are documentation completeness items in the new spec, not concerns about Phase L's structural correctness).

---

## Cross-references

- Plan body: `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` (v1.14)
- New DESIGN_SPEC audited: `DESIGN_SPECS/framework-driven-cli-binary-pattern.md` (Stage 2 DRAFT v1.0)
- Sister spec Layer 7 amendment landed: `DESIGN_SPECS/wire-format-byte-preservation-discipline.md:352-359`
- Lifecycle reference: `DESIGN_SPECS/pattern-codification-lifecycle.md` § Stage 2 line 71 (Audit detection requirement)
- Framework API verified: `ML_Headers/ModelInference.hpp:1688` (`stamp_write_for_model`)
- Bug classes verified: `DOCS/RECURRING_BUG_PATTERNS.md` Class 18 (line 1106) / Class 19 (line 1291) / Class 21 (line 1371) / Class 22 (line 1407)
- Sister C++ tool precedent: `tools/compare_scalers.cpp` (verified present at `tools/` ls)
- Sister spec audit detection conventions: `branchless-math-kernel-pattern.md:278` + `struct-padding-determinism-pattern.md:257`

---

**End of /dod-audit report.**
