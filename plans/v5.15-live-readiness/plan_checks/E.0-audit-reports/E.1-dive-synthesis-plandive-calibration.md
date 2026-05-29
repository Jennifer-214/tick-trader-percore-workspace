---
type: plan-dive-calibration
plan: subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md
gate: v5.15.5.F.4d.1.E.0
date: 2026-05-29
purpose: FIRST /plan-dive run — validate the instrument reproduces the hand-audited E.1-dive-synthesis.md findings before dives 2-9 rely on it (per that synthesis' Calibration note)
baseline_ref: E.1-dive-synthesis-HANDAUDIT-baseline.md (the hand-audit; canonical .E.1 punch-list)
scope_run: Layers 1 (mechanical) + 4 (anti-pattern, targeted) + 5 (findings-ingestion) + 6 (seam) — the deterministic core. Layers 2+3 (composed /precoding-audit-gate 6-agent) DEFERRED to .E.1 cycle-2 (post-amendment) per D-35.
verdict: CALIBRATION PASS — instrument validated; .E.1 stays RED (same punch-list)
---

# `.E.1` /plan-dive — calibration run · CALIBRATION PASS

First execution of `/plan-dive`. Goal: confirm it reproduces the hand-audited findings (`E.1-dive-synthesis-HANDAUDIT-baseline.md`) **#1/#2/#3** before dives `.E.2`→`.E.X` depend on it.

## Reproduction table (calibration target → result)

| Hand-audit finding | Dive layer | Result |
|---|---|---|
| **#1 conc-5 contradiction** (per-cluster "MPSC-style submit_queue" vs no-MPSC-primitive vs per-node single-producer assertion) | Layer 4 | **REPRODUCED** — `.E.1:585` `SubmitQueue<F> submit_queue; // MPSC-style (nodes write; adapter reads)` vs `.E.1:1560` "per-node `submit_queue` single-producer invariant (conc-5 CHANGES-BY-DESIGN closure)" vs ground truth `SPSCRing.hpp:12` "no MPMC support, no MPSC, no SPMC" (anchor verified EXACT). Contradiction confirmed. |
| **#2 FPN_Atomic* nonexistent** (D-54 aggregator depends on undesigned primitive) | Layer 1 | **REPRODUCED** — `FPN_AtomicAdd/Load/Store/Sub` confirmed NONEXISTENT in FixedPoint/ + CoreFrameworks/ + ML_Headers/ (targeted grep). |
| **#3 0/N findings ingested** | Layer 5 | **REPRODUCED** — `findings_sidecar:` ABSENT from `.E.1` frontmatter; 0 fix-design/F-NNN markers in body; canonical `.e.1` slice = **25** routed findings, none with a fix-design. (Hand-audit said "0/30" on the raw sidecar; deduped slice = 25.) |
| **#5 stale anchors / predates D-67..D-72** | Layer 1 | **REPRODUCED** — predecessor `.D` (should be `.D.1`); decision range `D-1..D-53` (should be `..D-73`); Phase A.1 expects HEAD `61ae3cc` (should be `dc37b24`); no `findings_sidecar:`/safeguard-phases. |
| seam (Layer 6) | Layer 6 | **MATCHED** hand-audit — 24 outbound forward-promise markers (detailed); inbound refs mostly to stale `.D` (1× `.D.1`). |

**No NEW substantive findings beyond the hand-audit** — which itself validates the hand-audit was thorough. `.E.1` verdict stands **RED** (amendment work, not a coding ship; punch-list = the hand-audit's).

## Calibration NOTES (tuning items for `/plan-dive` Layer 1)

The synthesis predicted both; confirmed:
1. **Symbol-existence checker is noisy on `.E.1`** — 10 "FABRICATION" hits are `<F>`-template-context false-positives (e.g. `NodeSlowPath_Cycle(NodeState<F>& node)` → "'F' not declared") + 1 path-prefix drift (`EngineSharded/Run.hpp` cited; real path `CoreFrameworks/EngineSharded/Run.hpp`). The REAL #2 signal (FPN_Atomic) needs the **targeted grep pairing** Layer 1 already prescribes. → `/plan-dive` Layer 1 should auto-filter `<F>`-template FPs + normalize the `CoreFrameworks/EngineSharded/` path prefix before reporting, else the checker's raw output buries the real signal.
2. **SPSCRing.hpp:12 "no MPMC/MPSC/SPMC" anchor is EXACT** (an earlier rg-display mangling was a terminal artifact, not corruption — file verified clean; no `.D.1` engine-code damage).

## Disposition

- **Instrument VALIDATED** for sequential dives `.E.2`→`.E.X`.
- **Layers 2+3 (composed `/precoding-audit-gate` 6-agent + `/blindspot-scan`) NOT fired here** — premature on an un-amended RED plan (would re-confirm RED). They fire as `.E.1` **cycle-2** AFTER the hand-audit punch-list amendments land (D-35 two-cycle convergence; the hand-audit was effectively cycle-1).
- `.E.1` guard-coverage-matrix rows: filled in Phase 2 (when `.E.1` is dived-to-GREEN), not at this calibration.
- Two `/plan-dive` Layer-1 tuning items above → fold into the codification-wave `/plan-dive` SKILL.md refinement (task #5 / Layer-1 hardening).

**Calibration verdict: PASS.** Proceed per D-73 phases: B (this) done → **A** (runtime-confirm on disposable clone) next.
