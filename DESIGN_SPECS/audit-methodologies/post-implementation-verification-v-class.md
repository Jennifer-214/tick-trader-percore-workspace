---
type: audit-methodology
stage: 2-draft
version: 1.1
established: 2026-06-15
tags: [audit-methodology, verification, sanitizers, definition-of-done, post-coding, meta-discipline]
surface: [post-implementation, pre-commit, ship-close]
sister_specs: [adversarial-multi-agent-audit-methodology.md, audit-driven-pre-coding-gate.md, definition-of-done-and-armed-scout-verification.md]
sister_memories: [feedback_v_class_post_implementation_verification.md, feedback_run_dedicated_audit_skills_not_just_armed_prompts.md, feedback_define_done_and_arm_scout_subagents.md, feedback_adversarial_framing_default_for_checks.md]
applies_at_skills: [/post-ship-audit, /ship, /verify-implementation]
---

# Post-implementation verification — the V-class

**Established:** 2026-06-15 (operator-surfaced at the A6 corrupt-model ingress: *"we should make a V-class agent as a 'verification post-implementation' using the appropriate skills... is it a good idea or just ceremony?"*). It is a good idea — at A6 it caught a pre-existing latent heap-use-after-free (TECH_DEBT-202) the normal suite missed. First canonical application: the A6 INGRESS (`.E.0.10`, this session).
**Status:** Stage 2 DRAFT — first canonical application noted (A6); promotes to Stage 3 at the 2nd application + when the `/verify-implementation` skill (or `/post-ship-audit` pre-commit mode) is built (the still-open codification, TaskList #16 at `.E.0.10`).

---

## The principle — the missing third leg of the fan-out

The pre-coding adversarial gate has two classes (`adversarial-multi-agent-audit-methodology.md` + `feedback_a_class_i_class_fanout_vocab`):

- **I-class** (INVESTIGATIVE) — maps the surface / write-set / blast-radius BEFORE coding.
- **A-class** (ADVERSARIAL) — tries to REFUTE the design BEFORE coding (default-refuted).

Both run on the DESIGN. Nothing structurally runs on the *shipped code* between "the design was blessed" and "commit." The **V-class** is that third leg — a single **post-implementation** verification pass:

```
I-class → A-class → [build the code] → V-class → commit
  (design)  (design)                    (CODE)
```

The V-class answers a question I/A cannot: **"does the CODE that landed actually match the design the pre-coding audits blessed — and does it survive the gates that only run on built artifacts (sanitizers, codegen, hot-path-diff)?"** A design audit cannot catch a use-after-free, a codegen regression, or a hot-path call-graph change — those exist only once the code is built. The V-class is where they get caught, per-implementation, instead of leaking to the ship-close gate (or production).

---

## The V-class checklist (what the single pass RUNS)

The V-class RUNS the gates + the dedicated skills on the SHIPPED code — it does not approximate them with an armed prompt (`feedback_run_dedicated_audit_skills_not_just_armed_prompts`). Concretely:

1. **Build** — every touched target (`./build.sh test` + `gui` + `suite` as the surface touches them); char-tests GREEN.
2. **Sanitizers — asan + ubsan, as a PER-IMPLEMENTATION pass, NOT deferred to ship-close, built FRESH from current source.** This is the load-bearing rule. It is the gate most likely to be skipped (it is slower + "the suite already passed") and the one most likely to catch a latent memory-safety or UB bug. Running it per-implementation is the entire point: `tools/run_all_tests.sh --full` (or `./build.sh asan` + `ubsan`). **FRESHNESS IS LOAD-BEARING (v1.1):** the instrumented binary MUST be (re)built from CURRENT source before the run — a stale `build_asan/` reports on code it never compiled, lying in BOTH directions (false-green on an unfixed bug; false-RED on a fixed one). `run_sanitizer_suite.sh` now rebuilds each lane first (`.E.0.10` anti-stale gate, guarded on `build.sh` presence so the hermetic self-test still runs its stubs). A sanitizer verdict from a binary nothing guaranteed-fresh is NOT verification (sibling of `feedback_passing_test_is_not_verification`).
3. **Hot-path untouched** — `tools/calls_graph_diff.sh verify` (the hot path's call graph is unchanged unless the ship deliberately touched it; H7/H8).
4. **Doc-CI** — `tools/check_session_docs.sh` (the mechanical doc/plan floor: citations, index-currency, singleton, memory bidirectionality).
5. **Surface-matched DOMAIN audits on the SHIPPED code** — route by the material (per `/decision-check` Stage 2.5): money → `/accounting-audit`; hot/slow/branchless/cache → `/hft-audit`; cfg/registry → `/dod-audit` + `/trace-deps`; ML/model/stamp → `/ml-audit`; train↔serve → `/parity-check`. These verify the CODE matches the blessed design — not that the design was right (the pre-coding gate did that), but that the implementation didn't drift from it.

The V-class returns an **M8 Definition-of-Done verdict** (`definition-of-done-and-armed-scout-verification.md`): code+producer / test-per-fix / sanitizers / hot-path / parity / promises-honored / docs-indexed / meta-codified. A ship TERMINATES only when that DoD is verified — the V-class IS that verification, applied per-implementation rather than only at ship-close.

---

## Why it is NOT ceremony — the A6 worked proof

The doubt the operator named ("good idea or just ceremony?") is the right question to ask of any new process gate. The answer at A6 is concrete: the asan leg of what-would-have-been-the-V-class surfaced a **heap-use-after-free** (`OrderEventLog_AsyncWriterRoutine` pops its SPSC ring after `delete oms`; TECH_DEBT-202 — corrected root cause: the join is not *missing*, it is *defeated* — the test's double-`Init` re-inits the ring + clobbers `writer_thread_active` while the writer runs → the guarded `Free` join no-ops → free-under-live-writer; RBP Class 50). Properties of that catch:

- The **normal suite passed** — the freed memory wasn't reused hard enough to trip an assertion. Only asan caught it.
- The bug was **pre-existing (Ship-B vintage)**, latent for multiple ships, because **asan is a ship-close gate, not per-commit**. A per-implementation V-class would have surfaced it at the Ship-B implementation, not many ships later.
- It is now a **`.E.0.10` ship-close blocker** — exactly the kind of cost that compounds when a memory-safety bug rides un-caught across ships.

So the V-class is not ceremony: it is the per-implementation application of a gate that was previously only end-of-ship, and it has already paid for itself once.

---

## The M7 framing — make it a pass, not a habit

Before this codification, "run the sanitizers + the domain audits on the shipped code" was AD-HOC — it depended on the implementer remembering to do it. That is the precise shape `structural-enforcement-when-memory-insufficient.md` (M7) addresses: a discipline that depends on memory recurs as a miss. The fix is to make it a **pass** (a named, routinely-fired verification step) rather than a **habit** (an intention that competes with shipping pressure). The skill codification (`/verify-implementation`, or `/post-ship-audit` extended to a PRE-commit mode) is the structural form; until it lands, this spec + the memory are the codified intent.

### The V-class's own inputs must be fresh (v1.1 — the `.E.0.10` dogfood catch)

Dogfooding the V-class on TECH_DEBT-202's OWN fix exposed a second-order trap: the asan leg ran a **prior-session `build_asan/`** (`run_all_tests --full` → `run_sanitizer_suite.sh` only *ran* the binary; nothing in the `--full` path rebuilt it), and reported the UAF the fix had **already closed** — the abort cited a pre-edit line number, the tell. A verification gate that runs a pre-built binary is only as fresh as whoever last built it; it can lie in BOTH directions. **Structural fix:** `run_sanitizer_suite.sh` now rebuilds each lane from current source before running (incremental; guarded on `build.sh` presence so the hermetic self-test still runs its stubs). This is itself an instance of the V-class principle — *the gate verifies the SHIPPED code, so its inputs (the instrumented binaries) must BE the shipped code, freshly compiled.* It is the `.E.0.6` "clean-rebuild-unmasks-stale-cache" lesson, now enforced at the sanitizer gate rather than relied upon as discipline.

---

## Relationship to the sister methodologies

| Sister | Layer | How the V-class relates |
|---|---|---|
| `adversarial-multi-agent-audit-methodology.md` (A-class) | PRE-coding, design | The V-class is its post-coding complement — A refutes the design, V verifies the code matches the blessed design + survives the build-only gates. Same fan-out, third leg. |
| `audit-driven-pre-coding-gate.md` | PRE-coding, design | The gate fires I+A before coding; the V-class fires after. Bookends. |
| `definition-of-done-and-armed-scout-verification.md` (M8) | Close-out | The V-class IS M8's verification, applied per-implementation (pre-commit) rather than only at ship-close. M8 is the verdict shape; the V-class is the routine that produces it per-ship-of-code. The two should cross-reference. |
| `feedback_run_dedicated_audit_skills_not_just_armed_prompts` | Discipline | The V-class RUNS the dedicated skills (the checklist is a checklist; an armed prompt is a hint). |
| `/post-ship-audit` | Post-ship | The retrospective sibling. The V-class is its PRE-commit counterpart — catch it before it lands, not after. |
| `/ship` | Close ritual | The V-class runs BEFORE `/ship`'s commit, so `/ship` commits verified code. |

---

## Open codification (the still-pending skill)

The methodology exists (this spec + the memory). The SKILL that mechanizes it is TaskList #16 at `.E.0.10`:

- Build `/verify-implementation` (OR extend `/post-ship-audit` to a PRE-commit mode) that composes the checklist above into one pass + returns the M8 DoD verdict.
- Add **V** to the I-class/A-class fan-out vocabulary memory (`feedback_a_class_i_class_fanout_vocab`): I → A → build → V.
- When the skill lands, this spec promotes Stage 2 → Stage 3 (first canonical = A6; the skill is the mechanization).

---

## Cross-references

- Sister memory: `feedback_v_class_post_implementation_verification.md` (the operator-collaboration trigger; this spec is the methodology body).
- Sister methodology: `adversarial-multi-agent-audit-methodology.md` (the A-class the V-class complements) + `audit-driven-pre-coding-gate.md` (the pre-coding bookend).
- Parent verdict shape: `definition-of-done-and-armed-scout-verification.md` (M8 — the DoD the V-class produces).
- Discipline it enforces: `feedback_run_dedicated_audit_skills_not_just_armed_prompts` (RUN the skills) + `feedback_adversarial_framing_default_for_checks` (the verification is adversarial by default).
- Worked-proof artifact: TECH_DEBT-202 (the OMS async-writer UAF the A6 asan leg caught) + the `.E.1`-foundation plan's OrderEvent-lifecycle fold.
- Lifecycle: `pattern-codification-lifecycle.md` (Stage 2 DRAFT → Stage 3 at the skill + 2nd application).

---

**End of post-implementation-verification-v-class v1.1 STAGE 2 DRAFT.** First canonical application: A6 INGRESS `.E.0.10` (the TECH_DEBT-202 catch). v1.1 (`.E.0.10`): sanitizer-freshness made load-bearing + the corrected TD-202 root cause + the stale-`build_asan` dogfood catch (`run_sanitizer_suite.sh` now rebuilds first). Stage 3 at the `/verify-implementation` skill landing + the 2nd application.
