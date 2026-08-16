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

## 2.5 Comments are point-in-time — verify CHECKABLE claims against the code
A comment was accurate WHEN WRITTEN; code drifts, so a comment is **NOT ground truth** for any fact you are about to rely on. **Verify when the claim is load-bearing for the work you are doing** (not every comment you read — that decays into noise). On a MISMATCH the **CODE is truth** — SURFACE the stale comment as a FINDING + SUGGEST the corrected wording (a stale code-fact comment isn't background; it actively misleads).

**The checkable-claim taxonomy** — WIDENED 2026-08-15 (E.1.2/D-421). This section used to list only codegen/perf/size, and **five of six real instances found in one session fell outside those triggers**; the agents caught them by generalizing past the letter of the rule, which is luck, not a rule working. Verify:
- **codegen** (`// CMOV-style` / "branchless" / "compiles to X") · **latency/perf** ("~4ns" / "verified in bench_X") · **size/layout/complexity** → disassemble · `check_latency_path_conformance.py` · `check_struct_size_budget.py`
- **reader/writer sets + concurrency** ("single writer AND reader" / "no atomics needed" / "the GUI reads X, not Y") → grep every reader. *Canonical: `SlowPathGateRegistry.hpp` asserted single-reader + "GUI reads PerNodeSnap, not gate_state"; the snapshot publisher reads `gate_state` from the producer thread to BUILD that PerNodeSnap bit. All three clauses false — and that comment is very likely **why** the field was never initialized: it told every later reader there was nothing to ask.*
- **quantifiers** — *every / all / only / never / single* → enumerate the set (M9). *`node_dd_pct` "recomputed before every read" covered 2 of 4.*
- **default values** → read the `_Default` function. *`oms_event_log_mode` "0 = legacy (default)" — the default is 1.*
- **guard-or-tool existence** ("CI Check N enforces…", "`tools/X.py` catches this") → `ls` it. **Highest severity of the family**: it doesn't just misinform, it manufactures confidence and stops anyone looking. *A registry comment promised "NEW CI Check 8 enforces…" for a tool that was never written; Class 30 was documented as structurally closed by nothing.*
- **`file:line` cites** → resolve them. *`Async.hpp` cited `ControllerEventLoop.hpp:3461`; the write was `:3486`.*
- **ordering** ("reset at the top of each rebuild") → compare line positions. *`strategy_halt_reason`'s reset sat 59 lines BELOW its producer; 17 of 20 SHALT codes had been unobservable since 2026-04-30.*

**Corollary — EXTEND the grammar, never work around it.** A comment stays verifiable only if what it says is expressible in the checked vocabulary. If the tag grammar can't say your thing, add the token: `check_code_tag_blocks.py` DERIVES the CATEGORY set from the ```category-set``` fence in the schema spec, so folding one is ONE token and ZERO tool edits — doc, code and gate stay equivalent by construction. Ask in order: (1) does the concept already exist one level down as a VALUE under an existing category? (2) only then, add the token. **Never smuggle the meaning into free text to get past the gate** — a value the grammar doesn't know is a claim no check can ever verify, which is exactly how the next stale comment is born. The gate now teaches both branches at the RED. Canonical miss (2026-06-30): a stale `// CMOV verified in bench` survived because an agent trusted it instead of disassembling — written pre-Ship-B (no x86 128-bit cmov for 16B `Money`; the analyzer's disassembly shows a real `je`), it nearly inverted the recommendation. Sister: `mechanical-verification-of-derived-code-facts.md` · `feedback_ground_design_in_real_code` · AR-8 (the writer is model-bounded — a stale self-comment is that bound made durable).

## 2.6 In-code tag-grammar — read tagged code + write it right (E.1.2.A)
The codebase is converting to a structured `[TAG]_` comment scheme — grammar SSoT: `DESIGN_SPECS/doc-disciplines/in-code-documentation-schema.md`. A converted unit = an orient block (`[FUNCTION]`/`[STRUCT]`/`[REGISTRY]`/`[FILE]` + `[TAG]`/`[SCOPE]`/`[SCHEMA]`/`[OVERVIEW]`/`[DIAGRAM]`) → `[CODE]`…`[END_CODE]` (the body VERBATIM — code-local comments STAY: struct-field comments, function step-comments, sub-group headers all remain in place; ONLY the unit-level WHY relocates — D-326) → detail (`[COMMENT]` dated partitions + `[SUPPORTING_DOCS]`/`[REFERENCE]` + a tool-owned `[DERIVED]` block). Rules you MUST honor: **(1) parse = ONE innermost-bracket regex** `\[([^\[\]]+)\]`, token[0]=CATEGORY (a closed set), rest=values; the outer `[[a] [b]]` list-grouping is non-innermost → skipped. **(2) `[TAG]` VALUES live in the ONE vocab** `DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md` (code renders UPPER_SNAKE, docs lower-hyphen; `_upper_snake_to_vocab` maps them). The classify/component families landed at D-322 — but **write the reuse-renames `[OMS_DRAINER]` / `[DETERMINISM]` / `[PERSISTENCE]` / `[BITMAP_PACKED]`, NOT `[DRAINER]` / `[DETERMINISTIC]` / `[PERSISTED]` / `[BIT_PACKED]`** (those RED). **(3) `[DERIVED]` facts** (`[SIZE]`/`[BRANCHES]`/`[STRADDLE]`/`[UPSTREAM]`/…) are TOOL-generated + CI-checked — **NEVER hand-edit** (that's the Class-18 mirror the system exists to kill); refresh via the tool. **(4) preserve the author's voice VERBATIM** when relocating prose into `[COMMENT]`/`[WHY]`. The validator `tools/check_code_tag_blocks.py` gates all of this (wired into `check_session_docs`; `[REFERENCE]` ids must resolve). A file with **no `[SCHEMA]_[` block is un-converted → treat it as prose**, don't force-convert. LAYOUT facts = clang; CODEGEN facts (instr/branches) = g++ ONLY (D-321).

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

### 3.1 When you DO grep: `.` does not mean the tree (Landmine 19)
`rg <pat> .` from the engine root **silently returns ZERO hits** from `tests/`, `tools/`, and
`plans/` — they are gitignored *and* directory symlinks into the workspace, and **no flag
combination rescues it** (`--no-ignore`, `--follow`, and both together were each measured at 0).
Naming the path (`rg <pat> tests/`) works normally. So an unqualified `rg … .` quietly answers a
*different question* than the one asked, and reports it with the same confidence.

**Always name your roots explicitly** — `rg <pat> CoreFrameworks/ Strategies/ ML_Headers/
MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/` — or search the workspace copy.
Then state in your report WHICH roots you covered, so a reader can see the boundary of your claim
instead of inferring "the tree".

**Why this is load-bearing and not pedantry:** Class 58's highest-yield check is *"the only
PRODUCER is a test fixture"* — a shape that lives, by definition, in `tests/`. An agent grepping
from `.` finds no fixture, concludes the producer set is empty, and returns a confident
false negative on precisely the check that matters most. Sister: Landmine 13 (rg vs gitignore rule
KIND) — same blindness family, different mechanism, and 13's fix does not fix this one.

## 4. Honor the cited decisions — don't re-litigate
Honor the decisions the orchestrator cites (the decision log). Don't re-open a **settled fork** (tombstone re-litigation wastes the pass — `feedback_arm_subagents_plan_and_future_aware`). If the supplied shape/seam is **materially wrong**, FLAG it loudly (the re-cascade signal, `feedback_recascade_audit_on_corrected_shape`) — never silently build on an invalidated frame.

## 5. Invariants in play (the orchestrator names the subset)
H1–H22. Hot/slow recurring: **H4** (Money / `FPN_Binary`, never float) · **H7/H20** (branchless data-dependent dispatch) · **H8** (hot p99 ≤500ns / slow ≤100µs) · **H11** (constant-iter + branchless reductions) · **H2** (no virtual / indirect on hot) · **H22** (per-node purity / scale-invariance).

## 6. Output contract
Structured, **severity-classified** findings, each citing `file:line` from CODE_MAP/grep (never recalled). You **RETURN findings** to the orchestrator — you do **NOT** edit code and you do **NOT** auto-proceed (consult-before-coding). A passing test is not verification (`feedback_passing_test_is_not_verification`); adversarially confirm your own work before "done". Your final message **IS** the data.

## 6.5 Report persistence (operator directive 2026-08-10 — every report is KEPT)
Your final report is saved **VERBATIM** to
`plans/<sprint>/reports/<YYYY-MM-DD>-<directive-slug>/<agent-task-slug>.md` — by the
**ORCHESTRATOR, at receipt** (you stay read-only; never write your own report file). So write
your final message as a **complete standalone document**: self-contained title, every claim
`file:line`-cited, refute-spots and open questions IN the report — assume it will be re-read
months later with zero conversation context. Raw transcripts in `/tmp` die at reboot (the
D-414 loss); the saved report is the durable artifact, and the `plan_checks/` register built
from it is the curated disposition layer — both exist, neither substitutes for the other.
Orchestrator side: save BEFORE synthesizing (`feedback_save_agent_reports_verbatim`);
`/reports/` is `frozen_record_paths`-enrolled (truthful artifacts — cite-repair/staleness
gates skip them).

## The registry (roles → `.claude/agents/`)
| Type | Role | Use |
|---|---|---|
| **i-class** | INVESTIGATIVE | map the surface / write-set / call-sequence / blast-radius / options → recommend |
| **a-class** | ADVERSARIAL | FIND/REFUTE a recommendation (default-refuted); the simpler/safer option; the cascade |
| **v-class** | post-impl VERIFY | the M8 Definition-of-Done (build + tests + sanitizers + calls_graph + parity + docs) |
| **d-class** | DECOMPOSITION | cut-lines + INBOUND/OUTBOUND seams for a too-big ship/plan |
| **c-class** | CURRENCY | re-ground vs HEAD + decided-vs-open sweep (stale prose / superseded seams / drifted cites) |

Lifecycle of a cascade: **C → D → I → A → [code] → V**. Label spawned agents `I-1`/`A-2`/`V-1`/… The skills that ARE this pattern: `/precoding-audit-gate` (I→A gate) · `/decision-check` (investigate→refute) · `/post-ship-audit` + the V-class discipline.
