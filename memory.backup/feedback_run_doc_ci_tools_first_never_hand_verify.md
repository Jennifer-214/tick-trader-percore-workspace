---
name: run-doc-ci-tools-first-never-hand-verify
description: "Verifying doc/plan/citation/index/memory correctness → run the deterministic CI TOOL first, never hand-verify by eye; the agent eyeballing file:line refs + byte counts + bidirectional links is the error-prone path the tools exist to replace. With context budget, run the full sweep, don't spot-check. And never schedule a defensive wakeup on a transient empty tool result — just retry the call."
metadata: 
  node_type: memory
  type: feedback
  sister_specs: [feedback_independence_for_judgment_not_mechanical.md, feedback_structural_enforcement_when_memory_insufficient.md, feedback_operator_pushback_as_audit_signal.md, feedback_document_as_you_go_over_catch_at_end.md]
  tags: [audit-methodology, framework-discipline, meta-discipline]
  originSessionId: b1ce1b7e-9d36-4f05-a210-c616603d3d9d
---

When verifying that docs / plan bodies / citations / indexes / memory frontmatter are correct, run the deterministic CI **tool** as the FIRST move — do not hand-verify by reading the files and eyeballing it. The agent checking `file:line` citations, byte counts, or bidirectional sister-links by eye is exactly the slow, error-prone path the tools exist to replace. This is `feedback_independence_for_judgment_not_mechanical` applied to self-verification: a mechanical check runs as the TOOL (determinism IS the correctness), not as agent judgment.

**Why (empirically, `.E` Session-4 2026-05-30):** the agent asserted "clean stopping point" / hand-"fixed" a citation path 3× across the session; each time a tool, when finally run, found it wrong — a fabricated `ML_Headers/Fingerprint.hpp` path (was `Backtest/`), a dropped `CoreFrameworks/` prefix on 3 plan-body citations (B-Plus caught all 3), a one-way memory sister-link (`check_doc_metadata --bidirectional` = exit 1, a red build). Hand-verification didn't just waste effort — it produced WRONG "clean" verdicts. Operator: "we have CI tools for this… why aren't we using them… I'm getting tired of doing this every time."

**How to apply:**
- **Tool first, not last.** Before claiming any doc/plan is clean, run the check. The canonical one-shot is `tools/check_session_docs.sh` (aggregates `check_doc_metadata --bidirectional --memories` + B-Plus `check_plan_body_symbol_existence` + forward-promise + meta-registry). Wired into `/close-session` Stage 2.0 as a HARD gate so it fires by default.
- **Full sweep, not spot-check.** Context budget is not a constraint — run the comprehensive suite, not one tool.
- **Never assert "clean" from a feeling of doneness.** "Clean" is a tool exit-0, nothing else.
- **Transient empty tool output → RETRY the call, don't schedule a defensive wakeup.** Empty Bash/Read returns this session were transient (and often my own zsh glob error, e.g. `--include=*.hpp`); a same-turn retry always worked. Scheduling a wakeup "to recover" produced 3 spurious no-op fires.
- **The structural fix already existed; I wasn't reaching for it.** B-Plus + capture-audit are pre-commit hooks — but only in the ENGINE repo, where `plans/` is gitignored, so they never gated WORKSPACE doc commits. `check_session_docs.sh` + the `/close-session` Stage 2.0 wiring closes that gap (M7 structural enforcement). The lesson is to let the wired tools fire, not pre-empt them with hand-assertion.

Sister: [[feedback_independence_for_judgment_not_mechanical]] (the parent — mechanical→tool, judgment→agent), [[feedback_structural_enforcement_when_memory_insufficient]] (M7; the aggregator+wiring is the structural close), [[feedback_operator_pushback_as_audit_signal]] ("are you sure?" → run the tool BEFORE re-answering).
