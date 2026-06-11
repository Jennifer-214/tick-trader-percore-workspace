---
type: handoff
date: 2026-06-10
status: active
ship_context: post-Ship-B (v5.15.5.F.4d.1.E.0.9 SHIPPED)
---

# Handoff — Ship B SHIPPED; `.E.0` phase COMPLETE; next = `.E.1` Foundation (Core→Node)

**State:** Ship B (decimal money) CLOSED 2026-06-10 — tag `v5.15.5.F.4d.1.E.0.9`, engine
`c2d0987` (ship commit `830615c` + 2 post-ship close-review commits: D-175 lot_max_qty clamp
on both submit paths + D-173 commission-branch tests + CMake orphan-endif fix; chain + tags
PUSHED). Suite **3285/0**; **Check-F GREEN un-bypassed** (D-157 closed); golden refrozen
(deliberate D-100 epoch); FP64 absorbed. Decision log D-168..D-189 is the SSoT;
postmortem `postmortems/2026-06-10-v5.15.5.F.4d.1.E.0.9-ship-b-postmortem.md`.

**Your immediate next action:** the **`.E.0` phase is COMPLETE** — both pre-pipeline
foundational ships SHIPPED (`.E.0.1` FP+replay determinism net = tag `.E.0.6`, 2026-05-31;
`.E.0.2` meta-error-tracking subsystem [D-76] = tag `.E.0.5`, 2026-05-30) plus the numeric
core (Ship A/A.5/B = `.E.0.7/.8/.9`). Genuine next = **`.E.1` Foundation: Core→Node rename
+ per-node drainer absorption + multi-exchange registry** (rename-ship-methodology Stage 3;
TECH_DEBT-142 closes there). The `.E.1` plan body is v0.1, pre-audit-gate (RED per dive) →
**amend + `/precoding-audit-gate` HIGH-RISK BEFORE coding.** PRE-`.E.1` GATES to verify first
(per the `.E.0.5` postmortem DoD / D-78): **Net-1** PERSIST characterization + golden-master
on the CURRENT engine + **guard-coverage-matrix no-HOLE** for the surfaces `.E.1` touches.

**Deliberate Ship-B residue (riding .E.3):** OrderResult double vehicle (S-8 scaled-i64),
commission-asset string-direct parse, BNB boot-query + runtime guard (D-173 full two-layer),
TD-149 residual (TUI/depth/recorder doubles). The fold stays gross-of-fee (S-3 slot ready).

**Known-unverified (operator-descoped 2026-06-10):** the GUI/suite build configs
(`build.sh gui` / `suite`) were NOT compiled post-flip — the GUI decouples at `.E.2`
anyway (operator call). Expect possible flip-residue compile fixes in
SettingsPanel/EngineTUI/BacktestPanels the first time those targets build. Sanitizer
lanes (tsan/asan/ubsan) also not re-run this ship — semantic flip, no new memory shapes;
re-run at the next sanitizer-cadence ship.

**Critical pickup-time reads:** decision-log Session-13/14 addenda + the postmortem +
`plan_checks/2026-06-10-p2b-flip-work-order.md` (the executed record). Resume `/accept-handoff`.
