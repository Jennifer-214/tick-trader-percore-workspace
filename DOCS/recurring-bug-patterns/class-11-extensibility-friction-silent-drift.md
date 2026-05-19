---
type: ledger-template
class_id: 11
title: Extensibility friction causing silent drift
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 11 — Extensibility friction causing silent drift

**Surface:** live (multi-site addition pattern — N sites must agree; X-macro registry pattern is the structural fix).

**Symptom:** A category that supports extension (codes, metrics,
panels, etc.) is implemented at multiple call sites without a
canonical spec. Each site evolves independently. Eventually two
sites disagree: same input, different output. Operator-visible
behavior diverges from operator-expected behavior; sometimes the
divergence affects evaluation logic (optimizer rankings, drift
detection, walk-forward gap thresholds) — making the entire
selection mechanism unreliable.

This class is distinct from Class 1 (lifecycle orphans — code
ABSENT) and Class 2 (display vs execution divergence across
layers — code in the WRONG LAYER). Class 11 is code IN MULTIPLE
PLACES that should agree but doesn't.

**Root cause:** Adding the first instance of a category is fine.
Adding the second copy-pastes the formula. By the third or fourth
site, the formula has been retyped slightly differently. There's
no single source of truth, so no test fails — both sides "look
reasonable in isolation."

**Detection:**
```bash
# Grep the formula's identifying token across the whole codebase.
# E.g. for "profit_factor", search for the divisor pattern.
grep -rnE "(profit_factor|gross_wins.*gross_losses)" --include="*.hpp" .
# Eyeball the matches: do all sites use the same epsilon? Same
# fabs? Same sentinel? If not, you've found a Class 11 instance.

# Variant per-category: search for any "X_names[]" or "X_table[]"
# array hand-maintained in parallel with an enum:
grep -rnE "static const char\* \w+_names\[\]" --include="*.hpp" .
# Mirror arrays are Class 11 in waiting.
```

**Known instances:**
- v5.6.0 — Controller `halt_reason = 10` (book-imbalance) was added
  in `ControllerEventLoop.hpp` but `halt_names[]` mirror in
  `GUI/DashboardPanels.hpp` had only indices 0-9. The display
  silently dropped the imbalance reason — operator saw "halted"
  with no reason text. Fix: the bound check made imbalance
  display work; the structural fix didn't land until v5.8.3.
- v5.8.3 (preventive) — converted `halt_reason` raw integers to
  `HALT_*` named constants via `FOREACH_HALT_REASON(X)`. Mirror
  retired; `HALT_NAMES` is the registry-driven single source.
  Found 8 indirect raw-int sites via `zero_gate(N)` lambda calls
  that the original plan had missed.
- v5.8.4c — `profit_factor` had 4 different formulas across 4
  sites: `(gl > 0.0001)`, `(gl > 0.001)`, no guard, and
  `(gl > 0.001)` with `-1.0` sentinel. The `-1.0` sentinel was
  packed into `profit_factor` itself and read by
  `OPT_METRIC_PF` — the walk-forward optimizer ranked
  perfect-wins runs LOWER than mediocre ones. Fix: canonical
  `Compute_ProfitFactor` returns `0.0` for no-losses; new
  `all_wins_run` flag handles distinct display.
- v5.8.4c — `expectancy` used `fabs(avg_loss)` in BacktestEngine
  but not in EngineTUI/ShardedSnapshot. Harmless when invariant
  held; defensive against future sign-flip. Fix: canonical
  `Compute_Expectancy` keeps `fabs`.
- v5.8.4c — `max_drawdown` had two independent implementations
  (post-hoc walk in `BacktestEngine` vs incremental per-tick in
  `BacktestSharded`). Formal equivalence ≠ bytewise FP
  equivalence. Fix: shared `MaxDrawdown_UpdateIncremental`
  helper called from both paths — bytewise identical by
  construction.

**Prevention:**
- **X-macro registry pattern.** Every "category that supports
  extension" should have a `FOREACH_<CATEGORY>(X)` registry +
  auto-generated arrays + `static_assert` size parity. See
  `DOCS/EASY_ADDITIONS_INVARIANTS.md` for the canonical spec.
- **Single-helper pattern for shared formulas.** When a metric or
  computation is needed at two cadences (post-hoc + incremental,
  backtest + live), extract a single inner-update helper that
  both paths call. Bytewise FP identity is structural, not test-
  validated.
- **Display vs math separation.** When a metric needs distinct
  display semantics (e.g. "all wins" → "∞"), use a separate flag
  rather than a sentinel value packed into the metric itself.
  Sentinel values get read by downstream consumers (optimizers,
  comparison logic) and silently corrupt rankings.
- **Readiness deep-audit before any phase that adds an extensibility
  point.** The v5.8.4c drift findings only surfaced when the
  readiness skill specifically grepped for divergent formulas —
  flagging "Class 11 in waiting" before code was written.

**Adjacent**: see `DOCS/STRATEGY_REFACTOR_IDEAS.md` for the longer-
term observation that adding MORE strategies will increase the
chance of strategy-regime miscalibration. The X-macro refactor
proposed there would NOT fix this class — it just makes new
strategies easier to add. Class-10 prevention is regime-gating +
filters + observability, all already in place post-v5.7.
