---
type: ledger-template
stage: 2-draft
version: 1.0
established: 2026-05-18
tags: [ledger-discipline, plan-template, doc-discipline]
surface: []
sister_specs: [doc-frontmatter-convention.md, doc-tag-vocabulary.md]
applies_at_skills: [/ship, /post-ship-audit, /bug-check]
---

# Ledger entry templates (consolidated)

**Established:** 2026-05-18 (v5.15.5.F.4d.1.B.3 doc-layer refresh — codify per-entry templates for all ledgers)
**Status:** Stage 2 DRAFT v1.0 — Stage 3 first canonical at next ledger entry creation; full migration at TECH_DEBT-115 Phase 3

Consolidated per-entry templates for all auto-write ledgers in the doc system. One doc covers all ledger types (less file proliferation; same templating discipline).

---

## Covered ledgers

| Ledger | Path | Per-entry template section below |
|---|---|---|
| TECH_DEBT | `DOCS/TECH_DEBT.md` | § TECH_DEBT entry |
| RECURRING_BUG_PATTERNS Class | `DOCS/RECURRING_BUG_PATTERNS.md` | § Bug Class entry |
| PARITY_ISSUES | `DOCS/PARITY_ISSUES.md` | § Parity issue entry |
| FEATURE_LOOKUP | `FEATURE_LOOKUP.md` | § Feature lookup entry |
| LANDMINES | `DOCS/LANDMINES.md` | § Landmine entry |
| HOT_PATH_CHANGELOG | `DOCS/HOT_PATH_CHANGELOG.md` | § Hot path changelog entry |

---

## § TECH_DEBT entry

**Frontmatter (per doc-frontmatter-convention.md):**

```yaml
---
id: TECH_DEBT-NNN
severity: low | medium | high
surface_tags: [<surface-tags per doc-tag-vocabulary.md>]
trigger: explicit-operator | next-maintenance-window | recurrence-count-N | sub-ship-Y
status: open | in-flight | closed
related_specs: [<DESIGN_SPECS paths>]
opened: YYYY-MM-DD
closed: YYYY-MM-DD  # only when status: closed
---
```

**Body sections (required):**

```markdown
### TECH_DEBT-NNN — <title>

- **Created:** YYYY-MM-DD (<context: what sprint/sub-ship surfaced this>)
- **Severity:** LOW | MEDIUM | HIGH (matches frontmatter)
- **Surface:** <what code/doc this touches; specific file/cluster/subsystem>
- **Sister:** <related TECH_DEBT entries or DESIGN_SPECS>
- **What's deferred:** <concrete description of work>
- **Why deferred (NOT effort-avoidance):** <rationale per `feedback_no_defer_for_effort.md` — sub-ship cycle priority / safety-bounded / specific technical reason; never "we'll get to it later">
- **Cost estimate:** <focused-work hours>
- **Trigger:** <explicit condition that opens this for action; NOT vague "future ship">
- **Status:** <open with trigger | in-flight at sub-ship X | closed at sub-ship Y>
- **Accountability mechanism:** <how this entry stays visible until acted on>
- **Cross-ref:** <DESIGN_SPECS / memory / sister TECH_DEBT entries>
```

**Worked example:** TECH_DEBT-110, -111, -112, -113, -114, -115 (all created at `.B.3` ship close 2026-05-18) demonstrate this shape.

---

## § Bug Class entry

**Frontmatter:**

```yaml
---
class_id: N
title: <one-line description>
surface_tags: [<surface-tags>]
severity: blocker | high | medium | low
recurrence_count: N
first_instance: vX.Y.Z (YYYY-MM-DD)
closure_mechanism: <how this class is closed structurally — DESIGN_SPEC / CI tool / framework discipline>
sister_classes: [<class IDs with overlapping concerns>]
---
```

**Body sections (required):**

```markdown
### Class N: <title>

**Detection signature:**
<Code/doc pattern that identifies an instance of this class>

**Why this is a class (not a one-off bug):**
<What pattern recurrence; first 2-3 instances cited as canonical history>

**Closure mechanism:**
<Specific DESIGN_SPEC or CI tool or framework discipline that closes this class structurally>

**False-positive surface (per M3 discipline):**
<What looks like Class N but isn't — distinguishes legitimate siblings; per `feedback_recurring-bug-pattern-anti-pattern-codification-distinguishes-legitimate-siblings`>

**Worked instances:**
- v5.X.Y (YYYY-MM-DD): <site> — <closure>
- v5.X.Z (YYYY-MM-DD): <site> — <closure>

**Sister classes:**
- Class N+1: <relationship>
- Class N-2: <relationship>

**Cross-ref:** <DESIGN_SPECS / TECH_DEBT / memory entries>
```

**Worked example:** RECURRING_BUG_PATTERNS.md Class 18 (sister-registry mirror-incomplete) + Class 21 (parallel wide-variant registries at auto-flow surface) + Class 23 (type-erased reinterpret_cast dispatch) demonstrate this shape.

---

## § Parity issue entry

**Frontmatter:**

```yaml
---
id: PARITY-NNN
title: <one-line description>
surface_tags: [<surface-tags>]
severity: blocker | high | medium | low
parity_axis: train↔serve | live↔backtest | scalar↔SIMD | wire-format-roundtrip | etc.
status: open | in-flight | closed
detected_at: vX.Y.Z (YYYY-MM-DD)
closed_at: vX.Y.Z (YYYY-MM-DD)
related_specs: [<DESIGN_SPECS paths>]
---
```

**Body sections (required):**

```markdown
### PARITY-NNN — <title>

- **Detected:** vX.Y.Z (YYYY-MM-DD) (<context>)
- **Parity axis:** train↔serve / live↔backtest / scalar↔SIMD / wire-format-roundtrip / etc.
- **Surface:** <files / structs / functions impacted>
- **Symptom:** <what diverged + observable behavior>
- **Root cause:** <why divergence occurred>
- **Fix:** <commit + ship-tag + DESIGN_SPECS amendments>
- **Sister parity issues:** <related PARITY entries>
- **Closure verification:** <test / audit / CI tool that proves parity now>
- **Cross-ref:** <DESIGN_SPECS / TECH_DEBT entries>
```

---

## § Feature lookup entry

**Frontmatter:**

```yaml
---
feature_name: <name>
introduced: vX.Y.Z (YYYY-MM-DD)
surface_tags: [<surface-tags>]
status: shipped | deprecated | retired
related_specs: [<DESIGN_SPECS paths>]
---
```

**Body sections (required) — per CLAUDE.local.md auto-write contracts:**

```markdown
### <feature-name> (vX.Y.Z+)

**What:** <one-line description>

**Cfg flags:** <list of `cfg.X` fields that toggle this feature>

**Fallback:** <what happens when feature DISABLED>

**Where to verify:** <file:line OR DESIGN_SPECS path OR test name>

**Paper-test sanity:** <how operator verifies feature working in paper-test>

**Gotchas:** <known edge cases, race conditions, library quirks>

**Related:** <sister features / DESIGN_SPECS / TECH_DEBT entries>
```

**Skip when:** Pure refactors / internal helper extraction / bug fixes restoring expected behavior / bytewise-identical perf optimizations.

---

## § Landmine entry

**Frontmatter:**

```yaml
---
id: LANDMINE-NNN
title: <one-line description>
surface_tags: [<surface-tags>]
severity: pthread-quirk | library-quirk | os-quirk | race-condition | other
debug_hours: N  # how long to debug if hit; landmines = >1h
status: known | mitigated | resolved
related_specs: [<DESIGN_SPECS paths>]
---
```

**Body sections (required):**

```markdown
### LANDMINE-NNN — <title>

- **Encountered:** YYYY-MM-DD (<context: which ship / what triggered investigation>)
- **Surface:** <library / OS facility / language quirk>
- **Symptom:** <what observable behavior looked like — usually mysterious>
- **Root cause:** <real explanation; often non-obvious>
- **Debug time:** N hours (qualifies as landmine if >1h)
- **Mitigation:** <how to avoid hitting again; specific code/cfg pattern>
- **Detection in future code:** <signature that suggests this landmine present>
- **Cross-ref:** <DESIGN_SPECS / TECH_DEBT / sister landmines>
```

**Worked example:** XGBoost+libgomp pthread parallelism landmine (v5.11.45) — current sole entry.

---

## § Hot path changelog entry

**Frontmatter:**

```yaml
---
id: HOTPATH-NNN
ship_tag: vX.Y.Z
title: <one-line description of what changed on hot path>
delta_ns: <p99 delta in nanoseconds; positive = slower, negative = faster, 0 = neutral>
surface_tags: [hot-path]
measurement_method: perf-stat | bench-harness | calls-graph-diff | manual-microbenchmark
related_specs: [<DESIGN_SPECS paths>]
---
```

**Body sections (required) — per H8 ship-blocker discipline:**

```markdown
### HOTPATH-NNN — vX.Y.Z — <title>

- **Ship:** vX.Y.Z (YYYY-MM-DD)
- **Hot path delta (p99):** +N ns / -N ns / unchanged
- **Sister pattern:** <DESIGN_SPECS path; e.g., branchless-dispatch-discipline.md>
- **Measurement method:** <perf stat / bench-harness / calls-graph-diff>
- **Acceptance:** verifies H8 hot-path p99 ≤500ns budget intact (or HOT_PATH_CHANGELOG entry justifies)
- **Reason for change:** <what feature/closure required hot-path modification>
- **Verification:** <test or measurement that demonstrates p99 maintained>
- **Cross-ref:** <DESIGN_SPECS / TECH_DEBT / sister ships>
```

**Worked examples:** v5.12.1.A.2 staleness gate (+1-2ns); v5.12.1.B.3 staleness mask (+1-2ns); v5.14.x kill-switch atomic read (+0ns).

---

## Auto-write integration

Per CLAUDE.local.md "Auto-write contracts" table:

| Ledger | Auto-write trigger | Auto-fire skill |
|---|---|---|
| TECH_DEBT | `/readiness` Check 25 / `/merge-scan` / scope-discussion deferral / sub-ship close | `/ship` postmortem step |
| Bug Class | New anti-pattern instance found by audit / pattern recurs across 3+ sites | `/bug-check` codification step |
| Parity issue | `/parity-check` finding / wire-format divergence detected | `/parity-check` skill |
| Feature lookup | New cfg flag / observability / persistence / boot gate / training knob / fallback | `/ship` skill at sub-ship close |
| Landmine | Operator surfaces >1h debug experience | Manual; `/handoff` skill prompts if surfaces during ship |
| Hot path changelog | `tools/calls_graph_diff.sh` detects hot-path modification | `/ship` skill at sub-ship close |

---

## Cross-references

- Sister: `doc-frontmatter-convention.md` (frontmatter discipline)
- Sister: `doc-tag-vocabulary.md` (tag vocabulary)
- Sister: `feedback_no_defer_for_effort.md` (TECH_DEBT deferral discipline)
- Sister: M3 meta-discipline (per DESIGN_PHILOSOPHY § 11.5 — Bug Class false-positive surface)
- CLAUDE.local.md § Auto-write contracts (ledger auto-write triggers)
- TECH_DEBT-115 (institutional-memory rollout — Phase 3 migrates existing ledger entries to frontmatter)

---

## Pattern lifecycle

- **Stage 1 (problem identification):** Caramel surfaced 2026-05-18 — "do we need a new way to handle the TECH_DEBT and RECURRING BUG CLASSES, etc with any of these updates as well?"
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-18)
- **Stage 3 (first canonical):** next ledger entry created uses this template (immediate)
- **Stage 4 (cohort migration):** all existing ledger entries migrate to YAML frontmatter at TECH_DEBT-115 Phase 3 (`.D` candidate ship)
- **Stage 5+ (mature):** ledger entries scaffold from this template via `/doc-create <ledger-type>` skill (queued)

---

**End of ledger-entry-templates v1.0 DRAFT.** Stage 3 first canonical applies to next ledger entry created.
