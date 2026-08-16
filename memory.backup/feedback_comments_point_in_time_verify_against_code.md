---
name: comments-are-point-in-time-verify-code-behavior-claims-against-the-code
description: "A comment making a CHECKABLE claim is a hypothesis, not documentation — verify when it becomes load-bearing for your edit and fix it in the SAME commit; WIDENED 2026-08-15 beyond codegen/perf/size to reader-sets, quantifiers, defaults, guard-existence, file:line cites and ordering, plus the extend-the-grammar corollary"
metadata: 
  node_type: memory
  type: feedback
  tags: [audit-methodology]
  originSessionId: 8b9ef1cd-6e14-438a-8cb3-86f7d4bdbead
  sister_specs: [feedback_ground_design_in_real_code.md, feedback_guards_compound_enforcement_is_leverage.md, feedback_match_anomaly_to_decision_log_before_escalating.md, feedback_resource_use_gated_on_existence_not_felt_need.md, feedback_single_source_of_truth_discipline.md, feedback_compaction_degrades_treat_handoffs_as_hints.md, project_remote_push_needs_operator_password.md]
  modified: 2026-08-16T01:49:14.842Z
---

A code comment is **point-in-time-accurate** — true when written — but code, and especially CODEGEN, drifts, so a comment is **NOT ground truth** for a behavior fact.

When a comment ASSERTS a code-behavior claim — codegen (`// CMOV-style` / "branchless" / "compiles to X"), latency/perf ("~4ns" / "verified in bench_X"), size/layout/cache-fit, or complexity — **verify it against the actual compiled code** (disassemble · `check_latency_path_conformance.py` · `check_struct_size_budget.py` · read the current code), NEVER trust the comment. On a comment-vs-code **MISMATCH** the **CODE is truth**: SURFACE the stale comment as a FINDING + SUGGEST the corrected wording (a stale code-fact comment isn't background — it actively misleads).

**Why (caught 2026-06-30):** a subagent verifying a hot-path select trusted a `// CMOV verified in bench` comment and concluded "≈0 gain, don't bother" — but the comment was stale (written pre-Ship-B when `Money` was narrower; at 16B `__int128` there is no x86 128-bit cmov, and the conformance analyzer's disassembly showed a real `je`). The stale comment nearly inverted the recommendation.

**How to apply:** armed into `DOCS/SUBAGENT_ARMING.md` §2.5 (all i/a/v/d/c agents read it first) + a CODEGEN row in [[mechanical-verification-of-derived-code-facts]]. Extends [[feedback_ground_design_in_real_code]] (cite live code, don't reconstruct — now: don't trust the COMMENT either) + AR-8 (the writer is model-bounded; a stale self-comment is that bound made durable). The fix is symmetric: when YOU find a comment-vs-code mismatch, propose the comment fix, don't just route around it.

---

## WIDENED 2026-08-15 (E.1.2 / D-421) — the taxonomy, and why the narrow version missed five of six

Six stale comments surfaced in one session and **five fell outside this memory's original
{codegen, latency, size} triggers**. The i-class agents caught them anyway, by generalizing past
the letter of the rule — which is good agents, not a rule working. So the trigger set is now the
full **checkable-claim taxonomy**:

- **reader/writer sets + concurrency** ("single writer AND reader" / "no atomics needed" / "the GUI
  reads X, not Y") → grep every reader.
- **quantifiers** — *every / all / only / never / single* → enumerate the set (M9).
- **default values** → read the `_Default` function.
- **guard-or-tool existence** ("CI Check N enforces…", "`tools/X.py` catches this") → `ls` it.
- **`file:line` cites** → resolve them.
- **ordering** ("reset at the top of each rebuild") → compare line positions.
- codegen / latency / size — the original three, unchanged.

**The instance that makes this bug-causing rather than hygiene.** `SlowPathGateRegistry.hpp` stated
the gate state had a single writer AND single reader, "no atomics needed", and that "GUI display
reads PerNodeSnap, not gate_state directly". All three false — the snapshot publisher reads
`gate_state` from the producer thread to *build* that PerNodeSnap bit. That comment told every later
reader the field was single-threaded, so nobody asked what it held before the first write, and it
was never initialized at all (indeterminate `uint16_t`, UB, cross-thread reader). **The stale
comment is what suppressed the question.**

**Guard-or-tool existence is the highest-severity kind**: it doesn't just misinform, it manufactures
confidence and stops anyone looking. A registry comment promised *"NEW CI Check 8 enforces…"* for a
tool that was never written — Class 30 was documented as structurally closed by nothing.

**Prefer narrowing to deleting.** "Recomputed before every read" became "…dominated by the recompute
at both CAPITAL reads; the two display reads are out-of-pass and show 0 for one cycle." The precise
version is what makes the next reader's question answerable.

### The other half — EXTEND the grammar, never work around it

A comment stays verifiable only if what it says is *expressible in the checked vocabulary*. When the
tag grammar can't say your thing, add the token — don't smuggle the meaning into free text, because
a value the grammar doesn't know is a claim no check can ever verify. That is how the next stale
comment is born. The path is cheap and already exists: `check_code_tag_blocks.py` **derives** the
closed CATEGORY set from the ```category-set``` fence in the schema spec, so folding a category is
ONE token and ZERO tool edits — doc, code and gate stay equivalent by construction.

Ask in order: (1) does the concept already exist one level down as a VALUE under an existing
category? (2) only then add the token. Worked instance: retiring `Portfolio_Save`/`_Load` wanted a
tombstone marker; `[TOMBSTONE]` RED-ed with a bare "UNKNOWN category", so I invented
`[COMMENT]_[TOMBSTONE — …]` — while the concept had existed all along as
`[ROW]_[TOMBSTONE]_[<retired-id>]`. Nothing pointed there. The gate now teaches both branches at the
RED, with teeth pinning each direction.

**General shape:** a gate that only says *no* manufactures workarounds. Any closed vocabulary needs
its extension path discoverable **at the RED**, or the vocabulary quietly stops describing the
system. Sister: [[feedback_resource_use_gated_on_existence_not_felt_need]].

### Why this moved to the always-loaded tier

`SUBAGENT_ARMING.md` § 2.5 carries this rule, and it is why the delegates found all six — but the
main session never loads that doc. **The rule armed the delegates and not the principal.** Promoted
from `MEMORY_EXTENDED.md` to `MEMORY.md` at the same time as the widening.

Sisters: [[feedback_ground_design_in_real_code]] · [[feedback_single_source_of_truth_discipline]] ·
[[feedback_compaction_degrades_treat_handoffs_as_hints]] (same shape, different artifact — a record
that was true when written and is read as current) ·
[[feedback_guards_compound_enforcement_is_leverage]] ·
[[feedback_match_anomaly_to_decision_log_before_escalating]] · Class 38 (phantom invariant — the
*never-enforced* sibling of this *was-true-then-drifted* class).
