---
type: meta-discipline
stage: 2-draft
established: 2026-07-17
tags: [audit-methodology, verification, structural-enforcement, test-infrastructure, doc-discipline]
surface: [ci-tooling, test-infrastructure]
sister_specs: [meta-disciplines/mechanical-verification-of-derived-code-facts.md, audit-methodologies/static-latency-path-conformance-analysis.md, meta-disciplines/structural-enforcement-when-memory-insufficient.md]
sister_docs:
  - DOCS/RECURRING_BUG_PATTERNS.md   # Class 51 (vacuously-green guard) — the anti-pattern this discipline prevents
applications:
  - 'check_conversion_completeness.py --selftest — synthetic DemoLumped6 (a 6-field struct lumped in a [FUNCTION] block) is FLAGGED; an ExecutionCore-shaped complete fixture scans CLEAN (E.1.2.A, D-362 first application)'
  - 'check_latency_path_conformance.py — 15 --selftest teeth; asserts its own non-vacuity by refusing a RollingStats wrapper optimized to 2 instr (Class 51 first canonical)'
  - 'check_code_tag_blocks.py --selftest — present-vs-absent per [REFERENCE] subcat (11 -> 20 checks)'
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

## Home + shared SSoT

`tests/schema_golden/` holds the golden-COMPLETE dogfood corpus; a sister golden-BROKEN set + a shared `calibration_fixtures.py` that EVERY tool's `--selftest` imports is the single source (so a new fixture is added once and every guard's selftest sees it — one-fixture-set, N guards; the `doc-intelligence-toolchain-architecture` "one core, N consumers" thesis applied to the test layer). *(Status 2026-07-17: the shared importer is Phase-C+ work; the completeness gate's in-line synthetic `DemoLumped6` is the proto-application, D-362.)*

## Sister disciplines

- `mechanical-verification-of-derived-code-facts.md` — the derived-fact guards (size/cache/latency/codegen) are exactly the tools this discipline calibrates; its § INVERSE (false-RED) IS the golden-COMPLETE half.
- **Class 51** (`DOCS/RECURRING_BUG_PATTERNS.md`) — the vacuously-green guard; this discipline is its structural prevention.
- `static-latency-path-conformance-analysis.md` — the first canonical non-vacuity self-asserting guard (15 teeth); an application.
- `structural-enforcement-when-memory-insufficient.md` (M7) — a guard is worth building only if it can fail; the calibration corpus is what makes "it can fail" provable + kept-provable as the code evolves.
