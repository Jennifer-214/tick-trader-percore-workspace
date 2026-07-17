---
name: project_remote_push_needs_operator_password
description: "Pushing to GitHub: RUN it with dangerouslyDisableSandbox (the default Bash sandbox isolates the ssh/gpg agent so a sandboxed push hangs), Caramel signs the GPG pinentry live; commits are free non-interactively. Do not defer pushes — just run them."
metadata: 
  node_type: memory
  type: project
  originSessionId: 38ff0058-1602-47c0-af7c-627a3a4357a4
  sister_specs: [feedback_micro_commits_compile_gated.md]
  tags: []
---

Pushing to the GitHub remotes (engine `FoxML_Trader_v2` + the private `tick-trader-percore-workspace`) is a thing you DO, not defer — Caramel 2026-07-04: *"you do know you can push and commit right. you just have to let me sign off on it for the gpg sig."* Two things must line up; once they do, it completes non-interactively:

1. **`dangerouslyDisableSandbox: true` on the Bash call.** The DEFAULT Bash sandbox ISOLATES the ssh/gpg agent, so a sandboxed `git push` can't reach it and HANGS (the 2-min timeout — earlier mis-attributed to "no pinentry the tool can fill"; the real first-order blocker is the sandbox network/agent isolation, NOT the auth). With the sandbox off, the push reaches her live agent. (Observed 2026-07-04: the SAME push hung in-sandbox, then EXIT=0 with `dangerouslyDisableSandbox` — engine `b10e778..84d73e0` + workspace pushes all landed this way.)
2. **Caramel's GPG sign-off.** The push's commit-signing pops a **pinentry on HER screen**; she enters the passphrase → it completes (3× EXIT=0 this session). Warm gpg-agent cache → she signs instantly; expired cache → the push hangs again → she re-signs, or runs `! git -C <repo> push` herself (the `!` prefix runs it in her session so the prompt reaches her).

**COMMITS are free** — they sign off the warm gpg-agent cache and succeed non-interactively even in-sandbox. Commit at clean boundaries autonomously (per [[feedback_micro_commits_compile_gated]]).

**Workflow:** commit freely → when ready to push, RUN it with `dangerouslyDisableSandbox: true` + tell her it's coming (the pinentry pops, she signs). Do NOT treat a push as blocked-pending-a-separate-ask — just run it; the only gate is her live sign-off. Fall back to asking her to `! git push` only if it hangs (she's away / cache expired).
