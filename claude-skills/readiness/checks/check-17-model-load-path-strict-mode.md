---
type: skill-check
check_id: 17
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Model-load path changes → strict-mode integration test
established: 2026-05-18
---

# /readiness Check 17 — Model-load path changes → strict-mode integration test

Trigger keywords: `CoreModelZoo`, `Model_Load`, `verify_model_stamp`,
`ModelHandle`, `held_out_gate_strict`, `feature_scaler_present`,
`scaler_load_failed`, `scaler_sha256`. When plan touches the model
load path:

- Verify the 3-tier strict-mode behavior (refuse / warn / skip)
  is preserved per `DOCS/CLAUDE_ML_INVARIANTS.md`.
- For each new failure mode, verify a corresponding PerCoreSnap
  field surfaces it (the v5.9.0b `model_load_failed` /
  v5.9.3a `scaler_load_failed` pattern).
- For each new failure mode, verify ML Status panel renders
  distinct state (red for warn-mode-with-identity, sand for
  legacy-no-attempt).
- For each new failure mode, verify rate-limited CRITICAL log
  fires (using `Health_LogCriticalRateLimited` per v5.9.0b).
- Verify integration test exists for BOTH refusal path AND
  warn-mode observability path (per
  `DOCS/CLAUDE_INVARIANTS.md` "Train-Serve Handoff Verification").

**Why this matters:** The v5.9.0b + v5.9.3a Gap H pattern is the
cure for the "silent fallback" class. Every new failure mode must
inherit the pattern. Otherwise we re-introduce silent drift.

**Verdict per item:**
- **PASS** ✅ — plan addresses
- **GAP** ⚠️ — must address before coding
- **DEFERRED** — explicit out-of-scope decision

These three checks fire in addition to Checks 11-14 (sprint guards).
Together they cover the v5.9 silent-failure class plus the v5.8
X-macro variant selection class.
