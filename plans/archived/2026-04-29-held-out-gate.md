# Held-Out Validation Gate — Plan (2026-04-29)

## Why this matters

You already have the **infrastructure** for held-out discipline
(`HeldOutSplit_Make` token-locked test sets, `Backtest_RunFullValidation`
walk-forward + held-out, `gap_acceptable_threshold` policy). What's
missing is the **enforcement**: nothing prevents you from loading a
model that hasn't passed the held-out gate into a live core.

Today's failure mode:
1. Train a model on a tick day, get 60% in-sample accuracy → looks great
2. Forget to run held-out validation → assume it'll generalize
3. Drop the `.bin` file into `models/`, set `core_N_model_path=...`
4. Engine loads model on boot → fires entries on production traffic
5. Out-of-sample edge is actually 50% (random) → bleed money

The discipline lives in CLAUDE.md (`Held-Out Validation Discipline`) but
**isn't enforced**. Anyone (you under deadline pressure, future you who
forgets) can skip it.

## Goal

Make it **mechanically impossible** to load a model into a live core
without an attestation that:
- Held-out validation has run on this exact model file
- Generalization gap was below the threshold
- The attestation is signed (tamper-evident)

## Design

### Stamp file

Alongside each `.bin` model, require a `.stamp` file:

```
models/
  ml_buy_signal_2026-04-28.bin     ← XGBoost binary
  ml_buy_signal_2026-04-28.stamp   ← attestation (NEW)
```

`.stamp` is small JSON-ish text:

```
{
  "model_file_sha256": "<sha256 of the .bin>",
  "model_format_version": 12,
  "trained_on": "2026-04-28",
  "wf_mean_val_metric": 0.55,
  "held_out_metric": 0.53,
  "generalization_gap": 0.02,
  "gap_threshold_used": 0.05,
  "stamp_signature_sha256": "<sha256 of all fields above + secret>"
}
```

The "secret" is a config-time value (`held_out_stamp_secret` cfg field,
unique per machine, gitignored). It's friction-not-security: prevents
accidental tampering, audits intentional tampering. Same posture as the
existing held-out unlock token.

### Boot-time check

When `core_N_model_path` is set:

1. Read `<model>.bin` — compute sha256 → `actual_model_sha`
2. Read `<model>.stamp` — parse JSON
3. Verify `model_file_sha256 == actual_model_sha` (binary not tampered post-stamp)
4. Verify `stamp_signature_sha256` against the rest of the stamp (stamp not tampered)
5. Verify `model_format_version` matches engine's `MODEL_FORMAT_VERSION`
6. Verify `generalization_gap <= gap_threshold_used`
7. If ANY check fails: refuse to boot with that model. Log CRITICAL with
   the specific failure. User must either re-stamp (rerun validation)
   or use a different model.

Cfg escape hatch (DEV ONLY): `cfg.held_out_gate_strict = 0` skips the
check, defaults to 1. Strict-off boots with a WARN log so it's visible.
Useful for testing model code without re-stamping every iteration.

### Stamp generation

A new tool: `tools/stamp_model.cpp` (compiled in build/) that runs
`Backtest_RunFullValidation` on a model + tick day and writes the
`.stamp` file. Takes:

```
stamp_model --model models/foo.bin --ticks data/BTCUSDT/2026-04-28.csv \
            --train-fraction 0.7 --val-fraction 0.15 \
            --held-out-fraction 0.15
```

Internally:
1. Load tick data
2. Make held-out split (locks the test set)
3. Run walk-forward CV on `[0, trainval_end_idx)`
4. Unlock test set with token
5. Run held-out evaluation ONCE
6. Compute gap = `|wf_mean_val - held_out|`
7. If `gap > gap_threshold_used`: print warning, write stamp anyway
   (user decides whether to ship with it; the boot-time check will fail)
8. Hash + sign + write `.stamp`

### Foxml_suite integration

The existing "Save Run" panel in `BacktestPanels.hpp` already produces
`expected.cfg` bundles. Extend it to ALSO produce `.stamp` files:

- "Save Run" → writes `runs/<bundle>/expected.cfg` (existing)
- New checkbox "Stamp model for live deploy" → also writes
  `runs/<bundle>/<modelname>.stamp` and copies the `.bin`

So the suite's UI is the primary path; CLI tool is for headless training.

## Implementation phases

### Phase 1 — Stamp format + boot check (~2-3h)

1. Define stamp format (JSON-ish, see above)
2. Add `held_out_stamp_secret` cfg field
3. Add `held_out_gate_strict` cfg field (default 1)
4. Add `verify_model_stamp()` helper in `ML_Headers/ModelInference.hpp`
5. Call helper from `CoreModelZoo_LoadAll()` for each model — refuse on fail
6. Add `tools/stamp_model.cpp` (CLI)
7. Tests: stamp-write + stamp-verify round-trip; tamper detection;
   format-version mismatch; gap-too-wide rejection

### Phase 2 — Foxml_suite integration (~1-2h)

1. Add stamp checkbox to "Save Run" panel
2. Call same `stamp_model` logic via library function
3. Update suite docs (when stamping is required, what to do if gap fails)

### Phase 3 — Existing models (~30 min)

Walk through `models/` directory, run `stamp_model` on each existing
model. Models that don't pass the gap threshold get flagged for retrain.

## Files touched

- `ML_Headers/ModelInference.hpp` — `verify_model_stamp()` + stamp parser
- `ML_Headers/CoreModelZoo.hpp` — gate the load
- `CoreFrameworks/ControllerConfig.hpp` — 2 new cfg fields
- `engine.cfg.example` — defaults + comments
- `tools/stamp_model.cpp` — new CLI
- `Backtest/BacktestPanels.hpp` — checkbox + stamp generation
- `tests/controller_test.cpp` — verify tests
- `CMakeLists.txt` — add stamp_model target
- `CLAUDE_INVARIANTS.md` — update Held-Out Validation Discipline
  invariant to reference the gate (was advisory; now enforced)

## Versioning

- v5.2.x — Phase 1 (boot check) — minor bump (cfg fields added; model
  files now require stamps to load)
- v5.2.x+1 — Phase 2 (suite UI)
- v5.2.x+2 — Phase 3 (re-stamp existing models)

Coordinate with v5.2.0 live-reconciliation work — both are pre-live
hardening.

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Stamp generation tooling has a bug → false positives reject good models | Phase 3 forces re-stamping during stable testing; bugs surface before live deploy |
| User loses stamp_secret → can't re-verify own stamps | Document recovery: regenerate secret, restamp all models |
| Gap threshold too strict, every model fails | Cfg-tunable `gap_acceptable_threshold` per CLAUDE_INVARIANTS already exists |
| Stamp format drift across versions | Version the stamp format; upgrade tool migrates |

## Rollback story

Tag `pre-held-out-gate`. If the gate misfires in production, set
`held_out_gate_strict=0` to bypass + ship the diagnosis. Don't disable
permanently.

## Out of scope

- Continuous re-validation as new tick days come in (could be a future
  v5.3.x — "models expire after N days of unseen data")
- Online learning gate (we don't currently retrain online)
- Multi-model ensembling stamps (each model stamps separately for now)
