---
type: ledger-template
class_id: 13
title: Worker-thread struct extended without updating snap-capture-before-free block
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
surface_tags: [training, gui-thread]
severity: high
recurrence_count: 3
first_instance: v5.9.5b
closure_mechanism: snap-capture invariant (worker captures every struct field to stack local before free(args)) + click-handler population invariant (every malloc-site populates every field) + /parity-check Section L production-caller field-population audit + /bug-check skill (v5.14) mechanizing detection greps
sister_classes: [4, 18]
---

## Class 13 — Worker-thread struct extended without updating snap-capture-before-free block

**Surface:** training / GUI worker threads (`Backtest/BacktestPanels.hpp`).
Not on engine hot path; affects training output correctness.

**Symptom:** worker thread reads garbage values for newly-added
struct fields. Manifests as silent data corruption (wrong
label_kind written to stamp, wrong output dir, wrong cfg flags).
May not crash — undefined memory often returns plausible-looking
values (0, recently-freed-then-reused bytes). Tests pass when the
test harness doesn't exercise the GUI worker path. Operator only
notices in paper-test when stamps reject ("unknown label_kind") or
models save to the wrong directory.

**Root cause:** worker functions follow a discipline of copying
malloc'd `args->snap_*` fields to stack locals, then `free(args)`,
then operating on the locals (race-free + early-free for memory
hygiene). When a new field is added to the worker-args struct in
revision N+1, the field is populated by the click handler but the
worker's snap-capture block is NOT updated to copy it before
`free(args)`. Subsequent `args->new_field` reads dereference freed
memory.

A second flavor of the same class: the click handler ITSELF
doesn't populate the new field after malloc, so even if the worker
captured it correctly, it would capture uninitialized memory.

**Detection:**

```bash
# 1. Find every worker_fn that does free(args).
grep -rn "free(args)" --include="*.hpp" --include="*.cpp" Backtest/

# 2. For each worker_fn, list args->* reads BEFORE free(args)
#    and compare against args->* reads AFTER free(args). Any
#    POST-free read is a bug.
#    (Per-function awk record-based scan works.)

# 3. Cross-reference: for every struct that's malloc'd + freed by
#    a worker, grep for ALL its field names in BOTH the worker's
#    pre-free capture block AND every click-handler that populates
#    it. Missing field on either side = bug.
```

A `/bug-check` skill (queued for v5.14) reads this class definition
+ runs the detection greps automatically + reports matches.

**Known instances:**

- **2026-08-21 · `E.1.2.D` · a NEW SUB-SHAPE: *snap block complete, consumer bypasses it*.**
  `MultiHorizonWorkerArgs` (`Backtest/BacktestPanels.hpp`) has carried click-time snapshots of all
  EIGHT XGBoost hyperparameters since v5.11.41 — populated at both click handlers, and read by
  **nothing**. `mh_run_one_horizon_fv` read `state->max_depth` etc. LIVE off the worker thread
  instead, and read three of them a SECOND time at `summary.txt`-write time, minutes later. So an
  operator edit during the label pass silently changed the saved model, `summary.txt` could disagree
  with the model beside it, and in parallel mode N threads read non-atomic ints while ImGui wrote
  them. The extraction of `mh_run_one_horizon_fv` from the parent worker (v5.11.41) is what
  converted eight snapped reads into eight live ones; the now-orphan snaps are the fossil that
  proves it. **This is the inverse of both previously-documented flavors** — the snap block is not
  missing and not stale, it is complete, correct, and unwired. Fixed engine `f99e102` (the same
  snapshot now also feeds the validation trainers and the stamp, so all four agree). Detection that
  works: for each `*WorkerArgs` field, grep its name — a snap with exactly ONE hit (its own
  population) is an unwired snap.
- **2026-08-21 · `E.1.2.D` · same class, `FullValidationWorkerArgs`.** The struct carried a snapshot
  block whose own comment describes this bug class verbatim (*"Capture-at-click eliminates the
  race"*), and `label_type` / the `wf_*` quartet / `gap_threshold` / `held_out_fraction` were simply
  never added to it — all read live from the worker. The `label_type` one needed no race at all:
  changing the combo between the Collect click and the Run-Full-Validation click made the worker
  train on one objective and stamp another. Fixed engine `6b1a9dd`; `label_type` is now sourced from
  `run_control->run_config`, i.e. the field that actually produced the labels.

- **v5.13.5 use-after-free in `train_multi_horizon_worker_fn`**
  (`Backtest/BacktestPanels.hpp:~3814` fix; tag `v5.13.5.B`,
  commit `6f3296c`). v5.13.5 added
  `snap_label_kind_per_horizon[]` + `snap_training_side` to
  `MultiHorizonWorkerArgs`. Old fields (horizons/tp_pcts/sl_pcts/
  auto_stamp_secret) were memcpy'd to stack before free; new fields
  were not. Subsequent reads at 4 sites (parallel-job populate +
  serial-mode loop call ×2) dereferenced freed memory → undefined
  label_kind in stamp + wrong training_side path routing. Caught
  by `/parity-check` Section L immediately after coding (audit ran
  in parallel with ship).

- **v5.13.5 single-horizon Train Model snap omission**
  (`Backtest/BacktestPanels.hpp:~4917` fix; tag `v5.13.5.A`,
  commit `743f228`). Same ship; sister bug. The Train Model click
  handler (single-horizon) routes through MultiHorizon worker
  since v5.11.44 but its click handler only populated the OLD snap
  fields, leaving the NEW v5.13.5 fields uninitialized in the
  malloc'd args. Worker read uninitialized memory → undefined
  label_kind / training_side. Caught by self-review during audit
  cycle (operator question "is the Train Model handler also
  populating the new fields?" prompted the check).

Both caught by `/parity-check` Section L (production-caller field-
population audit) — the parity audit was designed exactly for this
class after v5.9.5b found the same pattern in a stamp body context
(StampInferenceCfgInputs with 10 cfg-binding fields silently
unpopulated by the suite caller). Worth retroactively running
`/parity-check` when ANY worker-arg struct is extended.

**Prevention:**

- **Snap-capture invariant:** when extending a struct that's
  malloc'd → passed to pthread → freed in worker, the worker MUST
  capture every new field to a stack local before `free(args)`.
  PR-time check: `grep -A30 "struct .*WorkerArgs" file` lists the
  struct fields; cross-reference EVERY field appears in both the
  worker's pre-free capture block AND every click handler that
  allocates the struct.

- **Click-handler population invariant:** every malloc-site for a
  worker-args struct must populate EVERY field. Default-init via
  `(StructT*)calloc(1, sizeof(StructT))` would catch uninitialized-
  memory reads at runtime via deterministic-zero, but would NOT
  catch the use-after-free in flavor 1. Prefer explicit per-field
  population + a `/bug-check` scan.

- **`/parity-check` Section L** explicitly walks production callers
  for newly-added struct fields. Run it after ANY ship that
  extends a worker-arg struct.

- **`/bug-check` skill (v5.14):** mechanizes the detection greps
  here. Reads `RECURRING_BUG_PATTERNS.md` + walks `Backtest/` for
  `free(args)` sites + diffs `args->field` reads pre/post-free +
  reports mismatches. Lower friction than the manual grep.
