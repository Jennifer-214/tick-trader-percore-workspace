---
type: ledger-template
class_id: 59
title: Filesystem-as-interface artifact identity (an operator-facing artifact tree that is simultaneously a UI, a loader input, and a persistence store — with no grammar SSoT, no identity guard, and no tombstone discipline)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-08-22
surface_tags: [ml-inference, training, gui, persistence, boot-time, operator-ux]
severity: high
recurrence_count: 30
last_amended: 2026-08-22
first_instance: pre-v5.10 (the flat `<family>_horizon_<N>` grammar's second parser)
closure_mechanism: ML_Headers/ModelPathSchema.hpp (the ONE grammar header — builders + parsers + state filenames) + the D-431 nested layout (one filesystem node per bundle) + the LOUD retired-form detector (H21 tombstone applied to a path form) + save-side dir provisioning (FoxDir_CreateParents in every state writer) + loud-fail persistence fopens + side-addressed records (summary_entry/summary_exit) + role-aware display badges + the build.sh cwd-symlink set (launch dir cannot fork the world). Spec: DESIGN_SPECS/data-disciplines/model-artifact-path-schema-discipline.md
sister_classes: [12, 13, 18, 21, 44, 51]
decision_refs: [D-430, D-431]
---

# Class 59 — filesystem-as-interface artifact identity

## The shape

A directory tree that HUMANS browse, LOADERS parse, TRAINERS write, and STATE persists into —
with the grammar hand-copied per consumer, identity carried only by filenames, and no guard
watching any of it. Because the surface has no class/spec/CI (unlike registry, wire, cfg,
snapshot), defects accumulate silently and are discovered by the operator hitting them live.

## Sub-shapes (each with a measured instance from the 2026-08-21/22 census)

- **A · grammar divergence** — N parsers, M builders, hand-copied: three `_horizon_` acceptance
  rules (S2-F9, measured matrix: bounds, split-rule, truncation divergences); aliased spellings
  double-loading the canonical dir as two ensemble arms (S2-F5).
- **B · collision by shared name** — two writers, one filename: the exit run's `summary.txt`
  destroyed the buy record twice (D4/D-e; twins then run_1); `Save Run` wrote exit models as
  `buy_signal.json` (S2-F3).
- **C · identity-free artifacts** — a loadable file whose identity nothing checks: unstamped
  models load with every check vacuous (S2-F6); a cancelled train saved a VALID zero-tree husk
  over the real model (scan-2 NEW-1); mislabelled backups held a different horizon's model
  byte-for-byte (S2-F8 refresh).
- **D · creation-gap treadmill** — the writer needs a dir nothing creates: bandit/Thompson state
  silently unwritable per new family (S2-F1/NEW-2 — the manual mkdir stopgap was eaten twice in
  ONE day).
- **E · launch-cwd world forking** — every relative path resolves per launch dir: three divergent
  `sharded_snapshot.dat`, two `backtest.cfg` 348 lines apart, forked logging + GUI state (B-9).

## Detection signatures

- path grammar (`horizon_`/role filenames/state filenames) built or parsed OUTSIDE the schema
  header;
- an artifact writer whose failure path is a bare `return 0`;
- one filename reachable from two writers with different roles/sides/meanings;
- a loader that silently returns "nothing found" where a retired path form could sit;
- any cwd-relative persistent path not in the `build.sh` symlink set.

## False-positive surface (M3 — legitimate siblings, NOT instances)

- **Walker-inert operator dirs by design**: quarantine/backup dirs named OUTSIDE the grammar
  (`_quarantine_*`, `<fam>_backup_h<N>_<date>`) are the *sanctioned* parking mechanism — their
  inertness is the feature. An instance requires a LOADER or DISPLAY consuming the surface.
- **Test fixtures** building paths inline — they pin the grammar from outside on purpose.
- **Consumers of path VALUES** (cfg fields, stamp-adjacent sidecars) that never construct grammar.
- Not Class 21 (parallel registries — no registry here to parallel); not Class 13 (worker snap
  drift — this is disk identity, not thread capture); overlaps Class 44 where a written artifact
  has no live reader.

## Status at codification

Closed structurally at the D-431 nested ship (engine `609651f` + the same-day no-regret set) for
every capital-path sub-shape; residuals homed in the E.1.2.D plan (B-3 Past-Runs per-side rows,
B-8 shared-snapshot contention → decoupling roadmap, H21 ledger rows staged pending the operator's
D-394 bless).
