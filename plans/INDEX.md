# plans/ — INDEX

`plans/` is gitignored — these are personal working docs, not
version-controlled. Status-grouped index; individual plan files keep
their date prefixes for chronological lookup. Update INDEX entries
when a plan changes status.

**Status legend:**
- 🟢 ACTIVE — current sprint, work in progress or about to open
- 🟡 CANDIDATE — design captured, ship gated on a re-trigger
- ✅ SHIPPED — completed and merged
- 📋 REFERENCE — audits, design notes, deferred-items log,
  research direction maps; not sprint plans
- 🟦 PRIVATE — alpha-relevant; gitignored, workspace-backed only

---

## 🟢 ACTIVE — v5.12 sprint (drafted 2026-05-08)

**Master:**
- [v5.12 master](2026-05-08-MASTER-v5.12-pre-live-and-optimization.md)
  — Pre-Live Safety + Optimization Sprint, 4 phases, 13 ships, ~3-4 weeks

**Phase 1 — Pre-live safety (~2 days):**
- [v5.12.1.A](2026-05-08-v5.12.1.A-disconnect-flatten.md) — Disconnect-flatten policy
- [v5.12.1.B](2026-05-08-v5.12.1.B-staleness-gate.md) — Latency-aware prediction freshness gate
- [v5.12.1.C](2026-05-08-v5.12.1.C-ws-heartbeat.md) — WS heartbeat indicator
- [v5.12.1.D](2026-05-08-v5.12.1.D-confidence-sizing.md) — Confidence-conditional sizing infrastructure

**Phase 2 — Slow-path Tier 1 optimization (~1 week):**
- [v5.12.2.A](2026-05-08-v5.12.2.A-rolling-stats-avx512.md) — AVX-512 RollingStats residuals + Lemire divmod
- [v5.12.2.B](2026-05-08-v5.12.2.B-lazy-rebuild.md) — Lazy slow-path rebuild
- [v5.12.2.C](2026-05-08-v5.12.2.C-fpn-f32.md) — FPN<F=32> half-width variant
- [v5.12.2.D](2026-05-08-v5.12.2.D-treelite-aot.md) — Treelite AOT compile (SPECULATIVE)

**Phase 3 — ML research infrastructure (~1 week):**
- [v5.12.3.A](2026-05-08-v5.12.3.A-composite-signal.md) — Composite-signal extractor
- [v5.12.3.B](2026-05-08-v5.12.3.B-mixed-output-normalizer.md) — Mixed-output prediction normalizer
- [v5.12.3.C](2026-05-08-v5.12.3.C-time-exit-override.md) — Per-core time-exit override
- [v5.12.3.D](2026-05-08-v5.12.3.D-feature-mask.md) — Feature mask cfg per-core
- [v5.12.3.E](2026-05-08-v5.12.3.E-role-aliasing-cleanup.md) — v5.11.62 architectural cleanup

**Phase 4 — Strategy experiments (PRIVATE, ~2 weeks paper-test):**
- 🟦 `plans/2026-05-XX-v5.12-strategy-experiments-PRIVATE.md` — TBD when Phase 4 opens

**Plan-check report:**
- [v5.12 plan-check](plan_checks/2026-05-08-v5.12-pre-live-and-optimization.md)
  — verdict YELLOW (3 minor mitigations); no blockers before coding

---

## 🟡 CANDIDATE — future sprints (gated on Phase 4 findings)

- [v5.13 strategy-direction stubs](2026-05-08-v5.13-CANDIDATE-strategy-direction.md)
  — DELTA_DIVERGENCE, buy/sell-side specialized models, multi-model
  bandit, multi-strategy bandit, online learning, multi-objective
  models, multi-model exit blend strategies (4 patterns)
- [v5.13 volume-divergence feature](2026-05-08-v5.13-CANDIDATE-volume-divergence-feature.md)
  — DELTA_DIVERGENCE FOREACH_FEATURE row + retrain
- [v6.0 headless service + colo architecture](2026-05-08-v6.0-CANDIDATE-headless-service-colo.md)
  — engine/GUI decoupling, snapshot wire serialization, persistent
  service, io_uring, kernel-bypass NIC

---

## ✅ SHIPPED — v5.11 sprint (drafted 2026-05-06; closed 2026-05-08)

**Master:**
- [v5.11 master](2026-05-06-MASTER-v5.11-optimization-sprint.md)

**Selected sub-ships** (full list under `2026-05-06-v5.11.*.md`):
- v5.11.0 — System foundation (TCP_NODELAY, mlockall, FTZ/DAZ, PGO/LTO)
- v5.11.1 — Hot path AVX-512 (Part 1 audit)
- v5.11.2 — Slow path O(1) regression + RollingStats (Part 2 audit)
- v5.11.3-7 — see master plan tag summary
- v5.11.6 — Allocator eradication (5 sub-tags)
- v5.11.41 — Multi-horizon training complete
- v5.11.8 ML AOT — DEFERRED → v5.12 Phase 2.D (re-triggered)
- v5.11.9 carryover — DEFERRED #5/#7/#18; #5 → v5.12 Phase 3.D

**Sidecars:**
- [v5.11 OPTIMIZATION REFERENCE](2026-05-08-v5.11-OPTIMIZATION-REFERENCE.md)
- [v5.11 ANNOTATED REVIEW](2026-05-08-v5.11-ANNOTATED-REVIEW.md)
- [v5.11 hft-suggestions](2026-05-06-v5.11-hft-suggestions.md)
- [v5.11 deferred-items (older)](2026-05-08-v5.11-deferred-items.md)
- [v5.11 tier2-3-cleanup](2026-05-08-v5.11-tier2-3-cleanup.md)

---

## ✅ SHIPPED — v5.10 sprint (drafted 2026-05-02; closed 2026-05-06)

**Master:**
- [v5.10 master](2026-05-02-MASTER-v5.9-to-v5.10.md)

**Selected sub-ships:**
- [v5.10.0 foundation](2026-05-03-v5.10.0-foundation.md)
- [v5.10.0a ensemble engine master](2026-05-04-MASTER-v5.10.0a-ensemble-engine.md)
  + G.5/.6/.7/.8/.9/.10/.11 sub-ships
- [v5.10.0a grid-search multihorizon](2026-05-03-v5.10.0a-grid-search-multihorizon.md)
- [v5.10.0b FPN end-to-end](2026-05-04-v5.10.0b-fpn-end-to-end.md)
- [v5.10.0c hot model swap](2026-05-05-v5.10.0c-hot-model-swap.md)
- [v5.10.0d FOREACH_TARGET](2026-05-06-v5.10.0d-foreach-target.md)
- [v5.10.0e drift detection](2026-05-07-v5.10.0e-drift-detection.md)
- [v5.10.1 production caller closure](2026-05-06-v5.10.1-production-caller-closure.md)
- [v5.10.2 hot-swap parity hardening](2026-05-06-v5.10.2-hot-swap-parity-hardening.md)
- [v5.10.3 display + observability](2026-05-06-v5.10.3-display-and-observability.md)

---

## ✅ SHIPPED — earlier sprints

- [v5.9 ML hardening master](2026-05-01-v5.9-ml-hardening.md)
  + v5.9.5c/d/h/i/j sub-ships
- [v5.8 easy additions (X-macro registry pattern)](2026-05-01-v5.8-easy-additions.md)
- [v5.7 strategy quality](2026-04-30-v5.7-strategy-quality.md)
- [v5.6 auto-mode design](2026-04-30-v5.6-auto-mode-design.md)
- [v5.6 execution-display audit](2026-04-30-v5.6-execution-display-audit.md)
- [v5.4.1 per-core stats reset](2026-04-30-v5.4.1-per-core-stats-reset.md)

---

## 📋 REFERENCE docs (CANONICAL sources)

**Deferred items + research direction:**
- 🟦 [Deferred items log](2026-05-07-deferred-items.md) — every
  explicitly-deferred item with re-trigger conditions
- 🟦 [FUTURE_ML.md](FUTURE_ML.md) — research direction map; 11 alpha
  hypotheses

**Audits (PRIVATE):**
- 🟦 [Latency optimization audit](2026-05-06-latency-optimization-audit.md)
  — 13 parts, ~40 items
- 🟦 [Strategy + coding rules](2026-05-06-strategy-and-coding-rules.md)
  — 11 invariants
- 🟦 [Latency path discipline](2026-05-06-latency-path-discipline.md)
  — 7 architectural rules per cadence
- [Trader ML audit](2026-05-01-trader-ml-audit.md)

**Future direction stubs (post-v5.13):**
- [Future autotune](2026-05-06-future-autotune.md)
- [Future volatile strategy](2026-05-06-future-volatile-strategy.md)
- [Future autonomous local agent](2026-05-07-FUTURE-autonomous-local-agent.md)

**Pre-live readiness (older; partially absorbed into v5.12):**
- [Live reconciliation](2026-04-29-live-reconciliation.md)
  *(absorbed into v5.12.1.A reconcile path)*
- [Held-out gate](2026-04-29-held-out-gate.md)
- [Pre-live completion](2026-04-29-pre-live-completion.md)
- [Polish day master](2026-04-29-polish-day-master.md)
- [Strategy correctness audit](2026-04-29-strategy-correctness-audit.md)
- [Strategy profitability master](2026-04-29-strategy-profitability-master.md)
- [Strategy restoration master](2026-04-29-strategy-restoration-master.md)
- [Public release v2 strategy](2026-04-29-public-release-v2-strategy.md)
- [Future directions (older)](2026-04-29-future-directions.md)

**Misc reference (long-lived):**
- [post-v4.0 followups](post-v4.0-followups.md)
- [post-edge-hunt-c-and-d](post-edge-hunt-c-and-d.md)
- [legacy-deprecation-cleanup](legacy-deprecation-cleanup.md)
- [interview-prep-systems](interview-prep-systems.md)
- [learn-ml-zoo](learn-ml-zoo.md)
- [ml-training-roadmap](ml-training-roadmap.md)
- [ml-inference-harness](ml-inference-harness.md)
- [SLOW_PATH_OPTIMIZATION_2](SLOW_PATH_OPTIMIZATION_2.md)
- [ML optimizations](2026-05-08-ml-optimizations.md)
- [Stamp cpp gui](2026-04-29-stamp-cpp-gui.md)
- [Foxml extraction ideas](2026-05-01-foxml-core-extraction-ideas.md)
- [Foxml ML port to cpp](2026-05-01-foxml-ml-port-to-cpp.md)
- [Foxml absorption master](2026-05-01-MASTER-foxml-absorption.md)
- [Risks + open questions master](2026-05-01-MASTER-risks-and-open-questions.md)
- [Overnight test checklist](2026-04-30-overnight-test-checklist.md)
- [v5.10 design notes](2026-05-06-v5.10-design-notes.md)

**Session continuity:**
- [Session handoff 2026-05-06](SESSION_HANDOFF_2026-05-06.md)
- [All-plans preflight 2026-05-02](2026-05-02-ALL-PLANS-PREFLIGHT.md)
- [v5.10 all-plans preflight](2026-05-03-v5.10-ALL-PLANS-PREFLIGHT.md)

---

## 🟦 PRIVATE — workspace-backed (gitignored)

The entire `plans/` directory is gitignored at the engine repo;
mirrored to `tick-trader-percore-workspace` for off-machine backup
(via `/sync-workspace` skill). Files marked PRIVATE carry edge
content (alpha hypotheses, operator-specific deployment details,
audit findings) that should NEVER appear in the public AGPL repo.

When in doubt about whether a new plan should be private: see
`CLAUDE.local.md` "Going-forward rule for new docs" — defaults to
private if it captures unshipped strategy direction, optimization
findings, operator-specific deployment, or references private cfg
values.

---

## 📋 plan_checks/ — audit reports

Subfolder containing `/plan-check`, `/parity-check`, and `/readiness`
outputs. Survives across sessions; backed up via workspace.

- [v5.12 plan-check](plan_checks/2026-05-08-v5.12-pre-live-and-optimization.md)
- [v5.11 plan-check](plan_checks/2026-05-08-v5.11-sprint.md)
- [v5.10 plan-check](plan_checks/2026-05-06-v5.10-sprint.md)
- (multiple parity/readiness audits — see `plan_checks/` directory)

---

## Adding a new plan

Filename convention: `YYYY-MM-DD-name.md` for dated plans, plain
`name.md` for long-lived reference.

Plans worth writing:
- Multi-day work that touches > 3 subsystems
- Architectural changes (threading topology, data layout, API surface)
- Anything that needs a parity_harness or sanitizer gate

Plans NOT worth writing (just code):
- Bug fix < 1 day, single subsystem
- Test-only additions
- Cosmetic / doc changes

When opening a new sprint: master plan first; sub-plans drafted
sequentially as each phase opens (each accounts for prior ships'
state per cold-pickup completeness rule from CLAUDE.local.md).

---

## Maintenance

- New plan → add to **🟢 ACTIVE**, cross-link to master
- Sprint ships → move section to **✅ SHIPPED**
- Plan killed → mark `[KILLED YYYY-MM-DD: reason]`, don't delete
- Candidate becomes active → move from **🟡 CANDIDATE** to **🟢 ACTIVE**

---

*Status-grouped + chronological by date prefix within each section.
No filesystem subfolder migration — preserves cross-references +
symlinks.*
