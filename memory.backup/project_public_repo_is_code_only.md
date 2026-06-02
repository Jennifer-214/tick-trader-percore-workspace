---
name: project_public_repo_is_code_only
description: The public FoxML_Trader_v2 repo = ONLY what compiles/runs the engine; all dev apparatus (tests/tools/docs/skills/CI) is private
metadata: 
  node_type: memory
  type: project
  originSessionId: 5a3e2327-0ab0-43ac-b92b-9fc591f00b51
---

Decided 2026-06-02 ("spring cleaning"): the PUBLIC `FoxML_Trader_v2` repo contains ONLY what's needed to **compile + run** the engine — source + build system (`build.sh`/`CMakeLists`/`Makefile`/`run.sh`/`scripts`) + `LICENSE` + a **one-page `README`** (what it is · how to build · how to run) + `assets`. **Everything else is private** (gitignore-in-place / workspace-symlinked): **ALL of `DOCS/`** (operator/usage/config manuals + `CHANGELOG` + architecture — *depth never goes public*), `tests/` `tools/` `claude-skills/` `.githooks/` `experiments/` `build_latency/` `OPS/` + runtime state + cfg examples. (`DOCS/` real files are workspace-backed + symlinked into the engine, exactly like `tools/` — completed 2026-06-02.)

**Why:** the public repo is a clean *artifact*, not a window into the workflow — "people already saw HOW I work; that was useful; now they just get the code." The dev apparatus relocates to the private workspace and ships as a deliberate `workspace-template` release later if there's demand. The alpha (models/cfg/tuning) was always private, so this is about what the public artifact IS, not secrecy.

**How to apply:** the discriminator is *"compile + run the artifact"* (public) vs *"how it's built / operated-in-depth / maintained / reasoned-about"* (private) — so even a polished operator manual or `CHANGELOG` is private. New file in a public repo → ask "needed to compile/run?" yes = tracked, no = gitignore-in-place (or workspace-symlink if it's syncable apparatus). Build files referencing now-private dirs get skip-if-absent guards so a public clone still builds the engine. Tools symlinked into the engine from the workspace must use `.absolute()` not `.resolve()` (see LANDMINES Landmine 5). Full law: `DESIGN_SPECS/meta-disciplines/public-private-boundary-and-ecosystem-discipline.md`. Sister: [[user_correctness_first_not_ship_fast]]. Supersedes TECH_DEBT-153's narrow meta-only scope.
