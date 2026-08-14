# Decoupling endgoal roadmap — runtime / viewer separation (PRIVATE living doc)

**Date opened:** 2026-05-12 (v5.15 sprint kickoff session)
**Status:** LIVING DOC → **CONVERGING at `v5.15.5.F.4d.1.E.2`** (reframed 2026-05-28 at `.D.1`; see "Status" section below). Accumulates per-ship breadcrumbs.
**Predecessor / companion:** `plans/_future/2026-05-08-v6.0-CANDIDATE-headless-service-colo.md`
(v6.0 colo architecture; this doc is the operational roadmap toward it,
covering both engine + suite sides).

**Why this doc exists.** Per Caramel 2026-05-12:
> *"as we progress fixes should lay out the approach to actually
> decouple it since we have the context in memory, that way when we
> actually go to decouple, we basically already have a psuedo plan
> laid out"*

Forward-looking design discipline: every change touching GUI ↔ runtime
interfaces deposits a breadcrumb here documenting how it positions us
for the eventual decoupling sprint. By the time we actually do the
decoupling sprint, this doc IS the pseudo-plan — endgoal architecture
named + breadcrumbs accumulated + open design questions surfaced + a
readiness checklist saying when we can proceed.

**Where this doc lives.** Workspace-private (`plans/_future/` gitignore
pattern). Auto-synced via `/sync-workspace`.

---

## Status (2026-05-28): converging at `.E.2`

> **Reframing note (2026-05-28, `.D.1` doc sweep):** This document was drafted **2026-05-12** as future-vision when the codebase was still pre-`.E` per-core sharded with a monolithic `engine_gui` binary. The architecture described here **converged into the `.E` sub-sprint** at planning 2026-05-28 (per D-4, D-7, D-26, D-46). The "endgoal" framing below should now be read as **"lands at `v5.15.5.F.4d.1.E.2`"** — actively being built, not aspirational. The **original vision body is preserved below** (historical context — when the vision was first articulated + why decoupling matters); it uses the original 2026-05-12 working terminology (`per-core`, `engine_viewer`/`foxml_runtime` binary working-names) intentionally, bridged to the canonical post-`.E` vocabulary via `DOCS/DESIGN_PHILOSOPHY.md` § 15 Glossary.

This roadmap's vision lands at the **`.E.2`** ship. Canonical references:
- `.E.2` plan body: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md`
- `E-MASTER-REFERENCE.md` (CLAUDE.md + DESIGN_PHILOSOPHY amendments + supporting docs at `.E.2`)
- Decision log v2: D-4 (headless folded into `.E.2`) + D-7 (GUI focus reduced) + D-26 (GUI hard-deprecate at `.E.2`) + D-46 (documentation deliverables)
- Canonical binary names (per DESIGN_PHILOSOPHY § 15): `fox-engine` / `fox-tui` / `fox-cli` / `foxml-train` — these supersede the `engine_viewer` / `foxml_runtime` / `foxml_viewer` working-names in the original diagram below.

---

## `.E.0.10` breadcrumb (2026-06-10) — the published-snapshot pattern is the SHARED FOUNDATION (operator insight)

**Caramel surfaced this at the `.E.0.10` cross-thread torn-read investigation:** the torn-read fix, the decoupled monitor, and headless/SSH viewing are **ONE pattern, not three problems.**
- The GUI is the ONE site today that reads money SAFELY — off a seqlock-published `TUISnapshot` (vs the 9 cross-thread torn-read sites that read live OMS money raw; see `concurrency-patterns/cross-thread-multiword-read-consistency-discipline.md` + `.E.0.10` register).
- The `.E.1` **aggregator-published money snapshot** (the structural fix for the torn-read class — D-54 / decision-log F-2-AMEND) IS that same published-snapshot pattern, generalized to the whole money surface.
- And that aggregator-published snapshot IS the foundation the decoupled monitoring plane needs: the **headless engine publishes the snapshot; viewers (`fox-tui` / GUI / SSH / web) attach + read it.** Headless monitoring works *because* the viewer reads the published snapshot, not live state.

**Positioning for the decoupling sprint:** the `.E.1` aggregator-published-snapshot is **load-bearing for the decoupling end-goal**, not just a concurrency fix — it's the publish side of the runtime→viewer boundary. When `.E.2` builds the headless/viewer split, the money-snapshot publish channel should already exist (built at `.E.1`). So sequence-wise: `.E.1` aggregator (publish channel) → `.E.2` headless + viewer attach. Cross-ref: `.E.0.10` register § SESSION STATE (operator-architecture-insight) + decision-log F-2-AMEND + `cross-thread-multiword-read-consistency-discipline.md`.

**What `.E` adds beyond the original vision:** the **multi-exchange substrate** (per-cluster scaling) that the 2026-05-12 doc didn't cover — the `.E` Cluster/Node/Deployment hierarchy wasn't yet decided.

---

## `.E.1`/`.E.2` breadcrumb (2026-06-21) — manual TP/SL adjustment: a `fox-cli` verb, or dropped? (OPEN — D-241)

Operator design question surfaced the **control-boundary's sharpest case**, the complement to the publish-channel insight above. The GUI-drag adjustable TP/SL is **already inert on the sharded path** (TD-184 — the drag writes the *display* level `pos->take_profit_price`, but the hot exit gate reads `core->live_tp`/`live_sl`, never copied → a Class-2 display↔execution lie) AND the GUI itself **hard-deprecates at `.E.2`** (D-26 → `engine_gui` archived). So in the decoupled world there's no drag at all — manual exit-control becomes a **verb-or-nothing** choice on the `fox-cli` UDS command channel:
- **(A) drop it** — TP/SL fully engine-managed (strategy + ratchet + regime); no exit-adjust verb. Matches the headless-autonomous-shard-farm direction.
- **(B) keep it** as a `fox-cli adjust-exit` verb; engine side = the TD-184 `live_tp`/`live_sl` per-node wiring, command-triggered + validate-before-apply + reconciled with TD-189 (live-multiplier storage).

**Positioning:** this is the canonical *control* complement to the `.E.0.10` *publish* breadcrumb — **publish** = mmap snapshot (viewers read); **control** = UDS verbs (fox-cli writes). The TP/SL-adjust verb is the litmus for how much write-control the decoupled boundary exposes at all. **Decide at `.E.2` before the D-52 verb set locks.** → decision-log **D-241**; homed in the `.E.2` plan (command-channel/verb-set §) + the **TD-184** ledger entry.

---

## `.E.2` breadcrumb (2026-06-22) — backtest surface: CLI runner + read-only viewer (NOT a GUI utility) [OPEN — D-244]

Operator design Q — the **backtest-tool** complement to the publish + control breadcrumbs above. Backtest is decoupled from LIVE (research, not the 24/7 capital engine), and the GUI hard-deprecates at `.E.2` (D-26) — so should backtest stay a GUI utility, or go CLI? **Same decoupling pattern as live: headless compute + read-only viewer + CLI control.**
- **CLI runner is the core** — E.2's already-planned `foxml-train` (operator sketch `./foxmlsuite --backtest --config path`). Wins: SSH-friendly · scriptable/batchable · **reproducible** (`--config path` = the exact settings saved/versioned/re-runnable; a click-knobs GUI never captures what you ran) · lightweight (no SDL2/ImGui).
- **The GUI-viewer-nice value survives as a read-only viewer on the backtest's OUTPUT artifacts** (equity curve / trades / metrics) — visual exploration without the backtest logic in the GUI. Not either/or.
- **Positioning — the decoupling triad now has all three legs:** **publish** = mmap snapshot (`.E.0.10` breadcrumb) · **control** = UDS verbs (D-241 breadcrumb) · **compute/research** = the `foxml-train` CLI (this). The `.E.1.1` ③ config-compiler output (terminal + `config_error_log`) is the surface-agnostic seed that works for the CLI runner. **Decide at `.E.2`.** → decision-log **D-244**.

## Endgoal architecture (what success looks like)

```
        ┌────────────────────────┐         ┌────────────────────────┐
        │  ./engine               │         │  ./bin/engine_viewer    │
        │  (headless runtime)     │ ◄──────►│  (Grafana-style viewer) │
        │                         │ mmap/ws │                         │
        │  • Per-core hot path   │         │  • ImGui or TUI render  │
        │  • Slow path           │ ─────►  │  • Multiple instances   │
        │  • OMS / drainer       │ logs    │  • Reconnect-tolerant   │
        │  • Publishes snapshot  │ →       │  • Read-only view       │
        └────────────────────────┘         └────────────────────────┘

        ┌────────────────────────┐         ┌────────────────────────┐
        │  ./bin/foxml_runtime    │         │  ./bin/foxml_viewer     │
        │  (headless training)    │ ◄──────►│  (training panel viewer)│
        │                         │ disk    │                         │
        │  • Spawns CLI modes    │ artifacts│  • Tails per-run dirs   │
        │  • Per-run logs/state  │ ─────►  │  • Drives invocations  │
        │  • execv child workers │         │    via shell-spawn      │
        │  • All ops cmdline-able│         │  • Multi-run dashboard  │
        └────────────────────────┘         └────────────────────────┘
```

**Success criteria when decoupling sprint completes:**
- Engine runs headless as systemd service; survives viewer crash
- Multiple viewers can connect to same engine concurrently
- foxml_runtime invocable purely via cmdline (CI-friendly, scriptable)
- GUI viewer disconnect/reconnect doesn't impact runtime hot path
- State exposure protocol versioned + stable across viewer/runtime updates
- No code path mixes "runtime work" + "GUI rendering" in same process

---

## Decoupling axes (what specifically needs to decouple)

| Axis | Today | Endgoal |
|---|---|---|
| **Process boundary** | engine + GUI same process (engine_gui binary) | engine = separate process; GUI = viewer process attaches via IPC |
| **State exposure protocol** | TUISnapshot in-process double-buffer | mmap'd region OR Unix socket protocol; versioned schema |
| **Cfg layer ownership** | Cfg parsed by engine; engine_gui inherits | Cfg owned by runtime; viewer may have its own display cfg |
| **Lifecycle independence** | GUI crash kills engine; engine crash blocks GUI | Either can crash without affecting the other; reconnect-tolerant |
| **Multi-viewer support** | 1 GUI per engine process | N viewers concurrently; viewers read-only |
| **Training entry points** | GUI button → in-process pthread training | GUI button → execv child via FOREACH_CLI_MODE registry (v5.15.3 foundation) |
| **Logging structure** | Mixed stderr to single foxml_suite.log | Per-run dirs at logging/foxml_suite/<run_name>/; tailable per-horizon |
| **Progress/status IPC** | Shared in-process state (shared mutex) | Per-run disk artifacts; viewer polls |
| **HMAC chain stability** | Stamp body byte format stable today | Must remain stable across engine/viewer version skew |

---

## Running breadcrumbs — per-ship positioning notes

### v5.15.0 — ModelHandle X-macro migration + verify_model_stamp parser refactor (POSITIONING: ⬆️ positive)

**Date:** 2026-05-12 (SHIPPED; tag `v5.15.0`)

**Shipped:** As described. ModelHandle migrated to FOREACH_STAMP_BOUND_MODEL_CONST
X-macro with STAMP_HANDLE_GEN_<presence> dispatch (33 INCLUDE fields auto-generated
+ 10 SKIP_HANDLE filtered); 14 has_* direct fields → uint64_t has_flags bit-packed
with SHARED MASK_<name> constants across ModelStampResult + StampInferenceCfgInputs;
value fields renamed to canonical wire-key names (stamp_xgb_*/stamp_inf_*/stamp_label_*
→ unprefixed canonical); alignas(64) + 4-cluster layout (HOT 64B / HOT-2 64B / WARM
scaler / COLD stamp fields + paths) + explicit padding per CLAUDE.md item 27;
verify_model_stamp PRE_CFG parser refactored to X-macro dispatch via
tt::stamp_parse_field<T> templated helper (24 entries auto-flow; 4 hex/normalize
exceptions retained as manual branches). +23 anchor tests (.A bit-pack + .C round-trip
HMAC byte-equivalence). Tests 2904 → 2927. TECH_DEBT-003 + -014 CLOSED.

**Change:** ModelHandle migrated to FOREACH_STAMP_BOUND_MODEL_CONST X-macro
generation with bit-packed `has_flags` uint64_t; verify_model_stamp parser
refactored to data-driven dispatch table.

**Decoupling positioning:**
- **Stamp body becomes registry-introspectable.** Future viewer can call
  `./engine --dump-stamp-schema` (a planned FOREACH_CLI_MODE entry) to
  get the canonical wire-key list + types. Viewer-side schema cache
  becomes possible without re-parsing C++ headers.
- **Parser is data-driven dispatch.** Future engine versions can extend
  stamp body via registry; viewer reading older stamps degrades
  gracefully (Surface G `has_*` flags). Cross-version compat preserved.
- **Bit-packed has_flags uint64_t is mmap-friendly.** Single 8-byte
  field consumed via single load; viewer reads `has_flags & MASK_<X>`
  directly without struct walking. Foundation for mmap'd ModelHandle
  exposure later.

**Pattern established:** "wire format defined by X-macro registry; struct,
parser, emit, AUTOPOPULATE all auto-flow." Reusable for FUTURE
state-exposure protocols (e.g., snapshot wire format).

**Anti-breadcrumbs:** none.

---

### v5.15.1 — Model Health CollapsingHeader + PerCoreSnap bitmap (POSITIONING: ⬆️ positive)

**Date:** 2026-05-12 (SHIPPED; tag `v5.15.1`)

**Shipped:** 7 new BIT_FLAG drift entries to FOREACH_FAILURE_MODE
under tt::GROUP_DRIFT (feature_hash_drift / label_hash_drift /
build_flags_drift / scaler_drift / cfg_binding_drift /
stamp_hmac_not_verified / model_age_warn); new FOREACH_ARCH_FIELD_DRIFT
X-macro registry (4 entries) for non-CFG-bound drift detection at
TryLoadRole post-verify chokepoint; ModelHandle.drift_flags_at_load
uint16_t (repurposed 2B of v5.15.0's _hot_pad1) carries per-handle drift
state. ShardedSnapshot OR-aggregates each zoo role's drift_flags_at_load
into PerCoreSnap.failure_flags. v5.15.1.B closes TECH_DEBT-028 by
migrating 4 bool-as-uint8 PerCoreSnap fields (ml_scaler_present,
drift_breached, drift_kill_tripped, core_kill_tripped) to existing
state_flags uint16_t bitmap — REUSE of v5.14.9.B.2 bitmap surface
(cohort homogeneity preserved). MLStatusPanel Model Health
CollapsingHeader renders aggregated drift state with severity-colored
labels + hover tooltips + model age display.

Scope refinement vs original plan: at-load diagnostic hash cluster on
PerCoreSnap (handle_feature_hash_at_load etc.) dropped from .B.2 —
would have required adding feature_registry_hash + label_registry_hash
to ModelHandle as runtime-only fields (not in stamp body registry).
Drift BITS + tooltips were sufficient for v5.15.1 operator signal.
training_timestamp_us captured for model age display. At-load
diagnostic values deferred to v5.15.1.post or v5.15.2.

Tests 2927 → 2940 (+13 v5.15.1 anchor tests: state_flags bit round-trip
+ failure_flags drift bit round-trip + registry count invariants).

**Decoupling positioning:**
- **Drift state is publication-only.** Slow-path writes; GUI reads via
  the existing double-buffered TUISnapshot. Already follows the
  viewer pattern — no in-process locking; viewer reads stable snapshot.
- **Per-core drift bits in failure_flags uint16_t are mmap-friendly.**
  Single AND-mask check via `BITMAP_IS_SET`; no pointer indirection;
  viewer reads the bitmap directly. Same shape as Portfolio bitmap
  (CLAUDE.md item 1).
- **alignas(64) drift cluster** preserves cache-line independence —
  future mmap'd snapshot region won't accidentally share a line with
  hot-path-writing fields.

**Pattern established:** "new visible state goes through
FOREACH_FAILURE_MODE (failure subset) or PerCoreSnap cluster (general
state). Both are mmap-stable layouts."

**Anti-breadcrumbs:** none.

---

### v5.15.2 — Live-readiness boot gate + trading_mode + breakeven wire-up (POSITIONING: ⬆️⬆️ strongly positive)

**Date:** 2026-05-12 (SHIPPED; tag `v5.15.2`)

**Shipped:** trading_mode cfg field (PAPER/LIVE/SHADOW enum) stamp-bound via
FOREACH_STAMP_BOUND_CFG (every model carries training-time mode for audit trail).
NEW `CoreFrameworks/LiveReadiness.hpp` with FOREACH_LIVE_READINESS_CHECK X-macro
registry (9 entries: secret/mlockall/core_strategy/ml_model/model_age/feature_hash/
label_hash/build_flags/hmac_verified). aggregate_zoo_drift helper reads drift from
handle->drift_flags_at_load source-of-truth (NOT from PerCoreSnap.failure_flags which
isn't populated until snapshot publish AFTER pthread spawns; boot gate runs BEFORE).
LiveReadiness_Verify REFUSES on trading_mode=LIVE + any LR_SEV_REFUSE failure;
WARN-only on paper/shadow. breakeven_on_profit wired up (TECH_DEBT-024 close) via new
EventLoop_BreakevenOnProfit slow-path helper (mirrors trailing-SL OneCore/Wrapper
precedent; max-write composes cleanly with trailing-SL ratchet). `/readiness` Check 31
added (TECH_DEBT-033 close): verifies predecessor postmortem documents wider-build
GREEN result. Discovered `cfg.core_strategies_explicit_set` uint16_t bitmap already
existed at ControllerConfig.hpp:917 from v5.9.0c — no new tracking infra needed.

Cohort-audit verdict (per CLAUDE.local.md cohort-audit rule 2026-05-11):
trading_mode siblings = reconcile_mode + model_verify_strict; all 3 stay direct
uint8/int (enum-valued, NOT BIT_FLAG-eligible).

Tests 2940 → 2960 (+20 v5.15.2 anchor tests). Hot path UNTOUCHED. Slow-path cost:
trading_mode is boot-only; breakeven_on_profit ~80-150ns per active position per
cycle when bit set, ~1ns when bit unset; LiveReadiness_Verify ~10us boot-only.

**Change:** New `trading_mode` cfg field (uint8 enum) introduced;
LiveReadiness_Verify table-driven boot gate; cfg-default normalize pass;
TECH_DEBT-024 breakeven_on_profit wired.

**Decoupling positioning:**
- **`trading_mode` stamp-bound via FOREACH_STAMP_BOUND_CFG.** Future
  viewer can query "what mode was this model trained under?" without
  engine-internal state access. Surfaces as audit-trail field on the
  mmap'd stamp snapshot.
- **Pre-flight checklist is table-driven.** `kLiveReadinessChecks[]`
  static constexpr — future viewer can introspect "what does
  live-readiness check?" by reading the array. Could become a REST
  endpoint later (`GET /live_readiness`) without runtime changes.
- **Gate predicates are slow-path-cached** (per CLAUDE.md item 18(c)).
  Future viewer reading `gate_state.is_live` sees the cached predicate;
  no need to re-derive from cfg + state. Snapshot consumers get the
  derived predicate directly.

**Pattern established:** "table-driven gate checklists." Same pattern
could apply to engine boot gate, hot-swap pre-checks, retire-criteria
gate, etc. Future ships use the same `kFooChecks[]` shape.

**Anti-breadcrumbs:** none.

---

### v5.15.3 — Stamp_AssembleAndEmit helper + multi-horizon grid plumb + libgomp pthread-race close (POSITIONING: ⬆️⬆️ strongly positive; AMENDED 2026-05-12 post-audit)

**Date:** 2026-05-12 (SHIPPED; tag `v5.15.3` — amended after PARITY-021 root-cause reframe)

**Change (AMENDED):** `Stamp_AssembleAndEmit<F>` helper extracted from
RFV's existing emit chain at BacktestEngine.hpp:1039+ (refactor, not
new code); `train_model_worker_fn` switches to helper (PARITY-020 +
Class 18 mirror closed structurally); `FullValidationResults` plumbs
`req_grid_member_count/_idx/_horizon_count` (PARITY-021 close);
process-startup `setenv("OMP_NUM_THREADS", "1", 1)` at
foxml_suite.cpp:main() (CLAUDE.local.md landmine close); v5.11.45
forced-serial workaround REMOVED.

**Originally proposed but deferred to v5.16+ as TECH_DEBT-034:**
FOREACH_CLI_MODE X-macro registry, batch mode CLI infrastructure
(`foxml_suite --mode=...`), per-run logging structure
(`logging/foxml_suite/<run_name>/`), GUI button rewire to execv-spawn.
Speculative scope-creep based on misdiagnosed root cause (multi-horizon
DOES stamp via RFV; just missing grid_member_count population). Helper
extraction IS the proper structural prep for those future features.

**Decoupling positioning (AMENDED):**
- **Stamp_AssembleAndEmit helper IS the train_X_impl pure function**
  that future FOREACH_CLI_MODE (TECH_DEBT-034) will sit on top of.
  Single source of truth across train_model_worker_fn + RFV + future
  batch CLI entries. Pure function (no GUI dependencies; no shared
  state) → directly callable headless without refactor when v5.16+
  builds the CLI mode registry.
- **StampArgs POD struct with explicit default member init** —
  forward-compat for future field additions (CLAUDE.md item 27 padding
  determinism); future batch CLI can construct from cmdline args
  without conditional checks.
- **libgomp pthread-race close via process-startup setenv** unblocks
  parallel multi-horizon training (segfault landmine extinguished);
  enables future "run training on a different machine via SSH" — same
  binary can be invoked over SSH without code changes.
- **Class 18 mirror eliminated** at the stamp-emit boundary —
  train_model_worker_fn no longer asymmetric to RFV. Future ML cfg
  fields auto-flow to both callers via shared helper + AUTOPOPULATE.

**Pattern established:** "extract canonical assembly chain into pure
helper consumable by all callers (current GUI + future CLI/headless)."
The helper-extraction discipline IS the structural foundation for the
FOREACH_CLI_MODE work deferred to TECH_DEBT-034. Foxml_suite-side
decoupling proceeds via: (1) v5.15.3 — pure helpers extracted; (2)
TECH_DEBT-034 v5.16+ — CLI mode registry on top of helpers; (3) future
v5.16+ — GUI processes spawn execv children for training. Each step
inherits the prior step's structural readiness.

**Anti-breadcrumbs:** none. v5.11.45 forced-clamp workaround REMOVED
(was a temporary anti-pattern; replaced with proper structural fix).
Originally-proposed FOREACH_CLI_MODE / batch mode CLI / per-run logging
were SPECULATIVE scope on a misdiagnosed root cause — deferred to
TECH_DEBT-034 with the helper extraction as their structural precursor.

**Open design questions (DEFERRED to TECH_DEBT-034 design phase):**
- Per-run dir naming collision semantics (overwrite vs timestamp vs refuse)
- Progress file format (JSON vs plaintext)
- Cross-machine training cmdline interface (SSH wrapper vs runtime flag)

v5.15.3 doesn't need to answer these; helper extraction is the
precursor regardless of which answers ship later.

---

### v5.15.4 — Live-mode strict defaults + shadow-load hot-swap unification (POSITIONING: ⬆️⬆️ strongly positive; AMENDED 2026-05-12 post-audit)

**Date:** 2026-05-12 (SHIPPED; tag `v5.15.4` — amended after PARITY-023 fatal-flaw catch + design re-think)

**Change (AMENDED):** ControllerConfig_NormalizeForMode post-parse pass
flips strict defaults when trading_mode=LIVE; **shadow-load pattern**
replaces broken HotSwapSnapshot design (PARITY-023 caught fatal flaw —
captured pointers pointed at freed memory after the swap). Shadow-load:
`aligned_alloc(64, sizeof(T))` + load+validate into NEW allocation +
`__atomic_exchange_n` swap pointer + Free OLD state. Applied at BOTH
single-zoo + ensemble hot-swap sites. Plus `alignas(64)` retrofit on
EnsembleModelZoo + CoreModelZoo (latent alignment bug; member
ModelHandle alignas(64) + RidgeWeights AVX-512 alignment requests
unsatisfied with plain `malloc`). NEW DESIGN_SPEC:
`shadow-load-state-transition-pattern.md`.

**Decoupling positioning (AMENDED):**
- **Shadow-load pattern IS the canonical state-transition primitive.**
  Future state-exposure protocol (engine→viewer mmap'd snapshot) will
  use the same allocate-new + atomic-publish discipline. Same memory-
  ordering correctness; same lock-free reader access.
- **`aligned_alloc(64) + alignas(64)` discipline locked in.** Heap
  allocations satisfy member alignment guarantees; future mmap'd
  exposure can rely on cache-line layout being deterministic.
- **`__atomic_exchange_n` on pointer is THE primitive** for lock-free
  state swap. Future DoubleBufferedAtomic<T> template extraction
  (TECH_DEBT-035) builds on the same atomic ordering principles.
- **ControllerConfigKeyExplicit bitmap discipline** (uint16_t with
  named MASK_CFG_KEY_* constants) keeps cfg state mmap-friendly.

**Pattern established:** "shadow-load state transition" → captured in
DESIGN_SPECS/feature-patterns/shadow-load-state-transition-pattern.md as first-class
pattern (DRAFT v0.1 → ACTIVE v1.0 after v5.15.4 field-tests both
applications).

**DoubleBufferedAtomic<T> template extraction:** DEFERRED to
TECH_DEBT-035. Premature for v5.15.4 (HotSwap is single-owner; doesn't
need cross-thread double-buffer). BinanceDepth.hpp:80-89 stays as
canonical precedent for v5.16+ template extraction when engine→viewer
mmap shipped.

**Anti-breadcrumbs:** none. (Broken HotSwapSnapshot design from earlier
draft was caught + replaced BEFORE coding; never landed in repo.)

---

### v5.15.5.B — EventLoopState cache-layout sweep + 9 Class-18 mirror closures (POSITIONING: ⬆️⬆️⬆️ STRONGLY POSITIVE; foundational for mmap-mediated decoupling)

**Sub-ships:** `.B.1` through `.B.8` shipped 2026-05-13; tag `v5.15.5.B`
umbrella. Closes the EventLoopState side of the cache-layout discipline
that the decoupling sprint will inherit.

**Positioning rationale — why this is the SINGLE BIGGEST positive
breadcrumb for the future decoupling sprint:**

1. **Explicit `alignas(64)` cluster boundaries land at compile-time-
   enforced static_asserts on CoreContext + CoreSlowState + DisplayMeta +
   SlowPathTelemetry + WsHeartbeatTelemetry.** The decoupling sprint's
   shared-memory readers can carve out cache-line-aligned regions
   knowing the layout is locked. Without these, mmap-mediated GUI/engine
   separation would need to redo the alignment work + add `alignas`
   from scratch under unfamiliar coupling constraints.

2. **`CoreContextDisplayMeta` separation (.B.2) creates a NATURAL mmap
   region boundary.** Display-only fields now live on a sibling array
   `display_meta[MAX_EXECUTION_CORES]` on EventLoopState. Future
   decoupling: the GUI process can mmap THAT array read-only without
   pulling in the per-cycle decision state on `cores[]`. Pre-`.B.2`,
   display + decision were tangled — extracting them under decoupling
   pressure would have been a separate sub-sprint.

3. **`sp_telemetry` + `ws_telemetry` clusters (.B.2) ARE the cross-
   thread synchronization surface for the future.** These are the
   exact fields the engine writes that a separate GUI process would
   need to read at ~30-60 Hz. `alignas(64)` ensures the GUI process's
   reads don't cause cache-line ping-pong on engine's slow-path writes
   to neighbor fields. This is THE pattern the decoupling sprint
   inherits.

4. **`CORE_CTX_INIT_AUTOPOPULATE` (.B.7) shrinks the surface area
   that operates on EventLoopState pointer.** Future engine-process
   boot becomes registry-driven; the GUI viewer process doesn't need
   to know HOW the engine inits cores — just where the resulting
   shared-memory regions live.

5. **`ShardedSnapshot` loop fusion (.B.8) saves ~20 MB/s memory
   bandwidth at 60 Hz publish — bandwidth that's available for
   cross-process mmap operations** in the future decoupling.
   Inter-process shared-memory access goes through the same DRAM bus
   that the snapshot publisher uses; less GUI thread bandwidth =
   more headroom for the engine→GUI page faults + write-tracking
   when separated.

**Concrete decoupling implications:**

| Pre-`.B` surface | Post-`.B` surface | Decoupling readiness |
|---|---|---|
| Tangled CoreContext (display + decision in same struct) | Separate `cores[]` (decision) + `display_meta[]` (display-only) sibling arrays | Future GUI process can mmap display_meta read-only without touching cores[] |
| Implicit alignment via `alignas(64)` on `CoreLatencyStats` (transitive) | Explicit `alignas(64)` on `struct CoreContext` + `static_assert(sizeof%64==0)` + cluster anchor offset asserts | Layout is locked; viewer process can rely on struct shape stability |
| Cross-thread atomics scattered in CoreContext (sp_*) + EventLoopState (ws_*) | `SlowPathTelemetry` + `WsHeartbeatTelemetry` clusters each on own cache line via alignas(64) | Cross-process read traffic on these clusters is cache-line-bounded |
| 4 snapshot publisher walks burning ~26 MB/s bandwidth | 1 fused walk burning ~6.5 MB/s | More bandwidth headroom for the future engine→GUI mmap write-tracking |
| ~50 LOC manual init loop body per slot + ~16 LOC manual reset | One-line `CORE_CTX_{INIT,RESET}_AUTOPOPULATE` call per slot | Registry-driven; can hoist into shared init for headless engine process |

**Updates to readiness checklist (later in this doc):**

- ✅ Engine-side state structs have explicit cache-line alignment
   (was previously "TBD")
- ✅ Display-only fields separated from decision fields on EventLoopState
   (was previously "TBD")
- ✅ Cross-thread atomic clusters identified + alignas-isolated
- ✅ Snapshot publisher consolidated to single walk (positions for
   mmap-mediated zero-copy GUI in future)
- ⏳ STILL TBD: actually expose `cores[]` / `display_meta[]` via mmap
   shared-memory region. Pre-decoupling: works in-process. Post-
   decoupling sprint: viewer process mmap's the regions read-only;
   engine continues writing locally. The `.B` layout work means this
   becomes a CONFIG flip + small ipc wrapper, not a refactor.

**Anti-breadcrumbs:** none. Caramel pushed for 100% closure on `.B.7`
(vs 95%) precisely to avoid leaving anti-breadcrumb residue ("smaller
scope" deferral that would have left the slow_state arena allocator +
sibling-struct init at the call site, complicating future decoupling).

The `.B` sub-sprint is the model for how downstream sub-sprints (`.C`
OrderManagerState, `.D` FlowFeatures, `.E` ConfidenceScorer) should
unfold — registry-driven structural closures that make EACH sub-sprint
a positive decoupling breadcrumb.

---

### v5.15.5.C — OrderManagerState cache-layout sweep + bit-packing + wire-format registry (POSITIONING: ⬆️⬆️⬆️ STRONGLY POSITIVE; structural parallel to `.B` on the OMS side)

**Sub-ships:** `.C.1` (commit `945feb4`, tag `v5.15.5.C.1`) + `.C.2` partial S6
(commit `ccf7e4e`) + `.C.2` close (commit `852a6e3`, tag `v5.15.5.C.2`) +
`.C.2.1` fixup (commit `097f91f`, tag `v5.15.5.C.2.1`). Shipped 2026-05-13.

**Positioning rationale — why `.C` is foundational for mmap-mediated
OMS exposure:**

1. **OrderManagerState HOT/WARM/COLD cluster reorg (`.C.1`)** with
   compile-time-locked anchors (`result_queue`, `portfolio`, `adapter`,
   `total_submitted`, `flatten_pending`, `ks_min_balance`) on 64-byte
   boundaries. The future GUI process can mmap the OMS struct
   read-only knowing the layout is stable; no struct walking, no
   header re-parsing.

2. **Cross-thread atomic clusters isolated** (`.C.1`):
   `total_submitted/filled/rejected` (observability counters, drainer
   writer + snapshot publisher reader at 60 Hz) and `flatten_pending +
   recovery_until_us` (safety CAS, N slow-path writers + drainer
   reader) each on own cache line via `alignas(64)`. Same ND1 pattern
   as `.B.2` — the cross-process synchronization surface for future
   decoupling is now pre-isolated.

3. **`FOREACH_OMS_PERSIST_FIELD` wire-format registry (`.C.2`/S3a-W)**
   makes the snapshot persist BLOCK registry-driven. The same registry
   that drives engine save/load can drive an EXTERNAL viewer's
   deserializer. Viewer-side schema cache becomes possible without
   re-parsing C++ headers — same pattern as `.B`'s
   `FOREACH_STAMP_BOUND_*` for stamp body. Cross-version compat
   preserved via type+kind tuple shape.

4. **`oms_state_flags` uint8_t bitmap (`.C.2`/S3a)** + `last_exit_
   predicted_bitmap` uint16_t (`.C.2`/S3b) + `last_exit_predicted_
   meta` per-slot uint8_t (`.C.2.1`/LOW-2) compact the OMS state from
   ~50 bytes of byte-per-flag + array-per-attribute to ~3 packed
   words. The mmap exposure region for OMS state shrinks
   proportionally — viewer process can pull the full OMS-decision
   snapshot in a single cache line touch.

5. **FIRST APPLICATION of `multi-bit-state-encoding-pattern.md`
   (`.C.2.1`/LOW-2)** — `MemHeaders/OmsExitPredictorMetaRegistry.hpp`
   field-validates the pattern (regime + arm + valid in 1 byte;
   parallel decode via ILP at consumer). Future K-state fields
   (regime_state, strategy_id, halt_reason) inherit a tested
   substrate; the codebase-audit follow-up (TECH_DEBT-041) becomes
   "1 row per candidate" not bespoke per-field design.

6. **Wire-format byte-preservation discipline upgraded (`.C.2`/S3a-W)**
   via `OMS_PERSIST_SAVE_VAL_BIT(name, mask)` — bit-extracted as 4-byte
   int at save, bit-set at load commit. Snapshot version unchanged.
   This proves the pattern of "in-memory bit-pack + wire-format-
   stable int-emit" works for future decoupling protocols that need
   compact in-memory state + stable IPC wire encoding (the GUI
   process might consume a different in-memory representation than
   the engine's).

**Concrete decoupling implications:**

| Pre-`.C` surface | Post-`.C` surface | Decoupling readiness |
|---|---|---|
| OrderManagerState scattered HOT/COLD interleaved | Explicit HOT/WARM/COLD clusters w/ 6 offset-locked anchors | Viewer process can mmap with stable offsetof() |
| OMS save/load = 30+ hand-written fwrite/fread lines | `FOREACH_OMS_PERSIST_FIELD` registry-driven (3 FOREACH calls) | External viewer reuses same registry for deserialize |
| OMS state = 3 byte-per-flag + 2 per-slot byte arrays (~80 bytes) | 1 uint8_t + 1 uint16_t + 1 uint8_t[16] (~19 bytes) | OMS snapshot region shrinks 4× for mmap exposure |
| Per-slot exit-predictor = 2 int8_t arrays (32 bytes; -1 sentinels) | 1 packed uint8_t array (16 bytes; valid-bit) | Compact wire format + parallel decode in viewer |
| No design substrate for multi-bit state encoding | `multi-bit-state-encoding-pattern.md` + first application | Future K-state fields apply pattern by-row, not by-spec |

**Updates to readiness checklist (later in this doc):**

- ✅ OMS save/load format is registry-driven (was previously "TBD"; now
  `FOREACH_OMS_PERSIST_FIELD` covers all persisted OMS fields)
- ✅ OMS state is compact + bitmap-encoded (was previously "TBD"; now
  ~75% reduction in OMS-state byte count)
- ✅ Multi-bit state encoding pattern has design + first application
  + going-forward rule (was previously "no design substrate"; now
  fully established)
- ⏳ STILL TBD: actually expose OMS state via mmap. Pre-decoupling:
  works in-process. Post-decoupling: viewer mmap's snapshot region
  read-only. The `.C` cluster reorg + registry + bit-packing means
  this is a CONFIG flip + IPC wrapper, not a refactor.

**Anti-breadcrumbs:** none. Caramel pushed for full closure of all 4 audit
findings (MEDIUM-1, MEDIUM-2, LOW-1, LOW-2 + INFO test gap) plus FIRST
APPLICATION of the multi-bit pattern in the `.C.2.1` fixup — same
"headache now > issues later" discipline as `.B.7` AUTOPOPULATE 100%
closure (vs 95% deferral).

**The `.C` sub-sprint extends `.B`'s model to the OMS side and adds the
multi-bit state encoding substrate** that downstream sprints (`.D`
FlowFeatures, `.E` ConfidenceScorer, future v5.16 regime cohort
migration) inherit. Both `.B` and `.C` together = positive positioning
breadcrumb for both halves of the EventLoopState↔OrderManagerState
struct boundary that the decoupling sprint will read across.

---

### v5.15.5.F.4d.1.B.3 Phase L — `tools/stamp_model_cli.cpp` replaces `tools/stamp_model.sh` (POSITIONING: ⬆️⬆️⬆️ STRONGLY POSITIVE; first framework-driven CLI binary)

**Date:** 2026-05-18 (PLANNED at v1.14 plan body amendment; SHIPS at `.B.3` tag)

**Shipped (planned):** NEW `tools/stamp_model_cli.cpp` framework-driven C++ CLI binary
replaces `tools/stamp_model.sh` (716 lines of bash; 6+ cross-tool sync events documented
in script header across v5.2.3 / v5.8.8 / v5.9.3b / v5.9.4a / v5.9.5c / v5.11.18a + `.B.3`).
Thin wrapper (~150-200 LOC) over `stamp_write_for_model` framework API; CLI flag
interface matches bash for operator workflow continuity (per
`feedback_surface_operator_migration_path_proactively`); deprecation shim at
`tools/stamp_model.sh` (1-line `exec` redirect) preserves invocation patterns during
retention period (TECH_DEBT-110 tracks shim deletion). Closes Class 18 + 19 + 21 + 22
at cross-tool surface via structural elimination (drift impossible by construction).
NEW DESIGN_SPEC `framework-driven-cli-binary-pattern.md` Stage 2 DRAFT at workspace;
Stage 3 first canonical reference = this binary.

**Change:** Bash script (mirror of engine wire emit logic) → C++ CLI binary (uses
engine framework API directly). Cross-tool seam structurally eliminated for stamp
model workflow.

**Decoupling positioning:**

- **First canonical of `framework-driven-cli-binary-pattern.md`.** Pattern provides
  structural elimination for cross-tool surfaces that mirror engine wire emit. The
  pattern is reusable for FUTURE cross-tool surfaces (e.g., schema migration CLI;
  per-core override emission CLI; per-core overlay-bytes consumer if needed). Each
  future cross-tool surface that fits the pattern can apply structurally instead of
  accumulating Layer 7 discipline overhead.
  
  **STATUS UPDATE 2026-05-24 / 2026-05-27 PM:** Phase L first canonical REVERTED
  per YAGNI 2026-05-24 (foxml_suite already stamps models in-process; CLI was
  edge-case-only infrastructure). Both `tools/stamp_model.sh` AND draft replacement
  `tools/stamp_model_cli.cpp` DELETED. Pattern Stage 2 DRAFT retained as spec
  body. `.C` per-core override emission CLI also SKIPPED at 2026-05-27 PM post-`.B.8`
  pickup re-scope per same rationale + operator confirmation. Stage 4 cohort
  migration deferred to v5.16+ FOREACH_CLI_MODE registry (TECH_DEBT-034) alignment
  per "Training entry points" axis section below. Future cross-tool surfaces still
  candidates for pattern application post-FOREACH_CLI_MODE landing. See
  `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md` v1.1
  § "Pattern status update (2026-05-24)" + CLAUDE.local.md going-forward rule
  "Framework-driven CLI binary pattern Stage 4 cohort migration deferred to
  v5.16+ FOREACH_CLI_MODE" (2026-05-27 PM) for canonical rationale.

- **"Training entry points" axis advanced** — Phase L is a precedent for the
  FOREACH_CLI_MODE registry's eventual instantiation. `tools/stamp_model_cli.cpp`
  is the SECOND C++ tool in `tools/` (after `compare_scalers.cpp`) + first
  framework-driven C++ tool. The build-system pattern (CMake target alongside
  engine/engine_gui/foxml_suite) generalizes for FUTURE CLI binaries — e.g.,
  `tools/dump_stamp_schema_cli.cpp` (planned for decoupling sprint per v5.15.0
  breadcrumb).

- **Cross-tool wire-format mirror eliminated for stamp body surface.** Layer 7
  discipline (cross-tool emit-site enumeration) is OBVIATED at this specific surface.
  Future wire-format changes (SOFT or HARD version bumps) propagate through
  framework to CLI automatically; no cross-tool sync work. **Reduces decoupling-sprint
  work** — viewer-side stamp consumer can rely on stable engine-side wire emit
  without worrying about bash-side drift causing forward/backward compat issues.

- **Decoupling-friendly CLI invocation pattern.** The C++ CLI is invokable via
  `execv` (matches FOREACH_CLI_MODE pattern); a future GUI viewer can spawn the CLI
  as a child process for offline stamp signing without coupling to engine runtime.
  Builds on the v5.15.3 "Training entry points" decoupling vector.

- **Wire format byte preservation inherited from framework.** CLI uses
  `populate_stamp_cfg_from_derived` via `stamp_write_for_model` — same locale pin
  (LC_NUMERIC=C), same %.17g precision, same tt::cfg_emit_field<T> path. **HMAC chain
  byte-identical** between engine in-process emit and CLI emit by construction.
  Viewer-side HMAC verification works against both sources without distinction.

**Pattern established:** "Framework-driven CLI binary replaces bash mirror." Reusable
for ANY future cross-tool surface where the engine has a single-source-of-truth API
(stamp body / snapshot body / scaler body / model overlay body / etc.). Sister to the
v5.15.3 FOREACH_CLI_MODE registry pattern (which decouples training entry points; this
pattern decouples cross-tool wire emit).

**Anti-breadcrumbs:** none. Phase L is purely additive at the cross-tool surface
(replaces bash with C++; preserves operator flag interface via deprecation shim;
preserves wire format byte-for-byte; HMAC chain verifies bash-stamped legacy models
on engine via Decision F SOFT compat parser).

**Cross-references:**
- `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md` (NEW Stage 2 DRAFT)
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` § Layer 7 (cross-tool
  emit-site enumeration discipline — Phase L OBVIATES Layer 7 at this specific
  surface)
- `subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` Decision G + Step 1.6.8'
- `feedback_no_defer_for_effort.md` (caught my initial `.B.4`-split-as-deferral)
- `feedback_motivated_collaborator_for_caramel.md` (best-software discipline)

---

## Eventual display-truth items — 2026-08-14 operator spot-check cohort (PLAN items, deliberately NOT TECH_DEBT per operator directive)

> Operator live-dogfood findings during the E.1.2 pickup paper session, investigated by a 2-agent
> I-class pass the same evening. **Verbatim evidence + full site maps:**
> `plans/v5.15-live-readiness/reports/2026-08-14-ui-position-settings-mismatch/`
> (`i-class-positions-legcount-attribution.md` + `i-class-settings-registry-display.md`).
> Both items are display/monitoring-plane, E.1.2-persist-entanglement-verified CLEAN, and are
> INSTANCES under existing patterns — no new spec owed. Homed HERE per the auto-write contract
> (GUI ↔ runtime / TUISnapshot / cfg-ownership plane). These NEED to be addressed; a plan home
> (not a ledger) is the point.

### EV-1 — Pair/leg unit coherence + counter-family SSoT (the "2 legs shown as 2 positions" cohort)

- **Mechanism (confirmed):** one paired entry bumps `entries_processed` twice (per-fill doctrine, correct);
  `ShardedSnapshot.hpp:500-502` derives the per-node "open positions" display from `entries − exits` (→ 2)
  while the header pair-collapses the bitmap `(bm|bm>>1)&0x5555` (→ 1). Two planes disagree by construction.
  Full 16-site enumeration with per-site LOGICAL-PAIRS / SLOTS / MIXED verdicts in the report § 2.
- **Also in the cohort:** Stats-bar zeros on warm-restart (global `total_entries/total_exits` heartbeats are
  the ONE counter family neither persisted in v10 nor rebuilt by the replay reconstructor — report § 5;
  cleanest fix = re-source the stats plane from the persisted per-node sums, no wire change) · backtest
  `total_trades` double-count under partials (S14) · Stats `buys/2` truncation on half-pairs (S15) ·
  TUI/Run mixed-unit labels (S7/S8) · replay-vs-live W/L pair-parity divergence (A6,
  `ControllerEventLoop.hpp:1053-1055` per-leg vs `:1815-1847` per-pair) · **A8 live display bug:**
  Positions-row strategy palette `sc[]` missing the AUTO entry → OOB read when an AUTO node holds a
  position (`DashboardPanels.hpp:1401-1410`; the Header sibling was fixed at `:237-244`, Positions copy
  missed — Class-18 mirror; QUICK-KILL eligible any session).
- **Fix shape (locked by the I-pass option matrix; implement at the leaf):** O1 pair-aware geometry
  helpers (`Sharded_LogicalOpenCount` + `Sharded_NodeAnyOpen` joining the `Sharded_LegSlot`/`Sharded_SlotNode`
  family) + O4 unit-typed snapshot contract (PerNodeSnap carries `node_open_legs` AND `node_open_trades`;
  viewers stay geometry-dumb — the decoupled-viewer shape). `// SLOT-COUNT-DELIBERATE` tags on the 5
  legitimate slot-count sites (S3/S9/S10/S11/S12). O2 (new persisted counters) REJECTED — Class 43 + wire
  entanglement.
- **Spec sisters (instances-under-existing-patterns):** Class 2 (GUI-lie) · Class 43/45 SSoT family ·
  `decision-time-data-binding-pattern.md` · `cross-thread-snapshot-publish-cluster-isolation.md` ·
  `built-in-observability-pattern.md` · `per-node-position-ownership-model.md` (pair semantics; its future
  sub-pool note is why the collapse must live in ONE helper — per-node partial-enable would flip it) ·
  `DOCS/EXECUTION_DISPLAY_INVARIANTS.md` gains the unit rows at fix time.
- **Attribution/other-stuff dispositions from the same session:** leg-B "higher buy price" =
  EXPECTED (TP2 ratchet, `tp2_mult` default 2.0 — no code path gives leg B a different paper ENTRY;
  report § 6) · "MR shown as MOM/EMA" = **REPRO ANSWERED (operator screenshot, same evening): the
  CHART GATE-LINE TAGS** — other nodes' labeled gate lines (`C1 EMA`, `C3 MOM`) float at price levels
  adjacent to node 0's position markers with no visual linkage between a marker and ITS node's line
  (`ChartPanel.hpp:1226-1231`); the leaf's fix = link markers↔lines visually (match tint / draw the
  pair, or tag markers with their own node id). Plus 3 genuine AUTO-mode display defects to fix at
  the leaf: PerNodePnL bare resolved-now labels (`DashboardPanels.hpp:1690-1693`), node-0-only
  headline strategy (`ShardedSnapshot.hpp:364-377`), TUI binary strategy collapse
  (`EngineTUI.hpp:2234-2239`).
- **NEW lane (operator, same evening): per-leg budget/Value presentation.** Observed: with a pair on,
  each leg appeared to "consume $125" (the node's full allocation) rather than the ~50/50 split; the
  positions screen itself looked right. **Submit-side sizing VERIFIED CLEAN at HEAD** (orchestrator
  code-read: `Async.hpp:826-882` — the loop var is the NODE index, `intended_qty` node-indexed, split
  applied legA=`full×pct` / legB=`full×(1−pct)`, zero-qty leg skipped by the `>0` gate at `:888`) —
  so no capital double-spend path; this is a DISPLAY/budget-presentation lane. Candidates at the leaf:
  the Value column basis, the per-node budget tooltip source (`node_open_notional` vs allocation),
  and the half-pair shape (leg-B qty 0 via `partial_exit_pct` resolution → submit skipped → lone
  full-size-looking #0.A). Pin the operator's cfg `partial_exit_pct` at repro.
- **QUICK-KILLED same evening (2026-08-14, ahead of the leaf):** A8 Positions-row `sc[]` AUTO palette
  entry + static_assert (mirrors the Header fix) · the EV-2 D-1 stale `confidence_freshness_tau`
  per-node row DELETED from `per_node_fields[]` (stops NEW poison writes; operator's engine.cfg
  verified CLEAN of the key; the parity GUARD tool + the rest of EV-2 remain owed) · **D-9 UPGRADED
  latent→LIVE and fixed:** the operator's engine.cfg (16,962B) had crossed `cfg_write_field`'s 16KB
  buffer — any settings edit would have silently truncate-rewritten the file tail, and the rewrite
  path also carried a latent unbounded-suffix stack smash; now 64KB static buffers + loud REFUSE
  (never truncate) + total-bounds check (`SettingsPanel.hpp` cfg_write_field).
- **Mechanical stale-record corrections to sweep at the leaf:** `ShardedSnapshot.hpp:498-499` comment ·
  `EngineTUI.hpp:1290` comment · D-295's "4 GUI sites" tally (now 9 shapes — name-members rule).

### EV-2 — Settings per-node render completion (the .F.4c.3 Step-6 remainder) + the D-1 boot-brick guard

- **Ground truth:** the engine registries are ALREADY split (H17; `FOREACH_PER_NODE_CFG_FIELD` 88 rows /
  `FOREACH_GLOBAL_CFG_FIELD` 59 rows) and the per-node render TABLE already exists
  (`SettingsPanel.hpp:265-300`) — but it renders into the GLOBAL tab writing FLAT keys (the .F.4c.3
  Step-1 transitional state), while the per-core tabs still run the pre-registry manual
  `per_node_fields[]` (43 float rows). The operator's "per-node settings should be a different registry"
  is the UNSHIPPED REMAINDER of the locked `.F.4c.3` plan
  (`subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md` Step 6) — re-plan by
  reference, not new architecture.
- **⚠ URGENT sub-item (operator to route — capital-adjacent operational hazard, flagged same-evening):**
  **D-1 boot-brick:** the per-core tab still renders the RETIRED `confidence_freshness_tau` row
  (`SettingsPanel.hpp:777`, writer `:1933-1940`); one edit writes `node_N_confidence_freshness_tau=` into
  engine.cfg → `CFG_FAULT_UNKNOWN_KEY` → **next boot HARD-REFUSED** until hand-deleted. TECH_DEBT-208's
  claimed containment (parity tool + row deletion) NEVER LANDED at HEAD. The O-1 leaf = delete the row +
  build `check_gui_engine_cfg_key_parity.py` (GUI-writer-keys ⊆ parser-keys, with teeth) — small,
  independent, recommended NOW-tier rather than eventual.
- **The eventual leaf proper (O-2):** per-core tabs walk `g_per_node_cfg_render_mask` bound per-node
  (write `node_N_<name>` pre-WIP2f); per-node walk OUT of the Global tab (kills the D-2 silently-inert-edit
  display-lie on override-carrying nodes); delete `per_node_fields[]` + the 8 D-3 double-rendered manual
  twins; inherited-vs-override display per row (D-6 — the promised grey hint that never existed); section
  contiguity (D-4 — "Trading" currently appears as 5 same-label CollapsingHeaders). Blast radius: GUI-only
  + registry-comment reorder; no parser/wire change. Full defect table (D-1..D-10) in the report § 4.
- **Sequencing guards:** the `[core N]`/`[section]` cfg parser stays homed E.1.6/E.2 (D-275/D-276) — the
  leaf consumes it if it lands first, else ships `node_N_` writes; TECH_DEBT-191 flat-field deletion and
  WIP2f/g stay where the A24 decision homed them. NOT `v5.15.6-master-cfg-surface-unification` (that is
  cfg-FILES scope; cross-link only — its "operator never hand-edits cfg" goal DEPENDS on this leaf).
- **Mechanical stale-record corrections to sweep:** `SettingsPanel.hpp:1348-1349` (section-grouped claim
  FALSE) · `:1438-1439` (grey-hint claim FALSE) · TECH_DEBT-208 body (claims the guard+row-delete landed —
  neither exists at HEAD) · `cfg-scope-discipline.md:253` ("ResolveForCore deleted at WIP2f" — never landed).

---

## Pre-decoupling readiness checklist

Updated after each ship's breadcrumb is added. When all checked, the
decoupling sprint can proceed cleanly.

### foxml_suite side
- [ ] All training paths cmdline-invocable via FOREACH_CLI_MODE
      (v5.15.3 covers train_horizon, train_single, train_multi,
      run_full_validation; add walk_forward + collect_multi_horizon
      in future ship)
- [ ] Per-run state fully externalized to disk
      (v5.15.3 covers per-horizon progress + logs; add per-run cfg
      snapshot + per-run results.json in future ship)
- [ ] GUI process separation from runtime
      (v5.15.3 partial — GUI button spawns child but GUI itself still
      contains runtime entry points. Full separation = remove
      in-process training; GUI becomes pure shell-spawn + file-poll)
- [ ] Multi-viewer support
      (per-run dirs make this "free" for read-only viewers; multi-
      WRITER would need exclusive-lock semantics)
- [ ] Reconnect tolerance
      (filesystem-based state survives viewer disconnect; tested
      via "kill GUI, restart, run still running, GUI re-attaches")

### engine side
- [ ] TUISnapshot durable mmap'd region
      (today: in-process double-buffer; endgoal: mmap'd region with
      versioned schema)
- [ ] State-exposure protocol versioning
      (snapshot schema version + viewer compatibility check)
- [ ] Engine binary headless service
      (already mostly there — `./engine` runs with TUI; needs systemd
      unit + viewer attachment surface)
- [ ] engine_gui as separate viewer process
      (today: engine_gui = engine + ImGui in same process; endgoal:
      separate ./bin/engine_viewer that mmap-reads engine's snapshot)
- [ ] Trade log structure stable for viewer consumption
      (today: order_history.csv + paper_runs/; endgoal: stable schema
      + tailable + machine-parseable)

### Cross-cutting
- [ ] Stamp body format versioning + viewer compatibility
      (already preserved via MODEL_FORMAT_VERSION + Surface G has_*
      flags; verify viewer reads gracefully across versions)
- [ ] Cfg layer ownership — runtime vs viewer
      (decision: runtime owns; viewer has its own display-only cfg)
- [ ] Logging path discipline
      (v5.15.3 establishes per-run for foxml_suite; engine side needs
      analogous per-session structure)

---

## Open design questions (running TBD list)

These accumulate from ship breadcrumbs above + open thinking. Resolve
before or during the decoupling sprint.

### State exposure protocol
- mmap region vs Unix domain socket vs both? (Lean: mmap for hot
  snapshot reads; socket for command-channel + reconnect handshake)
- Versioning scheme — semver in schema header? Tagged-union for
  forward-compat? (Lean: schema_version field + has_* forward-compat
  flags, mirroring stamp body Surface G discipline)
- Read-only vs read-write viewer? (Lean: read-only; writer privileges
  via authenticated socket command-channel only)

### Multi-viewer concurrency
- Lock-free for mmap reads (already the TUISnapshot pattern; just
  needs durable backing)
- Per-viewer connection state on engine side? (Lean: stateless;
  engine doesn't track viewers; viewer maintains its own connection)

### Engine boot under headless
- systemd unit file template? (yes; private to operator's deployment)
- cfg path discovery — env var, /etc/foxml/?, CLI arg? (Lean: CLI
  arg with /etc/foxml/engine.cfg as default)
- Pidfile / port lock / mmap region path conventions?

### Viewer process
- Pure ImGui? TUI? Both? (Lean: keep both shapes; same backend, just
  different render paths)
- Discovery — how does viewer find engine's mmap region? (Lean: well-
  known path under /var/run/foxml/<instance_name>/snapshot.mmap)
- Reconnect semantics — keep last-known state on disconnect, retry?

### Cross-cutting
- HMAC stamp body byte-format stability across engine versions —
  test infrastructure for this? (Lean: CI runs old-stamp-on-new-engine
  + new-stamp-on-old-engine compatibility matrix)
- Audit trail — what's "the canonical record" of a trading session
  post-decoupling? Engine's per-session log? Snapshot history?
  Trade history? (Lean: trade history file is canonical; everything
  else is derivable)

---

## Anti-breadcrumbs (changes that would CONFLICT with decoupling)

Empty so far. As ships happen, if any change would CONFLICT with the
endgoal architecture (e.g., adds in-process-only state that can't be
mmap-exposed), capture it here + redirect at design time.

**Examples of what would go here if it happened:**
- "v5.X.Y added a callback registry where GUI registers fn pointers
  into engine — this CONFLICTS with separate-process viewer because
  fn pointers can't cross address spaces. Redirect: GUI uses
  filesystem-based event subscription instead."
- "v5.X.Y added in-process mutex protecting Y — CONFLICTS with mmap'd
  exposure. Redirect: use atomic seqlock instead."

---

## Cross-references

- **Companion v6.0 doc:** `plans/_future/2026-05-08-v6.0-CANDIDATE-headless-service-colo.md` (engine-side decoupling specifically; this doc adds the suite side + the running breadcrumbs)
- **Going-forward rule:** CLAUDE.local.md "Going-forward rule: decoupling-endgoal positioning at each fix" (set 2026-05-12)
- **First seeded by:** v5.15 sprint planning session 2026-05-12
- **Patterns established by:**
  - v5.15.0 — X-macro stamp body + bit-packed has_flags (mmap-friendly wire format)
  - v5.15.2 — table-driven gate checklists (introspectable + RESTable)
  - v5.15.3 — FOREACH_CLI_MODE registry (the extensibility surface itself)
  - v5.15.4 — atomic capture/validate/publish/revert (state-transition pattern)
  - **v5.15.5.F.4d.1.E.1.1 ③ (D-255) — capital-cfg validation at EVERY re-config seam.** The config-compiler converged on a single-source gate (`cfg_capital_gate_ok`) wired into the boot + backtest paths (item 1 LANDED `c6967be`), with the **live hot-reload gate** (`Async.hpp:321` keep-old-on-fault) + GUI-parser validation as remaining ③ items. Load-bearing for the decoupled runtime: a headless engine re-reads cfg on a control-plane signal (the decoupling endgoal), so EVERY decoupled re-config must inherit the gate — a malformed/out-of-range capital value can never enter a *running* engine via the control channel. The boot gate alone is insufficient once the runtime is headless + re-configurable (the `[section]` parser + `config_error_log` FILE are the E.2 continuation, homed there).
