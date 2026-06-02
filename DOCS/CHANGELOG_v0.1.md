# CHANGELOG v0.1.0 (DRAFT placeholder)

**Status:** PLACEHOLDER. To be filled at v0.1.0 ship close (`.E` sub-sprint complete).

Per D-14: software_version = "0.1.0" represents the full `.E` end-game state.

---

## v0.1.0 — Architecture E++ (target: post-`.E` sub-sprint close)

### Headline

Major architectural rework: per-node sub-account isolation; multi-exchange substrate; headless service architecture; io_uring + kTLS kernel-bypass I/O; WS-API persistent connections; event-sourced O(1) aggregator; strategy hot-reload.

### Ships landed

- `.E.0` Pre-coding plan audit + verification
- `.E.1` Foundation (Core → Node rename; per-node drainer absorb; multi-exchange registry; cluster topology)
- `.E.2` Headless + per-node configs + ML CLI + documentation push
- `.E.3` WS-API + persistent TLS connections
- `.E.4` io_uring + kTLS kernel-bypass I/O
- `.E.5` Real sub-accounts wired + capital allocation framework
- `.E.6` Exchange adapter framework generalization
- `.E.X` Strategy hot-reload via dlopen (power-user)

### Closed bug classes (structural)

- **Class 26** (Global consumer reading per-node field) — ELIMINATED structurally at `.E.1`
- **Class 27** (Single-value cache flattens per-instance) — ELIMINATED structurally at `.E.1`
- **Known KS race** (audit 2026-04-09 Async.hpp:432-442) — CLOSED as side-effect of aggregator-as-single-writer

### Closed TECH_DEBT entries

- TECH_DEBT-129 (per-node drainer architecture)
- TECH_DEBT-135 (Class 11 regime_names sibling-array)
- TECH_DEBT-NEW-1..10 (per-`.E` ship NEW entries)

### NEW DESIGN_SPECS landed (Stage 3 first canonical)

~30 NEW specs codified across `.E` sub-sprint. Full enumeration in `plans/v5.15-live-readiness/E-MASTER-REFERENCE.md`.

### Operator-facing changes

- **Binaries:** fox-engine + fox-tui + fox-cli + foxml-train (replaces engine + engine_gui + foxml_suite)
- **Config:** hierarchical layout (configs/clusters/<exchange>/nodes/node_<id>/*.cfg)
- **Sub-accounts:** real Binance sub-accounts per node; capital isolation
- **Hot-reload:** strategy code + cfg via SIGUSR1/SIGUSR2
- **Documentation:** substantial operator-facing docs landed (DEPLOYMENT_GUIDE; OPERATOR_MANUAL; ARCHITECTURE_OVERVIEW; GLOSSARY; INCIDENT_RUNBOOK; STRATEGY_LIFECYCLE; DR_TESTING; SECURITY; PERFORMANCE_TUNING; MIGRATION_FROM_v5.X; HARDWARE_REQUIREMENTS; FAQ; REPO_CLEANUP_GUIDE; CONTRIBUTING/)

### Hot path UNTOUCHED (except `.E.1` Core→Node rename + `.E.4` io_uring substitution)

H1-H20 invariants preserved. H8 latency budget intact.

### Tests

Test count: ~3289-3440 (vs 3239 baseline at v5.15.5.F.4d.1.D).

### NOT included at v0.1.0

- `.E.7` IBKR exchange (OPTIONAL-FUTURE; operator-triggered)
- `.E.8` DPDK / Onload (DEFERRED; requires DPDK-compatible hardware)
- Public usage guide (deferred to post-`.E` separate session)
- Repo rename to FoxML_PortfolioManager (DEFERRED per D-62)
- Backward compatibility for v5.X configs (clean break per D-9)

### Migration path

Per `DOCS/MIGRATION_FROM_v5.X.md`. ~2-4 hours operator one-time + 1-2 weeks staged deployment.

### Per-ship postmortems

Linked at v0.1.0 close per ship:
- postmortems/<date>-v5.15.5.F.4d.1.E.0-postmortem.md
- postmortems/<date>-v5.15.5.F.4d.1.E.1-postmortem.md
- ... etc per ship

---

**End of v0.1.0 CHANGELOG placeholder.**
Updated at each `.E` ship close + finalized at `.E` sub-sprint umbrella close.
