---
type: guard-coverage-matrix
sub_sprint: v5.15.5.F.4d.1.E
sprint: v5.15-live-readiness
established: 2026-05-28
status: scaffold (cross-cutting rows + distribution filled; per-ship rows filled during each `.E.x` focused dive)
owning_ship: v5.15.5.F.4d.1.E.0 (creates + owns); maintained `.E`-wide and beyond
decision_ref: DD-5 + D-67..D-72 (this session; see decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md)
sister_docs:
  - subplans/2026-05-28-v5.15.5.F.4d.1.E.0-precoding-plan-audit-verification.md (the gate that owns this)
  - subplans/2026-05-28-v5.15.5.F.4d.1.E-dependency-graph.md (the static DAG; this matrix is its DYNAMIC verification companion)
  - plan_checks/E.0-audit-reports/pre-implementation-findings/_SESSION-CONTEXT.md (the 141 findings = the row source)
tags: [verification-substrate, guard-coverage, safeguard-distribution, enforcement-ladder, rolling-window-seam]
---

# `.E` guard-coverage matrix + verification substrate

**The single artifact that answers: "what's protected, at what tier, by which guard, owned by which ship?"** — for the `.E` rework and the years after.

The maturity gradient this drives: *"neat repo I watch"* → *"oh shit I can use this"* (`.E.2` usability) → **"run real money on it"** (this matrix has no open HOLE cells). The threshold to capital is crossed when every row is enforced at some tier or carries an explicit accepted-rationale.

**Living doc.** Cross-cutting rows + the distribution are filled now (`.E.0` scaffold); each per-ship row is filled during that ship's focused dive (the rolling window, §5). The TIMELESS disciplines below (§1 ladder, §2 triad, §5 rolling-window/seam) get promoted to DESIGN_SPECS during `.E.0` Step-3 codification — they live here as the working draft until stable.

---

## 1. The enforcement ladder — push every guard as high as it goes

For each invariant / finding-class / safeguard, ask **"what's the highest tier I can push this to?"** — not "how do I fix this instance?" Death by a thousand cuts is impossible when each cut is a compile error or a red build.

| Tier | Mechanism | The bug becomes… | This codebase's instances |
|---|---|---|---|
| **1 — Structural / compile-time** | type-trait dispatch (H13), X-macro registries (H15-H19), `static_assert`, MBS_* encoding | **unrepresentable** (can't compile) | `tt::<verb>_field<T>`; `FOREACH_*` 1-row auto-flow; bitmap-overflow static_asserts |
| **2 — CI check** | `check_*.py` + pre-commit hook | breaks the build at commit | `check_meta_registry.py`, `check_per_core_registry_integrity.py`, `check_forward_promise_audit.py` |
| **3 — Regression / characterization test** | `tests/` | breaks the suite | `controller_test.cpp` (3239), `parity_harness.cpp`; the NEW PERSIST characterization tests |
| **4 — Runtime assertion / observability** | kill-switch on violation; metrics; audit log | caught loudly in paper-test | hierarchical kill switch; `.E.2` Prometheus + audit log |
| **5 — Periodic audit sweep** | `/bug-check`, `/anti-spaghetti`, `/dod-audit`, `/seam-audit` | found by a sweep that should return **CLEAN** | the cadence skills |

**Rules:**
- **One guard per class, at the highest reachable tier — never duplicate.** A compile-time guard makes the CI check redundant; don't write both. *Maximum safety = maximum coverage at the right tier, not maximum count.* Guard-sprawl is its own maintainability rot.
- **Hot-path constraint:** the 500ns branchless hot path takes **Tier-1 guards only** (no runtime checks affordable). Runtime money/risk checks live on the drainer/slow path. The tier depends on the path.

---

## 2. The verifiability triad — the answer to "is it working?"

The direct antidote to "death by a thousand cuts where you can't tell if something's broken":

1. **Determinism** (byte-identical cross-run / cross-binary): turns "is it working?" into "does it match the golden output?" — a *diff*, not a *judgment*. Verifiable by construction.
2. **Golden-master / characterization tests**: capture known-good once; every run diffs against it. The PERSIST tests are the first golden masters.
3. **Built-in observability** (`.E.2`): the engine continuously *tells you* its state; you stop guessing.

---

## 3. Safeguard → ship distribution (the map)

Distribute, don't pile: each safeguard lives in the ship rewriting the surface it guards (DAG-respecting, no orphans). Cross-cutting verification infra goes in `.E.0`/`.E.1` **first** so the rework is gated from commit one.

| Safeguard | Owning ship (as a named phase) | Status | Why there |
|---|---|---|---|
| Guard-coverage matrix (this doc) | `.E.0` | net-new | the "what's protected?" map; maintained `.E`-wide |
| PERSIST characterization tests | `.E.0` | in Job B | freeze current behavior before rework |
| Determinism CI gate (2× run + ±`USE_NATIVE_128` byte-compare) | `.E.0` → `.E.1` | net-new | verifiability backbone; FP-path confirm is `.E.0` runtime-confirm |
| Latency ratchet (H8 budgets as CI gate) | `.E.1` | net-new (have `LATENCY_BENCH`) | set early so every later ship is gated |
| CI-as-merge-gate (all-green-or-no-merge) | `.E.1` | partial | the spine |
| 3-path identity (backtest≡paper≡live diff) | `.E.1` spec → `.E.2` operational | DESIGN_SPEC exists | needs headless (`.E.2`) to run paper/live |
| Conservation invariants (accounting closes) | `.E.1` | net-new (+PERSIST in `.E.0`) | foundation accounting |
| Pre-trade risk gates (max pos/notional/fat-finger) | `.E.1` | partial (kill-switch) | OMS/drainer path, NOT hot path |
| Kill-switch hierarchy + tested flatten-all | `.E.1` | planned | foundation |
| Watchdog/liveness + staleness guards | `.E.1` + `.E.2` | net-new | never trade on stale state |
| Crash-recovery identity (recovered==pre-crash) | `.E.2` | planned (mmap-state) | needs mmap state-publish |
| Forensic observability (provenance/audit-log/replay/SLO) | `.E.2` | planned | "why did it trade?" |
| Chaos/DR testing (fire the safeguards on purpose) | `.E.2` + per-ship | planned (`DR_TESTING.md`) | a safeguard never watched fire isn't one |
| Idempotent submission (client order IDs) | `.E.3` | net-new | reconnect = double-submit risk |
| Reconnect → reconcile (no blind resume) | `.E.3` | planned | the WS-API ship |
| Reconciliation (engine vs exchange → halt) | `.E.3` base, `.E.5` per-node | pattern-referenced | needs persistent exchange connection |
| Per-node economic isolation | `.E.5` | planned | blast-radius containment |
| Mutation testing (validate the net has no holes) | `.F` | net-new | only meaningful once the net is built |

---

## 4. The guard-coverage matrix (the completeness contract)

**Rule:** no row may remain `HOLE` at `.E` close without an explicit accepted-rationale. An empty cell is a *visible to-do*, not an oversight. Status legend: **ENFORCED** / **PARTIAL** / **HOLE** (convention-only) / **TBD** (current enforcement audited during the owning ship's dive — this audit *is* the matrix-filling work).

### 4a. Hard invariants H1-H20

| # | Invariant | Highest reachable tier | Current guard (to verify) | Status |
|---|---|---|---|---|
| H1 | no malloc/new/vector/string/function | 2 (grep CI) | grep-based CI candidate | TBD |
| H2 | no virtual/shared_ptr/unique_ptr on hot path | 2 (grep CI) | — | TBD |
| H3 | no mutex/cv/sleep_for/pthread_rwlock | 2 (grep CI) | — | TBD |
| H4 | FPN not float/double on accounting | 2 (grep CI) | — | TBD |
| H5 | no scalar JSON/strstr/atof in parser | 2 (grep CI) | — | TBD |
| H6 | alignas(64) cross-thread + cluster by access | 3/review | — | TBD |
| H7 | hot path branchless | 1/3 | LATENCY_PROFILING; discipline | **PARTIAL → likely HOLE** |
| H8 | hot p99 ≤500ns; slow ≤100μs | 2 (CI gate) | `LATENCY_BENCH` exists; gate? | **PARTIAL → latency ratchet (`.E.1`)** |
| H9 | wire byte-preservation (HMAC bodies) | 2/3 | `parity_harness.cpp` + check tools | ENFORCED/PARTIAL |
| H10 | SIMD scalar fallback byte-identical | 2/3 | `check_h10_simd_determinism.sh` (REAL kernel AVX-512 vs `-mno-avx512f` scalar memcmp; `check_determinism.sh` gate 4 + pre-commit Check F; non-vacuity asserted) | **ENFORCED** (`.E.1.0`) |
| H11 | constant-iter branchless reductions | 1/3 | discipline | TBD |
| H12 | explicit padding in byte-equiv structs | 1 (static_assert) | — | TBD |
| H13 | no reinterpret_cast punning; `tt::` dispatch | 1/2 | type-trait; grep candidate | **PARTIAL** |
| H14 | no C++ bitfield syntax | 2 (grep CI) | `check_h14_no_bitfield.py` (pre-commit Check M; decidable, 0 hits, teeth-proven) | **ENFORCED** (`.E.1.0`) |
| H15 | every X-macro registry in FOREACH_REGISTRY | 2 | `test_meta_registry_coverage` | ENFORCED |
| H16 | metadata bit → derived filter | 2 | `test_metadata_bit_to_derived_filter_coverage` | ENFORCED |
| H17 | cfg fields auto-gen from FOREACH_CFG_FIELD | 2 | CI Check 2 | ENFORCED |
| H18 | sidecar override not parallel registry | 5/review | convention | PARTIAL |
| H19 | meta-registry topology (valid parent) | 2 | `test_meta_registry_topology` | ENFORCED |
| H20 | branchless SP/HP dispatch | 1/5 | discipline | **PARTIAL → likely HOLE** |

> **The matrix earns its keep on day one:** the invariants most likely to be convention-only (H7 / H10 / H13 / H14 / H20) are *exactly* the hot-path + determinism + branchless ones — the highest-blast-radius surface. That cluster is the death-by-a-thousand-cuts hotspot. Closing it (grep-CI + the determinism gate) is `.E.1`'s first-order matrix work.

### 4b. Finding-classes (the 141 + bug-catalog 1-36) — filled during the owning ship's dive

| Source | Rows | Owning ship | Status |
|---|---|---|---|
| `conc-5` (CRITICAL, race) | submit_queue single-producer | `.E.1` (CHANGES-BY-DESIGN) | TBD (runtime-confirm `.E.0` A2) |
| `live-bc-1` (CRITICAL, endpoint split) | Binance global/US | fix-now current code | TBD (config-trace `.E.0` A2) |
| fixedpoint-mem cluster (23, 9 HIGH) | `FPN_Sqrt`/`USE_NATIVE_128` determinism | `.E.1` + determinism gate | TBD |
| `E.1-findings.md` (30) | — | `.E.1` | TBD-during-dive |
| `E.2-findings.md` (14) | — | `.E.2` | TBD-during-dive |
| `E.3-findings.md` (10) | — | `.E.3` | TBD-during-dive |
| `E.5-findings.md` (6) | — | `.E.5` | TBD-during-dive |
| `E.6-findings.md` (2) | — | `.E.6` | TBD-during-dive |
| `PRE-PAPER-TEST` (55) | — | correctness gate (task #19) | TBD |
| `BACKLOG-STANDALONE` (24) | — | TECH_DEBT / `.F` | TBD |
| RECURRING_BUG_PATTERNS 1-36 | existing anti-patterns | `/bug-check` (Tier 5) | ENFORCED (catalog) |

### 4c. System-safety safeguards (from §3) — filled during owning ship's dive

(Reconciliation, idempotency, crash-recovery, watchdog, etc. — each becomes a row with its tier + guard + status when its ship is dived.)

### 4d. `.E.0.10` net hardening — the COMPLETE current guard set (filled at the `.E.0.10` close, 2026-06-15)

The pre-`.E.1` Net-1 ship added these ENFORCED guards; recorded so the matrix measures the complete guard set the `.E.1` dive inherits (`feedback_guard_matrix_bounds_foundation_hardening`):

| Safeguard | Tier | Guard | Status |
|---|---|---|---|
| A6 EGRESS — barrier range-validate at every gate-emit | 1+3 | `GateParameters_FinalizeEmit` single-dispatcher chokepoint (`SHALT_BAD_PCT`; range `[0,10000.0]` catches NaN/+Inf/neg; override-first-wins) — every dispatched strategy flows through it, a 7th auto-inherits + 12 char-tests | ENFORCED |
| A6 INGRESS — corrupt-model detect → per-arm-drop → majority node-SHALT | 1+3 | `barrier_is_corrupt` SSoT (`BarrierValidation.hpp`) at `ezoo_set_per_arm_barrier` + `EnsembleZoo_FinalizeCorrupt` + `MODEL_CORRUPT` CoreState (bit 5) + `SHALT_MODEL_CORRUPT` + trainer-emit floor + char-tests | ENFORCED |
| Class 44 — cfg-flag-orphan (operator-settable flag, no live reader) | 2 | `scan_class_44_cfg_orphan.py --strict` promoted to STANDING CI (`check_session_docs.sh` HARD 10) | ENFORCED |
| Class 47 — split-brain control authority (NEW-1) | 1 | `ControllerConfig_IsLiveCapital` single-authority predicate → the 3 illegal cells UNREPRESENTABLE; every authorizer routes through it; legacy single_core LIVE hard-refused (H21) | ENFORCED (structural); CI detector = candidate |
| Class 50 — re-init/reset defeats thread-join lifecycle | 3 (+2 cand) | quiesce-first `OrderEventLog_Init` + the dedicated Class-50 regression; the broader single-owner-`disk_file` + CI detector = `.E.1` SPSC rework | ENFORCED (instance) / PARTIAL (class → `.E.1`) |
| TD-202 OMS event-log UAF (asan ship-gate) | 2+3 | quiesce-first `Init` fix; asan FRESH 3632/0 — and `run_sanitizer_suite.sh` now REBUILDS each lane from current source (anti-stale: the gate had graded months-old binaries) | ENFORCED |

**STOP-condition verdict for `.E.1` entry:** the recorded HOLE cluster on the `.E.1`-touched surface is **§4a H7 / H10 / H14 / H20 + H8** (hot-path branchless · SIMD-fallback · bitfield · SP/HP dispatch · latency) — EXPLICITLY recorded + owned as `.E.1`'s **first-order matrix work** (grep-CI + the determinism gate + the latency ratchet, per §4a:110 + §3). These are deferred BY DESIGN, not overlooked: closing them before the rename would freeze hot-path behavior `.E.1` is about to reshape (two-foundations). **No *unrecorded* HOLE remains on the `.E.1` surface** (§4 completeness rule — every HOLE is a visible, owned to-do). `.E.1` enters with its hardening worklist explicit; the `.E.0.10` net is complete.

**↳ `.E.1` DECOMPOSITION (2026-06-15, D-225):** the HOLE cluster + the per-finding rows now have sub-ship owners (the 7-leaf decomposition). **§4a H7/H10/H14/H20+H8 HOLE cluster → owned by `E.1.0`** (the guards-first leaf — grep-CI + determinism gate + latency ratchet, BEFORE the rename). §4b finding-classes: the torn-read/kill rows → E.1.3; fill-completeness → E.1.4; per-cluster purity → E.1.5. Each leaf FILLS its rows at its dive (the rolling-window). Per-leaf row distribution: the `.E.1` sub-master § DECOMPOSITION + the leaf scaffolds.

---

## 5. Rolling-window seam cadence — how the dives sequence

Plan-by-plan, **but with bounded neighbor-overlap** so a decision in dive N can't silently break N+1.

```
dive N's window  =  { tail of N-1 that N depends on }   (inbound seam — re-verify predecessor delivered it)
                 ∪  { N itself }                          (full focus)
                 ∪  { head of N+1 that assumes from N }   (outbound seam — verify N satisfies successor)
```

- The **overlap is just the seam** — not the whole neighbor. Enough to verify cohesion; not so much that context bleeds. (Caramel's "minor overlaps" instinct.)
- The seam **is** the dependency-graph's **forward-promises / cross-ship invariants** at that boundary. The static DAG *declares* the edges; this rolling window *verifies each edge holds* as decisions are made — and re-checks if a decision moves a node. **Dynamic complement to the static DAG.**
- The **handoff doc carries the seam** between dives (outbound-seam section = next dive's inbound-seam check). Reworking the handoff template to encode this = making the rolling window the going-forward handoff process. (`/handoff` Stage 2.8 + `/accept-handoff` Stage 4.5 already do predecessor-verification — this makes it explicit + structured.)
- This is `/seam-audit` (one of the 5 audit-recommended skills) applied at the **planning** level. Proven necessity: deep-sweep pass-2 (a seam-scan) caught the slow→hot flag-clobber that no per-surface scan could see.

**Dive order:** `.E.1` first (foundation; highest-risk; root of the DAG; the `conc-5` call), then `.E.2` … each in its own focused context.

---

## 6. How this is maintained — the loop that keeps sweeps quiet

1. **Per-dive fill:** each `.E.x` dive fills its matrix rows (§4b/4c) to depth — every finding pushed to its highest tier, every safeguard a named phase with tests + acceptance.
2. **Yield-as-signal:** track sweep yield over time. Declining → structure working. A spike → a new class slipped in → add the guard that should've caught it (M7 escalation). Yield→0 is the proof the framework is sound.
3. **Fix-the-class-never-the-instance:** every bug, forever, asks "can this recur? → structural fix + a guard that makes recurrence a red build." `/test-strength-audit` guards the ratchet (tests only get stricter).

**What "bulletproof" actually means here** (the honest version — not "no bugs ever"): (1) **no silent damage** — every failure mode is caught (red build / failed test / runtime halt / alert); you always *know* if something's wrong; and (2) **no recurrence** — every class, once seen, is walled. Trustworthy because *verifiable + can't-silently-regress* — which is what lets you run real money on it.

---

**End of `.E` guard-coverage matrix v0.1 (scaffold).** Cross-cutting rows + distribution + disciplines filled; per-ship rows fill during each focused dive. Promote §1/§2/§5 to DESIGN_SPECS at `.E.0` Step-3 codification.
