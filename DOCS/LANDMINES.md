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

## Landmine 2 — detached-stdin hang: path-less `rg`/`grep` blocks forever (set 2026-05-31, v5.15.5.F.4d.1.E.0.1)

**Symptom:** a shell command — often a git **pre-commit hook**, or a `run_in_background` / CI / cron /
ssh-without-tty run — appears to "run" but never returns; sits at **0% CPU indefinitely** (observed: a
backgrounded determinism gate slept ~15 min before anyone noticed). The SAME command run
foreground/interactive is fine. It only hangs when **detached**.

**Root cause:** a **path-less `rg PATTERN`** (or a standalone `grep PATTERN` not consuming a pipe) reads
**stdin** when given no file/dir path. With a tty that's interactive; **detached**, stdin is an open fd
that never sends EOF, so the command blocks on `read()` forever. A git hook hanging this way **freezes
every commit**, silently.

**Why the obvious fix is fragile:** patching the one offending `rg` to take an explicit path (`.` / a
file) fixes *that* instance — but the rule "always pass a path" lived only in a **comment**
(`check_locale_determinism.sh:21`), which is the Class-38 phantom-invariant (a comment is not a guard).
One future path-less `rg` reopens it.

**Proper fix (SHIPPED `.E.0.1`):** **`exec </dev/null`** at the top of `.githooks/pre-commit` + every
detached-run determinism script (`check_determinism.sh`, `check_fp_determinism.sh`,
`check_locale_determinism.sh`, `check_determinism_selftest.sh`). One line redirects the whole script's
(and all its children's) stdin to `/dev/null` → any stdin-reader gets instant EOF instead of blocking.
**Structural**, not per-`rg`: closes the class regardless of any script's path discipline. **Guard:**
`check_determinism_selftest.sh` check (5) asserts each of those files retains its `</dev/null` redirect →
flags removal (close the class with a guard, not a comment). Adversarially verified both ways: path-less
`rg` under `exec </dev/null` returns instantly; the same `rg` fed a never-closing stdin hangs.

**Future-Claude debugging hint:** a shell command (esp. in a hook / `run_in_background`) hangs at 0% CPU
→ suspect a stdin-reader with no input; check for path-less `rg`/`grep`. Fix = `exec </dev/null` at the
top of the script, or `< /dev/null` on the specific command. When YOU run a command detached, add
`< /dev/null` so it can't hang on stdin.

**Reference:** `74bd77b` (first instance: `check_locale_determinism.sh` rg paths + the comment) ·
`.E.0.1` ship (the `exec </dev/null` structural close + guard) · RECURRING_BUG_PATTERNS Class 38
(phantom-invariant — the comment-not-a-guard shape) · meta-anti-pattern AR-4 (a check trusted without
watching it actually work).

---

## Landmine 3 — no warm-restart across the #11 numeric-core epoch (flatten before deploy) (set 2026-05-31, pre-#11 numeric-foundation)

**Symptom:** after deploying the #11 decimal-money numeric-core ship (the binary→decimal `FixedPoint<RADIX,FRAC>` epoch), an engine restart that expects to RECOVER open positions from a snapshot silently recovers nothing (or refuses to start) — any positions/balance held at deploy time are lost.

**Root cause:** the money repr change (`FPN<64>` binary → `<10,8>` decimal) changes `sizeof(FPN<F>)` + the raw byte layout of every money field. `ShardedSnapshotPersist.hpp` writes per-core money + `Position<F>` structs RAW via `fwrite` (magic + version gated, NOT HMAC). The epoch bumps `SHARDED_SNAPSHOT_VERSION` → the recovery path correctly REJECTS the old-version snapshot (by design — D-100 epoch boundary; the alternative, reading old bytes as decimal, would silently recover a corrupt balance, which is worse). But "correctly rejected" still means the pre-deploy state is unrecoverable.

**Why there's no clean fix:** you cannot migrate the old snapshot forward — the point of the epoch is that the old binary money values are not bit-translatable to exact decimal (re-deriving them would reintroduce the imprecision). Version-reject is the correct, safe behavior; the mitigation is operational, not code.

**Current mitigation (operational — MANDATORY at #11 deploy):** FLATTEN all open positions + drain to a clean flat state BEFORE deploying #11. Deploy onto a flat book. There is no warm-restart across this one epoch boundary. Normal warm-restart resumes working after the first post-#11 snapshot is written in the new format.

**Future-Claude debugging hint:** a post-#11 restart recovers no positions / rejects the snapshot at boot → check whether the snapshot predates the #11 epoch (version < the #11 bump). If so this is EXPECTED (not a bug); the pre-#11 state is gone by design. Investigate as a bug only if the snapshot is already post-#11-format.

**Reference:** decision-log D-100 (golden-epoch) + D-110 (the `ShardedSnapshotPersist` money surface) + D-117 (#11 phasing; P5 = persistence/recovery round-trip) · the #11 foundation plan acceptance (recovery round-trip + warm-restart test) · synthesis bite B-ζ.

---

## Landmine 4 — `/tmp` is `noexec` on this box: freshly-compiled test binaries won't run from there (set 2026-06-01, #11 Ship-A proof scaffold)

**Symptom:** compile a throwaway test/probe binary to `/tmp` (`g++ … -o /tmp/foo && /tmp/foo`) and the **run** fails with `permission denied: /tmp/foo` — even though the **compile succeeded**, the file is there, and it's `+x`. The SAME binary runs fine from the repo dir or `$HOME`. Looks like a permission bug; isn't.

**Root cause:** this hardened Arch workstation mounts `/tmp` with **`noexec`** (security baseline). The kernel refuses `execve()` on any file under a `noexec` mount regardless of the file's own `+x` bit. It's an environment property, not a build/permission/chmod problem.

**Current mitigation:** output ad-hoc test/probe binaries to an EXECUTABLE location — the repo root (`-o ./_tmpbin && ./_tmpbin; rm -f ./_tmpbin`) or `$HOME`, never `/tmp`. (The committed `.sh` gates already do this; this only bites interactive `g++ -o /tmp/…` one-liners.)

**Future-Claude debugging hint:** `permission denied` when **executing** a freshly-compiled binary (NOT a compile error, NOT a missing-file error) → you almost certainly wrote it to `/tmp`. Recompile with `-o ./something` in the repo dir (or `$HOME`) and run from there. Confirm the mount with `findmnt /tmp` or `mount | grep ' /tmp '` (shows `noexec`).

**Reference:** #11 Ship-A proof scaffold (`tools/ship_a_fp2_64_slice.cpp` + `tools/fp_value_equivalence_golden.cpp` compile+run, 2026-06-01) — first hit when the slice binary wouldn't run from `/tmp`; the Session-8 handoff carries the same warning inline for the slice recompile. Sub-`>1h` to diagnose, but environment-specific + recurring (every ad-hoc compile-test session), so it earns a durable entry over the per-session handoff.

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
