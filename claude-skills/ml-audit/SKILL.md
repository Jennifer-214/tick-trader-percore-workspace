---
name: ml-audit
description: Walk the ML pipeline (feature compute → model load → inference → display) systematically looking for silent failure modes and train-serve parity gaps. Output is a structured findings report with severity-classified items, NOT actual edits. User decides which items to pick up.
---

# /ml-audit — ML pipeline structural audit

## What this does

Walks the ML pipeline (feature compute → model load → inference →
display/health-log surface) systematically looking for **silent
failure modes** and **train-serve parity gaps**. **Does not edit
files.** Output is a findings report Jenny can prioritize from.

This is the systematized version of the audit pass we ran before
v5.9 (DOCS/V5_9_ML_HARDENING_AUDIT.md). Same structured walk,
spawned with a focused prompt, single concrete report.

Distinct from `/readiness`:
- `/readiness` verifies a *plan* (is this plan ready to code?)
- `/ml-audit` verifies *code state* (where are silent failures
  TODAY in the ML pipeline?)
- Different cadence: readiness fires before each phase; ml-audit
  fires before a sprint or when a paper-test surfaces issues.

## Invocation

- `/ml-audit` → audits the full ML pipeline against the standard
  10-category checklist (training, feature pipeline, stamp body,
  model load, inference, deployment, failure modes, observability,
  determinism, cfg consistency).
- `/ml-audit parity` → focused parity audit. Cross-references
  every place the live engine path and the backtest training path
  could diverge (cfg source, MLBuildContext population,
  Regime_ComputeSignals state pointers, stamp body fields, etc.).
  Smaller scope, faster.
- `/ml-audit <function-or-file>` → narrow audit of one function
  or file. Used for "I'm refactoring this body to a worker —
  what's the race surface + allocation path?"

## Pass structure

Spawn an Explore subagent. The subagent:

1. **Walks the standard 10-category checklist** (see Categories
   below). For each category, identifies concrete file:line
   citations of risk + classifies severity:

   - **CRITICAL** — blocks safe live deploy
   - **HIGH** — correctness bug or operator-blind degradation risk
   - **MEDIUM** — silent failure / observability gap
   - **LOW** — polish

2. **Cross-checks against existing audit findings.** If
   `DOCS/V5_9_ML_HARDENING_AUDIT.md` (or successor) exists,
   reference findings by ID (e.g., V5_9_AUDIT-#4) for traceability.
   Don't re-flag CONFIRMED-and-fixed items; do flag CONFIRMED+
   plan-gap items the audit doc captured but the codebase hasn't
   addressed yet.

3. **Verdict per category + overall.** Format matches /readiness:
   PASS / FIXED / GAP / DRIFT / DEFERRED / ACCEPTED.

4. **For each new finding, propose a fix.** Two-bar fix proposals:
   (a) doesn't impact functionality, (b) improves regression
   resistance (single source of truth, structural prevention,
   etc.). Reference the v5.8 single-source-of-truth principle.

5. **Output** — single markdown report, ~500-1500 lines:

```
# /ml-audit report — <date>

## Plan summary
- HEAD <sha>, tests <N>/0, calls_graph_diff <state>
- Audit scope: full / parity / <narrow target>

## Findings by severity
### CRITICAL
1. <Finding name> — <one-sentence summary>
   - File:line citations
   - Reproducer / current symptom
   - Recommended fix (high-level)
   - Effort estimate
   - Cross-ref: V5_x_AUDIT-#N if applicable

### HIGH
...

### MEDIUM
...

### LOW
...

## Cross-cutting concerns
(single fixes that close N findings)

## Live-vs-suite parity gaps (if /ml-audit parity or part of full)
| Dimension | Status | Plan-addresses? |
|---|---|---|
...

## Suggested ship sequence
- v5.x.0: <theme>
- ...

## NOT a bug (verified-safe items)
- ...
```

## Categories — full audit (10)

These match the v5.9 audit's structure. Each is a separate
heading in the output.

### Section A — Training pipeline
- Feature collection at sample boundaries (cadence parity with live)
- Label assignment (look-ahead bias, NaN handling per label_kind)
- Walk-forward purge buffer (post-gen invariant check)
- Class imbalance handling (sample_weight, scale_pos_weight)
- Held-out lock token (entropy, friction-grade documentation)

### Section B — Feature pipeline
- Verify every FeatureComputeCtx field is populated identically in
  both live + backtest paths. Currently 2 fields (signals,
  short_rolling) post v5.9.0a cleanup.
- NaN/Inf handling (FPN_IsValidFinite + std::isnan/isinf two-layer
  guard at Features_PackAll, post-v5.9.0)
- Feature scaling (mean-centering, unit-variance)
- Rolling stats warmup gate

### Section C — Model serialization / stamp body
- HMAC-SHA256 covers all fields that affect inference
- Locale pinning (LC_NUMERIC=C in both bash + in-process)
- Stamp tampering: HMAC fail closed
- Atomic writes (rename(2))
- Forward-compat parser tolerates unknown keys

### Section D — Model loading (CoreModelZoo)
- XGBoost parse failure → Model_IsLoaded returns 0 cleanly
- Concurrent load races (none; one-at-boot)
- Role discovery precedence (json → xgb → txt)
- held_out_gate_strict modes (-1/0/1) all correct

### Section E — Live inference
- Hot path seqlock read of cached_params
- Slow-path Model_Predict cost profile
- Prediction NaN/Inf guard (post-v5.9.0)
- Threshold strictly enforced (post-v5.9.0c effective_threshold field)

### Section F — Multi-core deployment semantics
- 4 cores all loaded with same model → independent slow_state but
  shared model handle
- core_N_risk_pct override semantics
- ML core mixed with AUTO/MR/etc. cores → state isolation

### Section G — Failure modes (LIVE-mode hazards)
- Model file deleted while engine running (no periodic check today)
- Memory pressure / OOM during predict
- Network feature dependencies (depth/orderbook WS reconnect → stale state)
- Confidence scorer hard-floor (post-v5.9.1)

### Section H — Observability
- Health log capture for ML entries (prediction, threshold, conf,
  registry hash) — post-v5.9.0b
- GUI surfaces for model-load failure — post-v5.9.0b ML Status panel
- ML strategy_halt_reason attribution
- Past Runs displays training context

### Section I — Determinism
- XGBoost random_state pinning (training-script concern, docs only)
- Replay determinism (same backtest tick file → bytewise identical
  predictions)

### Section J — Cfg consistency (expected.cfg vs engine.cfg)
- Field comparison list completeness
- Mismatch policy (warn vs refuse) — see model_verify_strict cfg
- Cfg-source divergence (engine.cfg vs backtest.cfg) — post-v5.9.0c
- Default-vs-deliberate cfg tracking — post-v5.9.0c

## Categories — parity-only audit (5)

When invoked as `/ml-audit parity`, narrow scope to live-vs-suite
divergence:

1. **Cfg path divergence** — which cfg does each binary read?
2. **Default cfg fallback** — what fields silently default? Are
   defaults distinguishable from deliberate?
3. **MLBuildContext population** — every state pointer populated
   identically in EventLoop_RebuildAllParameters_PerCore (live)
   and ShardedBacktestDriver (backtest)?
4. **Regime_ComputeSignals threading** — both paths pass identical
   args + produce identical RegimeSignals?
5. **Cross-binary version handshake** — engine_version + registry
   hash + format version match across engine_gui + foxml_suite?

## Categories — narrow audit (function/file)

When invoked as `/ml-audit <target>`, scope to the named function
or file. Walk:

1. **Race surface** — what state does this read/write? What's
   shared with the GUI render loop or other workers?
2. **Allocation paths** — every malloc/free/handle creation must
   have a matching cleanup on every exit path (success, error,
   cancel).
3. **Cancellation semantics** — if this is a worker pattern, where
   does cancel get polled? What's the bounded latency?
4. **UI re-entrance** — what happens if the user re-clicks the
   triggering button mid-run?
5. **Thread-safety of called APIs** — XGBoost, file I/O, etc.

This narrow mode is what we ran before v5.9.0d's Train Model
worker refactor. Output is structured per-section ~200-400 lines
of concrete file:line + mitigation proposals.

## Heuristics

### When findings cross-reference an existing audit doc

If `DOCS/V5_9_ML_HARDENING_AUDIT.md` exists, the agent should:
- Reference each closed finding by its ID (V5_9_AUDIT-#N)
- Distinguish "addressed-in-v5.9.X" from "addressed-but-not-shipped-yet"
  from "open-and-not-in-plan"
- New findings get next available IDs (V5_X_AUDIT-#N+1 onward)

### Effort estimate sanity check

Same heuristics as /readiness:
- New cfg field with parser + default + GUI tooltip: 30 min
- New X-macro entry: 5 min
- New ML feature wired through Features_PackAll + RegimeSignals + retrain: 2-3h
- Worker thread refactor (~200-line body): 30-45 min
- Stamp body schema change + bump MODEL_FORMAT_VERSION: 1-2h
- Train-serve parity regression test: 4-7h (depends on existing
  scaffolding, see tests/parity_harness.cpp)

### Anti-patterns to flag (CRITICAL)

- ML model load failure that doesn't surface to operator (CRITICAL
  in production; post-v5.9.0b should be HIGH at most)
- Feature compute returning NaN/Inf without guard at Features_PackAll
  output (post-v5.9.0 should be GAP if regressed)
- MLBuildContext field added in cfg parser but not populated in
  EventLoop_RebuildAllParameters (silent train-serve drift)
- New cfg default flipping behavior on upgrade (BREAKING-CHANGE
  unless explicitly justified)

### v5.9 architectural sprint guards

After v5.9.0a → v5.9.0d, check that the following invariants are
intact:

- `FOREACH_FEATURE(X)` registry hash unchanged unless deliberate
  retrain decision documented
- `FeatureComputeCtx` struct shape: only `signals` + `short_rolling`
  fields (the v5.9.0a aux-field cleanup)
- `Features_PackAll` returns -1 on validation failure (post-v5.9.0)
- `MODEL_FORMAT_VERSION` = 5 unchanged unless v5.9.3 standardization
  has shipped (then = 6)
- `stamp_format_version=1` field present in new stamps
- `HEALTH_CRITICAL` / `HEALTH_WARN` levels emit at min_level=0
- Engine header panel renders cfg path + tri-state core marker

## Map-update suggestions (post-audit)

Same as /readiness:

- **CODE_MAP.md regen** if audit found new functions to add
- **INVARIANTS_MAP.md update** if audit identified DRIFT/PARTIAL/GAP
- **DOCS/V5_X_ML_HARDENING_AUDIT.md update** with new findings
  (new V5_X_AUDIT-#N entries)
- **DOCS/CLAUDE_ML_INVARIANTS.md update** if a new structural rule
  surfaced

## What this skill is NOT

- Not a linter — `/dust` does that
- Not a code-quality audit — `/simplify` is closer
- Not a test runner — assumes existing tests pass
- Not predictive ("will this model make money?")
- Not a substitute for paper testing — surfaces gaps that paper
  testing would expose, but doesn't replace it

## When to use

- Before starting an ML-side multi-day plan (like v5.9 was)
- When paper testing surfaces a silent failure (run parity-only)
- Before refactoring a function body to a worker thread (run narrow)
- After a CLAUDE_ML_INVARIANTS.md update — re-audit to catch
  invariants the codebase no longer satisfies

## When to skip

- Single-function bug fixes (just fix the bug)
- Doc-only changes
- Audit was run within the last 2 weeks AND no major ML code
  changes since (re-running adds noise, surfaces stale findings)

## Author intent

Jenny's design principle (v5.8 onwards): "I want to make this good,
not just functional." This skill captures the audit pattern that
turns paper-test surprises into structurally-prevented bug classes.
Output is a findings doc operators + future-Claude can prioritize
from, not a wall of caveats.

Optional flags + their effort:
- full audit: ~10-15 min agent runtime, ~600-1500 line report
- parity-only: ~5-8 min, ~300-600 lines
- narrow (function/file): ~3-5 min, ~200-400 lines

The audit is a tool for deciding what to ship next, not a deliverable
in itself. Run it when the question "what should the next ship close?"
needs a structured answer.
