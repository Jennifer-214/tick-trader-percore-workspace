# SUBAGENT_ARMING.md — standing arming for spawned audit subagents

> SSoT for the M8 arming set, so it is a **registry row, not a memory** — closes the recurring
> *"I always forget to tell subagents about the new tools / skills"* gap (task #12, promoted `.E.1.0`).
> Every custom audit agent type (`.claude/agents/{i,a,v,d,c}-class.md`) reads THIS first.
> The ORCHESTRATOR hands the **per-surface kit** (target fn / specs / classes / invariants) in your
> spawn prompt; THIS doc is the standing half. Sister disciplines: M8
> (`definition-of-done-and-armed-scout-verification.md`) · `feedback_arm_subagents_plan_and_future_aware`
> · `feedback_run_dedicated_audit_skills_not_just_armed_prompts`. Paths are engine-root-relative
> (your cwd is the engine root).

## 1. Scout-first (M8)
Load → scout → execute. Never execute blind. Arm with the refs + toolchain + nav-infra + domain skill BELOW, scout the surface, THEN do your role's work.

## 2. Nav-infra — CONSULT before analyzing (read it; don't recall from memory)
- **`DOCS/CODE_MAP.md`** — `Pattern_FunctionName` → file:line ground truth (anti-fabrication; grep THIS, never recall a line). Regen if stale: `./tools/gen_code_map.sh`.
- **`DOCS/TOOLS.md`** — the tool inventory + disposition + invoker. RUN the matched tool; never hand-roll what a tool already does.
- **`DOCS/RECURRING_BUG_PATTERNS.md`** — the bug-class catalog (Class N). The known shapes your finding/edit must not miss or reintroduce (e.g. Class-51 vacuously-green guard · Class-50 re-init-defeats-join · Class 43–49 SSoT family).
- **The skill suite** (`CLAUDE.md` § "Skill suite") — APPLY the matched dedicated audit skill's methodology: read `claude-skills/<skill>/SKILL.md` and walk its checklist. Do **NOT** approximate a dedicated skill with a general armed prompt (`feedback_run_dedicated_audit_skills_not_just_armed_prompts` — the dedicated `/dod-audit` + `/hft-audit` passes surface what an H-invariant-only prompt misses).
- **Sprint nav** (paths in your spawn kit): the `.E` dependency-graph DAG + the finding-disposition register.

## 3. Mechanical toolchain — RUN these (don't just read the code)
- **`tools/check_latency_path_conformance.py`** *(NEW `.E.1.0`)* — static ASM latency-path gate: instruction-count budget · branch-classification `{loop / rare-cold / data-dependent-warm}` (the **H7/H20 meter** — drive data-dependent-warm → 0, D-235) · H4 no-scalar-float (incl. AVX/FMA) · no div / malloc / indirect / vtable · stack-spills · **non-vacuity self-defense**. `--selftest` (teeth) · `--asm` · `--update-budgets` (ratchet baseline).
- **`tools/check_struct_size_budget.py`** *(NEW `.E.1.0`)* — `sizeof` + cache-tier guard for non-serialized runtime structs (the derived-facts-drift guard; D-229). `--selftest`.
- **`tools/calls_graph_diff.sh`** — hot/sharded-path orphan + structure check (`SHARDED_FILES` sources `tools/lib/sharded_files.txt`).
- **`tools/check_determinism.sh`** — FP-golden + locale + replay + **gate 4 = H10 SIMD-fallback byte-compare**.
- **`tools/check_session_docs.sh`** — one-shot doc/plan CI aggregator (every doc/plan check in one run).
- **`tools/gen_code_map.sh`** — regen CODE_MAP.
- (`DOCS/TOOLS.md` is the full inventory; the above are the load-bearing + the NEW ones.)

## 4. Honor the cited decisions — don't re-litigate
Honor the decisions the orchestrator cites (the decision log). Don't re-open a **settled fork** (tombstone re-litigation wastes the pass — `feedback_arm_subagents_plan_and_future_aware`). If the supplied shape/seam is **materially wrong**, FLAG it loudly (the re-cascade signal, `feedback_recascade_audit_on_corrected_shape`) — never silently build on an invalidated frame.

## 5. Invariants in play (the orchestrator names the subset)
H1–H22. Hot/slow recurring: **H4** (Money / `FPN_Binary`, never float) · **H7/H20** (branchless data-dependent dispatch) · **H8** (hot p99 ≤500ns / slow ≤100µs) · **H11** (constant-iter + branchless reductions) · **H2** (no virtual / indirect on hot) · **H22** (per-node purity / scale-invariance).

## 6. Output contract
Structured, **severity-classified** findings, each citing `file:line` from CODE_MAP/grep (never recalled). You **RETURN findings** to the orchestrator — you do **NOT** edit code and you do **NOT** auto-proceed (consult-before-coding). A passing test is not verification (`feedback_passing_test_is_not_verification`); adversarially confirm your own work before "done". Your final message **IS** the data.

## The registry (roles → `.claude/agents/`)
| Type | Role | Use |
|---|---|---|
| **i-class** | INVESTIGATIVE | map the surface / write-set / call-sequence / blast-radius / options → recommend |
| **a-class** | ADVERSARIAL | FIND/REFUTE a recommendation (default-refuted); the simpler/safer option; the cascade |
| **v-class** | post-impl VERIFY | the M8 Definition-of-Done (build + tests + sanitizers + calls_graph + parity + docs) |
| **d-class** | DECOMPOSITION | cut-lines + INBOUND/OUTBOUND seams for a too-big ship/plan |
| **c-class** | CURRENCY | re-ground vs HEAD + decided-vs-open sweep (stale prose / superseded seams / drifted cites) |

Lifecycle of a cascade: **C → D → I → A → [code] → V**. Label spawned agents `I-1`/`A-2`/`V-1`/… The skills that ARE this pattern: `/precoding-audit-gate` (I→A gate) · `/decision-check` (investigate→refute) · `/post-ship-audit` + the V-class discipline.
