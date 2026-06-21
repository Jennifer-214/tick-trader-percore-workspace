---
type: refactor-pattern
stage: 2-draft
version: 1.2
established: 2026-06-21
tags: [refactor-pattern, ci-tooling, bulk-rename, terminology-evolution, static-analysis, structural-fix]
surface: [registry, boot-time, ci-tooling]
sister_specs: [rename-ship-methodology.md, struct-change-cascade-impact-tooling.md, canonical-sister-extension-discipline.md]
sister_docs: [DOCS/recurring-bug-patterns/class-36-overlapping-span-substitution-corruption.md, DOCS/recurring-bug-patterns/class-51-vacuously-green-guard.md, DOCS/recurring-bug-patterns/class-33-consumer-enumeration-undercount-on-deletion.md]
realizes_tech_debt: [TECH_DEBT-175a]
related_skills: [/trace-deps, /dependency-chain-trace, /readiness, /precoding-audit-gate]
related_tools: [check_struct_alignment.py, gen_code_map.sh, check_doc_rename_classification.py, check_tools_inventory.py, check_meta_registry.py, check_identifier_retirement.py]
canonical_decision: D-240 (plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md) — built on D-239; refined by the /decision-check gate (I-1 + A-2 + AR-11 cross-check, 2026-06-21)
applications: ["v5.15.5.F.4d.1.E.1.1 Core→Node rename (1st canonical — this ship)", ".E.1.2 NodeState SoA relayout (cascade.py struct mode — reserved subcommand)"]
---

# `cascade.py` — the change-cascade tool (rename enumeration)

> **Status: DESIGN DRAFT (stage 2), v1.2 — refined by the `/decision-check` gate (2026-06-21).** The reference
> the build follows + the TRACKING home. First canonical = `.E.1.1` (the `rename` subcommand). `struct` is a
> RESERVED future slot (`.E.1.2`; the TD-175 AST Tool A, re-cut). Promotes to stage 3 at `.E.1.1` close.
>
> **Gate outcome (the v1.1→v1.2 reshape):** an I→A `/decision-check` pass (i-class map + a-class refute +
> mandatory AR-11 cross-check) validated the CORE (the apparatus coverage-gap is real; NO canonical-sister
> covers it; the one-tool shape + substrate reuse + TD-175 split are sound) and surfaced two merit refinements
> that REDUCE tech-debt + avoid slop (operator-ratified 2026-06-21):
> - **R1 — `rename` is ENUMERATE-ONLY; no `--apply` over code.** The compiler is ALREADY the totality oracle
>   for code tokens (`rename-ship-methodology.md` Phase 4: human does ONE mechanical commit + red-build-
>   locally). A code `--apply` only adds a Class-36 *silent*-corruption surface (a wrong substitution inside a
>   string/comment COMPILES but is wrong) backstopped by that same compiler. Apparatus is ~10 files → human
>   co-migrates + the guards are the net. `--apply` automation = a NOTED future increment, not built (no
>   redundant corruption surface; no Class-36-algo SSoT-drift vs `check_doc_rename_classification.py`).
> - **R2 — the standing apparatus-currency coverage goes into the EXISTING `check_` guards, not a new
>   `cascade audit` subcommand.** The a-class verified most of it already exists (`check_meta_registry.py`
>   FOREACH-coverage + `check_tools_inventory.py` tool-file-existence); the one genuinely-uncaught gap is that
>   `check_tools_inventory._referenced()` (`:63-92`) omits `build.sh` → the `build.sh:271` silent-skip. So:
>   build the **1-line `build.sh`-scan extension to `check_tools_inventory.py` now** (concrete, convention-
>   fitting — standing guards stay `check_`-prefixed); the broader apparatus→dead-`FOREACH` cross-check is a
>   NOTED future increment (≈80% redundant with `check_meta_registry`; green until a future rename — building
>   it now is the diminishing-returns slop `feedback_framework_layer_payoff_diminishing_returns` warns of).
>
> **Post-build completeness fix (a-class audit, 2026-06-21 — operator: "ensure the tool is finding all places").**
> A V-class/adversarial completeness pass on the FIRST build (hand-list tokens + an identifier-START anchor)
> found a **Class-33 under-enumeration**: it missed `CoreSlowState` (a top-level per-node struct), the ~50-member
> `core_<stat>` field family, the `g_per_core_*` infra, embedded `*_core_id`, the `*_cores` node-count family,
> a whole file (`EventLoopAggregates.hpp`), guard macros, and operator-facing format keys — **2118 → 3645 real
> sites (~42% missed)**. Root cause: the START-anchor + a hand-list. Fix: the FAMILY-REGEX model + the
> sub-word-boundary rule above + a selftest positive-control per family. Verified by a **mechanical
> freeze ⊇ raw-`rg` file-set diff** (closes the AR-8 self-attestation the a-class flagged — the 33 residual
> diffs are all PRESERVE-only `CoreFrameworks` files, zero real misses). **Lesson: an enumerator's completeness
> is itself adversarially verified + mechanically cross-checked, never self-attested — the builder is
> model-bounded (`feedback_capture_and_check_are_model_bounded`).**

## What it is (one line)

`tools/cascade.py` — the operator's "cascade tool," answering *"if I change X, what cascades?"* On-demand:

| Subcommand | Disposition | Question | When |
|---|---|---|---|
| **`cascade rename`** | on-demand (SKILL-WIRED) | a token rename → every site across code **+ the apparatus dirs the compiler can't see** (`tools/`/`build.sh`/`.githooks/`), classified + the `#include`-cascade + the expected-residual allowlist | **`.E.1.1` (now)** |
| `cascade struct <T>` | on-demand | a struct's BYTES change → downstream offset/cache-line cascade (the TD-175 AST Tool A, re-cut) | reserved → `.E.1.2` |

The standing apparatus-currency NET lives in the existing `check_` guards (R2), NOT in `cascade.py`:
`check_tools_inventory.py` (+`build.sh` scan — the concrete fix this ship) catches a renamed tool-file the
apparatus still references. `cascade rename` PLANS the co-migration; the `check_` guards + the compiler CATCH
a miss. `cascade.py` sits BESIDE `check_struct_alignment.py`, REUSING its substrate IDIOM (the `.absolute()`
symlink-safe `ENGINE` resolver [LANDMINES 5/7], comment-stripping, `FOXML_ENGINE`-override selftest) — NOT its
engine-only `SCAN_DIRS`/`iter_files` (cascade must walk `tools/`/`build.sh`/`.githooks/` too; reuse the idiom,
not the literal scan set — the a-class's substrate-boundary catch).

## Why it exists (the coverage gap — "not optional")

The standing `.E.1.0` gates make an **engine-source** rename slip RED-build (the compiler is the totality
oracle for code tokens). **But a rename in `tools/`/`build.sh`/`.githooks/` commits GREEN** — those files
string-match the old spelling. Verified (I-1, `b9ce419`): ≥8 tool files + 2 DATA ledgers + `build.sh` carry
the rename tokens, **3 feeding pre-commit commit-blockers** — `check_per_core_registry_integrity.py:163,220`
(the regex dies silently; Check at `build.sh:271`), `tools/identifier_ledger.txt:13-18` (the `CORE_STATE_FLAG`
golden read by Check H), `check_plan_body_symbol_existence.py:86-87` (Check A symbol→header map). A regex that
no longer matches goes silently dead (`rename-ship-methodology.md` Phase-3 TOOL-REGEX bucket; RBP Class 51).

## Canonical-sister verdict (gate-confirmed — NO sister covers it)

Both the i-class + a-class hunted the "redundant infra" kill hardest (it's the exact mistake the struct-cascade
Tool A spec was RED-reviewed for) and BOTH cleared it independently:
- **vs `check_doc_rename_classification.py`:** structurally `.md`-only (`find_md_files:557-569` → `rglob("*.md")`)
  — CANNOT reach the apparatus surface that is `rename`'s reason to exist. It is the DOC-side EXECUTOR;
  `cascade rename` ENUMERATES (incl. FORWARD-DOC / HISTORICAL-PRESERVE buckets) and DEFERS doc APPLICATION to
  it. (Reuse note: if `--apply` is ever built — see R1 deferral — the Class-36 overlap-resolution must be
  EXTRACTED to a shared `tools/lib/` helper both import, never re-derived — the a-class SSoT-drift catch.)
- **vs `gen_code_map.sh`:** TYPE/struct-layout axis over `*.hpp`/`*.cpp` only (`--composition`/`--byte-context`/
  `--macros`/`--structs`) — never scans `tools/` for arbitrary tokens. Different axis. The struct-byte cascade
  IS its axis → correctly RESERVED to `cascade struct` (the re-cut Tool A), not `rename`.
- **vs `check_struct_alignment.py`:** an unrelated standing alignment/size GUARD — reuse substrate IDIOM,
  separate file (cramming = Class-21).

## `cascade rename` — what it computes

### Inputs (config, not hardcoded — RE-DERIVE per rename; reusable)
- **Token-set = FAMILY REGEXES, not a hand-list** (the completeness model — see the post-build a-class fix
  below). Each token is a regex matched at a SUB-WORD boundary `(?<![A-Za-z0-9])` that **allows a preceding
  `_`** (so embedded compounds — `origin_core_id`, `g_per_core_cfg_field_descriptors`,
  `saved_num_execution_cores` — ARE caught) but **blocks a preceding alnum** (so `score`/`record`/`encore`
  are NOT). The families: `core_[a-z]…` (the `core_id`/`core_idx` + ~50-member `core_<stat>` field family) ·
  `per_core…` · `Core[A-Z]…` (`CoreContext`/`CoreSlowState`/`CoreModelZoo`/`CoreSnap`/`CoreLatency*`) ·
  `PerCore…` · `CORE_[A-Z]…` (`CORE_STATE_FLAG`/`_CTX`/`_MODEL_*` + the guard macros) · `PER_CORE…` ·
  `\w+_cores\b` (`num_cores`/`effective_cores`/`registered_cores`/…) · `\.cores\[` · `core_%[dN]` (the
  operator-facing key format strings) + explicit `FOREACH_PER_CORE`/`FOREACH_CORE`/`MAX_EXECUTION_CORES`/
  `MAX_GUI_CORES`/`num_execution_cores`. Overlap-resolved per Class-36 (sort start-asc/longest-first, accept
  non-overlapping → an inner token contained in a longer one is dropped). **Family patterns (not an
  enumerated list) are load-bearing: a NEW `core_<stat>` field or `Core<Word>` type cannot silently escape.**
- **PRESERVE-list (longest-first anchored, Class-36):** `ExecutionCore`/`ExecutionCore_Tick`/`ExecutionCore_*`,
  `CoreFrameworks`, `MULTICORE`, **`FoxML_Core`** (PRIMARY — naive `Core`→`Node` makes `FoxML_Node`),
  CPU-hardware `core` (`cpu_id`/SMT/"physical core"/"single-thread-per-core").
- **Path exclusions:** `experiments/per_core_sharding/` + the **self-referential set** (`cascade.py` + its test
  fixtures + this spec + `rename-ship-methodology.md` + the rename plan body — they DISCUSS the tokens; sweeping
  them corrupts the apparatus; `rename-ship-methodology.md` Phase-5 self-ref rule).

### Scan surface (the widening = the point)
Engine source + **`tools/**`** + **`build.sh`** + **`.githooks/**`** + the doc trees (`DOCS/`, `DESIGN_SPECS/`,
`plans/_cross-cutting/`, `claude-skills/*/SKILL.md`, root lookup docs).

### Output: classified worklist (Phase-3 buckets) — ENUMERATE-ONLY
CODE-TOKEN (compiler-oracle'd) · TOOL-REGEX (the unique value — compiler-blind) · COMMENT/STRING · STALE-REWRITE
· FILE-PATH (drives the `#include`-cascade) · HISTORICAL-PRESERVE. **Plus:** the `#include`-cascade tooth (6
basename renames → ~27 `#include` + include-guard macros) and the **expected-residual ALLOWLIST** (post-rename
totality = "grep matches the allowlist EXACTLY", never "=0": the `node_id` 3-hit `Run.hpp:202/213` from
`2b8bd6c`, `experiments/`, the self-ref set, history). **Sister-cohort grouping (the a-class/I-1 catch):** the
`FOREACH_PER_CORE_CFG_FIELD` rename surfaces ALL its H15 dependents together (the 10 `MetaRegistry.hpp` rows
incl. the 5 H19 `PARENT_NAME` refs + the `check_per_core_registry_integrity.py` rename) **and** the H21 cohort
(`CORE_STATE_FLAG_*` + `tools/identifier_ledger.txt`) so each cohort moves as one
(`feedback_sister_cohort_amendment_completeness`).

The human then does the rename in ONE mechanical commit (`rename-ship-methodology.md` Phase 4; compiler =
code oracle; `check_doc_rename_classification.py` = the doc sweep, Phase 5). `cascade rename` re-run vs the
allowlist + the `check_` guards green = Phase-6 totality.

## H21 confirmation (gate MED-2 — rename-safe, NOT an epoch)
The `CORE_STATE_FLAG_*` flags persist by **bit VALUE** (the `CoreContext.core_state_flags` uint8 bitmap →
`ShardedSnapshot`), not by NAME (`identifier_ledger.txt:13-18` = `enum:CoreStateFlag|<NAME>|<value>`). Renaming
the C++ SPELLING preserves the value → H21-safe (H21 protects the value/slot, not the identifier). The rename
co-migrates `identifier_ledger.txt` NAMES via `check_identifier_retirement.py --update` (Check H, the
commit-blocker, is the existing H21 guard — already in the §HIGH cohort). Phase-6 grep-verifies no
CoreStateFlag VALUE changed. (If a flag NAME were itself wire-emitted as a string, it WOULD be an epoch — it is
not; verified bit-keyed.)

## Non-vacuity (Class 51 — `rename` proves it bites)
`rename` selftest carries a POSITIVE control: plant a stale `FOREACH_PER_CORE_CFG_FIELD` + a `"core_"` literal
in a temp `tools/`-shaped file → MUST find + classify them TOOL-REGEX (non-empty); a clean tree → exactly the
allowlist (no false positive on `FoxML_Core`/`experiments/`/the `node_id` 3-hit/the self-ref set). Hermetic
temp tree via `FOXML_ENGINE` (`/tmp` noexec — LANDMINE 11; in-repo tmp).

## Integration surface — ALL reference points (the deliverable)

### (A) Where `cascade.py` + the R2 guard-fix get WIRED
| Point | Add | Enforced by |
|---|---|---|
| `DOCS/TOOLS.md` | `cascade.py` row (PLANNED→done at build); SKILL-WIRED/on-demand | `check_tools_inventory.py` (HARD) |
| **`check_tools_inventory.py`** (R2 — the standing fix) | add `build.sh` to the `_referenced()` scan set (`:63-92`) so a renamed tool-file the `build.sh:271` guard references → RED (closes the silent-skip) + its teeth | itself (the inventory guard) |
| `tools/run_all_tests.sh` | `cascade.py --selftest` (HARD; mirrors conformance `:50-51`) | test runner |
| test-harness | `tools/test_cascade.py` (D-137 teeth — non-vacuity) | inventory guard |
| `rename-ship-methodology.md` | a "§ Mechanization" pointer (Phase 2 `rename` enumerate) | sister-ref check |
| `/trace-deps` + `/dependency-chain-trace` SKILLs | name `cascade rename` (TOKEN-blast sibling of `gen_code_map --composition` TYPE-blast, step 7) | nav-infra cohort guard |
| DESIGN_SPECS README/TAG_INDEX | auto-add this spec's row | `rebuild_doc_indexes.py --check` (HARD) |
| **(NOT) a `cascade audit` subcommand / check_session_docs / pre-commit Check letter** | — R2 dropped it; standing coverage rides `check_tools_inventory` (existing harness) | (the R2 rationale) |

### (B) The TOOL-REGEX co-migration cohort `cascade rename` SCANS (I-1-verified `b9ce419`; RE-DERIVE at run)
`check_per_core_registry_integrity.py:163,220` (**rename file→`check_per_node_…` + body + all refs** — HIGH) ·
`check_identifier_retirement.py:79-80`+`identifier_ledger.txt:13-18` (`CORE_STATE_FLAG_*`, **Check H
commit-blocker**; co-migrate via `--update`) · `build.sh:271` (`[ -f …]` silent-skip — the R2 fix guards this) ·
`scan_class_27_full.py:272` · `scan_class_44_cfg_orphan.py` · `check_doc_rename_classification.py` (KEEP_TOKENS)
· `check_meta_registry.py` · `check_storage_t_coverage.py:39`/`check_field_name_uniqueness.py:39-41`/
`check_struct_field_uniqueness.py:49`/`check_struct_size_budget.py:69` (`tt::CoreLatencyStats` type-row) ·
`check_plan_body_symbol_existence.py:86-87,121` (Check A) · `tools/lib/sharded_files.txt` + `*_baseline.txt` +
`locale_determinism_known_pending.txt:18` data lists · `validate_feature_mask.sh:125`.

> **Honest-scope ceiling (gate MED-1, Class-51):** the DATA-file / type-row staleness above (`identifier_ledger.txt`
> rows, `check_struct_size_budget.py:69` type-row, `check_plan_body_symbol_existence.py` map) is the LARGEST
> silent surface. `cascade rename` ENUMERATES + co-migrates it (it's in this cohort) — so the rename SHIP is
> safe. The STANDING net (the R2 `check_tools_inventory` fix) does NOT re-verify it; nor does the deferred
> apparatus→dead-`FOREACH` generalization fully. State this so a future "standing-net green" is never read as
> "apparatus is rename-clean." The full close is the noted-future generalization.

## Noted future increments (homed, NOT built — the R1/R2 deferrals)
- **`cascade rename --apply`** (R1): mechanical substitution over apparatus only, hard-gated on the `check_`
  guards RED→GREEN per substitution + the Class-36 overlap-resolution EXTRACTED to `tools/lib/` (shared with
  `check_doc_rename_classification.py`). Build only if hand co-migration recurs/proves error-prone. NOT for
  code (the compiler is the oracle).
- **The broader apparatus-currency standing guard** (R2): apparatus ref → dead `FOREACH_<NAME>` (composing
  `check_meta_registry.scan_codebase_foreach_macros()`) + DATA-file/type-row staleness. Closes the MED-1
  ceiling. Build when a 2nd rename needs it (M7 recurrence), not speculatively.

## Build sequencing + the E.1.1 ↔ E.1.2 seam
1. Build `cascade.py rename` (enumerate-only) on the `check_struct_alignment.py` substrate IDIOM + `--selftest`
   non-vacuity teeth. Enroll `DOCS/TOOLS.md`; wire `--selftest` into `run_all_tests.sh`.
2. Build the R2 `check_tools_inventory.py` `build.sh`-scan extension + its teeth.
3. RUN `cascade rename` → freeze the worklist into `plan_checks/` verbatim (Phase 2).
4. Human executes the rename (ONE code commit, compiler oracle, Phase 4; docs via `check_doc_rename_classification.py`
   Phase 5) → `cascade rename` vs allowlist + the `check_` guards green (Phase 6).
5. **OUTBOUND → `.E.1.2`:** the `struct <T>` subcommand (TD-175 AST Tool A, re-cut) slots into the SAME tool —
   zero CLI churn for `rename` (the reserved-slot payoff).

## Ledger (TD-175 split — `.E.1.1`)
Realizes **TECH_DEBT-175a** (`cascade rename` enumerator + the R2 `check_tools_inventory` `build.sh` fix),
closing at `.E.1.1` when both land teeth-proven. **TECH_DEBT-175 remainder** = the AST `struct` cascade (Tool A,
re-cut) → `.E.1.2`.

## Cross-references
[[rename-ship-methodology.md]] (the discipline this mechanizes — Phase 2 enumerate) · [[struct-change-cascade-impact-tooling.md]]
(the `struct` subcommand's design — re-cut) · [[canonical-sister-extension-discipline.md]] · RBP Class 36 / 51 /
33 · D-239 (the dive) + D-240 (this tool design + the gate refinement) · `check_tools_inventory.py` (the R2
standing-fix home) + `check_meta_registry.py` (the future-generalization's enumeration source) +
`check_identifier_retirement.py` (the H21 Check-H cohort) + `check_struct_alignment.py` (substrate idiom) +
`check_doc_rename_classification.py` (doc-side executor) · `feedback_enumerate_consumers_before_registry_row_deletion`
· `feedback_paste_tool_output_dont_summarize` · `feedback_framework_layer_payoff_diminishing_returns` (the R2
defer rationale) · TECH_DEBT-175a (home) + TECH_DEBT-175 (remainder → E.1.2).
