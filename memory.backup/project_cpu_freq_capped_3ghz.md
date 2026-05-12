---
name: CPU clock capped at 3 GHz on dev machine
description: Operator capped CPU clock at 3 GHz (2026-05-07) to keep laptop temps under control during long paper-test runs; latency benchmarks reflect 3 GHz, not boost.
type: project
originSessionId: eb96e5e5-7931-48ae-9510-0b0433c695bf
---
Operator capped the dev machine's CPU clock at 3 GHz on 2026-05-07.
Reason: prior to the cap, sustained 100%-usage runs (paper trading,
LATENCY_BENCH builds, cmake -j16) drove CPU temps high enough that
the operator stopped long runs early ("welp that spikes temps LOL"
on 2026-05-06). Capped at 3 GHz: temps stay ≤ 60°C at 100% usage.

**Why:** Long-running paper/backtest sessions are the operator's
primary engine validation workflow. Thermal throttling mid-run would
introduce timing noise that contaminates the test.

**How to apply:**
- Latency benchmarks (LATENCY_BENCH=ON, hot-path p99 captures) are
  now 3 GHz numbers, not boost. State this explicitly when reporting
  bench results — "v5.11.20 hot-path p99 = NNns @ 3 GHz" — so future
  comparisons against pre-cap numbers (anything pre-2026-05-07) are
  apples-to-apples.
- Production-target context: this is closer to real colo deployment
  (where pinned RT-class cores typically hold a stable freq) than
  pre-cap boost behavior was. Reporting 3 GHz numbers as the
  comparison baseline is fine.
- Don't be surprised if v5.11.20 (branchless ring buffer commit) shows
  smaller absolute p99 wins than the audit's pre-cap forecast — the
  delta math should still hold (relative improvement preserved
  across freq scaling for memory-stalled hot paths).

Intentionally NOT mirrored to engine config: this is OS-level
governor work, not engine cfg. `DOCS/OPERATOR_DEPLOYMENT.md` already
covers the production-side recipe (intel_pstate + perf governor +
pin-to-isolated-core); the laptop's 3-GHz cap is the dev-side analog.
