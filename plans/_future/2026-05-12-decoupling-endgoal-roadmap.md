# Decoupling endgoal roadmap — runtime / viewer separation (PRIVATE living doc)

**Date opened:** 2026-05-12 (v5.15 sprint kickoff session)
**Status:** LIVING DOC. Accumulates per-ship breadcrumbs.
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

**Date:** 2026-05-12 (amended after PARITY-023 fatal-flaw catch + design re-think)

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
DESIGN_SPECS/shadow-load-state-transition-pattern.md as first-class
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
