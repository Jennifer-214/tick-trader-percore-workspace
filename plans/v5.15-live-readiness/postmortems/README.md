# Postmortems — historical record (terminology preserved)

These postmortems are **historical record**. They use the terminology current when each was written — including `per-core` / `Core` / `MAX_CORES` / standalone `drainer` for pre-`v5.15.5.F.4d.1.E.1` ships.

**They are NOT rewritten when the architecture renames** (per `feedback_terminology_evolution_bridge_not_history_rewrite`). Rewriting history would falsify the evolution record and break `.E.1`'s "rename Core→Node" narrative coherence (you can't "rename per-core→per-node" if the history already says per-node).

**Reading older postmortems:** `per-core` ≈ today's `per-node`; the standalone `drainer` was absorbed into the per-node slow-path at `.E.1`. The canonical bridge is **`DOCS/DESIGN_PHILOSOPHY.md` § 15 Glossary** (terminology-evolution note). Code symbols (`CoreContext`, `MAX_CORES`, `state.cores`, `FOREACH_PER_CORE_CFG_FIELD`, cfg-field names) keep their `Core*` names in these records until `.E.1` renames the code itself.
