# Class 47 — Split-brain control authority (the safety gate and the execution authority key off different fields)

**Codified:** 2026-06-13 (v5.15.5.F.4d.1.E.0.10; NEW-1). **Severity:** CRITICAL (capital-safety; unguarded live capital reachable). **recurrence_count:** 1 (NEW-1; the boot/authority lift of the SSoT family).

## The pattern

ONE capital/safety/capability concept is governed by TWO (or more) INDEPENDENT fields, and the readers split: a **validation/safety gate** keys off field A while the **execution authority** keys off field B, with nothing coupling them → they silently decouple. The safety gate guards a door that isn't the real door.

Canonical: `use_real_money` gates EXECUTION (the OMS `MASK_OMS_STATE_LIVE_TRADING` bit + secrets + adapter, `Run.hpp:577`); `trading_mode` gates ONLY the safety pre-flight (`LiveReadiness_Verify:230`) + the strict-flips (`NormalizeForMode:2009`). BOTH decoupling directions are reachable:
- `use_real_money=1 + trading_mode=paper` → real capital, the ENTIRE pre-flight suite bypassed (WARN-only).
- `trading_mode=live + use_real_money=0` → pre-flight REFUSES boot, NO orders ever fire.

A fixture where the two fields AGREE hides it (the vacuous-test trap — vary the divergence cells, per `characterization-test-discipline.md`).

## Distinct from / sibling to

- **Class 43** (money value derived ≥2 ways) — same concept but a VALUE computed two ways; Class 47 is a CONTROL concept gated by two FIELDS.
- **Class 45** (reconstruct reads a different source field) — a forward-vs-reconstruct divergence; Class 47 is two CONCURRENT live authorities for one decision.
- **H21 / Class 40** (Knight — identifier reuse after retire) — Knight is sequential (a retired slot reused while its dead code is compiled-in); Class 47 is concurrent field-DUPLICATION of one control. Knight-adjacent: both end in "the wrong code path runs because a control's meaning is ambiguous."
- SSoT-violation family (43 / 45 / 47): 43 = value/formula, 45 = source-field forward-vs-restore, 47 = control-flag/authority.

## Detection signature

A capital/safety/capability concept whose **safety/validation gate reads a different field than its execution authority**. Grep the gate's predicate field + the execution path's field; if they differ for one concept → Class 47. Red flag: two operator-settable fields that "should agree" with no single derivation + no conflict-refuse.

## Structural fix

**Single-authority predicate** (`DESIGN_SPECS/framework-patterns/single-authority-predicate-for-mode-gating.md`): collapse to ONE predicate every authorizer routes through; the other field → derived / back-compat alias + tombstone (H21). The illegal cells become UNREPRESENTABLE (a guard could only DETECT them). The predicate is also the H22 scale-out seam (body relocates global→per-shard, zero call-site edits). Co-harden: hot-reload-protect the survivor; expose only the survivor in the GUI; tooltip-parity on the SAFETY_CRITICAL field.

## Closure mechanism

CI detector — flag a capital/safety concept gated by ≥2 independent fields where the gate-reader ≠ the execution-reader (candidate; folds into the per-registry-integrity check family). The single-predicate refactor is the structural close. H-promotion deferred to Stage 5 per `pattern-codification-lifecycle.md`.

## Canonical instance

NEW-1 (v5.15.5.F.4d.1.E.0.10) — see decision-log D-217 + DESIGN_SPEC `single-authority-predicate-for-mode-gating.md`. `use_real_money`/`trading_mode` collapsed to `ControllerConfig_IsLiveCapital`; legacy single_core LIVE hard-refused (H21); 6 co-hardening items (hot-reload protect, conflict-refuse, GUI single-surface, tooltip-inversion fix, SHADOW tombstone, stamp-train-time pin).
