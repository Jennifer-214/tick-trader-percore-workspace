---
type: ledger-template
class_id: 24
title: Capability-cfg surface mismatch (ML pipeline supports it; operator can't see / configure / verify it)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
surface_tags: [cfg-flow, ml-inference, gui-thread, registry]
severity: high
recurrence_count: 3
first_instance: v5.13.4
closure_mechanism: universal cfg registry + bitmap dispatcher (v5.15.5.F.4c) so new capability = single FOREACH_CFG_FIELD row with cfg parser + Settings render + stamp tag + per-core override auto-flow + FOREACH_BANDIT_ALGORITHM 5-state expansion with metadata-driven dispatch tables (v5.15.5.F.4d) + Cfg↔ML surface-alignment audit rule + /ml-audit at sub-ship close
sister_classes: [11, 18, 21, 23, 25, 27]
---

## Class 24 — Capability-cfg surface mismatch (ML pipeline supports it; operator can't see / configure / verify it)

**Detected:** 2026-05-14 (post v5.15.5.F.4c paper-test, surfaced by `/ml-audit` + operator-verification pass).
**Severity:** HIGH — operator-invisible ML capability = silent miscalibration risk.

### Recurring symptom

ML pipeline ships a capability (model role, ensemble dimension, blender mode, bandit algorithm, posterior parameter, exit-side mirror, etc.) but the cfg / Settings panel / HMAC stamp / drift-check surface doesn't expose it. The capability is *invisible* despite being in production code. Three observed instances:

- **v5.15.5.F.4c paper-test (2026-05-14):** `bandit_algorithm`, `thompson_*`, `ridge_*`, `confidence_*` (~17 fields) exist as struct fields with working parsers + stamp-bound emit, but NOT in `FOREACH_CFG_FIELD` — Settings panel renders nothing for them. Operator can't tune them via GUI.
- **v5.15.5.F.4c.2 (Thompson update wire):** `Thompson_Update` defined at `ML_Headers/ThompsonBandit.hpp:183` + fully tested, but **never called in any production reward-attribution path**. Slow-path lookback (`CoreModelZoo.hpp:1341`), trade-close reward (`CoreModelZoo.hpp:1402`), exit-side (`ControllerEventLoop.hpp:1731`) only call `Bandit_Update`. With `cfg.bandit_algorithm=1` (THOMPSON), Thompson reads its posterior for arm selection but the posterior never updates — Thompson sampling effectively-broken in production. Mode selectable, doesn't work.
- **v5.13.4 exit-side mirror (closed by v5.14.0.E):** `exit_bandits` / `exit_ridge_state` / `exit_reward_ring` exist parallel to buy-side, but for one ship the cfg surface only exposed buy-side knobs.

The shape: CODE adds a capability; SURFACE (cfg parser → Settings → stamp → drift) misses it. Capability is half-shipped — present in execution but invisible to operator.

### Root cause

Four downstream surfaces need updating per ML capability:
1. **Cfg parser** — does `engine.cfg` accept the operator-settable key?
2. **Settings render** — does the GUI panel show + allow editing?
3. **HMAC stamp tag** — is the value tagged in stamp body if parity-relevant?
4. **Per-core override** — if per-core makes sense, is `core_N_<key>` wired?

Adding an ML capability without auditing all four is the recurring failure.

### Structural fix

Per CLAUDE.md item 31 + DESIGN_PHILOSOPHY § 1.5: the universal cfg registry + bitmap dispatcher at v5.15.5.F.4c makes new capabilities → registry-row-only. Once a capability is a row in `FOREACH_CFG_FIELD`, cfg + Settings + stamp + drift auto-flow. "Added the feature, forgot the cfg surface" dies structurally.

`v5.15.5.F.4c.1` codifies this class + ships 18-row STAMP_BOUND cohort migration (first batch fix). `v5.15.5.F.4c.2` closes the Thompson_Update wire gap (second canonical instance).

### Prevention (going-forward rule + skill)

New CLAUDE.local.md going-forward rule (codified at .F.4c.1):

> **Cfg↔ML surface-alignment audit at every ML feature add.** Trigger: any new ML capability → answer four columns (cfg parse / Settings render / stamp tag / per-core override). Any "no" without documented exemption = feature not done. Fire `/ml-audit` at sub-ship close for any ship touching ML capability.

Optional `/cfg-ml-alignment` skill (deferred until 2nd ML feature add validates the rule fires correctly).

### .F.4d closure update (2026-05-16)

Class 24 instance #2 (Thompson_Update wire gap at `.F.4c.2`) **structurally closed at `v5.15.5.F.4d` MERGED**. `FOREACH_BANDIT_ALGORITHM` 3→5 state expansion (`EXP3` / `THOMPSON` / `EXP3_OP_THOMPSON_GHOST` / `THOMPSON_OP_EXP3_GHOST` / `BLENDED`) + auto-derived `g_buy_reward_dispatch` + `g_exit_reward_dispatch` dispatch tables (from metadata columns `exp3_up` + `thompson_up`) ensure `Thompson_Update` is wired via dispatch table from reward-attribution callers — `cfg.bandit_algorithm=THOMPSON` now actually updates the Thompson posterior in production paths (was silently frozen pre-`.F.4d`). Sister Class 24 instance landed via `DESIGN_SPECS/framework-patterns/multi-state-dispatch-with-per-state-update-metadata.md` Stage 3 ACTIVE (first canonical = bandit 5-state dispatch).

### Related classes

- **Class 11** (Extensibility friction) — sister at a different layer.
- **Class 18** (Mirror-incomplete) — same shape at single mirror; this class is the cross-surface variant.
- **Class 21** (Parallel descriptors) — sibling; same structural fix closes both for cfg fields.
- **Class 23** (Type-erased dispatch) — same ship's other anti-pattern; both eliminated via the .F.4c framework + .F.4d derived filter framework.

### Cross-references

- `plans/plan_checks/ml-audit-2026-05-14-cfg-ml-surface.md` — full audit findings + interpretation matrix
- `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md` — the framework that prevents this class
- `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md` — the dispatcher consumer that auto-flows registered rows
- `DESIGN_SPECS/framework-patterns/multi-state-dispatch-with-per-state-update-metadata.md` (NEW 2026-05-14 ahead of .F.4c.2) — pattern that closes the Thompson_Update-wire-missing shape via per-state metadata
- CLAUDE.md item 31 + DESIGN_PHILOSOPHY § 1.5 — framework discipline meta-principle
