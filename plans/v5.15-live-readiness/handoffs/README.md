# Handoffs — historical record (terminology preserved)

These handoff docs are **historical record** — each captured the state at a specific session boundary. They use the terminology current when written — including `per-core` / `Core` / `MAX_CORES` / standalone `drainer` for pre-`v5.15.5.F.4d.1.E.1` ships.

**They are NOT rewritten when the architecture renames** (per `feedback_terminology_evolution_bridge_not_history_rewrite`). A handoff describes a point-in-time; rewriting it would falsify what was true at pickup and break `.E.1`'s "rename Core→Node" narrative coherence.

**Reading older handoffs:** `per-core` ≈ today's `per-node`; the standalone `drainer` was absorbed into the per-node slow-path at `.E.1`. The canonical bridge is **`DOCS/DESIGN_PHILOSOPHY.md` § 15 Glossary** (terminology-evolution note). Code symbols keep their `Core*` names in these records until `.E.1` renames the code.
