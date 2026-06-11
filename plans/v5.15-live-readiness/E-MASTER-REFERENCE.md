---
type: master-reference
sub_sprint: v5.15.5.F.4d.1.E
sprint: v5.15-live-readiness
established: 2026-05-28
status: living-index (updated as artifacts created + referenced)
purpose: Single-point-of-access reference index for the entire .E sub-sprint trajectory
---

# v5.15.5.F.4d.1.E sub-sprint — MASTER REFERENCE INDEX

**Use this file to find anything related to the `.E` sub-sprint.** Plan bodies, decision logs, DESIGN_SPECS, supporting documentation, audit reports — all indexed here with links.

**Sub-sprint shape (final per D-58 + D-59):**

```
.E.0 Pre-coding plan audit + verification    (NEW per D-59; precedes all coding; LOW-RISK; ~3-5d)
  ↓ blocks all subsequent
.E.0.1 Pre-`.E.1` foundational-fix net (Net-2) (NEW per D-74; FP+replay determinism; HIGH-RISK; ~3-5d)
.E.0.2 Meta-error-tracking subsystem           (NEW per D-76; catalog + cascade-audit + close-out harvest + hardened /precoding-audit-gate [Piece 4; D-77/D-78]; MED; process-infra, no engine code — Phase-1, before pipeline)
  ↓ gates .E.1 (determinism + replay CI gates GREEN)
.E.1 Foundation                              (HIGH-RISK; ~5-7d)
  ↓
.E.2 Headless + configs + docs               (HIGH-RISK; ~10-14d)
  ↓
.E.3 WS-API + persistent connections         (MED-HIGH; ~5-7d)
  ↓
.E.4 io_uring + kTLS                        (HIGH-RISK; ~7-10d)
  ↓
.E.5 Real sub-accounts + capital            (MED; ~3-5d)
  ↓
.E.6 Exchange adapter framework gen.        (MED-LOW; ~3-5d; repurposed per D-58)
  ↓
.E.X Strategy hot-reload (standalone)       (MED; ~3-5d; slots anywhere after .E.2)
.E.7 IBKR (OPTIONAL-FUTURE; ~7-10d)         (deferred; reference example for FIX-protocol exchanges)
.E.8 DPDK (DEFERRED INDEFINITELY)           (deferred; no operator hardware; reference)
```

**Total `.E` sub-sprint effort:** ~25-35 days focused work (excluding deferred ships).

**▶ STATUS (2026-06-10):** the `.E.0` phase is COMPLETE — `.E.0` audit + `.E.0.1` determinism net (tag `.E.0.6`) + `.E.0.2` meta-error-tracking (tag `.E.0.5`) + the numeric core (Ship A/A.5/B = tags `.E.0.7/.8/.9`) all SHIPPED. **NEXT = `.E.1` Foundation** (Core→Node rename + per-node drainer absorption + multi-exchange registry; v0.1 plan, pre-audit-gate). Pre-`.E.1` gates per the `.E.0.5` DoD (D-78): **Net-1** PERSIST characterization + golden-master on the current engine + **guard-coverage-matrix no-HOLE** for the surfaces `.E.1` touches.

---

## 1. Plan body documents

### Active ships (will be coded)

| Ship | Plan body | Status |
|---|---|---|
| `.E.0` | `subplans/2026-05-28-v5.15.5.F.4d.1.E.0-precoding-plan-audit-verification.md` | ✅ EXECUTED (read-only audit phase; 141 findings → Net-1/Net-2 scope + Classes 37+) |
| `.E.0.1` | `subplans/2026-05-29-v5.15.5.F.4d.1.E.0.1-pre-E1-foundational-fix-net.md` | ✅ SHIPPED 2026-05-31 as tag `.E.0.6` (Net-2; FP+replay+locale determinism net; standing CI gates) |
| `.E.0.2` | `subplans/2026-05-29-v5.15.5.F.4d.1.E.0.2-meta-error-tracking-subsystem.md` | ✅ SHIPPED 2026-05-30 as tag `.E.0.5` (4 pieces: catalog `meta-anti-pattern-index.md` + /capture-audit Check 12 + /close-session harvest Stage 4.5/5.5 + hardened /precoding-audit-gate; close-G verified) |
| `.E.1` | `subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md` | DRAFTED v0.1 (substantial; ~3600 lines; RED per dive — amendment-bound) |
| `.E.2` | `subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md` | DRAFTED v0.1 |
| `.E.3` | `subplans/2026-05-28-v5.15.5.F.4d.1.E.3-ws-api-persistent-connections.md` | DRAFTED v0.1 (substantial; ~2500 lines) |
| `.E.4` | `subplans/2026-05-28-v5.15.5.F.4d.1.E.4-io-uring-ktls.md` | DRAFTED v0.1 (partial; Coding Sequence needs fix) |
| `.E.5` | `subplans/2026-05-28-v5.15.5.F.4d.1.E.5-real-subaccounts-capital-framework.md` | DRAFTED v0.1 (substantial; ~2000+ lines) |
| `.E.6` | `subplans/2026-05-28-v5.15.5.F.4d.1.E.6-alpaca-exchange.md` | DRAFTED v0.2 (REPURPOSED per D-58; framework focus + Alpaca worked example) |
| `.E.X` | `subplans/2026-05-28-v5.15.5.F.4d.1.E.X-strategy-hot-reload.md` | DRAFTED v0.1 (substantial; ~2000+ lines) |

### Deferred ships (retained as reference)

| Ship | Plan body | Status |
|---|---|---|
| `.E.7` | `subplans/2026-05-28-v5.15.5.F.4d.1.E.7-ibkr-exchange.md` | OPTIONAL-FUTURE; operator-triggered (per D-58) |
| `.E.8` | `subplans/2026-05-28-v5.15.5.F.4d.1.E.8-dpdk-kernel-bypass.md` | DEFERRED INDEFINITELY; no hardware (per D-57) |

---

## 2. Decision log + dependency graph

| Document | Path |
|---|---|
| Architectural decision log | `decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md` (D-1..D-60 + F-1..F-13 + C-1..C-6 + P-1..P-8) |
| Ship dependency graph | `subplans/2026-05-28-v5.15.5.F.4d.1.E-dependency-graph.md` |
| Original v1 decision log | `decision-logs/v5.15.5.F.4d.1.E-architecture-v1.md` (superseded by v2) |

---

## 3. NEW DESIGN_SPECS (Stage 2 DRAFT or Stage 3 first canonical at landing ship)

All NEW specs that land across `.E` sub-sprint. Stage 2 DRAFT skeletons created at `.E.0` for reference; Stage 3 first canonical content lands at the actual landing ship.

### From `.E.0` (this audit ship)

- `meta-disciplines/audit-driven-sub-sprint-trajectory-verification.md` — Stage 3 at `.E.0`

### From `.E.1` Foundation (12 NEW + 3 Stage 2 DRAFTs)

**framework-patterns/:**
- `foreach-exchange-meta-registry-pattern.md` — Stage 3
- `foreach-subaccount-meta-registry-pattern.md` — Stage 3
- `cluster-node-hierarchy-filesystem-layout-pattern.md` — Stage 3
- `per-cluster-shared-resource-pattern.md` — Stage 3
- `per-cluster-producer-pattern.md` — Stage 3
- `global-aggregator-readonly-pattern.md` — Stage 3
- `kill-switch-hierarchical-pattern.md` — Stage 3
- `per-node-paper-mode-flag-pattern.md` — Stage 3
- `runtime-mutable-vs-boot-time-config-pattern.md` — Stage 3
- `exchange-adapter-tt-dispatch-pattern.md` — Stage 3 (Binance canonical)
- `dev-vs-production-thread-topology-pattern.md` — Stage 3
- `event-sourced-aggregator-o1-pattern.md` — Stage 3 (per D-54)
- `crash-recovery-action-policy-pattern.md` — Stage 2 DRAFT (per D-47)
- `hybrid-reconciliation-cadence-pattern.md` — Stage 2 DRAFT (per D-50)
- `portfolio-soa-vectorization-pattern.md` — Stage 2 DRAFT (per D-55)

**meta-disciplines/:**
- `backtest-paper-live-convergence-discipline.md` — Stage 3

### From `.E.2` Headless + configs + docs (9 NEW + 1 Stage 2 promotion)

**meta-disciplines/:**
- `headless-engine-viewer-split-pattern.md` — Stage 3
- `gui-deprecation-decision-rationale.md` — Stage 3

**framework-patterns/:**
- `hierarchical-config-with-per-node-folders.md` — Stage 3
- `native-tui-via-mmap-readonly-pattern.md` — Stage 3
- `dual-format-metrics-publication-pattern.md` — Stage 3
- `crash-recovery-via-mmap-state-pattern.md` — Stage 3
- `hierarchical-config-validation-pattern.md` — Stage 3
- `built-in-observability-pattern.md` — Stage 3

**concurrency-patterns/:**
- `structured-audit-log-pattern.md` — Stage 3
- `spsc-vs-blackboard-selection-criteria.md` — Stage 3 (promoted from Stage 2 at .E.1; per D-56)

### From `.E.3` WS-API + persistent connections (3 NEW)

**concurrency-patterns/:**
- `persistent-ws-connection-management-pattern.md` — Stage 3

**framework-patterns/:**
- `per-exchange-submit-protocol-selection.md` — Stage 3
- `tls-session-resumption-pattern.md` — Stage 3

### From `.E.4` io_uring + kTLS (3 NEW)

**concurrency-patterns/:**
- `io-uring-kernel-bypass-pattern.md` — Stage 3
- `ktls-kernel-tls-pattern.md` — Stage 3

**framework-patterns/:**
- `per-node-io-rings-pattern.md` — Stage 3

### From `.E.5` Real sub-accounts + capital (2 NEW)

**framework-patterns/:**
- `per-node-economic-isolation-pattern.md` — Stage 3
- `capital-allocation-policy-pattern.md` — Stage 3

### From `.E.6` Exchange adapter framework generalization (1 NEW)

**framework-patterns/:**
- `exchange-adapter-implementation-contract.md` — Stage 3

### From `.E.X` Strategy hot-reload (2 NEW)

**framework-patterns/:**
- `strategy-hot-reload-via-dlopen-pattern.md` — Stage 3
- `dynamic-library-strategy-loading-pattern.md` — Stage 3

### From `.E.7` (DEFERRED; Stage 2 DRAFT only)

**framework-patterns/:**
- `fix-session-management-pattern.md` — Stage 2 DRAFT
- `multi-asset-class-symbol-pattern.md` — Stage 2 DRAFT
- `ibkr-fa-structure-pattern.md` — Stage 2 DRAFT

### From `.E.8` (DEFERRED; Stage 2 DRAFT only)

**concurrency-patterns/:**
- `dpdk-userspace-networking-pattern.md` — Stage 2 DRAFT
- `userspace-tls-pattern.md` — Stage 2 DRAFT

**framework-patterns/:**
- `kernel-vs-userspace-networking-cfg-pattern.md` — Stage 2 DRAFT

**Total NEW DESIGN_SPECS: ~38 (Stage 3 first canonical at landing ships) + 8 Stage 2 DRAFTs**

---

## 4. AMENDED existing DESIGN_SPECS

| Spec | Amendment | Landing ship |
|---|---|---|
| `concurrency-patterns/concurrency-model-summary.md` | Substantial rewrite (drainer removed; per-node owns trading flow; per-cluster shared resources; global aggregator) | `.E.1` |
| `data-disciplines/cache-line-discipline.md` | Stage 2 → Stage 3 promotion candidate (NodeState alignas(64) validated) | `.E.1` |
| `refactor-patterns/branchless-dispatch-discipline.md` | Extended with per-node strategy dispatch (fn-pointer-table) | `.E.1` |
| `framework-patterns/x-macro-registry-with-presence-dispatch.md` | FOREACH_EXCHANGE + FOREACH_SUBACCOUNT cited as 2nd + 3rd canonical applications | `.E.1` |
| `meta-disciplines/canonical-sister-extension-discipline.md` | Extended with BinanceAdapter-as-canonical-sister worked example | `.E.1` |
| `plan-templates/future-oriented-plan-template.md` | Added MANDATORY "Required reading + reference docs cross-check" section per D-52 | `.E.1` |

---

## 5. CLAUDE.md + DESIGN_PHILOSOPHY.md amendments

### CLAUDE.md (at .E.1 ship close)

- Concurrency model summary section — drainer removed; per-node + per-cluster + aggregator documented
- "How to find anything" section — FOREACH_EXCHANGE / FOREACH_SUBACCOUNT pattern queries added
- "How to ..." table — "Add a new exchange" entry pointing to `.E.6/.E.7` pattern
- Hard Invariants table — H20 reaffirmed extended to per-node dispatch
- Reference Docs (portal hierarchy) — cluster/node terminology adopted throughout

### DESIGN_PHILOSOPHY.md (at .E.1 ship close per D-46 + D-52 + D-53)

- § **Cluster/Node hierarchy** — Deployment > Cluster > Node terminology + structural meaning
- § **Multi-exchange substrate** — FOREACH_EXCHANGE + per-cluster adapter + per-cluster rate budget + per-cluster credentials
- § **Per-node economic isolation** — sub-accounts; exchange-enforced isolation; failure domain at economic layer
- § **Hot/slow path decoupling preserved** — each node = 2 CPU cores minimum; never collapse
- § **Power-user discipline** (preview for `.E.2`) — operator builds for self; CLI > GUI; mutable runtime > restart
- § **Backtest → paper → live transition discipline** — 4-step transition + drift sources per step

---

## 6. NEW supporting documentation (DOCS/ at `.E.2`)

### Operator-facing (per D-46)

| Doc | Path | Status |
|---|---|---|
| Deployment guide | `DOCS/DEPLOYMENT_GUIDE.md` | SKELETON (to be filled at `.E.2`) |
| Operator manual | `DOCS/OPERATOR_MANUAL.md` | SKELETON |
| Architecture overview | `DOCS/ARCHITECTURE_OVERVIEW.md` | SKELETON |
| Glossary | `DOCS/GLOSSARY.md` | SKELETON |
| Incident runbook | `DOCS/INCIDENT_RUNBOOK.md` | SKELETON |
| Strategy lifecycle | `DOCS/STRATEGY_LIFECYCLE.md` | SKELETON |
| Disaster recovery testing | `DOCS/DR_TESTING.md` | SKELETON |

### Contributing guides (per `.E.2`)

| Doc | Path | Status |
|---|---|---|
| How to add an exchange | `DOCS/CONTRIBUTING/add-exchange.md` | DRAFTED (substantial at `.E.6` deep-dive) |
| How to add a strategy | `DOCS/CONTRIBUTING/add-strategy.md` | DRAFTED |
| How to add a feature | `DOCS/CONTRIBUTING/add-feature.md` | DRAFTED |
| How to add a cfg field | `DOCS/CONTRIBUTING/add-cfg-field.md` | DRAFTED |
| How to add a design spec | `DOCS/CONTRIBUTING/add-design-spec.md` | DRAFTED |
| Build system | `DOCS/CONTRIBUTING/build-system.md` | DRAFTED |
| Testing strategy | `DOCS/CONTRIBUTING/testing-strategy.md` | DRAFTED |
| Audit workflow | `DOCS/CONTRIBUTING/audit-workflow.md` | DRAFTED |

### Additional supporting docs (NEW)

| Doc | Path | Status |
|---|---|---|
| Repo cleanup guide | `DOCS/REPO_CLEANUP_GUIDE.md` | DRAFTED |
| Security | `DOCS/SECURITY.md` | DRAFTED |
| Performance tuning | `DOCS/PERFORMANCE_TUNING.md` | DRAFTED |
| Migration from v5.X | `DOCS/MIGRATION_FROM_v5.X.md` | DRAFTED |
| Hardware requirements | `DOCS/HARDWARE_REQUIREMENTS.md` | DRAFTED |
| FAQ | `DOCS/FAQ.md` | DRAFTED |
| CHANGELOG v0.1 placeholder | `DOCS/CHANGELOG_v0.1.md` | DRAFTED (placeholder; filled at v0.1.0 close) |

### Audit templates + audit directory

| Doc | Path | Status |
|---|---|---|
| Per-plan audit template | `plans/v5.15-live-readiness/plan_checks/E.0-audit-reports/_TEMPLATE-per-plan-audit.md` | DRAFTED |
| Cross-ship synthesis template | `plans/v5.15-live-readiness/plan_checks/E.0-audit-reports/_TEMPLATE-cross-ship-synthesis.md` | DRAFTED |
| Audit directory README | `plans/v5.15-live-readiness/plan_checks/E.0-audit-reports/_README.md` | DRAFTED |

### Strategic / reference (final batch)

| Doc | Path | Status |
|---|---|---|
| Trajectory roadmap | `DOCS/ROADMAP.md` | DRAFTED (current → v0.1.0 → v0.2.0 → v6.X+) |
| Observability reference | `DOCS/OBSERVABILITY_REFERENCE.md` | DRAFTED (Prometheus metrics + Grafana queries + alerts) |

### NEW DESIGN_SPECS (promoted from memory in final batch)

- `meta-disciplines/iteration-spiral-signals-audit-meta-gap.md` (Stage 3; sister memory: feedback_iteration_spiral_signals_audit_meta_gap)
- `meta-disciplines/backwards-compat-not-default-concern.md` (Stage 3; sister memory: feedback_backwards_compat_not_default_concern)
- `data-disciplines/running-aggregate-vs-cycle-recompute-discipline.md` (Stage 2 DRAFT; sister: event-sourced-aggregator-o1-pattern)

### Deferred to post-`.E` separate session

| Doc | Reason |
|---|---|
| Public usage guide | Per operator clarification 2026-05-28; public-facing; separate session |
| QUICKSTART.md update for v0.1.0 | Existing v5.X version; refresh at `.E.2` ship close |
| README.md v0.1.0 refresh | `.E.2` ship close ritual |
| CHANGELOG.md per-ship rows | Written at each ship close |
| Per-ship postmortems | Written at each ship close |
| CFG_FIELD_REFERENCE.md / METRICS_REFERENCE.md | Auto-generatable from registries at `.E.2` |

---

## 7. NEW TECH_DEBT entries opened across `.E`

> ⚠️ **`.E.1` RENAME-APPROACH CONSTRAINT (TECH_DEBT-142, opened `.D.1` 2026-05-28):** the `.D.1` prose-token doc-rename tool (`check_doc_rename_classification.py`) is **structurally unsafe for `.E.1`'s ~5,000-site CODE rename** — it over-flags transition-docs / citations / current-state claims (proven at `.D.1` Phase F; see B19 pillar + Class 36). `.E.1` MUST design its Core→Node rename around **symbol/AST-aware** tooling (clang-based or equivalent), NOT prose-token substitution.

| Entry | Title | Source ship | Closure ship |
|---|---|---|---|
| **TECH_DEBT-142** (NEW `.D.1`) | **Doc-rename tool unsafe for `.E.1` code rename — needs symbol/AST tooling** | **`.D.1`** | **`.E.1`** |
| TECH_DEBT-140 (NEW `.D.1`) | `engine_mode` vestigial cfg field | `.D.1` | `.E.0.1`/`.E.1` |
| TECH_DEBT-141 (NEW `.D.1`) | `BacktestSharded_Run` → `Backtest_Run` unification | `.D.1` | `.E.1` |
| TECH_DEBT-129 (existing) | Per-core drainer architecture | - | `.E.1` |
| TECH_DEBT-135 (existing) | Class 11 regime_names sibling-array | - | `.E.1` (likely) |
| TECH_DEBT-NEW-1 | TUI implementation | `.E.1` | `.E.2` |
| TECH_DEBT-NEW-2 | CLI implementation | `.E.1` | `.E.2` |
| TECH_DEBT-NEW-3 | Headless engine binary build target | `.E.1` | `.E.2` |
| TECH_DEBT-NEW-4 | foxml-train CLI | `.E.1` | `.E.2` |
| TECH_DEBT-NEW-5 | Per-cluster reserve_pct + max_per_node_pct | `.E.1` | `.E.5` |
| TECH_DEBT-NEW-6 | Internal-transfer plumbing | `.E.1` | `.E.5` |
| TECH_DEBT-NEW-7 | Per-cluster market_hours enforcement | `.E.1` | `.E.6` (or operator-triggered) |
| TECH_DEBT-NEW-8 | Per-exchange session-aware ML training | `.E.1` | `.E.6` (or operator-triggered) |
| TECH_DEBT-NEW-9 | Persistent WS-API integration | `.E.2` | `.E.3` |
| TECH_DEBT-NEW-10 | io_uring + kTLS per-node I/O | `.E.2` | `.E.4` |
| TECH_DEBT-NEW-11 | Operator workflow runbook for prolonged outages | `.E.2` | v5.16+ |
| TECH_DEBT-NEW-12 | Multi-region deployment documentation | `.E.2` | v5.16+ |
| TECH_DEBT-NEW-13 | Multiple WS-API connections per cluster (pipelining) | `.E.3` | v5.16+ |
| TECH_DEBT-NEW-14 | Non-WS-API protocols for other exchanges | `.E.3` | `.E.6/.E.7` |
| TECH_DEBT-NEW-15 | io_uring fallback path for non-Linux dev | `.E.4` | (Linux-only; not closed) |
| TECH_DEBT-NEW-16 | kTLS cipher fallback | `.E.4` | v5.16+ |
| TECH_DEBT-NEW-17 | Smart NIC offload (Mellanox BlueField) | `.E.8` (deferred) | v6.X+ |
| TECH_DEBT-NEW-18 | FPGA tick processing | `.E.8` (deferred) | v6.X+ |

---

## 8. Existing canonical reference docs (read before coding)

### Tier 1 (always-loaded; auto-loaded by Claude Code)

- `/home/caramel/code/FoxML_Trader_v2/CLAUDE.md` — architectural orientation + H1-H20 invariants + skill suite categories
- `/home/caramel/code/FoxML_Trader_v2/CLAUDE.local.md` — going-forward rules + sprint state index
- `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md` — auto-memory index

### Tier 2 (performance-sensitive code triggers; on-demand)

- `DOCS/STRATEGY_AND_CODING_RULES.md` — 11 strict invariants (private)
- `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` — 13 parts (private)
- `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` — 7 architectural rules + pre-merge checklist
- `DOCS/DESIGN_PHILOSOPHY.md` — 14 sections + § 11.5 meta-discipline registry (M1..Mn)

### Tier 3 (existing DESIGN_SPECS catalog)

- `DESIGN_SPECS/README.md` — full catalog (~80+ specs)
- `DESIGN_SPECS/TAG_INDEX.md` — tag vocabulary index

### Tier 4 (existing bug class catalog + ledgers)

- `DOCS/RECURRING_BUG_PATTERNS.md` — Class 1-35 catalog
- `DOCS/tech-debt/open.md` — open TECH_DEBT entries
- `DOCS/tech-debt/closed.md` — closed TECH_DEBT entries
- `DOCS/PARITY_ISSUES.md` — parity surface tracking
- `DOCS/FEATURE_LOOKUP.md` — operator-facing feature inventory

---

## 9. Audit reports (lands at `.E.0` execution)

| Audit type | Output location | Status |
|---|---|---|
| Per-plan `/precoding-audit-gate` reports | `plans/v5.15-live-readiness/plan_checks/E.0-audit-reports/<plan-name>-<audit>.md` | TO BE GENERATED at `.E.0` |
| Per-plan synthesis | `plan_checks/E.0-audit-reports/<plan-name>-synthesis.md` | TO BE GENERATED at `.E.0` |
| Cross-ship synthesis | `plan_checks/E.0-audit-reports/cross-ship-synthesis.md` | TO BE GENERATED at `.E.0` |
| Anti-pattern + DOD synthesis | `plan_checks/E.0-audit-reports/anti-pattern-dod-synthesis.md` | TO BE GENERATED at `.E.0` |

---

## 10. Memory rules (feedback) applied across `.E`

These rules guided architectural decisions; every plan body cross-refs the relevant subset.

- `feedback_motivated_collaborator_for_caramel` — quality bar; hedge-fund-visibility
- `feedback_plan_right_not_fast` — detailed plan body before coding; this whole approach
- `feedback_audit_canonical_sister_before_new_infra` — every new infra extends canonical sister
- `feedback_audit_own_proposals_with_same_rigor` — 4-pillar audit on each plan body
- `feedback_proactive_novel_alternative_consideration` — explored 8+ radical alternatives
- `feedback_consult_on_audit_findings` — surface findings; iterate; triage
- `feedback_no_question_boxes` — inline text only
- `feedback_address_user_as_caramel` — Caramel / she / her
- `feedback_session_decision_log_discipline` — D-1..D-60 captured
- `feedback_iteration_spiral_signals_audit_meta_gap` — convergent steep across turns; not spiral
- `feedback_evaluate_options_on_robustness_latency_design_not_time` — option evaluation discipline
- `feedback_no_defer_for_effort` — substantial scope embraced
- `feedback_structural_fix_for_recurring_class` — Class 26 + Class 27 + KS race closed structurally
- `feedback_categorical_triggers_over_hardcoded_refs` — FOREACH_EXCHANGE > hardcoded list
- `feedback_single_source_of_truth_discipline` — per-node state has single writer
- `feedback_backwards_compat_not_default_concern` — clean break per operator directive
- `feedback_sister_cohort_amendment_completeness` — rename + amendments parallel
- `feedback_forward_promise_auto_write_verification` — forward-promises mechanically tracked
- `feedback_enumerate_consumers_before_registry_row_deletion` — Core→Node rename comprehensive
- `feedback_address_user_as_caramel` — collaboration discipline
- `feedback_cfg_field_categorization_at_registry_add_time` — new fields categorized
- `feedback_count_code_loc_not_total_lines` — file-size discipline
- `feedback_forward_decl_at_global_scope_not_namespace` — Class 34 avoidance
- `feedback_enumerate_block_scope_statics_before_hoist` — M6 discipline
- `feedback_cpp17_inline_variable_for_shared_state_across_tus` — header-only globals
- `feedback_proportionate_response_to_audit_findings` — findings triaged per severity
- `feedback_dont_measure_structural_work_by_loc` — structural work value by classes closed

---

## 11. Anti-pattern catalog references (Class 1-35)

Each plan body audited against these classes at `.E.0`:

| Class | Title | `.E` audit relevance |
|---|---|---|
| Class 11 | Hardcoded sibling array bypass | `.E.1` FOREACH_EXCHANGE; verify no leak |
| Class 14 | Fabricated symbols in plan body | All plans; B-Plus CI tool + manual grep |
| Class 18 | Mirror plans missing data flow | `.E.1` aggregator + per-node state ownership |
| Class 21 | Parallel wide-variant registry | `.E.1/.E.3` H18 sidecar discipline |
| Class 23 | Type-erased dispatch | `.E.1/.E.3/.E.6` `tt::*` dispatch (H13) |
| Class 24 | Cfg↔ML surface-alignment gap | `.E.1/.E.5/.E.6` ML feature cohorts |
| Class 25 | Cosmetic-fix surface | All plans; verify root-cause addressed |
| Class 26 | Global consumer reading per-core | `.E.1` CLOSURE; verify no later regression |
| Class 27 | Single-value cache flattens per-instance | `.E.1` CLOSURE; verify per-node ownership |
| Class 28 | Branchy SP/HP dispatch | `.E.1` H20 verification |
| Class 33 | Consumer enumeration undercount | `.E.1` Core→Node rename comprehensive |
| Class 34 | Forward-decl in namespace tt | `.E.1` global-scope verification |
| Class 35 | Block-scope statics in lambda hoist | `.E.1` M6 discipline verification |

---

## 12. Auditing checklist (operator-usable)

When auditing `.E` sub-sprint state, check:

### Plan body completeness
- [ ] All 7 active ship plan bodies (`.E.0-.E.6 + .E.X`) drafted at recreation-quality
- [ ] Each plan body has mandatory D-52 "Required reading + reference docs cross-check" section
- [ ] Each plan body cites: anti-patterns avoided + DESIGN_SPECS extended/applied + NEW DESIGN_SPECS + TECH_DEBT closed + memory rules + required reading

### Cross-ship integration
- [ ] Dependency graph reflects current ship trajectory
- [ ] Forward-promises in each plan match successor "Substrate landed at..." sections
- [ ] No conflicting forward-promises
- [ ] Cross-ship invariants verified at `.E.0`

### DESIGN_SPECS readiness
- [ ] All NEW spec stub files exist at correct paths (this index)
- [ ] Each spec has correct frontmatter (type / stage / version / established / sister_specs)
- [ ] Each cited DESIGN_SPEC link is valid

### Decision log integrity
- [ ] All D-X / F-X / C-X / P-X entries up-to-date
- [ ] Status field accurate per artifact
- [ ] Sister disciplines section reflects applied rules

### Anti-pattern catalog clean
- [ ] `.E.0` `/bug-check` returns CLEAN against all classes
- [ ] No NEW class instances introduced by plans
- [ ] Closed classes preserved

### Documentation deliverables
- [ ] All SKELETON docs exist (for `.E.2` fill-in)
- [ ] CLAUDE.md amendments planned at `.E.1`
- [ ] DESIGN_PHILOSOPHY.md amendments planned at `.E.1`

---

## 13. Operator workflow for `.E` sub-sprint pickup

**CRITICAL: Next session MUST start with `.E.0` audit execution before ANY coding work.** Per D-64 (audit-first execution discipline). Operator quality bar: "correctness here is vital, as well as avoiding bugs, and designing this to avoid adding tech debt".

Workflow:

1. Read this MASTER REFERENCE first
2. Read decision log v2 (D-1..D-64)
3. Read dependency graph
4. Run `/accept-handoff <handoff-path>` skill (loads handoff doc; verifies git state; recreates TaskList; runs `/capture-audit --deep`)
5. **`.E.0` EXECUTION (REQUIRED FIRST):** fire full audit suite per plan body at `subplans/2026-05-28-v5.15.5.F.4d.1.E.0-precoding-plan-audit-verification.md`
   - 5-agent `/precoding-audit-gate` HIGH-RISK tier × 7 plan bodies = 35 audit firings
   - 4 codebase-wide audits (`/anti-spaghetti` + `/registry-fit-audit` + `/test-strength-audit` + `/parity-check`)
   - Cross-ship invariant verification against dependency graph
   - Anti-pattern catalog (Class 1-35) check
   - DESIGN_SPECS pattern application verification
   - Forward-promise alignment verification
   - TECH_DEBT closure tracking
   - Stage promotion tracking
6. Triage findings (FIX-NOW / ACCEPT / DEFER) per `feedback_proportionate_response_to_audit_findings`
7. Apply FIX-NOW amendments; cycle 2 audit verifies GREEN
8. **ONLY THEN** begin `.E.1` Foundation coding per Phase A → ship close pattern

---

## 14. Status tracker (living index; update as artifacts created)

| Artifact category | Total | Drafted | Stage 3 promotion ready |
|---|---|---|---|
| Plan bodies (active ships) | 8 | 8 (some need expansion) | 0 (awaits `.E.0` GREEN) |
| Plan bodies (deferred) | 2 | 2 | N/A |
| Decision log entries (D-X) | 60+ | 60 | N/A |
| Decision log entries (F/C/P) | 27+ | 27 | N/A |
| NEW DESIGN_SPECS | ~38 + 8 DRAFTs | TO BE CREATED at `.E.0` | Per-landing-ship |
| AMENDED existing specs | 6 | Planned at landing | Per-landing-ship |
| Skeleton docs (DOCS/) | 8 ops + 5 contributing | TO BE CREATED at `.E.0` | Filled at `.E.2` |
| CLAUDE.md amendments | N | Planned at `.E.1` | At `.E.1` |
| DESIGN_PHILOSOPHY.md amendments | 6 new sections | Planned at `.E.1` | At `.E.1` |

---

**End of MASTER REFERENCE v1.0** (2026-05-28). Update as artifacts created + status changes.
