# Phase 7 prep — Validation infrastructure + writeup template

last updated: 2026-04-25 (evening — cross-plan amendments applied)

**Sidecar to:** `plans/live-readiness-master.md` "Phase 6/7 prep" section
**Time budget:** ~half to 1 day (net-new infrastructure)
**Risk:** low — infrastructure + discipline, not behavioral changes
**Test sidecar:** `plans/phase7-prep-validation-infrastructure-tests.md`

## Amendments applied 2026-04-25 evening

After cross-plan analysis:

1. **Commit 4 must update `expected.cfg` writer + reader** to include the two new cfg fields (`held_out_fraction`, `gap_acceptable_threshold`). Per CLAUDE.md FoxML Suite Code Key, `expected.cfg` is the model-bundle reproducibility cfg saved alongside each trained model — new cfg fields that affect training/eval MUST be saved/loaded for reproducibility to work. Original plan didn't mention this.
2. **`lock_token` width clarification** (Tier 2 note): `lock_token[33]` (32 chars + null) is described as "SHA256-hex" but SHA256 is 64 hex chars. Pin the choice at implementation: either truncated SHA256 (first 32 hex chars) or rename to acknowledge it's a short hash for friction, not security. Document the pick in commit 1.
3. **Backtest_RunWalkForward signature change** adds `split` parameter — verified single call site at `BacktestPanels.hpp:995`. Update both function + call site in same commit.
4. **Test Group 4 doesn't actually test `Backtest_RunFullValidation`** — it manually computes the gap comparison. Add at least one assertion that runs the function with synthetic data and verifies function-computed gap.
5. **Held-out lock token failure modes**: if user deletes `models/{run_name}/heldout.token` between split and unlock, behavior should be: split is unrecoverable, user must create a new split. Document this in commit 1.

## Context anchors — files to read FIRST

```
plans/live-readiness-master.md            ← orchestration + anti-drift discipline
Backtest/BacktestPanels.hpp                ← Training panel (where the held-out UI lives)
Backtest/ValidationSplit.hpp               ← existing walk-forward split logic
Backtest/BacktestEngine.hpp                ← Backtest_RunWalkForward function
README.md                                   ← where the "Trained Model Results" section goes
```

Branch state expected: on `experiment/live-readiness`. Doesn't conflict with Phase 6 prep, 8, 8a, 8b — touches different files.

## Failure mode IDs covered

- **Held-out test set discipline** — currently nothing prevents tuning hyperparameters AGAINST what should be a locked test set. With no infrastructure, the discipline is "remember not to do that," which is unreliable. Building a lock-token mechanism makes the discipline structural.
- **Walk-forward + held-out comparison framework** — currently walk-forward is the only validation. For final shipping, you want: walk-forward to pick hyperparameters, held-out for the unbiased estimate. No code combines them.
- **README writeup gets done at the wrong time** — without a template, the "Trained Model Results" section gets written under deadline pressure (when signal is found, energy is on shipping). Pre-writing the template lets the writer fill in numbers, not invent structure.

## Status discovery

- `Backtest/ValidationSplit.hpp` already has temporal split logic for walk-forward folds — reuse for held-out.
- `Backtest_RunWalkForward` in `BacktestEngine.hpp` runs CV but doesn't separate "train+CV vs held-out test."
- Training panel doesn't have a held-out concept at all.
- README has bench numbers + sample TUI screenshots but no Trained Model Results section.

What's net-new for this phase: the held-out infrastructure (split + lock + framework). README template is a doc-only commit.

## Commit plan (in order)

### Commit 1: Held-out test set split + lock-token mechanism

**Goal:** add a temporal data split that locks aside a final-test portion. Code refuses to use it during training/tuning unless explicitly unlocked (with a warning).

**Files:**
- `Backtest/HeldOutSplit.hpp` (new) — split logic + lock-token state
- `Backtest/BacktestPanels.hpp` Training panel — UI for "Reserve test set" toggle + "Held-out fraction" input

**Approach:**

```cpp
// HeldOutSplit.hpp
struct HeldOutSplit {
    int total_samples;
    int trainval_end_idx;    // [0, trainval_end_idx) = train+val
    int test_start_idx;      // [test_start_idx, total_samples) = held-out test
    int locked;              // 1 = test set inaccessible, 0 = unlocked (with warning)
    char lock_token[33];     // SHA256-hex of (config + data fingerprint at split time)
                             // — same token required to unlock
};

// Compute split — temporal, NOT random.
// fraction in [0.05, 0.30] typical (5% to 30% held out).
static inline HeldOutSplit HeldOutSplit_Make(int total_samples, double fraction);

// Returns 1 if asking to access test indices is allowed, 0 if locked.
// During training, this should always return 0 unless explicitly unlocked.
static inline int HeldOutSplit_TestAccessAllowed(const HeldOutSplit *s);

// Explicit unlock — requires the lock_token (proof you know what you're doing).
// Logs an unlock event to stderr + alert (if Notify is wired).
static inline int HeldOutSplit_Unlock(HeldOutSplit *s, const char *token);
```

The lock token is for friction, not security — the goal is "make accidental peeking impossible, intentional peeking auditable."

Training panel flow:
1. User clicks "Reserve test set" → Training panel computes a HeldOutSplit, stores token in a file (`models/{run_name}/heldout.token`)
2. Walk-forward runs ONLY on the train+val portion
3. To run final held-out evaluation: user explicitly clicks "Unlock + Evaluate Held-Out" — UI confirmation dialog, log line, alert
4. After unlock, the token is consumed (one-time use). Re-locking requires a new split.

**Anti-drift checks:**
- [ ] Walk-forward path automatically uses `[0, trainval_end_idx)` when a HeldOutSplit exists
- [ ] No code path can read `[test_start_idx, total_samples)` without checking `HeldOutSplit_TestAccessAllowed`
- [ ] Default behavior with no HeldOutSplit: walk-forward uses all samples (backward compat)

### Commit 2: Walk-forward + held-out comparison framework

**Goal:** function that takes a model + dataset + HeldOutSplit, runs both walk-forward and held-out eval, reports both side-by-side.

**File:** `Backtest/BacktestEngine.hpp` — new `Backtest_RunFullValidation` function

**Approach:**

```cpp
struct FullValidationResults {
    // walk-forward (existing fields)
    WalkForwardResults walkforward;

    // held-out (new)
    int held_out_count;
    float held_out_metric;        // accuracy or Pearson r per label_kind
    float held_out_mse;           // regression only
    float held_out_correlation;   // regression only
    OverfitReport held_out_overfit;  // train_metric (from walk-forward) vs val_metric (from held-out)

    // generalization gap — the load-bearing number for the writeup
    float wf_to_held_out_gap;     // |wf_mean - held_out| — should be small
    int gap_acceptable;           // 1 if gap < threshold (configurable)

    char fingerprint[65];         // for reproducibility
};

static inline void Backtest_RunFullValidation(FullValidationResults *out,
                                                const BacktestResults *data,
                                                const HeldOutSplit *split,
                                                int label_type, ...);
```

Decision logic:
1. Run walk-forward on train+val data only (using `[0, trainval_end_idx)`)
2. Take final hyperparameters from walk-forward
3. Train on full train+val with those hyperparameters
4. Predict on held-out test set
5. Compute held-out metric
6. Compute `wf_to_held_out_gap = |wf_mean_val - held_out_metric|`
7. If gap < `gap_acceptable_threshold` (cfg-driven, default 0.05 for accuracy, 0.05 for Pearson r): mark `gap_acceptable=1`. This is the "generalization is real" signal.

**Anti-drift checks:**
- [ ] Function refuses to run if `split.locked == 1` (must be unlocked first)
- [ ] Held-out evaluation never sees train+val samples (verify via index bounds)
- [ ] Function runs only ONCE per locked split (one-shot semantics)

### Commit 3: README "Trained Model Results" template

**Goal:** add a placeholder section to README that's filled in later.

**File:** `README.md`

**Approach:**

Add a new section under existing bench numbers:

```markdown
## Trained Model Results

> **Status:** model evaluation pending. Section will be filled in after Phase 7 finalize.

### Methodology

[Describe the held-out + walk-forward methodology]

### Walk-forward validation

| Fold | Train | Val | Status |
|---|---|---|---|
| 2/5 | TBD | TBD | TBD |
| ... |

Mean validation metric: TBD
Train/val gap: TBD

### Held-out test results

Held-out fraction: 20% (last 2 months of 12-month dataset)
Held-out metric: TBD
Walk-forward → held-out gap: TBD

### Strategy comparison

| Strategy | Total P&L (%) | Sharpe | Max DD | Win rate |
|---|---|---|---|---|
| SimpleDip (vanilla) | TBD | TBD | TBD | TBD |
| SimpleDip + ML gate | TBD | TBD | TBD | TBD |

### Equity curve

[screenshot placeholder]

### Reproducibility

Model fingerprint: TBD
Config bundle: `models/{run_name}/expected.cfg`
Data: BTCUSDT aggTrades, 2025-04-25 to 2026-04-25
Engine version: TBD
```

**Anti-drift checks:**
- [ ] No source code changes; doc-only commit
- [ ] Section uses placeholders, not fake numbers (don't accidentally ship "TBD" as an actual claim)

### Commit 4: Settings panel + cfg fields + expected.cfg sync

**Goal:** expose the held-out fraction + gap threshold in cfg + Settings panel + reproducibility bundle (amendment #1).

**Files:**
- `CoreFrameworks/ControllerConfig.hpp` — new fields
- `GUI/SettingsPanel.hpp` — new section
- `Backtest/BacktestPanels.hpp` (or wherever `expected.cfg` writer lives) — write `held_out_fraction` + `gap_acceptable_threshold` to bundle
- expected.cfg loader (model load path) — read both fields, verify against current cfg

**Why expected.cfg sync matters:** when a model is saved with a 20% held-out fraction and the user later loads it with a different fraction, results aren't reproducible. The expected.cfg writer/reader is the existing reproducibility mechanism — new fields must flow through it.

**New cfg fields:**
```cpp
FPN<F>   held_out_fraction;        // default 0.20 = 20% of data reserved
FPN<F>   gap_acceptable_threshold; // default 0.05 = 5% gap = good generalization
```

Settings panel section:
```cpp
{"held_out_fraction", "Held-Out %%", "Validation",  CFG_FLOAT, "%.2f",
 "Fraction of data reserved as held-out test set\n"
 "default 0.20 (20%% — last 2 months of 12-month dataset)\n"
 "code refuses to peek at this set during training/tuning\n"
 "explicit unlock required for final evaluation"},
{"gap_acceptable_threshold", "Gap Threshold", "Validation", CFG_FLOAT, "%.3f",
 "Max acceptable |walk-forward - held-out| gap\n"
 "default 0.05 — gap above this = poor generalization\n"
 "applied to both classification accuracy and regression Pearson r"},
```

## Verification

```bash
cmake --build build && cmake --build build_gui && build/controller_test
```

Manual:
1. Open Training panel
2. Select dataset
3. Click "Reserve test set" — verify 20% locked
4. Try to run held-out eval without unlocking — verify it refuses
5. Unlock with token — verify warning + audit log
6. Re-run — held-out eval runs, reports gap

## Definition of done

- [ ] All 4 commits land on `experiment/live-readiness`
- [ ] Test sidecar's assertions pass
- [ ] README has the new section with placeholders
- [ ] Settings panel exposes the two cfg fields
- [ ] Manual flow works end-to-end on synthetic data

## Tag at end

```bash
git tag phase7-prep-complete
```

## Known limitations / deferred (Phase 7 finalize, gated on signal)

- **Filling in the README numbers** — requires actual evaluation results
- **Tagging release v3.10.0** — only when results are publishable
- **HN post / writeup** — when results are real

## Anti-drift contract

The held-out lock-token is the discipline mechanism. If a future commit makes test set access easier (e.g., "auto-unlock for convenience"), that's a regression of the entire purpose. Tests pin the locked-by-default semantic; resist any "ergonomic" change that weakens it.
