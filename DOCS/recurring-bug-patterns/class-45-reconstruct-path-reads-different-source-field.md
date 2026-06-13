# Class 45 — Reconstruct-path reads a DIFFERENT source field than the forward path

**Codified:** 2026-06-12 (v5.15.5.F.4d.1.E.0.10; TECH_DEBT-186 harvest). **Severity:** HIGH (capital-correctness; silent divergence). **recurrence_count:** 2 (A1, A25).

## The pattern

A restore / reconstruct / replay / recovery path re-derives a value the FORWARD (live) path computes — but reads a **DIFFERENT source field** to do so → the two silently diverge. The forward value and the reconstructed value are *supposed* to be equal; a fixture where the two sources happen to coincide hides it (the vacuous-test trap — vary the fields whose divergence the assertion could mask, per `characterization-test-discipline.md`).

**Distinct from:**
- **Class 43** (money value derived ≥2 ways without single-sourcing the COMPUTATION) — same source, different FORMULA. Class 45 is a DIFFERENT SOURCE FIELD.
- **Class 18** (parallel emit/parse mirror that drifts) — Class 45 is a forward-vs-reconstruct divergence, not two mirrored registries.
- Sibling: AR-7 (structural-pattern false-completeness).

## Detection signature

Find a restore/replay/reconstruct function that ASSIGNS a value the forward path also computes, then compare the SOURCE field:
- forward path: `X = f(source_A)` — e.g. `live_tp = entry × (1 + ResolvePerFillTpPct(strategy, cfg))`
- reconstruct path: `X = g(source_B)` where `source_B != source_A` — e.g. restore reads global `cfg.take_profit_pct`; replay reads `OrderEvent.tp`
- Red flag: the two assign the SAME logical field (`live_tp`, `original_tp`) from DIFFERENT inputs, with no shared resolver.

## Canonical instances

- **A1** (`.E.0.10`, CLOSED): warm-restart recomputed `live_tp`/`live_sl` from the GLOBAL `take_profit_pct`, while the fresh-entry dispatcher read the per-strategy override (`simpledip_tp_pct` etc.) → a restored position exited at a different price than while live. **Fix:** single-source `ResolvePerFillTpPct`/`ResolvePerFillSlPct`, called by BOTH the entry dispatcher AND the restore path.
- **A25** (`.E.0.10`): post-fix, the event-log replay (`Portfolio_FromEventLog`) reconstructs `original_tp` from the expected-entry `OrderEvent.tp`, while the live path (`handle_buy_fill`) sets `fill × (1 + tp_pct)` → live ≠ replay. Dispositioned option (b) (documented non-reproducible + F-059 freeze-flag — the binary snapshot is the primary recovery); the full single-source rides the `.E.1` venue-net reconcile (`data-disciplines/per-node-position-ownership-model.md`).

## Structural fix

Single-source the derivation that BOTH paths call (the resolver-SSoT shape A1 established). The forward path and every reconstruct/replay/restore path call the SAME resolver — never re-derive from a sibling field. → `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` v1.3.

## False-positive surface

- A reconstruct path that reads a DIFFERENT field BY DESIGN (the two are genuinely independent quantities, not the same logical value) is NOT this class. Test: would the forward value and the reconstructed value be expected to be EQUAL? Yes + different sources → Class 45. Different quantities → not.
- A reconstruct path that reads the SAME field but applies a different FORMULA is Class 43, not 45.
