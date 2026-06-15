---
name: feedback_v_class_post_implementation_verification
description: "V-class = a single post-implementation verification pass that RUNS the dedicated skills + sanitizers on the SHIPPED code before commit (the M8 arm); I-class/A-class are pre-coding, V-class is post-coding"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 740c737e-bb42-40db-90db-3b6f6b3b07dc
  sister_specs: [feedback_define_done_and_arm_scout_subagents.md, feedback_run_dedicated_audit_skills_not_just_armed_prompts.md]
  tags: []
---

After implementing (and BEFORE committing), run a single **V-class** verification pass — the post-coding complement to the pre-coding I-class (investigative) + A-class (adversarial). The V-class RUNS the dedicated skills + gates on the ACTUAL shipped code, not the design:

- build (all touched targets: test + gui + suite), char-tests green
- **sanitizers (asan + ubsan)** — the gate most likely to be skipped + most likely to catch a latent bug; a per-IMPLEMENTATION run, NOT deferred to ship-close
- `calls_graph_diff` (hot-path UNTOUCHED) + `check_session_docs` (doc-CI)
- the DOMAIN audit skills on the SHIPPED code (`/dod-audit` / `/hft-audit` / `/accounting-audit` / `/ml-audit` as the surface matches) — verify the CODE matches the design the pre-coding audits blessed
- returns a Definition-of-Done verdict (M8): code+producer / test-per-fix / sanitizers / hot-path / parity / promises-honored / docs-indexed / meta-codified

**Why:** the M8 close-out discipline says a ship TERMINATES only when an enumerated DoD is verified — the V-class IS that verification, applied per-implementation. Caught at A6 (2026-06-15): ASan (run as the careful path) surfaced a PRE-EXISTING latent heap-use-after-free (TECH_DEBT-202, the OMS async-writer-not-joined UAF) that the normal suite missed + that ASan-at-ship-close-only would have deferred to the .E.0.10 close. The gap: sanitizers + domain-audits-on-shipped-code were AD-HOC (depended on the implementer remembering to run them), not a codified post-implementation pass. Structural-enforcement-when-memory-insufficient (M7): make it a pass, not a habit.

**How to apply:** after a substantive implementation, before commit, run the V-class — a single pass composing the gates + the surface-matched domain skills, returning the DoD verdict. The methodology BODY is now the DESIGN_SPEC `DESIGN_SPECS/audit-methodologies/post-implementation-verification-v-class.md` (Stage 2 DRAFT; A6 = first canonical) — this memory is its operator-collaboration trigger. The remaining codification is the SKILL: build `/verify-implementation` (OR extend `/post-ship-audit` to a PRE-commit mode) + add **V** to the I-class/A-class fan-out vocab (I→A→build→V). Good idea, NOT ceremony — it caught a real UAF. Sister: M8 (`definition-of-done-and-armed-scout-verification`), `feedback_run_dedicated_audit_skills_not_just_armed_prompts` (the V-class RUNS the skills, doesn't approximate them), `/post-ship-audit` (post-ship retrospective — V-class is its pre-commit sibling), `/ship` (the V-class runs BEFORE /ship's commit). [[feedback_define_done_and_arm_scout_subagents]] · [[feedback_run_dedicated_audit_skills_not_just_armed_prompts]]
