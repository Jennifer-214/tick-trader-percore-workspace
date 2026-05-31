---
type: audit-methodology
stage: 2-draft
version: 1.0
established: 2026-05-31
tags: [audit-methodology, scope-discipline, finding-triage]
sister_specs: [audit-driven-pre-coding-gate.md, audit-report-format.md]
applies_at_skills: [/precoding-audit-gate, /parity-check, /trace-deps, /readiness, /merge-scan, /dod-audit, /accounting-audit, /registry-fit-audit, /hft-audit, /blindspot-scan]
---

# Audit finding-kind taxonomy (orthogonal axes for triage + sequencing)

**Established:** 2026-05-31 (#11 money-numeric-core gate; decision-log D-116).
**Status:** DRAFT — first application: the #11 gate's 14 findings + 6 completeness-critic bites (this session).

## Problem

Findings were tagged on ONE axis: **severity** {CRITICAL / HIGH / MED / LOW}. Severity captures *urgency* — but it under-determines the *response*. A `CRITICAL` wording fix and a `CRITICAL` core-rewrite are both "CRITICAL" yet demand 5 minutes vs 5 days, different work, and different sequencing. Triage stalls because severity alone can't tell you what KIND of work a finding is — so you can't batch, route, or order findings by it.

## The axes (orthogonal — keep them un-mixed)

A finding carries **three orthogonal tags + one flag**:

| Axis | Values | Answers |
|---|---|---|
| **Severity** | CRITICAL / HIGH / MED / LOW | *How urgent?* (gates sequencing priority — never whether-to-address) |
| **Kind** | mechanical / structural / design | *What work-type?* (drives the work-stream) |
| **Disposition** | fix-in-ship / fold-to-task / ledger-with-ID / document | *Where does it land?* |
| **Widespread** (flag) | true / false | *Does it need an enumeration sweep?* (the "did we find ALL N sites" check) |

Severity and kind are independent — any severity can be any kind. The common error (the one that triggered this spec) is **mixing axes**: `{critical, structural, widespread}` reads like three peers but is severity=CRIT × kind=structural × widespread=true.

### Kind definitions
- **mechanical** — plan-text / citation / wording / acceptance-criterion fix. No design thought; often *compiler-forced* (a type change makes it a build error until written). → batch inline, do cheaply / last.
- **structural** — changes architecture / wiring / scope; needs a *recorded decision* but not a new algorithm. → decide the fork + record (decision-log), then write up.
- **design** — needs a NEW function / algorithm / data-shape designed. → routes to the design pass (e.g. the `/precoding-audit-gate` new-fn design-audit). The expensive ones.

### Widespread flag
Set when the finding's risk is *incomplete enumeration* (boundary cohorts, N call-sites, dispatcher families) rather than a single fix — triggers the verify-every-site sweep (`feedback_verify_every_enumerated_site_at_close` / `feedback_enumerate_set_before_categorical_claim`). A finding can be any kind AND widespread.

## Shorthand (for conversation + synthesis cells)

`<SEV>·<kind>[·wide]` — e.g. `CRIT·design`, `CRIT·structural`, `HIGH·design·wide`, `MED·mechanical·wide`. Use it inline in discussion AND as the KIND/WIDESPREAD synthesis columns, so operator + agent refer to a finding by its *shape*, not just its number. (This is the "easier conversation" payoff — a shared, compact triage vocabulary.)

## Kind → sequencing (the payoff: the tags ARE the order)

| Kind | Work-stream | When |
|---|---|---|
| design | the design pass (new-fn design-audit) | first — gates everything (the hard part) |
| structural | decide the fork + record | the decisions that gate the design |
| mechanical | batch plan-text edits | last / cheap |
| widespread (any kind) | enumeration sweep — verify every site | folded into whichever stream owns it |

Tagging by kind is not just labeling — it **partitions the findings into ordered work-streams**. That is *why* it speeds triage: read severity for urgency, kind for the plan.

## Composition with the response menu

Kind feeds `feedback_proportionate_response_to_audit_findings`'s A-D menu: **mechanical → (A) INLINE MERGE**; **structural → (B) ACCEPT or (C) FOLD**; **design → (D) ARCHITECT / route-to-design-pass**. Kind names the *shape*; the menu picks the *response*; disposition records *where it lands*. Three layers, one finding.

## Worked example — the #11 money-numeric-core gate (2026-05-31)

| # | Finding | Tag |
|---|---|---|
| C1 | which binary body `<2,64>` inherits (hoist vs regen) | `CRIT·design` |
| C2 | rounding is introduce, not swap | `CRIT·design·wide` |
| C3 | LIVE computes fees vs booking reported | `CRIT·structural` |
| C4 | fill path is `double`, missed boundary | `CRIT·design·wide` |
| C5 | decimal struct H12 layout | `CRIT·structural` |
| H1 | decimal Mul is a `__udivti3` libcall | `HIGH·design` |
| H2 | producer EMA muls / `ema_price` domain | `HIGH·structural·wide` |
| H3 | emit funnels through `FPN_ToDouble` ×3 | `HIGH·mechanical·wide` |
| H4 | FOREACH_EXCHANGE is a `.E.1` sister | `HIGH·structural` |
| B-α | order-submit quantization incomplete | `HIGH·design` |
| B-β | log/metrics money emit lossy (un-defer F-107) | `MED·mechanical·wide` |
| B-ε | compute-vs-storage split firm in P1 | `HIGH·structural` |

Reading the `design` rows IS the #11 design-pass agenda (C1/C2/C4/H1/B-α); the `structural` rows are the forks to decide (C3/C5/H2/H4/B-ε); the `mechanical` rows batch last (H3/B-β).

## Rollout
- **`/precoding-audit-gate` Stage 4 synthesis** — findings tables carry a KIND + WIDESPREAD column (landed with this spec).
- **Per-audit return format** — each audit tags its findings with the shorthand (queued; in the interim the gate's subagent-prompt template carries the instruction).
- **`feedback_proportionate_response_to_audit_findings`** — references this axis (the kind→menu mapping).

## Sister disciplines
- `audit-driven-pre-coding-gate.md` — the gate this taxonomy tags findings within.
- `audit-report-format.md` — the standardized report *container*; severity already lives in its finding shape, and each finding now also carries this taxonomy's `<SEV>·<kind>` tag (kind = the added per-finding axis).
- `implementation-layer-blindspot-taxonomy.md` (M4) — sibling taxonomy (kinds of *blind-spot*); this is kinds of *finding*. (The standing completeness-critic, D-119, is the surface-coverage axis of "what's missing"; that taxonomy is the code-detail axis.)
- `feedback_proportionate_response_to_audit_findings` (memory) — kind → response menu.
- `feedback_address_med_low_findings_not_just_high_crit` (memory) — every finding gets a disposition regardless of severity; this adds the kind dimension to that completeness.
