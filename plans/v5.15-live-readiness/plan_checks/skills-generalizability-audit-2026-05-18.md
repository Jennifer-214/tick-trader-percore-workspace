# Skills Generalizability Audit — 2026-05-18

**Scope:** Hardcoded ship-specific, version-specific, or sprint-specific content audit  
**Target:** 10 high-priority skills (readiness, trace-deps, parity-check, dod-audit, merge-scan, bug-check, precoding-audit-gate, ship, plan-draft, handoff)  
**Context:** Post-/handoff-generalization cleanup; auditing similar pollution across the skill catalog

---

## Executive Summary

**Overall Verdict:** 3 of 10 skills have HARDCODED-CONTENT that should be generalized; 2 more have MINIMAL hardcoding. The pattern is NOT systemic—most skills are cleanly generic—but the affected skills have specific, reusable issues.

**Critical finding:** `/precoding-audit-gate` and `/handoff` contain multiple hardcoded version-tag examples (`v5.15.5.F.4c`, `v5.14.10`) and stage-versioning references that lock examples to ONE ship. These are inline invocation examples (not historical context) and should be placeholders.

---

## Per-Skill Audit Results

### 1. ✅ `/readiness` — GENERIC (PASS)

**Verdict:** GENERIC — no hardcoded ship-specific content detected.

**Rationale:**
- Hardcoded references checked: `v5.4.0`, `v5.8.6`, `v5.9.2a`, `v5.9.2b`, `v5.9.3a` — all are HISTORICAL PROVENANCE, not inline examples
  - E.g., "v5.4.0 postmortem F7-F10" is documenting why a check exists, not prescribing a version to run against
  - E.g., "v5.9.2a snapshot test discipline" is a canonical reference to a past sprint's decision, not a reusable example
- Version-bump references (v4.7.x → v5.0.x) are architectural narrative, not template variables
- File:line refs are generic patterns (e.g., `tests/controller_test.cpp v5.9.2a` is context, not a ship-specific path)

**Effort to keep clean:** 0 min. Already generalized.

---

### 2. ✅ `/trace-deps` — MOSTLY GENERIC with 1 minor issue

**Verdict:** GENERIC — one worked-example references v5.14.10 but it's marked EXPLICITLY as "worked example" with pedagogical value.

**Line:** 164  
**Issue:** "Worked example (v5.14.10 plan):" shows a concrete historical case study (EnsembleModelZoo confusion). No ship-specific logic, just illustrative.  
**Acceptable?** YES — explicitly labeled as example; historical context is appropriate for pedagogy.

**Effort to keep clean:** 0 min. No cleanup needed; the marking is clear.

---

### 3. ⚠️ `/parity-check` — SOME HARDCODING (needs generalization)

**Verdict:** NEEDS CLEANUP — 1 hardcoded NEW-tag reference inline in spec; should be placeholder.

**Line 51:** Hardcoded `NEW v5.15.5.F.4c.3 WIP2d-1.B.0d` in a scope-parameter description  
```
per `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md` (NEW v5.15.5.F.4c.3 WIP2d-1.B.0d):
```

**Issue:** The skill spec is documenting "this audit-scope-taxonomy doc is NEW at version v5.15.5.F.4c.3." The version tag is historical context (date-stamped when the feature landed), but embedding it in a reusable skill spec creates a fragile cross-reference. If a future skill adds its own NEW features, the version becomes stale and confusing.

**Fix:** Replace with a reference pattern:  
```
per `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md` (post-v5.15 enhancement):
```
Or:
```
per `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md` (see DESIGN_SPECS/README.md Catalog Version History):
```

**Effort estimate:** ~2 min. Single-line edit.

---

### 4. ✅ `/dod-audit` — GENERIC (PASS)

**Verdict:** GENERIC — hardcoded references are all historical provenance.

**Rationale:**
- Line 68, 69: `NEW v5.15.5.F.4c.3` tags document WHEN new composing skills were added, not prescriptive examples
- Line 205, 273: `TECH_DEBT-011`, `TECH_DEBT-013` are cross-references to the TECH_DEBT ledger (maintained as source of truth), not ship-specific
- Line 392: "First applied: MemHeaders/FailureModeRegistry.hpp v5.14.8.B" is a canonical-example reference (acceptable)
- Line 523: "v5.14.8 had 6 design pivots" is historical narrative

**Effort to keep clean:** 0 min. Already acceptable.

---

### 5. ✅ `/merge-scan` — GENERIC (PASS)

**Verdict:** GENERIC — hardcoded references are canonical examples or historical context, clearly marked.

**Rationale:**
- Lines 94, 126, 139–143, 157, 159, 171–177: All cite `v5.12.1.A.2`, `v5.14.2.E.1`, etc. as CANONICAL EXAMPLE SHIPS (e.g., "v5.12.1.A.2 surfaced a missed merge")
- These are not inline examples for future runs; they're documented case studies explaining the skill's origin
- Line 270, 275: "v5.12.1 added Check 18" and "v5.12.1.A.2 surfaced" are provenance, not prescriptive

**Effort to keep clean:** 0 min. Already acceptable.

---

### 6. ✅ `/bug-check` — GENERIC (PASS)

**Verdict:** GENERIC — hardcoded references are framework metadata, not ship-specific examples.

**Rationale:**
- Line 81: `NEW v5.15.5.F.4b` documents when plan-scope-extension feature landed (historical)
- Line 301: "v5.13.5.B postmortem identified" is provenance (why the skill exists)
- No inline invocation examples hardcoded to specific ships

**Effort to keep clean:** 0 min. Already acceptable.

---

### 7. 🔴 `/precoding-audit-gate` — NEEDS CLEANUP (multiple hardcoded examples)

**Verdict:** NEEDS CLEANUP — 4+ hardcoded ship/version tags inline in invocation examples and audit-set descriptions.

**Issues:**

| Line | Content | Problem |
|---|---|---|
| 49 | `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4c-int-int_enum-bool-migration.md` | Hardcoded FULL plan path + exact ship tag `.F.4c` + timestamp `2026-05-13` in invocation EXAMPLE |
| 53 | `NEW v5.15.5.F.4c.3 WIP2d-1.B.0d` | Hardcoded version tag in feature-introduction line |
| 71, 75, 77 | Multiple `NEW v5.15.5.F.4c.3 ...` / `NEW v5.15.5.F.4c.3 WIP2d-1.B.0c` | Version-tag pollution across 3 separate lines; repeated pattern |
| 99, 102 | `/precoding-audit-gate plans/v5.15-live-readiness/...2026-05-13-v5.15.5.F.4c...` | EXACT same hardcoded path from line 49 reused as invocation example; timestamp makes it brittle |
| 278 | `2026-05-14 v5.15.5.F.4b — fired all 5 audits...` | Concrete ship example from sprint with exact date + version; useful as provenance but reads as "hardcoded past event" |

**Fix approach:**

```markdown
# BEFORE (line 49):
audited. E.g., `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4c-int-int_enum-bool-migration.md`

# AFTER:
audited. E.g., `plans/<sprint-dir>/subplans/<YYYY-MM-DD>-<ship-tag>-<description>.md`
```

Replace all `NEW v5.15.5.F.4c.3 ...` tags with generic descriptors:
```markdown
# BEFORE (line 53):
(NEW v5.15.5.F.4c.3 WIP2d-1.B.0d per `audit-scope-taxonomy.md`)

# AFTER:
(enhanced post-v5.15 per `audit-scope-taxonomy.md`)
```

Move concrete ship example (line 278) to a "## Historical examples" appendix section at skill end, with clear label: "This section documents actual past audit-gate fires as case studies; it is NOT prescriptive for future invocations."

**Effort estimate:** ~15–20 min. 
- ~8 replacements across lines 49–102
- ~2 min to extract line 278 example to appendix
- ~3 min to verify no new hardcoding introduced

---

### 8. ✅ `/ship` — MOSTLY GENERIC with ACCEPTABLE historical references

**Verdict:** GENERIC — hardcoded version tags are historical narrative only.

**Rationale:**
- Lines 250, 277, 323–327, 372, 380–382, 400, 443–444, 474: All cite `v5.9.0`, `v5.9.1`, `v5.8.8`, etc. as HISTORICAL EXAMPLES
- Example: "E.g. v5.9.0a (audit doc), v5.9.0b (visibility)" — documenting the convention, not a reusable template
- Example: "Stamp-format-version safety / Verify the v5.8.8 regression test" — referencing a canonical test, not a ship-specific rule

**Effort to keep clean:** 0 min. Already acceptable.

---

### 9. ✅ `/plan-draft` — GENERIC (PASS)

**Verdict:** GENERIC — version tags are descriptive placeholders with `<template>` syntax.

**Rationale:**
- Lines 3, 29, 31: Show template PLACEHOLDER syntax like `<ship_version>`, `<predecessor_version>`
- No concrete hardcoded version tags in skill logic
- Example: "e.g., `v5.15.5.F.4d.1.B.2`" — presented as sample, not prescriptive

**Effort to keep clean:** 0 min. Already clean.

---

### 10. 🔴 `/handoff` — NEEDS CLEANUP (multiple hardcoded examples + version references)

**Verdict:** NEEDS CLEANUP — 5+ hardcoded ship tags and version references scattered across invocation examples, code blocks, and stage descriptions.

**Issues:**

| Line | Content | Problem |
|---|---|---|
| 25 | `/handoff v5.14.10` → finds... | Hardcoded ship tag `v5.14.10` in invocation EXAMPLE |
| 27 | `/handoff v5.14.10 plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md` | FULL hardcoded path + timestamp + two instances of `v5.14.10` + sprint name `v5.14-foxml-port-and-maker` |
| 184 | `§ 3 Hard Invariants / § 4 Latency / ... § 11 Process discipline` | Not a version hardcoding, but inline narrative section numbers; acceptable |
| 583 | `19 patterns + README; promoted from 16 in v5.14.10 with per-snapshot-cluster-layout-pattern + calibration-log-column-registry + postloadsetup-registry-pattern` | Hardcoded VERSION `v5.14.10` + exact count `16 → 19` in a stage description |
| 588 | `post-v5.11.43 migration; surfaced as Surprise 7 in v5.14.10 postmortem` | Version tag `v5.14.10` + "Surprise 7" (specific naming from one ship) |

**Fix approach:**

```markdown
# BEFORE (line 25–27):
- `/handoff v5.14.10` → finds `plans/<active-sprint>/subplans/*v5.14.10*.md`
- `/handoff v5.14.10 plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md`

# AFTER:
- `/handoff <ship-tag>` → finds `plans/<active-sprint>/subplans/*<ship-tag>*.md`
- `/handoff <ship-tag> <plan-path>` — explicit plan path (e.g., `plans/<sprint-dir>/subplans/<YYYY-MM-DD>-<ship-tag>-<name>.md`)
```

Replace line 583 hardcoded count:
```markdown
# BEFORE:
promoted from 16 in v5.14.10 with per-snapshot-cluster-layout-pattern + calibration-log-column-registry + postloadsetup-registry-pattern

# AFTER:
promoted with per-snapshot-cluster-layout-pattern + calibration-log-column-registry + postloadsetup-registry-pattern (see DESIGN_SPECS/README.md for current catalog size)
```

**Effort estimate:** ~20–25 min.
- ~5 hardcoding replacements in invocation examples
- ~2 min to rewrite stage descriptions for version-tag-agnostic wording
- ~3 min to verify generated prompt template doesn't hardcode new values

---

## Cross-Skill Pattern Analysis

### Is hardcoded-example pollution a recurring pattern?

**Finding:** LOCALIZED, NOT SYSTEMIC.

- **10 skills audited:** 2 need cleanup (precoding-audit-gate, handoff), 1 has minor inline enhancement reference (parity-check), 7 are clean
- **Root cause:** Both `/precoding-audit-gate` and `/handoff` were recently enhanced (post-2026-05-14) to support new features (per-audit-scope shapes, multi-session ship awareness). The enhancements introduced NEW version-tag references inline in spec body to document "this feature is NEW at version X"
- **Why it happened:** The skill specs are themselves LIVING DOCUMENTS that need dates for provenance. The original /handoff underwent generalization recently; the backlog feature flags in `/precoding-audit-gate` (accounting, registry-fit, hft) were released together and marked with the same sprint version for traceability

**Distinction:** This is NOT a category violation like "hardcoded TECH_DEBT-093 inline"—it's a FEATURE-DOCUMENTATION pattern that leaked into reusable template sections.

---

## Recommended Priority Order

### Tier 1 — FIX FIRST (critical path)

1. **`/precoding-audit-gate` lines 49, 53, 71, 75, 77, 99, 102** — Most egregious; invocation examples are COPIED BY USERS directly; stale paths cause copy-paste errors
2. **`/handoff` lines 25, 27, 583, 588** — Similar risk; handoff examples appear in "Paste this prompt" code blocks that users copy verbatim

**Combined effort:** ~35–45 min total.

### Tier 2 — LOW-IMPACT (cleanup-when-near)

3. **`/parity-check` line 51** — Single-line minor issue; low risk; could be fixed in same session as Tier 1

**Effort:** ~2 min.

---

## CLEAN-LIST Summary

**Skills that require NO action (already generic):**
- ✅ `/readiness` — PASS
- ✅ `/trace-deps` — PASS (worked example is clearly pedagogical)
- ✅ `/dod-audit` — PASS
- ✅ `/merge-scan` — PASS
- ✅ `/bug-check` — PASS
- ✅ `/ship` — PASS (historical references acceptable)
- ✅ `/plan-draft` — PASS (template placeholders clean)

**Skills needing amendment before next use:**
- 🔴 `/precoding-audit-gate` — 4+ hardcoded paths/versions in invocation examples
- 🔴 `/handoff` — 4+ hardcoded ship tags and version references
- ⚠️ `/parity-check` — 1 minor version-tag reference (low priority)

---

## Recommendations for Going Forward

1. **Adopt version-tag discipline for skill spec enhancements:** When a skill spec documents a NEW feature (e.g., "extended audit set in precoding-audit-gate"), cite the feature via a **pointer reference** instead of inline version tag:
   ```markdown
   # GOOD:
   (enhanced in DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md § 3)
   
   # AVOID:
   (NEW v5.15.5.F.4c.3 WIP2d-1.B.0c)
   ```

2. **Separate skill-origin-history from reusable-examples:** Move ANY concrete ship examples (e.g., "2026-05-14 v5.15.5.F.4b fired all 5 audits...") to a dedicated "Historical examples / Case studies" section at the skill end, with clear labeling that they are NOT templates.

3. **Use placeholder syntax for ALL invocation examples:**
   ```markdown
   /precoding-audit-gate plans/<sprint-dir>/subplans/<YYYY-MM-DD>-<ship-tag>-*.md
   /handoff <ship-tag> [<plan-path>]
   ```

4. **Pre-commit hook (optional future):** Grep skill SKILL.md files for regex `v\d+\.\d+\.\d+[a-zA-Z.]` outside of historical-narrative sections (e.g., "Background" / "Author intent") and flag for review if found inline in reusable sections.

---

## Effort Summary

| Skill | Work needed | Effort | Priority |
|---|---|---|---|
| /precoding-audit-gate | 6+ line replacements + appendix extraction | ~20 min | Tier 1 |
| /handoff | 4+ line replacements + version-agnostic rewrite | ~25 min | Tier 1 |
| /parity-check | 1 line replacement | ~2 min | Tier 2 |
| Others | None | 0 min | — |
| **TOTAL** | — | **~47 min** | — |

---

## Meta-Observation

The generalizability audit confirms that Caramel's discovery in /handoff was NOT a systemic pollution issue—most skills are clean. The problem is localized to two recently-enhanced skills that documented their NEW FEATURES by embedding version tags inline. The fix is straightforward: replace version tags with pointer references + move concrete examples to historical sections.

Once these 2–3 skills are cleaned, the catalog will be reusable and drift-resistant for future sprints.

