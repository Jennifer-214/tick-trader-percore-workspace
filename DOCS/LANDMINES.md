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

**Root cause:** the money repr change (`FPN_Binary<64>` binary → `<10,8>` decimal) changes `sizeof(FPN_Binary<F>)` + the raw byte layout of every money field. `ShardedSnapshotPersist.hpp` writes per-core money + `Position<F>` structs RAW via `fwrite` (magic + version gated, NOT HMAC). The epoch bumps `SHARDED_SNAPSHOT_VERSION` → the recovery path correctly REJECTS the old-version snapshot (by design — D-100 epoch boundary; the alternative, reading old bytes as decimal, would silently recover a corrupt balance, which is worse). But "correctly rejected" still means the pre-deploy state is unrecoverable.

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

## Landmine 5 — `Path(__file__).resolve()` follows symlinks → a tool in a symlinked workspace finds the WRONG repo root (set 2026-06-02, code-only-public spring cleaning)

**Symptom:** after relocating `tools/` to the private workspace and symlinking it back into the engine (`engine/tools` → `../tick-trader-percore-workspace/tools`), `build.sh` ABORTS: `[per-core-cfg-CI] ERROR: file not found: <WORKSPACE>/CoreFrameworks/CfgFieldRegistry.hpp` — the tool hunts for ENGINE source under the WORKSPACE. The same tool ran fine before the move.

**Root cause:** the tool computes `REPO_ROOT = Path(__file__).resolve().parent.parent`. `.resolve()` FOLLOWS symlinks → `__file__` resolves to the tool's REAL location (`workspace/tools/X.py`) → `REPO_ROOT` becomes the workspace, not the engine. Every tool that reads engine source AND derives its root from `__file__` breaks this way once it lives in a symlinked-in workspace (11 of them here).

**Why the obvious fixes are traps:** gitignore-in-place (don't move it) is build-safe but loses the syncable-workspace goal; hardcoding the engine path works (private tools MAY hardcode) but isn't portable across machines.

**Proper fix:** swap `.resolve()` → `.absolute()` — `.absolute()` makes the path absolute WITHOUT following symlinks, so `__file__` keeps the engine (symlink) path → `REPO_ROOT` = engine. For `.sh`: env-override `REPO_ROOT="${FOXML_ENGINE:-$(cd "$(dirname "$0")/.." && pwd)}"`. Matches the machine-portable-resolver pattern the already-portable tools use. Build-file references to the now-private dirs also need skip-if-absent guards (`[ -f tools/X ]` in build.sh; `if(EXISTS .../tests)` in CMakeLists) so a public clone still compiles.

**Future-Claude debugging hint:** a tool "file not found"s ENGINE source under a WORKSPACE path → it used `__file__.resolve()` and now lives in the symlinked workspace. Grep `tools/*.py` for `__file__).resolve()` near `CoreFrameworks|ML_Headers|Strategies`; swap to `.absolute()`. Verify by running through the engine symlink path.

**Reference:** code-only-public spring cleaning (2026-06-02) · `DESIGN_SPECS/meta-disciplines/public-private-boundary-and-ecosystem-discipline.md` · `feedback_machine_portable_resolver_for_committed_tool_paths`.

**Recurrence (2026-06-29, ③ item-6):** the NEW `check_cfg_gate_caller_coverage.py` hit the SAME trap — `Path(__file__).resolve()` landed in the workspace → the tool found ZERO `ControllerConfig_Load` callers (a Class-51 vacuous PASS, averted only because it WARN-exits on a zero-caller count). Fixed via a walk-up `_engine_root()` that asserts `CoreFrameworks/` + `main.cpp` and FAILS LOUD if not found (a stricter variant of the `.absolute()` fix — silent-wrong-dir becomes a loud abort). **The trap recurs for EVERY new engine-root-deriving tool** → the structural close is a CI grep flagging `__file__).resolve()` near engine-source dir names in `tools/*.py` (candidate guard, not yet built).

---

## Landmine 6 — zsh does NOT word-split unquoted vars in `for` loops (set 2026-06-02)

**Symptom:** a Bash-tool loop `for f in $LIST; do mv "$f" …; done` (with `LIST="a b c"`) silently does nothing useful — it runs ONCE with `$f` = the whole `"a b c"` string. Counters increment past the failed ops, so it can falsely print `MOVED=3` while moving nothing. Bit the tools-privacy move TWICE.

**Root cause:** the Bash tool runs **zsh**, and zsh (unlike bash) does NOT word-split unquoted parameter expansions in `for … in $VAR` — the whole string is one word.

**Proper fix:** iterate in **Python** (`subprocess` for git/fs) for any list-of-items fan-out — deterministic, no shell-splitting surprises. In shell: `for f in ${=LIST}` (zsh split flag), a real array `arr=(a b c); for f in "${arr[@]}"`, or a literal in-loop list. (Separate sister glitch: coreutils briefly unresolvable — `command not found: mv` — so guard fan-out scripts with `command -v mv ln git >/dev/null || exit 1` to abort cleanly instead of half-applying.)

**Future-Claude debugging hint:** a shell `for … in $VAR` "did nothing" but reported success → echo `$f` inside; if it's the whole list, that's zsh non-splitting. Prefer Python for file/git fan-out in this environment.

**Reference:** code-only-public spring cleaning (2026-06-02) — two silent `MOVED=0` moves before diagnosis.

---

## Landmine 7 — symlinked tests/+tools/: a `../X` engine include resolves OFF the engine (C++ sibling of Landmine 5) (set 2026-06-08, #11 Ship-A pickup)

**Symptom:** a fresh `cmake -B build` build of `controller_test` (also `depth_recorder_test` / `parity_harness`) fails `fatal error: ../DataStream/MockGenerator.hpp: No such file or directory`, AND the pre-commit determinism gate fails to build `tools/replay_locale_gate.cpp` (`../CoreFrameworks/ParseFast.hpp` not found) — even though both engine headers exist. Built fine before the `tests/`+`tools/` symlink move; a build dir configured pre-symlink (an old `build_gui/`) still works off cached real paths, so it looks intermittent.

**Root cause:** `tests/` + `tools/` are symlinks into the private workspace. A `#include "../X"` in a symlinked-in source resolves `..` against the symlink's CANONICAL dir (the workspace), not the engine → `../DataStream` becomes `workspace/DataStream` (nonexistent). GCC canonicalizes the symlinked source dir for quoted-relative include resolution. The **C++ sibling of Landmine 5** (which is the Python `Path(__file__).resolve()` form of the same symlink trap).

**Why the obvious fixes are traps:** gitignore-in-place (un-symlink) is build-safe but FORKS the syncable-workspace copy — the same trade-off Landmine 5 names (the workspace stops being the single source); rewriting every `../` include is a wide cascade.

**Proper fix:** anchor the quote/`-I` include search on a REAL (non-symlink) engine subdir so `../X` resolves as `<realsubdir>/../X` == `<engine>/X`:
- **CMake** (covers controller_test / depth_recorder_test / parity_harness / compare_scalers): `include_directories(${CMAKE_SOURCE_DIR}/CoreFrameworks)` before the dev/test targets in `CMakeLists.txt`.
- **Gate scripts** that compile a tool with `-I$ROOT` (engine root): normalize the source to engine-root-relative — drop the `../` (`#include "CoreFrameworks/ParseFast.hpp"`), matching the sibling convention (`fp_determinism_golden.cpp` already uses `FixedPoint/...`). The lone offender was `replay_locale_gate.cpp`.

**Future-Claude debugging hint:** a test/tool build "file not found"s an ENGINE header that DOES exist, via a `../` include, after the tests/+tools/ symlink move → this. Fix = the CoreFrameworks anchor (CMake) or a root-relative include (script-compiled tool). Verify with a FRESH `cmake -B build && cmake --build build --target controller_test` (never a stale pre-symlink build dir).

**Reference:** #11 Ship-A storage-flip pickup (2026-06-08) — a fresh `controller_test` configure + the pre-commit determinism gate both broke on this; sibling of Landmine 5; fix = `CMakeLists.txt` CoreFrameworks anchor + `tools/replay_locale_gate.cpp` root-relative include. The flip session's `build_probe/` keystone logs show it was already biting then.

---

## Landmine 8 — the decimal epoch silently ACTIVATES latent parallel-derivation divergences (set 2026-06-10, v5.15.5.F.4d.1.E.0.10)

**Symptom:** a money value computed two ways — e.g. P&L gross as `round((exit−entry)×qty)` (1-mul) in one accounting path and `round(exit×qty)−round(entry×qty)` (2-mul) in another — reconciled fine under the OLD binary/FPN money but diverges by 1 ULP under the NEW decimal money, silently, on ~25% of realistic inputs, ACCUMULATING. Here: per-core `core_realized` stopped reconciling `oms.realized_pnl`.

**Root cause:** under FPN binary (2⁻⁶⁴ granularity) the two formulas differed by ~1e-19 — invisible at any sane tolerance, so the inconsistency was graded "not a present bug." Decimal half-even at 1e-8 amplifies the SAME formula gap to a real 1 ULP. The P2b decimal flip (Ship B, `838bf09`) mechanically carried the FPN formulas into decimal and ACTIVATED the latent divergence.

**Why the obvious fix didn't catch it:** "apply ONE canonical rounding mode everywhere" (D-105) is necessary but NOT sufficient — it governs HOW each multiply rounds, not WHETHER two paths compute the same expression. A uniform mode does not make two different formulas (1-mul vs 2-mul) agree. The formula split survived the mode fix.

**Proper fix (shipped `.E.0.10`, D-190):** single-source the COMPUTATION — one `Money_FillGross` helper (`Portfolio.hpp:397`) that every gross site calls, so the values reconcile by construction, not by discipline.

**Future-Claude debugging hint:** after ANY representation/epoch change (binary→decimal, truncate→half-even, scale change), RE-OPEN every "benign inconsistency" judgment AND sweep the money path for parallel/dual derivations of the same value. If you see two open-coded forms of one quantity (`Money_Sub(Mul,Mul)` vs `Mul(Sub,qty)`), that's the smell.

**Reference:** D-190 (amends D-105); PARITY-038; memory `feedback_single_source_the_computation_not_just_the_mode`; v5.15.5.F.4d.1.E.0.10.

---

## Landmine 9 — the engine does NOT symlink `DOCS/tech-debt/` (only individual `DOCS/*.md`): the real ledger is invisible from the engine path (set 2026-06-11, v5.15.5.F.4d.1.E.0.10)

**Symptom:** ledgering or reading a TECH_DEBT entry from the ENGINE path silently fails — `ls FoxML_Trader_v2/DOCS/tech-debt/` → "No such file or directory"; a `Read` of `DOCS/tech-debt/open.md` → "File does not exist"; a `DOCS/tech-debt/*.md` glob → "no matches found". Looks like the sub-file ledger was never created / the ledger is broken. It is NOT — it's fully populated in the WORKSPACE. Caused a real error this session: concluded "the ledger doesn't exist," appended a NEW TECH_DEBT-164 to `DOCS/TECH_DEBT.md`'s "Future debt findings" section — a DUPLICATE of the TECH_DEBT-164 already in `open.md` (an H21 identifier collision caught only by the `/close-session` Stage 5.5 independent review).

**Root cause:** `DOCS/` is symlinked into the engine PER-FILE (individual `DOCS/<name>.md` → workspace), NOT as a directory. The `DOCS/tech-debt/` SUBDIRECTORY was never symlinked. So `DOCS/TECH_DEBT.md` (the index/format doc) resolves from the engine, but the real numbered entries — `DOCS/tech-debt/{open,closed}.md` — exist ONLY at `tick-trader-percore-workspace/DOCS/tech-debt/`. The C++/Python sibling of Landmines 5 + 7 — the same symlink-topology trap, here as a MISSING subdir symlink.

**Why the obvious read fails:** the engine `DOCS/` listing shows the per-file-symlinked `.md` files but no `tech-debt/` subdir, so "the ledger" looks like just `TECH_DEBT.md` — which is the index, NOT the entries. A next-id grep against the engine path finds nothing → you mis-assign an already-used id (H21 violation).

**Current mitigation:** ALWAYS read/edit the tech-debt ledger via the WORKSPACE path — `tick-trader-percore-workspace/DOCS/tech-debt/{open,closed}.md`. Find the true next-free id with `rg -n '^### TECH_DEBT-[0-9]+' <workspace>/DOCS/tech-debt/open.md | tail`.

**Proper fix (deferred):** symlink the `DOCS/tech-debt/` subdir into the engine (like `plans/` is a dir symlink) so the engine + its tools see the real ledger. Until then, workspace-path discipline.

**Future-Claude debugging hint:** about to ledger a TECH_DEBT entry and the engine `DOCS/tech-debt/` "doesn't exist" → it's THIS, not a broken ledger. Go to the workspace path; check for an EXISTING entry at your intended id BEFORE writing (H21 — identifiers are append-only + immutable, never reuse a number).

**Reference:** v5.15.5.F.4d.1.E.0.10 close (2026-06-11) — duplicate TECH_DEBT-164 caught by `/close-session` Stage 5.5; siblings Landmine 5 (Python `__file__.resolve()`) + Landmine 7 (C++ `../` include); H21 (identifier retirement discipline).

---

## Landmine 10 — code+test change splits across TWO repos: code → engine, `tests/` → workspace (`git add tests/` in the engine = "beyond a symbolic link" → silent no-op commit) (set 2026-06-13, v5.15.5.F.4d.1.E.0.10 A24)

**Symptom:** after a code+test change — an engine fix in `CoreFrameworks/X.hpp` + a char-test in `tests/controller_test.cpp` — `cd engine && git add tests/controller_test.cpp` → `fatal: pathspec 'tests/controller_test.cpp' is beyond a symbolic link`; the following `git commit` then reports **"nothing to commit, working tree clean"** and the test is silently NOT committed (it never reached the engine repo). Looks like the commit worked; it didn't include the test.

**Root cause:** `tests/` (+ `plans/`, `DESIGN_SPECS/`, `tools/`) are symlinks into the private workspace. The PUBLIC engine repo tracks ONLY compile-the-code (`CoreFrameworks/`, `Strategies/`, … + build infra). A `tests/` path is beyond a symlink + not engine-tracked → `git add` refuses and `git commit` sees nothing. So ONE logical code+test change SPLITS across two repos: public code → engine repo, private test → workspace repo. (The COMMIT face of the symlink-topology family — siblings Landmines 5/7/9.)

**Current mitigation:** commit a code+test change as TWO commits, one per repo — `cd engine && git add CoreFrameworks/X.hpp && git commit` (public code) + `cd workspace && git add tests/X <+ docs/trackers> && git commit` (private test + captures). Cross-reference in the messages ("Pairs with engine `<sha>`"). Verify each repo's `git status` after — a "nothing to commit" right after editing a test is the tell. (Same split for the Edit tool: Read+Edit a `tests/`/`tools/` file via ONE consistent path — engine OR workspace — since the tool tracks the literal path string, not the canonical inode.)

**Future-Claude debugging hint:** `git add` of a `tests/`/`tools/`/`plans/`/`DESIGN_SPECS/` path in the ENGINE repo errors "beyond a symbolic link", OR an engine commit says "nothing to commit" right after you edited a test → the file is a workspace file; commit it in the workspace repo. EVERY A-series fix (engine code + char-test) hits this — plan two commits + a rollback tag on each repo.

**Reference:** v5.15.5.F.4d.1.E.0.10 A24 close (2026-06-13) — the char-test commit no-op'd in the engine, caught by the `git add` error; the symlink-topology family Landmines 5 (Python `__file__.resolve`) / 7 (C++ `../` include) / 9 (`DOCS/tech-debt/` subdir); privacy boundary `project_public_repo_is_code_only` + `public-private-boundary-and-ecosystem-discipline.md`.

---

## Landmine 11 — dispatched subagents are hard-denied on compiler (`g++`) invocation; the MAIN agent can compile (set 2026-06-20, v5.15.5.F.4d.1.E.1.1 Phase 2)

**Symptom:** a dispatched general-purpose subagent tasked with build/verification ("run `./build.sh test` + fresh asan/ubsan + conformance") reports it CANNOT run any C++-compiler-invoking command — every `g++` / `./build.sh asan` / `./build.sh test --clean` / forced recompile comes back "Permission to use Bash denied." Its MISSION (verify the build) fails not because the tree is broken but because it can't invoke the compiler. The SAME commands run fine from the MAIN agent.

**Root cause:** a session-level PERMISSION policy denies compiler invocation to dispatched subagents (observed for general-purpose via the Agent tool). It's a permission rule, NOT a sandbox issue — `dangerouslyDisableSandbox: true` does NOT lift it. The main agent gets an interactive/pre-approved permission path; a subagent gets a hard auto-deny (it can't prompt the operator). Only an incremental no-op `./build.sh test` (relink+run, no recompilation) slipped through this session — which is why the verify-agent had a `controller_test` number at all but couldn't run a fresh build or the sanitizers.

**Why it's non-obvious:** the agent still RETURNS a verdict, so it looks like it "ran" verification — but the compiler-gated parts were silently BLOCKED, not executed. A "build verified" from such an agent is HOLLOW; the denial is only visible if you read the agent's surprises/caveats.

**Current mitigation:** RUN all compile/build/sanitizer/conformance/determinism gates from the MAIN agent, never a dispatched subagent. Dispatch subagents for READ-ONLY analysis (grep/read/git) only. If a subagent must REPORT build state, have the MAIN agent run `./build.sh` in the background → the subagent reads the output file's tail (it does NOT invoke the compiler itself).

**Future-Claude debugging hint:** a dispatched subagent reports "can't run the build" / "permission denied on g++" → this, not a broken tree. Don't conclude the code is unbuildable; re-run the gate yourself. When designing a multi-agent verification fan-out, keep COMPILE/RUN in the main agent + give subagents the read-only half.

**Reference:** v5.15.5.F.4d.1.E.1.1 Phase 2 state-audit (2026-06-20) — the dispatched DoD-verification agent was hard-denied on every compiler command while the main agent ran `build.sh test` + fresh asan/ubsan + conformance fine. Sub->1h to diagnose but recurring (every multi-agent session that dispatches build/verify work) + environment-specific, so it earns a durable entry (cf. Landmine 4's same carve-out). Sister: memory `feedback_adversarial_framing_default_for_checks` (re-ground a subagent's EVIDENCE — a "build verified" from a compiler-denied agent is hollow). CAVEAT: may be sandbox/permission-config-specific; re-confirm it still holds before relying on it.

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
