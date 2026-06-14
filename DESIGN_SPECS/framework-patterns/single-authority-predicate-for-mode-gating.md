---
type: framework-pattern
stage: 2-draft
version: 1.0
established: 2026-06-13
tags: [framework-discipline, capital-safety, ssot, scale-invariance, structural-fix]
surface: [cfg-flow, boot-time, live-trading]
sister_specs: [per-node-purity-scale-invariance.md, capital-allocation-policy-pattern.md, dead-code-and-identifier-retirement-discipline.md, universal-cfg-field-registry-pattern.md]
applies_at_skills: [/trace-deps, /accounting-audit]
---

# Single-authority predicate for mode / capability gating

**Established:** 2026-06-13 (v5.15.5.F.4d.1.E.0.10 NEW-1). **Status:** Stage 2 DRAFT — first canonical = NEW-1 (the `use_real_money`/`trading_mode` split-brain collapse). **Closes:** RBP Class 47 (split-brain control authority) at the structural-fix layer; serves H22 (scale-invariance) + H21 (identifier retirement).

## The problem it solves

When ONE capital/safety/capability concept (e.g. "is this live capital?") is governed by MORE THAN ONE field, the readers drift: a validation/safety gate keys off field A while the execution authority keys off field B, and the two silently decouple (RBP Class 47 — "the gate guards a door that isn't the real door"). Canonical instance: `LiveReadiness_Verify` gated on `trading_mode==LIVE` while the OMS authorized real orders on `use_real_money` → real capital with the pre-flight bypassed AND pre-flight-refuse with no orders, both reachable.

## The pattern

1. **One predicate is the SOLE authority.** `inline bool <Concept>_Is<Mode>(cfg) := (cfg.<survivor> == <MODE>)`. Every authorizer — execution gate, safety pre-flight, snapshot/state selection, reset interlock, display — routes through this ONE function. No reader re-derives the concept from a different field.
2. **The survivor is the framework-governed field.** Pick the field the framework already governs (registry-resident, stamp-bound, metadata-tagged, multi-state) over a hand-rolled orphan. Richer type (an enum over a bool), existing drift-checks, and audit visibility all favor it.
3. **The retired field becomes a derived / back-compat ALIAS, tombstoned (H21).** Operators have it on disk → parse it as a write-through alias (`old=1` ⇒ set the survivor) + WARN + a conflict-REFUSE when the alias and an explicit survivor disagree. Delete the internal struct field; keep only the externally-visible cfg-key slot parse-compatible (the H21 reconciliation: delete the dead code, never recycle the visible slot).

## The scale-out seam (why a predicate, not inlined checks)

The predicate is ALSO the horizontal-scale seam (H22). Today its body reads the global cfg; at scale-out (per-cluster / per-node) the body relocates to read the resolved per-shard cfg — and because every authorizer already routes through the ONE function, the relocation is a single body edit, ZERO call-site changes. Adding the (N+1)th shard needs no authorizer change (the H22 operational test). Inlining `field==MODE` at N sites would force an N-site migration at scale-out. Sister to the H18 sidecar-override seam: centralize the variation point so the framework can move it once.

## Mandatory co-hardening (the authority must not re-decouple)

- **Hot-reload / mutation protection:** if the concept is a boot-time latch, the survivor field must be in the protected save/restore set so a mid-session cfg reload can't flip it (else the decouple re-opens on the reload path).
- **Single settable surface:** the GUI / operator surface exposes ONLY the survivor (not the derived alias), else the alias is independently flippable and re-opens the gap.
- **Doc/tooltip parity:** the survivor's operator-facing description must match its enum values exactly (a SAFETY_CRITICAL field with an inverted tooltip is its own hazard).

## Detection signature

A capital/safety/capability concept gated by ≥2 independent fields where the **gate-reader ≠ the execution-reader**. Grep the safety/validation gate's field, grep the execution authority's field; if they differ for one concept → Class 47. CI candidate: flag two distinct fields both feeding one concept's authorizers.

## Canonical instance

NEW-1 (v5.15.5.F.4d.1.E.0.10): `ControllerConfig_IsLiveCapital(cfg) := (trading_mode == TRADING_MODE_LIVE)`; `use_real_money` → parse alias + tombstone; legacy single_core LIVE hard-refused (H21 dead-capital-path, not repointed-and-kept-alive); the survivor `trading_mode` is registry/stamp/SAFETY_CRITICAL/3-state. The predicate relocates to `cluster.trading_mode` at `.E.1` (per-cluster authority), zero authorizer edits.
