---
name: feedback_test_change_enumeration_per_plan_body
description: "Every plan body touching tested code MUST enumerate test changes in dedicated section — (a) modified, (b) broken/replaced, (c) NEW unit tests added — to prevent silent test drift during restructure ships"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f8d1354c-702d-4ff6-b985-c90cafb1a1f2
---

When a plan body's coding sequence touches code that has TESTS, the plan body MUST include a dedicated "Tests changed" section before coding starts. Three sub-categories with explicit enumeration:

**(a) Modified tests** — mechanical-rename or signature-change tests that need to compile against new code shape (e.g., `state.cores[i].field` → `state.nodes[i].field` during Core→Node rename). Enumerate file:line-range references per affected test.

**(b) Broken/replaced tests** — tests that exercise now-deleted code paths. Either DELETE (with B14 deletion-cohort ordering rationale + Class 33 consumer-enumeration discipline) OR REPLACE with equivalent test against new code path. Document choice + justification per test.

**(c) NEW unit tests added** — tests added for NEW functions/API surface introduced by the ship. Per `feedback_motivated_collaborator_for_caramel` (quality bar) — every NEW function should have a unit test verifying behavior given controlled inputs. Include test name + what invariant verified.

**Why:** Restructure ships (Core→Node rename / per-node drainer absorption / multi-exchange substrate / etc.) touch test surface in ways that are easy to miss when planning is monolithic-scenario-test-centric. Without explicit enumeration:

- Modified tests may compile against renamed symbols but verify weakened invariants (Class 25 cosmetic-fix variant at test surface)
- Broken tests may get silently disabled (`#if 0` / `DISABLED_*` / commented assertions) instead of replaced — exactly the assertion-weakening that `/test-strength-audit` catches but only AFTER the damage is committed
- NEW functions may ship without test coverage → future regression risk + Class 14 fabrication risk at downstream plan-body citations
- Test corpus drift accumulates silently across restructure ships → eventual integrity collapse

Per existing test-strength-audit baseline discipline: the codebase ratio at v5.15.5.F.4d.1.D is ~3,135 assertions in monolithic `controller_test.cpp` + 31 integration + 26 depth-recorder. Strong baseline; protect against drift during restructure.

**Philosophy alignment:** Each plan body should also surface MOVEMENT toward function-granularity unit tests (per D-36 `tests/{unit,integration,chaos,benchmark,property}/` reorg at `.E.1`). Monolithic scenario tests are necessary but insufficient for restructure-resilience — unit tests at function granularity catch mechanical-rename-induced semantic drift that scenario tests cannot. Move toward unit tests as default for NEW API surface; preserve scenario tests as cross-cutting integration verification.

**How to apply:**

1. **At plan body draft** — enumerate (a) (b) (c) explicitly in dedicated "Tests changed" section before "Coding sequence" section
2. **At /readiness audit** — NEW Check (post-D-36) verifies the section exists + is complete; flag missing as audit finding
3. **At per-test triage in restructure ships** — distinguish (a) vs (b) vs (c) per test; never lump-categorize
4. **At post-ship-audit** — verify enumerated tests actually landed + no silent disablement crept in mid-ship

**Worked example:** Codified at `v5.15.5.F.4d.1.D.1` doc-sweep ship (plan body template amendment + NEW discipline). First canonical application = `.E.1` Foundation plan body Core→Node rename test enumeration (~200+ test-surface sites projected). `.E.1` audit (cycle 1) verifies the section exists + each enumerated change has rationale.

**Scope NOT covered:**
- Test-strength baseline assertions (covered by `/test-strength-audit` skill)
- Test reorganization layout decisions (covered by D-36 reorg work)
- Coverage measurement (separate discipline; queue for v5.16+ if needed)

**Sister:** [[feedback_consult_on_audit_findings]] (sister discipline; this extends to test surface) + [[feedback_motivated_collaborator_for_caramel]] (quality bar; NEW functions get tests) + [[feedback_multi_surface_deletion_ordering_discipline]] (test-surface is one of the deletion-kind categories per B14 pillar) + [[feedback_audit_canonical_sister_before_new_infra]] (NEW unit tests should test CONTRACT not implementation — per `canonical-sister-extension-discipline` + observable-behavior testing).
