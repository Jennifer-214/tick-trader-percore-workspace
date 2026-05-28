---
name: forward-promise-auto-write-verification
description: "When ship close promises an auto-write (PARITY entry / TECH_DEBT / catalog amendment / Stage promotion / next-ship-deferred work), next-ship verify it landed at expected ledger location. Catches forward-promise drift."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 219ed0c3-e701-4643-ab2e-f475f7b60f64
---

When a ship close promises an auto-write — PARITY entry / TECH_DEBT entry / catalog amendment / DESIGN_SPEC Stage promotion / Stage 6 escalation candidate — verify at next-ship-time that the promised auto-write actually landed at the expected ledger location.

**Why:** /blindspot-scan caught MED-6 finding at v5.15.5.F.4d.1.B.8 — `.B.7` Class 26 catalog line 98 promised DOCUMENTED-RISK PARITY entry advisory ("Forward advisory (PARITY ledger DOCUMENTED-RISK entry at .B.7 close)") for `partial_exit_pct` / `tp2_mult` historical calibration tainted-results, but the entry was never actually written to `DOCS/PARITY_ISSUES.md`. Forward-promise drift is silent — the catalog cites the entry's existence but the entry doesn't exist. Future readers + audit tools encounter the dangling reference.

**How to apply:** At each ship close + at next-ship pickup:
1. Grep prior ship's catalog amendments + postmortems + plan-body close-out sections for forward-promise sentinels: "forward advisory" / "DOCUMENTED-RISK entry at .X close" / "Stage 6 escalation candidate at .X" / "auto-write at ship close: ..." / "queued for .X" / "deferred to .X"
2. For each promised auto-write, verify it landed at expected ledger location (PARITY_ISSUES.md / TECH_DEBT.md / DESIGN_SPECS / MEMORY.md / Class catalog / etc.)
3. Surface UNFULFILLED forward-promises for retroactive closure at current ship OR explicit decision (re-defer with rationale / abandon with rationale / land now)

**Mechanical enforcement:** `/capture-audit` Check 11 (NEW v5.15.5.F.4d.1.B.8 — codified inline at Phase H.2.c) scans prior N ships (default 3) for forward-promise sentinels + verifies landing.

**Worked examples:**
- v5.15.5.F.4d.1.B.8 Phase G Step G.6 retroactively closes `.B.7` forward-promise (writes the DOCUMENTED-RISK PARITY entry that `.B.7` Class 26 catalog promised but never landed)
- v5.15.5.F.4d.1.B.8 Phase G Step G.7 (Check 11 dogfood) verifies `.B.8` own forward-promises (Stage 2 → 3 promotion candidates + Check 11 self-verification) are tracked
- Pattern application: at each ship close, /handoff Stage 1.8 invokes /capture-audit --deep which runs Check 11 against prior ship forward-promises

**Sister disciplines:**
- [[feedback_structural_enforcement_when_memory_insufficient]] (parent M7 meta-discipline; Check 11 IS the structural enforcement)
- [[feedback_sister_cohort_amendment_completeness]] (sister at AMENDMENT layer; both catch silent drift)
- [[feedback_compaction_degrades_treat_handoffs_as_hints]] (sister discipline; handoff doc forward-promises also need verification at next session)
- `claude-skills/capture-audit/SKILL.md` Check 11 (NEW codification at v5.15.5.F.4d.1.B.8)

**Stage 6 candidate framing:** memory codification alone insufficient for next-ship forward-promise tracking (operator can forget; AI session boundary loses context). Check 11 structural enforcement at commit-time per `/capture-audit --deep` invocation closes the loop.

**Lifecycle:** **Stage 3 first canonical promotion at v5.15.5.F.4d.1.D** (2026-05-28). The structural enforcement landing — NEW `tools/check_forward_promise_audit.py` (Check 11 Python detection logic; ~800 LOC; 24 sentinel patterns; 24 verifier functions) — IS the mechanical instantiation of this discipline. Two canonical applications now: (1) v5.15.5.F.4d.1.B.8 Phase G Step G.6 retroactive PARITY-033 closure of .B.7 forward-promise via discipline application; (2) v5.15.5.F.4d.1.D Phase B+F Check 11 Python implementation + skill integration (the mechanical-enforcement landing). Stage 4 cohort migration promotion at next ship surface OR after 3+ months operator use proving the discipline holds.
