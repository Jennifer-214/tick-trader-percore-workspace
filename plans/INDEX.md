# plans/ — INDEX

`plans/` is gitignored at engine repo + lives in workspace as private working
docs. Symlinked from engine `FoxML_Trader_v2/plans` → workspace `plans/`.

**Reorganized 2026-05-10 (post v5.14.9 sprint close)** into per-sprint
sub-dirs + category dirs. Each sprint = MASTER.md + subplans/ + plan_checks/ +
postmortems/ + handoffs/.

---

## 🟢 ACTIVE sprint

### [v5.14-foxml-port-and-maker/](v5.14-foxml-port-and-maker/) — FoxML port + maker MVP

- [MASTER.md](v5.14-foxml-port-and-maker/MASTER.md)
- **Status:** v5.14.0–.9 + tools/dod-audit-v0.1 SHIPPED; v5.14.10 (Thompson) + v5.14.11 (online corr) PENDING; v5.14.7 (maker MVP) DEFERRED-INDEFINITE (TECH_DEBT-008).
- 21 subplans, 45 plan_checks, 4 postmortems (`.5`, `.8`, `.9`, `v5.14.1`), 1 handoff (`.8`).
- **Next:** open v5.14.10 in fresh context via the handoff prompt in `handoffs/`.

---

## ✅ SHIPPED sprints

| Sprint | Description | Closed |
|---|---|---|
| [v5.13-sell-side-ml/](v5.13-sell-side-ml/) | Sell-side ML + bandit + per-horizon label kind UI | 2026-05-09 |
| [v5.12-pre-live-and-optimization/](v5.12-pre-live-and-optimization/) | Pre-live safety + AVX-512 + ML research infra | 2026-05-08 |
| [v5.11-optimization-sprint/](v5.11-optimization-sprint/) | 9-phase HFT optimization (allocator eradication, locale-immune parsing, OMS variance, AVX-512 bandit) | 2026-05-07 |
| [v5.10-ensemble-engine/](v5.10-ensemble-engine/) | Ensemble + hot-swap + drift detection + FPN-end-to-end | 2026-05-06 |
| [v5.9-to-v5.10/](v5.9-to-v5.10/) | ML hardening + bash CLI parity + GUI stamp UX + multiclass autostamp | 2026-05-02 |
| [foxml-absorption/](foxml-absorption/) | FoxML_Core extraction + port to C++ + math+training deep-audits | 2026-05-08 |
| [risks-and-open-questions/](risks-and-open-questions/) | Standing risk register + ML audit | ongoing reference |

---

## 📁 Category dirs (cross-sprint or sprint-independent)

### [_cross-cutting/](_cross-cutting/) — load-bearing ongoing references
- `2026-05-06-latency-path-discipline.md` — **7 architectural rules for latency-critical paths** (cited from `CLAUDE.local.md`)
- `2026-05-06-strategy-and-coding-rules.md` — strict invariants (no malloc, no virtual, no mutex, branchless, AVX-512-friendly)
- `2026-05-07-deferred-items.md` — sprint deferral log w/ re-trigger conditions (cited from CHANGELOG, ML_TRAINING.md, CLAUDE_ML_INVARIANTS.md)
- `ml-training-roadmap.md`
- `legacy-deprecation-cleanup.md`

### [_future/](_future/) — candidate / not-yet-scheduled
- v5.15+ cleanup backlog
- v6.0 candidate: headless-service-colo
- future-autotune, future-volatile-strategy
- FUTURE-autonomous-local-agent
- FUTURE_ML.md
- public-release-v2-strategy

### [_audits/](_audits/) — standalone deep-audit reports
- latency-optimization-audit (Gemini sweep)
- foxml-core math + training deep audits (now under `foxml-absorption/subplans/`)
- ml-optimizations
- regime-classification-universalization
- sizing-audit-2026-04-29
- V5_9_ML_HARDENING_AUDIT
- HETEROGENEOUS_WINSOR_EXIT_PLAYBOOK
- parity-2026-05-06-* (cross-sprint baseline parity)
- parity-2026-05-07-stamp
- audit-2026-05-09-regime-universalization

### [_ideas/](_ideas/) — brainstorm / learn / harness docs
- interview-prep-systems
- learn-ml-zoo
- ml-inference-harness
- SLOW_PATH_OPTIMIZATION_2

### [archived/](archived/) — pre-v5.9 deep history
Pre-v5.10 plans, polish-day master, strategy-* masters, v5.4-v5.8 plans, ALL-PLANS-PREFLIGHT, post-edge-hunt, post-v4.0-followups, SESSION_HANDOFF_2026-05-06. Reference only — not active work.

### [plan_checks/](plan_checks/) — NEUTRAL skill-output dir
Skills (`/parity-check`, `/trace-deps`, `/readiness`, `/merge-scan`, `/dod-audit`, `/test-strength-audit`, `/latency-track`, `/ml-audit`, `/plan-check`) write reports here per convention `<skill>-<YYYY-MM-DD>-<scope>.md`. At sprint close, mechanically batched into the relevant sprint's `plan_checks/` dir.

---

## Per-sprint dir layout (canonical)

```
plans/<sprint-name>/
├── MASTER.md          # sprint master plan
├── subplans/          # sub-tag plans (.A, .B, ...)
├── plan_checks/       # audit reports (post-sprint-close batched from plans/plan_checks/)
├── postmortems/       # session postmortems
└── handoffs/          # session-handoff prompts (when sprint spans sessions)
```

---

## Reorg history

- **2026-05-10** — Full directory reorganization post-v5.14.9 close. 132 plans + 79 audits batched into per-sprint dirs + category dirs. Engine-repo symlink (`FoxML_Trader_v2/plans` → `workspace/plans/`) unaffected (points at dir, not files). Cross-refs swept via `rg` + `sed`. Sealed historical changelogs (`DOCS/changelogs/`) intentionally not updated.

---

## How to find what you need

| Need | Look here |
|---|---|
| Current sprint plan | `v5.14-foxml-port-and-maker/MASTER.md` |
| A specific sub-ship (e.g., v5.14.9.F) | `v5.14-foxml-port-and-maker/subplans/*v5.14.9*` |
| Audit report for a recent ship | `v5.14-foxml-port-and-maker/plan_checks/` |
| Latency-discipline rules | `_cross-cutting/2026-05-06-latency-path-discipline.md` |
| Deferred-item log | `_cross-cutting/2026-05-07-deferred-items.md` |
| Future-roadmap candidates | `_future/` |
| Standalone deep audits | `_audits/` |
| Pre-v5.9 history | `archived/` |
| Fresh skill output (audits run today) | `plan_checks/` (neutral; batches into sprint dir at close) |
