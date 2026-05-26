---
name: enumerate-helper-signature-args-before-extract
description: "When extracting helper from inline body OR lambda body, MUST enumerate every body-internal symbol reference + per-callee parameter list + cross-check against helper signature BEFORE plan body lock. Sister to feedback_verify_symbol_existence_at_plan_drafting_time (SYMBOL-EXISTENCE side; Class 14) + feedback_enumerate_consumers_before_registry_row_deletion (CONSUMER-enumeration side; Class 18); THIS RULE is BODY-CONTENT side. Codify proactively at 2 instances per feedback_proactive_novel_alternative_consideration (don't wait for 3rd recurrence)."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc2542a7-8662-4b21-a393-f1598d05e50b
---

When proposing helper extraction from an inline body OR lambda body, the helper SIGNATURE must enumerate EVERY input the body reads + EVERY output the body writes. Planning that specifies "extract this body into a helper" without per-callee parameter enumeration produces signatures that don't match what the body actually needs — surfaces as cascading "wait this needs more args" at coding time + risk of cryptic compile errors.

**Why:** Caught twice during `.B.4` planning cycle (2026-05-25 + 2026-05-26):

1. **BootPerCore v1.6 O1 (4→8 args)** — v1.5 spec'd 4 args `(cfg, c, state, oms)`. Phase B body extraction at v1.6 surfaced body needs caller-owned static refs (`tick_ring` + `core`) + nullable ML zoo pointers (`zoo_ptr` + `ezoo_ptr`) + caller-precomputed `core_balance`. Drops unused `oms`. Net 8 args.

2. **SlowPathCycleOneCore v1.7.3 N-6 (6→9 args)** — v1.7.2 spec'd 6 args `(cfg, c, state, oms, price, ts_us)`. 5-parallel-agent audit at v1.7.2 (trace-deps + dod-audit + readiness + bug-check + plan-context-sweep) CONVERGED on body needs 4 additional inputs: `volume` + `now_tick` (distinct from `ts_us` microseconds) + depth fields (book_imb + book_spread + book_mid). BookSnapshot<F> sister-canonical reuse per `feedback_audit_canonical_sister_before_new_infra` (existing struct at DataStream/BinanceDepth.hpp). Net 9 args.

Both instances semantically identical class shape — planning spec'd helper signature based on PROPOSED structural intent, not against ACTUAL body content enumeration. Per `feedback_proactive_novel_alternative_consideration`: codify at 2-instance proactive threshold rather than wait for 3rd recurrence.

**How to apply:**

1. **Before plan body locks helper signature** for any extracted helper from inline body / lambda body / function body:
   - Read the body's SOURCE LINE RANGE in full
   - Enumerate every symbol reference: cfg fields / state struct member access / function calls / closure captures / atomic loads / static reads / lambda-scope locals / module-scope globals
   - For each function call inside the body, read the CALLEE'S full signature + verify each arg the caller provides
   - For each variable read inside the body, classify as: HELPER SIGNATURE arg / cfg-derived (no arg needed) / state-derived (no arg needed) / STAY_IN_CALLER (LIVE-only persistence sinks / threading observability / etc.)
   - Generate enumeration CSV artifact at `plan_checks/<date>-<ship>-<helper-name>-body-content-enumeration.csv` (sister to boot-call-sequence-enumeration.csv pattern at .B.4 Phase A Step A.4)

2. **At plan body lock**: helper signature args MUST match enumerated body-content requirements + per-callee parameter requirements. NO signature args that body doesn't read; NO body reads without signature args (unless explicitly STAY_IN_CALLER classified).

3. **At amendment time** (per `feedback_recheck_designspecs_on_pushback` + `feedback_iteration_spiral_signals_audit_meta_gap`): if any audit catches body-args gap, RE-RUN the enumeration discipline — don't just patch one arg at a time.

**Recognition markers (when this rule is being violated):**

- Plan body proposes "extract X body into helper Y" without enumerating body inputs
- Helper signature spec'd at "intent" level (e.g., "takes state + cfg + per-tick args") without specifying which per-tick args
- Audit catches signature args mid-amendment cycle (5+ args added at amendment vs caught at draft)
- Coding surfaces "wait this needs more args" cascade
- Spec uses "etc." or "..." in arg list (sign of un-enumerated args)

**Sister memories:**

- [[verify-symbol-existence-at-plan-drafting-time]] — sister CLASS 14 discipline (SYMBOL-EXISTENCE side; this rule extends to body-content layer)
- [[enumerate-consumers-before-registry-row-deletion]] — sister CLASS 18 discipline (CONSUMER side; this rule is the BODY-CONTENT side analog)
- [[audit-canonical-sister-before-new-infra]] — when extracted helper introduces new arg types, check existing canonical structs first (BookSnapshot reuse vs DepthBundle invention at v1.7.3 N-6 is the worked example)
- [[recheck-designspecs-on-pushback]] — REACTIVE companion (when pushback surfaces body-args gap, re-run enumeration)
- [[audit-own-proposals-with-same-rigor]] — PROACTIVE 4-pillar check (body-content enumeration is part of pillar 1 DESIGN_SPECS cross-check)
- [[proportionate-response-to-audit-findings]] — body-args gap is structural finding; full enumeration vs piecemeal patches
- [[proactive-novel-alternative-consideration]] — codify at 2-instance proactive threshold (THIS rule codified at 2 instances, not 3)
- [[plan-right-not-fast]] — body-content enumeration takes ~30-60 min at planning time vs hours of confusion at coding time

**Structural enforcement at `.B.4` ship close:**

- NEW `/readiness` Check 33 — body-content arg enumeration completeness verification at plan-time for any helper extract from inline/lambda body
- Extension to v1.7 D3 D.6 CI tool `tools/check_plan_body_symbol_existence.py` — add per-callee parameter-list grep against helper signature
- Memory amendment to MEMORY.md index (THIS file's pointer)
- Sister spec recommended at workspace `DESIGN_SPECS/meta-disciplines/body-content-enumeration-at-plan-time-discipline.md` (Stage 2 DRAFT per /dod-audit recommendation; promotes to Stage 3 first canonical with worked example pair: BootPerCore v1.6 O1 + SlowPathCycleOneCore v1.7.3 N-6)

**Codification trigger (worked examples for future):**

`.B.4` v1.6 O1 (BootPerCore 4→8 args; 2026-05-25) + `.B.4` v1.7.3 N-6 (SlowPathCycleOneCore 6→9 args; 2026-05-26). Both caught by audit at AMENDMENT time after draft locked; pre-draft enumeration would have caught at draft time saving 1-2 amendment cycles each. Pattern: helper extraction at body-content layer needs MORE rigor than registry-row sister discipline because body-content has cascading per-callee transitive requirements (each function called inside body has its own arg requirements).

Sister to `feedback_pre_draft_source_structure_enumeration` (NEW META-discipline candidate from `.B.4` v1.7.3 /plan-context-sweep on `.B.5-.B.11` — found that umbrella plans fabricated sub-file boundary names + function counts + macro existence from inferred labels rather than grep-verifying HEAD). Both rules fall under broader meta-class "planning-time fabrication of structural facts about source files" surfaced at 4-instance threshold per /plan-context-sweep agent.
