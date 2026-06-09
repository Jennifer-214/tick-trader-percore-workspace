---
type: running-list
sprint: v5.15-live-readiness
sub_sprint: v5.15.5.F.4d.1.E
established: 2026-05-28
status: living-list (accumulates throughout .E sub-sprint; entries close as their target ships land)
purpose: Track rename candidates surfaced throughout .E sub-sprint per `feedback_proactive_rename_candidate_surfacing`
discipline: feedback_proactive_rename_candidate_surfacing
canonical_glossary: DOCS/DESIGN_PHILOSOPHY.md § Glossary (anchor lands at .D.1)
sister_memory: feedback_proactive_rename_candidate_surfacing.md
---

# Rename candidates running list — `.E` sub-sprint

**Purpose:** Single source of truth for rename candidates surfaced throughout the `.E` sub-sprint. Each entry classified per severity tier; closed as target ship lands.

**Discipline:** New entries get added as discovered (audit / plan body review / code reading / DESIGN_SPECS sweep / etc.). At every ship's planning gate, scan list for items fitting current scope.

---

## Severity tiers (legend)

- **CLOSE-NOW** — small + clear + fits current ship scope; rename inline
- **QUEUE-FOR-NEXT-RENAME-SHIP** — substantive + clear new target; surface as forward-promise
- **TECH_DEBT-DEFER** — substantive + needs operator triage; TECH_DEBT entry + queue at named future ship
- **AMBIGUOUS** — surface with both-sides analysis; operator decides
- **CLOSED** — resolved; ship that closed it noted

---

## Active candidates

| # | Surface | Old name | Suggested new | Tier | Rationale | Target ship |
|---|---|---|---|---|---|---|
| 1 | Throughout codebase (~5000+ touch sites) | `state.cores[]` / `CoreContext` / `MAX_CORES` / `FOREACH_PER_CORE_CFG_FIELD` / `core_*` cfg fields | `state.nodes[]` / `NodeContext` / `MAX_NODES` / `FOREACH_PER_NODE_CFG_FIELD` / `node_*` | QUEUE-FOR-NEXT-RENAME-SHIP | Core→Node rename per Cluster/Node/Deployment hierarchy; D-27 decision | `.E.1` Foundation |
| 2 | `cfg.engine_mode` field | `engine_mode` (values: `sharded \| single_core`) | DELETE (vestigial) | QUEUE-FOR-NEXT-RENAME-SHIP | With `single_core` legacy deleted in `.E.0.1`, only one value remains; field is vestigial | `.E.0.1` precursor OR `.E.1` |
| 3 | `cfg.engine_arch` field | `engine_arch` (values: `per_core_slow \| centralized`) | **CLOSED — DELETED at `.B.4`** | CLOSED | Per `.D.1` cycle 1 trace-deps audit (2026-05-28): engine_arch field was already deleted at v5.15.5.F.4d.1.B.4 B14 first-canonical SHARDED-centralized 51-site deletion cohort. Surviving refs in archived/historical only; no rename or deletion candidate. | `.B.4` (closed) |
| 4 | `Backtest_Run` wrapper calling `BacktestSharded_Run` | `BacktestSharded_Run` | `Backtest_Run` (direct; no wrapper) | QUEUE-FOR-NEXT-RENAME-SHIP | With single_core gone, "Sharded" qualifier dead weight; unify | `.E.1` Foundation |
| 5 | `EngineSharded/` directory + namespace | `EngineSharded` | AMBIGUOUS — `Engine/` direct OR keep `EngineSharded` as historical | AMBIGUOUS | `Sharded` was differentiator from `EngineSingleCore`; with SingleCore gone, qualifier is dead weight BUT rename touches ~50-100 sites; operator call | TBD |
| 6 | `per-core risk-sharded` (tagline; CLAUDE.md + README + DESIGN_PHILOSOPHY) | `per-core risk-sharded` | `per-node risk-sharded` | CLOSE-NOW (in `.D.1`) | Narrative tagline update | `.D.1` doc sweep |
| 7 | `per-core ML model` (cfg refs in docs + DESIGN_SPECS) | `per-core ML model` | `per-node ML model` | CLOSE-NOW (in `.D.1`) for narrative; `.E.1` for cfg-field names | `.D.1` (narrative) + `.E.1` (cfg-field actual rename) |
| 8 | `per_core_slow` (cfg term + narrative) | `per_core_slow` | `per_node_slow` (or just delete the cfg if only mode) | QUEUE-FOR-NEXT-RENAME-SHIP | Architecture-naming consistency | `.E.1` Foundation |
| 9 | `single_core` doc references | `single_core` | DELETE references entirely | CLOSE-NOW (in `.D.1` once `.E.0.1` confirmed) | Deprecated mode being deleted; doc refs become misleading | `.D.1` doc sweep |
| 10 | `tools/check_per_core_registry_integrity.py` | `check_per_core_registry_integrity.py` | `check_per_node_registry_integrity.py` (rename + update internal logic to validate per-NODE-registry post-`.E.1` Core→Node rename) | QUEUE-FOR-NEXT-RENAME-SHIP | NAME-LEVEL COUPLING to per-core terminology; per N4 cycle 1 audit of `.D.1` (2026-05-28) sister-tool cohort completeness. Rename happens alongside engine code rename, NOT after. | `.E.1` Foundation |
| 11 | Other CI tools internal-logic updates (NOT renames) | `check_meta_registry.py`, `check_field_name_uniqueness.py`, `check_struct_field_uniqueness.py`, `check_storage_t_coverage.py`, `check_plan_body_symbol_existence.py`, `check_doc_metadata.py`, `check_forward_promise_audit.py` | Internal logic updated to validate per-NODE invariants post-rename + new sentinels for `.D.1` forward-promises | QUEUE-FOR-NEXT-RENAME-SHIP | Sister-tool cohort enumerated at `.D.1` Phase A.7 (per N4 cycle 1 audit). | `.E.1` Foundation (internal logic) + `.D.1` ship close (sentinels in `check_forward_promise_audit.py`) |
| 12 | FixedPoint binary core type spelling (2,439 bare-token lines engine+tests+tools; 39 `is_FPN_v` sites / 6 files, gate-corrected per S-3 — incl. 2 Python guard lines in `check_storage_t_coverage.py:86-87` outside the compiler oracle) | `FPN` / `is_FPN_v` | `FPN_Binary` / `is_fp_binary_v` | QUEUE-FOR-NEXT-RENAME-SHIP (IN-FLIGHT at A.5) | D-143 naming (binary/decimal public faces, settled BEFORE Ship-B decimal lands); deferred out of Ship A to preserve the 16B diff-anchor. `FPN_*` fn family (40 names, ≈2.8k refs) + FixedPoint64 absorb stay Ship-B (D-163). Added at A.5 planning 2026-06-09 — the decided rename was missing from this SSoT list. | **A.5 = `v5.15.5.F.4d.1.E.0.8` (this ship)** |

---

## Closed candidates

(Section to fill as candidates close)

| # | Surface | Closed at | Notes |
|---|---|---|---|

---

## Ambiguous / pending operator triage

| # | Surface | Question | Tier consideration |
|---|---|---|---|
| 5 (above) | `EngineSharded/` directory + namespace | Rename to `Engine/` (cleaner; ~50-100 site touches) OR keep `EngineSharded` (historical-naming continuity; matches `.E.1` per-NODE-sharded framing) | Operator preference; both have merits |

---

## Surfaces to scan as `.E` progresses (proactive triggers)

When working in these areas, scan for rename candidates:

- **Per-core ML model paths** (`core_N_model_path`) — likely rename to `node_N_model_path` at `.E.1`
- **Per-core risk percentages** (`core_N_risk_pct`) — likely rename to `node_N_risk_pct` at `.E.1`
- **Per-core ConfidenceScorer** — does the type name need renaming? (`PerCoreScorer` → `PerNodeScorer`?)
- **Per-core slow_state** (`slow_state`) — owning struct in NodeState? rename to `node_slow_state`?
- **Drainer** terminology — being absorbed into per-node at `.E.1`; doc refs need pruning
- **`fan_out`** producer behavior — preserve naming (canonical producer pattern) OR rename for clarity?
- **`engine_gui` binary** — being archived at `.E.2`; doc refs become historical
- **`foxml_suite` binary** — being archived at `.E.2`; replaced by `foxml-train` CLI
- **Single-vs-sharded backtest** — only sharded remains; `Backtest_*` family unification
- **Per-symbol ↔ per-cluster** — when sub-accounts land, per-symbol may become per-cluster per-symbol; surface terminology shifts

---

## Process notes

- Each new candidate gets a row above with tier + rationale + target ship
- At ship planning gate: scan list for items fitting current scope; bulk-close where reasonable
- AMBIGUOUS items: surface to operator for both-sides analysis; tier upgrade when decided
- After ship close: move closed items to "Closed candidates" section with closure notes
- Reference glossary at `DOCS/DESIGN_PHILOSOPHY.md § Glossary` for canonical target terminology (lands at `.D.1`)
- Per `feedback_proactive_rename_candidate_surfacing` sister-cohort discipline: when renaming X, enumerate all sister surfaces (docs + code + tests + plan bodies + memory)

---

**End of running list v1.0** (established 2026-05-28; living document throughout `.E` sub-sprint).
