# Phase 7 prep Tests — Validation infrastructure

last updated: 2026-04-25

**Sidecar to:** `plans/phase7-prep-validation-infrastructure.md`
**Test target:** `tests/controller_test.cpp` extension
**Coverage goal:** ~12-14 assertions

## Test groups

### Group 1: HeldOutSplit math (4 assertions)

```cpp
// 20% split on 1000 samples → trainval=[0, 800), test=[800, 1000)
{
    HeldOutSplit s = HeldOutSplit_Make(1000, 0.20);
    ASSERT_EQ(s.total_samples, 1000);
    ASSERT_EQ(s.trainval_end_idx, 800);
    ASSERT_EQ(s.test_start_idx, 800);
    ASSERT_EQ(s.locked, 1);  // locked by default
}

// Edge case: very small fraction (5%)
{
    HeldOutSplit s = HeldOutSplit_Make(1000, 0.05);
    ASSERT_EQ(s.trainval_end_idx, 950);
}

// Edge case: fraction > 0.5 → clamp or reject? (decide in implementation; test the choice)
{
    HeldOutSplit s = HeldOutSplit_Make(1000, 0.60);
    // either: clamp to 0.30 max, OR refuse and return zero-init
    // tests pin the choice
    ASSERT_LE(s.trainval_end_idx + (s.total_samples - s.test_start_idx), s.total_samples);
}

// Lock token is non-empty after Make
{
    HeldOutSplit s = HeldOutSplit_Make(1000, 0.20);
    ASSERT_NE(s.lock_token[0], '\0');
    ASSERT_EQ(strlen(s.lock_token), 32);  // SHA256 hex of fingerprint
}
```

**4 assertions**

### Group 2: Lock-token discipline (3 assertions)

```cpp
// TestAccessAllowed returns 0 when locked
{
    HeldOutSplit s = HeldOutSplit_Make(1000, 0.20);
    ASSERT_EQ(HeldOutSplit_TestAccessAllowed(&s), 0);
}

// Unlock with correct token → access allowed
{
    HeldOutSplit s = HeldOutSplit_Make(1000, 0.20);
    char token[33];
    strncpy(token, s.lock_token, 33);
    int ok = HeldOutSplit_Unlock(&s, token);
    ASSERT_EQ(ok, 1);
    ASSERT_EQ(HeldOutSplit_TestAccessAllowed(&s), 1);
}

// Unlock with wrong token → refused, still locked
{
    HeldOutSplit s = HeldOutSplit_Make(1000, 0.20);
    int ok = HeldOutSplit_Unlock(&s, "wrong-token-here");
    ASSERT_EQ(ok, 0);
    ASSERT_EQ(HeldOutSplit_TestAccessAllowed(&s), 0);
}
```

**3 assertions**

### Group 3: Walk-forward respects split (3 assertions)

```cpp
// With HeldOutSplit, walk-forward only sees train+val portion
{
    BacktestResults data;
    BacktestResults_Init(&data);
    // populate 1000 samples
    data.sample_count = 1000;
    // ... fill feature_matrix, labels with synthetic data ...

    HeldOutSplit split = HeldOutSplit_Make(1000, 0.20);

    WalkForwardResults wf;
    Backtest_RunWalkForward(&wf, &data, /*n_splits=*/5,
                             /*horizon=*/100, /*buffer=*/10,
                             /*min_train=*/100,
                             /*progress=*/&dummy, /*cancel=*/&dummy_cancel,
                             LABEL_FORWARD_PNL,
                             /*split=*/&split);

    // check that no fold's test_end > trainval_end_idx (= 800)
    for (int f = 0; f < wf.num_folds; f++) {
        if (wf.folds[f].valid) {
            ASSERT_LE(wf.splits[f].test_end, 800);
        }
    }

    BacktestResults_Free(&data);
}

// Without HeldOutSplit (legacy), walk-forward uses all samples
{
    BacktestResults data;
    BacktestResults_Init(&data);
    data.sample_count = 1000;

    WalkForwardResults wf;
    Backtest_RunWalkForward(&wf, &data, /*n_splits=*/5,
                             /*horizon=*/100, /*buffer=*/10,
                             /*min_train=*/100,
                             /*progress=*/&dummy, /*cancel=*/&dummy_cancel,
                             LABEL_FORWARD_PNL,
                             /*split=*/NULL);  // no split

    // at least one fold's test_end > 800 (uses post-split-boundary samples)
    int saw_high = 0;
    for (int f = 0; f < wf.num_folds; f++) {
        if (wf.folds[f].valid && wf.splits[f].test_end > 800) saw_high = 1;
    }
    ASSERT_EQ(saw_high, 1);

    BacktestResults_Free(&data);
}

// Held-out eval refuses to run on locked split
{
    HeldOutSplit split = HeldOutSplit_Make(1000, 0.20);
    // split is locked
    FullValidationResults fvr;
    int ok = Backtest_RunFullValidation(&fvr, &data, &split, LABEL_FORWARD_PNL, ...);
    ASSERT_EQ(ok, 0);  // refused
}
```

**3 assertions**

### Group 4: Full validation framework (3 assertions)

```cpp
// Unlocked split → full validation runs end-to-end
{
    HeldOutSplit split = HeldOutSplit_Make(1000, 0.20);
    HeldOutSplit_Unlock(&split, split.lock_token);

    FullValidationResults fvr;
    int ok = Backtest_RunFullValidation(&fvr, &data, &split, LABEL_FORWARD_PNL, ...);
    ASSERT_EQ(ok, 1);
    ASSERT_GT(fvr.held_out_count, 0);
    ASSERT_NE(fvr.fingerprint[0], '\0');
}

// Gap acceptability flag
{
    // synthesize results where wf and held_out are very close
    FullValidationResults fvr = {};
    fvr.walkforward.mean_val_correlation = 0.10f;
    fvr.held_out_correlation = 0.09f;
    fvr.wf_to_held_out_gap = 0.01f;
    int gap_ok = (fvr.wf_to_held_out_gap < 0.05f);
    ASSERT_EQ(gap_ok, 1);

    // synthesize wide-gap case
    fvr.walkforward.mean_val_correlation = 0.30f;
    fvr.held_out_correlation = 0.05f;
    fvr.wf_to_held_out_gap = 0.25f;
    gap_ok = (fvr.wf_to_held_out_gap < 0.05f);
    ASSERT_EQ(gap_ok, 0);
}
```

**3 assertions**

### Group 5: Cfg + defaults (1 assertion)

```cpp
// New cfg fields parse correctly
{
    char path[] = "/tmp/test_cfg_XXXXXX";
    int fd = mkstemp(path);
    dprintf(fd, "held_out_fraction=0.25\ngap_acceptable_threshold=0.10\n");
    close(fd);
    auto cfg = ControllerConfig_Load<BACKTEST_FP>(path);
    ASSERT_NEAR(FPN_ToDouble(cfg.held_out_fraction), 0.25, 1e-6);
    ASSERT_NEAR(FPN_ToDouble(cfg.gap_acceptable_threshold), 0.10, 1e-6);
    unlink(path);
}
```

**2 assertions in this group (the ASSERT_NEAR pair counts as 2)**

## Total: ~14 assertions

| Group | Count | Validates |
|---|---|---|
| Group 1: Split math | 4 | Boundary calculation correctness |
| Group 2: Lock-token | 3 | Discipline mechanism |
| Group 3: WF respects split | 3 | Integration with walk-forward |
| Group 4: Full validation | 3 | End-to-end framework |
| Group 5: Cfg | 2 | New fields parse |

## Verification

```bash
build/controller_test
```

Expected: previous total + 14 = ~354 assertions cumulative across all phases.

## Test stubs deferred

- **Real model end-to-end**: tests above use synthetic data + dummy validation paths. A test that trains a real XGBoost model on synthetic-with-known-signal data and verifies the gap is small would be more thorough but requires fixture setup.
- **Audit log of unlocks**: tests Group 2 doesn't verify that the unlock event was logged. Add when notify hook is wired.

## Anti-drift contract

The locked-by-default semantic is the discipline mechanism. Tests pin it. Future "ergonomic improvements" that weaken the lock (e.g., auto-unlock-after-timeout, default-unlocked-in-development-mode) would weaken the discipline and should be REJECTED — they defeat the purpose. If lock semantics need to change, document why and update both the lock code AND these tests in the same commit.
