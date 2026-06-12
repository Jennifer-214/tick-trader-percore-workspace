---
type: audit-methodology
stage: 3-first-canonical
version: 1.0
established: 2026-06-12
tags: [audit-methodology, test-discipline, capital-safety, determinism]
surface: [hot-path, slow-path, oms-drainer, persistence, live-trading]
sister_specs: [adversarial-multi-agent-audit-methodology.md, audit-driven-pre-coding-gate.md]
applies_at_skills: [/readiness, /test-strength-audit, /blindspot-scan, /precoding-audit-gate, /plan-dive, /accounting-audit]
canonical_instance: tests/controller_test.cpp oms-ts-1 / oms-ts-1b (Net-1, .E.0.10)
---

# Characterization-test discipline (the 3-lens pass)

**Established:** 2026-06-12 (v5.15.5.F.4d.1.E.0.10 Net-1; TECH_DEBT-164 part 2). **Status:** ACTIVE — the writing discipline for any characterization / golden-master test on a capital, determinism, or correctness-critical surface.

A **characterization test** freezes the REAL output of a code path on a fixed input so a later change (the `.E.1` Core→Node rename, a refactor, a re-pack) that silently shifts behavior becomes an instant red build instead of a silent capital loss. It is the [[feedback_golden_master_over_reimplemented_oracle]] model (freeze real output + diff; never a reimplemented oracle that drifts). This spec is the **how-to-write-one-right** companion: a characterization test that passes is not automatically a characterization test that *protects*. Three lenses separate the two. A test that fails any lens is theater — it goes green and guards nothing.

The canonical first instance is `oms-ts-1` / `oms-ts-1b` (`tests/controller_test.cpp`): the fee-EXACT fill→balance/P&L/fees round-trip. Every rule below cites it.

## The 3-lens pass

### Lens 1 — COMPLETE: freeze the whole write-set, not the headline value

The path writes more than the one number you came for. Freeze **every field the path mutates**, because the change you're guarding against can shift any of them, and an assertion that names only the headline lets the rest drift silently.

`oms-ts-1` does not stop at `balance`. It freezes `total_fees`, `realized_pnl`, `balance`, the **maker/taker bucket split** (`total_taker_fees` / `total_maker_fees`), `taker_fills_count` / `maker_fills_count`, the bucket invariant (`total_fees == maker + taker`), `last_was_win` bit, `last_realized_return[0]`, and `ks_peak_balance` — the *secondary* state a fill writes. A maker/taker mask-inversion leaves the aggregate `total_fees` correct but flips the buckets; only the split catches it.

**Failure mode this prevents (sister AR-7, structural-pattern false-completeness):** what's OUTSIDE the assertion's reach is the gap. Before writing the asserts, enumerate the path's complete write-set (grep the function's stores) and freeze each — do not freeze the field you happened to be thinking about.

### Lens 2 — NON-VACUOUS: the assertion must be able to FAIL (hand-derive; never capture-match)

A characterization assertion is worthless if it cannot go red on a real divergence. The trap is **capture-matching**: run the engine, copy whatever it produced into the assertion. That assertion is a tautology — it asserts the engine equals itself, and a regression that shifts the value *also shifts the "expected"* if you ever regenerate it carelessly. (The `oms-ts-2` false-invariant was exactly this: an assertion written to match the engine's output, proving nothing — it later masked the D-190 gross-formula drift.)

**The rule:** values are **HAND-DERIVED from the booking code and shown in the comment**, not capture-frozen. `oms-ts-1` derives `booked_fee = 1200 × 0.001 = 1.20`, `exit_fee = 1212 × 0.001 = 1.212`, `gross = 600 × 0.02 = 12.00`, `net = 12.00 − 2.412 = 9.588` — from reading `OrderManager_HandleFill` + `handle_sell_fill` + the `Money_FillGross` SSoT. A GREEN run then **cross-checks the human's reading** of the code; a RED run is a real divergence to investigate, never a "just edit the number to match" fixup.

**Vary the fields whose divergence the assertion could mask.** An all-winner test cannot catch a net-SIGN regression → `oms-ts-1b` adds the LOSS round-trip (`net = −14.412`, `last_was_win = 0`). Round inputs cannot exercise a rounding split → see the coverage disclaimer below. For **F-059** specifically, two divergence fields must be varied or the net is false-green:
- **Slippage book-price (paper-mode only).** The fill books at `tick ± slip` (entry `+`, exit `−`), NOT at `live_tp`: exit side `CoreFrameworks/Portfolio.hpp:201-203` (`exit_price = exit_price − exit_price×slippage_pct`); per-event branchless sign at `CoreFrameworks/ControllerEventLoop.hpp:1873-1890`, gated `effective_slip_pct = not_live ? slip_pct : 0` — so **live books the raw executionReport price** (slippage 0), neither `tick±slip` nor `live_tp`. `live_tp` is the exit *trigger* (the SG compare), never a booked price — conflating them mis-models both paths.
- **Flat-`tp_pct` overwrite of the strategy TP.** `CoreFrameworks/ExecutionCore.hpp:541-545`: when `tp_pct != 0`, `live_tp` is overwritten with the flat-percentage TP, **discarding** the strategy-computed volatility-scaled TP (e.g. Momentum's stddev-scaled `tp_offset`, `Strategies/Momentum.hpp:280-282`). A test that freezes only the flat-`tp_pct` exit masks the discarded stddev TP.

> These seams move as the code changes — and the precise line numbers above were themselves caught stale once (transcribed from a planning register instead of read from code; the AR-3 trap this very spec warns against). **Re-ground every file:line against current code at write time** (regen `CODE_MAP`, grep the symbol); task #7's finding-register carries the authoritative current seam set, but verify it too — a register is a planning artifact, not a guard.

### Lens 3 — NOT-FROZEN-BUG: characterize current CORRECT behavior; if it's wrong, fix-then-freeze

Characterization freezes current behavior to catch **regression** — but if the current value is itself **wrong**, freezing it enshrines the bug as the golden, and every future run defends the bug. This is the [[feedback_two_foundations_determinism_vs_correctness]] split: the determinism net (freeze current behavior) and the correctness fix (is the value right?) are **orthogonal foundations** — do not let "freeze it first" cement a defect.

Lens 2's hand-derivation is what surfaces this: deriving the value from the code forces the question *is this value correct?* When characterization **surfaces a real bug** — A1 (warm-restart recomputed TP/SL from the global, ignoring the per-strategy override), `oms-ts-2`→D-190 (gross open-coded two ways, 1-ULP drift), persist-8 (paper-reset zombie-active) — the test is **paired with the FIX** and freezes the **corrected** value. Char-now-paired-with-fix, never freeze-the-symptom. (The fix's do-now-vs-defer is the separate subsumption question; the *characterization* of the corrected value is not deferrable — a net that freezes a known-wrong value is worse than no net.)

## Companion disciplines (mandatory, not optional polish)

- **Coverage disclaimer — be honest about what the inputs do NOT exercise.** `oms-ts-1` carries a `D-190 COVERAGE DISCLAIMER`: its inputs are ROUND, so every `Money_Mul` has zero 8dp remainder → the 1-mul (`Money_FillGross`) form is value-identical to the 2-mul form *here*; this test does NOT exercise the D-190 split (that divergence is guarded by the divergent-input sibling + `check_money_gross_single_source.py`). State what a green run does NOT prove — a silent coverage gap reads as "covered" (sister AR-1, categorical claim over an un-enumerated set).
- **`// ADV-REFUTE` is binding** ([[feedback_adversarial_framing_default_for_checks]]). The derived values get an **independent** FIND/REFUTE re-derivation (≥2-3 agents, distinct lenses: vacuity/faithfulness · value-correctness · regression/completeness) **before** the test is "done" — the maker does not grade their own arithmetic (AR-8, self-attested verification). `oms-ts-1`'s panel folded 3 gaps the self-check missed (the D-190 overclaim, the maker/taker bucket, the loss/sign variant). Stamp the marker with the date + what the panel found.
- **Deterministic input first.** The golden is only as trustworthy as the replay; if the input is locale-fragile or FP-nondeterministic, fix THAT before freezing ([[feedback_phased_pre_rework_correctness_foundation]] net-gating).
- **Intentional change = reviewed regeneration.** A deliberate behavior change means a reviewed golden regeneration (guard with `/test-strength-audit`, like test-deletion justification), never a quiet number edit.

## How to apply (checklist)

1. Identify the path + grep its **complete write-set** (Lens 1).
2. **Hand-derive** each frozen value from the booking code; put the derivation in the comment (Lens 2).
3. Confirm each value is **correct**, not just current; if a derivation surfaces a wrong value, pair the test with the fix and freeze the corrected value (Lens 3).
4. **Vary** the fields whose divergence the assertion could mask (sign, slippage, alternate-formula inputs).
5. Write the **coverage disclaimer** (what the inputs don't exercise).
6. Get the **independent `// ADV-REFUTE`** re-derivation before declaring done.

## False-positive surface

- A test that captures-then-asserts is NOT automatically vacuous **if** the captured value is independently hand-derived and the capture is just a typing convenience — the test is the derivation, the source is incidental. The vacuity is in *deriving the expected FROM the run*, not in the two happening to match.
- A headline-only assertion is acceptable when the path provably writes exactly one field (rare; prove it by enumerating the write-set, don't assume it).
- Freezing current behavior on a CHANGES-BY-DESIGN surface is not Lens-3 violation — it's the wrong test entirely (two-foundations: do not characterize what you are about to deliberately change; e.g. `conc-5` concurrency model, the drainer→per-node absorption — OUT of Net-1 by design).

## Canonical references

`tests/controller_test.cpp` oms-ts-1 / oms-ts-1b (first canonical); [[feedback_golden_master_over_reimplemented_oracle]]; [[feedback_two_foundations_determinism_vs_correctness]]; [[feedback_passing_test_is_not_verification]]; `adversarial-multi-agent-audit-methodology.md` (the `// ADV-REFUTE` engine); Class 43 (the money-computation anti-pattern these tests most often surface). Governs Net-1 tasks #7 (F-059) + #8 (MED-tier characterization).
