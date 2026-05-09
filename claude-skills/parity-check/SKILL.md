---
name: parity-check
description: Comprehensive train↔serve identity audit. Walks every train-serve handoff surface (features, labels, scaler, stamp body fields, cfg, threading, build flags) systematically looking for parity drift. Distinct from /ml-audit — /parity-check is specifically about whether the trainer's view and the engine's view of "same input → same output" remain bytewise-identical. Output is a severity-classified findings report, NOT actual edits.
---

# /parity-check — Train↔serve identity audit

## What this does

Walks every surface where a value computed at TRAINING TIME must
match a value computed at SERVING TIME for the same input. Catalogs
risks by severity. Cross-checks against existing protections
(`FEATURE_REGISTRY_HASH`, scaler binding, stamp body verification,
snapshot tests, etc.). **Does not edit files.** Output is a
findings report.

This is the systematized version of the parity audit run on
2026-05-02 (which found 11 new gaps post-v5.9.2, leading to
v5.9.2c + v5.9.4a closure ships). Same structured walk, spawned
with a focused prompt, single concrete report.

## Distinct from `/ml-audit`

- **`/ml-audit`** — ML pipeline STRUCTURAL audit. Silent failure
  modes, NaN handling, observability gaps, "wired but unexercised"
  paths. Walks the pipeline looking for things that could break.
- **`/parity-check`** — train↔serve IDENTITY audit. Walks every
  handoff surface (training writes X, serving reads X) and checks
  whether bit-level parity is maintained. More narrow scope; deeper
  per-surface analysis.

Run both for major ML-pipeline changes. Run `/parity-check` alone
when the change is specifically train-or-serve adjacent (e.g.
adding a scaler, changing a feature compute fn, bumping
`MODEL_FORMAT_VERSION`).

## Invocation

- `/parity-check` → audits all train-serve handoff surfaces against
  the standard 10-category checklist
- `/parity-check features` → focused on `Features_PackAll` /
  `Regime_ComputeSignals` / RollingStats / FOREACH_FEATURE
- `/parity-check labels` → focused on `Label_*` body parity / no
  `LABEL_REGISTRY_HASH` exists yet (v5.10 candidate)
- `/parity-check scaler` → focused on FeatureStandardizer /
  `.scaler` sidecar / stamp's `scaler_sha256`
- `/parity-check stamp` → focused on stamp body schema (every field
  that's verified at load)
- `/parity-check cfg` → focused on cfg fields that affect inference
  (stamp-bound or not; v5.9.2b enumerated 9)

## Execution model (added 2026-05-09 — recursion fix)

**ONE-WAY HIERARCHY. NO LAYER 3.**

```
LAYER 1: ORCHESTRATION
  - Main Claude session (or another orchestrator skill)
  - Decides WHEN to invoke this skill
  - Spawns ONE Explore subagent

LAYER 2: EXECUTION (this skill runs HERE)
  - The spawned Explore subagent reads this spec + applies the
    procedure BELOW directly
  - DOES NOT spawn further subagents
  - May apply OTHER skill checklists (/readiness, /trace-deps)
    INLINE by reference
  - Returns a single combined report
```

**If you are reading this spec inside an Explore subagent:** YOU
ARE the parity auditor. Walk the 12 sections (A-L) using your
read/grep/bash tools. Do NOT spawn a nested subagent.

See `DOCS/SKILLS_HIERARCHY.md` for the full execution model.

## Pass structure

The parity auditor (Layer 2 subagent):

1. **Walks the standard 10-category checklist** (see Categories
   below). For each category, identifies concrete file:line
   citations of risk + classifies severity:

   - **CRITICAL** — silent runtime drift; predictions shift without
     operator awareness
   - **HIGH** — silent decision drift (gate fires/blocks differently);
     observable in P&L over hours
   - **MEDIUM** — observability gap or research-integrity issue
     (training comparisons not directly comparable); operator
     workflow friction
   - **LOW** — cosmetic / documentation
   - **DOCUMENT-ONLY** — architectural bound, not fixable (e.g.
     producer SPSC drop class)

2. **Cross-checks against existing protections.** v5.9 added many
   guards; the audit must distinguish "actual gap" from
   "already-protected" findings:

   - `FEATURE_REGISTRY_HASH` (v5.8.6) — catches X-macro structural
     changes; doesn't catch function-body changes
   - Snapshot tests (v5.9.2a) — catch function-body changes for
     features + labels + ConfidenceScorer + SimpleDip strategy
   - Scaler `feature_registry_hash` binding (v5.9.3a) — catches
     scaler/feature drift independently
   - Stamp body `scaler_sha256` (v5.9.3a) — catches scaler tamper
   - Stamp body `engine_version` (v5.8.6) + `cross_major_engine`
     check (v5.9.2b) — catches major-version incompatibility
   - `acknowledge_cross_binary_version_drift` (v5.9.4) — minor-
     version + cadence WARN suppression
   - Stamp body `inference_cfg_*` fields (v5.9.2b) — 9 cfg fields
     stamp-bound: confidence_threshold_scale, barrier_gate_enabled,
     confidence_hard_block_threshold, held_out_fraction,
     freshness_tau, bandit_blend_ratio, fee_rate_maker,
     fee_rate_taker, training_poll_interval
   - Stamp body `model_num_outputs` (v5.9.4a) — catches output
     dimension mismatch
   - 3-tier strict-mode behavior (v5.9.0b refused/warned/silent
     pattern; v5.9.3a generalized)

   For each finding: cross-reference to existing protection. If
   protected, mark `ALREADY-PROTECTED` + cite the protection.

3. **Verdict per category + overall.** Format matches /readiness:
   PASS / FIXED / GAP / DRIFT-RISK / DEFERRED / ACCEPTED.

4. **For each new finding, propose a fix.** Two-bar fix proposals:
   (a) doesn't impact functionality, (b) follows established v5.9
   pattern (Surface G stamp body extension, 3-tier strict-mode,
   distinct PerCoreSnap field per failure mode).

5. **Output** — single markdown report, ~600-1500 lines.

**Save the report to a private file as well as printing it.**
Convention (set 2026-05-06): write to
`plans/plan_checks/parity-<YYYY-MM-DD>-<scope>.md` where `<scope>`
is the audit scope (`full`, `features`, `labels`, `scaler`, `stamp`,
`cfg`, etc., per the invocation). `mkdir -p plans/plan_checks` first.
Workspace-symlinked, gitignored from public repo. Print to stdout
too for live operator review.

```
# /parity-check report — <date>

## Plan summary
- HEAD <sha>, tests <N>/0, calls_graph_diff <state>
- Audit scope: full / features / labels / scaler / stamp / cfg
- Cross-check baseline: post-v5.9.4a protections inventory

## Findings by severity

### CRITICAL
1. <Finding name> — <one-sentence summary>
   - File:line citations
   - Reproducer / current symptom
   - Recommended fix (Surface G pattern OR specific to surface)
   - Effort estimate
   - Cross-ref: existing protection? (ALREADY-PROTECTED / GAP)

### HIGH
...

### MEDIUM
...

### LOW
...

### DOCUMENT-ONLY
...

## Cross-cutting concerns
(single fixes that close N findings)

## Behavior matrix (verify train and serve agree for default cfg)
| Scenario | Trainer view | Engine view | Identical? |
|---|---|---|---|
...

## Suggested ship sequence
- v5.x.0: <theme>
- ...

## NOT a bug (verified-safe items)
- ...
```

## Categories — full audit (10)

These match the 2026-05-02 audit's structure (which led to v5.9.2c
+ v5.9.4a). Each is a separate heading in the output.

### Section A — Tick consumption parity
- Live: `Tick<F>` (FPN price/qty/timestamp_us)
- Backtest: `HistoricalTick` (double price/qty, int64 timestamp_us)
- Question: do the two structs surface IDENTICAL data to
  `Regime_ComputeSignals` / `Features_PackAll`?
- Risk: FPN→double round-trip differences; field ordering / packing
- Verifier: spot-check by tracing one tick from CSV/WS through to
  RegimeSignals fields

### Section B — Feature pipeline parity
- Verify every `FeatureComputeCtx` field is populated identically in
  both live + backtest paths
- NaN/Inf handling (FPN_IsValidFinite + std::isnan/isinf two-layer
  guard at Features_PackAll, post-v5.9.0)
- Feature scaling (mean-centering, unit-variance — v5.9.3 scaler)
- Rolling stats warmup gate
- Snapshot test coverage for Compute fn bodies (v5.9.2a)

### Section C — Label pipeline parity
- Label_* function bodies (no LABEL_REGISTRY_HASH yet — v5.9.2a
  snapshot tests are sole protection)
- NaN handling per label_kind (v5.9.1: binary→0.5, regression→0.0,
  multiclass→NAN sentinel skip)
- Walk-forward purge buffer (v5.9.0 post-gen invariant check)

### Section D — Scaler sidecar binding (v5.9.3+)
- Sidecar's embedded `feature_registry_hash` matches build's
- Sidecar's `num_features` matches `NUM_REGISTERED_FEATURES`
- Sidecar's `stddev_floor_q` Q32 round-trips correctly
- Stamp's `scaler_sha256` matches actual sidecar SHA-256
- Compute math identical to apply math (double, not FPN; std::fmax floor;
  cast→subtract→divide→cast sequence)
- Two-layer NaN guard (pre-apply via Features_PackAll + post-apply
  finite check)

### Section E — Stamp body schema parity
- Verifier parses every emitter field with `has_*=0` default for
  legacy stamps
- HMAC signature inclusive of all key=value lines (canonical body)
- Locale pinning (LC_NUMERIC=C in both bash + in-process)
- Atomic stamp write (`.tmp + rename`)
- Forward-compat parser tolerates unknown keys
- Bash `tools/stamp_model.sh` produces identical canonical body for
  identical inputs (v5.8.8 round-trip test)

### Section F — Cfg parity (inference-affecting fields)
Stamp-bound cfg fields (v5.9.2b + v5.9.4a):
- confidence_threshold_scale, barrier_gate_enabled,
  confidence_hard_block_threshold, held_out_fraction,
  freshness_tau, bandit_blend_ratio, fee_rate_maker, fee_rate_taker,
  training_poll_interval, model_num_outputs

NOT stamp-bound (potential gaps):
- Anything else that affects inference. Walk ControllerConfig.hpp
  for fields used by ML_BuildParameters or strategy dispatchers.

### Section G — Cross-binary handshake
- ENGINE_VERSION_STRING in stamp's `engine_version` field (v5.8.6)
- Cross-major detection (v5.9.2b `cross_major_engine` flag)
- Cross-minor WARN (v5.9.4 `acknowledge_cross_binary_version_drift`)
- Cadence parity (v5.9.4a `training_poll_interval` boot WARN)
- Build flags (USE_NATIVE_128, USE_XGBOOST) — currently
  documentation-only; v5.10 candidate for fingerprint binding

### Section H — Threading + initialization
- MLBuildContext fully populated in live (`EventLoop_RebuildAllParameters_PerCore`
  at ~line 1800+) AND backtest (`BacktestSharded.hpp`)
- ConfidenceScorer init at all 3 boot sites
  (ControllerEventLoop.hpp:509, EngineSharded.hpp:834,
  BacktestSharded.hpp:267)
- All new struct fields zero-init'd (v5.9.1a discipline; verify
  Model_Init, EventLoopState_Init, TUI_CopySnapshotSharded
  populator)

### Section I — Determinism
- XGBoost random_state pinning (training-script concern, docs only)
- Replay determinism (v5.9.2 regression test: same backtest tick file
  → bytewise identical predictions across two runs)
- nthread=1 for reproducible XGBoost

### Section J — Observability surface coverage
- Each silent-failure mode has a distinct PerCoreSnap field:
  - ml_model_load_failed (v5.9.0b)
  - ml_scaler_load_failed (v5.9.3a)
  - ml_nan_feature_events / ml_nan_prediction_events (v5.9.0b)
  - warmup_progress_pct (v5.9.1)
- Each failure mode has a corresponding ML Status panel branch
- Each failure mode has rate-limited CRITICAL log
  (Health_LogCriticalRateLimited)

### Section L — Production-caller field-population audit (v5.9.5b addition)

Verifying that a stamp body / serialization struct contains a field
is NOT the same as verifying every production caller POPULATES that
field. v5.9.5b found that v5.9.2b + v5.9.3a + v5.9.4a added 10
inference cfg fields to `StampInferenceCfgInputs`, with full verifier
coverage and snapshot tests for the function — but the in-process
emit at `Backtest_RunFullValidation` (the suite's Run Full Validation
button) passed `nullptr` for `inf`. Result: every suite-emitted
stamp lacked all 10 fields' protection. Tests passed because they
called `stamp_write_for_model` directly with synthetic `inf`, not
through the production caller.

Same shape: a CLI tool gets a `--scaler-sha256=` flag (v5.9.3b)
and the GUI Run Model worker logs the SHA — but no caller ever
passes the SHA into `stamp_write_for_model`'s `scaler_sha256_hex`
field for the auto-stamp path.

For each newly-added stamp body / serialization field, /parity-check
must walk:

1. **Field defined in struct** — yes / no
2. **Function under test populates it round-trip** — yes / no
3. **EVERY production caller populates it** — yes / no (the gap class)
4. **CLI tool exposes it (if applicable)** — yes / no
5. **GUI suite exposes it via cfg/UI input** — yes / no

Items 3+ are the silent-failure-class. Severity classification:

- **CRITICAL** if the field's protection is silently disabled in
  production (e.g. cfg-binding fields not emitted = stamps don't
  catch cfg drift)
- **HIGH** if the field is partially populated (some callers populate,
  others don't = inconsistent stamps in same operator workflow)
- **MEDIUM** if the field exists but no production path consumes it
  yet (dead schema)

Heuristic for finding the gap quickly:

```bash
# Does any non-test code construct StampInferenceCfgInputs?
grep -rn "StampInferenceCfgInputs\s\+[a-z_]\+\s*=" \
   --include="*.hpp" --include="*.cpp" \
   $REPO | grep -v tests/
```

If the answer is "no production callers" but the verifier reads the
fields, the protection is silently disabled. Same shape works for
any other input-aggregator struct.

### Section K — Build-warning audit (v5.9.5a addition)

Source-read audits miss bugs the compiler can statically detect.
Every full /parity-check pass MUST run `./build.sh test gui suite`
and grep the output for warnings. Specific classes that are
parity-relevant:

- **`-Wstringop-overflow`** — manually-sized stack buffers in
  serialization paths (e.g. `uint8_t body_buf[N + M + ...]`).
  v5.9.5a found a 564-byte write into a 556-byte buffer in
  `FeatureStandardizer.hpp` write+verify paths — `hash_w` field
  added without updating the buffer formula. Stack overflow,
  silent until compiler stack layout shifts.
- **`-Waggressive-loop-optimizations`** — UB in loop bounds; can
  cause divergence between debug + release builds (parity surface
  if loop iterates differently across builds).
- **`-Wuninitialized`** — read of stack-allocated state that
  wasn't zero-init'd (v5.9.1a was an instance: 7 CoreContext
  fields read garbage on first slow-path rebuild because
  EventLoopState_Init didn't zero them). Compiler often misses
  these for non-trivial types but worth grepping.
- **`-Wstringop-truncation`** — `strncpy` patterns where the
  truncation isn't intentional. Common in path-building for stamp
  files / scaler sidecars.

For each warning surfaced by the build:
- Severity = CRITICAL if it lands in serialization / load paths
  (silent file format corruption, false SHA matches, stack overflow)
- Severity = HIGH if init-time / cfg parsing
- Severity = MEDIUM/LOW otherwise

The audit must NOT silently accept "warnings exist but tests pass."
Tests pass when the bug's symptoms happen to land in dead stack
space; a compiler / -O level / ASAN run change can flip that.

## Categories — narrow audit (single surface)

When invoked as `/parity-check <surface>`, scope to one section
above. Output is condensed (200-400 lines) but with deeper
per-section analysis.

## Heuristics

### When findings cross-reference an existing audit doc

If `DOCS/V5_9_ML_HARDENING_AUDIT.md` (or successor) exists, the
agent should:
- Reference each closed finding by its ID (V5_9_AUDIT-#N)
- Distinguish "ALREADY-PROTECTED-by-vX.Y" from "open-not-in-plan"
- New findings get next available IDs (V5_X_AUDIT-#N+1 onward)

### Cross-reference DOCS/PARITY_ISSUES.md before flagging (added v5.14.1.B)

`DOCS/PARITY_ISSUES.md` is a running ledger of known parity findings
across all sprints. Format: `PARITY-NNN` IDs with status (OPEN /
OPEN-DEFERRED / FIXED / DOCUMENTED-RISK / NOT-A-BUG).

**Before flagging a new finding:**
1. Grep `PARITY_ISSUES.md` for the file:line / cfg-field /
   function-name your finding involves
2. If a matching `PARITY-NNN` entry exists:
   - **Status: OPEN** → cite the existing ID; mark as STILL-OPEN in
     your audit, don't re-allocate a new ID
   - **Status: OPEN-DEFERRED** → cite the ID + the target ship; flag
     if the deferred ship is already past
   - **Status: FIXED** → verify the fix actually holds (the FIXED →
     CLOSED transition needs ONE clean parity-check run); re-open
     if regression detected
   - **Status: DOCUMENTED-RISK** → cite the ID + skip; the risk is
     accepted by the operator
   - **Status: NOT-A-BUG** → cite the ID + skip; investigation
     proved safe
3. If no matching entry:
   - Allocate next `PARITY-NNN` (highest existing + 1)
   - **AUTO-WRITE the new entry directly into
     `DOCS/PARITY_ISSUES.md`** — append the standard format block
     (Found / Severity / Class / Site / Symptom / Root cause / Fix
     path / Target ship / Status: OPEN / Workaround) under the
     "## Issues" section
   - Also include the entry inline in the audit report for visibility
   - Add a status-update log entry to the dated log section at the
     bottom of `PARITY_ISSUES.md` referencing the audit report path

**Auto-write contract** (set 2026-05-09 per Caramel feedback):
- New findings MUST be added to `PARITY_ISSUES.md` by the audit
  agent — not deferred to operator review. The ledger is the single
  source of truth; a finding that exists only in an audit report
  but not in the ledger is invisible to future audits.
- Status updates (FIXED, NOT-A-BUG, OPEN-DEFERRED reclassification)
  also auto-write to the ledger after a verification rerun.
- Operator reviews the ledger at sprint boundaries to recategorize
  / accept / reject; agent does the mechanical bookkeeping.

**Why this matters:** without the cross-reference step + auto-write,
every audit re-discovers the same OPEN-DEFERRED issues (noise) and
may incorrectly re-flag DOCUMENTED-RISK items (operator confusion).
Without auto-write, findings live only in transient audit reports
and disappear from the operational view.

### Effort estimate sanity check

Reference effort costs (from v5.9 sprint):
- New stamp body field (Surface G pattern): 30-45 min
- New PerCoreSnap field + populator + ML Status panel branch: 30 min
- New cfg field with stamp binding: 1h
- New helper in BacktestEngine.hpp: 30 min
- Snapshot test for a new compute fn: 15 min
- Sidecar binary format extension: 2-3h (similar shape to v5.9.3a)

### Anti-patterns to flag (CRITICAL)

- Hardcoded threshold value used in two places that should agree
  (e.g. v5.9.4a found 0.52 binary threshold in display logic that
  doesn't match training's actual baseline for multiclass)
- New stamp body field without `has_*` flag forward-compat
  (BREAKING-CHANGE for legacy stamps)
- Display reads a different field than execution writes
  (display↔execution invariant breach, v5.6.0 pattern)
- Cfg field added but consumer not wired (half-wired, v4.7.x lesson)
- Failure mode added without distinct PerCoreSnap field (operator
  conflates failure causes)
- Silent fallback path on a parity check failure (forbidden;
  3-tier strict-mode rule)

### v5.9 architectural sprint guards

After v5.9 closes (v5.9.5+), check that the following invariants
are intact:

- `FOREACH_FEATURE(X)` registry hash unchanged unless deliberate
  retrain decision documented + version field bumped
- `FeatureComputeCtx` struct shape: only `signals` + `short_rolling`
  fields (the v5.9.0a aux-field cleanup)
- `Features_PackAll` returns -1 on validation failure (post-v5.9.0)
- `MODEL_FORMAT_VERSION` = 5; bump only when MODEL FILE serialization
  shape changes (NOT for stamp body extensions — those use Surface G
  forward-compat pattern with `has_*` flags)
- Stamp body has all 9 inference_cfg_* fields available
  (confidence_threshold_scale, etc. per v5.9.2b) plus model_num_outputs
  (v5.9.4a)
- `HEALTH_CRITICAL` / `HEALTH_WARN` levels emit at min_level=0
- ML Status panel renders all 4 distinct states (model_load_failed,
  scaler_load_failed, scaler: applied, scaler: NONE)
- Engine boot WARN fires for cross-major engine_version + cross-minor
  + cadence mismatch (suppressible via cfg)
- Health log rotation works (v5.9.4)

## Map-update suggestions (post-audit)

Same as /readiness:

- **CODE_MAP.md regen** if audit found new functions to add
- **INVARIANTS_MAP.md update** if audit identified DRIFT/PARTIAL/GAP
- **DOCS/V5_X_ML_HARDENING_AUDIT.md update** with new findings
  (new V5_X_AUDIT-#N entries)
- **DOCS/CLAUDE_ML_INVARIANTS.md update** if a new structural rule
  surfaced
- **DOCS/PARITY_LIFECYCLE.md update** if a new surface added
- **DOCS/PARITY_VERIFICATION_CHECKLIST.md update** if a new
  per-surface check pattern emerged

## What this skill is NOT

- Not a linter — `/dust` does that
- Not a code-quality audit — `/simplify` is closer
- Not a structural-failure-mode audit — `/ml-audit` covers that
- Not a test runner — assumes existing tests pass
- Not predictive ("will this model make money?")
- Not a substitute for paper testing — surfaces gaps that paper
  testing would expose, but doesn't replace it

## When to use

- Before starting an ML-side multi-day plan that touches train-serve
  handoff (scaler, stamp, cfg-binding)
- When paper testing surfaces a parity surprise (run focused mode
  for the suspected surface)
- After any FOREACH_FEATURE / FOREACH_TARGET change
- After any stamp body schema change
- Before declaring a sprint complete (sprint-exit gate, like v5.9.4a
  ran before postmortem)

## When to skip

- Single-function bug fixes that don't cross train-serve boundary
- Doc-only changes
- Audit was run within the last 2 weeks AND no major ML code
  changes since (re-running adds noise, surfaces stale findings)

## Author intent

Jenny's design principle (v5.8 onwards): "I want to make this good,
not just functional." This skill captures the parity audit pattern
that turns paper-test surprises into structurally-prevented bug
classes. Output is a findings doc operators + future-Claude can
prioritize from, not a wall of caveats.

The skill is a tool for deciding what to ship next, not a
deliverable in itself. Run it when the question "are we still at
1:1 train↔serve identity?" needs a structured answer.

Optional flags + their effort:
- full audit: ~10-15 min agent runtime, ~600-1500 line report
- narrow (features/labels/scaler/etc.): ~5-8 min, ~300-600 lines

## Background — why this is distinct from /ml-audit

The 2026-05-02 audit run during v5.9 walked 25 categories: tick
consumption, slow-path observation timing, cfg-driven feature
behavior, RollingStats / Regime state init, hour-of-day timestamp
source, RORRegressor state, FlowState etc., depth/orderbook,
tick precision, bandit state persistence, held-out integrity,
build flag drift, XGBoost reproducibility, sample interval cadence,
stamp body locale pinning, atomic write residue, per-core load
order, PerCoreSnap field-init, fee model parity, snapshot version
vs cfg coupling, ConfidenceScorer IC buffer drift, BarrierGate
constants, health log JSONL schema, CSV row order, producer
drop. Found 11 new gaps post-v5.9.2 (4 CRITICAL/HIGH, 4 MEDIUM,
2 LOW, 1 DOCUMENT-ONLY).

Those 11 findings drove v5.9.2c (CSV sort, IC buffer, HeldOutSplit
token, PerCoreSnap audit) + v5.9.4 (cross-binary handshake) +
v5.9.4a (model_num_outputs, poll_interval cadence WARN, Gap I
auto-unlink). The methodology generalized — that's what this skill
captures.

The pattern's worth: a single comprehensive audit caught issues
that 4 separate readiness checks missed, because readiness checks
verify "this plan against this surface" and parity audits walk
"every surface against every protection."
