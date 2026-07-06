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

## 2.5 Comments are point-in-time — verify code-BEHAVIOR claims against the code
A comment was accurate WHEN WRITTEN; code + codegen drift, so a comment is **NOT ground truth** for a behavior fact. When a comment asserts codegen (`// CMOV-style` / "branchless" / "compiles to X"), latency/perf ("~4ns" / "verified in bench_X"), or size/layout/complexity — **verify it against the actual compiled code** (disassemble · `check_latency_path_conformance.py` · `check_struct_size_budget.py` · read current code), never trust the comment. On a MISMATCH the **CODE is truth** — SURFACE the stale comment as a FINDING + SUGGEST the corrected wording (a stale code-fact comment isn't background; it actively misleads). Canonical miss (2026-06-30): a stale `// CMOV verified in bench` survived because an agent trusted it instead of disassembling — written pre-Ship-B (no x86 128-bit cmov for 16B `Money`; the analyzer's disassembly shows a real `je`), it nearly inverted the recommendation. Sister: `mechanical-verification-of-derived-code-facts.md` · `feedback_ground_design_in_real_code` · AR-8 (the writer is model-bounded — a stale self-comment is that bound made durable).

## 2.6 In-code tag-grammar — read tagged code + write it right (E.1.2.A)
The codebase is converting to a structured `[TAG]_` comment scheme — grammar SSoT: `DESIGN_SPECS/doc-disciplines/in-code-documentation-schema.md`. A converted unit = an orient block (`[FUNCTION]`/`[STRUCT]`/`[REGISTRY]`/`[FILE]` + `[TAG]`/`[SCOPE]`/`[SCHEMA]`/`[OVERVIEW]`/`[DIAGRAM]`) → `[CODE]`…`[END_CODE]` (the body, comments moved OUT) → detail (`[COMMENT]` dated partitions + `[SUPPORTING_DOCS]`/`[REFERENCE]` + a tool-owned `[DERIVED]` block). Rules you MUST honor: **(1) parse = ONE innermost-bracket regex** `\[([^\[\]]+)\]`, token[0]=CATEGORY (a closed set), rest=values; the outer `[[a] [b]]` list-grouping is non-innermost → skipped. **(2) `[TAG]` VALUES live in the ONE vocab** `DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md` (code renders UPPER_SNAKE, docs lower-hyphen; `_upper_snake_to_vocab` maps them). The classify/component families landed at D-322 — but **write the reuse-renames `[OMS_DRAINER]` / `[DETERMINISM]` / `[PERSISTENCE]` / `[BITMAP_PACKED]`, NOT `[DRAINER]` / `[DETERMINISTIC]` / `[PERSISTED]` / `[BIT_PACKED]`** (those RED). **(3) `[DERIVED]` facts** (`[SIZE]`/`[BRANCHES]`/`[STRADDLE]`/`[UPSTREAM]`/…) are TOOL-generated + CI-checked — **NEVER hand-edit** (that's the Class-18 mirror the system exists to kill); refresh via the tool. **(4) preserve the author's voice VERBATIM** when relocating prose into `[COMMENT]`/`[WHY]`. The validator `tools/check_code_tag_blocks.py` gates all of this (wired into `check_session_docs`; `[REFERENCE]` ids must resolve). A file with **no `[SCHEMA]_[` block is un-converted → treat it as prose**, don't force-convert. LAYOUT facts = clang; CODEGEN facts (instr/branches) = g++ ONLY (D-321).

## 3. Mechanical toolchain — SEARCH the tool index BEFORE you grep, then RUN the tool over grep
**The rule (general — do this for ANY directive; do NOT rely on the list below being complete or on recalling which tools exist):** before you reach for grep/bash to answer a directive, LOAD + SEARCH the full `DOCS/TOOLS.md` inventory (it's small — load it, don't skim from memory) for a tool that covers the directive. If one does, RUN it — the tool is the *authority*, and it catches the compiler-blind / transitive / ledger surfaces a grep silently misses (canonical: `check_identifier_retirement`'s ledger + tool-SOURCES lockstep — a grep would never flag it; the #3 + deletion sweep 2026-07-01 grepped where these were the authority → the orchestrator had to re-run them). Grep is the FALLBACK — correct ONLY for **open-ended discovery** where no tool matches ("find every decision-anchored replica"). The tools you'll hit most (ILLUSTRATIVE — `DOCS/TOOLS.md` is the SSoT, not this list):
- **`tools/gen_code_map.sh`** — regen CODE_MAP; **`--composition <T>`** (transitive byte-affected containers) + **`--byte-context <T>`** (the sizeof / memcmp / fwrite / HMAC enforcement sites) = the MANDATORY struct-layout cascade (CoreFrameworks surface rule — run FIRST before any core-struct layout change; don't grep for containers).
- **`tools/check_struct_alignment.py`** — (a) `alignas(>16)` bare-malloc guard + **(c) byte-serialization size-pin coverage** (a fwrite/memcmp/SHA/HMAC type MUST carry `static_assert(sizeof==N)`; H9/H12). RUN for a serialization / size-pin question.
- **`tools/check_identifier_retirement.py`** — H21 wire-id / snapshot-VERSION / persisted-enum tombstone guard vs the golden ledger. RUN before deleting/renumbering a persisted identifier (it flags the ledger + tool-SOURCES rows a grep misses).
- **`tools/check_per_node_registry_integrity.py`** — PerCoreCfg X-macro integrity + Class 25/26 paired-access + UNINDEXED-GLOBAL. RUN for a per-node cfg-scope question.
- **`tools/check_latency_path_conformance.py`** *(NEW `.E.1.0`)* — static ASM latency-path gate: instruction-count budget · branch-classification `{loop / rare-cold / data-dependent-warm}` (the **H7/H20 meter** — drive data-dependent-warm → 0, D-235) · H4 no-scalar-float (incl. AVX/FMA) · no div / malloc / indirect / vtable · stack-spills · **non-vacuity self-defense**. `--selftest` (teeth) · `--asm` · `--update-budgets` (ratchet baseline).
- **`tools/check_struct_size_budget.py`** *(NEW `.E.1.0`)* — `sizeof` + cache-tier guard for non-serialized runtime structs (the derived-facts-drift guard; D-229). `--selftest`.
- **`tools/calls_graph_diff.sh`** — hot/sharded-path orphan + structure check (`SHARDED_FILES` sources `tools/lib/sharded_files.txt`). RUN for an orphan / dead-code question.
- **`tools/check_determinism.sh`** — FP-golden + locale + replay + **gate 4 = H10 SIMD-fallback byte-compare**.
- **`tools/check_session_docs.sh`** — one-shot doc/plan CI aggregator (every doc/plan check in one run).
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
