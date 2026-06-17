---
type: audit-methodology
stage: 3-first-canonical
version: 1.0
established: 2026-06-16
tags: [audit-methodology, latency-discipline, branchless-discipline, structural-fix, determinism]
surface: [hot-path, slow-path, ml-inference, ci-tooling]
sister_specs:
  - meta-disciplines/mechanical-verification-of-derived-code-facts.md
  - refactor-patterns/branchless-dispatch-discipline.md
  - refactor-patterns/critical-moment-determinism-over-average-latency.md
sister_docs:
  - DOCS/RECURRING_BUG_PATTERNS.md  # Class 51 (vacuously-green guard) — the tool's non-vacuity self-defense is its first canonical
applies_at_skills: []
applications:
  - 'the 7-row .E.1.0 manifest: ExecutionCore_Tick (hot) + RollingStats_Push + regime/confidence/ridge feature kernels (slow)'
  - 'D-235 ML-degrade label-vacuity caught at DESIGN time (assert the FLAGS, never the strategy_id label)'
  - 'the H7/H20 branchless meter: data-dependent-warm branch count → 0 (subsumes the undecidable grep)'
---

# Static latency-path conformance analysis (instruction-budget from ASM, not wall-clock-ns)

## The problem this solves

**Latency is a derived code-fact** (per `mechanical-verification-of-derived-code-facts.md`) — but unlike struct SIZE (one `sizeof`), a wall-clock-ns latency number is **non-deterministic** (box, thermals, neighbours, frequency scaling) and **not CI-reproducible**, so it can neither gate a commit nor diff cleanly across runs. A runtime latency bench therefore can't be the standing guard for H8 (hot p99 ≤500ns / slow ≤100µs): it measures a moving target, and on a determinism-prioritizing system (the HFT premise) the **variance** is the cost that matters more than the mean (see `critical-moment-determinism-over-average-latency.md` — jitter-where-it-matters).

**The reshape (D-233/D-234):** gate a **STATIC instruction-budget proxy disassembled from the PRODUCTION binary**, not a wall-clock measurement. Instruction count + branch classification are deterministic functions of the compiled code — diffable, gating, zero engine behavior. The true wall-clock + cache-miss confirmation remains a *deferred* dynamic PMU step (the two-layer design); the static layer is the standing CI gate.

This is the **latency arm** of the derived-fact-budget-gate family — sister to `check_struct_size_budget.py` (the SIZE arm). Both mechanize a hand-commented fact into a guard; both are the M7 close of "convention proved insufficient."

## What it gates (from the ASM of each manifest kernel)

| Gate | Invariant | Mechanism |
|---|---|---|
| instruction-count budget | H8 (proxy for the latency budget) | count mnemonics in the kernel's real body; grandfathered baseline + no-new-regression ratchet |
| **branch-classification** `{loop / rare-cold / data-dependent-warm}` | **H7/H20** (the branchless meter) | classify each branch; **drive the data-dependent-warm count → 0** (D-235) — SUBSUMES the H7/H20 grep, which was undecidable on source |
| no scalar float (incl. AVX/FMA) | H4 (Money/FPN, never float on money paths) | detect `*sd`/`*ss`/`vfmadd*`/`cvt*` outside the sanctioned feature seams |
| no div | § 5 (determinism / latency) | detect integer `idiv` / `div` |
| no malloc / lock / stdio / throw | H1 / Rule 2 | detect `call` to the forbidden externs (`objdump -r` for the reloc names) |
| no indirect / vtable | H2 | detect `call *` / `jmp *` (indirect, non-jump-table) |
| **no un-analyzed warm work** | the non-vacuity floor | transitive recurse into same-TU callees; **fail LOUD** on a warm call to a body not in the `.o` + not a sanctioned extern |

## The design lessons (the load-bearing content — author a sister gate from THESE)

### 1. Kernel-granularity — gate the bounded LEAVES, never the ORCHESTRATOR (D-238)

A single-TU probe over an **orchestrator** (`EventLoop_RebuildOneCore`) over-inlines the *entire* pipeline — incl. cold persistence, logging, boot paths — into one body → a signal **flood** (~190 findings, mostly cold-reachable). **Gate the bounded per-cycle KERNELS instead** (`ExecutionCore_Tick`; `RollingStats_Push`; the regime / confidence / ridge feature kernels). The discriminator: a **kernel** has a bounded, characterizable per-cycle cost; an **orchestrator**'s body is the *union of everything it calls* and is not a meaningful latency unit. Orchestrators carry an in-tool NOTE explaining why they are not rows — the omission is documented, not silent (else it reads as covered).

### 2. Probe-wrapper disassembly for always-inline templates

The hot/slow kernels are `always_inline` templates with no out-of-line symbol. The tool compiles a **probe TU** that forces one instantiation under the **PRODUCTION flags** (`-O3 -march=native`, *no* `LATENCY_PROFILING`, *no* `USE_XGBOOST`), then disassembles the probe's body. Build in an **in-repo tmp dir** (`/tmp` is `noexec` — a standing LANDMINE). `FOXML_ENGINE` overrides the root.

### 3. Source-keyed exemptions single-sourced to the engine's H4-sanctioned seams (D-237)

The feature domain legitimately uses libm transcendentals + money↔feature conversions — H4 sanctions them at named seams. Exempt them **WITHOUT widening the gate**:
- a per-manifest-row source-keyed **`allow`** list — **file-level** for a pure-feature file, **`file:line`** for a mixed file (`FixedPointN.hpp` carries both money and feature ops);
- a **`FEATURE_MATH_EXTERN`** name-whitelist (the libm `sqrt`/`exp`/`pow`/`log`/… + double `min`/`max`/`round` + the int128↔double conversions) — the out-of-line form of the already-source-allowed inlined `vsqrtsd`.
- **CRITICAL — forbidden-calls exempt by `file:line`-ONLY, never file-level.** A file-level `allow` meant for the float/div feature-seam must NOT wave through a `malloc`/stdio on that file (Class-51 mode D — caught by the final verification pass). The exemptions are rationale-carrying + drift-self-surfacing (a row whose allow no longer matches the source fails loud).

### 4. Transitive STRUCTURAL scan, fail-loud — not positional (the cold-quartile fix)

A warm `call` into a same-TU body must be **recursed into** (bounded `MAX_FOLLOW_DEPTH`), not waved past. The recurse/fail decision is **STRUCTURAL** (a defined callee → recurse; a sanctioned extern → allow; anything else → `unanalyzed_warm`, fail LOUD), **never positional**. A `lo + 0.75·span` "this call is in the cold quartile" heuristic mis-classified a compute-then-delegate kernel's FINAL (delegating) call as cold → skipped the hazard → a false-green (Class-51 mode B″).

### 5. The tool asserts its OWN non-vacuity (Class-51 first canonical)

A guard that disassembles a symbol the optimizer **eliminated** would "pass" a budget over an empty body — the vacuously-green guard (`Class 51`). The tool **refuses to grade a body it cannot prove it found**: it resolves the kernel's real out-of-line body by length-prefixed mangled name (incl. `.isra`/`.constprop` clones), picks the **largest non-vacuous** match, and **fails LOUD** if none exists (it proved this on itself — it refused `RollingStats_Push`'s optimized-to-2-instruction wrapper until the body-symbol follow landed). Corollaries the build learned:
- **single-source the gate** — `_hard_findings` is the ONE pass/fail decision, so a detected-but-un-gated finding is structurally impossible (the **decorative div-gate**, Class-51 mode B′: `idiv` was detected + printed + teethed, but `main` never gated on it → exited "clean"). Teeth assert the **GATE**, not a count.
- **teeth carry a POSITIVE control**, not only a negative — `--selftest` must prove the check RAN on the real target + greens only when the property holds, not merely that it CAN go red.

## Why this is verified by INDEPENDENT review, not the builder's dogfood (AR-8)

The **builder of a guard is MODEL-BOUNDED** — they cannot write a non-vacuity self-check for a vacuity mode they never imagined. So a guard's own dogfood + teeth are *necessary but not sufficient*: the conformance analyzer declared itself "clean" at every build round, yet **5 independent adversarial passes** each surfaced a load-bearing hole the teeth had greened — the AVX/FMA `vfmadd` blindness, the forbidden-call-blind-to-external-syms, a `jmp*`-tail-call detector that false-flagged GCC switch-tables (reverted → `call *`-only), the decorative div-gate, the cold-quartile false-green, the forbidden-file-level exemption. This is the canonical instance of **AR-8** (self-attested verification) and the reason **TECH_DEBT-207** escalates independent-review-by-default to mid-session tool/code builds. **A guard that codifies against a bug class is itself the highest-risk surface for that bug class** — verify it adversarially, not by its own green.

## Coverage boundaries (named, not silent — per the no-silent-caps discipline)

In-tool NOTE comments record what is deliberately NOT a manifest row:
- `EventLoop_RebuildOneCore` — orchestrator (lesson 1).
- `Model_Predict*` — an XGBoost external-API stub (~39 instr); not statically analyzable → the coverage gap is homed (TECH_DEBT-206), not hidden.
- `OnlineCycleStep` — a `.text.unlikely` tail-jmp shape the current scanner can't follow (tail-call look-back is future work).

## Wiring + closure (the standing net)

- **pre-commit Check N** (trigger-scoped to the manifest's source files + the tool + the baseline; `SKIP_LATENCY_CONFORMANCE_CHECK` bypass + a re-baseline hint).
- **`run_all_tests.sh`** — the gate + `--selftest` teeth, both HARD.
- **grandfathered baseline** at `tools/lib/latency_path_budgets.json` (per-kernel `instructions` + `data_dependent`); `--update-budgets` re-baselines under a pinned toolchain + tolerance. E.1.0 grandfathers the current counts as a no-new-regression floor; the **reduction** (driving data-dependent-warm → 0) is the optimization leaf (D-236), not this ship.
- enrolled in `DOCS/TOOLS.md`; mechanizes `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` + the hot/slow invariants.

## Future expansion (build-when-earned, not speculative)

- **The dynamic PMU arm** — `perf stat -e branch-misses,L1-dcache-load-misses` confirms the allowlisted branches mispredict ~0% + the working set is L1d-resident. The static layer FLAGS; the dynamic layer is the VERDICT for the un-static-decidable part (mirrors the SIZE arm's static-budget-flags / perf-counter-decides split in `mechanical-verification-of-derived-code-facts.md`).
- **Tail-call look-back** — follow a `.text.unlikely` tail-`jmp` to its target (closes the `OnlineCycleStep` gap) without re-introducing the switch-table false-positive that got the naive `jmp*` detector reverted.

## Pattern lifecycle

- **Stage 1 (problem):** H8 needed a guard; a runtime bench is non-deterministic + non-CI-able (D-232 hardened re-pass found the substrate vacuous).
- **Stage 2 (draft):** the static-conformance reshape (D-233/D-234).
- **Stage 3 (first canonical):** THIS SHIP (.E.1.0) — the 7-row manifest, exit 0, CI-wired + baselined, 5-pass adversarially verified; first canonical of the Class-51 non-vacuity-self-defense discipline.
- **Stage 4 (cohort):** a 2nd derived-fact gate adopting the non-vacuity + source-allow + named-coverage-boundary pattern (the SIZE arm `check_struct_size_budget.py` is the sibling already).
- **Stage 5 (CLAUDE.md):** candidate once the dynamic PMU arm lands + the data-dependent-warm reduction completes.
