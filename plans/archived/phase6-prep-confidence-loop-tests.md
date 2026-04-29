# Phase 6 prep Tests — Confidence loop

last updated: 2026-04-25

**Sidecar to:** `plans/phase6-prep-confidence-loop.md`
**Test target:** `tests/controller_test.cpp` extension
**Coverage goal:** ~10-12 assertions

## Test groups

### Group 1: RollingIC math (4 assertions)

```cpp
// Pushing perfectly correlated (pred, actual) pairs → IC ≈ 1.0
{
    RollingIC ic;
    RollingIC_Init(&ic, 50);
    for (int i = 0; i < 50; i++) {
        double p = (double)i;
        double a = 2.0 * p + 1.0;  // linear, perfect correlation
        RollingIC_Push(&ic, p, a);
    }
    double r = RollingIC_Compute(&ic);
    ASSERT_NEAR(r, 1.0, 0.05);
}

// Random uncorrelated → IC near 0
{
    RollingIC ic;
    RollingIC_Init(&ic, 100);
    srand(42);
    for (int i = 0; i < 100; i++) {
        double p = (double)rand() / RAND_MAX;
        double a = (double)rand() / RAND_MAX;
        RollingIC_Push(&ic, p, a);
    }
    double r = RollingIC_Compute(&ic);
    ASSERT_LT(fabs(r), 0.2);  // near 0 with some noise
}

// Empty IC → 0 (no divide-by-zero)
{
    RollingIC ic;
    RollingIC_Init(&ic, 50);
    double r = RollingIC_Compute(&ic);
    ASSERT_NEAR(r, 0.0, 1e-9);
}

// Window rolls — only last N pairs counted
{
    RollingIC ic;
    RollingIC_Init(&ic, 10);
    // first 10 pairs: anti-correlated
    for (int i = 0; i < 10; i++) RollingIC_Push(&ic, (double)i, -(double)i);
    // next 10 pairs: positively correlated → should overwrite
    for (int i = 0; i < 10; i++) RollingIC_Push(&ic, (double)i, (double)i);
    double r = RollingIC_Compute(&ic);
    ASSERT_GT(r, 0.5);  // rolled to positive correlation
}
```

**4 assertions**

### Group 2: ConfidenceScorer composition (3 assertions)

```cpp
// IC=0, freshness OK → confidence near 0
{
    ConfidenceScorer cs;
    ConfidenceScorer_Init(&cs, 50, /*tau=*/60.0);
    // push noise → IC near 0
    srand(42);
    for (int i = 0; i < 50; i++) {
        ConfidenceScorer_Update(&cs, (double)rand() / RAND_MAX,
                                  (double)rand() / RAND_MAX);
    }
    double conf = ConfidenceScorer_Compute(&cs, /*data_age_sec=*/0.0);
    ASSERT_LT(conf, 0.3);  // low confidence on noise
}

// Strong signal, fresh → high confidence
{
    ConfidenceScorer cs;
    ConfidenceScorer_Init(&cs, 50, /*tau=*/60.0);
    for (int i = 0; i < 50; i++) {
        double p = (double)i / 50.0;
        ConfidenceScorer_Update(&cs, p, 2.0 * p);  // perfect correlation
    }
    double conf = ConfidenceScorer_Compute(&cs, /*data_age_sec=*/0.0);
    ASSERT_GT(conf, 0.7);  // high confidence on strong signal
}

// Stale data → confidence decays
{
    ConfidenceScorer cs;
    ConfidenceScorer_Init(&cs, 50, /*tau=*/60.0);
    for (int i = 0; i < 50; i++) {
        ConfidenceScorer_Update(&cs, (double)i, 2.0 * (double)i);
    }
    double conf_fresh = ConfidenceScorer_Compute(&cs, /*data_age_sec=*/0.0);
    double conf_stale = ConfidenceScorer_Compute(&cs, /*data_age_sec=*/300.0);
    ASSERT_LT(conf_stale, conf_fresh);  // freshness decay
}
```

**3 assertions**

### Group 3: Gate effective-threshold logic (3 assertions)

```cpp
// confidence_enabled=0 → original threshold preserved
{
    PortfolioController<BACKTEST_FP> ctrl;
    auto cfg = ControllerConfig_Default<BACKTEST_FP>();
    cfg.confidence_enabled = 0;
    cfg.ml_buy_threshold = FPN_FromDouble<BACKTEST_FP>(0.6);
    PortfolioController_Init(&ctrl, cfg);
    // simulate STRATEGY_ML with prediction 0.55 (below 0.6 threshold)
    // expected: gate blocks because pred < threshold
    // (need to call the slow-path gate logic — or test the helper directly)
    ASSERT_TRUE(/* gate blocks at 0.55 < 0.6 */);
}

// confidence_enabled=1, low confidence → effective threshold higher → blocks even at higher pred
{
    PortfolioController<BACKTEST_FP> ctrl;
    auto cfg = ControllerConfig_Default<BACKTEST_FP>();
    cfg.confidence_enabled = 1;
    cfg.ml_buy_threshold = FPN_FromDouble<BACKTEST_FP>(0.3);  // low base
    cfg.confidence_threshold_scale = FPN_FromDouble<BACKTEST_FP>(2.0);
    PortfolioController_Init(&ctrl, cfg);
    // confidence near 0 → effective_thr = 0.3 * (2.0 - 0) = 0.6 (clamped to ≤ 1.0)
    // pred = 0.5 → blocked even though above raw threshold
    ASSERT_TRUE(/* gate blocks at 0.5 < 0.6 effective */);
}

// confidence_enabled=1, high confidence → effective threshold ≈ base
{
    // same setup but confidence ≈ 1.0
    // effective_thr = 0.3 * (2.0 - 1.0) = 0.3 (= base)
    // pred = 0.5 → fires (above 0.3)
    ASSERT_TRUE(/* gate fires at 0.5 > 0.3 effective */);
}
```

**3 assertions**

### Group 4: Backward compat (2 assertions)

```cpp
// Old cfg without confidence_threshold_scale: defaults to 2.0
{
    char path[] = "/tmp/test_cfg_XXXXXX";
    int fd = mkstemp(path);
    dprintf(fd, "confidence_enabled=1\n");  // no other confidence fields
    close(fd);
    auto cfg = ControllerConfig_Load<BACKTEST_FP>(path);
    ASSERT_NEAR(FPN_ToDouble(cfg.confidence_threshold_scale), 2.0, 1e-6);
    unlink(path);
}

// confidence_enabled=0 → cfg flag honored even with other fields set
{
    char path[] = "/tmp/test_cfg_XXXXXX";
    int fd = mkstemp(path);
    dprintf(fd, "confidence_enabled=0\nconfidence_window=200\n");
    close(fd);
    auto cfg = ControllerConfig_Load<BACKTEST_FP>(path);
    ASSERT_EQ(cfg.confidence_enabled, 0);
    ASSERT_EQ(cfg.confidence_window, 200u);  // value parsed even if disabled
    unlink(path);
}
```

**2 assertions**

## Total: ~12 assertions

| Group | Count | Validates |
|---|---|---|
| Group 1: RollingIC | 4 | RollingIC math correctness |
| Group 2: ConfidenceScorer | 3 | Composition with freshness |
| Group 3: Gate logic | 3 | Effective threshold formula end-to-end |
| Group 4: Backward compat | 2 | New cfg fields with defaults |

## Verification

```bash
build/controller_test
```

Expected: previous total + 12 = ~340 assertions.

## Test stubs deferred

- **Real-fill simulation**: tests above use synthetic (pred, actual) pairs. A test that runs Backtest_Run with a known-quality model and verifies confidence converges to expected level would be more comprehensive but requires fixture setup. Defer until needed.
- **Multi-core confidence**: per-core ConfidenceScorers don't exist yet. When/if they do, add tests for cross-core independence.

## Anti-drift contract

These tests pin the confidence-loop semantics. If anyone changes the formula `effective_thr = base * (scale - conf)`, the tests should break — that's a feature, force discussion + intentional update.
