---
name: project_remote_push_needs_operator_password
description: "Pushing to GitHub needs Caramel's interactive password confirmation; commits are free to do autonomously"
metadata: 
  node_type: memory
  type: project
  originSessionId: 38ff0058-1602-47c0-af7c-627a3a4357a4
  sister_specs: [feedback_micro_commits_compile_gated.md]
  tags: []
---

Pushing to the GitHub remotes (engine `FoxML_Trader_v2` + the private `tick-trader-percore-workspace`) needs Caramel's **interactive confirmation** — the SSH push (and her commit-signing key) prompt for a password, and a **non-interactive `git push` from the Bash tool HANGS** (no pinentry the tool can fill — observed as a 2-min timeout + `ssh-add -l` → "Error connecting to agent"). She stated it directly: *"you can commit and stuff but for pushing to remote, you have to get my input."*

**COMMITS are free** — they GPG-sign off the warm gpg-agent cache and succeed non-interactively. So commit at clean boundaries autonomously (per [[feedback_micro_commits_compile_gated]]).

**PUSHES need her** — RUN the push (so the prompt reaches her terminal and she enters the password) and tell her it's coming, or ask her to push. NEVER push non-interactively expecting it to complete; it will hang and waste a turn. If a *commit* ever hangs too, that's the gpg-agent cache having expired (rare) — she enters the GPG passphrase then.
