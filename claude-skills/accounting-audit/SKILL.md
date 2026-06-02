---
name: accounting-audit
description: Scan accounting / money tracking paths for silent-correctness hazards — Class 27 scalar cfg-mirror caches, per-core fee/commission indexing gaps, slippage / fee floor cross-path inconsistency, float/double in accounting paths (H4), lossy FPN_ToDouble conversions, position/balance update atomicity, backtest↔live accounting parity. Output is a severity-classified findings report, NOT actual edits. Operator triages.
type: skill
concern: domain-audit
audit_cadence: ad-hoc
tags: [fixed-point-math, structural-fix, failure-observability]
surface: [oms-drainer, hot-path, slow-path, backtest, live-trading, wire-format]
sister_skills: [/parity-check, /hft-audit, /dod-audit, /bug-check, /ml-audit]
loads_dynamically: [DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md, DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md, DESIGN_SPECS/data-disciplines/cache-layout-discipline-for-hot-side-structs.md, DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md, DOCS/DESIGN_PHILOSOPHY.md, DESIGN_SPECS/meta-disciplines/skill-knowledge-consultation-and-auto-routing.md]
skill_kind: judgment
associated_anti_patterns: [DOCS/RECURRING_BUG_PATTERNS.md, DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md]
associated_decisions: [plans/<active-sprint>/decision-logs/]
associated_postmortems: [plans/<active-sprint>/postmortems/]
associated_ledgers: [DOCS/TECH_DEBT.md, DOCS/PARITY_ISSUES.md]
trigger_heuristics: ["accounting / money-path audit / fee / slippage / FPN / balance -> suggest /accounting-audit"]
---

# /accounting-audit — Accounting / money-tracking path audit

> **Stage 0 — consult institutional knowledge** (per `skill-knowledge-consultation-and-auto-routing.md`): before judging, load this skill's `associated_*` slice (specs / anti-patterns / decisions / postmortems / ledgers) + run the canonical-sister check; if running as a cold Explore/Plan subagent, ensure CLAUDE.md/MEMORY are loaded first. Then the preloads:
>
> **Stage 0 preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 3 (Hard Invariants) — H4 (FPN<F> for accounting; never float/double) + H9 (wire-format byte preservation including stamp accounting fields)
> - § 1.5 (Framework-driven extensibility meta-principle) — Class 27 + Class 24 closure rationale
>
> **Stage 0 preload** (workspace/DESIGN_SPECS/):
> - `decision-time-data-binding-pattern.md` — Class 27 structural fix; the principle this skill enforces
> - `cfg-scope-discipline.md` — per-instance scope decisions for accounting fields
> - `cache-layout-discipline-for-hot-side-structs.md` — subsystem state layout for accounting consumers
> - `postloadsetup-registry-pattern.md` — fallback cache cfg-reload sync mechanism
>
> Cite specific § N rows in finding descriptions.

## What this does

Walks the accounting / money-tracking paths systematically looking for silent-correctness hazards that classic test suites don't catch. Distinct from:
- `/parity-check` (ML train↔serve identity; specific to model pipeline)
- `/hft-audit` (universal HFT principles: cache, branchless, lock-free)
- `/dod-audit` (DOD pattern application)
- `/bug-check` (generic RECURRING_BUG_PATTERNS scan; this skill is the specialized first-line-of-defense for Class 27 + accounting-specific surfaces)
- `/ml-audit` (ML pipeline silent failures; accounting is sister but distinct surface)

Output is a structured findings report. NOT actual edits. Operator decides which items to pick up.

## Scope (per audit-scope-taxonomy.md)

This skill accepts scope as first positional arg per `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md`:

- `current` (default when no scope specified) — accounting paths in recent edits + touched files
- `wide` — full codebase accounting sweep; HIGH context cost; recommended quarterly
- `scoped <glob>` — file/dir glob (e.g., `/accounting-audit scoped CoreFrameworks/OrderManager*`)
- `module:<name>` — named module per `MODULE_MAP.md` registry. Most-used for accounting: `OMS`, `accounting`, `backtest`. Recommended for iterative module-by-module accounting deep-dives.
- `chain:<symbol>` — N/A (use `/dependency-chain-trace` for symbol flow traces; chain-trace pairs well with accounting-audit for fee/slippage cohort sweeps)

**Most appropriate scope shapes for /accounting-audit:** `current` (during active work), `module:OMS` / `module:accounting` / `module:backtest` (iterative deep accounting audits), `wide` (quarterly + post-Class-27-codification sweeps).

## Invocation

- `/accounting-audit` — default scope `current`; accounting paths in recent edits
- `/accounting-audit <scope>` — explicit scope per taxonomy
- `/accounting-audit <scope> [focus_keywords...]` — narrow by concern within scope

**Examples:**
- `/accounting-audit current` — fast feedback during active coding
- `/accounting-audit module:OMS` — deep accounting audit of OMS module
- `/accounting-audit module:accounting fee_rate` — focused fee_rate scan in accounting module
- `/accounting-audit wide cross-path-parity` — full sweep narrowed to live↔backtest parity
- `/accounting-audit scoped Backtest/BacktestSharded.hpp` — single-file scan

## Pass structure

Spawn an Explore subagent. The subagent walks the standard 10-category checklist + the focus keywords. For each category, identifies concrete file:line citations of risk + classifies severity.

### Severity tiers

- **CRITICAL** — silent miscalculation of real money values; affects accounting reconciliation; potentially-violates-H4-invariant; immediate triage required
- **HIGH** — parity drift between live + backtest accounting; per-instance flatten risk; OMS / drainer pattern that won't survive cfg hot-swap; brittleness in money path
- **MEDIUM** — observability gap; auditable-trail incompleteness; per-instance distinction risk under upcoming changes; cohort-eligible Class 27 instance
- **LOW** — style / micro-correctness improvement that doesn't affect accounting today

### 10-category checklist

1. **Class 27 instances (scalar cfg-mirror)** — scan designated subsystem state types (per `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` § Class 27 target subsystems) for scalar fields that mirror cfg field names. Each is a candidate for pre-resolve onto in-flight object (Order/Position/Event) OR registry-driven per-instance cache (FOREACH_<SUBSYS>_CFG_CACHE fallback). The CI check that enforces Class 27 prevention (currently `tools/check_per_core_registry_integrity.py` Check 7) catches new instances; this audit catches existing ones + edge-case patterns.

2. **Per-core / per-instance fee_rate + commission indexing** — every fee/commission read MUST resolve to the relevant instance (per-core via `cfg.cores[c]` or pre-resolved on in-flight object). Flag global `cfg.fee_rate_*` reads at sites that have per-instance context available.

   **Class 26 sub-shape distinction (NEW v5.15.5.F.4d.1.B.8 amendment):** Class 26 has TWO sub-shapes documented at `DOCS/recurring-bug-patterns/class-26-global-consumer-reading-per-core-field.md § Sub-shapes`:
   - **Sub-shape A (WRONG-INDEX paired-access)** — `cfg.core_overrides[X]` + `cfg.cores[Y]` paired access with X != Y; CI Check 9 catches mechanically per `tools/check_per_core_registry_integrity.py`
   - **Sub-shape B (UNINDEXED-GLOBAL at per-core consumer site)** — `cfg.X` / `cfg->X` / `resolved_cfg.X` UNINDEXED on per-core-with-global-sister fields (fee_rate / fee_rate_taker / fee_rate_maker / slippage_pct); CI Check 10 catches mechanically (sister to Check 9; M7 6th canonical)

   **When firing this audit:** distinguish sub-shape A vs B in findings; cite Check 9 / Check 10 respectively for mechanical detection. Findings format: `class_subshape: A` or `class_subshape: B`. Reference: `.B.7` Async.hpp:814+853 (sub-shape A); `.B.8` ControllerEventLoop.hpp:3605+3670+3042 + StrategyLifecycle.hpp:272 + ShardedSnapshot.hpp:249 (sub-shape B).

3. **Slippage / fee floor consistency across paths** — slippage_pct, fee_floor_pct, slip + fee model MUST be byte-equivalent across slow-path / drainer / backtest. Flag divergence (e.g., backtest uses cfg.fee_rate while live uses oms->fee_rate_taker).

4. **H4 enforcement (FPN<F> for accounting)** — scan accounting paths for `float` / `double` storage of monetary values. Display-only conversions OK; accounting STORAGE must be FPN<F>. Flag double-typed fields in Position, Order, balance/realized_pnl/fees, ConfidenceScorer reward updates with monetary semantics.

5. **Lossy FPN_ToDouble in accounting paths** — `FPN_ToDouble(...)` calls inside accounting computations introduce double-precision loss; the result must be converted back via FPN_FromDouble before storage. Flag double-typed intermediates in accounting chains that don't round-trip through FPN.

6. **Position / realized_pnl / balance update atomicity** — single-source-of-truth invariants. `oms->balance` + `oms->realized_pnl` + `portfolio.total_fees` + `core_realized` per-core must compose consistently. Flag double-updates, missing updates, or order-dependent updates that could race.

7. **Backtest ↔ live accounting parity** — `BacktestSharded` accounting paths MUST produce byte-equivalent fees/P&L/balance to live engine given identical fill stream. Flag silent divergences (e.g., backtest uses static cfg.fee_rate, live uses dynamic per-core).

8. **PortfolioController vs OMS accounting consistency** — legacy `PortfolioController` (single_core) + sharded OMS maintain separate accounting state. The cohort's accounting struct must enforce sanity invariant `total_fees == total_maker_fees + total_taker_fees` across both paths.

9. **`static const T = cfg.X` HAZARD** — function-local static caches of cfg-derived values freeze first value forever; no sync path. Class 27 fn-local variant. Always-flag regardless of subsystem (grep: `static\s+const\s+\w+\s+\w+\s*=\s*\w*FPN_ToDouble\s*\(\s*cfg\.\w`).

10. **Kill switch / drawdown / risk envelope per-instance** — `kill_switch_daily_loss_pct`, `kill_switch_drawdown_pct`, `max_drawdown_pct`, `max_exposure_pct` are per-core (cfg.cores[c]) per cfg-scope-discipline.md. Flag global reads at sites with core_id in scope.

## Cross-skill composition

- **Calls `/registry-fit-audit`** when a finding suggests a registry was the wrong tool (e.g., FOREACH_<SUBSYS>_CFG_CACHE used where pre-resolution should apply). Defers registry-shape recommendation to that skill.
- **Invoked by `/precoding-audit-gate`** when audit scope includes accounting / money paths (any plan touching OMS, fee/commission, P&L, balance, kill switches, fee floors, slippage).
- **Sister to `/bug-check`** — bug-check is the generic registry-driven scan; accounting-audit is the specialized first-line-of-defense for Class 27 + accounting-specific anti-patterns. Findings can be cross-tagged.

## Output format

Generate a structured markdown report:

```markdown
# /accounting-audit findings — <date> <scope>

## Summary
- CRITICAL: N findings
- HIGH:     N findings
- MEDIUM:   N findings
- LOW:      N findings

## Findings

### [CRITICAL-1] <title> (`File/Path.hpp:LINE`)
- **Severity:** CRITICAL
- **Category:** <one of the 10 categories>
- **Class:** Class 27 / Class 24 / Class 18 / N-A
- **Details:** <mechanical explanation of the silent-correctness hazard>
- **Recommended fix:** <pre-resolve onto in-flight object | per-core array via FOREACH_<SUBSYS>_CFG_CACHE | Pattern 2 (inline cfg.cores[c]) | other>
- **DESIGN_SPEC reference:** <relevant pattern doc>

### [HIGH-1] ...
...
```

Cross-reference EVERY finding to:
1. A DESIGN_SPEC if the fix is a known pattern
2. A RECURRING_BUG_PATTERNS class if applicable
3. The CI check that would catch regression (if any) — Check 7 for Class 27

## Anti-patterns to flag (DO NOT DO THIS in your own findings)

- Do **not** flag display-only `FPN_ToDouble` conversions (GUI render, log emit). These are H4-compliant.
- Do **not** flag missing accounting code paths that genuinely don't apply (e.g., flagging "no fee_rate field on TickEvent" — TickEvent isn't an accounting object).
- Do **not** propose fixes that would introduce mirror state across threads (the cure is worse than the disease).
- Do **not** suggest fixing scalar cfg-mirror by "just sync more often" — that's Class 27 perpetuation; structural fix is pre-resolve or registry fallback.

## When to use

- **Quarterly accounting sweep** — full pass across the codebase to catch new Class 27 instances + accounting drift
- **Pre-ship for any plan touching OMS / drainer / fee/commission / kill switch surfaces**
- **Post-paper-test surfacing of accounting anomaly** — narrow scope to the surface that showed unexpected behavior
- **Pre-live-readiness ship gate** — comprehensive sweep before flipping `trading_mode=live`

## Cross-references

- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` — the principle for Class 27 closure
- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` — per-instance scope for accounting fields
- `DESIGN_SPECS/data-disciplines/cache-layout-discipline-for-hot-side-structs.md` — subsystem state layout
- `DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md` — fallback cache cfg-reload hook
- `DOCS/RECURRING_BUG_PATTERNS.md` Classes 24, 25, 26, 27 — the recurring anti-patterns this skill catches
- `tools/check_per_core_registry_integrity.py` Check 7 — CI enforcement for Class 27
- `DOCS/MANUAL_FIELDS_INVENTORY.md` Section C — Class 27 exemption registry
- CLAUDE.md item 31 + DESIGN_PHILOSOPHY § 11 framework-selection criteria — meta-principle
