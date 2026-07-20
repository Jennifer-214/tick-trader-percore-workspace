---
type: meta-discipline
stage: 3-first-canonical
established: 2026-06-02
sprint: v5.15-live-readiness
tags: [privacy-boundary, ecosystem, workspace, repo-hygiene, institutional-memory]
surface: [repo-structure, build, tooling]
sister_specs:
  - meta-disciplines/single-source-of-truth-discipline.md
  - meta-disciplines/structural-enforcement-when-memory-insufficient.md
  - data-disciplines/file-size-split-discipline.md
status: active
---

# Public/Private Boundary + Ecosystem Discipline ("the code-only-public law")

The governing rule for what lives in a PUBLIC project repo vs the PRIVATE workspace,
and how the workspace becomes a reusable ecosystem. Decided 2026-06-02 (Caramel) during
the v5.15 "spring cleaning" pass on `FoxML_Trader_v2`.

> ## ⚠️ SUPERSEDED AS A GOING-FORWARD LAW — 2026-07-19
>
> **Everything went ALL-PRIVATE on 2026-07-06.** All repos migrated to the `Jennifer-214`
> GitHub account and were set private; there is **no live public repo** for the code-only law
> below to govern. Confirmed by Caramel 2026-07-19: *"its all private repos… ill eventually make
> something public or make people sign NDAs or something."*
>
> **What this means for a reader:**
> - **The law below is HISTORICAL.** It accurately describes the 2026-06-02 → 2026-07-06 regime and
>   the public snapshot that still exists from it. **Do NOT apply it as a constraint on new work** —
>   going-forward development is unconstrained by a public/private split, so private-only material
>   (exotic approaches, operator apparatus, full docs) may live wherever it fits best.
> - **The `.gitignore`-in-place mechanism it describes is now legacy motivation.** Paths were ignored
>   to keep a public repo code-only. That rationale is dead. Ignores that remain should be justified
>   by a CURRENT reason (build artifacts, generated files, secrets) — not by this law.
>   → This directly matters to tooling: **`.gitignore` must never be an implicit input to corpus
>   membership** (the TECH_DEBT-245 shape — see D-393 / `doc-intelligence-toolchain-architecture.md`
>   § "The corpus contract").
> - **The ecosystem section below still stands** — the workspace-as-reusable-template thesis is
>   independent of whether any given repo is public.
>
> **Re-publication is an OPEN question, not a settled boundary.** Caramel has floated a future public
> surface and/or NDA-gated access. When that is decided it earns a NEW decision entry and this spec is
> rewritten around it — the old law should not be silently reactivated as the default.
>
> Sisters: memory `project_public_repo_is_code_only` (records the pivot) · D-390 mechanism 3 (content
> staleness — this spec read `status: active` describing a dead regime for ~2 weeks, which is exactly
> the shape the `0.2` (g) supersede-check is being built to catch).

## The law

> **A public project repo contains ONLY what someone needs to COMPILE-AND-RUN the code.**
> Source + build system + `LICENSE` + a **one-page `README`** (what it is · how to build · how to
> run) (+ assets the README renders). **Everything else is private** — tests, all dev/CI tooling,
> **ALL docs (including `CHANGELOG` + operator/usage/config manuals — depth never goes public)**,
> experiments, benchmarks, runtime state, and the operator's workflow apparatus.

**The discriminator:** *"compile + run the artifact"* → public. *"how it's built / operated-in-depth /
maintained / reasoned-about"* → private. The public repo is the **artifact**, not a window into the
workflow — so even a polished operator manual or CHANGELOG is private (it documents *operating*, not
*compiling*). The one public doc is a one-page README; everything deeper lives in the private `DOCS/`.

**Why (operator rationale):** the public repo is a clean *artifact*, not a window into the
workflow. "People already saw *how* I work — that was useful; now they just get the code."
The dev apparatus isn't hidden out of secrecy (the private workspace's existence is known) —
it's *relocated* so the public face is uncluttered and the apparatus can ship as its own
deliberate **template-workspace release** later, if there's demand.

**The alpha is never the question.** The genuine edge (models, `*.cfg`, tuning, strategy
params) is *already* private. So the public/private line is NOT about secrecy — it's about
**what the public artifact IS**: the engine, buildable, nothing else.

## What's PUBLIC (the compile-and-run set)

Engine source (`CoreFrameworks/` `Strategies/` `ML_Headers/` `FixedPoint/` `MemHeaders/`
`DataStream/` `Backtest/` `GUI/` + `main.cpp` / `foxml_suite.cpp` / `Version.hpp` /
`Limits.hpp` / `Licensing.hpp`) · build system (`CMakeLists.txt` `Makefile` `build.sh`
`run.sh` `scripts/`) · `LICENSE` (legal, AGPL) · **one-page `README.md`** (compile-and-run only — all
depth lives in the private `DOCS/`) · `assets/` (only if the README renders them) · `.gitignore`.

## What's PRIVATE (everything else)

`tests/` · `tools/` (all CI/dev/doc tooling) · `DOCS/` · `claude-skills/` · `.githooks/` ·
`experiments/` · `build_latency/` · `OPS/` · runtime state (`*.snapshot`) · cfg examples ·
`CODE_OF_CONDUCT.md` / `BOUNTY.md` (operator-discretion: community files MAY stay public).

## Mechanism (build-safe; learned the hard way)

1. **Default: gitignore-in-place** — add the path to `.gitignore` + `git rm -r --cached` it.
   The file **stays physically on disk** (local build / dev / hooks all work unchanged), it
   is just **untracked** → not published. This is the safe, reversible default. It does NOT
   move anything, so nothing that resolves paths can break.
2. **For the syncable apparatus (tools/), relocate to the workspace + symlink back** —
   `mv` to `../tick-trader-percore-workspace/<dir>`, leave a gitignored dir-symlink in the
   engine. This makes the workspace the SSoT (the "living syncable method"). BUT it triggers
   the resolution landmine below.
3. **Guard the build for a public clone** — `build.sh` / `CMakeLists.txt` reference the now-
   private `tests/` + `tools/`. Wrap each reference so an absent dir is skipped, not fatal:
   - `build.sh`: `[ -f tools/X ] && python3 tools/X` (skip-if-absent).
   - `CMakeLists`: `if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/tests) ... endif()` around dev/test
     targets. A public clone then configures + builds the **engine**, skipping dev targets.

## Landmines codified by this pass

- **`Path(__file__).resolve()` FOLLOWS symlinks → use `.absolute()`.** A tool that derives
  its repo root from `__file__` and lives in the workspace (symlinked into the engine) will
  resolve into the WORKSPACE and hunt for engine source there → build ABORT. `.absolute()`
  keeps the engine (symlink) path; `.resolve()` follows it to the workspace. For `.sh`, use a
  `${FOXML_ENGINE:-$(cd "$(dirname "$0")/.." && pwd)}` env-override. **Private tools MAY
  hardcode** the engine path (only on the operator's machine), but `.absolute()`/env is
  cleaner — private *and* portable across the operator's machines / SSH-grid. (Sister:
  `feedback_machine_portable_resolver_for_committed_tool_paths`.)
- **zsh does NOT word-split unquoted vars in `for` loops.** `for p in $LIST` runs ONCE with
  the whole string. Use a Python loop (or `${=LIST}` / an array) for list iteration in the
  Bash tool — this bit the move TWICE this session (silent `MOVED=0`).

## The ecosystem (where this is going)

`workspace-template` (`~/code/workspace-template`) is the reusable scaffold: an `/instantiate`
engine that scans a target repo, interviews, and scaffolds a private `<project>-workspace`,
symlinking the workflow in + gitignoring it in the host. Per-project workspaces
(`tick-trader-percore-workspace`, `linux-theme-workspace`, …) are instances. This boundary
discipline is a **template law** — every instantiated project inherits "public = code,
private = apparatus." The host-gitignore the template installs should encode this set.

## Cross-references

- The session's full decision trail: `plans/v5.15-live-readiness/decision-logs/` (this pass).
- Correctness-first prime directive (the sister "law"): `DOCS/DESIGN_PHILOSOPHY.md` §0 +
  `memory/user_correctness_first_not_ship_fast.md`.
- Always-loaded byte-budget guard (sister hygiene): `tools/check_always_loaded_budget.py` +
  `data-disciplines/file-size-split-discipline.md`.
- TECH_DEBT-153 (the narrower precursor: meta-only tools-privacy) — SUPERSEDED in scope here.
