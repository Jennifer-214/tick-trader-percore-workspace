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

## Tag schema (added v5.15.5.F.4d planning 2026-05-14)

Each pattern can be tagged on 6 dimensions to enable `/precoding-audit-gate` Stage 1 auto-derivation, discoverability filters, and codification-lifecycle visibility:

| Dimension | Values | Use |
|---|---|---|
| **Surface** | hot-path / slow-path / boot / parser / GUI / wire-format / drainer / cross-thread / training / backtest | Where the pattern applies |
| **Concern** | latency / determinism / structural-fix / failure-observability / operator-UX / maintainability / framework-discipline | What problem class the pattern serves |
| **Bug-class closed** | Class 11 / 14 / 18 / 19 / 20 / 21 / 23 (per `DOCS/RECURRING_BUG_PATTERNS.md`) | Which RECURRING_BUG_PATTERNS class this pattern extinguishes |
| **Hard invariant served** | H1-H18 (per `DOCS/DESIGN_PHILOSOPHY.md` § 3) | Which hard invariant this pattern enables |
| **Lifecycle stage** | Stage 1 (audit) / 2 (DRAFT) / 3 (first ref) / 4 (cohort) / 5 (CLAUDE.md item) / 6 (tooling) / 7 (wider audit) | Per `pattern-codification-lifecycle.md` |
| **Application count** | 1 / 2-3 / 3+ | Maturity indicator |

Tagged format example (compact 1-line):
```
**Tags:** structural-fix, wire-format, registry-driven; closes Class 18 + Class 21; serves H9 + H17; Stage 4 (cohort migration); 3 applications
```

**Tagging discipline:** new patterns get tagged at DESIGN_SPEC draft (Stage 2). Existing untagged patterns are tagged retroactively as time allows — see TECH_DEBT entry for codebase-wide tagging sweep (added 2026-05-14). Tags enable `/precoding-audit-gate` to auto-derive focus by matching plan keywords to spec tags.

---

## Catalog (v5.14.4 + v5.14.8 + v5.14.9 + v5.14.10 + v5.14.11 + v5.15.5 deliverables — 57+ patterns)

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
| `type-trait-dispatch-via-tt-namespace.md` | `tt::<verb>_field<T>(T& dst, ...)` with destination-by-reference + type-family static_assert + if-constexpr branches per trait. 3-barrier structural fix (no void*+offset API + X-macro extractor chokepoint + compile-time type guard) closes Class 23 (type-erased reinterpret_cast dispatch) | ACTIVE (v5.14.8.A.merged precedent at `tt::stamp_parse_field<T>`; codified v5.15.5.F.4b at `tt::cfg_parse_field<T>`) |
| `multi-state-dispatch-with-per-state-update-metadata.md` | Specialization of x-macro-registry-with-presence-dispatch for enums where each state has asymmetric dispatch behavior across multiple axes. Metadata columns per row declare row-local behavior; dispatch masks auto-compute via X-macro reduction; adding a state = 1 row addition. Closes Class 18 (mirror) + Class 19 (enum naming) + Class 24 (capability-cfg surface mismatch) at the dispatch site. First canonical application: FOREACH_BANDIT_ALGORITHM 5-state ghost-training expansion (.F.4c.2). | **NEW (v5.15.5.F.4c.2)** DRAFT v1.0 (pending ship; Stage 2 → 3 at first reference) — structural-fix, registry-driven, framework-discipline; closes Class 18+19+24; serves H14; Stage 2 (DRAFT); 0 applications until .F.4c.2 |
| `per-instance-registry-pattern.md` | Generalized framework for registries that instantiate N times across an instance axis (per-core, per-symbol, per-strategy, per-horizon, per-regime). X-macro registry declares rows once; framework auto-generates per-instance struct shape + descriptor array + bitmap masks + render tables. Eliminates "global default + per-instance override" anti-pattern. First canonical application: per-core cfg split at .F.4c.3. | **NEW (v5.15.5.F.4c.3)** DRAFT v1.0 — structural-fix, framework-discipline, registry-driven; closes Class 24; serves H14 + future H-codifications for per-instance discipline; Stage 2 (DRAFT); 0 applications until .F.4c.3 |
| `cfg-scope-discipline.md` | Decision discipline for choosing scope (GLOBAL / PER_CORE / future axes) when adding a new cfg field. Codifies the "could two cores reasonably want different values?" decision question + 4 named anti-patterns (global-default-with-override FORBIDDEN, per-instance fields in global "for convenience", mixing scopes in same field family, backward-compat shim re-introducing override). Closes Class 24 (capability-cfg surface mismatch) at the architectural-decision level. | **NEW (v5.15.5.F.4c.3)** DRAFT v1.0 — discipline, registry-driven, decision-framework; closes Class 24 structurally; Stage 2 (DRAFT); 0 applications until .F.4c.3 |
| `multi-action-registry-walker-family.md` | FOREACH_REGISTRY_ACTION roster of N walker actions (parse/save/render/stamp/drift) × M registries via parameterized templates. Adding a new axis = N new instantiations (mechanical); adding a new action = 1 new walker template (one-time then reused). Eliminates N × M manual walker bodies → N + M mechanical. First canonical application: 5 actions × 2 cfg registries at .F.4c.3. | **NEW (v5.15.5.F.4c.3)** DRAFT v1.0 — structural-fix, framework-discipline, registry-driven; closes Class 18 (walker mirror) + Class 21 (parallel walkers); Stage 2 (DRAFT); 0 applications until .F.4c.3 |
| `cfg-section-parser-state-machine.md` | INI-style `[<axis> <instance>]` cfg parser state machine for per-instance registries. Lines before any section parse against global; lines inside `[core N]` parse against per-instance registry. Unknown keys produce explicit ERRORS with migration hints (no silent fallback). Reusable across all per-instance axes — adding a new axis = 1 new section-header recognizer entry. First canonical application: `[core N]` parser at .F.4c.3. | **NEW (v5.15.5.F.4c.3)** DRAFT v1.0 — framework-discipline, parser-state, discoverability; closes Class 24 at cfg-load surface; Stage 2 (DRAFT); 0 applications until .F.4c.3 |

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
| `audit-driven-pre-coding-gate.md` | Multi-audit pattern + compaction-handoff verification + MID-sprint audit guidance + `/blindspot-scan` IMPLEMENTATION-DETAIL layer (added v5.15.5.F.4d.1.B.3 per meta-discipline M4) | ACTIVE (v5.14.8 + .9 update + 2026-05-18 M4 extension) |
| `implementation-layer-blindspot-taxonomy.md` | 12-category implementation-detail blind-spot taxonomy (B1-B12 — type-change cascades / field-name collisions / transitional state / surface G applicability / compile-time scaling / STORAGE_T coverage / include cycles / TYPE-SENSITIVE consumer classification / unverified claim chain / struct layout / if-constexpr context / row-order parity). SHAPE audits answer "is design right?"; IMPLEMENTATION-DETAIL answers "will code compile/run without surprise?". Fired by `/blindspot-scan` skill. Sister to `audit-driven-pre-coding-gate.md` as the IMPLEMENTATION-DETAIL layer; codified per `DESIGN_PHILOSOPHY.md` § 11.5 meta-discipline M4. | **NEW (v5.15.5.F.4d.1.B.3)** Stage 2 DRAFT v1.0 — meta-discipline, audit-layer; first canonical application at `.B.3` Step 1.6.3 pre-coding (12 pillars confirmed; no NEW pillars surfaced — inflection reached at first fire) |
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
| `registry-bitmap-set-discipline.md` | Anti-pattern recognition + structural fix templates for registry-bitmap pairs where SET sites are missing or bypassed. Two shapes: (A) data write without companion BITMAP_SET, (B) SET chokepoint bypassed by alternate loader path. 3 fix templates (AUTOPOPULATE / single chokepoint / accessor wrapper) + 3 `/dod-audit` detection signatures. | **NEW (v5.15.5.F.3)** ACTIVE (2 canonical applications: `arms_with_barriers_mask` Shape A via accessor wrapper; `drift_flags_at_load`→`failure_flags` Shape B via chokepoint extension). → CLAUDE.md item 30 promotion (meets 2+ apps criterion). |

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

### Framework discipline patterns (CLAUDE.md item 31 + DESIGN_PHILOSOPHY § 1.5)

These are meta-patterns codified at v5.15.5.F.4d planning — frameworks that other patterns compose into. Each documents a framework that future-cohort migrations reuse 1-row mechanically.

| Doc | Pattern | Status |
|---|---|---|
| `decision-time-data-binding-pattern.md` | The principle that per-instance cfg values bind at decision time and flow forward with the in-flight object (Order/Position/Event/TradeEvent), NOT in subsystem state. First line of defense: pre-resolve onto in-flight object. Second line (fallback): registry-driven per-instance cache (`FOREACH_<SUBSYS>_CFG_CACHE`). Codifies the framework-selection sub-principle (registries optimize for ADDING; principle+sweep optimizes for ELIMINATING) — first canonical "registry was wrong; principle is right" application. Closes Class 27 (scalar cfg-mirror flattens per-instance distinction). CI Check 7 + `/accounting-audit` skill + `/registry-fit-audit` skill enforce. ALSO a branchless win (Pattern 4 in branchless-dispatch-discipline.md): pre-resolution eliminates per-fill cmov on cfg-derived dispatch. | **NEW (v5.15.5.F.4c.3 WIP2d-1.B.0c)** DRAFT v1.0 — structural-fix, framework-selection, decision-framework, branchless; closes Class 27; serves H4 (accounting integrity) + H6 (cache discipline); Stage 2 (DRAFT); 0 applications until WIP2d-1.B.1 (Order `effective_fee_rate`) + WIP2d-1.B.1.b cohort sweep |
| `branchless-dispatch-discipline.md` | Branchless dispatch discipline for SP/HP data-dependent code. Codifies 4 patterns: (1) fn pointer table for single-enum dispatch; (2) 2D state×type dispatch table (HandleFill canonical application — collapses dedup + type dispatch into one branchless lookup); (3) mask-select for binary cheap-both-sides; (4) pre-resolution at decision time via in-flight object (composes with decision-time-data-binding). Decision matrix + real-world mispredict cost (30-100ns, not textbook 5-15ns). Closes Class 28 (branchy SP/HP dispatch when branchless feasible). Established after hand-wave audit caught "branch is fine because predictor handles it" framing applied to drainer per-fill dispatch — that's throughput thinking applied to a determinism-prioritizing system. | **NEW (v5.15.5.F.4c.3 WIP2d-1.B.0d)** DRAFT v1.0 — structural-fix, latency, drainer, hot-path, slow-path, branchless, framework-discipline; closes Class 28; serves H7 + H8; Stage 2 (DRAFT); 0 applications until B.1 HandleFill refactor |
| `audit-scope-taxonomy.md` | 5-shape scope taxonomy for audit skill invocations: `current` (active edits — fast/low-context default), `wide` (full codebase — HIGH context; quarterly), `scoped <glob>` (file-glob), `module:<name>` (semantic module per MODULE_MAP.md — module-by-module deep audits), `chain:<symbol>` (data-flow trace via /dependency-chain-trace). Replaces coarse "comprehensive vs focused" binary with situational scope spectrum. All audit skill specs reference taxonomy + accept scope as first positional arg. Per-audit scope supported in /precoding-audit-gate audit_set syntax. Established after Caramel call-out that comprehensive sweep eats context fast on large codebases → shallow findings; situational scope gives appropriate depth per pass. | **NEW (v5.15.5.F.4c.3 WIP2d-1.B.0d)** DRAFT v1.0 — discipline, audit, process, framework-discipline, operator-UX; serves audit quality + context-budget management; Stage 2 (DRAFT); 0 applications until skill spec updates land |
| `registry-coverage-ci-check-pattern.md` | CI enforcement of registry ↔ struct consistency at field-add time. Two variants share Python tool template + exemption mechanism: **Shape A** (positive coverage — every struct field matching predicate MUST be in registry, OR explicit-exempt with rationale + migration trigger) and **Shape B** (anti-pattern enforcement — every struct field MUST NOT match forbidden shape, OR explicit-exempt). Retroactively extracted from 3 canonical applications: Check 2 per-core cfg field coverage (Shape A; v5.15.5.F.4c.3) + Check 7 scalar cfg-mirror anti-pattern (Shape B; v5.15.5.F.4c.3 WIP2d-1.B.0c) + Check 8 OmsState per-slot sibling array coverage (Shape A; v5.15.5.F.4c.4 NEW). Closes 5 bug classes (Class 18 + Class 19 + Class 21 + Class 27 + Class 30) at the structural field-add-discipline layer. Per-variant Stage tracking: Shape A Stage 3 ACTIVE (2 canonicals); Shape B Stage 2 DRAFT (1 canonical) — Shape B variant-level promotion to Stage 3 awaits 2nd canonical. Canonical example of `pattern-codification-lifecycle.md`'s "retroactive extraction + umbrella unification at 3rd canonical" lifecycle variant. | **NEW (v5.15.5.F.4c.4)** Stage 3 ACTIVE — structural-fix, framework-discipline, ci-tooling, registry-driven; closes Class 18 + 19 + 21 + 27 + 30 at field-add discipline layer; serves H15 (sister discipline); Stage 3 ACTIVE (3 canonical apps at extraction; per-variant Stage tracking) |

| Doc | Pattern | Status | Tags |
|---|---|---|---|
| `metadata-bit-driven-derived-filter-framework.md` | Generic framework for declaring derived filters over a parent registry (e.g., FOREACH_CFG_FIELD) via metadata bit. 3 variants: GUI-only / wire-format / wire-format-two-source. Composes with Layer 5b lock + AUTOPOPULATE + bitmap-bool emit_source dispatch. First canonical application: STAMP_BOUND_CFG_DERIVED at .F.4d. | **Stage 3 ACTIVE v1.0 (landed v5.15.5.F.4d ship close 2026-05-16)** | structural-fix, wire-format, registry-driven; closes Class 21 at derived-filter surface; serves H9 + H16; Stage 3 ACTIVE (1 canonical application: STAMP_BOUND_CFG_DERIVED bandit/thompson cohort + retroactive `.A.7` cohort + bandit_blend_ratio + 5-6 other inference_cfg fields) |
| `meta-registry-pattern-for-codebase-registry-discipline.md` | Codebase-wide registry-of-registries discipline. `FOREACH_REGISTRY` with LEVEL/PARENT columns; CI cross-checks every X-macro registry has a row. Closes "added registry but forgot to document" class structurally. | **Stage 3 ACTIVE v1.0 (1st canonical landed v5.15.5.F.4c.3 WIP2d-0.B; 2nd canonical + codebase-wide topology v5.15.5.F.4d 2026-05-16)** | structural-fix, framework-discipline, discoverability; closes Class 18 at meta-layer; serves H15 + H19; Stage 3 ACTIVE (2 canonical applications: FOREACH_PER_CORE_DOMAIN_BITMAP at .F.4c.3 + FOREACH_REGISTRY codebase-wide at .F.4d) |
| `sidecar-override-pattern-for-registry-auto-flows.md` | Sidecar override table for registries with standard-case auto-flow + custom-semantics overrides. Replaces wide-variant duality with single auto-flow path + small sparse sidecar indexed by parent's FIELD_IDX. CI cross-check enforces relationship. First canonical: FOREACH_DRIFT_OVERRIDE at .F.4d (replaces FOREACH_CFG_DRIFT_CHECK wide variant). | **Stage 3 ACTIVE v1.0 (landed v5.15.5.F.4d ship close 2026-05-16)** | structural-fix, registry-driven, framework-discipline; closes Class 21 at auto-flow-with-overrides surface; serves H18; Stage 3 ACTIVE (1 canonical application: FOREACH_DRIFT_OVERRIDE 5-row XGBoost cohort with split sidecars per registry scope) |
| `framework-composition-overview.md` | Visualizes how multiple frameworks compose for cfg infra at .F.4d (universal cfg registry + tt:: dispatch + derived-filter framework + sidecar override + meta-registry + X-macro struct gen). Cold-pickup map. | **Stage 3 ACTIVE v1.0 (landed v5.15.5.F.4d ship close 2026-05-16)** | framework-discipline, discoverability; serves H15-H19; Stage 3 ACTIVE (1 composition application: cfg infrastructure at .F.4d) |
| `type-erased-per-core-resource-handle-pattern.md` | Cross-layer state references via void* field + cast at consumer site (where layer-Y typed headers are in scope). Two variants based on parent struct topology: **Variant A** (single void* on per-core context — canonical `ctx.ensemble_handle`) vs **Variant B** (per-core void* array indexed by core_id on engine-wide singleton state — canonical `oms.ezoo_refs[core_id]` + `oms.core_cfg_refs[core_id]`). § F architectural-correction lesson codified: verify parent struct's ownership topology (per-core vs engine-wide) BEFORE writing sidecar examples. Closes ad-hoc cross-layer crossings class structurally; serves H1 (no virtual dispatch) + H6 (cluster placement) + H17 (cfg struct independence). | **NEW (v5.15.5.F.4d.1 planning 2026-05-16)** Stage 2 DRAFT v1.0 (3 canonical applications observed at `.F.4d` ship close: `ctx.ensemble_handle` pre-existing + `oms.ezoo_refs` + `oms.core_cfg_refs` NEW) | structural-fix, framework-discipline, cross-layer-isolation, cluster-placement; closes ad-hoc-cross-layer-crossings class structurally; serves H1 + H6 + H17; Stage 2 (DRAFT); 3 applications |

**Status note (post-.F.4d):** stamp-vs-runtime-drift-detection-registry.md wide variant gets DEPRECATED for cfg-drift surface (superseded by sidecar pattern). Narrow variant stays — different surface; not over cfg. See TECH_DEBT-059.

**~72 patterns total** (57 catalog + **4 Thread A framework specs Stage 3 ACTIVE at v5.15.5.F.4d 2026-05-16** — metadata-bit-driven-derived-filter-framework + meta-registry-pattern-for-codebase-registry-discipline + sidecar-override-pattern-for-registry-auto-flows + framework-composition-overview + 1 multi-state-dispatch-with-per-state-update-metadata Stage 2→3 first canonical at .F.4d + 4 NEW DRAFT pending .F.4c.3 + 1 retroactive extraction `registry-coverage-ci-check-pattern.md` Stage 3 ACTIVE shipped 2026-05-16 + 1 multi-bit-state-encoding-pattern INVARIANT promotion at .F.4d with 5 canonical applications + **1 NEW Stage 2 DRAFT `type-erased-per-core-resource-handle-pattern.md` at v5.15.5.F.4d.1 planning 2026-05-16** — 3 canonical applications at `.F.4d` ship close codified: `ctx.ensemble_handle` Variant A pre-existing + `oms.ezoo_refs[core_id]` + `oms.core_cfg_refs[core_id]` Variant B NEW). Adding new patterns: write the doc, add a row above with tags, cross-link from related docs. (Process meta-tip: follow `pattern-codification-lifecycle.md` — the meta-pattern that captures HOW to fully codify a new architectural discipline end-to-end.)

## Quick discovery — "I need to..."

- **...add a cfg flag (boolean toggle)** → `cfg-flag-eligibility-criteria.md` (decide eligibility) → `heterogeneous-registry-pattern.md` (pick domain) → `registry-tuple-as-single-source-of-truth.md` (5-col tuple)
- **...add a compute mode chosen by enum** → `curve-registry-pattern.md`
- **...add an algorithm enum with per-state asymmetric behavior** (e.g., "state X updates posterior A but not B; state Y updates B; state Z updates both") → `multi-state-dispatch-with-per-state-update-metadata.md`
- **...replace multiple booleans with a bitmap** → `bitmap-flag-api.md` (which VARIANT?) → variant-specific doc:
  - Engine cfg domain → `heterogeneous-registry-pattern.md`
  - Per-core boolean → `partner-core-bitmap-pattern.md`
  - Function-local summary → `transient-aggregation-bitmap-pattern.md`
  - Registry has_flags → `x-macro-registry-with-presence-dispatch.md`
- **...add per-core override to a bitmap field** → `per-bit-per-core-override-pattern.md`
- **...stamp-bind a registry-derived field** → `wire-format-byte-preservation-discipline.md` (HMAC byte-equivalence) + `x-macro-registry-with-presence-dispatch.md` (emit_source column)
- **...avoid forgetting to populate a field at a production caller** → `autopopulate-pattern-for-production-caller-class.md` OR `autopopulate-from-arity-macro-family.md` (depending on caller shape)
- **...decide between structural fix vs direct patch** → `structural-fix-preferred-decision-framework.md`
- **...add a CI check enforcing registry coverage or anti-pattern enforcement** → `registry-coverage-ci-check-pattern.md` (Shape A positive coverage OR Shape B anti-pattern enforcement; sister to `tools/check_per_core_registry_integrity.py` template; 3 canonical applications at extraction time)
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
- **...build a typed-field dispatcher over a registry (parser/save/render/drift-check)** → `type-trait-dispatch-via-tt-namespace.md` (3-barrier structural fix: no void*+offset API + X-macro extractor chokepoint + compile-time type guard; closes Class 23 type-erased reinterpret_cast anti-pattern; CLAUDE.md item 23)

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
