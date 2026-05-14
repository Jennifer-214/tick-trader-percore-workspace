# DESIGN_SPECS — reusable architectural pattern reference library

**Established 2026-05-09 (mid v5.14.8 sprint).** Workspace-private. Each doc captures ONE solved design problem so future ships can reuse the pattern without re-deriving.

## Purpose

When a session solves a non-trivial architectural problem (e.g., "how do we make this registry handle partial-mirror struct generation cleanly?"), the design exploration + decision rationale + final pattern is valuable beyond the specific ship. It often reveals a REUSABLE TEMPLATE that applies elsewhere.

This directory is the library of those templates. Each doc:
- Names the pattern + its problem
- Walks the design space (options considered, why we picked one)
- Shows the concrete shape (code snippets, file references, examples)
- Documents the trade-offs + when NOT to apply
- Cross-references where the pattern was first applied + subsequent uses

## Naming convention

`<pattern-kebab-case>.md` — describe the pattern, not the specific ship.

Good: `bitmap-flag-api.md`, `x-macro-registry-with-presence-dispatch.md`, `audit-driven-pre-coding-gate.md`

Bad: `v5.14.8-stamp-body.md` (ship-specific; not reusable), `bitmap-stuff.md` (too vague)

## Structure per doc (~200-400 lines target)

```markdown
# <Pattern Name>

**Established:** YYYY-MM-DD (ship vX.Y.Z)
**Status:** ACTIVE / DEPRECATED / SUPERSEDED-BY-X
**Cross-references:** related design specs, code files, postmortems

## Problem statement
1-3 paragraphs. Recurring symptom + root cause class. WHY this pattern exists.

## Design space explored
Options A/B/C... considered, with trade-offs. WHY the chosen option won.

## The pattern (concrete shape)
Code snippets, macro definitions, struct shapes. Self-contained enough that a future
session can implement it without reading the original ship.

## Trade-offs + when to apply
- Apply when: <symptoms>
- Skip when: <symptoms>
- Cost: <effort, complexity, blast-radius>
- Win: <bug-class extinction, latency, etc.>

## Reference implementations
- First applied: <code path + commit/tag>
- Subsequent uses: <list>

## Lessons / gotchas
Surprises during implementation. Compaction-degraded handoff watch-outs. Etc.
```

## Catalog (v5.14.4 + v5.14.8 + v5.14.9 + v5.14.10 + v5.14.11 deliverables — 26 patterns)

Organized by category for quick discovery. Each pattern is one file in this dir.

### Core registry patterns (X-macro-driven extensibility)

| Doc | Pattern | Status |
|---|---|---|
| `x-macro-registry-with-presence-dispatch.md` | X-macro registry with token-paste (Y3) dispatch for partial-mirror struct generation. Emit_source column extension. | ACTIVE (v5.14.8) |
| `autopopulate-pattern-for-production-caller-class.md` | Production-caller field-population class extinction (AUTOPOPULATE companion macro from source-struct) | ACTIVE (v5.14.8) |
| `autopopulate-from-arity-macro-family.md` | _FROM_PAIR / _FROM_TRIPLE / _FROM_HEX / _FROM_SEPTUPLE — AUTOPOPULATE variant for callers with SCATTERED locals (no source struct) | ACTIVE (v5.14.9.F-.F.3) |
| `pre-post-cfg-registry-split-for-emit-order-preservation.md` | PRE/POST registry split when emit order must interleave with sister registry | ACTIVE (v5.14.8) |
| `registry-tuple-as-single-source-of-truth.md` | Option D — 5-col tuple feeds cfg + parser + GUI + override + stamp-binding + docs from ONE source | ACTIVE (v5.14.9.F.5) |
| `curve-registry-pattern.md` | FOREACH_<DOMAIN>_CURVE — named compute fns chosen by enum (LINEAR/EXP/STEP) via fn-pointer dispatch | ACTIVE (v5.14.9.A) |
| `calibration-log-column-registry.md` | FOREACH_<LOGNAME>_COL — auto-generated CSV header + row from registry; Variant A (fprintf direct) + Variant B (snprintf to buffer) | ACTIVE (v5.14.10.D + .F; 2 reference applications: calib log + trade log) |
| `postloadsetup-registry-pattern.md` | FOREACH_<DOMAIN>_POST_LOAD — auto-flow init/load steps to N call sites (boot + backtest + hot-swap); Class 18 mirror prevention via single helper walking registry | ACTIVE (v5.10.0a.G.7 + v5.13.4 + v5.14.10.C; 3 applications) |

### Registry decision frameworks

| Doc | Pattern | Status |
|---|---|---|
| `heterogeneous-registry-pattern.md` | SCOPE COLUMN vs DOMAIN SPLIT vs HYBRID (Form 1/2/3); Y3 dispatch canon; cache-layout discipline | ACTIVE v1.0 (field-tested v5.14.9.F-.F.6 + .G + .H) |
| `cfg-flag-eligibility-criteria.md` | 5-criteria decision algorithm — when a boolean is cfg-flag-eligible (and when it's not; `lat_enabled` cautionary tale) | ACTIVE (v5.14.9.F step 0) |
| `slow-path-gate-registry-pattern.md` | FOREACH_SLOW_PATH_GATE + AUTOPOPULATE; SCOPE COLUMN form canonical example | ACTIVE (v5.14.9.B.0) |
| `structural-fix-preferred-decision-framework.md` | When to invest in structural fix vs direct patch | ACTIVE (v5.14.8) |

### Bitmap variants

| Doc | Variant | Status |
|---|---|---|
| `bitmap-flag-api.md` | Base BITMAP_* macros (BITMAP_IS_SET / BITMAP_SET / BITMAP_BIT_U16 etc.) + 5 applied-variant cross-refs | ACTIVE (v5.14.8) |
| `partner-core-bitmap-pattern.md` | Per-core bool[N] → 1-bit-per-core in uint16/32/64 on parent struct (v5.14.9.G — `partner_pending_bitmap`) | ACTIVE (v5.14.9.G) |
| `transient-aggregation-bitmap-pattern.md` | Function-local aggregation bitmap with headroom (v5.14.9.H — `scaler_summary_flags`) | ACTIVE (v5.14.9.H) |
| `per-bit-per-core-override-pattern.md` | PER_CORE_OVERRIDE_BITMAP_DOMAINS — branchless bit-select for per-core overrides on bitmap fields (v5.14.9.F.6) | ACTIVE (v5.14.9.F.6) |

### Discipline / process patterns

| Doc | Pattern | Status |
|---|---|---|
| `audit-driven-pre-coding-gate.md` | Multi-audit pattern + compaction-handoff verification + MID-sprint audit guidance | ACTIVE (v5.14.8 + .9 update) |
| `wire-format-byte-preservation-discipline.md` | Guarding HMAC chains across registry refactors | ACTIVE (v5.14.8) |
| `avx512-byte-determinism-pattern.md` | 8 rules for AVX-512 vectorization with bytewise-identical scalar reference path; SHA-256 cross-binary lock test pattern; Rule 8 added v5.14.11.B.4 (branchless within vectorized block) | ACTIVE (v5.11.7 + v5.14.11.B; first + second applications) → CLAUDE.md item 25 |
| `pattern-codification-lifecycle.md` | Meta-pattern — 7-stage lifecycle for codifying a new architectural pattern (audit → DESIGN_SPEC → first reference → cohort migration → CLAUDE.md item → tooling enforcement → wider audit). v5.14.11.B mega-bundle is the canonical first explicit application | ACTIVE (v5.14.11.B umbrella; meta-pattern retroactively documenting the implicit lifecycle applied in v5.14.8/.9/.10) |

### Cross-thread snapshot patterns

| Doc | Pattern | Status |
|---|---|---|
| `per-snapshot-cluster-layout-pattern.md` | alignas(64) clustering of cross-thread snapshot fields by concern; cache-line span budgeting; static_assert(offsetof) enforcement | ACTIVE (v5.14.10.0; first application: PerCoreSnap bandit telemetry cluster) |

### Math kernel patterns

| Doc | Pattern | Status |
|---|---|---|
| `sliding-window-online-statistics-pattern.md` | Sum-of-squares fixed-window incremental statistics with drop-oldest math; bounded-input numerical-stability argument; AVX-512 outer-product shape; eliminates periodic-reset code smell. **Multi-window variant** (v5.15.5.D): one ring buffer serves N independent running sums via per-window eviction offsets — long-window evicts at `samples[head]`, short-window at `samples[head - K]`; warm-up phase (count ≤ K) both sums equal | **INVARIANT STATUS** (3 canonical applications: v5.14.11.A Ridge correlation matrix; v5.14.11.B.3 AVX-512 vectorization; v5.15.5.D BookImbHistory dual-window mean; v5.15.5.E.D RollingRMSE running-sum) → CLAUDE.md item 29 |
| `branchless-math-kernel-pattern.md` | Constant-iter inner reductions (use MAX_* constants, not runtime n); pre-zero invariants establish zero contributions for out-of-bounds iterations; no `if` guards inside reductions; IEEE-754 x-0=x exact preserves bytewise-equivalence with prior variable-iter | ACTIVE (v5.14.11.B.1 first application: Cholesky_Solve); → CLAUDE.md item 26 |
| `generic-ring-buffer-template-pattern.md` | Generic `RollingWindow<T, N>` template (count + head + window + samples[N]); variants COMPOSE for type-specific math. Closes Class-18 mirror between ring-buffer struct types. Bare template (no internal alignas; consumer owns alignment). `/dod-audit` Stage 6 detection signature embedded for missed-application flagging. | **NEW (v5.15.5.E.C)** ACTIVE (RollingIC + RollingRMSE first 2 applications). Future: BookImbalanceHistory, LargeTradeState, SpreadState, RollingStats, DriftHistory.samples migration candidates (Stage 7 wider audit). |

### Struct layout patterns

| Doc | Pattern | Status |
|---|---|---|
| `struct-padding-determinism-pattern.md` | Explicit `int<N>_t _padding<N> = 0;` default-init fields for structs in byte-equivalence contexts (memcmp / SHA-256 / wire format). Eliminates UB padding bytes via C++ default member init; same struct size; future-proof against stack-layout shifts | ACTIVE (v5.14.11.B.2 first application: FPN<F>; second application: ThompsonBanditState); → CLAUDE.md item 27 |

### Determinism patterns

| Doc | Pattern | Status |
|---|---|---|
| `prng-choice-for-replay-determinism.md` | When replay-determinism + persistence are both load-bearing, prefer SIMPLE algorithm with small state (splitmix64; 1 uint64) over HIGH-QUALITY algorithm with large state (mt19937_64; 312 words). `std::normal_distribution` is UNSAFE for cross-binary replay (libstdc++-implementation-defined). Pattern + Box-Muller recipe + seed-scrambling helper + SHA-256-locked sample-trace test. | ACTIVE (v5.14.10.A first application: ThompsonBanditState PRNG) |

### Dependency-injection patterns

| Doc | Pattern | Status |
|---|---|---|
| `template-deferred-dependency-injection.md` | Logic-only headers preserve I/O-free contract by taking side-effect primitive as template parameter (`typename Fn`); caller injects via lambda. Same shape across live/test/backtest. Zero runtime overhead (compiler inlines lambda). | ACTIVE (v5.14.4.B.1 + .B.2 first applications: Reconcile_ApplyMissedFills + Reconcile_AutoCancelStale) |

**26 patterns total.** Adding new patterns: write the doc, add a row above, cross-link from related docs. (Process meta-tip: follow `pattern-codification-lifecycle.md` — the meta-pattern that captures HOW to fully codify a new architectural discipline end-to-end.)

## Quick discovery — "I need to..."

- **...add a cfg flag (boolean toggle)** → `cfg-flag-eligibility-criteria.md` (decide eligibility) → `heterogeneous-registry-pattern.md` (pick domain) → `registry-tuple-as-single-source-of-truth.md` (5-col tuple)
- **...add a compute mode chosen by enum** → `curve-registry-pattern.md`
- **...replace multiple booleans with a bitmap** → `bitmap-flag-api.md` (which VARIANT?) → variant-specific doc:
  - Engine cfg domain → `heterogeneous-registry-pattern.md`
  - Per-core boolean → `partner-core-bitmap-pattern.md`
  - Function-local summary → `transient-aggregation-bitmap-pattern.md`
  - Registry has_flags → `x-macro-registry-with-presence-dispatch.md`
- **...add per-core override to a bitmap field** → `per-bit-per-core-override-pattern.md`
- **...stamp-bind a registry-derived field** → `wire-format-byte-preservation-discipline.md` (HMAC byte-equivalence) + `x-macro-registry-with-presence-dispatch.md` (emit_source column)
- **...avoid forgetting to populate a field at a production caller** → `autopopulate-pattern-for-production-caller-class.md` OR `autopopulate-from-arity-macro-family.md` (depending on caller shape)
- **...decide between structural fix vs direct patch** → `structural-fix-preferred-decision-framework.md`
- **...verify a sprint plan before coding** → `audit-driven-pre-coding-gate.md`
- **...add CSV columns to a log writer (fprintf-style)** → `calibration-log-column-registry.md` (pick Variant A=fprintf-direct OR Variant B=snprintf-to-buffer based on writer characteristics)
- **...add a post-load init/load step that runs at boot + backtest + hot-swap** → `postloadsetup-registry-pattern.md` (registry walk by single helper; prevents Class 18 mirror gap at N call sites)
- **...add fields to a cross-thread snapshot struct (PerCoreSnap-style)** → `per-snapshot-cluster-layout-pattern.md` (cluster by concern with alignas(64); cache-line span budget)
- **...add a SIMD-vectorized kernel that must produce bytewise-identical output to scalar** → `avx512-byte-determinism-pattern.md` (8 rules + SHA-256 cross-binary lock test pattern)
- **...add running statistics over a fixed window (correlation, variance, IC, turnover)** → `sliding-window-online-statistics-pattern.md` (sum-of-squares fixed-window form + drop-oldest math + bounded-stability argument)
- **...add a math kernel on the slow/hot path** → `branchless-math-kernel-pattern.md` (constant-iter inner reductions + pre-zero invariants; no if guards inside reductions; IEEE-754 x-0=x exact for bytewise-equivalence)
- **...add a struct that will be compared bytewise (memcmp / SHA-256 / wire format)** → `struct-padding-determinism-pattern.md` (explicit `_padding = 0` fields for all implicit padding gaps; eliminates UB padding bytes structurally)
- **...add a new boolean cfg field that has 2+ siblings in the same family** → `cfg-flag-eligibility-criteria.md` "Cohort audit when new field has siblings" section (run framework on cohort, not just new field)
- **...codify a new architectural pattern that emerged from a sprint** → `pattern-codification-lifecycle.md` (7-stage lifecycle: audit → DESIGN_SPEC → first reference → cohort migration → CLAUDE.md item → tooling enforcement → wider audit)
- **...add a PRNG to randomized code (Monte Carlo, Bayesian sampling, training-time shuffling)** → `prng-choice-for-replay-determinism.md` (simple algorithm + small state for cross-binary replay; `std::normal_distribution` is a landmine — use own Box-Muller)
- **...call an I/O primitive from a logic-only header without breaking the contract** → `template-deferred-dependency-injection.md` (take callable as template parameter; caller injects via lambda)
- **...extract canonical stamp-emit / production-assembly logic shared by 2+ callers** → `orchestration-helper-with-pod-args-pattern.md` (POD args struct with default member init + helper wraps AUTOPOPULATE + manual per-call population + external call; closes Class 18 mirror at production-caller level)
- **...safely swap state under concurrent readers (model hot-swap, cfg deploy, key rotation)** → `shadow-load-state-transition-pattern.md` (allocate-load-validate-atomic_exchange-Free-old; no torn moment → no revert needed; pre-swap untouched on any failure)
- **...add a mode-specific cfg default flip that honors operator overrides** → `post-parse-normalize-with-explicit-key-bitmap-pattern.md` (bitmap of "operator set this key" + post-parse normalize pass; no magic sentinels; explicit overrides always respected)

These are extracted from v5.14.8 + v5.14.9 + v5.14.10 + v5.14.11 + v5.15 sprint work. Future sprints add more as they solve new problems.

## Going-forward

When a session solves a non-trivial design problem:
1. Capture in postmortem doc DURING the work (mid-session, low-cost)
2. After the ship lands, extract a DESIGN_SPECS doc from the postmortem
3. Cross-link from postmortem → DESIGN_SPEC + from DESIGN_SPEC → first-application commit/tag

Example flow: v5.14.8.A.merged ships → postmortem captures the design pivots → extract `x-macro-registry-with-presence-dispatch.md` referencing the merged ship's commits.

## Cross-references

- `DOCS/EASY_ADDITIONS_INVARIANTS.md` (engine repo) — companion: registry pattern audited categories table; this directory holds the FULL design rationale per pattern.
- `DOCS/RECURRING_BUG_PATTERNS.md` — bug-class catalog. DESIGN_SPECS often correspond to "we extinguished class N via pattern X" entries.
- `DOCS/TECH_DEBT.md` — deferral ledger. DESIGN_SPECS often unblock TECH_DEBT items.
- `CLAUDE.local.md` going-forward rules — high-level discipline rules; DESIGN_SPECS are the concrete how-to backing them.
