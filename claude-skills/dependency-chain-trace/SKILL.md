---
name: dependency-chain-trace
description: Trace a specific symbol or data path through every site that touches it across the codebase. NOT a point-scan — a flow trace. Outputs a graph of read/write sites, lifecycle classification (thread + cadence + type), cohort siblings, and blast-radius assessment. Use for pre-coding scope understanding, post-coding migration verification, cohort discovery, debugging, and class-27/class-28 close verification. Skill is `chain:<symbol>` shape per audit-scope-taxonomy.md.
---

# /dependency-chain-trace — Symbol / data-path flow audit

> **Stage 0 preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 3 (Hard Invariants) — H1-H18 may apply to symbols traced (cfg fields, OMS state, snapshot fields)
> - § 6 (Concurrency family) — cross-thread interactions matter for flow trace
>
> **Stage 0 preload** (workspace/DESIGN_SPECS/):
> - `audit-scope-taxonomy.md` § "chain <symbol>" — the shape this skill embodies
> - `cfg-scope-discipline.md` — relevant when tracing cfg fields
> - `decision-time-data-binding-pattern.md` — relevant when tracing pre-resolved values
> - `branchless-dispatch-discipline.md` — relevant when tracing dispatch-table inputs

## What this does

Traces a specific SYMBOL (struct field, enum value, function, global variable, named cfg field) through every site in the codebase that touches it. Distinct from point-scan audits (`/hft-audit`, `/dod-audit`, `/bug-check`, etc.) which scan for PATTERNS across the codebase — this skill scans for SITES TOUCHING ONE SYMBOL.

Output is a structured flow report: definition site, all write sites (classified by thread/cadence/type), all read sites (classified the same way), data flow graph (which writes feed which reads), cohort siblings (related symbols), and blast radius assessment.

**Does NOT modify code.** Output is read-only flow analysis.

## When to use

- **Pre-coding scope understanding** — before changing a value's shape/semantics, understand FULL surface that touches it. Avoids Class 18 mirror-incomplete after edits.
- **Post-coding migration verification** — after migrating a value (e.g., cfg field to per-core), verify ALL sites updated. Confirms no stragglers.
- **Cohort discovery** — find all sites that touch a value family (e.g., trace `fee_rate_*` cohort). Informs B.1.b-style cohort sweeps.
- **Debugging** — trace where data was written + where it was read; identify mismatch source.
- **Class 27 / Class 28 close verification** — after structural fix lands, confirm all sites migrated; no stragglers.
- **Plan-mode** — when designing a refactor, trace the value to understand blast radius before scoping.

Distinct from sister skills:

| Skill | Shape | Question answered |
|---|---|---|
| `/hft-audit` | Pattern point-scan | "Where in the codebase do PATTERN-X violations exist?" |
| `/bug-check` | Pattern point-scan (registry-driven) | "Where do known bug classes exist?" |
| `/dod-audit` | Pattern point-scan (DESIGN_SPECS-driven) | "Where are missed pattern applications?" |
| `/dependency-chain-trace` | **Symbol flow trace** | "Where does THIS specific symbol go and get touched?" |

## Scope (per audit-scope-taxonomy.md)

This skill's scope shape is `chain:<symbol>` per audit-scope-taxonomy.md § 5. The symbol arg is REQUIRED:

```
/dependency-chain-trace <symbol>
```

Symbol forms accepted:
- Struct field path: `cfg.cores[c].fee_rate_maker`, `Order::pre_resolved.fee_rate`, `oms->oms_state_flags`
- Enum value: `ORDER_FILLED`, `STRATEGY_ML`, `BANDIT_ALGORITHM_THOMPSON`
- Function: `OrderManager_HandleFill`, `Order_BindPreResolved`
- Global variable: `g_fill_dispatch`, `g_per_core_cfg_render_mask`
- Cfg field name (resolves to registry row + struct field): `fee_rate_maker`, `bandit_algorithm`

The skill resolves the symbol to definition site + all touch sites via grep + AST analysis.

## Invocation

- `/dependency-chain-trace <symbol>` — trace the symbol; default depth (~2 levels of indirect reference)
- `/dependency-chain-trace <symbol> deep` — also follow function-call propagation (where this symbol gets passed as arg → traced into the callee body)
- `/dependency-chain-trace <symbol> cohort` — also discover cohort siblings (symbols typically touched alongside this one)

## Workflow

Spawn an Explore subagent. The subagent:

### 1. Resolve the symbol

Find DEFINITION site:
- Struct field: locate the struct declaration containing the field
- Enum value: locate the enum declaration
- Function: locate the function definition
- Global variable: locate the declaration
- Cfg field name: resolve to FOREACH_*_CFG_FIELD row + struct field via registry lookup

Output: `<symbol> defined at <file>:<line>`. If symbol not found, ERROR with suggestions (typo? scope-qualified name needed?).

### 2. Find all WRITE sites

Greppable patterns:
- Direct assignment: `<symbol> = `, `<symbol>[X] = `, `obj.<symbol> = `, `ptr-><symbol> = `
- Compound assignment: `<symbol> += `, `<symbol> &= `, etc.
- Setter function call: `<Type>_Set<Field>(...)` (for accessor-mediated writes)
- Mutator function call: function names matching `*_Set*` / `*_Push*` / `*_Update*` that take `<symbol>` as out-param
- Initialization: declarations with initializer; constructor calls

For each write site, capture:
- file:line
- enclosing function name
- write expression (full RHS)
- inferred WRITE-CADENCE (boot / cfg-load / per-cycle / per-fill / per-tick / cross-thread-snapshot)
- inferred WRITE-THREAD (producer / drainer / slow-path / hot-path / GUI / boot)

### 3. Find all READ sites

Greppable patterns:
- Direct read: `<symbol>`, `<symbol>[X]`, `obj.<symbol>`, `ptr-><symbol>` (in non-assignment context)
- Comparison: `<symbol> == X`, `<symbol> != X`, `<symbol> < X`, etc.
- Function arg: `func(<symbol>, ...)` or `func(..., <symbol>, ...)`
- Getter function call: `<Type>_Get<Field>(...)` (for accessor-mediated reads)
- Dispatch input: `<symbol>` used as switch/if condition OR table index

For each read site, capture:
- file:line
- enclosing function name
- read expression context
- inferred READ-CADENCE
- inferred READ-THREAD

### 4. Build data flow graph

For each write/read pair, infer which writes feed which reads via:
- Same thread + temporal ordering (write before read in same fn body)
- Cross-thread snapshot publish/consume contracts (e.g., slow-path writes seqlock + hot-path reads it)
- File I/O contracts (cfg load writes; engine reads at boot)

Output: graph nodes (writes + reads) + edges (write → read flow paths).

### 5. Classify by lifecycle + thread

Lifecycle phases:
- `cfg-load` — written at cfg parser / load time; read forever after
- `boot-once` — written at engine boot; immutable thereafter
- `per-cycle` — written every slow-path cycle (~10ms); read at hot-path or next cycle
- `per-fill` — written per drainer fill; read by accounting/event log
- `per-tick` — written per tick (rarely; hot-path discipline avoids state mutation)
- `cross-thread-snapshot` — written by one thread; published to another via seqlock/atomic
- `transient` — short-lived; written + consumed within single call chain

Cross-thread interaction summary:
- Which threads write
- Which threads read
- Publication mechanism (seqlock, atomic, file, queue)
- Race surface (is the publish/consume sequence ordered correctly?)

### 6. Discover cohort siblings (optional; `cohort` arg)

For the traced symbol, find sibling symbols typically touched in the same call paths:
- Same struct, adjacent fields (e.g., `fee_rate_maker` + `fee_rate_taker`)
- Same registry cohort (other rows in the same FOREACH_X registry)
- Touched in the same function bodies as the primary symbol

Output: cohort sibling list with overlap analysis (which functions touch BOTH the primary and the sibling).

### 7. Compute blast radius

If the primary symbol's shape, semantics, or location were to change, what breaks?
- Direct compile-time dependencies (callers of changed function; readers of changed field type)
- Wire-format dependencies (stamp body / drift check / persisted state)
- Test-fixture surface (number of test sites touching the symbol)
- Cross-version compat surface (snapshot/persist compatibility)

Output: severity-classified blast radius assessment.

## Output format

Generate a structured markdown report:

```markdown
# Dependency chain trace: `<symbol>` — <date>

## Definition
- **Site:** `<file>:<line>`
- **Form:** <struct field | enum | fn | global>
- **Type:** <type signature>

## Write sites (N total)

### `<file>:<line>` — `<enclosing_fn>` [<thread> / <cadence>]
- Write: `<expression>`
- Context: <brief description>

(repeat for each write site)

## Read sites (M total)

### `<file>:<line>` — `<enclosing_fn>` [<thread> / <cadence>]
- Read: `<expression context>`
- Used for: <dispatch | comparison | passthrough | computation>

(repeat for each read site)

## Data flow graph

<ASCII or markdown graph showing write→read flows>

## Lifecycle classification

- Primary lifecycle: <cfg-load | boot-once | per-cycle | ...>
- Cross-thread interactions: <list>
- Publication mechanism: <seqlock | atomic | file | queue | none>

## Cohort siblings (if `cohort` arg)

- `<sibling_symbol>` — touched at <K> sites overlapping with primary's touch set
- (repeat per sibling)

## Blast radius assessment

- Direct compile deps: <count> + severity
- Wire-format deps: <yes/no> + which surfaces
- Test fixture surface: <count of test sites>
- Cross-version compat: <impact>

## Recommended caveats for downstream change

- (e.g., "If changing this field's type, also update sibling field X; verify stamp body Layer-5b hash; migrate ~14 test fixtures")
```

## Anti-patterns to flag (DO NOT DO THIS in your own findings)

- Do **not** trace symbols outside the scope of structural concern (e.g., loop counters, throwaway locals). Filter for symbols that DO actually flow through the codebase.
- Do **not** confuse `chain:<symbol>` with `module:<name>` — chain is FLOW trace; module is FILE SET scan.
- Do **not** produce shallow analysis. The point of chain trace is DEPTH — every site classified by thread + cadence + type. If the trace yields a flat list of grep hits without classification, the audit didn't do its job.
- Do **not** suggest fixes (this is read-only flow analysis). The findings inform downstream decisions; OTHER skills (`/patch-planner`, `/dod-audit`) suggest fixes.

## Cross-skill composition

- **Invoked by `/precoding-audit-gate`** when scope includes a `chain:<symbol>` audit (rare; only for plans focused on a specific symbol's migration)
- **Sister to `/dod-audit`** — chain trace identifies the FULL surface; dod-audit identifies missed PATTERNS on that surface
- **Sister to `/accounting-audit`** — chain trace finds where a value flows; accounting-audit verifies the flow respects accounting invariants
- **Output feeds `/patch-planner`** — chain trace's blast radius assessment informs patch design

## When to use

- Pre-coding for a structural fix that changes a value's shape or semantics (verify blast radius before designing)
- Post-coding to verify cohort migration completeness (e.g., post-cohort-migration ship, trace the migrated symbol cohort to confirm all sites read from the new source)
- Class 27 / Class 28 close verification (trace the migrated symbol; confirm no stragglers)
- Debugging cross-thread data flow issues (which writer wrote what was read?)
- Cohort discovery for a planned sweep (trace `cfg.cores[c].fee_rate_maker` + cohort to find sibling fields)

## Cross-references

- `DESIGN_SPECS/audit-scope-taxonomy.md` § 5 (`chain:<symbol>` shape definition)
- `DESIGN_SPECS/decision-time-data-binding-pattern.md` — relevant when tracing pre-resolved values
- `DESIGN_SPECS/cfg-scope-discipline.md` — relevant when tracing cfg fields
- `DESIGN_SPECS/branchless-dispatch-discipline.md` — relevant when tracing dispatch-table inputs
- All point-scan audit skills — sister/complementary tools
