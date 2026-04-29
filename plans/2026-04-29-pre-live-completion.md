# Pre-Live Completion — Master Plan (2026-04-29)

Closes the two remaining pre-live items from today's polish work:

1. **Reconcile boot-sequence wiring** — Phase 1 logic shipped in v5.2.1
   but not yet CALLED at engine boot. Today: wire it as dry-run.
2. **Stamp generation tool** — `verify_model_stamp` shipped in v5.2.0
   but no way to GENERATE stamps without hand-crafting via openssl.
   Today: ship a bash script that signs pre-computed metrics.

Both are small ships (~30 min each). Both close real pre-live gates
without committing to the larger Phase 2 work (full reconcile apply +
C++ stamp binary that runs validation directly).

## Why ship today

- Reconcile dry-run completes the arc end-to-end. v5.2.1 ships infra +
  tests but the engine doesn't actually call it. A dry-run wiring
  surfaces exchange-vs-local disagreement at boot in live mode without
  applying changes — making "what would happen?" visible before
  trusting the apply path.
- Stamp script unblocks the held-out gate. Today users could hand-write
  stamps but it's friction. A 30-line shell wrapper around openssl
  removes that friction without committing to the bigger C++ stamp tool.

## Ship 1 — v5.2.2: reconcile boot wiring (dry-run only)

### Where

`CoreFrameworks/EngineSharded.hpp` line 786 — currently when
`live_trading=1`, the engine logs `[snapshot] LIVE mode: skipping
snapshot load (exchange-truth-of-state)` and moves on. That's the slot.

### Edits

```cpp
} else {
    fprintf(stderr, "[snapshot] LIVE mode: reconciling with exchange truth\n");
    BinanceOrderAPI* api = &g_sharded_binance_adapter.workers_api[0];

    double usdt = 0.0, btc = 0.0;
    BinanceOrderAPI_GetBalances(api, &usdt, &btc);

    char open_buf[16384] = {0};
    char trades_buf[65536] = {0};
    BinanceOrderAPI_GetOpenOrders(api, open_buf, sizeof(open_buf));
    BinanceOrderAPI_GetMyTrades(api, /*since=*/0, trades_buf, sizeof(trades_buf));

    tt::ReconcileOpenOrder orders[16];
    tt::ReconcileTrade trades[256];
    int no = tt::Reconcile_ParseOpenOrders(open_buf, orders, 16);
    int nt = tt::Reconcile_ParseMyTrades(trades_buf, trades, 256);

    int local_open = __builtin_popcount(oms.portfolio.active_bitmap);
    auto result = tt::Reconcile_Decide(usdt, btc, orders, no, trades, nt, local_open);
    tt::Reconcile_LogReport(result, cfg.reconcile_dry_run);

    if (result.refused_boot) {
        fprintf(stderr, "[reconcile] refusing to boot — see CRITICAL above\n");
        BinanceAdapter_ShutdownState(&g_sharded_binance_adapter);
        std::signal(SIGINT, prev_int);
        std::signal(SIGTERM, prev_term);
        return;
    }
    // Phase 2: apply (cancel orders, replay fills, force-close stale locals)
    // Deferred — requires BinanceOrderAPI_CancelOrder + Command synthesis.
}
```

### Verification

- Tests already cover the logic (v5.2.1 has 23 assertions). No new tests
  needed for the wiring itself — the integration is "do the calls happen
  in the right order?" which is structural.
- Manual smoke test: `engine_mode=sharded`, `use_real_money=1`,
  `use_testnet=1`, real Binance testnet API key in secrets.cfg. Boot the
  engine; verify `[reconcile] exchange:` log lines appear with sane
  numbers. No real fills should be applied (dry_run=1 default).

### Acceptance

- Build green
- 776/776 tests still pass (no test changes — wiring only)
- Boot path log shows reconcile fired in live mode
- Paper mode behavior unchanged

### Rollback

`pre-v5.2.2-reconcile-wiring` tag. Revert is mechanical — restore the
"skipping snapshot load" log line.

## Ship 2 — v5.2.3: bash stamp tool

### Where

New file: `tools/stamp_model.sh` (executable shell script).

### What it does

```bash
./tools/stamp_model.sh \
    --model models/aggressive/buy_signal.bin \
    --secret "$HELD_OUT_STAMP_SECRET" \
    --wf-mean-val 0.55 \
    --held-out-metric 0.53 \
    --gap-threshold 0.05 \
    --trained-on 2026-04-28
```

Computes:
- `model_sha256` from the .bin file via `sha256sum`
- `gap = |wf_mean_val - held_out_metric|`
- HMAC-SHA256(secret, canonical_body) via `openssl dgst`

Writes `<model>.stamp` with the same format `verify_model_stamp` reads.

Refuses to write if `gap > gap_threshold` (with `--force` override for
edge cases).

### Why bash, not C++ binary

- ~30 min vs 2-3h
- No linking issues with `Backtest_RunFullValidation`
- User runs validation in foxml_suite (already exists); this just
  signs the result
- Future v5.3.x could replace with a C++ binary that runs validation
  directly if that ergonomic friction matters. For now this is enough.

### Verification

- Round-trip test: stamp a model with known metrics, then run
  `verify_model_stamp` against it. Should return `valid=1`.
- Negative test: stamp with `gap=0.10`, `gap_threshold=0.05`, `--force`.
  Verify rejects the stamp on load (since gap > threshold).

These tests already exist in v5.2.0's test group (8 stamp-verify
assertions). No new tests for v5.2.3 — the bash script generates input
that the existing C++ verifier consumes.

### Acceptance

- Script executes without errors with valid args
- Generated stamp passes `verify_model_stamp` round-trip
- Refuses write when gap > threshold (without `--force`)
- Documented in `Strategies/README.md` or a new `tools/README.md`

### Rollback

Just delete `tools/stamp_model.sh`. No engine changes.

## Versioning

| Version | Item | Effort |
|---|---|---|
| v5.2.2 | Reconcile boot wiring (dry-run + refuse) | ~30 min |
| v5.2.3 | Bash stamp tool | ~30 min |

Total: ~1h. Both ship before EOD.

## What's NOT in this plan (deferred)

- **Reconcile Phase 2** (full apply path): `BinanceOrderAPI_CancelOrder`,
  trade-to-Command synthesis, force-close local helper. Real engineering;
  ~3-4h. Defer to v5.3.x or whenever live trading actually starts.
- **C++ stamp_model binary**: runs `Backtest_RunFullValidation` end-to-end
  from CLI. ~2-3h. The bash script unblocks the workflow; binary is
  ergonomic improvement only.
- **WS reconnect reconcile** (Reconcile Phase 2): re-fetch openOrders +
  myTrades on every WS reconnect. Useful but not boot-blocking.
- **Heartbeat reconcile** (Phase 3): `reconcile_interval_sec > 0` poll
  loop. The cfg field exists but nothing reads it yet. Add when
  paranoia level rises (real money + long sessions).
- **Manual cancel detection** (Phase 4): user cancels via Binance UI
  while engine running. Edge case; defer.

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Reconcile fetch hangs on REST timeout | `binance_retry_request` already has timeout + 3-attempt retry. If it fully fails, we'd see a 0 return code — log and proceed with empty state (treat as "no exchange data"). Edge case worth a Phase 2 unit test. |
| Stamp script signature mismatch with verify_model_stamp | Ensure both use identical canonical body format. Test via round-trip. |
| Live boot hangs forever waiting for testnet REST | Reconcile is at most 3 REST calls × ~500ms timeout = ~1.5s worst case. Acceptable. |
| User pastes wrong metrics into stamp script | Refuse-on-gap-too-wide is the safety net. User can `--force` only with explicit intent. |

## Order of attack

Sequential — both small enough to ship in one session:

```
1. Tag pre-v5.2.2-reconcile-wiring
2. Edit EngineSharded.hpp:786 — wire reconcile dry-run
3. Build + test (no new tests; structural integration)
4. Commit + tag v5.2.2 + push

5. Tag pre-v5.2.3-stamp-tool
6. Write tools/stamp_model.sh
7. Round-trip verify the script generates valid stamps
8. Commit + tag v5.2.3 + push
```

End state: pre-live hardening end-to-end, dry-run mode for both
gates, ready for first live deploy with operator confidence.
