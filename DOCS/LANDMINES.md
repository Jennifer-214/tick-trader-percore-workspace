# LANDMINES.md — Known operational pitfalls

**Workspace-private.** Pitfalls accumulated across sprints that are
non-obvious from the code but recurring enough to need documenting.
Read before debugging segfaults, races, parallelism issues, or
anything else that "should just work" but doesn't.

Each landmine documents: symptom + root cause + current mitigation
+ proper fix (deferred or shipped) + future-Claude debugging hint.

---

## Landmine 1 — XGBoost + libgomp + pthread parallelism (set 2026-05-07, v5.11.45)

**Symptom:** `foxml_suite` SIGSEGV when clicking Train Multi-Horizon
(or Train Model post-v5.11.44 since Train Model now routes through
MH worker). Backtrace shows crash inside `libgomp::GOMP_parallel`
called from XGBoost internals — `RowsWiseBuildHistKernel`,
`BuildHistLeftRight`, `PredValueByOneTree`, `PredictDMatrix`. Hits
during fold training in WF or during prediction.

**Root cause:** XGBoost is not safe under "concurrent booster
trainings in different pthreads". libgomp's parallel-region setup
races even when each pthread calls `omp_set_num_threads(1)` to cap
its OpenMP team. The team allocation in libgomp uses shared
process-global state that multiple pthreads can corrupt
simultaneously.

**Why the obvious fix didn't work:**
- v5.11.41.C: parallel multi-horizon spawned N pthreads, each pinned
  XGBoost's `xgb_train_nthread = 1`. Insufficient.
- v5.11.44 hotfix: added `omp_set_num_threads(1)` + `omp_set_dynamic(0)`
  at top of `mh_per_horizon_parallel_worker`, also pinned
  `xgb_eval_nthread = 1` (WF folds use eval not train). Still
  segfaulted.
- The libgomp parallel-region setup itself is the issue, not the
  thread count.

**Current mitigation (v5.11.45):** default
`cfg.multi_horizon_max_threads = 1` (forced serial). Operator opts
in to parallel mode by setting `>= 2`; worker fires a CRITICAL log
warning telling her about the segfault risk.

**Proper fix (deferred):** call
`setenv("OMP_NUM_THREADS", "1", /*overwrite=*/1)` at process start in
`foxml_suite.cpp:main()` BEFORE any pthreads exist. Sets libgomp's
global default once; all child threads inherit. No per-thread races.
Affects ALL XGBoost in the binary (not just multi-horizon), so it's
more invasive than the cfg toggle. Worth doing eventually but needs
testing across all training/prediction surfaces.

**Workaround for parallel-mode speedup:** train models for different
horizons in SEPARATE foxml_suite invocations (each its own process,
no pthread interaction). E.g., shell-script that loops over horizons,
each runs `./bin/foxml_suite --batch ...` (no live UI). Cumbersome
but parity-safe.

**If a future Claude session sees a segfault in XGBoost training:**
- Check if `cfg.multi_horizon_max_threads >= 2` is set (operator
  opted in to parallel mode). If yes: set it to 1, retry serial.
- If still crashing under serial: different root cause (NOT this
  landmine). Look for actual memory bug in worker code.

**Reference:**
- v5.11.41.C added the parallelism (`mh_per_horizon_parallel_worker`)
- v5.11.44 attempted libgomp fix (didn't work)
- v5.11.45 changed default to serial
- No upstream XGBoost issue tracking this specifically; it's a known
  general issue with libgomp's pthread interaction.

---

## How to add a new landmine

When you encounter a non-obvious pitfall (segfault, race, parallelism
issue, build-system surprise, library quirk, hardware-specific
behavior) that took >1h to debug, add an entry here following the
template above:

1. **Symptom** — what the operator sees + how to reproduce
2. **Root cause** — what's actually wrong (technical detail)
3. **Why the obvious fix didn't work** — saves the next person from
   trying the same dead ends
4. **Current mitigation** — what's in place today
5. **Proper fix (deferred or shipped)** — long-term resolution
6. **Workaround** — operator escape hatch if any
7. **Future-Claude debugging hint** — "if you see X, check Y first"
8. **Reference** — version tags + plan files

Auto-write contract: this doc is the canonical home for
operational landmines that recur. Don't bury them in postmortems
(those get rotated) or chat memory (compacted away). Surface them
here so they survive context decay.
