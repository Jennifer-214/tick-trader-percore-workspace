---
name: parity-check
description: Comprehensive train↔serve identity audit. Walks every train-serve handoff surface (features, labels, scaler, stamp body fields, cfg, threading, build flags) systematically looking for parity drift. Distinct from /ml-audit — /parity-check is specifically about whether the trainer's view and the engine's view of "same input → same output" remain bytewise-identical. Output is a severity-classified findings report, NOT actual edits.
type: skill
concern: shape-audit
audit_cadence: per-ship
tags: [wire-format, framework-discipline, audit-methodology]
surface: [ml-inference, training, wire-format, parser, cfg-flow]
sister_skills: [/ml-audit, /trace-deps, /readiness, /precoding-audit-gate]
loads_dynamically: [DOCS/DESIGN_PHILOSOPHY.md, DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md, DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md, DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md]
---

# /parity-check — Train↔serve identity audit

> **Uniform parameter + preload contract:**
>
> **Optional invocation args** (mirrors /precoding-audit-gate signature):
> - `<scope_path>` — plan path or specific code surface; default = full codebase sweep
> - `[focus_keywords...]` — narrow scan focus (e.g., "STAMP_BOUND" "Layer 5b" "scaler binding")
>
> **Stage 0 DESIGN_PHILOSOPHY preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 5 (Determinism family) — train-serve parity, wire format, FPN, struct padding, PRNG, AVX-512 byte-determinism, math kernel constant-iter
> - § 7 (Structural-fix family) — AUTOPOPULATE production-caller class extinction; PRE/POST registry split
>
> Cite specific § N rows in finding descriptions.

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

## Scope (per audit-scope-taxonomy.md)

This skill accepts scope as first positional arg per `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md`:

- `current` (default when no scope specified) — parity audit of recent edits + touched train-serve surfaces
- `wide` — full codebase train-serve parity sweep across all 10-category checklist; HIGH context cost; recommended quarterly + before live-readiness ships
- `scoped <glob>` — file/dir glob
- `module:<name>` — named module per MODULE_MAP.md (most-used: `ML-pipeline`, `wire-format`); iterative module-by-module parity audits
- `features` / `labels` / `scaler` / `stamp` / `cfg` (legacy invocations) — surface-narrowed scans (preserved)

**Most appropriate scope shapes for /parity-check:** `current` (during active ML-pipeline coding), `module:ML-pipeline` / `module:wire-format` (iterative deep audits), legacy surface-narrowed (`features`, `stamp`, etc.) when focused, `wide` (pre-live-readiness + quarterly).

## Invocation

- `/parity-check` — default scope `current`; recent train-serve edit audit
- `/parity-check <scope>` — explicit scope per taxonomy
- `/parity-check features` → focused on `Features_PackAll` / `Regime_ComputeSignals` / RollingStats / FOREACH_FEATURE (legacy)
- `/parity-check labels` → focused on `Label_*` body parity (legacy)
- `/parity-check scaler` → focused on FeatureStandardizer / `.scaler` sidecar / stamp's `scaler_sha256` (legacy)
- `/parity-check stamp` → focused on stamp body schema (legacy)
- `/parity-check cfg` → focused on cfg fields that affect inference (legacy)

**Examples:**
- `/parity-check current` — fast feedback during active ML-pipeline coding
- `/parity-check module:ML-pipeline` — deep audit of ML-pipeline module
- `/parity-check module:wire-format stamp` — stamp-focused scan in wire-format module
- `/parity-check wide` — pre-live-readiness + quarterly full sweep
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

0. **Stage 0 — DESIGN_SPECS preload** (added 2026-05-14 alongside
   CLAUDE.local.md condense). Parity work has a stable cluster of
   patterns it audits against; load these into context BEFORE walking
   the 10-category checklist so findings can cite specific pattern
   rules:

   - `tick-trader-percore-workspace/DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md`
     — byte-equivalence for HMAC inputs, stamp bodies, persistence
     formats, replay-determinism
   - `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md`
     — STAMP_CFG_AUTOPOPULATE + STAMP_MODEL_CONST_AUTOPOPULATE; closes
     PARITY-002/003/004/005/008 production-caller class
   - `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md`
     — FOREACH_STAMP_BOUND_CFG / FOREACH_FEATURE / FOREACH_STAMP_BOUND_MODEL_CONST
     registry shape
   - `tick-trader-percore-workspace/DESIGN_SPECS/wire-format-patterns/pre-post-cfg-registry-split-for-emit-order-preservation.md`
     — FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG / _POST_CFG canonical
     emit-order preservation
   - `tick-trader-percore-workspace/DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md`
     — explicit `_padding = 0` fields for byte-equivalence structs
   - `tick-trader-percore-workspace/DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md`
     — scalar fallback bytewise-identical to AVX-512 paths
   - `tick-trader-percore-workspace/DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md`
     — when a cfg field requires stamp-binding (5-criteria framework
     + cohort audit)
   - `DOCS/PARITY_ISSUES.md` (workspace-symlinked) — existing parity
     findings ledger; cross-ref each new finding against the
     ledger BEFORE flagging (avoid re-discovering closed items)
   - `DOCS/RECURRING_BUG_PATTERNS.md` Classes 18-21 — recurring bug
     class registry

   For each loaded doc, hold its body in context. When a finding
   surfaces, reference the matching DESIGN_SPECS rule by filename + line.

   **Auto-write contract (CLAUDE.local.md):** any new finding MUST
   be written to `DOCS/PARITY_ISSUES.md` with its severity classification
   + recommended fix; don't defer the ledger update to "operator copies
   after review". Status updates (FIXED / NOT-A-BUG / recategorization)
   on verification reruns auto-write too.

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
   - Stamp body `inference_cfg_*` fields — walk current
     `FOREACH_STAMP_BOUND_CFG_DERIVED` registry rows at
     `MemHeaders/CfgGateRegistry.hpp`. Initial cohort (v5.9.2b +
     v5.9.4a baseline) was 10 fields; current set may differ.
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
Stamp-bound cfg fields: walk current `FOREACH_STAMP_BOUND_CFG_DERIVED`
registry rows at `MemHeaders/CfgGateRegistry.hpp`. Initial cohort
(v5.9.2b + v5.9.4a baseline) was 10 fields; current set may differ.

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
- MLBuildContext populated at every entry point (live + backtest cohort)
- ConfidenceScorer init at all boot sites (current cohort surfaces via
  `/dependency-chain-trace ConfidenceScorer_Init`)
- All new struct fields zero-init'd (v5.9.1a discipline; verify
  Model_Init, EventLoopState_Init, TUI_CopySnapshotSharded
  populator)

### Section I — Determinism
- XGBoost random_state pinning (training-script concern, docs only)
- Replay determinism (v5.9.2 regression test: same backtest tick file
  → bytewise identical predictions across two runs)
- nthread=1 for reproducible XGBoost

### Section J — Observability surface coverage
- Each silent-failure mode has a distinct PerCoreSnap field (per
  failure-mode-to-snap-field discipline); enumerate current rows from
  PerCoreSnap struct
- Each failure mode has a corresponding ML Status panel branch
- Each failure mode has rate-limited CRITICAL log
  (Health_LogCriticalRateLimited)

### Section M — Claim → evidence chain requirement (added 2026-05-18 — meta-discipline M4 / Pillar B9)

Every claim in a `/parity-check` report about runtime behavior, type compatibility, or framework-handles-this-automatically MUST cite source-of-truth evidence: file:line + the relevant code excerpt OR description of what the cited code DOES.

**Anti-pattern (caught at .B.3 v1.11):** report claims "`tt::cfg_drift_compare<T>` auto-handles FPN/double cross-type comparison via implicit conversion" — but report didn't cite the template definition file:line + the relevant branch. Operator question forced verification → trust-but-verify discipline gap.

**Procedure:**

1. For every "framework handles X" / "T auto-converts to T'" / "this is already safe" claim, identify the file:line of the implementation
2. Read the cited file:line; verify the claim matches actual code
3. Cite both the file:line AND the verification result in the report

**Verdict:**
- All claims cited + verified → PASS
- Any unverified claim → demote to "unverified; needs follow-up read" status; demand follow-up before plan body lock

**Cross-references:**
- `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` § B9
- `DESIGN_PHILOSOPHY.md` § 11.5 meta-discipline M4

---

### Section N — Row-order parity (added 2026-05-18 — meta-discipline M4 / Pillar B12)

When migrating an emit walker from legacy registry (e.g., FOREACH_STAMP_BOUND_CFG body order) to master registry (e.g., FOREACH_PER_CORE_CFG_FIELD master declaration order) for currently-flagged STAMP_BOUND_CFG_DERIVED rows, verify wire-format row ordering preserves OR is annotated as intentional reorder under SOFT-bump.

**Procedure:**

1. Enumerate currently-flagged rows in master registry
2. Compare to legacy walker emit order for the same rows
3. Diff → emit reorder punch-list per row
4. Verify Layer 5b structural invariants (`tests/wire_format_invariants.hpp` I1-I5) tolerate the diff OR plan body documents intentional reorder under SOFT-bump procedure per `wire-format-byte-preservation-discipline.md`

**Verdict:**
- Order identical → PASS
- Diff annotated + SOFT-bump landing → PASS
- Diff present + not annotated → SILENT-RISK (Layer 5b invariants only catch post-facto; surface in pre-coding)

**Cross-references:**
- `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` § B12
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` Layer 5b + Layer 6
- `DESIGN_PHILOSOPHY.md` § 11.5 meta-discipline M4

---

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
