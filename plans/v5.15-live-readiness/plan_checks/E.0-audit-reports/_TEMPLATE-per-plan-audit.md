---
type: audit-report
audit_ship: v5.15.5.F.4d.1.E.0
target_plan: <PLAN_PATH>
audit_cycle: 1 | 2 | 3
audit_date: YYYY-MM-DD
audit_type: precoding-audit-gate-HIGH-RISK
auditor_agents:
  - parity-check
  - trace-deps
  - dod-audit
  - readiness
  - blindspot-scan
verdict: GREEN-READY-TO-CODE | YELLOW-AMEND-RECOMMENDED | RED-BLOCKING-FIX
---

# Audit Report: <Plan Title> (Cycle <N>)

**Audit ship:** v5.15.5.F.4d.1.E.0
**Target plan:** <path-to-plan-body>
**Cycle:** <N>
**Auditor agents:** 5 (parity-check + trace-deps + dod-audit + readiness + blindspot-scan)

---

## Audit invocation

```
/precoding-audit-gate <target_plan_path>
```

Or per-agent:
- `/parity-check --scope plan-body --plan <target>`
- `/trace-deps --plan <target>`
- `/dod-audit --plan <target>`
- `/readiness <target>`
- `/blindspot-scan --plan <target>`

---

## Per-agent findings

### parity-check

**Verdict:** GREEN / YELLOW / RED
**Finding count:** N (HIGH: X / MED: Y / LOW: Z)

| # | Severity | Description | Triage |
|---|---|---|---|
| 1 | HIGH | <finding-1> | FIX-NOW / ACCEPT / DEFER |
| 2 | MED | <finding-2> | ... |

### trace-deps

**Verdict:** ...
**Finding count:** ...

| # | Severity | Description | Triage |
|---|---|---|---|
| ... |

### dod-audit

**Verdict:** ...
**Finding count:** ...

| # | Severity | Description | Triage |
|---|---|---|---|
| ... |

### readiness

**Verdict:** ...
**Finding count:** ...

10-item checklist results:
- Item 1: PASS / FAIL / N-A
- Item 2: ...
- ...

### blindspot-scan

**Verdict:** ...
**Finding count:** ...

Per 12-pillar taxonomy:
- B1 ...
- B2 ...
- ...

---

## Synthesis

### Convergent findings (across multiple audits)

| Finding | Surfaced by | Triage |
|---|---|---|
| <convergent finding-1> | parity-check + trace-deps | FIX-NOW |
| ... | ... | ... |

### Per-finding triage decision

| Finding | Severity | Decision | Plan amendment? | Sentinel |
|---|---|---|---|---|
| 1 | HIGH | FIX-NOW | YES | <!-- D/C/F: D-XX --> |
| 2 | MED | ACCEPT WITH RATIONALE | NO | (decision log entry; deferred) |
| ... | ... | ... | ... | ... |

---

## Cycle <N> verdict

**Overall:** GREEN-READY-TO-CODE / YELLOW-AMEND-RECOMMENDED / RED-BLOCKING-FIX

**If YELLOW:** what amendments needed; expected cycle <N+1> result.
**If RED:** what must be resolved before any cycle <N+1>.

---

## Action items (for operator triage)

- [ ] Fold finding-1 into plan body amendment
- [ ] Accept finding-2 with rationale documented in decision log
- [ ] Defer finding-3 to `.F` audit sweep (capture as TECH_DEBT)
- [ ] ...

---

## Re-fire criteria (cycle <N+1>)

Cycle <N+1> required if:
- Any RED-BLOCKING findings remain
- HIGH findings triaged FIX-NOW + plan body amended
- Substantive plan body amendment (changes architectural decision; rescopes phase)

Cycle <N+1> NOT required if:
- All findings triaged ACCEPT or DEFER
- Plan body not substantively amended
- Operator explicitly accepts findings without amendment

---

**End of per-plan audit report template.**
