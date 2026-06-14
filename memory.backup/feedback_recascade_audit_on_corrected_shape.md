---
name: feedback_recascade_audit_on_corrected_shape
description: "When a pre-coding fan-out reveals the SUPPLIED shape (handoff/register/spec seams) was materially WRONG, re-cascade I+A on the CORRECTED shape before building — don't build on the discovery pass's now-invalidated frame."
metadata: 
  node_type: memory
  type: feedback
  tags: [audit-methodology]
  sister_specs: [feedback_a_class_i_class_fanout_vocab.md, feedback_adversarial_framing_default_for_checks.md, feedback_compaction_degrades_treat_handoffs_as_hints.md, feedback_ground_design_in_real_code.md]
  originSessionId: 6842ea9a-ef46-4122-b6c2-94c834863ba2
---

A pre-coding fan-out armed with SUPPLIED facts (a handoff's cited seams, a register's finding shape, a discipline-doc's worked-example line numbers) can discover the supplied shape is materially WRONG — seams stale/wrong-path, the task smaller/different than described, the "keystone" largely duplicating existing work. The FIRST (discovery) pass's design is then built on an invalidated frame. **Re-cascade: re-run I-class (map/design) → A-class (refute) on the CORRECTED shape before building.** The discovery pass found WHAT the shape is; the second cascade designs the work RIGHT on the true shape (and any operator-requested lens — e.g. HFT/DOD — applies to the corrected design, not the wrong one).

**Why:** worked at F-059 (2026-06-14, `.E.0.10`). The handoff + register + `characterization-test-discipline.md` ALL carried the same stale F-059 seams (`Portfolio.hpp:201-203` single_core-only; `ControllerEventLoop.hpp:1873-1890` slip block deleted by A9; the real production exit path `handle_sell_fill`+`DrainPostFillOneCore` unnamed) AND the "keystone" largely duplicated `oms-ts-1`/`1b`+A9+A25. The first I+A fan-out CAUGHT it — the A-class corrected the I-class AND the orchestrator's own "✅ CURRENT" seam calls. Building on the supplied shape would have produced a wrong-path, duplicative, partly-false-green test; the re-cascade designed it right (the per-core exit gap + reconciliation + slip-into-net).

**How to apply:** (1) A pre-coding fan-out's FIRST job = verify the supplied shape against code ([[feedback_ground_design_in_real_code]]); supplied artifacts drift ([[feedback_compaction_degrades_treat_handoffs_as_hints]]). (2) Shape holds → design. (3) Shape materially wrong → capture the correction at the SSoT (the register) + fix the stale supplied docs (spec/handoff) + THEN re-cascade I+A on the corrected shape before writing code. (4) Don't treat the discovery pass's mid-flight design as final — it reasoned from the wrong frame. The A-class is what catches the wrong shape ([[feedback_adversarial_framing_default_for_checks]]); the I/A roles + the two meanings of "cascade" are in [[feedback_a_class_i_class_fanout_vocab]].
