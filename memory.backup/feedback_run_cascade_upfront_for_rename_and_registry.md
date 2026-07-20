---
name: feedback_run_cascade_upfront_for_rename_and_registry
description: "Run cascade.py rename/registry UPFRONT before any token rename or registry-macro change — enumerate the blast-radius (incl. the H15 MetaRegistry enrollment + the compiler-blind tools/.githooks/ refs) FIRST; don't edit-then-grep-for-stragglers."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a9f02eea-b737-43be-9dda-4497b9a95922
  sister_specs: [feedback_enumerate_consumers_before_registry_row_deletion.md, feedback_resource_use_gated_on_existence_not_felt_need.md, feedback_structural_enforcement_when_memory_insufficient.md]
  tags: []
---

Before renaming a token or changing a registry macro (rename / merge / delete / add-consumer), RUN the cascade tool FIRST to enumerate the full blast-radius — do NOT edit-then-grep-for-stragglers reactively.

- `cascade.py rename` — a token-rename campaign's full worklist across engine source PLUS the **compiler-blind apparatus** (`tools/` / `build.sh` / `.githooks/` — these commit GREEN on a stale regex; the build cannot see them).
- `cascade.py registry <FOREACH_NAME>` — one registry macro's footprint, role-classified (DEFINITION / **H15-ENROLLMENT** / EXPANDER / REFERENCE) + the MetaRegistry-enrollment status checked (D-298; built at `.E.1.2` right after this exact miss).

**Why:** the compiler is the totality oracle for engine-SOURCE code tokens (a rename slip red-builds), so the build already covers those. What SLIPS the build is (a) the **H15 MetaRegistry enrollment** — a registry rename/merge silently orphans it, and only `test_meta_registry_coverage` catches it — and (b) the **compiler-blind apparatus** (`tools/`/`.githooks/`). Running cascade UPFRONT surfaces both as first-class rows before you edit; discovering them after is a fix-after-discovery, not a plan.

**Why codified (M7):** the `.E.1.2` NodeCtx-registry unify hit this class TWICE in one session — the `Sharded_SlotNode` site-count, then the `FOREACH_NODE_CTX_FIELD` MetaRegistry enrollment — both found REACTIVELY despite the tool AND the discipline already existing. Two hits on one class ⇒ the memory-tier discipline was insufficient; the structural fix is the purpose-built `registry` subcommand + this run-it-UPFRONT rule.

Sisters: [[feedback_resource_use_gated_on_existence_not_felt_need]] (the felt-need miscalibration — the tool existed, I didn't reach for it up front), [[feedback_enumerate_consumers_before_registry_row_deletion]] (the consumer-enumeration discipline this operationalizes into one command), [[feedback_structural_enforcement_when_memory_insufficient]] (M7 — recurrence ⇒ structural). H15 (MetaRegistry coverage) + `refactor-patterns/rename-cascade-enumeration-tooling.md` (the spec).
