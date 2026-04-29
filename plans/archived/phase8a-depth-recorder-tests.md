# Phase 8a Tests — DepthRecorder

last updated: 2026-04-25

**Sidecar to:** `plans/phase8a-depth-recorder.md`
**Time budget:** ~2 hours on top of Phase 8a implementation
**Test target:** New `tests/depth_recorder_test.cpp` binary (separate from controller_test)
**Coverage goal:** 15-17 assertions

## Why a separate test binary

DepthRecorder writes to disk and depends on filesystem state. controller_test stays in-memory by design. A separate binary keeps the test concerns isolated:
- `controller_test` — pure unit tests, fast, no filesystem
- `depth_recorder_test` — integration-y tests with tempdir setup/teardown

CMake adds the new binary to the build. Pattern mirrors existing controller_test setup.

## Test fixture pattern

Each test creates a unique tempdir, exercises the recorder, asserts, cleans up:

```cpp
class DepthRecorderTest {
    char tempdir[256];
    DepthRecorder rec;
public:
    DepthRecorderTest() {
        snprintf(tempdir, sizeof(tempdir), "/tmp/depth_rec_test_XXXXXX");
        char *p = mkdtemp(tempdir);
        ASSERT_NE(p, NULL);
        DepthRecorder_Init(&rec, "TEST", tempdir, /*max_days=*/30, /*enabled=*/1);
    }
    ~DepthRecorderTest() {
        DepthRecorder_Close(&rec);
        // recursive rmdir of tempdir
    }
};
```

## Test groups (corrected per cross-plan errata)

### Group 1: Init + Write + Readback (5 assertions)

```cpp
// Write 10 synthetic snapshots, read CSV back, verify
{
    BookSnapshot<BACKTEST_FP> snap = BookSnapshot_Init<BACKTEST_FP>();
    for (int i = 0; i < 10; i++) {
        snap.bids[0].price = FPN_FromDouble<BACKTEST_FP>(60000.0 - i);
        snap.bids[0].qty   = FPN_FromDouble<BACKTEST_FP>(1.0 + i * 0.1);
        snap.asks[0].price = FPN_FromDouble<BACKTEST_FP>(60001.0 + i);
        snap.asks[0].qty   = FPN_FromDouble<BACKTEST_FP>(0.5 + i * 0.05);
        snap.last_update_id = 1000 + i * 50;  // realistic jump (not +1!)
        snap.timestamp_us   = (uint64_t)(time(NULL)) * 1000000ULL + i * 100000;
        DepthRecorder_Write(&rec, &snap);
    }
    DepthRecorder_Close(&rec);  // flush

    // read back the CSV
    char path[512];
    snprintf(path, sizeof(path), "%s/TEST/depth/%04d-%02d-%02d.csv",
             tempdir, year, month, day);
    FILE *f = fopen(path, "r");
    ASSERT_NE(f, NULL);

    char line[512];
    fgets(line, sizeof(line), f);  // header
    ASSERT_NE(strstr(line, "timestamp_us"), NULL);
    ASSERT_NE(strstr(line, "last_update_id"), NULL);

    int row_count = 0;
    while (fgets(line, sizeof(line), f)) {
        if (line[0] == '#') continue;  // skip gap markers if any
        row_count++;
    }
    ASSERT_EQ(row_count, 10);

    // verify last row's values
    fseek(f, 0, SEEK_SET);
    char *last = NULL;
    char buf[1024];
    while (fgets(line, sizeof(line), f)) {
        if (line[0] != '#' && line[0] != 't') {  // not header, not comment
            strncpy(buf, line, sizeof(buf));
            last = buf;
        }
    }
    ASSERT_NE(last, NULL);
    // CSV format: timestamp_us,last_update_id,bid_price,bid_qty,ask_price,ask_qty
    // last row had i=9: bid=59991, ask=60010, update_id=1000+9*50=1450
    ASSERT_NE(strstr(last, ",1450,"), NULL);  // update_id field

    fclose(f);
}
```

**5 assertions**

### Group 2: Daily rotation (3 assertions)

```cpp
// Write a snapshot at 23:59:30 UTC and another at 00:00:30 UTC next day
// → two files, one per day
{
    BookSnapshot<BACKTEST_FP> snap = BookSnapshot_Init<BACKTEST_FP>();

    // Day 1, 23:59:30 (UTC seconds since epoch for some specific day)
    uint64_t day1_us = /* compute */;
    snap.timestamp_us = day1_us;
    snap.last_update_id = 100;
    DepthRecorder_Write(&rec, &snap);

    // Day 2, 00:00:30 (60 seconds later)
    uint64_t day2_us = day1_us + 60 * 1000000ULL;
    snap.timestamp_us = day2_us;
    snap.last_update_id = 200;
    DepthRecorder_Write(&rec, &snap);

    DepthRecorder_Close(&rec);

    // verify both files exist
    char path1[512], path2[512];
    // ... derive paths from day1_us, day2_us ...
    struct stat st;
    ASSERT_EQ(stat(path1, &st), 0);  // day 1 file exists
    ASSERT_EQ(stat(path2, &st), 0);  // day 2 file exists

    // verify each contains 1 data row (not 2 in either)
    int row1 = count_csv_rows(path1);
    ASSERT_EQ(row1, 1);
    int row2 = count_csv_rows(path2);
    ASSERT_EQ(row2, 1);
}
```

**3 assertions**

### Group 3: Gap detection — CORRECTED logic (4 assertions)

This implements the corrected gap-detection logic per cross-plan errata:
- `lastUpdateId` going backward = real gap (impossible normally)
- Wallclock gap > N seconds between snapshots = real gap
- Per-message `lastUpdateId` jump within normal range = NORMAL, do NOT log

```cpp
// Normal case: lastUpdateId jumping +50 between snapshots = NO gap marker
{
    BookSnapshot<BACKTEST_FP> snap = BookSnapshot_Init<BACKTEST_FP>();
    uint64_t base_us = (uint64_t)time(NULL) * 1000000ULL;
    snap.timestamp_us = base_us;
    snap.last_update_id = 1000;
    DepthRecorder_Write(&rec, &snap);

    // 100ms later, lastUpdateId += 50 (normal busy book)
    snap.timestamp_us = base_us + 100000;
    snap.last_update_id = 1050;
    DepthRecorder_Write(&rec, &snap);

    DepthRecorder_Close(&rec);
    int gap_lines = count_lines_starting_with(path, "# GAP");
    ASSERT_EQ(gap_lines, 0);  // no false positive
}

// lastUpdateId going BACKWARD = real gap (indicates reconnect-to-stale-snapshot)
{
    BookSnapshot<BACKTEST_FP> snap = BookSnapshot_Init<BACKTEST_FP>();
    snap.timestamp_us = base_us;
    snap.last_update_id = 5000;
    DepthRecorder_Write(&rec, &snap);

    snap.timestamp_us = base_us + 100000;
    snap.last_update_id = 4500;  // backward!
    DepthRecorder_Write(&rec, &snap);

    DepthRecorder_Close(&rec);
    int gap_lines = count_lines_starting_with(path, "# GAP");
    ASSERT_GT(gap_lines, 0);  // gap marker present
}

// Wallclock gap > 2 seconds between snapshots = real gap (WS was silent)
{
    BookSnapshot<BACKTEST_FP> snap = BookSnapshot_Init<BACKTEST_FP>();
    snap.timestamp_us = base_us;
    snap.last_update_id = 1000;
    DepthRecorder_Write(&rec, &snap);

    snap.timestamp_us = base_us + 5 * 1000000ULL;  // 5 seconds later
    snap.last_update_id = 1050;
    DepthRecorder_Write(&rec, &snap);

    DepthRecorder_Close(&rec);
    int gap_lines = count_lines_starting_with(path, "# GAP");
    ASSERT_GT(gap_lines, 0);
}

// DepthRecorder_LogGap explicit call (from disconnect site)
{
    DepthRecorder_LogGap(&rec, base_us);  // explicit gap log
    DepthRecorder_Close(&rec);
    int gap_lines = count_lines_starting_with(path, "# GAP");
    ASSERT_EQ(gap_lines, 1);
}
```

**4 assertions**

### Group 4: AutoPrune (3 assertions)

```cpp
// Pre-create 5 daily files spanning 60 days, then init with max_days=30
{
    char tempdir[256];
    snprintf(tempdir, sizeof(tempdir), "/tmp/prune_test_XXXXXX");
    mkdtemp(tempdir);

    char depth_dir[300];
    snprintf(depth_dir, sizeof(depth_dir), "%s/TEST/depth", tempdir);
    mkdir_p(depth_dir);

    // create 5 files with mtimes spanning 60 days
    int days_old[] = {1, 15, 25, 35, 60};
    for (int i = 0; i < 5; i++) {
        char path[512];
        // filename based on YYYY-MM-DD; or use stat-based mtime
        snprintf(path, sizeof(path), "%s/2026-04-%02d.csv", depth_dir,
                 25 - days_old[i]);  // simplified
        FILE *f = fopen(path, "w");
        fputs("dummy", f);
        fclose(f);
        // touch with old mtime
        struct utimbuf ut;
        ut.actime = ut.modtime = time(NULL) - days_old[i] * 86400;
        utime(path, &ut);
    }

    DepthRecorder rec;
    DepthRecorder_Init(&rec, "TEST", tempdir, /*max_days=*/30, /*enabled=*/1);

    // After Init, files older than 30 days should be gone
    int remaining = count_files_in_dir(depth_dir);
    ASSERT_EQ(remaining, 3);  // 1, 15, 25 days old kept; 35, 60 pruned

    // Specifically: 35-day-old file gone
    ASSERT_NEEDS_HELPER_OR_EXPLICIT_PATH;
    // 1-day-old file kept
    ASSERT_NEEDS_HELPER_OR_EXPLICIT_PATH;
}
```

**3 assertions**

### Group 5: Error handling (2 assertions)

```cpp
// fopen failure: bad data_dir → recorder logs + disables itself, doesn't crash
{
    DepthRecorder rec;
    DepthRecorder_Init(&rec, "TEST", "/nonexistent_path/", /*max_days=*/30, /*enabled=*/1);
    // even though enabled=1, it should fail gracefully on first write
    BookSnapshot<BACKTEST_FP> snap = BookSnapshot_Init<BACKTEST_FP>();
    DepthRecorder_Write(&rec, &snap);  // should not crash
    // recorder may have set itself to disabled, file=NULL
    ASSERT_EQ(rec.file, (FILE*)NULL);  // or similar invariant
    ASSERT_EQ(rec.count, 0u);  // no successful writes
}

// disabled=0 → all calls are no-ops
{
    DepthRecorder rec;
    DepthRecorder_Init(&rec, "TEST", tempdir, /*max_days=*/30, /*enabled=*/0);
    BookSnapshot<BACKTEST_FP> snap = BookSnapshot_Init<BACKTEST_FP>();
    DepthRecorder_Write(&rec, &snap);
    DepthRecorder_LogGap(&rec, 0);
    // no files should be created in tempdir
    int files = count_files_in_dir(tempdir);
    ASSERT_EQ(files, 0);
}
```

**2 assertions**

## Build integration

`tests/depth_recorder_test.cpp` is a new file. **This requires a CMakeLists.txt addition as part of Phase 8a's commit list.** Pattern matches the existing `controller_test`:

```cmake
# Add right after the existing controller_test entry (~line 175):
add_executable(depth_recorder_test tests/depth_recorder_test.cpp)
target_compile_options(depth_recorder_test PRIVATE -O3 -march=native -funroll-loops -flto)
target_include_directories(depth_recorder_test PRIVATE ${CMAKE_SOURCE_DIR}/..)
add_test(NAME depth_recorder_test COMMAND depth_recorder_test)
```

This goes in **Phase 8a commit 4** (final commit, alongside cfg field + tooltip + changelog). Do NOT split into a separate commit — keep the test binary + the production code that needs testing in the same commit so the relationship is visible in `git log`.

Phase 8a Definition of Done updates:
- [ ] `depth_recorder_test` builds clean
- [ ] All 17 assertions pass
- [ ] Tests pass 3 times in a row (no flakiness from filesystem races)

## Total: 17 assertions

| Group | Count | Phase 8a commit it validates |
|---|---|---|
| Group 1: Init/Write/Readback | 5 | Commit 2 (DepthRecorder.hpp) |
| Group 2: Daily rotation | 3 | Commit 2 |
| Group 3: Gap detection (corrected) | 4 | Commit 3 |
| Group 4: AutoPrune | 3 | Commit 2 |
| Group 5: Error handling | 2 | Commits 2+3 |

## Verification

```bash
cmake --build build -j$(nproc)
build/depth_recorder_test
```

Expected: **17 passed, 0 failed.**

## Test stubs deferred

- **Concurrent writes from depth thread**: tests above use single-threaded fixture. Real depth thread uses pthread, atomic. A multi-thread stress test (1000 writes in parallel) would be useful but requires more harness. Defer to integration testing on testnet.
- **CSV parser correctness across all field combinations**: a fuzz-style test that generates random valid BookSnapshots and round-trips through write+parse. Defer.
- **Real Binance JSON corpus replay**: capture real testnet depth events, feed through parser, then write to recorder. Replay-based test. Defer until testnet recording exists.

## Anti-drift contract

If anyone later modifies CSV format, daily rotation logic, or gap detection thresholds:
- These tests must still pass without modification, OR
- The change is breaking, requires a CSV-format-version bump, and the test is updated alongside the production change in the same commit

Like the regression tests: these are drift guards, not specs to update casually.
