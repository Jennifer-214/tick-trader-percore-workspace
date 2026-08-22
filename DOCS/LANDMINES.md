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

## Landmine 12 — editing a memory file with malformed YAML frontmatter → the harness CLOBBERS the frontmatter to a stub (set 2026-07-18, E.1.2.A)

**Symptom:** after an Edit/Write to a memory file (`~/.claude/projects/<proj>/memory/*.md`), its FRONTMATTER is silently replaced with a minimal stub — `name: ""`, every field (description / type / tags / sister_specs) GONE, and `originSessionId` overwritten with the CURRENT session's id. The BODY survives intact; only the frontmatter is lost. Surfaces as a `check_session_docs.sh` red — "MISSING type field" / the memory bidirectional+index HARD check — but ONLY because that check is scoped to session-TOUCHED files, so it fires the moment you edit the (already latently-defective) file.

**Root cause:** the harness's memory subsystem RE-SAVES a memory file after you modify it. If the frontmatter YAML is MALFORMED — e.g. a stray `    []` line dangling under a flow-style `sister_specs: [a, b, c]` (a `.E.0.4` memory-migration artifact) — the harness's YAML parser chokes and writes a FALLBACK stub, dropping every field. The trigger is the pre-existing bad YAML, not your edit's content; your edit merely pulls the file into the harness's re-save path. (A harness-interaction cousin of the symlink-topology family — Landmines 5/7/9/10 — but the harness memory-store, not a workspace symlink, is the actor.)

**Why it's non-obvious:** the Edit/Write returns "success" and the BODY is correct, so nothing looks wrong until the next doc-CI sweep — and even then "MISSING type field" reads like a you-authored-it-wrong error, not a silent clobber of fields that were fine 10 seconds earlier.

**Current mitigation (2026-07-18):** the specific `[]` defect was swept corpus-wide — 0 malformed `[]` lines + 0 `name: ""` stubs remain (fixed `feedback_process_weight_by_surface_blast_radius` [restored from an in-session pre-edit Read] + `feedback_auto_route_input_to_matching_skill`). Removing the `[]` in the SAME edit is safe: the harness re-parses the post-edit CLEAN YAML and keeps it.

**Proper practice (future-Claude):** after ANY Edit/Write to a memory file, RE-READ its frontmatter to confirm it held (name + type + tags present; not a `name: ""` stub). If clobbered, restore from the pre-edit content — an in-session earlier Read is the most reliable source (git may not track the memory dir) — with CLEAN, well-formed YAML. NEVER leave malformed YAML in a memory frontmatter: it is a latent clobber-trigger that fires on the next edit. `check_session_docs.sh` (memory bidirectional+index) is the backstop, but it only fires on touched files, so a latent defect sits silent until someone edits that file.

**Future-Claude debugging hint:** a memory shows `name: ""` + the current session's `originSessionId`, or the doc-CI reds "MISSING type field" on a memory you just edited → it was clobbered on save; restore the real frontmatter (in-session Read / workspace backup) with valid YAML, and grep the corpus for other `^\s*\[\]\s*$` triggers before they bite.

**Reference:** E.1.2.A (2026-07-18) — hit when the D-365 process-weight carve-out edit clobbered `feedback_process_weight_by_surface_blast_radius`; caught by `check_session_docs.sh`, restored + the `[]` class swept (2/2). Sub->1h to diagnose but harness-specific + recurring (every future memory edit over a latent defect), so it earns a durable entry (cf. Landmines 4/11 same carve-out). Sister: the symlink-topology landmines 5/7/9/10.

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

## Landmine 13 — ripgrep SKIPS a gitignored DIRECTORY but RETURNS a file-level-ignored FILE (set 2026-07-20, E.1.2.B `0.2`)

**The trap.** A `.gitignore` containing `private/` hides `private/x.hpp` from `rg`. A `.gitignore`
containing `hidden.hpp` does **not** hide `hidden.hpp` from `rg`. Both are "gitignored" as far as
`git check-ignore` is concerned — `git check-ignore -v hidden.hpp` confirms the rule matches — but
ripgrep's behaviour differs by rule KIND.

**What it cost.** The non-vacuity tooth written to prove TECH_DEBT-245's fix used a FILE-level
ignore fixture. It passed. It would also have passed against the **unfixed** rg-based enumerator,
because rg returns file-level-ignored files anyway — so the tooth proved nothing about the thing it
was written to prove. A negative test that cannot fail on its target is the exact Class-51 shape,
planted inside the guard built to close Class-51.

**How to avoid it.** Any fixture asserting gitignore behaviour MUST use a **directory** rule. That
is also the real-world shape here — the live instance was `.gitignore:167 Strategies/private/`.
Verify discrimination explicitly: `rg` must see 0 and the replacement enumerator must see 1.

**Related:** TECH_DEBT-245 (closed) · `calibration-corpus-non-vacuity-discipline.md` (the tooth
needs a tooth) · Class-51.

## Landmine 14 — the tech-debt ledgers spell one anchor THREE ways, and PARITY is not symmetric with TECH_DEBT (set 2026-07-20, E.1.2.B `0.2`)

**The trap.** An entry's defining anchor is written three ways — `### TECH_DEBT-N` (heading),
`id: TECH_DEBT-N` (bare), `- **id:** TECH_DEBT-N` (bold) — and roughly **37% of defining headings
are ZERO-PADDED** (`TECH_DEBT-016`). Any single-spelling grep is half-blind, and the two namespaces
do **not** share a safe shortcut: every TECH_DEBT entry has a `###` heading, but **10 of 41 PARITY
entries live in ```yaml fences with no heading at all**. So "just anchor on the heading" is correct
for TECH_DEBT and silently wrong for PARITY.

**What it cost.** Three separate live defects, all shipped and all green: a pre-commit gate
(`check_forward_promise_audit.py`) blind to 102 of 201 open entries, emitting a HIGH telling you to
write an entry that already existed — and passing **vacuously** in the other leg, which certifies a
still-open item as moved; two SKILL.md prose recipes with the same pattern, run literally by a human
or agent, producing a false BLOCK; and `check_tech_debt.py --close`, where the SAFE spelling
(`--close 16`) errored while the DANGEROUS one (`--close 016`) silently rewrote both ledgers. The
orchestrator's own greps returned 0 for every id until the format was actually inspected — a
uniform-zero result is the tell.

**How to avoid it.** Match the UNION with padding tolerance:
```
NS=TECH_DEBT; N=245     # or NS=PARITY
rg -n -e "^### $NS-0*$N\b" -e "^id: $NS-0*$N\b" -e "^- \*\*id:\*\* $NS-0*$N\b" <ledger>
```
(the namespace is a VARIABLE deliberately — writing the literal `<NS>-0` inline creates a string the
citable-ID scanner reads as a citation to id `0`, which is how this very entry first went RED)
(`-e` repeated rather than alternation, so it survives a markdown table cell). Better: import the
resolver — `_anchor`/`_has_entry`/`_entry_block` in `check_forward_promise_audit.py`, whose
`--selftest` pins these exact cases. **And never trust a zero/empty result from an anchor grep until
you have looked at what the anchor actually looks like in the file.**

**Related:** Class-51 mode F (half-blind anchor) · D-405 (locate-vs-derive) · D-407 · TECH_DEBT-263
(the resolver has 1 of ~7 consumers) · TECH_DEBT-262 (the parent generator).

## Landmine 15 — `check_tech_debt.py --close` MUTATES two ledgers; it was write-by-default (set 2026-07-20, E.1.2.B `0.2`)

**The trap.** `--close N` moves an entry `open.md` → `closed.md` with no undo but git. Until
2026-07-20 it wrote **by default** — `--dry-run` was opt-in, no diff was shown, and there was no
confirmation. Nothing in its `--help` suggested a read-only probe was unsafe.

**What it cost.** It was fired during a **read-only verification** — to check a claim that the tool
was zero-pad-blind — and silently moved TECH_DEBT-016, an entry transcribed into `open.md` earlier
that same session. Caught only because the output wording differed from the agent report being
verified; reverted with `git checkout`. The agent's report had shown a `--dry-run` invocation and
the flag was dropped when the command was retyped.

**How to avoid it.** It now routes through `bless.confirm_mutation()` and HARD-REFUSES `rc=2`
non-interactively, so this specific trap is closed. The general lesson stands: **before running any
tool flag during verification, check whether it writes** — `--close`, `--fix`, `--apply`,
`--update`, `--bless` all mutate somewhere in this toolchain. Prefer `--dry-run` and confirm the
output says DRY-RUN. **If you are an agent and hit the rc=2 refusal: that is the control working,
not a permission problem to route around.**

**Related:** D-407 · TECH_DEBT-255 (closed over an un-enumerated set — this was the missed writer) ·
D-394 (the TTY contract) · Class-51.

---

## Landmine 16: A background wrapper's exit code is not your build's (2026-08-15)

**What happened.** A backgrounded `cmake --build … > log 2>&1; RC=$?; echo "build RC=$RC"; grep …`
reported **exit code 0** in its completion notification — while the compile had *failed*. The
wrapper's exit status is the **last command's** (the `echo`/`grep`), not the build's. I then ran the
**stale** test binary and read its `3732 passed, 0 failed` as green. The only thing that caught it
was that the count hadn't moved after adding 7 checks.

**Why it is nasty.** Every individual signal looked healthy: the notification said 0, the suite said
0 failed, the binary ran. It is Class-57 emit-boundary flattening produced by *my own wrapper*, and
it manufactures a false green on the exact artifact you are about to trust.

**How to avoid it.** Structure any backgrounded verification so the wrapper's exit *is* the result:

    cmd > log 2>&1; RC=$?
    if [ $RC -ne 0 ]; then echo "FAILED RC=$RC"; grep -E "error:" log | head; exit $RC; fi
    ./binary > tlog 2>&1; TRC=$?
    echo "suite RC=$TRC"; exit $TRC

And treat a **test count that did not change** as a red flag in its own right — a passing suite that
did not grow after you added assertions is a stale binary until proven otherwise.

**Related:** Class 57 · `block_pipe_rc_read.sh` (the sister trap, `$?` after a pipeline) ·
`feedback_passing_test_is_not_verification`.

---

## Landmine 17: You cannot demonstrate UB in a test — assert the property instead (2026-08-15)

**What happened.** Closing the `gate_state` indeterminate-read (a struct member with no initializer,
read cross-thread), the obvious non-vacuity control was: construct the *pre-fix* shape over
`0xAA`-poisoned storage and assert the poison survives. **It failed at -O2** — while the bug it
models is entirely real and was independently probe-confirmed.

**Why.** Reading an uninitialized object is undefined behaviour, so the compiler is entitled to
fold, elide or invent the result. A control whose expected outcome depends on UB behaving
consistently is not a control — it will flap by optimization level, compiler version, and
surrounding code.

**How to avoid it.** Assert the deterministic property that *distinguishes* the two cases. Here:
`std::is_trivially_default_constructible` is `false` for a struct that initializes itself and `true`
for one that doesn't — a compile-time fact, no UB in the observation path. (Also worth pinning what
the fix does *not* cost: an NSDMI changes trivially-DEFAULT-CONSTRUCTIBLE, never
trivially-COPYABLE, so wire/memcpy surfaces are untouched.)

**Corollary:** to *observe* the real-world behaviour of an uninitialized read, you need a separate
probe binary with a realistic frame shape — and even then the answer is "fresh stack reads 0, dirty
stack keeps the poison", i.e. the defect is the **absence of a guarantee**, not an observable value.
Say that, rather than over-claiming a garbage read that a reviewer can trivially fail to reproduce.

**Related:** Class 51 (non-vacuity) · `feedback_passing_test_is_not_verification`.


## Landmine 18: two concurrent `./build.sh test` runs truncate the test binary — and it reports as "Permission denied" (2026-08-15)

**Symptom.** `./build/controller_test` fails with `Permission denied` (rc **126**). That code and
message read as a sandbox/permissions problem, and the obvious next move — re-run with the sandbox
disabled — fails *identically*, which appears to confirm the wrong diagnosis.

**Actual cause.** A second `./build.sh test` was still running. Mid-link the binary exists at **0
bytes with mode `-rw-r--r--`** (no exec bit yet — the linker has created but not finished it). Exec
on a non-executable file is exactly `EACCES` → 126. Nothing about permissions is wrong; the file is
simply not a program yet.

**How it happened here.** A foreground build hit the 120 s tool timeout and was moved to background;
not realising it was still alive, a second build was started. The FIRST build then completed far
enough to run the suite and reported `./build.sh: line 270: ./build/controller_test: Permission
denied` — because the SECOND build had truncated the binary out from under it.

**Diagnostic that settles it in one line** (distinguishes truncation from a real mount/mode issue):
```bash
ls -la build/controller_test          # 0 bytes + no `x` in the mode  => a build is mid-link
findmnt -no OPTIONS -T build/         # look for `noexec` => a genuinely different problem
```

**Rule.** Never start a second build while one is in flight — including one the harness backgrounded
after a timeout. Wait on the running task (`TaskOutput` with `block: true`) rather than re-issuing.
The engine's `build/` is a single shared output dir with no per-invocation locking, so concurrent
builds race on the same artifacts.

**Why it belongs here rather than in a tool doc:** the misleading part is not any tool's behaviour —
it is that a *build race* surfaces as a *permissions error*, so the whole investigation points away
from the cause. Sister to Landmine 16 (a background wrapper's exit code is not your build's): both
are "the signal you get is not about the thing that broke".

## Landmine 19: `rg <pat> .` from the engine root is BLIND to `tests/`, `tools/`, `plans/` — and no flag rescues it (2026-08-16)

**The trap.** Every enumeration that recurses from the engine root silently excludes three of the
most-searched directories. `tests/`, `tools/`, `plans/` are simultaneously listed in the engine
`.gitignore` (`:140`, `:141`, `:22`) **and** directory symlinks into the workspace. Measured at
HEAD, `STAMP_SET` in `tests/controller_test.cpp` — 80 real hits when the path is named:

| invocation | controller_test files found |
|---|---|
| `rg -l STAMP_SET .` | **0** |
| `rg --no-ignore -l STAMP_SET .` | **0** |
| `rg --follow -l STAMP_SET .` | **0** |
| `rg --no-ignore --follow -l STAMP_SET .` | **0** |
| `rg -l STAMP_SET tests/` | 1 (80 hits) |

**I could not isolate a single mechanism, and that is the point.** Gitignore alone does not explain
it (`--no-ignore` doesn't rescue), symlink-non-descent alone does not explain it (`--follow` doesn't
rescue), and the two together still return zero. The durable statement is therefore the MEASURED
behaviour, not a mechanism story: **no flag combination makes `.` cover those trees; only naming the
path does.** Stated this way deliberately — a mechanism I cannot demonstrate would be exactly the
plausible-but-unverified claim this arc keeps catching.

**What it costs.** A false NEGATIVE that reads identically to a clean result. This is not
hypothetical: it bit during D-421 step 6 arming on 2026-08-16. Enumerating the `inference_cfg`
group-bit PRODUCER set (`STAMP_SET(…, inference_cfg)`):

| method | real setter sites found |
|---|---|
| `rg … .` + `STAMP_SET\([^)]*inference_cfg\)` | **2** — `StampBoundModelConstRegistry.hpp:856`, `NodeModelZoo.hpp:459` |
| explicit roots + paren-safe match | **7** |

> ⚠️ **Line anchors into `StampBoundModelConstRegistry.hpp` re-derived 2026-08-17** — a +90-line
> insert (D-426 `STAMP_PUT`) silently shifted every cite in this section, and `:715` landed
> *inside* an unrelated new comment rather than obviously nowhere, which is worse than dangling.
> B-Plus's anchor leg is scoped to PLAN BODIES, so `DOCS/`, `tools/` and source comments are
> ungated and nothing reds on this class. **Re-derive by SYMBOL, not by line:**
> `grep -n 'STAMP_AUTOPOPULATE_SET_HAS_inference_cfg\|STAMP_PARSER_SET_HAS_inference_cfg'`.

The 5 missed: `StampBoundModelConstRegistry.hpp:826` (paren trap — the site D-421 calls *"the single
site whose reachability decides the whole loop"*) and all four in `tests/` (symlink trap):
`controller_test.cpp:15588`, `:15662`, `:24017`, `:27783`. Class 58's own detection block names
*"the only PRODUCER is a test fixture"* as the highest-yield check of sub-shape B — and that is the
one check `.`-recursion is structurally guaranteed to fail.

**A third silent-zero in the same sitting, worth its own line:** this shell is **zsh**, which does
NOT word-split an unquoted `$VAR`. `R="dirA dirB"; rg pat $R` passes ONE bogus path named
`"dirA dirB"` → rg errors to stderr and the pipeline prints nothing. Suppressed with `2>/dev/null`
it is indistinguishable from a clean no-match. Use a literal path list, an array, or `${=R}`.

**Also note the counts here are SETTER SITES, not "fixtures that hide a bug".** Of the four in
`tests/`, only `:15588` and `:15662` drive `stamp_write_for_model → verify_model_stamp` (the
chain-exercising fixtures that make a dead gate look live); `:24017` and `:27783` are macro-semantics
unit tests over synthetic local structs (`struct StampTest { uint64_t has_flags = 0; }`) and are
entirely legitimate. Any tool partitioning producers by production-vs-test needs that THIRD category
or it will report the legitimate two as findings.

**How to avoid it.** Name roots explicitly and REPORT which you covered:
`rg <pat> CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/`
A tool doing this enumeration must resolve the symlinks or take an explicit root list — and any
finding of the form "no producer exists" is unsound until the search boundary is stated.

**Second trap found in the same breath (different family, same paragraph of damage).** The regex
`STAMP_SET\([^)]*inference_cfg\)` misses `STAMP_SET((inf), inference_cfg)` — `[^)]*` cannot cross the
nested paren. That miss drops `ML_Headers/StampBoundModelConstRegistry.hpp:826`, which D-421 records
as *"the single site whose reachability decides the whole loop"*. Match with paren-depth awareness,
never a negated-char-class. This is the same defect class as the `fox-symdeps` `header_base` bug
fixed the same day (a pattern blind to `<>` nesting returned a template argument where a function
name belonged) — **nesting-blind patterns are their own recurring shape, on angles and parens alike.**

**Related:** Landmine 13 (rg vs gitignore rule KIND — same blindness family, different mechanism, and
its fix does not fix this) · the symlink-topology family Landmines 5 / 7 / 9 / 10 · Class 58 sub-shape
B · D-421 step 6 · `DOCS/SUBAGENT_ARMING.md` § 3.1 (where the standing rule now lives).

## Landmine 20: the sanitizer builds could not run at all — and the failure mimics a truncated test suite (2026-08-16)

**Symptom.** `./build.sh asan` prints `--- asan: ok ---`, then `./build_asan/controller_test` dies
instantly with `AddressSanitizer: stack-overflow ... in main` without running a single test.

**Cause 1 — stack.** H1 keeps the engine off the heap, so the char-test fixtures are stack objects
and `main`'s frame is already large. ASan wraps every stack object in redzones; the frame measured
**~72MB** (`bp-sp` at the abort) against the usual **8MB** `ulimit -s`. The plain `-O3` build fits;
the instrumented one cannot. Raising to 64MB is still not enough — use 256MB.

**Cause 2 — leaks, and this is the one that wastes an hour.** Boot-time node arenas are allocated
once and never freed (correct for a process meant to run for weeks; tests build many controllers
without tearing them down). LeakSanitizer therefore reports **~187MB across ~1100 allocations** from
`PortfolioController_Init` / `EventLoopState_Init` / `_alloc_and_init_slow_state` on *every* run.

**Why cause 2 is a trap rather than noise.** LSan runs at exit and takes the process down **before
stdout is flushed**. So the last visible line is truncated mid-word, the final `RESULTS:` never
prints, and the last surviving summary is an **intermediate** section tally — `RESULTS: 1109 passed,
0 failed`. Against the plain build's 3755 that reads exactly like *"ASan only covers 30% of the
suite"*. It does not. Every test ran and passed; you are looking at a buffering artifact.

**The fix — use the runner, not the raw binary:**

```bash
tools/run_sanitizer_tests.sh asan     # or ubsan / tsan
LEAKS=1 tools/run_sanitizer_tests.sh asan   # opt in when auditing allocation lifetime
```

All three are GREEN as of 2026-08-16: **3755 passed / 0 failed / 0 diagnostics / rc=0** each.

**TSan corollary.** TSan reports 2-3 data races in `TUISnapshot_ReadInto` / `Publish_End`. That is a
**seqlock**: the payload copy races by design and correctness comes from the `s1 == s2` re-check,
which TSan has no model for. The real guard is the v5.11.3.B `tear_count == 0` test. Suppressed with
a stated reason + cost in `tools/tsan_suppressions.txt`; the proper fix is `__tsan_acquire`/
`__tsan_release` annotation, after which the entry should be deleted.

**And the meta-lesson, which cost the most time here.** The first cut of `run_sanitizer_tests.sh`
grepped only for `ERROR: ...Sanitizer` — but TSan says `WARNING:`. It printed **PASS** on a run with
`rc=66` and 3 live races. A green built by a detector that cannot see the failure mode is AR-18 all
over again, committed inside the tool written to make sanitizers trustworthy. The runner now gates on
three independent signals: a final `RESULTS` line exists (an early death is not a pass) · zero
diagnostics (both `ERROR` and `WARNING` spellings, plus TSan's own tally) · `rc == 0`, with an
explicit message when the suite is green but the runtime disagrees.

## Landmine 21: the engine↔workspace symlink topology breaks tools that RESOLVE it — compile-outside-build-dir and engine-side subpaths both fail (2026-08-20)

**Two measured instances, one family** (the symlink-topology family of Landmines 5/7/9/10/19,
but a different mechanism than 19's search blindness — these are tools that FOLLOW the link and
then trip on what they find):

1. **The tests TU is uncompilable outside the build dir.** `g++ -fsyntax-only tests/controller_test.cpp`
   from the engine root fails: g++ **realpath-resolves** the `tests/` DIRECTORY symlink to
   `~/code/tick-trader-percore-workspace/tests/`, after which the TU's relative includes
   (`../FixedPoint/...`) resolve against the WORKSPACE root and miss — the engine's sibling dirs
   are not there. Measured at the E.1.2.C a-class pass (plan-level verdict A-10). The build-dir
   compile works because CMake passes absolute include dirs; ad-hoc syntax probes, clangd without a
   compile-commands entry, and any "quick `g++ -fsyntax-only`" sanity check all hit this. **Probe
   from the build system's flags or not at all.**

2. **Engine-side subpaths under a per-FILE-symlinked dir do not exist.** Engine `DOCS/` is a REAL
   dir containing per-file symlinks (e.g. `DOCS/TECH_DEBT.md -> ../../tick-trader-percore-workspace/...`),
   NOT a dir symlink — so workspace-side SUBDIRS (`DOCS/tech-debt/open.md`) have no engine-side
   path at all. Measured 2026-08-20: `rg ... DOCS/tech-debt/open.md` from the engine root → exit 2
   file-not-found, which reads as "no matches" if the rc is swallowed (Class-57 adjacency). Same
   session, the reverse trap: `tests/`/`tools/`/`plans/` ARE dir symlinks, so those engine-side
   subpaths DO work. The topology is MIXED by design (privacy boundary) — never infer one rule
   from the other.

**Mitigation / rule:** for workspace-owned trees, name the WORKSPACE ABSOLUTE path in tools,
greps, and editors (`~/code/tick-trader-percore-workspace/DOCS/...`); compile probes on the tests
TU go through `build/` (or replicate CMake's `-I` set). The handoff "WILL BITE" line that carried
this ad hoc now lives here.

**Related:** Landmine 19 (search-side blindness of the same topology) · `feedback: engine CLAUDE.md
is a symlink` memory (edit workspace-side) · E.1.2.C plan register #14 · a-class plan verdict A-10.

**Landmine 21 addendum (2026-08-20, same close):** engine `DOCS/` has exactly ONE regular file among
its 61 per-file symlinks — `DOCS/CODE_MAP.md`. The regen (`gen_code_map.sh`) writes it ENGINE-LOCALLY
(gitignored); the version-controlled copy is the workspace-TRACKED mirror, which must be re-SYNCED at
close (`cp` engine→workspace, the `1a4ec47`-precedent step) or the committed ground-truth map goes
stale while the live one looks current. Measured this close: the mirror was two sessions stale and
still listed a deleted function until the Stage-5.5 reviewer caught it. Corollary to the mitigation
rule above: "use workspace absolute paths for workspace-owned trees" EXCEPT CODE_MAP, where the
engine-side file is the fresh one and the workspace copy is the committed one.


---

## Landmine 22 — `ControllerConfig<F>` is RAW-FINGERPRINTED; adding a field to it breaks every model stamp

**Cost:** one build cycle + a full revert of a nearly-finished change (2026-08-21, E.1.2.D).

**What happened.** Fixing the hyperparameter split-brain needed three values (`max_depth`,
`learning_rate`, `n_estimators`) to reach the validation trainers. The obvious route — and the one
its four already-plumbed siblings use — is to add them to `ControllerConfig`, since both trainers
read `data->config_used`. That builds cleanly right up until:

```
ControllerConfig.hpp:1476: static assertion failed: ControllerConfig<F> layout changed ->
the RAW model-fingerprint shifts. Bump N to the new sizeof AND regen the backtest golden. (D-254)
```

**Why it bites.** The struct is memcmp'd/hashed RAW into the model fingerprint (H9/H12), so its
`sizeof` is wire-visible. A field added for a purely *training-time* convenience invalidates the
cfg fingerprint on every existing stamp. The guard is a `static_assert`, so it is loud and
immediate — but only AFTER you have written the field, its default, and its consumers.

**The rule:** before adding ANY field to `ControllerConfig`, ask whether the value is engine
CONFIGURATION or merely transport. If it is transport (a click-time snapshot, a per-run parameter),
thread it as a function parameter instead — `Backtest_RunFullValidation`'s
`const tt::XGBHyperparams *hp_override` (default `nullptr` = prior behaviour bytewise) is the
worked example. Perturbing a fingerprinted struct for a training-time convenience is the wrong
trade even when it compiles.

**Related:** D-254 (the size-pin) · H9/H12 · D-430 (5) · the E.1.2.D plan leaf 4.
