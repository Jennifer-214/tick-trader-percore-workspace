---
type: data-discipline
stage: 3-first-canonical
tags: [data-oriented-design, framework-discipline, ml-inference, operator-ux]
surface: [ml-inference, boot-time, gui, training]
sister_specs:
  - meta-disciplines/dead-code-and-identifier-retirement-discipline.md
  - framework-patterns/x-macro-registry-with-presence-dispatch.md
  - meta-disciplines/advertised-capability-never-exercised.md
applications:
  - "D-431 nested-layout ship (engine 609651f) — the first canonical: ModelPathSchema.hpp + walker child-scan + loud retired-form detector + picker child-probe + migrate script"
created: 2026-08-22
decision_refs: [D-430, D-431]
---

# Model-artifact path schema discipline — the filesystem IS an interface

## The class this closes (RECURRING_BUG_PATTERNS Class 59)

Every other persistence surface in this codebase — registry, wire format, cfg, snapshot — carries a
class, a spec, and a guard. The **model-artifact tree carried none of the three**, and H21 covered
no path form and no role filename (S2-F11). The consequence, measured as a ~30-instance census
across three i-class scans (2026-08-21, re-derived 2026-08-22): defects accumulated silently for
months because *nothing was watching a surface that is simultaneously an operator UI, a loader
input, a trainer output, and a persistence store*.

## The schema (D-431, operator-decided NESTED)

```
models/<class>/<family>/                          ← the BUNDLE node (= cfg node_model_dir)
models/<class>/<family>/horizon_<N>/<role>.json[.stamp]
models/<class>/<family>/{bandit_state, exit_bandit_state,
                         buy_thompson_state, exit_thompson_state}.json
models/<class>/<family>/horizon_<N>/{summary_entry.txt | summary_exit.txt}
```

One filesystem node per logical unit: family delete = one `rm -r`, backup = one `cp -r`, the family
glob cannot over-match prefix-sibling backups, and bundle-scoped state lives inside the node its
savers target. `<class>` derives ONCE per run from the run's PRIMARY label kind (S2-F4: a mixed
Label-Kind CSV must never fragment one family across two class trees).

## The disciplines

1. **One grammar header.** `ML_Headers/ModelPathSchema.hpp` owns every builder
   (`ModelPath_HorizonDir`) and every parser (`Model_ParseHorizonSibling` — canonical round-trip
   included — and `ModelPath_ParseHorizonChild`) plus the state filenames. A new consumer starts
   from the schema; an inline `snprintf` path grammar in consumer code is an instance of the class.
   (Lineage: this is the third one-rule-N-consumers extraction on this surface, after
   `Training_ResolveRole` and the 3G-ii matcher unification.)
2. **Canonical spelling only.** A parser accepts exactly the spelling the builders emit (the leaf-8
   round-trip `strcmp`); aliased spellings (`07500`, `+7500`, …) are rejected, because every loader
   REBUILDS paths from parsed ints and an alias therefore double-loads the canonical dir.
3. **Path forms are H21 identifiers.** A retired form is TOMBSTONED LOUDLY, never silently
   abandoned: the walker keeps a diagnostics-only probe for the retired flat form
   (`<family>_horizon_<N>` siblings) and prints the exact `mv` fix; the picker marks un-migrated
   dirs "FLAT-FORM: migrate". An un-migrated artifact must never become silently invisible — that
   is the exact failure shape the discipline exists to kill. Ledger coverage of path forms + role
   filenames extends H21 SOURCES (rows staged; operator D-394 bless applies).
4. **The writer that needs a dir provisions it.** Savers call the mkdir SSoT
   (`FoxDir_CreateParents`) on their base dir; loaders NEVER mkdir (read paths don't provision).
   Manual mkdir stopgaps are a treadmill — measured eating its own stopgap twice in one day.
5. **State writers fail LOUD.** A persistence `fopen` failure prints path + errno; a bare
   `return 0` swallowed an unwritable state path for a family's whole lifetime.
6. **Artifact records are side-addressed.** `summary_entry.txt` / `summary_exit.txt` — a shared
   filename across roles is a collision class (it destroyed the operator's best model's record
   twice). Displays follow the record they show (role-aware badges).
7. **cwd must not fork the world.** Every cwd-relative persistent surface (models/, data/,
   logging/, cfgs, GUI .ini) is symlinked into every build dir by `build.sh` (the engine.cfg
   convention, generalized) — measured pre-fix: three divergent snapshot files, two cfgs 348 lines
   apart.

## Detection heuristics

- grep for `_horizon_`/`horizon_` path grammar OUTSIDE ModelPathSchema.hpp (builder or parser) →
  instance of discipline 1.
- an artifact writer whose failure path is a bare return → discipline 5.
- a filename shared by two writers with different roles/sides → discipline 6.
- a loader silently returning 0 where a retired form could plausibly sit → discipline 3.

## False-positive surface (M3)

- Deliberately walker-inert operator dirs (quarantines, dated backups outside the grammar) are NOT
  instances — inertness-by-grammar is the *sanctioned* way to park artifacts.
- A consumer reading a path from cfg/stamp VALUES (not building grammar) is not an instance.
- Test fixtures build paths inline by design (they pin the grammar from outside); the schema header
  is for production consumers.

## History (why the nested fork was decided the way it was)

Scan-2's original verdict ("nested WORTH IT, not close, before leg 4") was **refuted as framed** by
its own `/decision-check` (reports: `plans/v5.15-live-readiness/reports/2026-08-22-Da-decision-check/`):
the "no node for the bundle" argument was factually wrong (savers write the same path under both
layouts — the defect was dir *creation*), and the leg-4 trigger bound to the mkdir fix, not the
migration. The unanimous no-regret set landed first; the operator then chose NESTED on the honest
cost sheet (~13-15 sites, 3 function restructures, one focused day) for the ergonomics + the
schema-SSoT consolidation moment + the decoupling-roadmap shape — and it shipped same-session.
