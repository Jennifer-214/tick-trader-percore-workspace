# Overnight test checklist (v5.4.5)

Test session kicked off 2026-04-30 evening. Engine running v5.4.5
binary. Looking at this in the morning — what to check, in order.

## Where we left off

Today we shipped v5.4.0 → v5.4.5 (six versions, all tagged on origin).
Ten bug classes documented in `DOCS/RECURRING_BUG_PATTERNS.md`:

- Class 1: strategy lifecycle orphans → fixed (v5.4.0)
- Class 2: display ↔ execution divergence → fixed (v5.4.0 P4 / 5.4.1 / 5.4.2)
- Class 3: drain count under partials → fixed (v5.4.1)
- Class 4: snapshot save/load asymmetry → fixed (v5.4.3)
- Class 5: Reset Paper completeness → fixed (v5.4.3)
- Class 6: OMS counter persistence → fixed (v5.4.4)
- Class 7: threading races → audited clean (no findings)
- Class 8: cost-gate + vol-scale silently inactive → documented, NOT fixed (v5.5+ feature port)
- Class 9: shutdown blocking on user-undesired ops → fixed (v5.4.5)

## Morning checklist — in priority order

### 1. Did the engine run all night without crashing?

```bash
ps aux | grep engine_gui | grep -v grep
ls -la logging/health.jsonl
# Check process uptime; check for engine_gui zombies / extra processes
```

If process is dead with non-zero exit, check `logging/` for stderr
captures. Most likely cause of overnight crash: a corner case the
v5.4.0-5 changes introduced that wasn't covered by 888 tests.

### 2. Did Bug B reproduce? (Per-Core P&L stuck at zero)

Open the GUI. Look at the Per-Core P&L panel. After overnight trades:
- If C0/C1/C2/C3 show non-zero realized P&L matching trade history sum
  → **Bug B may have been a stale-snapshot artifact from earlier session.**
  We didn't fix anything that would have made counters bump if they
  weren't bumping before. So if they're working now, the bug fixed
  itself via the snapshot-version reset. Document that and move on.
- If counters still all zero despite many trades → **Bug B reproduces.**
  Inspect `logging/health.jsonl`:
  ```bash
  jq '. | select(.category=="drain")' logging/health.jsonl | head -50
  ```
  Look at: `my_mask`, `last_open`, `last_close`, `realized_pre`. If
  realized_pre stays 0 across many drain entries while the masks
  reflect real fill bits, the increment path is failing — narrow to
  the specific path that misses.

### 3. Did the new buy gates fire correctly?

User reported "the new buy gates are working so much better" before
sleep. Verify it sustained overnight:
- Trade History should show entries from multiple cores (not just
  one repeating).
- Strategies should show different behavior — MR buying dips, MOM
  buying breakouts, EMA gated by crossover, SimpleDip on dips.
- If all cores cluster on identical entries / identical exits, the
  v5.4.0 lifecycle wiring may not be effective in practice.

### 4. Did shutdown work cleanly?

When the user is awake and ready to stop the engine: Ctrl+C should
exit within 5 seconds even with open positions. v5.4.5 fix.

If shutdown still hangs, the force-close logic (now bypassed) may
not have been the only blocker. Check logging for the per-stage
"[sharded] joining X..." prints that show which thread is hung.

### 5. Are session-cumulative fees showing correctly now?

Account header: `fees: $X.XX` should show the real total (was always
$0.00 in sharded pre-v5.4.1). Compare against sum of Trade History
"Fee" column.

### 6. Reset Paper still works cleanly?

If user clicked Reset Paper at any point: Per-Core P&L should be
fully zero (not just partially), no ghost cooldown blocking next
trades.

## If Bug B reproduces — next investigation steps

1. Capture `logging/health.jsonl` and share with Claude.
2. Check `last_closed_mask` value relative to `my_mask` per drain
   entry. If they overlap but `realized_pre` doesn't bump → check
   whether HandleFill actually wrote `last_fill[slot].exit_net_pnl`.
3. If `last_closed_mask` doesn't match expected slots → check the
   drainer thread's processing order; maybe the mask gets cleared
   before DrainPostFill sees it.

## If everything's clean

- v5.4.5 is the new stable. Tag it on main branch when comfortable.
- Move to v5.5: Class 8 port (cost gate + vol scale) as the next
  feature ship.
- Or take a break. Today shipped a lot.

## Don't fix anything overnight

Claude will not ship any more code changes while user sleeps. Risk
of breaking the test session > value of one more polish fix. Audit
findings can be documented but won't be acted on until user is back.
