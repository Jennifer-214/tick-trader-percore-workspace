---
type: meta-discipline
stage: 3-first-canonical
established: 2026-07-17
tags: [audit-methodology, verification, structural-enforcement, test-infrastructure, doc-discipline]
surface: [ci-tooling, test-infrastructure]
sister_specs: [meta-disciplines/mechanical-verification-of-derived-code-facts.md, audit-methodologies/static-latency-path-conformance-analysis.md, meta-disciplines/structural-enforcement-when-memory-insufficient.md, meta-disciplines/differential-to-absolute-gate-contract-widening.md, meta-disciplines/advertised-capability-never-exercised.md]
sister_docs:
  - DOCS/RECURRING_BUG_PATTERNS.md   # Class 51 (vacuously-green guard) — the anti-pattern this discipline prevents
  - tools/goldens/README.md          # the golden / exception-baseline / ratchet / rules taxonomy, at the point of confusion (D-395: enrolled here rather than re-minted as a spec)
applications:
  - 'check_conversion_completeness.py --selftest — synthetic DemoLumped6 (a 6-field struct lumped in a [FUNCTION] block) is FLAGGED; an ExecutionCore-shaped complete fixture scans CLEAN (E.1.2.A, D-362 first application)'
  - 'check_latency_path_conformance.py — 15 --selftest teeth; asserts its own non-vacuity by refusing a RollingStats wrapper optimized to 2 instr (Class 51 first canonical)'
  - 'check_code_tag_blocks.py --selftest — present-vs-absent per [REFERENCE] subcat (11 -> 20 checks)'
  - 'check_corpus_membership.py --selftest — planted ADD / DELETE / count-unchanged RENAME / REORDER each FLAGGED, absent golden is a HARD failure, and the git-tracked PIN filter proven non-trivial (E.1.2.B 0.2; the blessed-output first canonical)'
  - 'bless.py --selftest — all three refusal paths proven (non-TTY drift, non-TTY create, no bypass parameter) plus no-op-does-not-write (D-394/D-369)'
  - 'check_identifier_retirement_selftest.sh — every plant ASSERTED after its version-decrease tooth was found DEAD (a stale hardcoded anchor made the sed a no-op, so the case proved nothing); now value-derived and wired into check_session_docs (E.1.2.B 0.2)'
---

# Calibration corpus — every guard asserts its own non-vacuity against {golden-COMPLETE x golden-BROKEN}

**Established:** 2026-07-17 (decision-log D-362; E.1.2.A completeness-gate ship). Generalizes the ad-hoc `--selftest` into a systematic, co-evolving FIXTURE SET — the POSITIVE discipline that prevents **Class 51 (the vacuously-green guard)**.

## The pattern

A guard-tool (a CI checker, a validator, a coverage gate, a conformance analyzer) that cannot FAIL on a planted defect is **vacuously green** — it passes not because the code is clean but because the guard is blind. The base fix is a `--selftest` that PROVES the guard fires. Made SYSTEMATIC: every guard asserts its non-vacuity against a shared, co-evolving **calibration corpus** —

- **golden-COMPLETE fixtures** — a correct, fully-conforming exemplar (ExecutionCore-shaped) that MUST scan **CLEAN**. Catches the INVERSE failure — a guard that cries wolf on correct code (the false-RED; see `mechanical-verification-of-derived-code-facts.md` § INVERSE, where `check_struct_size_budget.py` false-RED'd the cache-disciplined `ExecutionCore`).
- **golden-BROKEN fixtures** — one MINIMAL synthetic per error class, each of which MUST be **FLAGGED**. A guard that passes a known-broken fixture has a blind spot, caught immediately.

Every tag-tool's `--selftest` asserts against BOTH halves: passes every known-complete, flags every known-broken.

## Fixtures are SYNTHETIC / frozen — never a live file

A **live** broken file gets FIXED and stops being broken — so a selftest anchored to it silently goes vacuous the moment the file is cleaned. Not hypothetical: the completeness `--selftest` originally flagged the real `GateControlNetwork.hpp` half-conversion; when Phase-C CONVERTED GCN, that anchor would have gone green-for-the-wrong-reason, so it was swapped for a SYNTHETIC `DemoLumped6` (a 6-field struct lumped in a `[FUNCTION]` block — corpus-independent by construction). **Rule: the standing calibration fixtures are synthetic/frozen copies, never live corpus files.** The live half-conversions are calibration INPUTS during a cleanup (they exist, broken, now) but never the standing corpus.

## The corpus GROWS with the discovered error taxonomy

Each new error class the operator or an audit surfaces -> a new synthetic BROKEN fixture + a tool check that flags it + a `--selftest` row that asserts it. This is how the guards stay calibrated to catch OTHER errors, not just the already-known ones — the corpus is the institutional memory of "every way this has been seen to break." A guard is only as trustworthy as the breadth of broken fixtures it has proven it flags.

## Writer/transform tools additionally assert IDEMPOTENCY + ROUND-TRIP

A guard READS; a WRITER (`--fix` / `--apply` / `update` / a scaffold-generator) MUTATES. A writer's `--selftest` asserts the two non-vacuity halves above (golden-COMPLETE stays clean, golden-BROKEN is flagged) PLUS two writer-specific properties, because a writer has failure modes a read-only guard can't have:

- **Idempotency** — running the writer TWICE on its own output is a NO-OP (0 changes / byte-identical). A writer that INSERTS or APPENDS without a present-check double-writes on re-run (a `[SIZE]` tag twice; the FPN `--apply` → `FPN_Binary_Binary`) — invisible to a one-pass selftest, but it bites the moment the writer is re-fired by standing CI or a **pre-commit auto-`--fix`** (exactly the 1:1-auto-sync use, D-365). See `DOCS/RECURRING_BUG_PATTERNS.md` **Class 56**.
- **Round-trip** — the writer's OUTPUT re-parses CLEAN through the VALIDATOR (the one-producer-N-consumers gate). A writer that emits malformed grammar silently poisons every downstream consumer (CI gate + plugin + doc-viewer); assert it by running the validator (`check_code_tag_blocks.validate_file`) on the writer's output inside the selftest, not just eyeballing it.

**First canonical:** `check_cache_layout.py --selftest` (E.1.2.A) — the `refresh_derived` present-or-insert asserts {REWRITE · INSERT · **IDEMPOTENT** (2nd `--fix` = 0) · COVERAGE-BOUND (un-probed struct untouched, D-363) · **ROUND-TRIP** (output re-parses through `check_code_tag_blocks`)}. This idempotency proof is the **precondition** for wiring a writer into a pre-commit auto-`--fix`: you cannot safely auto-run a writer in CI until it is provably a no-op on unchanged input.

## Blessed OUTPUT goldens — the lifecycle (added 2026-07-20; D-386/D-394/D-395/D-396)

An **output golden** pins what a producer EMITS for a fixed input, so a change in output REDs. It belongs in this discipline rather than a spec of its own (D-395: `tools/goldens/README.md` already holds the taxonomy — enrolled here as its canonical reference rather than re-derived).

**(1) Know which of the four artifacts you are holding.** They answer different questions and conflating them is how a gate quietly stops meaning anything:

| Artifact | Question | Lifecycle |
|---|---|---|
| **golden** (`tools/goldens/*`) | *is the output still what we blessed?* | changes only by an explicit `--bless` that SHOWS the diff |
| exception baseline (`tools/lib/*_baseline.txt`) | *which known-bad findings are tolerated?* | **shrinks** toward zero |
| ratchet (`latency_path_budgets.json`) | *has this metric regressed past its ceiling?* | monotone; re-baselined deliberately |
| rules (`*.json` contracts, schemas) | *what ARE the rules?* | edited when the rule changes |

> An exception list grandfathers things that are **wrong**; a golden pins something that is **right**.

**(2) Who may re-bless — a TTY, and nothing else (D-394).** Re-blessing REQUIRES an interactive terminal, SHOWS the per-file diff together with what the record currently holds and how many entries would be REMOVED, and demands a typed confirmation. Non-interactive **hard-refuses rc=2** — it fails fast rather than blocking on stdin, so it cannot wedge a pipeline. **No `--yes`/`--force`.** The property this buys is the one that makes a golden a TOTAL acceptance oracle at all (M10): a delegated agent is structurally *incapable* of blessing one. The moment an agent can re-bless on red, the golden matches by construction and asserts nothing — Class 51, planted in the guard layer itself. **Route every golden through ONE shared bless helper** (`tools/bless.py`): two goldens with hand-rolled re-bless paths WILL drift into opposite postures, which is exactly what TECH_DEBT-255 recorded before the H21 identifier ledger was migrated onto the shared path.

**(3) A no-op must not write (D-369).** Re-blessing an unchanged golden leaves the file byte-identical. Check this BEFORE the TTY gate: an unchanged golden needs no human decision, so refusal is for MUTATION, not for a null act — and any "run the producer, expect 0-diff" currency check depends on it.

**(4) Bind the golden to its RULES epoch.** A golden is downstream of a contract; when the RULES change, a re-bless is legitimate, and when only the CONTENT drifts it may not be. Carry a `contract_version` and trip a tripwire on a rules change so the two cases are distinguishable rather than both arriving as an undifferentiated diff. Reuse the `[ASSERT]_[EPOCH_TRIPWIRE]` shape (`in-code-documentation-schema.md`; `MONEY_ENCODING_EPOCH` at `FixedPointN.hpp`) — **cross-reference it, do not re-derive it.**

**(5) Pin a LIST, never a COUNT — and pin the DISTRIBUTED population.** Measured from this repo: commit `1da1c1c` moved SIX files' identities with the tracked count going 167 → 167, **delta ZERO**. A count pin is structurally blind to renames and to any swap. And a golden is a COMMITTED, DISTRIBUTED artifact, so it must pin only what resolves identically on a fresh clone: the first corpus golden pinned 31 untracked entries including two **mkstemp random-named** scratch files, and a fresh clone diverged 31 lines unconditionally (**D-396** — SCAN population ≠ PIN population; the enumerator stays gitignore-blind, the pin does not).

**(6) The golden's own non-vacuity.** Everything above still owes the two halves at the top of this spec. A membership golden's `--selftest` must prove a planted ADD, a planted DELETE, a **count-unchanged RENAME** (the defect a count-pin misses), and a REORDER are each FLAGGED, and that an ABSENT golden is a HARD failure rather than a pass. *Absence-passes-silently is Class 51 planted in the guard layer.* **The tooth needs a tooth:** the first gitignore-non-vacuity fixture written for `check_conversion_completeness` used a FILE-level ignore, which ripgrep does not skip — so it would have passed against the very enumerator it existed to catch. Rewritten directory-level and verified discriminating (rg sees 0, the contract walk sees 1). A negative test is only worth what its own negative case proves.

## Home + shared SSoT

`tests/schema_golden/` holds the golden-COMPLETE dogfood corpus; a sister golden-BROKEN set + a shared `calibration_fixtures.py` that EVERY tool's `--selftest` imports is the single source (so a new fixture is added once and every guard's selftest sees it — one-fixture-set, N guards; the `doc-intelligence-toolchain-architecture` "one core, N consumers" thesis applied to the test layer). *(Status 2026-07-17: the shared importer is Phase-C+ work; the completeness gate's in-line synthetic `DemoLumped6` is the proto-application, D-362.)*

## Sister disciplines

- `mechanical-verification-of-derived-code-facts.md` — the derived-fact guards (size/cache/latency/codegen) are exactly the tools this discipline calibrates; its § INVERSE (false-RED) IS the golden-COMPLETE half.
- **Class 51** (`DOCS/RECURRING_BUG_PATTERNS.md`) — the vacuously-green guard; this discipline is its structural prevention.
- `static-latency-path-conformance-analysis.md` — the first canonical non-vacuity self-asserting guard (15 teeth); an application.
- `structural-enforcement-when-memory-insufficient.md` (M7) — a guard is worth building only if it can fail; the calibration corpus is what makes "it can fail" provable + kept-provable as the code evolves.
