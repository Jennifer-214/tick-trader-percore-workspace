---
type: future-roadmap
status: captured (homed to .E — a future E sub-ship; data-gated on historical tick/depth corpus)
established: 2026-06-14
sprint_origin: v5.15.5.F.4d.1.E.0.10 (A6 corrupt-model discussion → operator idea: prime the statistical state from long history at boot)
gates_on: [.E per-node + determinism foundation, a historical tick/depth corpus at the configured cadence]
seams: [EventLoop_UpdateRollingState, RegimeSignals, Regime_Classify, DepthReplayState + the recorder + the backtest driver, the warm-restart snapshot, the .E.0.1 determinism net, per-node slow_state]
sister_docs: [plans/_future/2026-05-12-decoupling-endgoal-roadmap.md, plans/_future/2026-06-14-book-aware-fill-model-and-microstructure-alpha.md]
---

# Warm-start state priming — deterministic long-horizon history replay at boot

Captured 2026-06-14 from a Caramel idea (during the A6 corrupt-model gate). **Homed to `.E`** as a future sub-ship.

## The idea (operator framing)

Today, at boot/warmup the engine's rolling statistics — regression slope, R², variance, the regime classification — are computed over only the **preceding ~128 ticks** (the fixed rolling window). So at boot the engine has a thin, short-horizon view: it "knows" only the last 128 ticks, which at an arbitrary boot point is a noisy, possibly-unrepresentative slice. The first trades after boot are made on that thin context.

**The idea:** during warmup, **replay N years / months / days of historical data** (at the configured interval/cadence) **through the rolling-stats + regime machinery**, so the engine's regression/regime/variance state is **calibrated to the long-horizon history** — aware of where it sits relative to a long-run average — instead of only the last 128 ticks. Effectively: **simulate having been running continuously for ~5 years of tick data**, rather than cold-starting at an isolated, inaccurate point.

## Why it's valuable

- **Cold-start inaccuracy → calibrated first trade.** A 128-tick regression/variance at an arbitrary boot point is noise; priming from history means the *first* decision is informed by the long-run context, not a thin snapshot.
- **Regime awareness from tick 1.** The regime classifier (RANGING/TRENDING/VOLATILE/MILD_TREND) reflects where the market sits vs its long-run behaviour, not just the last 128 ticks.
- **Train-serve consistency.** The ML models were trained on history where the rolling features reflected the full context; priming the *serve-time* rolling state to match closes a cold-vs-trained statistical gap (sister to the parity discipline).
- **Determinism-friendly.** A deterministic warm-start replay (same history → same warm state) yields a reproducible, well-defined boot state — fits the `.E.0.1` determinism net (the warm state becomes part of the reproducible boot).
- **Per-node-pure (H22).** Each node warm-starts its OWN rolling/regime state from its history + resolved cfg — no cross-node coupling.

## Expanded design thoughts (for the future-self who builds it)

1. **Multi-timescale state — the fixed window can't *hold* 5 years.** A 128-tick window structurally cannot retain a 5-year horizon. Two ways to get "long-horizon awareness": (a) a **long EMA** (O(1) memory, exponential decay — cheap, captures a long-run baseline) running ALONGSIDE the short reactive window; or (b) a **precomputed long-run baseline** the warmup establishes. Likely a SHORT (reactive) + LONG (context) pair of rolling states, both primed at boot.
2. **Warmup cost vs the ≤5s boot budget.** Replaying millions of ticks at every boot may blow the warm-restart latency budget. Options: (a) **precompute the warm state offline → load a "warm-state snapshot"** (deterministic, fast boot — like the determinism golden; probably the cleanest); (b) bounded recent-history replay at full res + a precomputed long-run summary; (c) downsample the deep history. The precomputed-warm-state-snapshot keeps boot fast AND deterministic.
3. **Reuse the existing replay infra.** `DepthReplayState` + the recorder + the backtest/sharded-backtest driver already replay history deterministically. The warmup-replay reuses that machinery — run history through the slow-path rolling/regime state **without executing trades** to PRIME the state, then switch to live. (It's "backtest the warmup, keep the state, drop the trades.")
4. **Complements the warm-restart snapshot.** The engine already warm-restarts position/balance state from a snapshot; this primes the *statistical* state (rolling/regime), the missing half of a true warm-start.
5. **Determinism is mandatory.** The warm-start replay must be byte-deterministic (same corpus + cadence → same warm state) so boot state is reproducible — same bar the `.E.0.1` net holds everything else to.

## Window-size as a complementary lever (operator context, 2026-06-14)

The 128-tick window can't *hold* 5 years — but its SIZE is a tunable parameter that **subtly propagates into everything derived from it** (regression slope/R², variance, regime classification, the ML feature window). So there are TWO levers for long-horizon awareness, and they compose rather than compete:
- **Window size** (the cheap, partial lever): extend the rolling window (e.g. 128 → 1024) so more history feeds the derived stats directly. Bounded by memory + the reactive-vs-smooth tradeoff (a longer window is less reactive). Currently **128** (the operator's present choice); tunable — "we went with this for now, but the point is the *subtle downstream influence* + the tunability, captured for later."
- **Replay-priming** (the deep lever, this doc's main idea): prime the state from long history at boot so even a SHORT window boots with long-run context (a long EMA / precomputed baseline alongside the short window).

The window-size knob is the simpler near-term tune (bump it + re-evaluate the downstream derivations); replay-priming is the structural fix that **decouples long-horizon awareness from window size entirely**. Keep BOTH in scope — complementary, not either/or.

## Open shape decisions (at build time)
- Precomputed warm-state snapshot vs at-boot replay (latency vs simplicity vs determinism).
- Short-window + long-EMA multi-timescale vs a single long baseline; which features get a long horizon (regression? variance? regime hysteresis? the ML feature window?).
- Corpus scope + cadence (5y ticks is huge — depth too? per-symbol?).
- Where it sequences in `.E` (after the per-node + determinism foundation; needs the corpus).
