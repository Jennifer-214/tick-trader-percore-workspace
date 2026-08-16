---
name: project_remote_push_needs_operator_password
description: "Pushing to GitHub: just RUN it. Push is SSH TRANSPORT ONLY and does not sign — already-signed commits need no GPG at push time. Verified 2026-08-15: plain sandboxed push, no flag, no prompt, rc 0. Commits are free. Do not defer pushes or ask permission for them."
metadata:
  node_type: memory
  type: project
  originSessionId: 38ff0058-1602-47c0-af7c-627a3a4357a4
  sister_specs: [feedback_micro_commits_compile_gated.md, feedback_comments_point_in_time_verify_against_code.md]
  tags: []
  modified: 2026-08-16T01:47:40.121Z
---

Pushing to the GitHub remotes (engine `FoxML_Trader_v2` + the private
`tick-trader-percore-workspace`) is a thing you DO, not defer — Caramel 2026-07-04:
*"you do know you can push and commit right."*

**THE CORRECTION (2026-08-15) — `git push` does NOT sign anything.** COMMITS carry the GPG
signature; push is pure SSH transport of objects that were already signed when they were made. The
earlier version of this memory said *"the push's commit-signing pops a pinentry on HER screen"* —
that conflated two different mechanisms, and it is why a whole session's worth of pushes got
deferred behind an imagined gate. If the commits already exist, a push needs **SSH only**.

**Verified 2026-08-15, directly:** `git push origin feat/v5.15-live-readiness` run from the DEFAULT
Bash sandbox, with NO `dangerouslyDisableSandbox`, no pinentry, no hang — `0a15f07..49df9d2`, rc 0,
immediate. `ssh-add -l` reported *"Error connecting to agent: No such file or directory"* at the
same moment, and `git ls-remote` on the private repo authenticated fine — so the key is reachable
without an agent in this environment.

**Workflow: commit at clean boundaries, then just push.** Do not ask permission for the push itself
and do not treat it as blocked-pending-a-separate-ask. Escalate only on an ACTUAL failure, in this
order: (1) plain push — the normal case; (2) retry with `dangerouslyDisableSandbox: true` if it
hangs (the 2026-07-04 observation that a sandboxed push can be agent-isolated may still hold on
other machine states); (3) ask her to run `! git -C <repo> push` so any prompt reaches her terminal.

**COMMITS are free** — they sign off the warm gpg-agent cache and succeed non-interactively. Commit
autonomously at clean boundaries (per [[feedback_micro_commits_compile_gated]]).

**The meta-lesson, which is why this memory now carries a sister to
[[feedback_comments_point_in_time_verify_against_code]]:** this entry was cited to the operator as
*"push needs your terminal"* — which the memory did not even say — and the underlying mechanism
claim was wrong on top of that. A memory is a point-in-time observation about a MECHANISM; when it
is load-bearing for an action you are about to refuse to take, verify it (`ssh-add -l`,
`git ls-remote`, or simply try the thing) before quoting it as a constraint. Refusing to act on a
stale memory costs more than the memory saves.
