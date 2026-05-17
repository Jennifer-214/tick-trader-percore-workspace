# /anti-spaghetti — Structural codebase audit for parallel-infrastructure anti-patterns

**Established:** 2026-05-17 (v5.15.5.F.4d.1.B planning — codified during deep design conversation when Caramel asked "is this codebase becoming spaghetti?")
**Status:** **Stage 3 ACTIVE v1.1** (promoted from Stage 2 DRAFT at `v5.15.5.F.4d.1.B.1` ship close 2026-05-17; first canonical run at `.B` audit Batch 2 found 3-way triplet CRITICAL + CoreCtx HIGH + 6 MEDs KEEP; methodology retroactively validated; periodic cadence locked per `project_anti_spaghetti_audit_cadence` memory)

**Tags:** structural-audit, framework-discipline, registry-driven, pre-coding-gate, periodic-health-check

---

## Purpose

Scan the codebase for **structural duplications at framework boundary** — specifically the class of anti-patterns where parallel infrastructure has been built when a canonical sister pattern exists. This is the meta-pattern that produces Class 14 (scattered manual cfg sites), Class 18 (mirror), Class 19 (hardcoded enum names in gating), Class 21 (parallel wide-variant at auto-flow surfaces), Class 27 (scalar cfg-mirror caches).

The skill answers: "Where in the codebase have we added new infrastructure when canonical sister exists?"

## When to fire

- **Periodic codebase-wide health check** (quarterly, or when "is this becoming spaghetti?" comes up)
- **Post-new-anti-pattern-codification sweep** (after a new Class is added to `RECURRING_BUG_PATTERNS.md`, scan for additional instances)
- **Pre-coding audit gate dimension** for plans proposing new framework infrastructure (specifically: any new X-macro registry / metadata bit / dispatch table / sidecar / consumer macro)
- **After Path γ-class structural critique surfaces** during a plan's pre-coding gate (validate no sister-shape duplication exists elsewhere)
- **Operator instinct check** — when something "feels parallel" but isn't obviously broken yet

## When NOT to fire

- Single-file or isolated-feature audit (use `/dust` for generic cleanup OR `/bug-check` for known-class instance scan)
- Hot-path latency analysis (use `/hft-audit` or `/latency-track`)
- ML-pipeline parity audit (use `/ml-audit` or `/parity-check`)
- DESIGN_SPECS pattern application against the catalog (use `/dod-audit`)

## Distinct from existing skills

| Skill | Concern | Granularity |
|---|---|---|
| `/bug-check` | Instances of known bug classes from `RECURRING_BUG_PATTERNS.md` | line-level instance scan |
| `/dod-audit` | DESIGN_SPECS pattern application | per-section against catalog |
| `/merge-scan` | Reuse-merge opportunities (atomic loads, fn bodies, fields) | code-level pattern |
| `/dust` | Generic cleanup (comments, oversized fns, dead code) | per-file mechanical |
| **`/anti-spaghetti`** | **Structural duplications at framework boundary** (registries, dispatch tables, consumer macros, gates) | **architecture-level** |

The distinguishing thing: `/anti-spaghetti` looks at **whole-registry pairs + their consumer ecosystems** asking "do these encode the same thing twice with drift potential?" — not "is this single site buggy?"

## Methodology (5 phases)

### Phase 1 — Enumerate all FOREACH_* registries

```bash
rg -tcpp '#define FOREACH_[A-Z_]+\(X\)' /home/caramel/code/FoxML_Trader_v2/ --include="*.hpp" --include="*.cpp"
```

Output: every X-macro registry. Note file:line + name + approximate row count + header doc comment.

### Phase 2 — Per registry, extract metadata signature

For each registry:
- **Row name set** — `X(name1, ...) X(name2, ...) ...` → list of names
- **Consumer sites** — `rg "FOREACH_<NAME>\("` to find every invocation site
- **AUTOPOPULATE / X_GEN sister macros** — sister patterns that walk this registry
- **Documented purpose** — header comment summary
- **Approximate concern surface** — cfg / stamp / model-state / drift / display / etc.

### Phase 3 — Cross-compare for overlap

Detect overlap by:
- **Row name set intersection** — Jaccard similarity over field names. >50% = high overlap; 30-50% = medium; <30% = low.
- **Consumer macro overlap** — sites that walk multiple registries together (often a signal that the registries are doing the same job)
- **Purpose semantic overlap** — heuristic match against header comment phrases ("cfg-derived", "stamp", "drift", "wire-format", "inference_cfg", "model-const", etc.)

### Phase 4 — Per overlap candidate, structural-fix question

For each detected overlap pair/cluster, answer:

| Question | If YES | If NO |
|---|---|---|
| Same conceptual surface; different consumer behavior? | **CRITICAL — unify under single registry + multi-consumer macros (Path γ shape)** | Continue questions |
| Distinct concerns coincidentally sharing some field names? | **LOW — leave alone (false positive)** | Continue |
| Legacy + new with intended migration? | **HIGH — flag for migration completion** | Continue |
| Sister pattern shape with no overlap but recurring anti-pattern? | **MED — codify shared pattern in DESIGN_SPECS** | Mark unknown |

### Phase 5 — Rank findings + structural fix proposal

For each finding:
- **Severity** (CRITICAL / HIGH / MED / LOW) per Phase 4 outcome
- **Registry pair** + overlap analysis (row set Jaccard + shared consumers + semantic overlap)
- **Structural fix proposal** — which registry stays canonical; which folds; what consumer macros emerge
- **Cross-ref** to `RECURRING_BUG_PATTERNS.md` Class 14/18/19/21/27 as appropriate
- **Cross-ref** to `DESIGN_SPECS/canonical-sister-extension-discipline.md` (NEW Stage 2 DRAFT; lands alongside this skill)
- **Effort estimate** per fix (LOC delta + consumer migration count)
- **Risk classification** (LOW / MED / HIGH wide-blast-radius)

Plus secondary patterns to flag:
- **Class 14 instances** — manual cfg fields outside canonical FOREACH_*_CFG_FIELD registries
- **Class 19 instances** — hardcoded enum name strings in gating expressions
- **Class 27 instances** — scalar cfg-mirror caches (CI already enforces; flag NEW occurrences pre-CI)

## Output format

Structured findings report (saved to `plan_checks/anti-spaghetti-<date>-<ship>.md`):

```markdown
# /anti-spaghetti report — <date> — <ship/sprint>

## Phase 1 summary
Registries enumerated: <N>
Sites: <file:line list>

## CRITICAL findings (N)

### CRIT-1 — <Registry A> + <Registry B> — parallel infrastructure
Overlap: <X% row name overlap> + <Y shared consumers>
Path γ shape: <describe duplication>
Structural fix: <which folds; consumer macros emerge>
Cross-ref: Class 18, Class 21, `canonical-sister-extension-discipline.md`
Effort: ~<H>h focused; <LOC delta>
Risk: <LOW/MED/HIGH>

### CRIT-2 — ...

## HIGH findings (N)
...

## MED findings (N)
...

## LOW findings (count summary; don't enumerate)

## Top-line verdict
<GREEN: no spaghetti detected> / <YELLOW: notable parallel infrastructure> / <RED: substantial consolidation warranted>

## Recommendations
- Folds that belong at next ship (<=N hours bound)
- Folds that warrant dedicated cleanup ship
- Patterns to codify in DESIGN_SPECS
```

## Composes with

- **`/precoding-audit-gate`** — extends Layer 1 with `/anti-spaghetti` as D6 dimension for plans proposing new framework infrastructure
- **`/readiness`** — Check 29 (new): "If plan proposes new registry, does it cite canonical sister inspection?"
- **`/dod-audit`** — `/anti-spaghetti` operates BELOW the DESIGN_SPECS catalog (registry-level); `/dod-audit` operates AT the catalog
- **`/bug-check`** — `/anti-spaghetti` SURFACES structural duplications that produce Class 18/21 instances; `/bug-check` finds the instances themselves
- **`/merge-scan`** — `/anti-spaghetti` and `/merge-scan` are sister skills; merge-scan finds code-level reuse opportunities; anti-spaghetti finds architecture-level duplications

## Doesn't do (NOT scope)

- Edit code (output is findings report, NOT actual edits)
- Auto-merge registries (operator decides per cycle)
- Decide which fix to apply (operator triages findings)
- Verify shipped code (use `/parity-check` + `/trace-deps` for that)

## DESIGN_SPECS dynamic loads

- `canonical-sister-extension-discipline.md` (NEW Stage 2 DRAFT; lands with this skill) — defines the discipline
- `sidecar-override-pattern-for-registry-auto-flows.md` — sidecar canonical shape
- `meta-registry-pattern-for-codebase-registry-discipline.md` — H15 + H19; registry topology
- `pattern-codification-lifecycle.md` — when a recurring anti-pattern gets codified
- `RECURRING_BUG_PATTERNS.md` Class 14/18/19/21/27 — bug class catalog

## Pattern lifecycle (per `pattern-codification-lifecycle.md`)

- **Stage 1 (problem identification):** retroactive — `.A` Path γ correction + `.B` Path γ #2 critique both surfaced same shape; codified as discipline at `.B` planning 2026-05-17
- **Stage 2 (skill spec draft):** THIS DOC (2026-05-17)
- **Stage 3 (first canonical run):** `.B` audit Batch 2 `/merge-scan` codebase-wide invocation (this batch's findings retroactively validate the methodology)
- **Stage 4 (CLAUDE.md item promotion):** when 3+ anti-spaghetti fold operations land structurally OR when the discipline becomes load-bearing for sprint planning

## Cross-references

- Established at: v5.15.5.F.4d.1.B planning 2026-05-17 (Caramel pushback "is this codebase becoming spaghetti?")
- Sister rules: `feedback_audit_canonical_sister_before_new_infra.md` (memory; NEW), `feedback_plans_cite_sister_registry_inspection.md` (memory; NEW), `project_anti_spaghetti_audit_cadence.md` (memory; NEW)
- Sister DESIGN_SPEC: `canonical-sister-extension-discipline.md` (NEW Stage 2 DRAFT)
- CLAUDE.md item 31 (framework-driven extensibility meta-principle)
- CLAUDE.md item 19 (structural fix preferred when bug class can recur)
- Closes meta-class "parallel infrastructure added when canonical sister exists" structurally via periodic audit + pre-coding gate dimension

---

**End of skill spec v1.0 DRAFT.** First canonical run feedback will iterate to v1.1.
