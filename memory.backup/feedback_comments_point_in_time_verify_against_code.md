---
name: comments-are-point-in-time-verify-code-behavior-claims-against-the-code
description: "A comment was accurate when written but code/codegen drift; for any comment asserting a code-BEHAVIOR fact (codegen / cmov-vs-branch / \"branchless\" / latency / size / \"verified in bench\"), verify against the compiled code, never trust the comment; flag + suggest a fix on mismatch"
metadata: 
  node_type: memory
  type: feedback
  tags: [audit-methodology]
  originSessionId: 8b9ef1cd-6e14-438a-8cb3-86f7d4bdbead
  sister_specs: [feedback_ground_design_in_real_code.md]
---

A code comment is **point-in-time-accurate** — true when written — but code, and especially CODEGEN, drifts, so a comment is **NOT ground truth** for a behavior fact.

When a comment ASSERTS a code-behavior claim — codegen (`// CMOV-style` / "branchless" / "compiles to X"), latency/perf ("~4ns" / "verified in bench_X"), size/layout/cache-fit, or complexity — **verify it against the actual compiled code** (disassemble · `check_latency_path_conformance.py` · `check_struct_size_budget.py` · read the current code), NEVER trust the comment. On a comment-vs-code **MISMATCH** the **CODE is truth**: SURFACE the stale comment as a FINDING + SUGGEST the corrected wording (a stale code-fact comment isn't background — it actively misleads).

**Why (caught 2026-06-30):** a subagent verifying a hot-path select trusted a `// CMOV verified in bench` comment and concluded "≈0 gain, don't bother" — but the comment was stale (written pre-Ship-B when `Money` was narrower; at 16B `__int128` there is no x86 128-bit cmov, and the conformance analyzer's disassembly showed a real `je`). The stale comment nearly inverted the recommendation.

**How to apply:** armed into `DOCS/SUBAGENT_ARMING.md` §2.5 (all i/a/v/d/c agents read it first) + a CODEGEN row in [[mechanical-verification-of-derived-code-facts]]. Extends [[feedback_ground_design_in_real_code]] (cite live code, don't reconstruct — now: don't trust the COMMENT either) + AR-8 (the writer is model-bounded; a stale self-comment is that bound made durable). The fix is symmetric: when YOU find a comment-vs-code mismatch, propose the comment fix, don't just route around it.
