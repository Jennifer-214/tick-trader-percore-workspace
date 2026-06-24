---
description: Data-oriented-design audit. Walks DESIGN_SPECS pattern catalog dynamically and scans current code OR a plan file for missed pattern applications (cache alignment, branchless dispatch, bit-packing, bitmap dispatchers, X-macro registries, BITMAP_* API reuse, false sharing). Cross-references each finding to the relevant DESIGN_SPECS doc. Distinct from /hft-audit (generic HFT principles) — this skill knows OUR specific pattern library and flags missed applications. Output is a structured findings report, NOT actual edits — operator reviews + decides which to triage.
type: skill
concern: shape-audit
audit_cadence: ad-hoc
tags: [data-oriented-design, framework-discipline, pattern-codification, structural-fix, branchless-discipline]
surface: [hot-path, slow-path, registry, bitmap-packed, wire-format]
sister_skills: [/hft-audit, /merge-scan, /bug-check, /readiness, /registry-fit-audit, /accounting-audit, /precoding-audit-gate]
loads_dynamically: [DOCS/DESIGN_PHILOSOPHY.md, DESIGN_SPECS/README.md, DESIGN_SPECS/meta-disciplines/skill-knowledge-consultation-and-auto-routing.md]
skill_kind: judgment
associated_anti_patterns: [DOCS/RECURRING_BUG_PATTERNS.md, DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md]
associated_decisions: [plans/<active-sprint>/decision-logs/]
associated_postmortems: [plans/<active-sprint>/postmortems/]
associated_ledgers: [DOCS/TECH_DEBT.md, DOCS/PARITY_ISSUES.md]
trigger_heuristics: ["DOD pattern application / missed cache-align/branchless/bit-pack -> suggest /dod-audit"]
---

# /dod-audit — Data-oriented-design pattern audit

> **Uniform parameter + preload contract:**
>
> **Optional invocation args** (mirrors /precoding-audit-gate signature):
> - `<scope_path>` — file path (plan or code file) to scope the scan; default = full codebase sweep
> - `[focus_keywords...]` — narrow scan focus (e.g., "cache layout" "bit-pack")
>
> **Stage 0 — consult institutional knowledge** (per `skill-knowledge-consultation-and-auto-routing.md`): before judging, load this skill's `associated_*` slice (specs / anti-patterns / decisions / postmortems / ledgers) + run the canonical-sister check; if running as a cold Explore/Plan subagent, ensure CLAUDE.md/MEMORY are loaded first. Then the DESIGN_PHILOSOPHY preload:
>
> **DESIGN_PHILOSOPHY preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 3 (Hard Invariants) — H6, H7, H10-H13 are pattern-applied
> - § 4 (Latency cost framework) — cycles vs cache vs branch costs
> - § 7 (Structural-fix family) — X-macro registries, AUTOPOPULATE, tt:: dispatch, 3-barrier design
>
> Cite specific § N rows in finding descriptions to give operator the WHY context.

## What this does

Reads `tick-trader-percore-workspace/DESIGN_SPECS/*.md` (the canonical
library of architectural patterns established by past sprints), extracts
each pattern's signature, and scans either current code OR a plan file
for **missed pattern applications** — surfaces where the code/plan does
something the long way when an established pattern would handle it
cleanly.

Reports per-pattern:

- **CLEAN** — no missed applications found in audited surface
- **APPLIED-N** — N existing applications already follow the pattern
  (sanity check; no triage needed)
- **MISSED-N** — N candidate sites that would benefit from the pattern
  (operator triage candidates)
- **DEFERRED-N** — N sites are documented `// FUTURE OPPORTUNITY:` or
  flagged in TECH_DEBT.md as deliberate-deferral

**Does NOT modify code.** Output is a structured report saved to
`plans/plan_checks/dod-audit-<YYYY-MM-DD>-<surface>.md` + printed to
stdout. Findings are severity-classified; operator decides which to
fold into the current ship vs defer.

**Register spills — the register-level rung of the cache/working-set discipline (added `.E.1.1` 2026-06-24).** The same gradient the DOD patterns optimize — register > L1 > spill-to-stack — has a register-level rung: a hot fn whose simultaneously-live values exceed the ~16 GP registers SPILLS to the stack (an extra `mov %reg,-N(%rbp)` store + a later reload + a longer dependency chain + variance). DOD LAYOUT choices drive it — holding several 16B `Money`/`FPN_Binary<64>` values live at once (TWO GP regs EACH), wide hot structs, over-unrolling. When auditing a hot/slow-path layout, flag register-pressure risk as a SIBLING of false-sharing, and ROUTE verification to `tools/check_latency_path_conformance.py` (it reports `spills=N` — **ADVISORY**, not strict-teeth'd: a frame-relative store isn't always a spill, so a non-zero count is an inspect-the-`-S` signal, not an auto-fail). Concept + mitigation: `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` § Register spills.

## Why DESIGN_SPECS-driven

The skill never hardcodes the pattern list. It parses
`DESIGN_SPECS/*.md` dynamically and dispatches based on what's there.
Future patterns added to the library (e.g., a new
`DESIGN_SPECS/lock-free-queue-pattern.md`) are auto-included in the
next run — no skill spec edit needed.

Same structural-fix-preferred shape as /bug-check parsing
RECURRING_BUG_PATTERNS.md or FOREACH_FEATURE registry-as-source-of-truth.

## Distinct from sister skills

| Skill | Scope | Relationship to /dod-audit |
|---|---|---|
| /hft-audit | Generic HFT principles (cache alignment, branchless, lock-free) — universal, project-agnostic | Overlapping concerns at general level; /hft-audit catches generic violations, /dod-audit catches missed pattern applications using OUR specific library (DESIGN_SPECS) |
| /merge-scan | Computation reuse opportunities (atomic loads, clock_gettime, cfg accesses, state fields) | Orthogonal — /merge-scan = computation sharing; /dod-audit = pattern application |
| /foxlib-promotion | Generic primitives extraction to public lib | Sister direction — /foxlib-promotion = EXTRACTION (project → lib); /dod-audit = APPLICATION (lib → code) |
| /bug-check | Codebase scan for OUR-codebase-specific recurring bug patterns | Same shape (registry-driven, output-only), different domain — /bug-check = bug class history; /dod-audit = pattern library application |
| /readiness | Plan completeness verification | /readiness Check 27 invokes /dod-audit on plan files; compose-by-reference per SKILLS_HIERARCHY.md |
| /trace-deps | Dependency-chain plan-time audit | Orthogonal — /trace-deps = does plan claim X exists; /dod-audit = does plan apply available patterns |
| /parity-check | Train↔serve identity | Orthogonal — different audit dimension |
| /latency-track | Latency-critical addition tracking | Sister — /latency-track = "you added this; document the cost"; /dod-audit = "you should apply this pattern; the cost would be lower" |
| /patch-planner | Generates fix blueprints from findings | Downstream — /dod-audit FINDS, /patch-planner BLUEPRINTS |
| /accounting-audit | Class 27 cfg-mirror caches + accounting / money tracking surface | **Composes** — /dod-audit findings touching accounting paths defer the Class 27 + accounting-specific verdicts here |
| /registry-fit-audit | Registry-fit per framework-selection criteria (registry vs principle+sweep) | **Composes** — when /dod-audit finding suggests "this registry shape is wrong" OR "should this be a registry at all?", defer verdict to /registry-fit-audit. /dod-audit identifies pattern application gaps; /registry-fit-audit decides whether the proposed pattern (registry) is the right shape. |

## When to use

- **Plan-mode (highest-value invocation)** — before coding starts,
  audit the plan against pattern library. Catches design gaps when
  the cost of fixing is changing one paragraph in a plan, not
  rewriting code post-implementation. Same shape as v5.14.8's audit-
  driven pre-coding gate.
- **Codebase sweep (post-coding sanity check)** — after a ship lands,
  verify the new code applied patterns where applicable; surface any
  missed sites for follow-up.
- **Subsystem focus** — when reviewing a specific subsystem (e.g.,
  "audit OMS for bit-packing opportunities"), focused scope.
- **Pre-paper-test gate** — fold into pre-deployment checklist
  alongside /bug-check.

## When to skip

- Single-file bug fix (no architectural surface change)
- Doc-only changes
- Recently run (within 24h) and codebase hasn't materially changed
- During paper-testing phase (run BEFORE start, not during)

## Scope (per audit-scope-taxonomy.md)

This skill accepts scope as first positional arg per `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md`:

- `current` (default when no scope specified) — pattern-application audit of recent edits + touched files
- `wide` — full codebase sweep across all DESIGN_SPECS patterns; HIGH context cost
- `scoped <glob>` — file/dir glob (e.g., `/dod-audit scoped CoreFrameworks/OrderManager*`)
- `module:<name>` — named module per `MODULE_MAP.md` registry (e.g., `OMS`, `ML-pipeline`, `accounting`); recommended for iterative module-by-module pattern application audits
- `plan <plan-path>` — plan-mode (existing); audit a plan file's proposed code against pattern library
- `pattern <pattern-name>` — focused single-pattern scan (existing)

**Most appropriate scope shapes for /dod-audit:** `current` (during active work), `module:<name>` (iterative deep pattern audits), `plan <plan-path>` (pre-coding plan verification), `wide` (post-new-pattern-codification sweeps).

## Invocation

- `/dod-audit` — default scope `current`; pattern-application audit of recent edits
- `/dod-audit <scope>` — explicit scope per taxonomy
- `/dod-audit plan <plan-path>` — plan-mode (legacy invocation; remains supported)
- `/dod-audit pattern <pattern-name>` — focused single-pattern scan (legacy invocation; remains supported)

**Examples:**
- `/dod-audit current` — fast feedback during active coding
- `/dod-audit module:OMS` — deep pattern-application audit of OMS module
- `/dod-audit wide` — quarterly full sweep across DESIGN_SPECS catalog
- `/dod-audit plan plans/<sprint-dir>/subplans/<plan>.md` — pre-coding plan check
- `/dod-audit pattern decision-time-data-binding-pattern` — focused single-pattern scan

## Execution model (per SKILLS_HIERARCHY.md)

**ONE-WAY HIERARCHY. NO LAYER 3.**

```
LAYER 1: ORCHESTRATION
  - Main Claude session OR another orchestrator skill (e.g., /readiness
    Check 27 referencing /dod-audit by-reference)
  - Decides WHEN to invoke this skill
  - Spawns ONE Explore subagent

LAYER 2: EXECUTION (this skill runs HERE)
  - The spawned Explore subagent reads this spec + DESIGN_SPECS/*.md
    and applies the audit using its OWN read/grep/bash tools
  - DOES NOT spawn further subagents
  - Returns a single combined report
```

**If you are reading this spec inside an Explore subagent:** YOU ARE
the auditor. Read the DESIGN_SPECS catalog + apply the audit using
your read/grep/bash tools. Do NOT spawn nested subagents.

**Composition:** /readiness Check 27 invokes /dod-audit by reading
this spec + applying the audit inline as a sub-section of /readiness's
report. By-reference composition, not by-spawning. See
`DOCS/SKILLS_HIERARCHY.md`.

## Pass structure

Spawn an Explore subagent. The subagent:

### Step 1 — DESIGN_SPECS catalog ingest

Read every `*.md` file in
`tick-trader-percore-workspace/DESIGN_SPECS/` (skipping `README.md`).
For each pattern doc, extract:

- **Pattern name** (filename stem; kebab-case)
- **Status** (frontmatter or "## Status" section: ACTIVE / DEPRECATED /
  SUPERSEDED-BY-X)
- **Apply-when symptoms** (from "## Trade-offs + when to apply" section)
- **Skip-when symptoms** (same section)
- **Reference implementations** (file:line citations for first
  application + subsequent uses)
- **Detection signatures** — any explicit "## Audit detection" section
  (NEW convention — DESIGN_SPECS docs may add this section to give
  the audit skill grep patterns or AST shapes to scan for; if absent,
  fall back to symptom-based heuristics below)

If a pattern doc is missing required sections (no "## Trade-offs",
no apply-when), emit **doc-debt finding** at top of report (not
ship-blocking; flagged for DESIGN_SPECS maintainer).

### Step 2 — Surface enumeration

Determine what to audit:

- **Full sweep** (no arg): walk all `*.hpp` `*.cpp` files in
  `CoreFrameworks/`, `Strategies/`, `ML_Headers/`, `DataStream/`,
  `MemHeaders/`, `Backtest/`, `GUI/`, `FixedPoint/`. Skip `tests/`
  (different audit shape; tests audit themselves).
- **Subsystem path** (`<path>` arg): walk that file or directory.
- **Plan-mode** (`plan <plan>` arg): parse the plan file's proposed
  code snippets + named functions/structs + claimed cfg fields. Audit
  against patterns BEFORE the code is written.
- **Pattern-focused** (`pattern <name>` arg): scope to a single
  DESIGN_SPECS pattern; broader codebase sweep limited to that
  pattern's heuristics.

### Step 3 — Pattern checks (per surface)

For each pattern in the catalog, scan the surface for
missed-application candidates. The 10 baseline check categories:

#### 3a. Cache alignment

Detection signatures:
- `struct .* {` blocks WITHOUT `alignas()` decorator on perf-critical
  surfaces (CoreFrameworks/, ExecutionCore, hot path)
- Cross-thread struct members without cache-line span analysis (false
  sharing risk)
- Hot/cold field placement: cold fields placed in middle of hot
  cluster (forces cache-line load for cold data on hot access)

Cross-ref: `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md` (cache-line awareness
section), CLAUDE.md item 4 (per-core data plane), TECH_DEBT-011
(PerCoreSnap layout sensitivity).

False-positive filter: skip cold-path structs (boot init, debug
panels) — they don't need cache-line care.

#### 3b. Cache miss / false sharing

Detection signatures:
- Multiple cores writing to adjacent fields in the same cache line
  (SoA layout violations)
- Frequently-accessed fields fragmented across N cache lines instead
  of clustered

Cross-ref: CLAUDE.md item 4 (per-core SoA discipline).

False-positive filter: ≥2 colocated cross-thread writes required.
Single-thread struct fragmentation is style, not bug.

#### 3c. Concurrency invariants

Detection signatures:
- Cross-thread shared state without `_Atomic` / `std::atomic` /
  seqlock pattern
- Release/acquire semantics missing on cross-thread data publishes
- New shared state added without checking single-writer rule
  (DOCS/CLAUDE_INVARIANTS.md)

Cross-ref: CLAUDE.md OMS submit funneling (item 5),
DOCS/CLAUDE_INVARIANTS.md threading rules.

False-positive filter: same-thread reads + writes don't need
atomics. Boot-only state doesn't need atomics.

#### 3d. Branchless candidates

Detection signatures:
- Hot-path `if` branches on data-dependent predicates (mispredict
  risk; branchless mask compute would dominate)
- Slow-path `if` chains where compiler can't cmov (not a bug; potential
  optimization)
- Multiple sequential `if` checks on the same predicate (suggests
  cached predicate at top of function, item 18(c))

Cross-ref: CLAUDE.md item 18 (slow-path latency reduction priority,
sub-clauses a/b/c/d).

False-positive filter: don't flag every if-statement. Only:
- Hot path single-site branches with cmov-friendly shape, OR
- Slow path `if` chains gated by cfg flag NOT cached at slow-path
  entry (item 18(c) violation), OR
- 3+ sequential branches on same predicate

#### 3e. Bit-packing candidates

Detection signatures:
- ≥3 colocated `uint8_t` boolean fields in a struct (bit-pack to
  uint16_t/uint32_t/uint64_t bitmap)
- ≥2 colocated cross-thread `uint8_t` boolean fields (bit-pack PLUS
  atomic mask updates via `__atomic_fetch_or`)
- Existing bool flag fields where BITMAP_* API would be cleaner

Cross-ref: `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md` (base API + variants),
`DESIGN_SPECS/data-disciplines/partner-core-bitmap-pattern.md` (per-core 1-bit-per-core variant),
`DESIGN_SPECS/refactor-patterns/transient-aggregation-bitmap-pattern.md` (function-local summary variant),
`DESIGN_SPECS/framework-patterns/per-bit-per-core-override-pattern.md` (per-bit per-core override variant),
`DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md` (decision algorithm before migrating),
CLAUDE.md item 1 (Portfolio uint16_t bitmap), CLAUDE.md item 20 (BITMAP_* API),
TECH_DEBT-013 (BIT_FLAG candidate inventory).

**Class 26 sub-shape distinction at per-core surface (NEW v5.15.5.F.4d.1.B.8 amendment):** when /dod-audit findings touch per-core cfg surface, distinguish Class 26 sub-shapes per `DOCS/recurring-bug-patterns/class-26-global-consumer-reading-per-core-field.md § Sub-shapes`:
- **Sub-shape A (WRONG-INDEX paired-access)** — `cfg.core_overrides[X]` + `cfg.cores[Y]` paired access with X != Y; CI Check 9 catches mechanically per `tools/check_per_node_registry_integrity.py`
- **Sub-shape B (UNINDEXED-GLOBAL at per-core consumer site)** — `cfg.X` / `cfg->X` / `resolved_cfg.X` UNINDEXED on per-core-with-global-sister fields (fee_rate / fee_rate_taker / fee_rate_maker / slippage_pct); CI Check 10 catches mechanically (sister to Check 9; M7 6th canonical)

Per /dod-audit findings citing per-core surface, cite Check 9 / Check 10 respectively for mechanical detection coverage. Sister-skill alignment with /accounting-audit category 2 (which has the same Class 26 sub-shape A/B distinction noted at v5.15.5.F.4d.1.B.8 Phase H.2.b). `/bug-check` auto-handled via RECURRING_BUG_PATTERNS dynamic read (no skill amendment needed; verified by /blindspot-scan v1.1 H-RECURSIVE-1 sister-skill cohort enumeration). `/ml-audit` + `/registry-fit-audit` + `/hft-audit` not in sister cohort (no Class 26 references per same enumeration).

False-positive filter: ≥3 colocated bools required. Single bool flag
is fine. Per-record vs cross-record awareness — DON'T flag per-Order
bit-packing across all orders (item 20 trade-off section). Run
cfg-flag-eligibility-criteria's 5-criteria before flagging cfg booleans
(lat_enabled-class false positives caught here).

#### 3f. Bit-field dispatchers

Detection signatures:
- Switch-on-enum dispatch with ≥3 cases that all share signature
  (function-pointer table candidate)
- X-macro candidate: ≥3 parallel struct field additions or N-site
  manual update following same shape (CLAUDE.md item 13)
- AUTOPOPULATE companion candidate: X-macro registry with ≥2
  production-caller construction sites (item 21)
- PRE/POST split candidate: registry with canonical wire-format that
  must interleave with sister registry (item 22)

Cross-ref: `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md`,
`DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md`,
`DESIGN_SPECS/framework-patterns/autopopulate-from-arity-macro-family.md` (variant for scattered locals),
`DESIGN_SPECS/wire-format-patterns/pre-post-cfg-registry-split-for-emit-order-preservation.md`,
`DESIGN_SPECS/framework-patterns/registry-tuple-as-single-source-of-truth.md` (5-col tuple — registry feeds N consumers),
`DESIGN_SPECS/framework-patterns/curve-registry-pattern.md` (named compute fns chosen by enum — fn-pointer dispatch),
`DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md` (SCOPE COLUMN vs DOMAIN SPLIT decision),
`DESIGN_SPECS/framework-patterns/slow-path-gate-registry-pattern.md` (slow-path gate registry canonical example),
CLAUDE.md items 13, 21, 22.

False-positive filter: ≥3 sites required for X-macro candidate. ≥2
production-caller construction sites required for AUTOPOPULATE. Don't
flag single-site switches. For switch-on-enum dispatching to similarly-
named free functions (linear_X / exp_X / step_X), check curve-registry-
pattern.md before flagging — already-applied is CLEAN; missing is MISSED.

#### 3g. Wire-format byte preservation discipline

Detection signatures:
- Plan/code modifies stamp body, snapshot, or other HMAC-protected /
  version-locked wire format WITHOUT explicit byte-preservation note
- Field rename/delete in registries that emit canonical bodies

Cross-ref: `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md`,
CLAUDE.md item 15 (parity-tested-by-construction).

False-positive filter: only fires for stamp body, snapshot, model
binary format, run history JSONL.

#### 3h. Structural fix preferred (decision framework)

Detection signatures:
- Plan/code patches a single instance of a recurring bug class without
  considering structural extinction (X-macro registry, helper
  extraction, AUTOPOPULATE companion)
- Multiple sites being patched independently when a unified helper +
  registry would close the class

Cross-ref: `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md`,
CLAUDE.md item 19, RECURRING_BUG_PATTERNS Class 18.

False-positive filter: true one-off bugs (pattern won't recur) get
direct patch. Only fires when bug class history shows ≥2 recurrences
OR plan explicitly identifies "we'll need to patch this again."

#### 3i. Math kernel constant-iter + branchless (CLAUDE.md H11)

Detection signatures:
- Math kernel inner reduction loop with VARIABLE upper bound that
  varies per outer iteration (e.g., `for k=0..j-1` where j is an
  outer-loop counter). Should be `for k=0..MAX_*` per the constant-iter
  invariant.
- `if` statement INSIDE a reduction loop body (no early-exit or
  short-circuit; just edge-case skip). Branchless via algorithmic
  zero-invariant (pre-zero state arrays).
- `#if defined(__AVX512F__)` block with `if (...)` guards inside the
  vectorized setup (same problem as scalar; mask handles edge case).
- Cholesky-like algorithm without pre-zero pattern at appropriate
  granularity (per-row, per-solve, per-cycle).

Cross-ref: `DESIGN_SPECS/refactor-patterns/branchless-math-kernel-pattern.md`,
CLAUDE.md item 26 (math kernels constant-iter + branchless),
CLAUDE.md item 18 (slow-path latency reduction sub-clauses).

**MECHANIZED (`.E.1.0`):** `tools/check_latency_path_conformance.py` is the static enforcer for the H11 (loop-structure/complexity), H7/H20 (branch-classification), and H4 (no-float) lenses on the hot/slow paths — the **2nd derived-fact-budget gate** (sister to `check_struct_size_budget.py`; both: manifest → compile-a-probe → measure → gate ≤ budget → `--selftest` teeth). RUN it for the branchless + constant-iter + derived-fact-budget lenses; its **data-dependent-warm** branch count is the H20-reduction meter (→ 0; the curation + reduction = the optimization leaf, D-234/D-235/D-236).

False-positive filter: outer loops with per-call-stable bounds
(`for i=0..n_models`) are ACCEPTABLE — branch predictor handles them
cleanly. Only flag INNER reductions with bounds that vary across
outer-loop iterations within a single call.

#### 3j. Struct byte-equivalence padding (CLAUDE.md H12)

Detection signatures:
- Struct with implicit padding (sizeof(T) > sum_of_member_sizes(T))
  AND used in `memcmp` / `sha256_bytes` / `hmac_*` / wire-format
  contexts. Implicit padding bytes are UB.
- Struct has mixed-alignment members (e.g., `uint64_t` followed by
  `int32_t`) creating padding gap; needs explicit `_padding = 0` field.
- Struct returned by value through a function AND consumer compares
  via `memcmp` (latent regression risk under stack-layout shifts).

Cross-ref: `DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md`,
CLAUDE.md item 27 (structs in byte-equivalence contexts have explicit
zero-init padding), CLAUDE.md item 12 (display↔execution invariant
relies on snapshot byte determinism), CLAUDE.md item 15 (parity-tested-
by-construction).

False-positive filter: structs NOT used in byte-equivalence contexts
(internal types only; never compared bytewise) don't need explicit
padding. Verify usage via grep before flagging.

### Step 4 — DESIGN_SPECS cross-reference

For each finding, link to the relevant DESIGN_SPECS doc + cite the
canonical-shape section. Format:

```
PATTERN: bitmap-flag-api
  - Apply-when symptom matched: 4 colocated uint8_t bools in PerCoreSnap
  - DESIGN_SPECS reference: bitmap-flag-api.md "## The pattern (concrete shape)"
  - First applied: MemHeaders/FailureModeRegistry.hpp v5.14.8.B
  - Suggested fix: replace bools with uint16_t state_flags + MASK_*
  - Effort estimate: ~1-2h
```

### Step 5 — TECH_DEBT auto-write

For each finding the operator marks DEFER (or that the audit suggests
deferring with rationale), auto-append entry to
`DOCS/TECH_DEBT.md` per CLAUDE.local.md auto-write contract. Same
discipline as /parity-check + PARITY_ISSUES.md.

Entry shape:
```markdown
### TECH_DEBT-NNN — <one-line title from finding>

- **Created:** <date> by /dod-audit run on <surface>
- **Severity:** <CRITICAL/HIGH/MEDIUM/LOW from finding>
- **Surface:** <file path / subsystem>
- **What's deferred:** <description from finding>
- **Why deferred:** <rationale from operator review>
- **Cost estimate:** <from finding>
- **Trigger:** <what event should re-prompt fixing>
- **Status:** OPEN
- **Cross-ref:** DESIGN_SPECS/<pattern>.md, /dod-audit run report
```

DO NOT auto-write findings the operator marks ADDRESS-NOW (those land
in current ship's plan). DO NOT auto-write CLEAN/APPLIED findings.

### Step 6 — Output

Save report to `plans/plan_checks/dod-audit-<YYYY-MM-DD>-<surface>.md`
+ print to stdout.

Convention: `<surface>` is:
- `codebase` for full sweep
- the basename of the audited path (e.g., `OrderManager`) for
  subsystem scope
- the plan's stem (e.g., `<sprint>-<topic>` from the plan filename) for
  plan-mode

Output format:

```markdown
# /dod-audit report — <surface> — <date>

## Catalog ingested
- N patterns from DESIGN_SPECS/
- Patterns detected (active): <list>
- Doc-debt findings: <list, if any>

## Summary

| Pattern | CLEAN | APPLIED | MISSED | DEFERRED |
|---|---|---|---|---|
| bitmap-flag-api | — | 4 | 2 | 0 |
| x-macro-registry-with-presence-dispatch | — | 12 | 0 | 1 |
| autopopulate-pattern-for-production-caller-class | ✅ | 5 | 0 | 0 |
| ... |

## Findings (severity-ordered)

### CRITICAL — <title>
- **Surface:** <file:line>
- **Pattern:** <DESIGN_SPECS doc reference>
- **Symptom:** <what's wrong>
- **Suggested fix:** <concrete proposal>
- **Effort estimate:** <hours>
- **Cross-references:** <related findings, TECH_DEBT entries>

### HIGH — <title>
...

### MEDIUM — <title>
...

### LOW — <title>
...

## Recommendations

### Address now (ship-blocking or strong recurring class)
- ...

### Address during current ship (folded into open plan)
- ...

### Defer with TECH_DEBT entry
- ... (auto-written entries listed)

### CLEAN — no action
- ... (sanity check; pattern correctly applied)

## Verdict: GREEN / YELLOW / RED

GREEN — no critical findings; ship as planned
YELLOW — one or more HIGH findings; address before ship close
RED — CRITICAL findings; revisit plan/code before continuing
```

## Severity calibration

- **CRITICAL** — correctness/perf bug (e.g., false sharing on hot path,
  HMAC chain break risk, stale-cache concurrency hazard). Block ship.
- **HIGH** — recurring pattern with clear DESIGN_SPECS solution that
  the surface explicitly violates. Address before ship close.
- **MEDIUM** — DOD principle violation; pattern would clean up the code
  but no immediate harm. Worth addressing in current ship if effort < 1h.
- **LOW** — readability/clarity opportunity; defer-to-TECH_DEBT
  acceptable.

## Heuristics

### False-positive mitigation

The skill's heuristics use minimum thresholds to avoid noise:

- **Bit-packing**: ≥3 colocated bools, OR ≥2 colocated cross-thread
  bools (false-sharing concern). Single bool is fine.
- **Branchless**: don't flag every `if`. Only hot-path single-site
  branches with cmov-friendly shape, OR slow-path `if` chains gated by
  cfg flag not cached at slow-path entry, OR 3+ sequential branches on
  same predicate.
- **X-macro**: ≥3 sites required. Don't flag single-site switches.
- **AUTOPOPULATE**: ≥2 production-caller construction sites required.
- **Cache alignment**: skip cold-path structs.
- **Concurrency**: skip same-thread reads/writes + boot-only state.

### Plan-mode emphasis

Plan-mode is the highest-value invocation. v5.14.8 had 6 design pivots
that would have been caught earlier with this audit. Plan-mode catches
patterns when the cost of "applying" is one paragraph in a plan, not
rewriting code post-implementation.

### DESIGN_SPECS auto-detection of new patterns

The skill walks `DESIGN_SPECS/*.md` at runtime. Future ships adding new
patterns (e.g., `lock-free-queue-pattern.md` or
`perf-counter-aggregation-pattern.md`) auto-include in the next run.
Same shape as /bug-check parsing RECURRING_BUG_PATTERNS.md.

If a new DESIGN_SPECS doc lacks an "## Audit detection" section, the
skill falls back to symptom-based heuristics from "## Trade-offs +
when to apply" + "## Reference implementations". DESIGN_SPECS authors
SHOULD add explicit detection sections for skill efficiency.

### Output format reuse

Same structure as /readiness, /trace-deps, /merge-scan, /bug-check —
report at `plans/plan_checks/dod-audit-<YYYY-MM-DD>-<surface>.md`.
Operator already knows the format; reduces cognitive overhead.

### Periodic vs on-demand

Ship as on-demand (operator-invoked) initially. Revisit as
nightly /loop or pre-ship gate after we've used it a few cycles to
gauge noise level. Default: operator triggers; not auto-scheduled.

## Cross-references

- `DESIGN_SPECS/README.md` — catalog purpose, pattern doc structure
- `DOCS/SKILLS_HIERARCHY.md` — execution model (Layer 1 / Layer 2)
- `DOCS/RECURRING_BUG_PATTERNS.md` — bug class catalog (sister
  registry; /bug-check is the corresponding execution skill)
- `DOCS/TECH_DEBT.md` — deferral ledger; /dod-audit auto-writes
  per the auto-write contract
- `CLAUDE.md` items 13, 16, 18, 19, 20, 21, 22, 23 — pattern doctrine
- `CLAUDE.local.md` — going-forward rules + auto-write contract
- `.claude/skills/readiness/SKILL.md` Check 27 — invokes /dod-audit
  by-reference for plan-mode pre-coding gate
- `.claude/skills/bug-check/SKILL.md` — sister registry-driven skill
- `.claude/skills/foxlib-promotion/SKILL.md` — sister direction
  (extraction)
- `.claude/skills/hft-audit/SKILL.md` — generic HFT principles audit;
  overlaps on cache/branchless/concurrency at general level

## What this skill is NOT

- Not a code formatter (`/dust` does that)
- Not a unit-test runner (assumes existing tests pass)
- Not a security scanner (`/security-review` does that)
- Not a benchmark (`/latency-track` covers latency-additions)
- Not predictive ("will applying this pattern improve metric X?") —
  purely structural; pattern application is a separate decision

## Future variants

- `/dod-audit diff <commitA>..<commitB>` — re-audit when codebase
  drifts mid-plan (catches "I planned for v5.X.x, but pattern Y was
  added since")
- `/dod-audit all-active` — full sweep across all subsystems
  (current behavior of no-arg invocation; alias for clarity)
- `/dod-audit catalog` — print the ingested DESIGN_SPECS catalog
  without running detection (debugging tool)
- Pattern-doc reuse across projects: future consideration. The skill
  is workspace-specific today; templating to read DESIGN_SPECS from
  any workspace would make it FoxLIB-eligible for cross-project use.

## Versioning

Skill v0.1 (initial) — registry-driven baseline. Future v0.2+ may
add specific check categories as DESIGN_SPECS catalog grows.
