---
name: feedback_consult_indexes_before_full_reads
description: "When a corpus has index / summary / map files (MEMORY.md, MASTER-BACKLOG, _SESSION-CONTEXT, README, E-MASTER-REFERENCE, dependency-graph, find-recipes), consult THOSE first for structure / location / counts / disposition — then read only the full file(s) you actually need. The indexes exist for exactly this; reading everything when an index would answer the question wastes tokens + context. Order: index → grep → targeted read → full read, cheapest-first."
metadata: 
  node_type: memory
  type: feedback
  tags: [audit-methodology, scope-discipline]
  originSessionId: 3e806606-ac69-40fd-ac33-45906443bae4
  sister_specs: [feedback_run_doc_ci_tools_first_never_hand_verify.md, feedback_match_anomaly_to_decision_log_before_escalating.md, feedback_resource_use_gated_on_existence_not_felt_need.md]
---

Before reading a large corpus end-to-end, **consult its index / summary / map files first** — they exist precisely so you don't have to read everything. MEMORY.md (the memory index), a directory's `_SESSION-CONTEXT.md` / `_README.md` / `MASTER-BACKLOG.md` / `findings-merge-map.txt`, `E-MASTER-REFERENCE.md`, a `dependency-graph.md`, the doc-find recipes — each gives structure, location, counts, and disposition at a fraction of the bytes. Read the FULL file only for the specific detail the index can't answer.

**Why:** tokens + context are the budget. The `.E.0` findings corpus (2026-06-10) is ~480 KB across 11 files; its index files (`MASTER-BACKLOG.md` 10 KB + `_SESSION-CONTEXT.md` 12 KB + `findings-merge-map.txt` 3 KB) answered "what are the buckets / where do they live / which collide / what's CRIT+HIGH" in ~25 KB — reading all 11 sidecars would have spent ~20× the tokens for the same plan-vs-findings cross-check. The index-first read got the structure; targeted reads get the detail. An index that exists but goes unread is wasted infrastructure (sister shape: [[feedback_run_doc_ci_tools_first_never_hand_verify]] — use the purpose-built artifact, don't redo its job by hand).

**How to apply:** (1) Landing on an unfamiliar dir/corpus → `ls` + read the `_*` / `MASTER-*` / `README` / index files BEFORE any full-file read. (2) Looking something up across the doc system → MEMORY.md / E-MASTER-REFERENCE / the find-recipes first, grep second, full-read last. (3) Escalate to reading (or sub-agent-digesting) a large full file ONLY when the index genuinely lacks the detail — and then read the *specific* part, not the whole thing. The order is **index → grep → targeted read → full read, cheapest-first.** (4) Building a new corpus → give it an index file, so future reads are cheap (the indexes earn their keep both ways).
