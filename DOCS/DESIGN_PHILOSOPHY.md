# DESIGN_PHILOSOPHY.md

**Workspace-private.** The narrative + WHY companion to `CLAUDE.md`'s
operational orientation. Read this when:
- Cold-pickup of an unfamiliar surface (which family of principles applies?)
- Designing a non-trivial change (which discipline tier am I choosing into?)
- New contributor onboarding (where does the codebase's mental model live?)
- Making a design trade-off (which family's rules dominate?)

`CLAUDE.md` (always-loaded) gives the orientation + hard invariants;
`DESIGN_SPECS/README.md` (catalog) gives the pattern reference;
`DOCS/RECURRING_BUG_PATTERNS.md` gives the failure-mode catalog.
**This doc gives the WHY** — the mental model that makes the patterns
make sense.

---

## How to read this doc

Every principle is tagged with a discipline tier:

| Tier | Meaning | Override path |
|---|---|---|
| **HARD** | NEVER break. Architectural invariant that defines what this codebase IS. | None — if you'd break it, you're building a different codebase |
| **STRONG** | Apply unless specifically justified. Default for the surface. | Justify in code comments + commit message; document the override in TECH_DEBT.md or CLAUDE.local.md |
| **SOFT** | Do when reasonable. Improves quality but doesn't redefine the architecture. | Drop when a specific reason makes it costly; no formal justification needed |
| **PROCESS** | Gate or decision framework. Tells you when to apply other principles. | The framework IS the override mechanism |

Each section ends with **Cross-references** linking to canonical sources
(CLAUDE.md item N, DESIGN_SPECS path, RECURRING_BUG_PATTERNS class).
Those are the source-of-truth; this doc is the synthesis.

---

## 0. Prime directive — correctness-first (safety-critical grade) [HARD]

**This stance sits ABOVE the priority gradient in § 1.** Before "latency vs determinism vs maintainability," before any pattern or tier, there is one rule: **this is capital-bearing HFT, held to the discipline of safety-critical software — avionics, NASA flight software, fly-by-wire — NOT "move fast and break things."**

**Correctness and planning beat speed, every time, and the trade is not close:**
- A wrong-but-fast answer on money / determinism / accounting code is a *loss of capital or a corrupted persisted invariant*, not a defect you patch next sprint. There is no "ship it and iterate" on the path that moves real money.
- **Planning IS the work** (§ 11; `feedback_plan_right_not_fast`). The hard part is deciding *rightly*, not *quickly*; indecisiveness while planning is a feature, not a delay.
- **Thoroughness fires BY DEFAULT** (`feedback_never_skip_thoroughness_unless_explicit`). Reviews, audits, verification are not optional accelerable steps — skipping one is how a silent error reaches capital. Skip is operator-explicit only, never agent-judgment.
- **When execution FLAILS** — repeated failed attempts, thrashing, a tail of ever-smaller fixes — STOP, slow down, re-plan, ask. Flailing fast is still flailing.

**Why HARD, not aspirational — the cost asymmetry IS the argument.** The downside of being slow is bounded (time). The downside of being wrong is unbounded (capital; a corrupted invariant; a Knight-Capital reactivation). When the downside is unbounded you do not optimize the bounded cost. This is *why* the codebase carries the apparatus it does — the determinism net, the audit gates, the Hard Invariants, the guard layer are the mechanical expression of "correctness is not negotiable." They are load-bearing, not ceremony.

**How to apply:** default to the deliberate, planned, verified path; never trade correctness for velocity; surface decisions and ask rather than rush past them. This directive is FORMALIZED into the reusable `workspace-template` so every project in the ecosystem inherits it — correctness-first is the house style, not a per-project choice.

**Cross-references:** `CLAUDE.md` Prime-directive callout (the always-loaded headline that guarantees this is never skipped) · § 1 (the priority order this sits above) · § 11 + § 11.5 (audit-driven process discipline) · memories `user_correctness_first_not_ship_fast` / `feedback_plan_right_not_fast` / `feedback_never_skip_thoroughness_unless_explicit` / `feedback_evaluate_options_on_robustness_latency_design_not_time`.

---

## 1. What this codebase optimizes for (the foundational frame)

A single-symbol HFT trading engine that:
- Hits sub-microsecond p99 on the hot path (40-400ns for `ExecutionCore_Tick`)
- Gives DETERMINISTIC outputs across runs, binaries, and locales
- Surfaces operational visibility (failure modes, drift, observability)
- Stays MAINTAINABLE under feature pressure (drift classes structurally extinct)
- Trades operator-edit ergonomics off branchlessly (settings tab + tooltips matter)

Everything in this doc is in service of those four. When two principles
conflict, the priority order is:

1. **Latency** (hot path budget — never give it up)
2. **Determinism** (cross-run, cross-binary, cross-locale; load-bearing for replay + train/serve parity)
3. **Maintainability** (structural fix preferred when a bug class can recur)
4. **Operator UX** (comment-preserving cfg writes, tooltip preservation, no surprising behavior changes)

If you're trading off principles, name which one wins + why.

### The cost framework (CLAUDE.md item 28; the lens for all decisions)

At ~3 GHz x86 with AVX-512:

| Operation | Cost | Multiplier vs cycle |
|---|---|---|
| 1 CPU cycle | ~0.3 ns | 1× |
| L1 hit | ~1 ns | ~3× |
| L2 hit | ~4 ns | ~13× |
| L3 hit | ~13 ns | ~43× |
| **DRAM (L1 miss; cold cache)** | **~100 ns** | **~300×** |
| Branch mispredict (textbook single stall) | ~3-5 ns | ~10-15× |
| **Branch mispredict (real-world HFT pipelined)** | **~30-100 ns** | **~100-300×** |
| Indirect call (fn pointer, L1-hot target) | ~3-5 ns deterministic | ~10-15× |
| Locked atomic / mutex acquire | ~20-50 ns + scheduling | ~100×+ |
| Syscall | ~200-500 ns | ~700×+ |
| Page fault | ~10-100 μs | ~30,000×+ |
| Mutex contention (kernel wait) | up to ms | ~3,000,000×+ |

**Branch mispredict cost — real-world vs textbook (updated 2026-05-15 at v5.15.5.F.4c.3 WIP2d-1.B.0d after a hand-wave audit caught this gap):**

The textbook "5-15ns" mispredict cost is the SINGLE-STALL number. On modern pipelined x86 CPUs (14-20 stage pipelines) executing dependent operations, mispredict cost commonly measures 30-100ns in real HFT codebases because:
- Pipeline flush discards speculative work downstream of the mispredict
- Dependent operations on the wrong-side branch cascade
- Wrong-side branch target may not be in L1i cache (instruction-cache miss on recovery)
- Compounds especially badly under instruction-level parallelism (HFT code is ILP-heavy)

For decisions about branchless-vs-branchy SP/HP dispatch, use the **30-100ns** number, not 5-15ns. The textbook number is misleading for this codebase's measurement context.

Decision rules that fall out of this:
- **Approach A (+N cycles, -M cache misses) beats Approach B (-N cycles, +M misses) when M > N/300.** For N=10 cycles, 1 saved miss = ~30× net win.
- **Branchless A (+N cycles) beats branchy B (1 branch, M% mispredict) when M > N/100** (using real-world 30ns mispredict cost; was N/16 under textbook 5ns number). For data-dependent branches commonly mispredicting 30-50%, branchless ALWAYS wins.
- **Branchless ALWAYS wins on p99** (deterministic cost vs branch's variable mispredict tail). For a system that values determinism over throughput (this codebase), p99 consistency dominates average throughput.
- **H20 INVARIANT: Branchless preferred for SP/HP data-dependent dispatch EVEN WHEN NOMINALLY SLOWER.** Mask code / fn pointer tables / cmov / mask-select / dummy-redirect approaches can be optimized later (better instruction selection at next compiler upgrade, vectorization opportunity, prefetch hints, hot-cold split). Branch mispredicts CANNOT be optimized away — they're a hardware cost. The choice isn't "minimize average cycles"; it's "minimize variance to make the system deterministic." A branchless dispatch that costs +5ns deterministic is better than a branch that costs 0-100ns variable, because the +5ns can be reduced over time while the 100ns mispredict tail can't. Codified as H20 in CLAUDE.md. Closes Class 28 (branchy SP/HP dispatch when branchless feasible).
- **NEVER syscall on hot path.** A single syscall costs more than the full per-tick budget.
- **NEVER allow page faults on critical pages.** Lock memory at boot via `mlockall(MCL_CURRENT | MCL_FUTURE)`.
- **NEVER acquire mutexes on hot/slow path.** The unbounded tail under contention nukes any latency budget.
- **NEVER default to "branch is fine because predictor handles it" for SP/HP data-dependent dispatch.** That's a throughput frame applied to a determinism-prioritizing system. Per H20: default to branchless via fn pointer table / 2D state-table / mask-select / pre-resolution per `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md`.

**Cross-references:** CLAUDE.md item 28 (cycles vs cache), `DESIGN_SPECS/refactor-patterns/latency-vs-cache-decision-framework.md`, `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md` (NEW at .F.4c.3 WIP2d-1.B.0d).

---

## 1.5 Framework discipline (the meta-principle behind structural fixes)

This codebase deliberately invests upfront complexity in FRAMEWORKS — X-macro
registries, AUTOPOPULATE companions, type-trait dispatch (`tt::` namespace),
derived-filter macros, sidecar override tables, meta-registries — when the
trade-off math favors framework over ad-hoc:

1. **Pattern recurrence is foreseeable** (≥2 future applications projected)
2. **Bug class can recur** (sites can drift apart over time)
3. **Framework cost ≤ projected savings across N applications** (upfront LOC + maintenance < per-instance ad-hoc cost × N)

The trade-off: framework code is HARDER TO READ at first encounter than
ad-hoc per-instance code. The PAYOFF is that future additions become
1-row mechanical changes; the framework's API encodes the discipline so
contributors can't drift from it.

### Why this matters in this codebase specifically

Recurring drift classes have cost 1-3h per occurrence on average, and we've
seen 3-4× recurrence on classes that "weren't going to come back" — Class 14
plan-API-drift (5× recurrence), Class 18 mirror-incomplete (4× recurrence
before `EnsembleModelZoo_PostLoadSetup` structurally closed it), Class 21
parallel descriptors (closed structurally at v5.15.5.F.4 via single
`CfgFieldDescriptor` + `lives_in_struct` discriminator). Each framework that
closes a bug class structurally saves multiples of its upfront cost.

### Complexity budget calculation

Before investing in a framework, compute the breakeven:
- **Upfront cost:** framework code LOC + DESIGN_SPEC drafting + audit/test infrastructure
- **Per-application savings:** avoided per-instance LOC × projected N applications
- **Breakeven N ≈ upfront cost / per-app savings**

For the v5.15.5.F.4 cfg-registry work: upfront ~1500 LOC; per-app savings
50-200 LOC × ~20 known future applications (cfg fields + derived filters +
drift overrides + new registries) = breakeven within the v5.15.6 sprint;
lifetime payoff 4-10×.

### When NOT to invest in a framework

- Single known application + no clear recurrence signal (one-shot bug fix)
- Pattern variance too high (no shared shape to extract)
- Framework cost ≥ projected savings × N (negative ROI)
- Premature: less than 3 codebase applications + no DESIGN_SPEC yet
  (per `pattern-codification-lifecycle.md` Stage 2 requirement)

### Composition reduces total complexity

Multiple frameworks often COMPOSE — e.g., the v5.15.5.F.4d ship composes:
- Universal cfg registry (`FOREACH_CFG_FIELD`)
- `tt::` type-trait dispatch (parse / save / render trio)
- Derived-filter framework (`FOREACH_DERIVED_FILTER` over CFG_FIELD)
- Sidecar override pattern (over CFG_FIELD)
- Meta-registry (`FOREACH_REGISTRY` managing all the above)
- X-macro struct generation (Cfg struct fields from `FOREACH_CFG_FIELD`)

The composition is intentional. Each framework handles ONE concern;
together they extinguish 5 bug classes (Class 14, 18, 19, 21, 23). Without
the framework discipline, each concern would be solved independently with
parallel infrastructure — more total complexity, less coverage.

### Framework-selection criteria (added v5.15.5.F.4c.3 WIP2d-1.B.0c)

> **Registries optimize for ADDING MORE of a pattern. When the right answer is to STOP HAVING the pattern, a principle + audit + delete is better than a registry.**

A sharpening of the framework-discipline meta-principle. Not every pattern that repeats N times warrants a registry. The decision matrix:

| Pattern characteristic | Reach for |
|---|---|
| N items share structure + multi-site addition is recurring + N is GROWING (and SHOULD grow) | **Registry** (X-macro / FOREACH_X) |
| Pattern should NOT exist or should be ELIMINATED | **Principle + audit + delete + CI check** |
| Mix: some instances genuine + most should be eliminated | **Principle PRIMARY + registry as fallback** for the rare genuine instances |

Why this matters: a registry mechanicalizes ADDITIONS of the pattern. If we name the pattern + make adding it easy, we make eliminating it harder — registry rows accumulate, become load-bearing, become "the way we do this," entrench. When the pattern should shrink (Class 27 cfg-mirror caches that should be replaced by pre-resolution onto in-flight objects), a registry framework actively works against closure.

The principle-first answer:
1. **Name the principle** in a DESIGN_SPEC (one canonical doc)
2. **Sweep the codebase** for existing instances (one audit)
3. **Delete + migrate** each instance to the principle-aligned shape (per-site)
4. **CI check** enforces that new instances can't be added (one tool extension)
5. **Registry as fallback** only for the edge cases where the principle genuinely doesn't apply (rare; near-vestigial)

First canonical case: Class 27 (scalar cfg-mirror on subsystem state). Initial impulse was `FOREACH_SUBSYSTEM_CFG_CACHE` registry to mechanicalize per-core cache addition. Sharpening pushback: most instances should be ELIMINATED via pre-resolve onto in-flight Order/Position/Event, not mechanicalized. Registry kept as second-line fallback for the genuinely-no-in-flight-object cases (likely 0-1 actual instances). Codified in `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md`.

The discipline contrast:
- Framework-discipline meta-principle (this section above): "invest in framework when recurrence is foreseeable"
- Framework-selection sub-principle (this addition): "but FIRST ask whether the recurrence is itself the bug — if so, principle + sweep + delete + CI beats framework"

Both apply. The trade-off question is: WILL this pattern accumulate value (more instances over time = more leverage from framework), OR will this pattern accumulate technical debt (more instances over time = more sites to eventually clean up)? If accumulate-debt, don't optimize for additions — optimize for elimination.

### Cross-references

- § 7 Structural-fix family — the bug-class-recurrence motivation
- § 11 Process discipline — "don't measure structural work by LOC" + decision discipline application
- `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` — the 7-stage codification process
- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md` — direct-patch vs structural-fix decision
- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` — first canonical "registry was wrong; principle is right" application; closes Class 27
- CLAUDE.md item 19 — structural fix preferred (codified principle)
- CLAUDE.md item 31 — framework-driven extensibility (codifies THIS section)

---

## 2. Hard invariants (NEVER break)

These define what this codebase IS. Breaking any of them = building a
different codebase.

| # | Rule | Tier | Source |
|---|---|---|---|
| H1 | No `malloc` / `new` / `std::vector` / `std::string` on hot/slow/drainer/parser paths | HARD | STRATEGY_AND_CODING_RULES Rule 1 |
| H2 | No `virtual` functions / `std::function` / `std::shared_ptr` anywhere | HARD | STRATEGY_AND_CODING_RULES Rule 2 |
| H3 | No `std::mutex` / `condition_variable` / `sleep_for` / `pthread_rwlock` anywhere | HARD | STRATEGY_AND_CODING_RULES Rule 3 |
| H4 | `FPN_Binary<F=64>` for accounting math; NEVER `float`/`double` on accounting paths (display-only OK) | HARD | CLAUDE.md item 4 (per-node data plane); STRATEGY_AND_CODING_RULES |
| H5 | No `atof` / `strstr` / scalar JSON in parser inner loops; use `simdjson` / `fast_float` / `parse_double_fast` | HARD | STRATEGY_AND_CODING_RULES Rule 6 |
| H6 | Cross-thread fields get `alignas(64)` to isolate cache lines; no false sharing | HARD | STRATEGY_AND_CODING_RULES Rule 7; CLAUDE.md item 12 |
| H7 | Hot path is BRANCHLESS for data-dependent dispatch (mask compute, cmov; per Rule 8 of latency-path-discipline) | HARD | latency-path-discipline.md Rule 8 |
| H8 | Hot path p99 ≤500ns; slow path p99 ≤100μs (regression = ship blocker) | HARD | CLAUDE.md item 17 |
| H9 | Wire-format byte preservation for HMAC-signed bodies (stamps, snapshots, RunHistory); locale pinning at emit | HARD | DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md |
| H10 | AVX-512 SIMD kernels MUST have a scalar fallback producing BYTEWISE IDENTICAL output | HARD | CLAUDE.md item 25; DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md |
| H11 | Math kernels on slow/hot path are CONSTANT-ITER + branchless within the inner reduction | HARD | CLAUDE.md item 26; DESIGN_SPECS/refactor-patterns/branchless-math-kernel-pattern.md |
| H12 | Structs used in byte-equivalence contexts (memcmp / SHA-256 / wire format) have EXPLICIT zero-init padding fields | HARD | CLAUDE.md item 27; DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md |
| H13 | Type-erased `*reinterpret_cast<T*>((char*)cfg + offset) = v` style dispatch is FORBIDDEN — use `tt::<verb>_field<T>` with T deduced (Class 23 3-barrier fix) | HARD | CLAUDE.md item 23; DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md; RECURRING_BUG_PATTERNS Class 23 |
| H14 | NO C++ bitfield syntax (`name : N`) anywhere — multi-bit state encoding uses manual `SHIFT_*`/`MASK_*` constants + `MBS_*`/`BITMAP_*` branchless accessors over `uint{8,16,32,64}_t` storage; layout/signedness/packing-order are implementation-defined (conflicts with H6/H9/H10/H12) | HARD | DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md + DESIGN_SPECS/framework-patterns/bitmap-flag-api.md; CLAUDE.md item 30 |
| **H15** | Every X-macro registry in the codebase MUST have a row in `FOREACH_REGISTRY` meta-registry. Adding a new registry without enrollment fails CI Check `test_meta_registry_coverage`. Closes meta-Class-18 (added registry but forgot to document). | **HARD (codified `.F.4d` 2026-05-16)** | DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md; CLAUDE.md item 31 |
| **H16** | Every `CfgFieldDescriptor::MetadataFlag` bit MUST have a derived filter row in `FOREACH_DERIVED_FILTER` OR a documented exemption with rationale. CI Check `test_metadata_bit_to_derived_filter_coverage` enforces. | **HARD (codified `.F.4d` 2026-05-16)** | DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md |
| **H17** | `ControllerConfig<F>` cfg struct fields auto-generated from `FOREACH_CFG_FIELD` via X-macro; NO manual cfg field declarations. `PerCoreCfg<F>` body = X-macro only (CI Check 2 since `.F.4c`). Runtime/derived state stays manual but documented in `MANUAL_FIELDS_INVENTORY.md` with rationale. CI build-fails on drift via `tools/check_per_core_registry_integrity.py`. | **HARD (codified `.F.4d` 2026-05-16)** | DESIGN_SPECS/framework-patterns/manual-fields-inventory-pattern.md; DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md § Reverse-drift |
| **H18** | Custom-semantics for registry auto-flows via SIDECAR OVERRIDE pattern (sparse `FOREACH_<DOMAIN>_OVERRIDE` indexed by parent's `FIELD_IDX`); NEVER parallel wide-variant registries (Class 21 anti-pattern at auto-flow surface). STRONG initially; HARD after 2nd cohort application per `pattern-codification-lifecycle.md`. | **STRONG → HARD (codified `.F.4d` 2026-05-16; 1st canonical: XGBoost drift override 5-row cohort in `FOREACH_DRIFT_OVERRIDE`)** | DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md |
| **H19** | Every `FOREACH_REGISTRY` row with LEVEL > 0 (any non-root registry) MUST declare a valid PARENT. Topology discipline; CI Check `test_meta_registry_topology` enforces (per the enforced `MetaRegistry.hpp` numbering: Level 0 = codebase-wide root `FOREACH_REGISTRY` / `ROOT_NONE`; Level 1 = direct registry / PARENT `FOREACH_REGISTRY`; Level 2 = child of a Level-1 meta-registry; numbering corrected to match code `.E.0.10` 2026-06-11). | **HARD (codified `.F.4d` 2026-05-16)** | DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md |
| **H20** | Branchless preferred for SP/HP data-dependent dispatch EVEN WHEN NOMINALLY SLOWER. Mask code / fn pointer tables / cmov / mask-select / dummy-redirect can be optimized later (better instruction selection, vectorization, prefetch hints); branch mispredicts CANNOT (30-100ns real-world per § 4 framework). For determinism-prioritizing system (HFT premise), variance from branches is the bigger cost. Sister to H7 (hot-path strict); H20 generalizes to SP + drainer + producer-fan-out. Exceptions per decision matrix in `branchless-dispatch-discipline.md`. | **HARD (codified `.F.4c.3` WIP2d-1.B.0d 2026-05-15; ratified into hard-invariants table at `.F.4d` 2026-05-16)** | DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md; CLAUDE.md item 18 + 28; RECURRING_BUG_PATTERNS Class 28 |

**Family grouping notes:** H1-H6 are operational baseline (no malloc / no virtual / no mutex / no float on accounting / no slow parser / cache discipline). H7-H8 are latency budget. H9-H12 are determinism guards (wire-format / SIMD parity / math kernels / struct padding). H13-H14 are type-system + bit-encoding discipline (Class 23 / Class 20 / Class 14 prevention). **H15-H20 close the framework consolidation cycle (codified `.F.4d` 2026-05-16)** — codebase-wide registry topology (H15 + H19) + metadata-bit derived filter coverage (H16) + cfg struct auto-generation (H17) + sidecar override for custom semantics (H18) + branchless dispatch generalized to SP/drainer/producer (H20).

These are the floor. Everything below builds on them.

---

## 3. Data-oriented design family

**WHY this family exists.** The hot path's per-tick budget (≤500ns) is a
tiny fraction of a single DRAM round-trip (~100ns). The hot path can
afford a handful of cache hits + some L2 fetches; it CANNOT afford any
DRAM misses. So everything the hot path touches per tick must already
be in L1/L2. This drives every memory layout decision.

The slow path budget (≤100μs) is looser but compounds tightly under
load. Same discipline, slightly relaxed (predictable branches OK,
larger working sets OK, but no syscalls / no allocations / no mutex).

### Principles in this family

**STRONG: Bitmap-pack flags when ≥3 booleans coexist in a struct.**
- Memory: 16 flags in 2 bytes vs 16 bytes byte-per-flag
- Atomic multi-flag updates: 1 instruction (`__atomic_fetch_or`) vs N stores
- Branchless multi-flag check: 1 cycle (mask AND) vs N branches
- Cache: flag-set for entire core fits one word
- Use `BITMAP_*` macros from `MemHeaders/BitmapMacros.hpp` (CLAUDE.md item 20)
- Per-record bit-packing (one bit per record across many records) is the EXCEPTION — usually loses to per-record cache locality

**STRONG: Bit-pack small-state fields (1-3 bits each) into a single byte/word — NOT adjacent `uint8_t` fields.**
- Anti-pattern: `struct { uint8_t severity; uint8_t category; uint8_t mode; uint8_t _pad; }` — wastes 3 bytes; loses cache-line packing efficiency; later widening (uint8 → uint16) is schema bend
- Pattern: pack states as bits in a single `uint8_t` / `uint16_t` with named bit positions + branchless accessor helpers (per `bitmap-flag-api.md`)
- Apply DURING struct design — retrofitting later is schema bend (consumer macros need updates)
- For ≥4 distinct values per field: use multi-bit slots per `multi-bit-state-encoding-pattern.md` (CLAUDE.md item 30)
- Detection: any new struct with ≥2 adjacent `uint8_t state_<N>` fields where each represents an enum of ≤4 values → consolidation candidate. `/dod-audit` Stage 6 detection signature.
- Canonical applications: `DriftOverride` flags + `RegistryRosterEntry.flags` + `ManualFieldInventoryEntry.kind` (all v5.15.5.F.4d ship)

**STRONG: Cluster fields by access pattern, not declaration convention.**
- Hot READS go in line 0 (first cache line of struct)
- Hot WRITES go in their own cluster (avoid invalidating reads)
- Cross-thread fields (atomic flags, snapshot pointers) get `alignas(64)` on their OWN line
- Cold init-time fields go in the cold cluster (last lines of struct)
- See `DESIGN_SPECS/data-disciplines/cache-layout-discipline-for-hot-side-structs.md` + `decision-first-cluster-layout-pattern.md`

**STRONG: Branchless mask compute for data-dependent dispatch on hot path.**
- Pattern: `result = (cond_mask & if_true_value) | (~cond_mask & if_false_value)`
- See latency-path-discipline.md Rule 8 + CLAUDE.md item 18
- Predictable branches (cfg flags set at boot) can stay branchy — branch predictor handles them at ~0ns

**STRONG: Use `__builtin_expect` for predicted-rare branches; `__attribute__((cold))` for cold helpers.**
- Pattern: `if (__builtin_expect(can_enter | can_exit, 0)) { /* event push */ }` — predictor learns "not taken" within ~1k ticks; steady-state cost ~0ns
- See latency-path-discipline.md Rule 4

**SOFT: Use compile-time elision (`template <bool> + if constexpr`) for default-off features.**
- Disabled state compiles to ZERO instructions
- Used for `LAT_ENABLED`, debug instrumentation, etc.
- See CLAUDE.md item 18(a) + cfg-flag-eligibility-criteria.md (when to use template-elision vs cfg-flag bitmap)

**SOFT: AVX-512-friendly layouts** — if a state array is 8×64-bit (e.g., bandit weights), it fits one __m512d register. Plan accordingly. See CLAUDE.md item 25 + STRATEGY_AND_CODING_RULES Rule 5.

### What NOT to do

- ❌ Per-record bit-packing across millions of records (cache locality + indirection cost > memory savings)
- ❌ Mutex protection of bitmap reads (bitmap reads are inherently lock-free)
- ❌ Bitmap field without overflow guard — `static_assert(FOREACH_X_COUNT_VALUE <= sizeof(type) * 8)` is mandatory (Class 20; bitmap-overflow-protection-discipline.md)

**Cross-references:** CLAUDE.md items 1, 12, 20, 28; DESIGN_SPECS/framework-patterns/bitmap-flag-api.md, cache-layout-discipline-for-hot-side-structs.md, decision-first-cluster-layout-pattern.md, per-snapshot-cluster-layout-pattern.md, multi-bit-state-encoding-pattern.md, latency-vs-cache-decision-framework.md; RECURRING_BUG_PATTERNS Class 20 (bitmap overflow).

---

## 4. Latency cost framework family

**WHY.** Hot path is per-tick (~1μs intervals); slow path is per-cycle
(~100 ticks × 1μs ≈ 100μs intervals). Drainer is per-fill. Each path
has a budget that's a few orders of magnitude tighter than naive code
would produce. Decisions about WHAT TO ADD to a path must be reasoned
against the path's budget.

### Principles in this family

**HARD: Hot path lat budget ≤500ns p99; slow path ≤100μs p99.**
- `tools/calls_graph_diff.sh` + bench gate verify before merge
- Replay-determinism test at `tests/controller_test.cpp:10251` is bytewise lock

**STRONG: Latency-additions to hot/slow/drainer paths get tracked.**
- Document in `DOCS/HOT_PATH_CHANGELOG.md` with cost estimate (ns) + branchless analysis + cache impact + FUTURE optimization note
- Run `/latency-track` skill after sprints touching audited surfaces
- See CLAUDE.md item 17

**STRONG: Slow-path additions follow specific reduction patterns.**
- Default-OFF safety gates → compile-time elision via `template <bool ENABLED> + if constexpr` (zero cost when disabled)
- ALWAYS-ON gates → branchless mask compute on cached state
- Runtime-toggleable + load-bearing → cache an "any_gate_enabled" mask at slow-path entry; later checks are AND-mask compares
- Avoid sprinkling cfg-flag checks through deep functions — hoist to slow-path top + pass a small struct of resolved predicates
- Mask compute > switch on enum: for "any of these states?" queries, single mask AND beats switch (branchless, predictable, single uop)
- See CLAUDE.md item 18

**STRONG: Reuse-audit before adding new code.**
- Before writing a new function or duplicating state access, scan the codebase + adjacent in-flight plans for: existing functions with overlapping responsibility, atomic loads / `clock_gettime` / cfg accesses that could be SHARED across consumers in the same slow-path cycle, state fields that could be reused, conversion paths (FPN_Binary ↔ double, system_clock ↔ rdtsc) that already exist
- Hot-path/producer paths get branchless mask compute on shared data; slow-path can use predictable branches with shared reads
- Run `/merge-scan` periodically; ship-time check in `/readiness` (item 18) catches per-plan misses
- See CLAUDE.md item 16

**SOFT: AOT-compile ML inference when latency tightens.** XGBoost C API is ~1-5μs per inference; Treelite-style transpilation can drop this to <100ns with AVX-512 parallel tree evaluation. Path documented in LATENCY_OPTIMIZATION_AUDIT.md Part 4.3.

### What NOT to do

- ❌ Adding latency-impacting code without a HOT_PATH_CHANGELOG entry
- ❌ Sleeping on hot/slow path (any `sleep_for` is a syscall + scheduler dependency)
- ❌ Synchronous I/O on drainer thread (cascading stalls; OrderEventLog uses async logger thread)

**Cross-references:** CLAUDE.md items 16, 17, 18, 28; STRATEGY_AND_CODING_RULES Rules 1-9; LATENCY_OPTIMIZATION_AUDIT.md (13 parts; private); plans/_cross-cutting/2026-05-06-latency-path-discipline.md (8 rules + anti-pattern history).

---

## 5. Determinism family

**WHY.** This codebase has THREE determinism contracts:
1. **Replay-determinism** — same input ticks → same output trades (operator-side audit + bug investigation)
2. **Train-serve parity** — features computed at training time = features at inference time (model accuracy depends on it)
3. **Cross-binary determinism** — paper-trade run + live-trade run with same cfg + same ticks → bytewise-identical decisions (HMAC chains for stamp verification)

Breaking ANY of these fails silently and accumulates over time. The
discipline that prevents this is COMPREHENSIVE — every byte that
participates in a deterministic computation must come from a
deterministic source.

### Principles in this family

**HARD: FPN_Binary<F=64> for accounting math.** Floating-point arithmetic is non-associative + locale-dependent + has subnormals. Fixed-point is integer math + bytewise-deterministic across compilers + binaries.

**HARD: Wire-format byte preservation for HMAC-signed bodies.**
- Locale pinning at emit (`uselocale(newlocale(LC_NUMERIC_MASK, "C", 0))`) — per-thread, lock-free
- Per-entry format strings locked in registry's `fmt` column (registry-driven emit ALWAYS uses this format)
- Layer 5b canonical body snapshot hash test prevents accidental row reorder
- Surface G `has_*` forward-compat flags preserve legacy stamps without `MODEL_FORMAT_VERSION` bumps
- Round-trip HMAC test against committed v(N-1) stamp fixture
- See `wire-format-byte-preservation-discipline.md`

**HARD: Parity-tested-by-construction.** Every train→serve handoff surface (features, labels, scaler, cfg, stamp body, threading, build flags) gains protection by adding a registry/binding/snapshot, NOT ad-hoc tests.
- Pattern: `FEATURE_REGISTRY_HASH` + scaler `feature_registry_hash` + stamp body `has_*` forward-compat flags + snapshot tests for compute-fn bodies
- Prefer Surface G stamp body extension (`has_<field>` flag with `model_format_version` UNCHANGED) over `MODEL_FORMAT_VERSION` bumps
- Run `/parity-check` before declaring an ML-side sprint complete
- See CLAUDE.md item 15; DOCS/PARITY_LIFECYCLE.md, PARITY_VERIFICATION_CHECKLIST.md

**HARD: NaN-free feature pack.** `Features_PackAll` is the SINGLE chokepoint where every feature value is validated. Two-layer guard: `FPN_IsValidFinite` (catches FPN_Binary saturation past 1e15) + IEEE-754 `isnan/isinf` post float-cast. Returns `-1` sentinel on failure; caller skips prediction cycle + increments `nan_feature_events_total`. Adding a new feature does NOT add a separate validation site — pack-time is the load-bearing surface; downstream code trusts the pack output.

**HARD: AVX-512 SIMD kernels have scalar fallback producing BYTEWISE IDENTICAL output.**
- Every AVX-512 kernel has `#if defined(__AVX512F__)` else baseline
- 7-8 rules per `avx512-byte-determinism-pattern.md` + SHA-256 lock test template
- Cross-binary replay determinism is load-bearing — paper-trade audits + HMAC chains + cache-warm replay tests all break under 1-ULP divergence
- See CLAUDE.md item 25

**HARD: Math kernels on slow/hot path are CONSTANT-ITER + branchless within reductions.**
- Inner reductions iterate a compile-time-constant count (e.g., `MAX_RIDGE_MODELS=8`, NOT runtime `n`)
- NO `if` guards inside reduction loops
- Zero-contribution iterations are bytewise no-ops via IEEE-754 invariants (`x*0=0`, `x-0=x` exact)
- Algorithmic state pre-zero (per-row, per-solve, per-cycle) establishes the zero-invariant
- See CLAUDE.md item 26; `branchless-math-kernel-pattern.md`

**HARD: Structs used in byte-equivalence contexts have EXPLICIT zero-init padding.**
- Any struct compared via `memcmp` / SHA-256 / wire format / HMAC input declares ALL padding bytes via `int<N>_t _padding<N> = 0;` default-init fields
- Implicit C/C++ struct padding is UB unless explicitly initialized
- Pattern documented in `struct-padding-determinism-pattern.md`
- See CLAUDE.md item 27

**STRONG: PRNG choice for replay-determinism + persistence.**
- When replay-determinism + persistence are both load-bearing, prefer SIMPLE algorithm with small state (splitmix64; 1 uint64) over HIGH-QUALITY algorithm with large state (mt19937_64; 312 words)
- `std::normal_distribution` is UNSAFE for cross-binary replay (libstdc++-implementation-defined output)
- Pattern: simple algorithm + small state + Box-Muller helper + seed-scrambling helper + SHA-256-locked sample-trace test
- See `prng-choice-for-replay-determinism.md` (CLAUDE.md item 24's first reference application)

**STRONG: Sliding-window incremental statistics over a fixed window.**
- For statistics (mean, variance, covariance, correlation) over the K most recent records, maintain running sums via subtract-then-add at sample eviction: `sum += x_new - x_oldest`
- Eliminates periodic-reset code smell common in vanilla-Welford-with-drift-mitigation
- Bounds drift by window contents (each record's contribution added once + subtracted once across its K-record lifetime)
- See CLAUDE.md item 29; `sliding-window-online-statistics-pattern.md`

### What NOT to do

- ❌ `std::normal_distribution` anywhere replay-determinism matters (libstdc++ implementation-defined)
- ❌ `atof` in parsers (locale-dependent; produces "0,55" → 0.0 under de_DE)
- ❌ Variable-iteration math kernels on slow path (drift class; replace with constant-iter + pre-zero)
- ❌ Wide refactors that change struct field offsets in HMAC-signed bodies (Layer 5b hash test fires; investigate before resetting hash)

**Cross-references:** CLAUDE.md items 14, 15, 24, 25, 26, 27, 29; DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md, avx512-byte-determinism-pattern.md, branchless-math-kernel-pattern.md, struct-padding-determinism-pattern.md, prng-choice-for-replay-determinism.md, sliding-window-online-statistics-pattern.md; PARITY_LIFECYCLE.md, PARITY_VERIFICATION_CHECKLIST.md.

---

## 6. Concurrency family

**WHY.** No mutexes anywhere — period. Every cross-thread interaction
must be lock-free, wait-free, or designed for eventual consistency
with explicit staleness tolerance. The reason: a single mutex acquisition
under contention can stall the hot path for milliseconds (kernel wait
+ scheduler), which is 10,000× the per-tick budget.

### Principles in this family

**HARD: All thread sync via lock-free primitives only.**
- **SPSC/MPSC rings** (`MemHeaders/SPSCRing.hpp`) for producer/consumer messaging
- **ParameterSlot seqlock** (`CoreFrameworks/ExecutionCore.hpp`) for slow→hot push of GateParameters (1 reader, 1 writer; ~6ns full read; ~1ns cached-seq check)
- **`alignas(64) atomic<T>`** for single-byte cross-thread flags (e.g., `permission`, `kill_tripped`)
- See STRATEGY_AND_CODING_RULES Rule 3 + latency-path-discipline.md Rule 7

**HARD: Per-node data plane.** Each engine owns its rolling/regime/flow state. No shared state between cores on the slow path. Producer thread fans Binance ticks across SPSC rings to per-node consumers. See CLAUDE.md item 4.

**HARD: OMS submit funneling.** The drainer thread is the SOLE caller of `OrderManager_Submit`. Any other code path that would submit goes through the drainer's MPSC submit queue. Single-writer = lock-free; multiple-writer = MPSC ring. See CLAUDE.md item 5.

**STRONG: SPSC ring failure → counter, not retry.**
- `SPSCRing_TryPush` returns false when full
- Increment a failure counter; preserve state so next tick retries naturally
- NEVER busy-wait or block on push
- See latency-path-discipline.md Rule 3

**STRONG: Cross-thread fields get `alignas(64)` to avoid false sharing.**
- Hot READS go in own cache line cluster
- Cross-thread atomic writes go in own `alignas(64)` block
- Verify with grep: any `__atomic_load_n` / `std::atomic<T>` field should have `alignas(64)` or be in a struct that does
- Periodically run `perf c2c` to verify no false sharing under load
- See latency-path-discipline.md Rule 1

**STRONG: Smart CPU pinning** — slow-paths avoid SMT siblings of busy threads via `/sys` topology read at boot. Reduces tail variance from cross-SMT cache eviction. See CLAUDE.md item 11.

**SOFT: Memory ordering** — default `__ATOMIC_RELAXED` for observability flags (no happens-before constraint with other data). Upgrade to `release-acquire` when the bitmap synchronizes OTHER data (e.g., result-ready flag releasing a result struct).

**PROCESS: Failure-path observability via counter increment + slow-path scrape.**
- When a hot-path operation can fail (ring full, NaN feature, etc.), increment a counter; do NOT log
- Slow path scrapes counter periodically + logs delta if non-zero, OR surfaces via TUISnapshot
- Counters are lock-free single-writer (the failing thread's own); read by slow path with `__atomic_load_n(..., ATOMIC_RELAXED)`
- See latency-path-discipline.md Rule 2

### What NOT to do

- ❌ `std::mutex` / `condition_variable` / `pthread_rwlock` anywhere
- ❌ `std::shared_mutex` (atomics + potential blocking)
- ❌ Busy-wait on push (couples hot-path latency to drainer responsiveness)
- ❌ `fprintf` / `printf` / `write()` from hot/slow path (libc stdio mutex; cascading stall under degraded conditions)
- ❌ Synchronous I/O on drainer thread (use async logger thread per OrderEventLog pattern)

**Cross-references:** CLAUDE.md items 4, 5, 11; STRATEGY_AND_CODING_RULES Rule 3; latency-path-discipline.md Rules 2, 3, 7; LATENCY_OPTIMIZATION_AUDIT.md Part 6 (system & OS jitter).

---

## 7. Structural-fix family (the most load-bearing meta-pattern)

**WHY this family exists.** The codebase has a long history of bug
classes that recur when the same pattern at multiple sites drifts
apart — e.g., parser site forgets to add the new cfg field that the
struct site added; mirror code paths drift apart over time; production-
caller forgets the populator step. Direct-patching each instance is
recurring debt; structural fix (compile-time enforcement, X-macro
registry, single chokepoint) eliminates the bug CLASS — not just the
instance. The decision framework: if a bug class has recurred 3+
times, structural fix is the correct path even at higher upfront cost. **The deliverable is the GUARD, not the patch** — a guard is permanent leverage (it protects the whole class against every future regression, forever, with no one thinking about it); over a capital-bearing system's lifetime the enforcement layer compounds harder than any single feature, so weigh a guard against its lifetime of silent saves, not its one-time cost (memory `feedback_guards_compound_enforcement_is_leverage`).

### Principles in this family

**STRONG: X-macro registry is the standard pattern for multi-site additions.**
- Any category where "adding the next instance" requires touching ≥2 code sites must use a `FOREACH_<CATEGORY>(X)` registry
- Audited categories: strategies, ML features, SHALT codes, halt_reason codes, regimes, stateful GUI panels, backtest metrics, stamp-bound cfg fields, architectural stamp-body model-const fields, failure-mode observability fields
- See CLAUDE.md item 13; `EASY_ADDITIONS_INVARIANTS.md`; `x-macro-registry-with-presence-dispatch.md`

**STRONG: Structural fix preferred when bug class can recur.**
- When facing a bug whose ROOT CAUSE is "same pattern at multiple sites drifted apart" (Class 18 mirror, parallel paths), prefer compile-time enforcement (X-macro registry, helper extraction with all callers unified) over direct patch
- Reason: 4× recurrence of v5.9.5b production-caller class before STAMP_CFG_AUTOPOPULATE extinguished it. Each occurrence cost 1-3h debug. Structural fix would have cost ~3h once.
- See CLAUDE.md item 19; `structural-fix-preferred-decision-framework.md`

**STRONG: AUTOPOPULATE companion macro for X-macro registries with production-caller side effects.**
- When a registry has multiple production callers that ASSEMBLE the registry-driven struct, define an AUTOPOPULATE companion macro that auto-generates per-field populator code via X-macro expansion
- Production callers replace ~50-100 LOC of manual `inf.X = src.X; inf.has_X = 1;` blocks with one `STAMP_X_AUTOPOPULATE(target, source)` call
- Closes production-caller field-population class structurally — adding a new registry field becomes 1 row; AUTOPOPULATE picks it up at next compile; forgetting becomes impossible
- See CLAUDE.md item 21; `autopopulate-pattern-for-production-caller-class.md`

**STRONG: PRE/POST registry split for canonical-emit-order preservation.**
- When a registry's entries must emit at positions INTERLEAVED with a SISTER registry's entries (HMAC-locked wire format), split FOREACH into `_PRE_CFG` and `_POST_CFG` halves
- Same tuple shape across halves; struct generation + AUTOPOPULATE walk the union; emit walks halves separately
- See CLAUDE.md item 22; `pre-post-cfg-registry-split-for-emit-order-preservation.md`

**STRONG: Type-trait dispatch via templated helpers (`tt::` namespace).**
- C++17 `if constexpr` discards branches at TEMPLATE INSTANTIATION
- In **non-template macro context** (X-macro expansion in regular function body), all branches must be SYNTACTICALLY VALID for ALL types
- Fix: extract type dispatch into a templated helper function that's instantiated per-T
- Required ANY TIME a non-template context uses if-constexpr with branches that have different syntax requirements per type (typical: `char[N]` strncpy vs scalar cast)
- This pattern is the foundation of the **3-barrier structural fix for Class 23** (type-erased reinterpret_cast dispatch): API surface has no void*+offset entry + X-macro extractor passes field by reference + type-family static_assert at each tt:: function
- See CLAUDE.md item 23; `type-trait-dispatch-via-tt-namespace.md`; RECURRING_BUG_PATTERNS Class 23

**STRONG: Registry-bitmap SET discipline.**
- When a registry of flag bits (FOREACH_*) is paired with a bitmap field + downstream consumers (BITMAP_IS_SET, branchless mask compute, `/readiness` checks), the SET sites are SEPARATE actions from the data writes — easy to forget
- Two anti-pattern shapes: (A) data write without companion BITMAP_SET, (B) SET chokepoint bypassed by alternate loader path
- Structural fix templates (preference order): AUTOPOPULATE companion → single chokepoint function → accessor wrapper
- See CLAUDE.md item 30; `registry-bitmap-set-discipline.md`

**HARD: Dead-code elimination + identifier retirement (the Knight-Capital discipline; H21).**
- Persistence/wire-visible identifiers — snapshot/format VERSION numbers + persisted/logged/wire-emitted enum CODES + persisted bitmap bits + cfg-field name keys — are APPEND-ONLY + IMMUTABLE. Never renumber, value-reuse, or silently drop one: old persisted state, an old wire/HMAC message, or an un-updated node carries the OLD meaning of a reused identifier and silently activates the wrong path. This is the Knight Capital failure mode ($440M / 45 min, 2012 — a dormant "Power Peg" flag reused while its dead code was still compiled in).
- Retire by TOMBSTONE (RESERVED / LEGACY_ / DEPRECATED comment; keep the number), never reassign the slot — new meaning = new identifier. Reconciles with backwards-compat-not-default: delete the dead CODE cleanly, just never recycle the externally-visible SLOT (old state / an un-updated node still references it).
- Remove dead code, don't leave it (prove-then-remove via `/dead-code-trace`; the compiler does NOT warn on unused `inline` helpers — they rot silently). A dead capital-path (strategy/gate/OMS/kill-switch) is removed, never merely `cfg`-disabled.
- Mechanized: `tools/check_identifier_retirement.py` + golden identifier-ledger (pre-commit Check H + `/readiness` Check 46 + `/post-ship-audit` dead-code/identifier sweep). Codifies conventions already in informal use (`BanditAlgorithm` "OPTION C wire-byte preservation"; `RESERVED` bit anchors; `LEGACY_` versions).
- See CLAUDE.md H21; `dead-code-and-identifier-retirement-discipline.md`; RECURRING_BUG_PATTERNS Class 40; § 5 (determinism — the persistence/wire angle).

**PROCESS: Codify design principles in CLAUDE.md as patterns mature.**
- Promote to CLAUDE.md once: ≥2 codebase applications OR DESIGN_SPECS doc exists, AND pattern is broad
- Items 19-30 are the codified history of this lifecycle
- See `pattern-codification-lifecycle.md` (7-stage lifecycle: audit → DESIGN_SPEC → first reference → cohort migration → CLAUDE.md item → tooling enforcement → wider audit)

### What NOT to do

- ❌ Premature abstraction (registry overhead requires ≥3 entries + ≥2 caller sites; CLAUDE.md item 13 threshold)
- ❌ Structural fix for one-off bugs (use direct patch; this framework is for RECURRING classes)
- ❌ Adding to a registry without updating its AUTOPOPULATE companion (silently breaks production callers)
- ❌ Bypassing the X-macro extractor with hand-written if-chains (defeats the structural fix; reintroduces the drift class)

**Cross-references:** CLAUDE.md items 13, 19, 21, 22, 23, 30; DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md, autopopulate-pattern-for-production-caller-class.md, autopopulate-from-arity-macro-family.md, pre-post-cfg-registry-split-for-emit-order-preservation.md, structural-fix-preferred-decision-framework.md, type-trait-dispatch-via-tt-namespace.md, registry-bitmap-set-discipline.md, dead-code-and-identifier-retirement-discipline.md, pattern-codification-lifecycle.md; RECURRING_BUG_PATTERNS Class 11 (extensibility friction), Class 13 (snapshot mirror), Class 18 (mirror-incomplete), Class 23 (type-erased dispatch), Class 40 (reactivatable dead code / repurposed persistence-ID).

---

## 8. Failure observability family

**WHY.** Production HFT systems fail in ways that aren't obvious from
exit codes — silent drift, partial corruption, degraded model accuracy,
subtle timing regressions. The discipline is to make failures VISIBLE
the moment they happen, with enough metadata to diagnose without
re-deriving context.

### Principles in this family

**HARD: NaN-free feature pack with single-chokepoint validation.** See Determinism family above.

**STRONG: Failure modes registry with bit-flag storage.**
- `FOREACH_FAILURE_MODE` registry tracks all observable failure conditions
- BIT_FLAG entries auto-pack into a uint16_t / uint32_t / uint64_t bitmap
- COUNTER_U32 entries track recurring failure rates
- PERCENT_U8 entries track degraded states with severity gradient
- Storage class declared per-entry; AUTOPOPULATE handles dispatch
- See `MemHeaders/FailureModeRegistry.hpp`; CLAUDE.md item 13 (storage class discipline)

**STRONG: Drift detection registries (boot + runtime).**
- `feature_registry_hash` / `label_registry_hash` / `build_flags_hash` compared at model load vs current
- `scaler.feature_registry_hash` vs `handle.feature_registry_hash` cross-check
- `cfg.binding_drift` checks stamp-bound cfg field count + values
- `STAMP_HMAC_NOT_VERIFIED` set when held_out_stamp_secret was empty at load
- `MODEL_AGE_WARN` triggered when training_timestamp_us > model_max_age_hours
- All consolidated into `failure_flags` bitmap on PerCoreSnap → GUI Model Health panel

**STRONG: Per-arm reward observability invariant.**
- Each ensemble arm's prediction is graded INDEPENDENTLY against actual price movement
- Per-arm rewards observable regardless of which arm was selected
- Enables shadow-training (parallel bandit logging without acting), counterfactual evaluation, multi-algorithm A/B testing
- See CLAUDE.md item 24

**SOFT: Audit-driven detection of failure modes.**
- `/dod-audit` Stage 6 detection signatures for each pattern
- `/bug-check` registry-driven scan of `DOCS/RECURRING_BUG_PATTERNS.md`
- Adding a new bug class to RECURRING_BUG_PATTERNS auto-includes it in next /bug-check run

### What NOT to do

- ❌ Silent failure handling (any error returned from a hot-path operation must increment a counter; slow path observes)
- ❌ Mixing failure-flag storage classes in the same word without per-entry storage class declaration
- ❌ Adding a failure mode without paired GUI surface (display ↔ execution invariant; CLAUDE.md item 12)

**Cross-references:** CLAUDE.md items 12, 14, 24; `MemHeaders/FailureModeRegistry.hpp`; DOCS/CLAUDE_INTEGRATION.md (display↔execution invariant adoption pattern); /dod-audit + /bug-check skills.

---

## 9. Architectural primitives family

**WHY.** Beyond the cross-cutting principles above, certain
architectural decisions define the codebase's specific shape. These
aren't general principles; they're CHOICES that, once made, constrain
everything else. Understanding them is required to design new features
that fit the codebase.

### Principles in this family

**HARD: Per-position TP/SL exits on hot path; portfolio management on slow path.** TP/SL evaluation lives in `SG_Evaluate` (hot, branchless). Portfolio sizing, exposure tracking, drawdown checks live in slow path. See CLAUDE.md item 2.

**HARD: Fill consumption every tick.** No unprotected exposure. Even if no events arrive, the drainer drains; even if no fills arrive, the consumer consumes. See CLAUDE.md item 3.

**HARD: OMS submit funneling.** Drainer is sole `OrderManager_Submit` caller. See Concurrency family.

**STRONG: OneCore helpers shared by 3 callers.** Centralized live, per_core_slow live, backtest. Structural train-serve parity by construction — same helper function called from all three contexts means same behavior. See CLAUDE.md item 6.

**STRONG: TUI independent of engine.** Engine runs headless (no rendering on hot path). TUI reads state via double-buffered `TUISnapshot` (with seqlock since v5.11.3). GUI thread / TUI thread runs at ~60 Hz; engine is unaffected. See CLAUDE.md item 8.

**STRONG: Warmup observes market before trading.** Gates on slow-path sample count, not just tick count. Prevents trading during cold-cache cold-state startup. See CLAUDE.md item 7.

**STRONG: Partial exits dispatcher post-cap.** Strategies stay leg-A-only (single-position evaluators); the dispatcher decides if a second leg (partial exit) gets an entry. Hot path branch-gates leg B. See CLAUDE.md item 10.

**SOFT: No API key for market data WS.** Public Binance trade stream + depth WS endpoint. Avoids latency cost of authentication round-trips on data path. Order WS uses authenticated REST endpoint. See CLAUDE.md item 9.

### What NOT to do

- ❌ Adding an exit mode to slow path (exits are HOT-path; slow path only sets parameters)
- ❌ Bypassing OMS submit funnel (drainer must be the only caller)
- ❌ Coupling TUI to engine state directly (always go through TUISnapshot)
- ❌ Trading during warmup (warmup gates are NEVER short-circuited)

**Cross-references:** CLAUDE.md items 2, 3, 6, 7, 8, 9, 10, 11; /strategy-template skill (canonical strategy lifecycle); CoreFrameworks/EngineSharded.hpp (architectural anchor); plans/v5.15-live-readiness/MASTER.md (current sprint context).

---

## 10. Operator UX family

**WHY.** This codebase has ONE operator (currently Caramel; future
contributors will inherit). The operator-side surfaces — cfg files,
GUI tooltips, logs, paper-test workflow — are LOAD-BEARING for
correct operation. Breaking operator UX silently (e.g., dropping a
tooltip, changing default behavior, removing comment-preservation in
cfg writes) is a real bug, even if no test catches it.

### Principles in this family

**STRONG: Comment-preserving cfg writes.** `cfg_write_field(path, key, value)` at `GUI/SettingsPanel.hpp:472` does per-field text-splice that PRESERVES operator comments + line ordering in the cfg file. NEVER replace this with a wholesale `Cfg_Save(FILE*)` that rewrites the file from scratch.

**STRONG: Tooltip preservation byte-identical during migrations.**
- Hand-tuned operator prose (multi-line tooltips with examples, fee structure explanations, Discord/Telegram setup notes) MUST be preserved when migrating GUI fields between sources of truth
- Use C++ raw string literals `R"(...)"` or escaped `\n` to keep the bytes identical
- Tooltip changes are an operator-visible behavior change; they require explicit decision, not silent drift

**STRONG: Categorical applicability for cfg field gating in GUI.**
- NEVER hardcode strategy/regime/op-mode names in gating conditions
- Use category bitmaps (`STRAT_CAT_USES_BANDIT`, `OP_MODE_CAT_LIVE`, etc.) so adding a new strategy auto-applies relevant cfg fields
- See `categorical-tag-applicability-pattern.md`; CLAUDE.local.md going-forward rule "Categorical applicability for new cfg fields"

**STRONG: Cross-file cfg surfaces use `lives_in_struct` discriminator.**
- ONE `CfgFieldDescriptor` + `lives_in_struct` enum value; never parallel descriptors per cfg file
- Closes Class 21 (multiple parallel descriptors) drift class
- See `CoreFrameworks/CfgFieldRegistry.hpp`; CLAUDE.md item 21 (closes Class 21 + 23)

**SOFT: Default behavior preservation on version upgrades.**
- New cfg field defaults should match pre-existing behavior when operator hasn't set them
- Surface G `has_*` flags in stamp body preserve forward-compat without `MODEL_FORMAT_VERSION` bumps
- Live mode strict defaults via post-parse normalize pass (changes effective behavior of `model_verify_strict` etc. only when `trading_mode == LIVE` AND operator hasn't explicitly set the override)

**PROCESS: FEATURE_LOOKUP.md auto-write on new operator-visible features.**
- Per CLAUDE.local.md auto-write contract: agent MUST add an entry to `FEATURE_LOOKUP.md` when a new operator-visible feature ships
- Entry includes: what / cfg flags / fallback / where to verify / paper-test sanity / gotchas / related references
- Skip auto-write for: pure refactors, internal helper extraction, bug fixes restoring expected behavior, bytewise-identical perf optimizations

### What NOT to do

- ❌ Wholesale-rewrite of cfg files (loses operator comments + ordering)
- ❌ Tooltip drift during migrations (the operator notices)
- ❌ Hardcoded strategy enum names in gating (breaks when next strategy added)
- ❌ Parallel descriptors per cfg file (Class 21 mirror drift)

**Cross-references:** `categorical-tag-applicability-pattern.md`; `universal-cfg-field-registry-pattern.md` § "Cross-file cfg unification"; CLAUDE.local.md auto-write contracts; `tick-trader-percore-workspace/FEATURE_LOOKUP.md`; RECURRING_BUG_PATTERNS Class 19, 21.

---

## 11. Process discipline family

**WHY.** Multi-day architectural work + sprint-cadence shipping require
process discipline that prevents drift between plan + reality, catches
recurring bug classes pre-coding, and keeps the audit infrastructure
(skills + DESIGN_SPECS + RECURRING_BUG_PATTERNS) in sync with the code.

### Principles in this family

**HARD: Cold-pickup plan completeness — 10 fields.**
- Every plan must specify: branch state, exec-order matches deps, Step-0 first concrete move, function-names cited (verified via grep), file:line refs, stale-claim audit, effort-vs-LOC reconciliation, source-audit references, predecessor + dependent plans, tag + rollback anchors
- Fresh-context coder shouldn't lose hours re-deriving context
- See `/readiness` skill Cold-pickup section + DOCS/CLAUDE_REVIEW.md

**HARD: Verify handoffs against current code.**
- Compaction degrades — handoff prompts may have stale function names, line refs, struct shapes
- ALWAYS re-verify handoff claims via grep before acting
- See memory `feedback_compaction_degrades_treat_handoffs_or_hints.md`

**STRONG: Audit-driven pre-coding gate.**
- HIGH-RISK ships, first pattern applications, or cross-cutting changes get `/parity-check + /trace-deps + /readiness + /merge-scan + /dod-audit` fired in parallel BEFORE coding
- Operator decides whether to fire (NOT auto-triggered)
- Synthesize convergent findings to `plans/plan_checks/<sprint>-<sub-ship>-fresh-audits-synthesis.md`
- THEN consult operator before coding (do NOT auto-proceed even if findings look clear)
- See `audit-driven-pre-coding-gate.md`

**STRONG: After pre-coding audit, ALWAYS consult before coding.**
- Present findings + list potential fixes + iterate with operator
- Do NOT auto-proceed even if findings look clearly addressable
- See memory `feedback_consult_on_audit_findings.md`

**STRONG: Boundary-stable refactors over wide cascades.**
- Default to keeping public types unchanged + isolating new behavior INSIDE
- Reserve cascade for when the boundary type ITSELF is the bug
- Refactor that crosses ≥4 files: stop, propose stable boundary first
- See memory `feedback_reduce_touch_sites.md`

**STRONG: Cohort-audit when new cfg field has 2+ siblings.**
- New boolean cfg field with 2+ semantic siblings (`ridge_*`, `bandit_*`) → audit cohort
- All-eligible: migrate together; mixed eligibility: TECH_DEBT per-sibling
- See `cfg-flag-eligibility-criteria.md` § "Cohort audit"; CLAUDE.local.md going-forward rule

**STRONG: New docs default to private.**
- Docs capturing unshipped direction / optimization findings / operator-edge / private cfgs → `plans/` (workspace, gitignored, date-prefixed)
- Public architectural-only → `DOCS/`
- Auto-private gitignore patterns: `*_AUDIT.md`, `FUTURE_*.md`, `*-design-notes.md`, `*-suggestions.md`, etc.
- See CLAUDE.local.md going-forward rule

**STRONG: Workspace mirror for edge content.**
- `/sync-workspace` skill mirrors plans/ + .claude/skills/ (auto via symlinks); cfg files + .env + *.local.md (explicit copy)
- Run on-demand at end of session / after plan finalized / after skill updated

**SOFT: Suggest mid-sprint audits when work impacts downstream.**
- HIGH-RISK ship just shipped / first pattern application / cross-cutting changes → suggest `/test-strength-audit + /dod-audit + /parity-check` in parallel
- Wait for greenlight; don't auto-trigger
- Skip for routine pattern-application or pure additive work

**PROCESS: Auto-write contracts.**
- When an audit / skill / sub-ship surfaces an item, the agent MUST write the entry to the named ledger
- Surface → Ledger map: parity findings → PARITY_ISSUES.md; deferred items → TECH_DEBT.md; operator-visible features → FEATURE_LOOKUP.md; decoupling positioning → decoupling-roadmap; cohort findings → TECH_DEBT.md; operational landmines → LANDMINES.md
- See CLAUDE.local.md "Auto-write contracts" section

**PROCESS: No defer for effort-avoidance.**
- "Smaller scope" recommendations have been wrong 3/3 times in past sessions vs operator's "do it right now" instinct
- Defer is last-ditch, never an effort-avoidance escape hatch
- See memory `feedback_no_defer_for_effort.md`

**PROCESS: No MVP for plumbing/refactor work.**
- MVP is for genuinely-new features with external dependencies (maker orders w/ orderbook)
- Plumbing/pattern-application work ships the FULL DOCUMENTED DESIGN
- See memory `feedback_no_mvp_for_plumbing_only_for_unknown_unknowns.md`

**PROCESS: Single-cycle exist+good (design once, maintain forever).**
- For foundational / interconnected / determinism-gated infrastructure where the requirement is KNOWN, take a piece exist→good within ONE cycle — don't ship "it exists" and defer "make it good" to a later cycle. Re-traversing capital/determinism-gated code re-opens the whole verification surface (re-prove, re-freeze goldens, re-audit); the cost of getting-it-good-now is far below the re-traversal cost.
- This is NOT the common "make it exist, then make it good" — that advice is for exploratory product code with unknown-unknowns (MVP to discover the requirement). Often there is no exist-vs-good tradeoff at all (the Ship-A branchless ops were value-identical to the saturating ones — "good" fit inside "exists").
- Scope guard: genuine unknown-unknowns still warrant an MVP probe (see "No MVP for plumbing" above).
- See memory `feedback_design_once_maintain_forever.md` + `feedback_no_defer_for_effort.md`

**PROCESS: Don't measure structural work by LOC.**
- For pattern-building / refactor / class-closure work, lead with classes-closed + patterns-codified + future-work-becomes-mechanical
- LOC is incidental (can even be negative)
- See memory `feedback_dont_measure_structural_work_by_loc.md`

### What NOT to do

- ❌ Coding directly off a plan without /readiness verification
- ❌ Auto-proceeding past audit findings without operator consult
- ❌ Wide cascades when boundary-stable refactor would work
- ❌ Premature deferral as effort-avoidance
- ❌ MVP-style ship for refactor work where the design is documented

**Cross-references:** CLAUDE.local.md going-forward rules; memories at `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/`; /readiness, /parity-check, /trace-deps, /merge-scan, /dod-audit, /bug-check, /handoff skills; DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md, structural-fix-preferred-decision-framework.md, pattern-codification-lifecycle.md.

---

## 11.5 Meta-disciplines (when audits surface their own gaps)

The audit-driven pre-coding gate (§ 11) catches plan-vs-code drift, dependency gaps, plan completeness, reuse opportunities, pattern-application gaps. But audits THEMSELVES have gaps — surfaces they don't reach. When iteration count grows with DIMINISHING per-iteration severity, the iteration count IS the signal of an audit METHODOLOGY gap (a META-gap).

This section codifies the meta-disciplines that close audit-methodology gaps as they emerge — and how the discipline catalog evolves over time.

### PROCESS: Iteration spiral signals a meta-gap.

When plan body amendment iterations find smaller-and-smaller findings across 4+ cycles, stop individual-finding-chase. Ask: "what AUDIT METHODOLOGY GAP caused us to keep finding small issues?". Codify the META-gap immediately; apply a comprehensive sweep with new discipline; verify inflection (next iteration finds nothing material).

Common meta-gap shapes (catalog grows as new gaps surface):

| Meta-discipline | Signal | Codification | Closes |
|---|---|---|---|
| **M1 — Sister-registry parity verification** | Plan body references column on sister registry that doesn't exist at HEAD; or sister registry sig migrated but cohort siblings deferred without rationale | `canonical-sister-extension-discipline.md` § Temporal evolution + cohort migration; `/readiness` Check 36; `/trace-deps` cohort-parity amendment | Class 14 sister-registry-shape-drift instance prevention |
| **M2 — Cross-tool emit-site enumeration** | Wire-format-changing plan enumerates engine code but misses cross-process emitters (CLI tools, training scripts, recording tools) | `wire-format-byte-preservation-discipline.md` Layer 7; `/parity-check` Section E amendment; future-oriented-plan-template wire-format section | Wire-format drift across cross-process emit surfaces |
| **M3 — Anti-pattern codification distinguishes legitimate siblings** | New anti-pattern class text would false-positive on legitimate sibling patterns that match the textual shape but are semantically different | `RECURRING_BUG_PATTERNS.md` codification template requires explicit "False-positive surface" subsection | False-positive recurrence reports on legitimate patterns |
| **M4 — Implementation-detail audit layer above SHAPE** | SHAPE audits (parity / trace / readiness / merge / dod) return GREEN-or-YELLOW after 3+ iterations; operator senses unaddressed concerns; type-change cascades / field-name collisions / context-dependent C++ constructs / row-order drift remain unchecked | `implementation-layer-blindspot-taxonomy.md` (12-category taxonomy); `/blindspot-scan` skill (Layer-2 audit); `/readiness` Checks 36-39; `/trace-deps` TYPE-SENSITIVE classification; `/parity-check` claim→evidence + row-order amendments; CI tools `check_field_name_uniqueness.py` + `check_storage_t_coverage.py` | 12 categories of implementation-detail blind spots SHAPE audits miss |
| **M5 — Train-serve execution-layer parity** | Pre-coding audit gate misses train-serve EXECUTION-LAYER parity (boot calls + slow-path-cycle body asymmetry between LIVE and BACKTEST drivers); cfg/stamp/wire-format audits don't cover this layer | `train-serve-execution-layer-parity.md` (Stage 3 first canonical at .B.4 ship close via EngineCommon extract); pre-coding audit gate amendment for HIGH-RISK ships touching `EngineSharded.hpp` boot OR slow-path-cycle | Train-serve execution-layer drift (worked example: 4 CRITs at .B.3 close that 6 audits missed — kill_switch dead 14+ months + Strategy_InitPerCore never called in backtest since v5.4) |
| **M6 — Body-content arg enumeration before helper extract** | Plan body specifies helper SIGNATURE based on PROPOSED structural intent without enumerating ACTUAL body content + per-callee parameter requirements; surfaces as cascading "wait this needs more args" at coding time | `feedback_enumerate_helper_signature_args_before_extract`; `/readiness` Check 33; body-content enumeration CSV artifact at `plan_checks/<date>-<ship>-<helper>-body-content-enumeration.csv` | Helper-extract signature drift at body-content layer (worked examples: BootPerCore v1.6 O1 4→8 args + SlowPathCycleOneCore v1.7.3 N-6 6→9 args) |
| **M7 — Structural enforcement when memory codification proves insufficient** | Memory codification of discipline proves insufficient at next-cycle observation; same bug class recurs DESPITE codified memory at SAME surface in SAME cycle as codification; cognitive-load amplifier present (long files / mechanical amendments / cross-file drift) | `structural-enforcement-when-memory-insufficient.md` (Stage 3 first canonical at .B.4 v1.7.4); 6-stage lifecycle promotion (memory→audit→multi-agent→CI tool→pre-commit hook); `/capture-audit` skill; `tools/check_*.py` + `.git/hooks/pre-commit` | Memory-only-discipline failure modes for cognitive-load-amplifier surfaces (worked example: Class 14 Stage 3 → 6 via B-Plus CI tool after v1.7.3 → v1.7.4 cycle introduced 6 NEW fabrications AFTER M6 codification) |

**Aggregating index (2026-05-29):** M1-M7 above — plus the B14-B19 implementation-blindspot pillars (`implementation-layer-blindspot-taxonomy.md`) and the workspace-hygiene / cascade shapes — are cross-indexed in `DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md`, the **META parallel of `RECURRING_BUG_PATTERNS`** (a greppable catalog of NON-code recurring errors; populated by the `/close-session` harvest; consumed by `/capture-audit` Check 12 + the hardened `/precoding-audit-gate`). The enumerate-set discipline (`feedback_enumerate_set_before_categorical_claim`) is cataloged there as **AR-1** + is the standing **M8-candidate**.

### PROCESS: SHAPE audits answer "is the design right?"; IMPLEMENTATION-DETAIL audits answer "will the code compile and run without surprise rework?"

Both layers needed; neither substitutes for the other. After `/precoding-audit-gate` returns GREEN-or-YELLOW with the SHAPE audit set, fire `/blindspot-scan` if any of: struct-gen migration crosses ≥2 registries / type unification migration / cross-registry consumer / macro hoisting from call site into framework primitive / include surface change / wire-format ordering change / pre-coding audit gate ran 3+ batches with iterative findings.

### PROCESS: Adding a new meta-discipline.

When a meta-gap surfaces:

1. Recognize the iteration-spiral signal (per `feedback_iteration_spiral_signals_audit_meta_gap`)
2. Codify the META-gap as a DESIGN_SPEC body (Stage 2 DRAFT)
3. Amend the relevant audit skill(s) to encode the discipline structurally
4. Add `/readiness` Check (N+1) if plan-time verification is feasible
5. Add a CI tool stub if mechanical detection is feasible
6. Write a feedback memory documenting the trigger + how-to-apply
7. Add the new Mn row to the meta-discipline table above
8. At ship close: promote the DESIGN_SPEC to Stage 3 ACTIVE; the new discipline is now part of the gate

This is the discipline-evolution machinery: the codebase's meta-rules are NOT static; they grow as new audit-methodology gaps surface. Each Mn codification adds a structural guard that future ships inherit mechanically — the discipline encoded in skills + specs + CI rather than in human memory.

### PROCESS: DESIGN_PHILOSOPHY as the master settings portal.

Where to find any principle in force, organized by layer:

| Layer | Source | Read when |
|---|---|---|
| **Hard invariants (H1-H20)** | § 2 of this doc + CLAUDE.md table | Always-loaded; never break |
| **Family principles** | § 3-10 of this doc | Designing a non-trivial change in that family |
| **Process disciplines** | § 11 + § 11.5 of this doc | Planning a ship; recognizing meta-gap; firing audits |
| **Patterns catalog** | `DESIGN_SPECS/README.md` + per-pattern doc | Building a new feature; sister-extension search |
| **Anti-pattern catalog** | `DOCS/RECURRING_BUG_PATTERNS.md` | Pre-coding sweep; codifying new Class |
| **Operator-collaboration rules** | `memory/MEMORY.md` + per-rule body | How Claude should engage with operator on this codebase |
| **Sprint state** | sprint MASTER plan + CLAUDE.local.md "Current sprint state" | Cold-pickup; ship sequencing |
| **Going-forward rule index** | CLAUDE.local.md "Going-forward rules" | Discovering which discipline applies to a trigger |
| **Auto-write contracts** | CLAUDE.local.md "Auto-write contracts" | Determining which ledger an audit finding belongs in |

The portal hierarchy reads top-down:

```
CLAUDE.md                       (orientation; always loaded)
     ↓
DESIGN_PHILOSOPHY.md            (WHY + meta-rules; this doc; read on cold-pickup)
     ↓
DESIGN_SPECS/                   (HOW patterns; 80+ specs; read on-demand per topic)
     ↓
RECURRING_BUG_PATTERNS.md       (anti-patterns; 30+ classes; read for pre-coding sweep)
     ↓
memory/                         (operator-collaboration rules; auto-loaded)
     ↓
CLAUDE.local.md                 (operator overlay + sprint state index; auto-loaded)
```

CLAUDE.md is for ARCHITECTURAL ORIENTATION (what the codebase IS). DESIGN_PHILOSOPHY is for PRINCIPLES (why it is that way + how to extend). DESIGN_SPECS is for PATTERNS (how to apply the principles concretely). RECURRING_BUG_PATTERNS is for ANTI-PATTERNS (what to avoid). Memory is for COLLABORATION (how Claude should engage with this specific operator). CLAUDE.local.md is for INDEX + SPRINT STATE (where to find things + what's currently in flight).

If you can't find the answer at the layer you're looking at, go DOWN the hierarchy. CLAUDE.md → DESIGN_PHILOSOPHY → DESIGN_SPECS is the standard descent.

**Cross-references:**

- `feedback_iteration_spiral_signals_audit_meta_gap` (memory rule; the recognition pattern)
- `feedback_implementation_detail_blindspot_recovery_via_taxonomy` (memory rule; M4 specifically)
- `feedback_audit_canonical_sister_before_new_infra` (memory rule; M1 producer side)
- `feedback_enumerate_consumers_before_registry_row_deletion` (memory rule; M1 consumer side)
- `DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md` (parent pattern for /precoding-audit-gate)
- `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` (M4 codification)
- `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md` (M1 codification)
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` Layer 7 (M2 codification)
- `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` (Stage 2 DRAFT → Stage 3 ACTIVE workflow)

---

## 12. What this codebase EXPLICITLY does NOT optimize for

Every codebase has design choices it says NO to. Naming them keeps focus.

- **Multi-symbol portfolio management.** Single-symbol design. Adding multi-symbol would require fundamental rework of the per-node sharded model + portfolio bitmap + risk allocation. Defer indefinitely.
- **Maker order execution.** No consistent order-book data source today; TECH_DEBT-008 indefinite defer. Engine is taker-side only.
- **Sub-millisecond fill confirmation.** Binance REST round-trip is ~50-200ms; we don't try to beat the network.
- **Multi-tenant operator support.** Single-operator tooling (one paper-test session at a time; one cfg file).
- **GPU-accelerated ML inference.** XGBoost C API + future Treelite AOT path is sufficient; GPU dependency adds deployment friction without proportionate latency win for our model sizes.
- **Cross-platform (Windows, macOS).** Linux-only (`isolcpus`, `nohz_full`, `rcu_nocbs`, `mlockall`, `MAP_HUGETLB`, AVX-512). Windows/macOS deployments would need rework of OS-level tuning.
- **Web frontend / browser GUI.** Native ImGui via SDL2; no HTTP server, no JS frontend. Operator runs locally.
- **Distributed deployment.** Single-process, single-machine. No cross-machine orchestration.
- **Backtest performance optimization (subsecond per-day).** Backtest engine prioritizes train-serve parity over throughput; running multi-day backtests is acceptable.
- **Exotic strategies requiring heavy state (deep RL, full order-book modeling).** Lightweight strategies (regression-driven, ML inference, fixed rules) only. Heavy state breaks the per-node sharding contract.

When operator priorities shift — e.g., a new revenue path requires
multi-symbol — these explicit-NOs become explicit decision points,
not silent assumptions.

---

## 13. Cross-reference index

Every claim in this doc traces to a canonical source. Use this table
for quick lookups when implementing or reviewing.

| Topic | CLAUDE.md item | DESIGN_SPECS path | RECURRING_BUG_PATTERNS class |
|---|---|---|---|
| Portfolio bitmap | 1 | bitmap-flag-api.md | — |
| Per-position TP/SL hot, portfolio slow | 2 | — | — |
| Fill consumption every tick | 3 | — | — |
| Per-node data plane | 4 | — | — |
| OMS submit funneling | 5 | — | — |
| OneCore helpers | 6 | — | — |
| Warmup observes before trading | 7 | — | — |
| TUI decoupling | 8 | — | — |
| No API key for market data WS | 9 | — | — |
| Partial exits dispatcher post-cap | 10 | — | — |
| Smart CPU pinning | 11 | — | — |
| Display ↔ execution invariant | 12 | display-execution-invariant-registry-pattern.md | — |
| X-macro registry | 13 | x-macro-registry-with-presence-dispatch.md | Class 11 |
| NaN-free feature pack | 14 | — | — |
| Parity-tested-by-construction | 15 | wire-format-byte-preservation-discipline.md | — |
| Reuse-audit | 16 | — | — |
| Latency-additions tracked | 17 | — | — |
| Slow-path latency reduction | 18 | latency-vs-cache-decision-framework.md | — |
| Structural fix preferred | 19 | structural-fix-preferred-decision-framework.md | Class 18 |
| Bit-packed flag storage (BITMAP_*) | 20 | bitmap-flag-api.md, bitmap-overflow-protection-discipline.md | Class 20 |
| AUTOPOPULATE companion | 21 | autopopulate-pattern-for-production-caller-class.md | Class 14 |
| PRE/POST registry split | 22 | pre-post-cfg-registry-split-for-emit-order-preservation.md | — |
| Type-trait dispatch via tt:: | 23 | type-trait-dispatch-via-tt-namespace.md | Class 23 |
| Per-arm reward observability | 24 | prng-choice-for-replay-determinism.md | — |
| AVX-512 byte determinism | 25 | avx512-byte-determinism-pattern.md | — |
| Math kernels constant-iter + branchless | 26 | branchless-math-kernel-pattern.md | — |
| Struct padding determinism | 27 | struct-padding-determinism-pattern.md | — |
| Cycles vs cache cost framework | 28 | latency-vs-cache-decision-framework.md | — |
| Sliding-window incremental stats | 29 | sliding-window-online-statistics-pattern.md | — |
| Registry-bitmap SET discipline | 30 | registry-bitmap-set-discipline.md | — |
| Categorical-tag applicability | (CLAUDE.local.md rule) | categorical-tag-applicability-pattern.md | Class 19 |
| Cross-file cfg unification | (CLAUDE.local.md rule) | universal-cfg-field-registry-pattern.md § "Cross-file" | Class 21 |
| Cohort audit when new cfg sibling | (CLAUDE.local.md rule) | cfg-flag-eligibility-criteria.md § "Cohort audit" | — |
| Boundary-stable refactors | (memory rule) | — | — |
| Audit-driven pre-coding gate | (CLAUDE.local.md rule) | audit-driven-pre-coding-gate.md | — |
| Pattern codification lifecycle | (CLAUDE.local.md rule) | pattern-codification-lifecycle.md | — |
| Framework-driven extensibility (meta-principle) | 31 | (§ 1.5 — this doc) | — |
| Metadata-bit-driven derived filter framework | (item 31 sub-pattern) | metadata-bit-driven-derived-filter-framework.md | — |
| Meta-registry of registries (codebase-wide) | (item 31 sub-pattern) | meta-registry-pattern-for-codebase-registry-discipline.md | — |
| Sidecar override pattern for auto-flows | (item 31 sub-pattern) | sidecar-override-pattern-for-registry-auto-flows.md | — |
| Framework composition (cfg infra at .F.4d) | (item 31 sub-pattern) | framework-composition-overview.md | — |
| Plan API drift (fictional functions) | — | — | Class 14 |
| Function signature drift | — | — | Class 15 |
| Naming convention drift | — | — | Class 16 |
| Architectural deferral without grep | — | — | Class 17 |
| Mirror-incomplete plans | — | — | Class 18 |
| Hardcoded instance names | — | — | Class 19 |
| Bitmap overflow without static_assert | — | — | Class 20 |
| Multiple parallel descriptors | — | — | Class 21 |
| Runtime cfg gating scattered | — | — | Class 22 |
| Type-erased reinterpret_cast dispatch | — | type-trait-dispatch-via-tt-namespace.md | Class 23 |
| M1 — Sister-registry parity verification (meta-discipline) | (this doc § 11.5) | canonical-sister-extension-discipline.md | — |
| M2 — Cross-tool emit-site enumeration (meta-discipline) | (this doc § 11.5) | wire-format-byte-preservation-discipline.md § Layer 7 | — |
| M3 — Anti-pattern codification distinguishes legitimate siblings (meta-discipline) | (this doc § 11.5) | (codification template in RECURRING_BUG_PATTERNS.md intro) | — |
| M4 — Implementation-detail audit layer above SHAPE (meta-discipline) | (this doc § 11.5) | implementation-layer-blindspot-taxonomy.md | — |

---

## 14. How to extend this doc

When a new architectural pattern matures (per `pattern-codification-lifecycle.md`):

1. The pattern gets a DESIGN_SPEC body
2. After 2+ codebase applications, the pattern becomes a CLAUDE.md item
3. **Add it to this doc** under the appropriate family section (or create a new family)
4. Update the cross-reference index in section 13

When a new bug class gets a 3rd recurrence:

1. Add Class N entry to `DOCS/RECURRING_BUG_PATTERNS.md`
2. If a positive antidote pattern is established → add DESIGN_SPEC
3. **Cross-link from the relevant family section in this doc**
4. Update the cross-reference index

When operator priorities shift:

1. Update section 12 (explicit NOs) to remove the item or add a new explicit-YES
2. Update CLAUDE.md if the change affects always-on context
3. Add a CLAUDE.local.md going-forward rule if the change has process implications

---

## 15. Glossary

Canonical terminology source-of-truth for the post-`.E` architecture. All other docs cross-reference this section; never duplicate definitions. New terms introduced anywhere in the codebase MUST be added here.

**Terminology-evolution note (codified `.D.1` 2026-05-28):** terminology evolved at `v5.15.5.F.4d.1.E.1` — `per-core`→`per-node`, `Core`→`Node`, drainer absorbed into per-node slow-path. **Pre-`.E.1` historical-record docs** (postmortems / handoffs / changelogs / the RECURRING_BUG_PATTERNS catalog / shipped plan bodies) use `per-core` accurately for their time and are NOT rewritten (rewriting would falsify the evolution record + break `.E.1`'s "rename Core→Node" narrative coherence). **Current + forward-looking docs** use `per-node`. This Glossary is the bridge: when reading older docs, `per-core` ≈ today's `per-node`. Code symbols (`CoreContext`, `MAX_CORES`, `state.cores`, `FOREACH_PER_CORE_CFG_FIELD`, cfg-field names) keep their `Core*` names in citations until `.E.1` renames the code itself. (Per `feedback_terminology_evolution_bridge_not_history_rewrite`.)

**Numeric-core spelling note (A.5, `v5.15.5.F.4d.1.E.0.8`, 2026-06-09):** the binary fixed-point TYPE renamed `FPN` → `FPN_Binary` (D-143/D-163) ahead of Ship-B's `FPN_Decimal`. Reading pre-A.5 docs/history: `FPN` ≈ today's `FPN_Binary`. The `FPN_*` FUNCTION family (`FPN_Mul`, `FPN_ToDouble`, …) did NOT rename (Ship-B decides the op-surface naming); the trait `is_FPN_v` RETIRED onto `is_fp_binary_v`. Full entry: operator `DOCS/GLOSSARY.md` § Numeric core.

**Scope of this Glossary:** DEPLOYMENT/ARCHITECTURE-level terms only. Runtime-level primitives (`seqlock`, `SPSC ring`, `BG_Evaluate`, `SG_Evaluate`, `FPN_Binary<F=64>`, `tt::` namespace, `OMS_DrainSubmit`, `Regime_Classify`, kill-switch lifecycle) belong in the operator-facing `DOCS/GLOSSARY.md` (lands at `.E.2`), not here.

### Deployment hierarchy

- **Deployment** — the engine instance (whole); one process; one systemd unit. Owns ≥1 cluster. Unit of operator start/stop/restart.
- **Cluster** — per-exchange grouping within a deployment. Owns producer thread + exchange adapter + sub-account pool + rate budget + WS user-data connection + per-cluster credentials + market-hours enforcement. Failure-isolated (per-cluster kill flag halts only that cluster). One cluster = one exchange.
- **Node** — logical trading unit within a cluster. Bound 1:1 to a sub-account. Owns slow + hot pthread pair on dedicated CPU resources (typically 2 CPU cores), its own strategy + ML model + risk params + portfolio slot. Per-node failure domain at the economic layer (exchange-enforced via sub-account isolation). (Was "core" pre-`.E.1`.)
- **ExecutionCore** — runtime hot-path execution context WITHIN a Node; per-thread CPU-execution unit; distinct concept from the deployment-unit "Node". **PROPOSED canonical:** keep the `ExecutionCore` name for the runtime CPU-execution concept (it names a CPU-execution unit, not a deployment shard, so it reads correctly post-rename). **NOT YET RATIFIED** — D-27 renames `CoreContext`→`NodeContext` but is SILENT on `ExecutionCore`; confirm its disposition at `.E.1` design (rename to `ExecutionNode`/`NodeExecCtx` vs keep `ExecutionCore`). Do not treat this entry as a decided fact until `.E.1` confirms.
- **CPU core** — hardware concept; physical processor core. References stay "CPU core" (never "node"). One Node typically uses 2 CPU cores.

### Threading

- **Producer thread** — one per cluster. Reads exchange WS feed; parses ticks; fans-out to per-node SPSC rings; replicates ema_price; publishes viewer state. (Was global single producer pre-`.E.1`.)
- **Drainer thread** — DEPRECATED post-`.E.1`; absorbed into per-node slow-path. Pre-`.E.1` was the global thread running `OMS_DrainSubmit` + `OrderManager_Tick` + `DrainPostFill`.
- **Aggregator** — single global thread; reads per-node state via seqlock; computes per-cluster + global totals; sets hierarchical kill flags. Read-only wrt per-node state (per-node writes; aggregator reads). Event-sourced per-fill atomic updates; periodic cycle = integrity verification only.
- **Hot path** — per-node per-tick context; branchless (H7); ≤500ns p99 (H8). **Slow path** — per-node per-poll-interval context; ≤100μs p99 (H8).

### Economic + isolation

- **Sub-account** — exchange-enforced economic isolation unit; one Node bound 1:1 to one sub-account. Structurally stronger than virtual partition. Canonical isolation mode for exchanges supporting sub-accounts (Binance); virtual partition is the fallback (Alpaca/IBKR retail).
- **Capital allocation** — cluster-level distribution across Nodes (`reserve_pct` + `max_per_node_pct`); aggregator enforces at submit time.

### Build / runtime artifacts

- **fox-engine** — headless engine binary (systemd service in production); state via mmap, commands via UDS. Replaces `engine_gui` (archived `.E.2`).
- **fox-tui** — read-only notcurses viewer (reads mmap zero-copy). **fox-cli** — command sender via UDS. **foxml-train** — headless ML training CLI (replaces `foxml_suite`, archived `.E.2`).

### Mode + version flags

- **`mode = backtest | paper | live | shadow`** — per-node operating mode (4-state H14 MBS encoding).
- **`topology.mode = dev | production`** — deployment-wide thread scheduling (dev OS-scheduled; production isolcpus + nohz_full + pinning). Same binaries.
- **ENGINE_VERSION_STRING** — per-ship internal version (high-velocity). **SOFTWARE_VERSION_STRING** — platform milestone (coarse; starts `v0.1.0` for full `.E` end-game). Both HMAC-stamped.

---

**End of DESIGN_PHILOSOPHY.md.** This doc is the WHY behind the codebase's
mental model. The patterns + items + bug classes referenced are the source-
of-truth — this doc synthesizes. Read it cold-pickup; refer to it when
designing; cross-link from it when extending.
