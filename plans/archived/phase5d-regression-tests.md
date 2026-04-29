# Phase 5d Regression Tests — locking in this weekend's bug fixes

last updated: 2026-04-25

**Time budget:** ~2 hours
**Status:** runs BEFORE Phase 8/8a/8b — the discipline is "test the bugs we just fixed before fixing more"

## Why this exists

Eight real bugs got found + fixed across Saturday and Sunday. Each is documented in CLAUDE.md as an invariant + in `DOCS/changelogs/2026-04-25-*.md` as a postmortem. But the FIXES are only verified by manual smoke testing — there are no automated regression tests guarding against the same class of bug returning.

Locking these in as tests is the cheapest insurance against a future commit re-introducing one. Each test is small (~3-5 assertions) but the protection is permanent.

This sidecar is what runs **before any Phase 6 work begins** — not technically a sub-phase, but a discipline gate. It's a single commit that adds tests, no new functionality.

## Bugs to lock in

| Bug | Commit | What's tested |
|---|---|---|
| equity_curve preservation in `_Reset` | `fcf9616` | Reset preserves equity_curve pointer + capacity, not just sample buffers |
| EnsureCapacity floor (cap=0 → spinner) | `fcf9616` | EnsureCapacity with `capacity=0`, `needed=1` returns INIT_CAP, not infinite-loops |
| Label-type-aware metric dispatch | `cd2936d`, `8d175b1` | LabelType_IsBinary/IsRegression/IsMulticlass return correct kind for each label_type |
| Multiclass per-sample weights | `38ab41d` | XGBoost_ComputeMulticlassWeights produces inverse-frequency weights summing correctly |
| scale_pos_weight zero-positive guard | `38ab41d` | XGBoost_ComputeScalePosWeight(n_pos=0) returns 1.0, not divide-by-zero |
| min_warmup_samples clamp | `c6aa0cc` | ControllerConfig_Load with min_warmup_samples=512 clamps to 128 + warns |
| GATE_REASON_TABLE coverage | `c95ef3f` | Every GATE_REASON_* constant has a non-null entry in GATE_REASON_TABLE |
| Label-buffer accumulation | `9155558` | Multi-file label buffer correctly accumulates count across files (integration test) |

## Test commit plan

### Single commit: `tests: regression tests for 2026-04-25 bug fixes`

**File:** `tests/controller_test.cpp` — append a new section at the end. ~17 new assertions.

**Approach: 5 test groups, ordered by complexity.**

#### Group 1: Dynamic-buffer lifecycle (3 assertions)

```cpp
// equity_curve preservation across Reset
{
    BacktestResults r;
    BacktestResults_Init(&r);
    double *original_curve = r.equity_curve;
    int original_cap       = r.equity_capacity;
    // simulate a run: bump counts
    r.equity_count = 5;
    r.sample_count = 100;
    BacktestResults_Reset(&r);
    ASSERT_EQ(r.equity_count, 0);
    ASSERT_EQ(r.equity_capacity, original_cap);
    ASSERT_EQ(r.equity_curve, original_curve);
    BacktestResults_Free(&r);
}

// EnsureEquityCapacity floor: capacity=0 → INIT_CAP (not infinite loop)
{
    BacktestResults r = {};
    r.equity_capacity = 0;
    r.equity_curve    = NULL;
    int ok = BacktestResults_EnsureEquityCapacity(&r, 1);
    ASSERT_EQ(ok, 1);
    ASSERT_GTE(r.equity_capacity, BACKTEST_EQUITY_INIT);
    free(r.equity_curve);
}

// EnsureCapacity (samples) same floor
{
    BacktestResults r = {};
    r.sample_capacity = 0;
    r.feature_matrix = r.labels = NULL;
    r.sample_tick_indices = NULL;
    r.sample_prices = NULL;
    r.sample_regimes = NULL;
    int ok = BacktestResults_EnsureCapacity(&r, 1);
    ASSERT_EQ(ok, 1);
    ASSERT_GTE(r.sample_capacity, BACKTEST_SAMPLES_INIT);
    free(r.feature_matrix); free(r.labels); free(r.sample_tick_indices);
    free(r.sample_prices); free(r.sample_regimes);
}
```

#### Group 2: Label-type-aware metric dispatch (4 assertions)

```cpp
ASSERT_EQ(LabelType_NumClasses(LABEL_WIN_LOSS), 0);
ASSERT_EQ(LabelType_NumClasses(LABEL_FORWARD_PNL), 1);
ASSERT_EQ(LabelType_NumClasses(LABEL_PEAK_VALLEY_STABLE), 3);
ASSERT_EQ(LabelType_NumClasses(LABEL_REGIME), 4);

ASSERT_EQ(LabelType_IsBinary(LABEL_WIN_LOSS),   1);
ASSERT_EQ(LabelType_IsRegression(LABEL_FORWARD_PNL), 1);
ASSERT_EQ(LabelType_IsMulticlass(LABEL_PEAK_VALLEY_STABLE), 1);
ASSERT_EQ(LabelType_IsMulticlass(LABEL_REGIME), 1);

// Out-of-bounds label_type returns safe defaults
ASSERT_EQ(LabelType_IsBinary(999), 1);   // unknown kind defaults to binary (safest fallback)
ASSERT_EQ(LabelType_IsRegression(-1), 0);
```

#### Group 3: Class-balance helpers (4 assertions)

```cpp
// scale_pos_weight basic
{
    float labels[] = {1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f};  // 2 pos, 4 neg
    int n_pos = 0, n_neg = 0;
    double w = XGBoost_ComputeScalePosWeight(labels, 6, &n_pos, &n_neg);
    ASSERT_EQ(n_pos, 2);
    ASSERT_EQ(n_neg, 4);
    ASSERT_NEAR(w, 2.0, 1e-6);
}

// scale_pos_weight zero-positive guard (degenerate dataset)
{
    float labels[] = {0.0f, 0.0f, 0.0f};
    int n_pos = 0, n_neg = 0;
    double w = XGBoost_ComputeScalePosWeight(labels, 3, &n_pos, &n_neg);
    ASSERT_EQ(n_pos, 0);
    ASSERT_NEAR(w, 1.0, 1e-6);  // not NaN, not divide-by-zero
}

// Multiclass weights: inverse-frequency
{
    float labels[] = {0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 2.0f};  // 4 of c0, 1 of c1, 1 of c2
    float weights[6];
    int counts[16];
    XGBoost_ComputeMulticlassWeights(labels, 6, 3, weights, counts);
    ASSERT_EQ(counts[0], 4);
    ASSERT_EQ(counts[1], 1);
    ASSERT_EQ(counts[2], 1);
    // weight[i] = total / (K * count[label[i]])
    ASSERT_NEAR(weights[0], 6.0f / (3.0f * 4.0f), 1e-5);  // c0 sample: 0.5
    ASSERT_NEAR(weights[4], 6.0f / (3.0f * 1.0f), 1e-5);  // c1 sample: 2.0
    ASSERT_NEAR(weights[5], 6.0f / (3.0f * 1.0f), 1e-5);  // c2 sample: 2.0
}

// Regression metric helpers: Pearson correlation
{
    float pred[]   = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};
    float labels[] = {2.0f, 4.0f, 6.0f, 8.0f, 10.0f};   // perfectly correlated, 2x scale
    float r = WalkForward_ComputeCorrelation(pred, labels, 5);
    ASSERT_NEAR(r, 1.0f, 1e-4);
}
```

#### Group 4: Config + clamping (2 assertions)

```cpp
// min_warmup_samples > 128 clamps to 128 (with warning printed)
{
    // write a temp cfg file with min_warmup_samples=512
    char path[] = "/tmp/test_cfg_XXXXXX";
    int fd = mkstemp(path);
    dprintf(fd, "min_warmup_samples=512\n");
    close(fd);
    auto cfg = ControllerConfig_Load<BACKTEST_FP>(path);
    ASSERT_EQ(cfg.min_warmup_samples, 128u);  // clamped
    unlink(path);
}

// fee_rate parsing pct → fraction (legacy mode, before Phase 8)
{
    char path[] = "/tmp/test_cfg_XXXXXX";
    int fd = mkstemp(path);
    dprintf(fd, "fee_rate=0.10\n");
    close(fd);
    auto cfg = ControllerConfig_Load<BACKTEST_FP>(path);
    ASSERT_NEAR(FPN_ToDouble(cfg.fee_rate), 0.001, 1e-6);  // 0.10% = 0.001 fraction
    unlink(path);
}
```

#### Group 5: Coverage tables (2 assertions)

```cpp
// GATE_REASON_TABLE has an entry for every GATE_REASON_* constant
{
    for (int i = 0; i < NUM_GATE_REASONS; i++) {
        ASSERT_NE(GATE_REASON_TABLE[i].name, NULL);
        ASSERT_NE(GATE_REASON_TABLE[i].name[0], '\0');
    }
}

// REJECT_REASON_NAMES same
{
    for (int i = 0; i < NUM_REJECT_REASONS; i++) {
        ASSERT_NE(REJECT_REASON_NAMES[i], NULL);
        // index 0 is "" by design (REJECT_REASON_NONE has no name)
        if (i > 0) ASSERT_NE(REJECT_REASON_NAMES[i][0], '\0');
    }
}
```

#### Group 6: Label-buffer accumulation (integration — 1 assertion)

This one's harder to unit test cleanly because it requires the full `Backtest_Run` pipeline. **Recommendation: defer to integration test in Phase 8 testnet validation**, or add a small synthetic test fixture that loads 2 hand-crafted CSV files and verifies the label_count after the post-pass equals the sum of file ticks (not just the last file's count).

```cpp
// Integration test: multi-file label buffer correctly accumulates
// (this is harder to unit-test in isolation; included as a stub)
{
    // build 2 tiny CSV files in /tmp with known tick counts
    // call Backtest_Run with collect_features=1, label_type=LABEL_FORWARD_PNL
    // assert: results->labels[0..sample_count) all have non-default values
    //         (not all zeros, which would indicate the label-buffer bug)
    // This is harder than a unit test — defer to integration.
    // Document as a known gap to address with a fixture later.
}
```

## Verification

```bash
cmake --build build -j$(nproc)
build/controller_test
```

Expected: 279 + 17 = **296 passed, 0 failed**.

If any assertion fails: that's a regression in the fix itself, NOT a flaky test. Investigate immediately.

## Definition of done

- [ ] Single commit on `experiment/live-readiness` (or `experiment/phase5-zoo` if pre-merge)
- [ ] controller_test goes from 279 → 296 assertions
- [ ] All passing on first commit
- [ ] CHANGELOG entry: `DOCS/changelogs/2026-04-XX-phase5d-regression-tests.md`

## Tag

```bash
git tag phase5d-regression-tests
```

## Why this matters

Each of these tests guards against a specific re-introducible bug class. Specifically:

- **Group 1** prevents another `_Reset` regression where someone adds a new dynamic field and forgets to extend the helper.
- **Group 2** prevents future label types from silently defaulting to binary if someone forgets to update the helpers.
- **Group 3** prevents class-balance compensation from regressing to "no compensation" or "divide by zero."
- **Group 4** prevents the user-hostile silent-fail with min_warmup_samples > 128.
- **Group 5** prevents future GATE_REASON_* additions from leaving stale name tables.

These are exactly the bug classes that took multiple sessions to find this weekend. Locking them in costs ~2 hours; not locking them in risks paying that bug-hunting cost again.
