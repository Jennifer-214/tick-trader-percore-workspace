---
name: feedback-script-transforms-need-output-eyeball
description: "Scripted mass-edits are sanctioned tooling BUT are where artifacts breed — every scripted pass gets real-diff eyeball + the gate battery before commit; checkers can false-positive, the SSoT validator arbitrates"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 48cf1e7d-3242-4daf-951a-a95b831f0804
---

Caramel (2026-07-16, mid E.1.2.A P6): *"the python scripts to change stuff is usually fine, its just what i see causing the most issues or stuff, keep that in mind."* Said after the normalize pass — the batch-era scripted conversions were the source of every artifact class the pass fixed (wholesale-wrapped banners, mismatched bars, one copied-not-moved duplication).

**Why:** a deterministic transform is only as correct as its site classification + byte assumptions; truncated dumps, wrap-joins, and boolean-vs-depth state tracking all produced real misses this session. The script's SUCCESS output proves it ran, not that it did the right thing.

**How to apply:**
- Scripted transforms stay sanctioned (she prefers them to hand-editing at scale) — but every scripted pass ends with (1) eyeballing REAL output diffs (git diff hunks, not the script's own log), and (2) the full mechanical gate battery, before commit.
- Fail-loud exact-match assertions in transform scripts (rep() with count checks); copy old_strings from Read output, never from clipped python prints.
- When two of your own checkers disagree, the production validator/tool is the SSoT arbiter — fix the CHECKER, don't "fix" green files.

Sisters: [[feedback-passing-test-is-not-verification]], [[feedback-run-doc-ci-tools-first-never-hand-verify]], [[feedback-verify-by-context-not-count]].
