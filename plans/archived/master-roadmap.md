# Master Roadmap — post-v4.0.3 → first real-money trade

**Created:** 2026-04-26 (overnight, after v4.0.3, after Plan Review Checklist
codification in CLAUDE.md, after Track E was identified as the principled fix.)

**Purpose:** single document that orders every pending work-stream in the
trading-suite repo and applies the CLAUDE.md "Plan Review Checklist" to
each. Replaces the ad-hoc "what's next?" conversation that has been
happening in chat.

**Update protocol:** edit this file when a plan ships, when a new plan
is added, or when an audit verdict changes. Pickup notes
(`plans/YYYY-MM-DD-pickup*.md`) reflect *yesterday's session*; this file
reflects the *whole arc*.

---

## Status snapshot (2026-04-26)

- **Sharded engine:** production. v4.0.3 shipped twelve features ported
  from legacy. Hot path 40-400ns p99, branchless+masked+FPN.
- **Legacy `PortfolioController`:** kept for backtest training generation
  + benchmark; runtime-warns at startup; **explicitly deprecated** for
  live use (Jenn 2026-04-26: "we can ignore legacy functionality...
  sharded version is up to date enough").
- **Live-trading infra:** complete (kill switch, OMS, paper/live sync,
  depth recording, alerting, snapshot v8). Architecturally ready.
- **ML pipeline:** end-to-end working. `CoreModelZoo` with 4 roles.
  `ConfidenceScorer` per core. **Edge not yet found** — v4.3 features
  did not unlock medium-horizon prediction; 0.050/1000 binary remains
  the only configuration with statistical lift.
- **Drift risk:** sharded vs legacy backtest features can diverge
  silently. `Regime_ComputeSignals` is the single source of truth, but
  the *callers* must populate equivalent state. Cadence (poll_interval
  vs slow_path_interval) realigned in v4.0.3 F2; deeper unification
  pending Track E.

---

## Active focus

**Sequence the user has confirmed:**

1. ✅ **Track E** — sharded backtest unification (E.1-E.7 all shipped
   2026-04-26). Absorbed D.5. Sharded is the only backtest path;
   `Backtest_Run` is a thin wrapper around `BacktestSharded_Run`.
   Net deletion: ~250 LOC. controller_test 544/544. Tags on origin:
   `pre-track-e`, `pre-track-e-polish`, `pre-track-e3`, `pre-track-e7`
   + four `backup/pre-track-*` branches.
2. **D.2** + **D.4** — train-serve-safe feature additions, queued behind E
3. **D.1** + **D.3** + **D.5 follow-on** — depth-derived features
   *unlocked* by E (currently blocked because backtest doesn't replay depth)
4. **C.3** — maker-only execution (1-2 weeks, the big lift)
5. **Phase 1 polish** — Stats/Positions/Trade-History per-core surfacing
6. **ANSI TUI deprecation** + **stale TUISnapshot field cleanup**
7. **FoxLIB catch-up** — push relevant updates to public mirror
8. **Partial exits to sharded** (architectural — see below)
9. Speculative: multi-asset, per-core charts, replay mode

---

## Plan inventory + checklist verdict summary

For each plan: status (DONE / ACTIVE / QUEUED / DEFERRED / RESEARCH /
ARCHIVED) and a one-line verdict from the Plan Review Checklist.
Drilldown is below.

| Plan | Status | Hot path | Train-serve | Surface area | Overall verdict |
|---|---|---|---|---|---|
| sharded-completion-plan.md | **DONE** (47/47 in tasks) | PASS | PASS | PASS | **ARCHIVED** |
| live-readiness-master.md | **DONE** (Phase 5-8 shipped) | PASS | PASS | PASS | **ARCHIVED** |
| ml-inference-harness.md | **DONE** | PASS | PASS | PASS | **ARCHIVED** |
| phase5d-* | **DONE** | PASS | PASS | PASS | **ARCHIVED** |
| phase6-prep-confidence-loop | **DONE** | PASS | PASS | PASS | **ARCHIVED** |
| phase7-prep-validation-infrastructure | **DONE** | PASS | PASS | PASS | **ARCHIVED** |
| phase8a-depth-recorder | **DONE** | PASS | PASS | PASS | **ARCHIVED** |
| phase8b-operational-monitoring | **DONE** | PASS | PASS | PASS | **ARCHIVED** |
| phase8-maker-taker | **DONE** | PASS | PASS (accepted divergence) | PASS | **ARCHIVED** |
| **track-e-sharded-backtest.md** | **SHIPPED 2026-04-26** (E.1-E.7) | **PASS** (1ns hot-path mask added in E.3) | **FIXED — sharded ↔ sharded ML parity confirmed** | **net-deletion (~250 LOC)** | **DONE** |
| post-edge-hunt-c-and-d.md | **REVISED** (2026-04-26) | mixed (C.3 has hot-path) | mixed (D.1/D.3 blocked on E.3) | medium | **OK — sequencing aligned with Track E** |
| post-v4.0-followups.md | **ACTIVE — backlog** | LOW (mostly GUI) | PASS (no feature changes) | LOW | **OK as backlog; some items need their own plans** |
| ml-training-roadmap.md | **RESEARCH** | n/a | n/a | n/a | **OK — research notes, not a work plan** |
| learn-ml-zoo.md | **RESEARCH** | n/a | n/a | n/a | **OK — self-study notes** |

---

## Discovery from this audit

**`Backtest/BacktestSharded.hpp` already exists** as a Phase 13 stub
(377 LOC, dispatched from `Backtest_Run` when `engine_mode=sharded`
AND `collect_features=0`). Track E is **not** "build from scratch" —
it is "finish + adopt as default + delete legacy." Specifically:

- ✅ Replay loop, tick conversion, RollingStats wiring, OMS init —
  all present.
- ✅ Strategy gate currently SimpleDip-only — easily extended.
- ❌ No feature collection (this is the load-bearing piece).
- ❌ No regime / gate-reason diagnostics.
- ❌ Walk-forward / `Backtest_RunWalkForward` still uses legacy.
- ❌ `Backtest_RunSweep` (optimizer) still uses legacy.
- ❌ No depth replay (D.5).

This shrinks Track E from "rewrite the whole backtest" to **"complete
the existing scaffolding for one strategy at a time and migrate
training paths incrementally."** Estimate revises down: ~7-10 days
focused work, not the original 13.

---

## Per-plan checklist drilldown

Walking each ACTIVE / PROPOSED plan against the 10 checklist sections.
Verdict labels (PASS / FIXED / GAP / DRIFT / DEFERRED / ACCEPTED) per
the audit vocabulary in CLAUDE.md.

### Track E — sharded backtest unification (PLAN WRITTEN — see `plans/track-e-sharded-backtest.md` for full audit)

**Goal:** delete every reason for backtest features to drift from live
features. Backtest becomes "the sharded engine, fed synthetic ticks
from CSV, with a feature-collection hook bolted on."

**Phases (revised given existing scaffolding):**
- **E.1** — Feature collection hook in `BacktestSharded_Run`. Add a
  per-tick-with-completed-slow-path callback that reads
  `RegimeSignals` (already populated by `EventLoop_RebuildAllParameters`)
  and writes a row to `BacktestResults.feature_matrix`. ~1 day.
- **E.2** — Multi-strategy support in `BacktestSharded_Run`. Drop the
  SimpleDip-only gate; let any strategy register. Match the per-core
  strategy dispatch from `EngineSharded`. ~1 day.
- **E.3** — Depth replay (D.5). New `DepthReplayState` parallel to
  `DepthSharedState`, fed from `data/{SYMBOL}/depth/YYYY-MM-DD.csv`.
  `book_imbalance` becomes train-serve safe. Spread features (D.3)
  unlock here. ~3 days.
- **E.4** — `Backtest_RunWalkForward` migration. Replace its inner
  legacy `PortfolioController` calls with `BacktestSharded_Run` per
  fold. Maintain parity tests: same input, same fold splits, **same
  feature matrix to floating-point tolerance**. ~2 days.
- **E.5** — `Backtest_RunSweep` migration. Same shape as E.4. ~1 day.
- **E.6** — Parity validation harness. CLI tool that runs both legacy
  and sharded paths on the same data and diffs feature matrices.
  Asserts ≤ 1e-6 relative error per cell. ~1 day.
- **E.7** — Delete `Backtest_Run` legacy body + remove dispatcher.
  `BacktestSharded_Run` becomes the only entry point. ~½ day.

**Checklist verdict:**
1. Hot path purity — **PASS.** Track E touches *backtest* code only;
   live hot path is unchanged. The whole point is that backtest *uses*
   the same hot path live does.
2. Train-serve parity — **THIS IS THE FIX.** E exists to eliminate
   parity drift. After E ships, "did we update both paths?" stops
   being a question — there is one path.
3. Surface area — **MEDIUM.** Touches ~6 files (BacktestSharded.hpp,
   BacktestEngine.hpp, BacktestPanels.hpp where Walk-Forward is
   invoked, ShardedBacktestDriver.hpp for hooks, possibly
   StrategyParameters.hpp). After E.7, NET DELETION of ~700 LOC
   (legacy `Backtest_Run` body, redundant ML feature plumbing in
   PortfolioController). **Reduces** future maintenance surface.
4. Pointer init + heap lifecycle — **PASS** *if* feature collection
   uses existing `BacktestResults.feature_matrix` (already lifecycle-
   managed via `_Init` / `_Reset` / `_Free` / `_EnsureCapacity`).
   GAP if it adds new heap state — must follow the four-site rule.
5. Backward compatibility — **ACCEPTED divergence.**
   `MODEL_FORMAT_VERSION` does NOT bump (features unchanged). Saved
   Runs from before E remain readable. After E.7 deletes legacy,
   `engine_mode=single_core` becomes a no-op cfg field — leave it
   parsed-but-ignored for one release, drop in next.
6. Multi-threading correctness — **PASS.** Backtest is single-
   threaded. The shared-state question (`DepthSharedState`,
   `DepthReplayState`) is owned-by-one-thread in backtest, so SPSC
   ring discipline is moot. Document this as a backtest invariant
   so a future "parallelize backtest" effort doesn't quietly break it.
7. Test coverage — **GAP** that the plan must address. Required:
   parity test harness (E.6) + multi-strategy regression in
   `controller_test` + walk-forward fold-deterministic test.
8. Docs + invariants — **GAP** that the plan must address. Need:
   - new "Backtest = Sharded with Synthetic Feed" invariant in
     CLAUDE.md
   - delete "Backtest path inherits via wrapper" rule (obsolete)
   - update "Cross-Mode Init Placement" — `EngineSharded_Run` and
     `BacktestSharded_Run` must mirror each other
9. Forward maintenance — **PASS.** New features add to one code
   path; backtest gets them automatically. **This is the single
   biggest leverage win in the roadmap.**
10. Rollback story — `pre-track-e` tag + `backup/pre-track-e-2026-04-XX`
    branch before E.1. Each E.N a separate commit so individual
    phases revertable.

**Outcome of audit:** plan written to
`plans/track-e-sharded-backtest.md` 2026-04-26. All 10 checklist
sections re-walked inside that doc with phase-level verdicts. GAPs
(tests in §7, docs in §8, heap lifecycle for `DepthReplayState`
in §4) tracked inside individual phase exit criteria.

---

### post-edge-hunt-c-and-d.md — REVISED 2026-04-26

**Changes applied:**
- D.5 moved into Track E.3 (one doc owns the depth-replay work).
- D.1 reclassified from "train-serve safe today" → BLOCKED on E.3
  (backtest doesn't replay depth, so `book_imbalance=0` in features
  was a real DRIFT bug the prior plan missed).
- D.3 gate updated: blocked by E.3, not D.5.
- C.1 marked SHIPPED (v4.4 prep).
- C.3 received per-section pre-flight checklist verdict — three
  GAP/NEED-AUDIT items (hot path, pointer init, threading) flagged
  for re-audit before each sub-phase.
- Sequencing rewritten: "now until E ships" / "post-E Wave 1-4."

**Verdict on the revised plan:** all sections audited. The DRIFT on
D.1 was the most important finding — the prior plan would have
shipped a feature that returned 0 in training and non-zero in serving.

### post-v4.0-followups.md — backlog OK, three items need own plans

Walking the audit findings (already partially audited in the file
itself — good!):

1. **UX polish (items 1-3):** PASS. Pure GUI, low surface, OK as
   ad-hoc commits.
2. **Kill switch panel (item 4):** PASS. Pure GUI, reads existing
   `OrderManagerState::ks_*`. ~1 hour work.
3. **Notification panel (item 5):** PASS. New ring buffer in
   `NotifyState`. ~2 hours.
4. **Panic flatten button (item 6):** GAP. Live vs paper behavior
   diverges; needs explicit confirmation flow. **Worth its own
   short plan** (`plans/panic-flatten.md`) before coding.
5. **Per-core dashboard view (item 7):** medium project, ~1 day.
   PASS.
6. **Replay mode (item 8):** **partially obsolete** after Track E —
   `BacktestSharded_Run` already replays from CSV. Replay mode in
   the GUI = "trigger backtest and stream the resulting equity
   curve into the live chart." Re-evaluate after Track E.
7. **Live A/B comparison (item 9):** GUI work. PASS.
8. **Hot-swap-to-ML on no-model silently falls back to SimpleDip:**
   GAP. ~1-hour fix, refuse the swap with a fprintf warning.
   **Schedule this BEFORE first live trade** — it's a misleading
   live-mode behavior.
9. **Sharded ConfidenceScorer state doesn't persist:** GAP for
   *production* live (research-OK). Snapshot v9 bump. ~1 day.
   Schedule when first model with real IC ships.
10. **Buy Gate panel global gate_direction:** GAP. Cosmetic but
    misleading when mixed strategies run. ~1 hour.
11. **Settings_Load doesn't initialize defaults:** PASS — already
    mitigated, but the proper fix (seed `s->float_vals[]` from
    `ControllerConfig_Default<F>()`) is ~1 hour and worth doing.

**Verdict:** the file is OK as a backlog catalog. Three items above
(panic flatten, ConfidenceScorer persistence, partial exits) deserve
their own short plan docs before being coded.

### ml-training-roadmap.md — research notes, OK

Not a work plan in the implementation sense — it's the research
journal. Active for "what model to train next, what feature config
matters." Doesn't need checklist audit — no code surface.

### learn-ml-zoo.md — self-study, OK

Not a work plan. Self-education notes for understanding the
existing architecture.

---

## Out-of-band items that need their own plans

These came up during this audit. **Listed in priority order.**

1. **`plans/track-e-sharded-backtest.md`** — ✅ WRITTEN + AUDITED
   (2026-04-26). Highest priority. Code start gated only on tagging
   `pre-track-e` and pushing the backup branch.
2. **`plans/partial-exits-sharded.md`** — TODO write. Architectural
   surgery, ~4-5 hours hot-path work. Touches Portfolio slot
   allocation, ExecutionCore, OrderManager_HandleFill, drain_with_submit.
   Existing audit notes in post-v4.0-followups (lines 254-308) is
   the seed. Does NOT block Track E — orthogonal.
3. **`plans/panic-flatten.md`** — TODO write. Live-vs-paper behavior
   divergence needs explicit design. Short.
4. **`plans/snapshot-v9-confidence-state.md`** — TODO write. Per-core
   ConfidenceScorer + staged_prediction + active_prediction +
   last_confidence persistence. Schedule when production live needs it.

---

## Decisions locked (carry forward through plans)

These came out of conversation with Jenn over multiple sessions; the
roadmap honors them.

1. **Sharded is the product. Legacy is benchmark + research.** Don't
   spend cycles polishing legacy. Don't worry about backward compat
   on legacy-only paths. Eventually delete legacy live engine
   (already runtime-warns).
2. **ANSI TUI is afterthought.** Keep it building, defer redesign.
   GUI is the production interface.
3. **No backward compat across major version cleanups.** Saved Runs
   from earlier feature versions get retrained, not migrated. Cfg
   fields can be deleted in major versions.
4. **Principled fixes over patches.** Track E is canonical: instead
   of "patch each new feature into both paths forever," make there
   be only one path.
5. **Train-serve parity is sacred.** Every plan must answer "does
   this preserve / fix train-serve parity?"
6. **Hot path purity is sacred.** ≤500ns p99 budget. Currently
   40-400ns. Adding ≥10ns requires explicit plan justification.
7. **Plan Review Checklist applies to every multi-day plan.** Audit
   BEFORE coding. Audit-after-the-fact has caught real bugs in this
   codebase, every single time.

---

## Risks across the roadmap

| Risk | Severity | Mitigation |
|---|---|---|
| Track E migration introduces silent feature drift during transition | HIGH | E.6 parity harness — assert ≤1e-6 difference before each migration phase commits |
| C.3 maker-only logic invalidates models trained on taker assumptions | MEDIUM | Re-audit before C.3, paper-soak in maker mode for 1+ week before live |
| ConfidenceScorer reset on every restart corrupts production calibration | MEDIUM | Snapshot v9 (deferred until first production model) |
| Hot-swap-to-ML misleading behavior bites in first live session | MEDIUM | One-hour fix BEFORE first live trade |
| Plan documents drift out of sync with this master | LOW | This file's "Update protocol" header — touch on every plan ship |
| New features keep getting batch-bumped MODEL_FORMAT_VERSION, invalidating Saved Runs | LOW | Group bumps; document in changelogs (already convention) |

---

## Pickup pointer

When resuming a session: read this file first, then the most recent
`plans/YYYY-MM-DD-pickup*.md` for "what was happening last night."
This file is the long arc; pickup notes are short-horizon state.

Active task tracker state (2026-04-26 overnight):
- #53 — master roadmap with checklist audit ✅ DONE
- #54 — Track E plan with full checklist audit ✅ DONE
- #55 — revise C+D for cohesion ✅ DONE

Next concrete actions: **tag `pre-track-e`** at HEAD, push backup
branch, then start Track E.0 → E.1 (feature collection hook is the
load-bearing piece).
