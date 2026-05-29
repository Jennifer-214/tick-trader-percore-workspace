---
type: handoff-template
scope: .E sub-sprint per-ship planning handoffs (one context window per ship)
established: 2026-05-28 (operator one-context-window-per-plan workflow; task #22)
extends: /handoff — adds .E-specific findings_sidecar + cross-ship-invariant + per-finding-fix-design-status sections
---

# `.E`-ship planning-handoff template

**Workflow:** one dedicated context window per `.E` ship (E.0 → E.1 → E.2 → …) for maximum planning depth; chained by this template. Copy → fill placeholders → save as `<YYYY-MM-DD>-<ship-tag>-handoff.md`. Receiver opens a fresh window and runs `/accept-handoff <path>`.

**Why a template (vs generic /handoff):** the `.E` ships share a structure — each ingests a routed findings sidecar, must preserve cross-ship invariants, and lays per-finding fix-designs in its own plan body. This template pre-wires those so no `.E` window starts cold or forgets its findings.

---

## 1. Ship scope + end goal
`<ship-tag>` — `<1 sentence: what surface closes / what capability lands>`. Predecessor: `<tag>`. Successor: `<tag>`. Audit tier: `<HIGH/MED/LOW>`.

## 2. Git state (pickup verify)
Engine HEAD `<sha>` (+ predecessor tag `<tag>`); workspace HEAD `<sha>`; branch `<branch>`; rollback anchor `<pre-tag>`.

## 3. Findings sidecar + per-finding fix-design status  ⟵ the .E-specific core
`findings_sidecar: <path>`. Per-finding table: `id | severity | fix-design status (pending/designed/landed) | lands at <ship>`.
**Discipline:** runtime-confirm provisionals on a disposable clone BEFORE writing any test/CI (never a test for an unconfirmed bug). PERSIST findings (behavior `.E` keeps) → characterization tests BEFORE the rename; CHANGES-BY-DESIGN findings (behavior `.E` alters) → new-invariant test AS PART of the ship.

## 4. Cross-ship invariants this ship must preserve
From `E-dependency-graph`: `<the slice relevant to this ship — what upstream ships established that this ship must not break>`.

## 5. Required reading (ship surface)
`<this ship's plan body>` + `<surface DESIGN_SPECS>` + `<relevant decision-log D-entries>` + `_SESSION-CONTEXT.md` (audit pickup) + `E-MASTER-REFERENCE.md`. Plus CLAUDE.md / CLAUDE.local.md / MEMORY.md baseline (auto).

## 6. Pre-coding gate
Fire `/precoding-audit-gate` at the declared tier (+ `/blindspot-scan` if struct-gen / type-unification / cross-registry consumer / wire-format ordering). Consult before coding (`feedback_consult_on_audit_findings`).

## 7. Verification gate
Acceptance criteria: CLOSED bug classes / CLOSED TECH_DEBT / LANDED DESIGN_SPECs / hot-path-untouched (or TOUCHED-WITH-CHANGELOG) / build all 5 binaries / tests baseline + NEW. **Tests-changed section** (per `/readiness` Check 45). Tie-back: how this ship advances the sprint MASTER goal.

---

## Pickup
`/accept-handoff <this-handoff-path>` → loads cited reads + runs `/capture-audit --deep` + `/readiness` + recreates TaskList + verifies git state + outputs PICKUP-READY + concrete next action.
