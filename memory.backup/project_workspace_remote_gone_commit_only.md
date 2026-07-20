---
name: project-workspace-remote-gone-commit-only
description: "SUPERSEDED 2026-07-19 — the workspace remote is ALIVE again (re-pointed to Jennifer-214); sync/close SHOULD push. The old 'commit-only, never push' rule is retired."
metadata: 
  node_type: memory
  type: project
  originSessionId: 48cf1e7d-3242-4daf-951a-a95b831f0804
  modified: 2026-07-20T03:51:02.900Z
  sister_specs: [feedback_compaction_degrades_treat_handoffs_as_hints.md, feedback_verify_by_context_not_count.md, project_public_repo_is_code_only.md]
  tags: []
---

**⚠️ CORRECTED 2026-07-19 — this memory's original claim is NO LONGER TRUE, and following it caused real harm.**

**Current fact (verified 2026-07-19 by `git ls-remote --exit-code origin HEAD` → rc=0):** the workspace repo `~/code/tick-trader-percore-workspace` **HAS a live remote** — `git@github.com:Jennifer-214/tick-trader-percore-workspace.git`. It was re-pointed from the dead `Jennyfirrr` origin (that account was deleted 2026-07; see [[project-public-repo-is-code-only]]) to the current `Jennifer-214` account at some point after 2026-07-16.

**What the stale version cost:** it instructed `/sync-workspace` and `/close-session` to "end at the COMMIT — skip `git push`." Followed literally, that left **77 commits unpushed** — including entire sessions of decision logs, DESIGN_SPECS, and memories that exist on exactly one machine. The workspace holds the institutional memory (decision log · specs · plans · memories); it is the LEAST replaceable thing here and it was the least backed up. Caramel raised it directly: *"remote backups are always good, we need those."*

**How to apply now:** `/sync-workspace` and `/close-session` **push** the workspace after committing. Do not skip it, and do not re-diagnose a "dead remote" — verify with `git ls-remote --exit-code origin HEAD` before concluding anything about remote state. The engine + plugin repos have their own remotes and push cadences.

**⚠️ PUSHES REQUIRE CARAMEL'S SIGN-OFF — a hang is EXPECTED, not a fault (confirmed 2026-07-19).** SSH is configured for per-operation confirmation, so `git push` BLOCKS until she approves. Observed signature: first attempt times out (~2 min), a retry may fail outright, a later retry succeeds once approved. `ssh-add -l` reports **"Error connecting to agent"** and that is NORMAL for this setup — there is no long-lived agent by design. **Do NOT** diagnose this as a broken key, a dead remote, or an auth failure, and do NOT advise re-adding a key (that advice was given in error at the 2026-07-19 close). Just say a push is pending her approval and wait, or ask her to approve. Corollary: a push cannot run unattended — never schedule one in a background/automated step that assumes it completes.

**The generalizable lesson (why this file was corrected rather than deleted):** a memory asserting an environment FACT ("no remote exists") silently expires when the environment changes, and nothing re-checks it — so it kept producing a wrong action for three days. Environment-state memories must name their verification command so a reader can re-confirm cheaply, instead of inheriting a stale fact as settled. Sisters: [[feedback_compaction_degrades_treat_handoffs_as_hints]] (same shape at the handoff surface) · [[feedback_verify_by_context_not_count]].
