---
type: meta-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-06-12
tags: [capital-safety, ssot, structural-fix, migration-discipline, data-oriented-design]
surface: [hot-path, slow-path, oms-drainer, persistence, live-trading]
sister_specs: []
explains_classes: [Class 25, Class 26, Class 27, Class 43, Class 44, torn-read-class]
explains_findings: [A1, A9, A10, A20, A21, A22, A23, A24, A25]
---

# Representation-migration completeness (the meta-pattern under the .E.0.10 capital-bug cohort)

**The one-line meta-pattern.** When you migrate a *value's representation* incrementally — its **layout** (24B→16B), its **scope** (single-core flat → per-core shadow), its **derivation** (expected-entry → per-fill price), or its **threading** (single-writer → a second writer thread the new topology added) — you create a **second representation of the same value**. Unless the migration rewires **every** consumer in the same change, a consumer silently keeps reading the **OLD/stale** representation. The value is correct in one representation and stale in another; the bug **compiles, runs, and passes most tests** — it only shows on the input/timing/thread-interleaving where the two diverge.

This is the structural root the `.E.0.10` adversarial sweep kept re-finding. It is not a collection of unrelated bugs — it is **one meta-pattern with four sub-shapes**, and naming it is what makes the fix structural (single-source) instead of twenty patches.

## Why it recurs here (the honest cause — not sloppiness)

Incremental migration is the *correct* way to evolve a complex capital system: small steps, each compiling, each shippable. This engine did **three** large representation migrations — single-core → per-core sharding, binary → decimal money (24B→16B), and expected-entry → per-fill pricing (Phase-14). Each step that adds a representation **without retiring the old one + rewiring all of its consumers** leaves residue. Residue from three overlapping migrations is exactly this cohort. The skill on display is doing the migrations at all; the discipline this spec adds is *finishing* each one.

## The four sub-shapes (with the family they map to)

| sub-shape | the two representations | bug class | findings |
|---|---|---|---|
| **Scope** | flat global value ↔ per-core shadow (`cores[slot]`) | Class 25/26, H22 | A24, A10 |
| **Derivation** | absolute (expected-entry) ↔ per-fill (actual-fill) | Class 44, A1-family | A25, A1, A10 |
| **Binding** | a migrated field ↔ its old/orphaned consumer (or producer) | Class 44 | A9, A11/A12, A16 |
| **Threading** | single-writer ↔ a 2nd writer thread the new topology added | torn-read class (#10) | A22, A23 |

(The `.E.0.10` reconcile cohort A20/A21 is a *sibling* root — untested live-only code — not this meta-pattern; keep them distinct.)

## The structural fix (single, repeated shape)

**Single-source each value's representation.** One canonical home; every other "representation" is a *derived view* computed on demand, not a parallel store that can go stale:
- **Scope:** mutate `cores[slot]` directly (the per-core view IS the source), or sync the mutated flat field into `cores[slot]` before any consumer reads it — never leave a flat mutation that a `cores[slot]` reader can't see (A24).
- **Derivation:** compute the consumed value from the *one* authoritative input — e.g. resolve TP from the per-fill price at every read-site via the shared `ResolvePerFillTpPct` SSoT, so the absolute `original_tp` is display-only, never a trigger (A25, A1).
- **Binding:** at a field migration, enumerate **every** consumer (sister to Class 33 consumer-enumeration) and rewire each; **delete** the old representation so a stale read is a compile error, not a silent zero (A9, A11/A12).
- **Threading:** publish the cross-thread value through the **one** sync primitive the design already has (the `ParameterSlot` seqlock) — fold the bare `intended_*`/`allocated_balance` mirrors into the seqlock'd pack; never a bare load of a >8-byte field written by another thread (A22/A23).

## The prevention discipline (the "as we go" rule)

A **representation migration** earns the same gate a **deletion** earns (Class 33): before it lands, (1) enumerate ALL consumers of the value, (2) name the single-source target, (3) verify no consumer is left reading the old representation. A migration that adds a representation without these three is incomplete — and an incomplete migration is this meta-pattern waiting to fire.

## Mechanical enforcement (use the tools; build the missing ones)

EXISTING guards already cover parts of the family — use them, don't hand-check:
- `tools/check_per_core_registry_integrity.py` — Class 25/26 paired-access + **UNINDEXED-GLOBAL** detector (the Scope sub-shape).
- `tools/check_money_gross_single_source.py` — the Derivation/SSoT sub-shape for gross P&L (D-190).
- `tools/scan_class_27_full.py` — scalar cfg-mirror (Binding-adjacent).
- `cross-thread-multiword-read-consistency-discipline.md` + the reader-side rule — the Threading sub-shape.

The GAP (the missing structural close, M7): **one struct-field produce/consume tracker** — sister to `/dependency-chain-trace` but at FIELD granularity — flags `write-with-no-live-read` / `read-with-no-live-write` / `>8B cross-thread-written field read outside a seqlock` / `flat-mutation-then-cores[slot]-read`. It catches all four sub-shapes mechanically, doubles as the field-access map a DOD re-pack (TECH_DEBT-159) needs, and feeds the `subsystem-designs/` catalogue. The Class-44 CI-check candidate is its seed; this tool is the meta-pattern's permanent guard. (Scope as a future discipline-ship.)

## Cross-references

`single-source-of-truth-discipline.md`; Class 43/44 + Class 25/26/27 + the torn-read class (`DOCS/recurring-bug-patterns/` + `concurrency-patterns/cross-thread-multiword-read-consistency-discipline.md`); H22 (per-node purity); `subsystem-designs/exit-chain-tp-sl-design.md` (the as-built design these divergences sit in); `plan_checks/E.0.10-finding-disposition-register.md` A1/A9/A10/A20-A25.
