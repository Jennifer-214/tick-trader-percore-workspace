---
type: plan-check
subtype: readiness
ship_tag: v5.15.5.F.4d.1.E.1.1
date: 2026-06-22
head_at_check: 1da1c1c
plan: plans/v5.15-live-readiness/subplans/2026-06-15-v5.15.5.F.4d.1.E.1.1-core-node-rename.md
invoked_by: /accept-handoff (Stage 6, composed inline)
verdict: GREEN-pending-owed-adversarial-re-gate
---

# /readiness — E.1.1 (Core→Node rename + cfg "config compiler") — 2026-06-22

Receiver-side verification at pickup. Engine HEAD `1da1c1c`, clean tree, **3635/0** (build re-run, verified). `check_session_docs.sh` SWEEP CLEAN (16/16 HARD+ADV).

## What we already have (Stage 0 preamble)
- ② Core→Node rename + single_core Phase 1-3 deletion = **LANDED + green** (`1da1c1c` / `b9ce419` chain). Only ③ (cfg config-compiler) + ⑤ V-class remain.
- ③ is **DECIDED** (D-242 config-compiler / D-243 buffer-fix-only / D-244 backtest-CLI OPEN→E.2, not a ③ blocker) — see decision log. The sibling precedent `ConfigField_Set` (returns 0/1 on key-match, `controller_test.cpp:18361`) is the fault-mechanism model, not reinvented.
- Surface specs in play: `cfg-scope-discipline.md` (Class 25/26/27), `dead-code-and-identifier-retirement-discipline.md` (H21 — keys are operator-text → clean-break correct), `rename-ship-methodology.md`, multi-surface deletion ordering (B14/Check 41).

## Checklist verdicts
| # | Item | Verdict | Notes |
|---|---|---|---|
| 1 | Hot-path purity | PASS | rename = names only (determinism golden byte-identical); ③ cfg validation is boot/slow parser, not hot path |
| 2 | Train-serve parity | PASS | ③ touches no feature/label/stamp; D-243 path = load-location ≠ model identity |
| 3 | Surface area | PASS | ③ scoped (2 parsers + 2 bricks + 2 ⊆ guards + fault bitmap); single_core deletion was 3-phase leaves-first, DONE |
| 4 | Pointer/heap | PASS | H1 — fixed-buffer readout, no heap |
| 5 | Backward compat | ACCEPTED | cfg-key clean-break = deliberate behavior change (operator migrates `core_→node_`); H21-correct (operator-text, not wire); snapshot VERSION untouched (E.1.2 owns) |
| 6 | Multi-threading | PASS | flag-based fault (`cfg_load_fault_flags` → ControllerConfig cold region next to `live_capital_cfg_conflict`@`:576`); NEVER abort-in-Load (3 confirms: hot-reload bulk-copy / GUI Settings_Load crash / no-error-channel) |
| 7 | Test coverage | PASS* | List A empty (② cleaned keys) · List B flip @ `controller_test.cpp:24098` CONFIRMED (the v5.14.9.D "legacy key parses without crash" test → flip to assert-fault) · List C 6-7 new chars. *Check-45 heading nit below |
| 8 | Docs + invariants | PASS | FEATURE_LOOKUP + migration note @ close; new anti-pattern candidate (incomplete-deletion `_PLACEHOLDER` brick); DESIGN_SPECS seeds (hierarchical-config-validation / runtime-mutable-vs-boot-time) |
| 9 | Forward maintenance | PASS | two ⊆ guards (parser⊆registry + GUI-recognized⊆engine-recognized) close the desync→brick CLASS at CI (framework-driven) |
| 10 | Rollback | PASS | tag `pre-v5.15.5.F.4d.1.E.1.1` @ `b9ce419` verified exists |

Cold-pickup C.1–C.10: GREEN (branch/phases/first-move/fn-names/rollback all present); only line-anchors drifted (C.5) → re-derived below.

## RE-DERIVED line map at HEAD `1da1c1c` (the cascade SSoT cites are pre-Phase-3 — Check-32 flagged 14 anchor drifts)
- `ControllerConfig.hpp` `node_` parser: 7 recognized branches `:2839 :2847 :2858 :2866 :2879 :2892 :2902` + outer per-node block opener `:2929` (HARD-REFUSE fall-through = end of the `:2929` block; was cascade's `:2968`/`:3099`).
- `cfg_load_fault_flags` home: next to `live_capital_cfg_conflict` @ `ControllerConfig.hpp:576` (init `:1661`, set `:3236`).
- fgets buffer (D2 harden): `char line[256]` @ `ControllerConfig.hpp:2050`.
- legacy global keys `engine_mode` / `num_execution_cores`: **0 residual parse branches** (Phase-3 deleted / rename renamed) → both now hit the unrecognized path = exactly what the global-key refuse must catch.
- GUI bricks (delete): `num_execution_nodes_PLACEHOLDER` @ `SettingsPanel.hpp:456`, `confidence_freshness_tau` @ `:669` (C-2 brick; coordinate w/ PARITY-006). GUI parser `strncmp(p,"node_",5)` @ `:922`; `Settings_Load` def @ `:871` (call @ `:1690`).
- Guard to BUILD (absent, correct): `tools/check_gui_engine_cfg_key_parity.py` — guard-FIRST, teeth-RED-proven before the brick deletes.

## Findings (non-blocking)
- **DRIFT (non-blocking):** cascade SSoT `2026-06-21-E.1.1-cfg-clean-break-precoding-cascade.md` carries pre-Phase-3 line cites; current map above. The handoff body already uses `~:2929` (current).
- **DOCUMENT-ONLY:** Check-45 — plan has `### Test-change enumeration` but the tool greps `## Tests changed`; normalize the heading so the mechanical check passes.
- **DOCUMENT-ONLY:** cascade SSoT frontmatter `status: SCOPE-LOCKED-PENDING-OPERATOR-SIGNOFF` is mildly stale (D-242/243/244 logged + micro-calls delegated 2026-06-22); the "+ adversarial re-gate" half is still accurate.

## Verdict: 🟢 GREEN — pending the owed adversarial re-gate
The plan is structurally sound and citation-verified. The ONLY thing between here and coding ③ is the **targeted adversarial re-gate on the config-compiler DELTAS** (the handoff's NEXT ACTION — errors/warnings classification · key-match-not-field-written over-fire · compile-gating-every-fresh-start incl. backtest · `cfg_load_fault_flags` bitmap + fixed-buffer readout · terminal+`config_error_log` output). That is an operator-directed gate (consult-before-coding) — NOT a /readiness-discovered blocker. After the re-gate: code ③ atomic (guards teeth-RED → bricks delete → HARD-REFUSE) → ⑤ V-class (asan/ubsan) → ship-close.
