# Phase 6 prep — Confidence loop (mostly wired, gap-fill + tests + docs)

last updated: 2026-04-25 (evening — cross-plan amendments applied)

**Sidecar to:** `plans/live-readiness-master.md` "Phase 6/7 prep" section
**Time budget:** ~2-3 hours (much smaller than originally scoped — most wiring is already done)
**Risk:** very low — verifying existing code + adding tests + adding docs
**Test sidecar:** `plans/phase6-prep-confidence-loop-tests.md`

## Amendments applied 2026-04-25 evening

After cross-plan analysis vs. CLAUDE.md "FPN-Only Accounting" rule + codebase spot-check:

1. **CLAUDE.md "Snapshot sync rule" is NOT stale** — already updated to the simplified "thin wrapper" form. Original plan said "verify and update CLAUDE.md" — that step is unnecessary, drop it.
2. **Confidence-loop double arithmetic at PortfolioController.hpp:1588** (`effective_thr = base_thr * (2.0 - conf)`) is a **pre-existing FPN-only violation**, not introduced by this phase. Add to CLAUDE.md "Known violations to fix" list in commit 3 alongside kill switch + orphan recovery already documented there. Fix is out of scope for 6prep — would change cfg field semantics.
3. **Test sidecar Group 1 uses platform-dependent `rand()`** (Tier 2 note). When implementing tests, replace with deterministic seeded LCG (~5 lines) so tests pass identically on glibc, musl, macOS.
4. **Test sidecar Group 3 has placeholder `ASSERT_TRUE(/* gate blocks at 0.55 < 0.6 */)`** — actual gate testing infrastructure isn't fully spec'd. Either expose a small helper for the gate-threshold formula in a header, or test through a fuller controller setup. Decide at implementation time.

## Status discovery (2026-04-25)

When the live-readiness master plan was written, this phase was scoped at 1-2 days. On reading the actual code, I found the wiring is **mostly already done**:

| Component | Status |
|---|---|
| `RollingIC` / `ConfidenceScorer` structs | ✓ exist in `ML_Headers/ConfidenceScore.hpp` |
| `ConfidenceScorer` field on `PortfolioController` | ✓ `ctrl->confidence` |
| `last_confidence` field | ✓ `ctrl->last_confidence` |
| Init in `PortfolioController_Init` | ✓ line 342-345 |
| `(prediction, realized_return)` pushed on every fill | ✓ `PortfolioController.hpp:490-493` (gated on `confidence_enabled` + `STRATEGY_ML`) |
| Confidence used in gate decision | ✓ `PortfolioController.hpp:1583-1596` — `effective_thr = base_thr * (2.0 - conf)` |
| `confidence_enabled` cfg flag | ✓ exists, defaults to 0 |
| TUISnapshot fields (confidence, IC, RMSE, freshness) | ✓ `s->ml.confidence*` |
| ANSI TUI display | ✓ `TUIAnsi.hpp:573-574` |
| GUI Dashboard display | ✓ `DashboardPanels.hpp:322-326` |
| ML Intelligence panel breakdown (IC, RMSE, freshness, bar) | ✓ `DashboardPanels.hpp:832-847` |
| BacktestSnapshot auto-sync | ✓ `BacktestSnapshot_Copy` is thin wrapper over `TUI_CopySnapshot` (snapshot sync rule from CLAUDE.md is stale — verify and update CLAUDE.md) |

**What's actually missing:** tests, verification that the existing implementation is correct under all paths, an invariant in CLAUDE.md, possibly tunable parameters.

## Failure mode IDs covered

- "Found signal → emergency wiring sprint" — eliminated by pre-wiring (already done; this phase verifies + tests)
- "Confidence loop logic is broken on edge cases" — covered by tests we add
- "Stale CLAUDE.md sync rule misleads future contributors" — covered by doc update

## Commit plan (in order)

### Commit 1: Verify existing wiring + lock with tests

**Goal:** prove the confidence loop works as intended on noise-floor predictions, real signal predictions, and edge cases.

**File:** `tests/controller_test.cpp` — append confidence-loop test group (see test sidecar for full list)

Specifically:
- Mock a fill stream of (prediction, realized_return) pairs, push through `ConfidenceScorer_Update`, assert IC converges to expected value
- Confidence on noise-floor predictions ≈ 0 → effective threshold ≈ 2× base → never fires (safe)
- Confidence on perfect predictions ≈ 1.0 → effective threshold ≈ base → fires normally
- `confidence_enabled=0` path is unchanged (backward compat)

**Anti-drift check:**
- [ ] Existing `controller_test` 279 + previous additions (296 from Phase 5d regression) all pass
- [ ] New tests don't depend on real Binance fill events (use synthetic data)

### Commit 2: Surface tunable parameters in cfg

**Goal:** make `confidence_window`, `confidence_freshness_tau`, and the `2.0 - conf` formula's coefficient adjustable from cfg instead of hardcoded.

**Files:**
- `CoreFrameworks/ControllerConfig.hpp` — add 3 fields with defaults
- `CoreFrameworks/PortfolioController.hpp:1583-1596` — read from cfg instead of hardcoding `2.0`
- `GUI/SettingsPanel.hpp` — add to "ML / Confidence" section

**New cfg fields:**
```cpp
uint32_t confidence_window;       // RollingIC window (default 100, was hardcoded)
FPN<F>   confidence_freshness_tau; // freshness decay time constant (default 60s, was hardcoded)
FPN<F>   confidence_threshold_scale; // formula: effective_thr = base * (this - conf), default 2.0
```

**Anti-drift check:**
- [ ] Defaults match current hardcoded behavior (no behavior change unless cfg overrides)
- [ ] `confidence_enabled=0` path unaffected

### Commit 3: CLAUDE.md doc — Confidence Loop invariant

**File:** `CLAUDE.md` Safety Invariants section, new subsection.

**Content:**

```markdown
### Confidence Loop Invariant

When `confidence_enabled=1` and `strategy_id=STRATEGY_ML`:
1. Every fill MUST push `(prediction, realized_return)` into RollingIC via `ConfidenceScorer_Update`
2. Confidence MUST be computed before the gate decision in slow path
3. Effective threshold formula: `effective_thr = base_thr * (confidence_threshold_scale - conf)`, clamped to ≤ 1.0
4. With confidence ≈ 0 (noise-floor or untrained model), the gate effectively never fires — safe-by-default behavior
5. NEVER read `last_confidence` from the hot path — only slow path / display
```

**Add to "Known violations to fix" list (amendment #2):**
```markdown
- Confidence-loop gate decision (`PortfolioController.hpp:1588`):
  `double effective_thr = base_thr * (2.0 - conf)` is pure double math gating
  buys. Pre-existing violation. Fix would change `confidence_threshold_scale`
  cfg field semantics — defer to a later FPN-cleanup pass, not 6prep scope.
```

(Snapshot sync rule update originally planned here is **dropped** per amendment #1 — CLAUDE.md is already correct.)

**Anti-drift check:**
- [ ] CLAUDE.md changes only documentation; no code paths affected

## Verification

```bash
cmake --build build -j$(nproc) && build/controller_test
cmake --build build_gui -j$(nproc)
```

Expected: all pre-existing assertions pass + new confidence test group passes.

Manual: enable `confidence_enabled=1` on a noise-floor model, observe in TUI that confidence stays near 0 and ML strategy doesn't fire. Then disable, observe normal behavior returns.

## Definition of done

- [ ] All 3 commits land on `experiment/live-readiness`
- [ ] Test sidecar's assertions all pass (see `phase6-prep-confidence-loop-tests.md`)
- [ ] CLAUDE.md updated with Confidence Loop invariant + corrected snapshot sync note
- [ ] Settings panel shows new tunable cfg fields
- [ ] No new compile warnings

## Tag at end

```bash
git tag phase6-prep-complete
```

## Known limitations / deferred (Phase 6 finalize, gated on signal)

- **Comparing confidence-weighted vs raw prediction**: requires a model with non-zero validation Pearson r. Park here, return when signal exists.
- **Tuning `confidence_threshold_scale` formula**: the `2.0` default is a magic number. Tuning requires real signal to A/B against.
- **Per-core confidence scorers**: current design is one ConfidenceScorer per controller. If multi-core models with different signal characteristics emerge later, may need per-core scorers. Defer until that's a real need.

## Why this phase is short

The infrastructure was built ahead of time (probably during a Phase 5 sub-task). Phase 6 prep is just verifying it's correct + locking it with tests + documenting. The "1-2 days" estimate in the master plan was based on assuming we had to BUILD the loop; we just have to verify and test it.

Master plan total time estimate adjusted: Phase 6 prep is ~half day, not 1-2 days.
