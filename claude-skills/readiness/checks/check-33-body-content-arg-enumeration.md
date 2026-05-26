---
type: skill-check
check_id: 33
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Body-content arg enumeration completeness (M6 META discipline)
established: 2026-05-26
sister_checks: [check-32-plan-body-symbol-existence-verification, check-34-audit-tier-declaration-and-scope-match]
---

# /readiness Check 33 — Body-content arg enumeration completeness (v5.15.5.F.4d.1.B.4+; M6 META discipline)

**When this fires:**

Plan body proposes ANY helper extract from inline body / lambda body / function body OR proposes new helper function signature without enumerating each input. Triggered when:

- Plan body uses phrase "extract X into helper Y" / "lift body of Z" / "factor out W"
- Plan body declares NEW function/helper signature for code that previously lived inline
- Plan body shows helper signature with "etc." or "..." in arg list

**Why this matters (v5.15.5.F.4d.1.B.4 lesson — M6 codification trigger):**

Codified at v1.7.3 of `.B.4` as `feedback_enumerate_helper_signature_args_before_extract` after pattern surfaced TWICE in same ship:

- **BootPerCore v1.6 O1 (4→8 args)** — v1.5 spec'd 4 args. Phase B body extraction surfaced body needs caller-owned static refs (`tick_ring` + `core`) + nullable ML zoo pointers + caller-precomputed `core_balance`. Net 8 args after audit cycle.
- **SlowPathCycleOneCore v1.7.3 N-6 (6→9 args)** — v1.7.2 spec'd 6 args. 5-parallel-agent audit CONVERGED on body needs 4 additional inputs: `volume` + `now_tick` + depth fields wrapped in `BookSnapshot<F>`. Net 9 args.

Per `feedback_proactive_novel_alternative_consideration`: codify at 2-instance proactive threshold rather than wait for 3rd recurrence.

The class: plan body specifies helper SIGNATURE based on *proposed structural intent* without verifying against ACTUAL body content + per-callee parameter requirements. Surfaces as cascading "wait this needs more args" at coding time + risk of cryptic compile errors.

**What to verify:**

For each helper-extract proposal in the plan body:

1. **Body source range cited:** Plan body lists explicit `<file>.hpp:<startline>-<endline>` range for the body being extracted.

2. **Body-content enumeration artifact exists:** Verify CSV at `plans/<sprint>/plan_checks/<date>-<ship>-<helper-name>-body-content-enumeration.csv` (sister to boot-call-sequence-enumeration.csv pattern). Each row: symbol-reference / category (HELPER-SIG-ARG / cfg-derived / state-derived / STAY-IN-CALLER) / source line / rationale.

3. **Per-callee parameter verification:** For each function call inside the body, plan body must cite callee signature OR include a "callee signatures" subsection in the artifact CSV.

4. **Helper signature matches enumeration:** Helper signature args list in plan body == HELPER-SIG-ARG rows in CSV (no signature args without body reads; no body reads without signature args unless STAY-IN-CALLER classified).

5. **"etc." / "..." absence:** No "etc." or "..." in plan body helper signature arg lists.

Verdict:
- **PASS** — all 5 criteria met for every helper-extract proposal
- **GAP** — any criterion missed → require enumeration artifact + signature alignment before next coding step
- **NOT-APPLICABLE** — plan body proposes no helper extracts (pure refactor / file-split / ledger-update ship)

**Output:**

If GAP, add to the /readiness report:

```
### Body-content arg enumeration finding (Check 33)

Plan body proposes helper extract for <helper-name> from <file>:<line>-<line>
but missing:
- [ ] Source range cited
- [ ] Enumeration CSV at plan_checks/<date>-<ship>-<helper-name>-body-content-enumeration.csv
- [ ] Per-callee parameter verification (callee signatures cited)
- [ ] Helper signature matches enumeration (no orphan args; no missing args)
- [ ] No "etc." / "..." in signature arg list

Risk: M6 anti-pattern (helper extraction at body-content layer). Past instances
required 1-2 amendment cycles each to discover missing args at audit time.

Action: produce enumeration CSV before coding. Use grep + read on source range;
classify every symbol; cite each function call's signature.
```

**Effort:** 30-60 min per helper extract at planning time vs hours of confusion at coding time + amendment cycles.

**Sister checks:**

- **Check 32** — plan-body symbol-existence verification (compile-time tool; runs after this check passes; catches drift in code samples beyond signature args)
- **Check 34** — audit tier declaration (HIGH-RISK ships with helper extracts must declare tier; routes appropriate audit depth)

**Sister memories:**

- `feedback_enumerate_helper_signature_args_before_extract` (M6 codification rule)
- `feedback_verify_symbol_existence_at_plan_drafting_time` (sister Class 14 discipline; symbol-existence side)
- `feedback_enumerate_consumers_before_registry_row_deletion` (sister CLASS 18 discipline; consumer-enumeration side)
- `feedback_audit_canonical_sister_before_new_infra` (when extracted helper introduces new arg types, check existing canonical structs first — BookSnapshot reuse worked example)

**Trigger origin:** v5.15.5.F.4d.1.B.4 v1.7.3 cycle (M6 codification after BootPerCore + SlowPathCycleOneCore both required late-arg-discovery amendments).
