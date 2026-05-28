---
type: audit-methodology
stage: 3-first-canonical
version: 1.0
established: 2026-05-15
tags: [audit-methodology, meta-discipline, framework-discipline]
surface: [registry]
sister_specs: [audit-driven-pre-coding-gate.md, implementation-layer-blindspot-taxonomy.md]
applies_at_skills: [/parity-check, /trace-deps, /readiness, /merge-scan, /dod-audit, /bug-check, /blindspot-scan, /anti-spaghetti]
---

# Audit scope taxonomy (5 shapes for situation-dependent audit invocation)

**Established:** 2026-05-15 (v5.15.5.F.4c.3 WIP2d-1.B.0d — codified after Caramel call-out that "comprehensive vs focused" is too coarse; large codebase needs situation-dependent scope spectrum to manage context budget + give appropriate depth per pass).
**Status:** Stage 2 DRAFT v1.0 → Stage 3 ACTIVE at `.F.4c.3` ship close
**Tags:** discipline, audit, process, framework-discipline, operator-UX; serves audit quality + context-budget management; Stage 2 (DRAFT); 0 applications until skill spec updates land
**Cross-references:**
- All audit skill specs (`/hft-audit`, `/dod-audit`, `/bug-check`, `/parity-check`, `/accounting-audit`, `/registry-fit-audit`, `/precoding-audit-gate`, `/dependency-chain-trace`) — consume this taxonomy
- `pattern-codification-lifecycle.md` — sister (process pattern; this is operational pattern)
- `audit-driven-pre-coding-gate.md` — sister (when to audit; this is HOW to scope the audit)
- CLAUDE.md skill suite + "How to ..." discovery table — references taxonomy

---

## Problem statement

For a codebase of FoxML_Trader_v2's size (1000+ files, ~150k+ LOC, 60+ registries, deeply layered), "comprehensive vs focused" is too coarse an audit-scope axis. Specifically:

1. **Comprehensive sweep eats context fast.** Full-codebase grep + analysis fills a session's context window before producing actionable findings. Audit output becomes shallow because the agent can't load detailed file content for every site.
2. **Focused (single file) misses cross-file patterns.** Many bug classes (Class 18 mirror-incomplete, Class 25 scope erosion, Class 27 cfg-mirror cache) span MULTIPLE files. Single-file audit misses the cross-file shape.
3. **Different work cadences need different audit shapes.** Mid-active-work audit (verify current edits) is different from sprint-close audit (verify whole ship) is different from quarterly health audit (find new bug classes).
4. **Data-flow trace is a different audit shape entirely.** "Trace where this symbol goes" is a graph traversal, not a point-scan; doesn't fit any existing skill cleanly.

The codified scope taxonomy below addresses all four issues with 5 named scope shapes. All audit skills accept scope as first-class arg + reference this DESIGN_SPEC.

---

## The 5 scope shapes

### 1. `current` — Active work scope

**Coverage:** Uncommitted changes (`git diff` working tree + staged) + commits since branch base + symbols/types directly touched by current edits.

**When to use:**
- Mid-coding feedback loop (after a batch of edits, before commit)
- Pre-commit check (catch regressions in just-changed code)
- Resume-from-handoff verification (audit what the prior session edited)
- During iterative refinement (each iteration audits its own delta)

**Context cost:** LOW — only loads touched files + immediate dependencies. Fast feedback.

**Limitation:** Misses pre-existing issues elsewhere in the codebase. Use `wide` or `module` for that.

**Invocation example:** `/hft-audit current` — audit recent edits for branchless violations.

### 2. `wide` — Full codebase sweep

**Coverage:** Full codebase. All files in scan dirs (CoreFrameworks/, ML_Headers/, Strategies/, Backtest/, DataStream/, MemHeaders/, tests/ where applicable).

**When to use:**
- Quarterly health audit (find new bug classes; calibrate baseline)
- Post-codification of new anti-pattern (sweep for existing instances of newly-named class)
- Pre-paper-test full audit (comprehensive verification before live-readiness)
- Skill refinement (verify skill catches what it should across the codebase)

**Context cost:** HIGH — fills context fast; depth per file is shallow. Output is broad-shallow.

**Mitigation:** When findings exceed reasonable triage size (>30 findings), follow up with `module`-scoped re-audits per priority area.

**Invocation example:** `/hft-audit wide` — quarterly branchless discipline audit.

### 3. `scoped <glob>` — File-glob / path scope

**Coverage:** Files matching the glob OR within the given directory path. Standard shell-glob syntax.

**When to use:**
- Audit a specific file or set of files (e.g., recently rewritten subsystem)
- Drill into a specific subsystem after a `wide` sweep flagged it
- Verify a particular API surface before a downstream change

**Context cost:** LOW-MED — bounded by glob size.

**Limitation:** Operator must know which files to specify. Use `module` for semantic grouping when file membership isn't precisely known.

**Invocation example:** `/hft-audit scoped CoreFrameworks/OrderManager*` — audit OMS files specifically.

### 4. `module <name>` — Named module / semantic group

**Coverage:** Files belonging to a named MODULE — a semantic grouping that may span multiple directories or even repos. Module-to-files mapping is defined per-skill OR looked up from a shared module registry (`tick-trader-percore-workspace/DOCS/MODULE_MAP.md` — to be established as a separate sub-ship).

**Named modules (initial registry):**

| Module name | Files / directories included |
|---|---|
| `OMS` | `CoreFrameworks/Order*`, `CoreFrameworks/OMSReady.hpp`, `MemHeaders/OmsFieldRegistry.hpp`, `MemHeaders/OmsPhasedDrain.hpp`, `CoreFrameworks/Reconcile*`, `CoreFrameworks/BinanceOrderAPI.hpp` |
| `engine` | `CoreFrameworks/EngineSharded.hpp`, `CoreFrameworks/ControllerEventLoop.hpp`, `CoreFrameworks/ExecutionCore.hpp`, `CoreFrameworks/ControllerConfig.hpp`, `CoreFrameworks/CfgFieldRegistry.hpp`, `CoreFrameworks/MetaRegistry.hpp` |
| `ML-pipeline` | `ML_Headers/*` |
| `strategies` | `Strategies/*` |
| `backtest` | `Backtest/*` |
| `data-stream` | `DataStream/*` |
| `GUI` | `GUI/*` |
| `tests` | `tests/*` |
| `cfg-surface` | `CoreFrameworks/ControllerConfig.hpp`, `CoreFrameworks/CfgFieldRegistry.hpp`, `CoreFrameworks/CfgFieldDispatch.hpp`, `CoreFrameworks/MetaRegistry.hpp` |
| `accounting` | `CoreFrameworks/OrderManager.hpp`, `CoreFrameworks/Portfolio.hpp`, `CoreFrameworks/PortfolioController.hpp`, `CoreFrameworks/ControllerConfig.hpp` (fee/slippage cfg fields), `ML_Headers/ConfidenceScore.hpp` |
| `wire-format` | `ML_Headers/StampBoundCfgRegistry.hpp`, `ML_Headers/StampBoundModelConstRegistry.hpp`, `ML_Headers/CfgDriftCheckRegistry.hpp`, `ML_Headers/ModelInference.hpp`, snapshot/persist files |
| `bandit` | `ML_Headers/BanditAlgorithmRegistry.hpp`, `ML_Headers/CoreModelZoo.hpp` (bandit dispatch), `ML_Headers/ThompsonBandit.hpp` |
| `risk` | `CoreFrameworks/RiskGates.hpp` (if exists), kill-switch + drawdown surfaces in OMS + ControllerEventLoop |

**When to use:**
- Module-by-module deep audit (iterate through modules; deep analysis per pass)
- Area-of-concern audit (e.g., "audit `OMS` for Class 27 + Class 28")
- Pre-coding audit when work touches a specific module
- Cohort sweep after a new pattern is codified (audit each module for the new pattern)

**Context cost:** MED — bounded by module size; designed for "fits in one focused session per module."

**Module registry maintenance:** As the codebase grows, modules are added to `MODULE_MAP.md`. New module names get a SHORT (one-word) identifier + the file/dir membership. Skills look up the registry at invocation time.

**Invocation example:** `/hft-audit module:OMS` — audit OMS module for branchless violations (loads only OMS files into context).

### 5. `chain <symbol>` — Dependency-chain / data-flow trace

**Coverage:** Track a specific symbol or data path through every site that touches it. NOT a point-scan — a flow trace. Output: graph of read/write sites, lifecycle, cross-thread interactions, blast radius.

**When to use:**
- Pre-coding: understand the FULL surface of a value before changing it (avoids Class 18 mirror-incomplete after edits)
- Post-coding: verify ALL sites updated when a value's semantics changed (e.g., after migrating a cfg field to per-node)
- Cohort discovery: find all sites that touch a value family (e.g., `fee_rate_*` cohort)
- Debugging: trace where data was written, where it was read, identify mismatches
- Class-27/Class-28 close verification: confirm all sites migrated; no stragglers

**Workflow** (executed by `/dependency-chain-trace` skill):
1. Find symbol DEFINITION (struct field declaration, enum value, global variable, function)
2. Find all WRITE sites (`X = `, `X[...] = `, `X(...) = `, mutator function calls)
3. Find all READ sites (member access, function arg, comparison, etc.)
4. Classify each site by:
   - Thread (which thread executes it: producer/drainer/slow-path/hot-path/GUI/boot)
   - Cadence (boot-once / per-cycle / per-fill / per-tick / per-cmd / cross-thread-snapshot)
   - Type (definition / mutation / observation / propagation / serialization)
5. Build the DATA FLOW graph: which writes feed which reads (temporal + lifecycle)
6. Identify cohort siblings (related symbols typically touched together)
7. Compute blast radius (if this symbol changes shape/semantics, what breaks)

**Output:** Structured flow report. Sections: Definition, Writes (per thread + cadence), Reads (per thread + cadence), Data flow graph, Cohort siblings, Blast radius assessment, Recommended caveats for downstream change.

**Context cost:** MED — bounded by the symbol's actual touch surface. Most symbols touched 5-50 places.

**Limitation:** Doesn't find pattern instances elsewhere (use `wide` or `module` for that). Single-symbol focus.

**Invocation example:** `/dependency-chain-trace cfg.cores[c].fee_rate_maker` — flow audit before B.1.b cohort sweep.

---

## Decision matrix — which scope when

| Situation | Default scope | Why |
|---|---|---|
| Active coding feedback loop | `current` | Fast iteration; only touched code |
| Pre-commit check | `current` | Catch regressions in just-changed code |
| Post-handoff verification | `current` + targeted re-audit if findings | Verify what prior session did |
| Quarterly codebase health | `wide` | Find new bug classes; calibrate baseline |
| New anti-pattern codified | `wide` then `module:<priority>` | Sweep for existing instances; deep-dive priority areas |
| Pre-paper-test full check | `wide` (multiple skills in parallel) | Comprehensive verification before live-readiness |
| Pre-coding for known area | `module:<area>` | Bounded depth; manageable context |
| Verify cohort migration completeness | `chain:<symbol>` | Confirm all sites updated |
| Investigate specific subsystem | `module:<subsys>` or `scoped:<glob>` | Bounded depth; appropriate file set |
| Debug specific data flow | `chain:<symbol>` | Trace where data went wrong |
| Sprint pivot / new pattern application | `module:<area>` then `chain:<symbol>` for the new pattern | Module-level depth + chain-level verification |

The scope shape is a SITUATIONAL DECISION, not a one-size-fits-all default. Operators (and the agent) pick the appropriate shape per work context.

---

## Invocation conventions (uniform across audit skills)

All audit skills accept scope as the FIRST positional argument (or `--scope=<shape>` named):

```
/<skill-name> <scope> [focus_keywords...]
/<skill-name> current
/<skill-name> wide
/<skill-name> scoped <glob>
/<skill-name> module:<name>
/<skill-name> chain:<symbol>
```

**Default scope when omitted:** `current` (active work) for most audit skills — fast feedback, low context cost. Operator override via explicit scope arg.

**Exception — `/dependency-chain-trace`:** scope arg is REQUIRED (the symbol/path to trace).

**Composability** — `/precoding-audit-gate` accepts per-audit scope in its audit_set:
```
/precoding-audit-gate <plan_path> parity:current,trace:current,dod:module:OMS,hft:scoped:CoreFrameworks/Order*
```

---

## Skill spec contract (uniform section across audit skills)

Every audit skill spec includes a section:

```markdown
## Scope (per audit-scope-taxonomy.md)

This skill accepts scope as first positional arg:
- `current` (default) — uncommitted edits + recent commits + touched symbols
- `wide` — full codebase sweep
- `scoped <glob>` — file/dir glob scope
- `module:<name>` — named module (see MODULE_MAP.md registry)
- `chain:<symbol>` — N/A for this skill (use /dependency-chain-trace)

When scope is `current` or `module:<name>`, skill spawns ONE subagent loading only the in-scope files. When scope is `wide`, skill spawns subagent(s) per logical scan dir to avoid context overflow.
```

The skill spec then documents which scope shapes are most appropriate for the skill's domain.

---

## Trade-offs + when to apply

**Apply taxonomy when:**
- Audit skill is invoked
- Operator is unclear which scope fits the situation (default to `current`; escalate to `module` or `wide` if needed)
- Composing multi-skill audit gates with per-audit scope discipline

**Skip taxonomy when:**
- One-off code-question lookup (not really an audit)
- Skill genuinely scope-less (e.g., `/handoff` is operational, not an audit)

**Cost:**
- Skill spec updates (one-time per skill; ~5-7 skills)
- NEW skill `/dependency-chain-trace` (one-time; ~250 LOC of spec)
- MODULE_MAP.md maintenance (ongoing; updates as new modules emerge)
- Operator cognitive load: understanding the 5 shapes (one-time)

**Win:**
- Context budget management (large codebase doesn't overflow audit context)
- Appropriate depth per audit (module-by-module gives deeper analysis than wide sweep)
- New audit shape (chain trace) becomes invocable
- Skill composition becomes precise (per-audit scope in /precoding-audit-gate)
- Anti-pattern: "comprehensive vs focused" coarse binary defaults retired

---

## Reference implementations

Populated at Stage 3 ACTIVE — shipped skill specs get cross-refs back here.

- (pending) `claude-skills/hft-audit/SKILL.md` — first canonical scope arg adoption (.F.4c.3 WIP2d-1.B.0d)
- (pending) `claude-skills/dod-audit/SKILL.md` — scope arg adoption
- (pending) `claude-skills/bug-check/SKILL.md` — scope arg adoption
- (pending) `claude-skills/parity-check/SKILL.md` — scope arg adoption
- (pending) `claude-skills/accounting-audit/SKILL.md` — scope arg adoption (already has subsystem scope concept; uniforms)
- (pending) `claude-skills/registry-fit-audit/SKILL.md` — scope arg adoption (already has registry scope concept; uniforms)
- (pending) `claude-skills/precoding-audit-gate/SKILL.md` — per-audit scope in audit_set
- (pending) `claude-skills/dependency-chain-trace/SKILL.md` — NEW skill for `chain:<symbol>` shape

---

## Lessons / gotchas

- **Don't default to `wide`** — eats context. Default to `current`; escalate scope when findings warrant.
- **Module names should be SHORT (one-word)** — `OMS`, `engine`, `ML-pipeline`. Long names create friction at invocation time.
- **MODULE_MAP.md needs maintenance** — when new subsystems are added, register them. CI check could enforce that every directory in scan-dirs maps to at least one module (future).
- **`chain:<symbol>` is a graph traversal, not a point-scan** — `/dependency-chain-trace` skill is genuinely different from `/hft-audit` and friends; don't try to bolt chain-trace onto point-scan skills.
- **Per-audit scope in /precoding-audit-gate is powerful but complex** — `parity:current,trace:current,dod:module:OMS,hft:wide` is precise but verbose. Default to uniform scope per gate invocation; per-audit override when warranted.
- **The hand-wave failure mode is "I'll just sweep the whole codebase"** — for any non-trivial codebase, that overflows context AND produces shallow analysis. Scope discipline forces appropriate depth.

---

## Cross-references

- All audit skill specs (consume this taxonomy)
- `audit-driven-pre-coding-gate.md` — when to audit; this spec answers HOW to scope
- `pattern-codification-lifecycle.md` — sister process pattern
- (future) `tick-trader-percore-workspace/DOCS/MODULE_MAP.md` — module registry
- CLAUDE.md skill suite table — references taxonomy
- CLAUDE.local.md going-forward rule — "When invoking audit skills, specify scope per situation"
