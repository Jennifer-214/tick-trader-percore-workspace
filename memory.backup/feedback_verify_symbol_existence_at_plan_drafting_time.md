---
name: feedback-verify-symbol-existence-at-plan-drafting-time
description: "Before plan body cites any function/symbol/file:line as part of structural-change proposal, verify the cited symbol EXISTS in current code via comprehensive grep. Fabricated/stale symbol names cause coding-time wasted cycles. Sister to canonical-sister-discipline (producer side) + enumerate-consumers (consumer side); THIS rule is SYMBOL-EXISTENCE side."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f7bb757d-2b7c-4ba6-9c4a-1c7d60bff493
---

**When proposing structural change** (refactor / helper extract / registry consolidation / mirror close), plan body cites specific functions / symbols / file:line refs. **Verify EACH cited symbol EXISTS in current code via comprehensive grep BEFORE plan body finalizes** — fabricated/stale symbol names cause coding-time wasted cycles.

**Why:** Codified 2026-05-25 at `.B.4` v1.5 amendment cycle after Phase A enumeration sweep caught D1: plan body v1.0 → v1.4 cited `OrderManager_RegisterCore(c)` as a per-core boot call to extract into `EngineCommon_BootPerCore`. Comprehensive `rg "OrderManager_RegisterCore" /home/caramel/code/FoxML_Trader_v2/` at HEAD `64e7101` returned **zero matches** — the function does not exist anywhere in the codebase. Actual function at the cited region is `EventLoopState_RegisterCore`. Plan body conflated two distinct framework concerns: registering a core into the event loop's dispatch table (the real call) vs. registering a core into an OMS routing table (no such mechanism exists; OMS routes via `core_id` field on `Order` struct).

The drift survived 5 amendment cycles (v1.0 / v1.1 / v1.2 / v1.3 / v1.4) + 6 audit firings (/precoding-audit-gate / /blindspot-scan / /accounting-audit / /train-serve-asymmetry-sweep / /anti-spaghetti / /dod-audit). None of those audits explicitly verified that cited symbol names existed in current code. Phase A Step A.4 enumeration sweep (mandated by `feedback_enumerate_consumers_before_registry_row_deletion`) caught it on the FIRST grep-verification pass.

**How to apply:** Before plan body proposes any structural change citing specific symbols:

1. **List ALL cited symbols** (function names / type names / file:line refs / macro names) in scope of the change
2. **Run comprehensive grep per cited symbol:**
   ```bash
   rg "<symbol_name>" <codebase_root> -g '*.hpp' -g '*.cpp' -g '*.py' -g '*.md'
   ```
3. **Verify each match:**
   - Symbol EXISTS at cited line ±5 (line drift OK; missing entirely is NOT)
   - Symbol type matches plan body's framing (function vs type vs macro)
   - If callsite signature cited: verify arg count + types match
4. **For file:line refs:** verify line ±10 (small drift acceptable; large drift signals stale fork-point)
5. **If ANY symbol cited is fabricated OR missing:** STOP plan body finalization; investigate (was it renamed? deleted? never existed?)

**Recognition markers:**
- Plan body lists 10+ symbol citations from a 2-week-old audit report → audit may have been against pre-merge codebase; verify each
- "Per the audit at [old date]" framing → audit findings may have stale citations; re-verify
- Plan body claims "OrderManager_X" or "EventLoop_Y" without operator confirmation the function exists → grep first
- Cross-component refactor proposals (e.g., extract to NEW header) → both source surfaces + target API need symbol-existence verification

**Sister memories:**
- [[feedback_audit_canonical_sister_before_new_infra]] — PRODUCER side discipline (don't create parallel infra; grep for existing patterns first)
- [[feedback_enumerate_consumers_before_registry_row_deletion]] — CONSUMER side discipline (don't delete without enumerating consumers)
- **THIS RULE** — SYMBOL-EXISTENCE side (don't cite without verifying cited symbol exists)

Three sister disciplines all map to the same root principle: **comprehensive grep before structural change**. Each catches a different failure mode:
- Producer side catches "we're building infra that already exists"
- Consumer side catches "we're deleting infra that has more consumers than we listed"
- Symbol-existence side catches "we're referencing infra that never existed in the first place"

**Where in plan body to apply:**
- Decision matrix table cites: verify symbol names
- Coding sequence step descriptions cite: verify function names + file:line refs
- "Pre-coding concerns" section cites: verify hazards reference real code
- Sister registry / sister pattern table cites: verify cited patterns exist + at cited file:line

**Coding-time fallback:** even with planning-time verification, ALSO run comprehensive grep at Phase A audit gate (sister to Step A.4 enumeration). Catches drift between plan body lock + coding start.

**Sister to compaction-degradation rule:** [[feedback_compaction_degrades_treat_handoffs_as_hints]] — handoffs lose precision (sigs, paths, counts, asymmetry depth). Plan bodies inherit handoff precision when drafted in compacted sessions. This rule is the COUNTERMEASURE: always re-verify cited symbols against current code, especially when plan body is drafted in late session.

**Sister to iteration-spiral rule:** [[feedback_iteration_spiral_signals_audit_meta_gap]] — 5 amendment cycles at `.B.4` for `OrderManager_RegisterCore` drift would have been compressed to 1 cycle if v1.0 had grepped for the cited symbol. This rule is the META-GAP CLOSURE.

**Trade-off:** for plan bodies citing ≤5 symbols, manual verification at drafting time is trivial (~2 min). For plan bodies citing 50+ symbols (large refactor), batch the grep via shell loop or delegate to an enumeration agent (like the Phase A Step A.4 dispatch pattern). Either way, the verification is cheaper at planning time than at coding time.
