---
type: idea
established: 2026-06-16
surface: [ml-inference, feature-engineering]
status: research-question
---

# ML inference feature-window granularity — single-tick vs window/rolling-window

> Homed from a loose `note` file at the workspace root (`/close-session` Stage 4.6 fix-sweep, 2026-06-16). Operator-captured idea — preserved verbatim below + framed.

**The question (verbatim):** *"for the ML inference, training on deriving the inference based on a single tick, or a window before or rolling window stats. should investigate further."*

**Framing / why it matters:** the inference's feature basis is a design choice with train-serve + latency consequences:
- **single-tick** features — lowest latency, lowest state, but noisiest signal;
- **window-before** (fixed lookback at decision time) — more context, bounded compute;
- **rolling-window stats** (the existing `RollingStats` cohort: W=128/256/512/1024) — the current basis; richest signal but the dominant slow-path cost (the ROLLING section, + the shared-market-state / SPMC sharing question, D-230).

**Cross-refs:** the rolling-window cost + the cluster-shared-market-state question (D-230 — compute once per cluster, share across nodes) directly bears on this; the train-serve feature-parity discipline (M5) constrains any change. Investigate alongside the `.E` cluster work + the FeatureRegistry.

**Disposition:** research question, not yet scoped. Revisit when the cluster/optimization work (E.1.2/E.1.3) opens the rolling-stats surface.
