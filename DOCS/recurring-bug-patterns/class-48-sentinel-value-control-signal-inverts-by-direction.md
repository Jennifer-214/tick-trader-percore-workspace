---
type: ledger-template
class_id: 48
title: Control intent encoded as a context-dependent sentinel VALUE instead of an explicit flag (the "magic value" veto that inverts under the opposite direction/branch)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-06-14
surface_tags: [hot-path, slow-path, capital-safety, branchless-dispatch, gate-dispatch, ssot]
severity: high
recurrence_count: 1
first_instance: 2026-06-14 (v5.15.5.F.4d.1.E.0.10 gate-substrate 3-I→3-A cascade — the A13 no_trade_band port: suppressing an entry by publishing `bg_price_threshold = Money_Zero()` as a "no-fire sentinel" fires on EVERY tick for a buy-ABOVE strategy [Momentum, the only `GATE_FLAG_BUY_ABOVE` setter] because `price_above = price > 0` is always true; the cost-safety gate inverts into fire-always. Caught by the A-class adversarial pass + orchestrator code-read BEFORE landing — a prevented instance.)
closure_mechanism: route every "block/suppress this" control decision through an EXPLICIT, direction/context-agnostic control FLAG (here `GATE_FLAG_BUY_BLOCKED`, whose `blocked_mask = -blocked` forces the gate result to 0 regardless of price OR direction — GateParameters.hpp:182-184), NEVER a data VALUE a downstream comparison re-interprets. A value-encoded sentinel is safe ONLY if its effect is identical in EVERY branch that reads it; the moment a sibling branch (opposite comparison direction, a different mode) reads the same field with inverted meaning, the sentinel flips from "never" to "always." Optional structural hardening (footgun-proof the primitive): make the gate treat the sentinel as never-fire in BOTH directions so a stray sentinel cannot invert (engine hot-path change → heavier audit). **Detection — HEURISTIC (no clean mechanical check; the same zero-threshold is LEGITIMATE for buy-below):** flag a write of a known no-fire sentinel (`bg_price_threshold = ...Zero()` / a magic value) on a code path that can set the OPPOSITE-direction flag (`GATE_FLAG_BUY_ABOVE`) WITHOUT pairing the explicit veto flag. `/bug-check` carries the Class signature (registry-driven); a dedicated CI tool is a candidate IF it recurs (the False-positive surface makes a clean mechanical check non-trivial).
sister_classes: [2, 44, 47, 41]
sister_memories: [feedback_single_source_of_truth_discipline, feedback_adversarial_framing_default_for_checks]
---

# Class 48 — Control intent encoded as a context-dependent sentinel VALUE (the "magic value" veto that inverts in the other branch)

A control decision — "block this entry," "suppress this action" — is encoded as a magic DATA VALUE (a sentinel threshold, a zero, an out-of-range number) that a downstream comparison is expected to read as "don't fire." It **compiles, runs, and is correct in the branch the author tested** — but the value's effect is **direction/context-dependent**: a sibling branch (the opposite comparison direction, a different strategy/mode) reads the SAME field with the OPPOSITE interpretation, so the sentinel silently inverts from "never fire" to "fire always." On a capital path that is a runaway — a safety gate becomes fire-on-every-tick.

This is the *control-signal* sibling of the SSoT-violation family (Class 43/45/47): the bug is not a divergent value, it is a control INTENT smuggled through a data value whose meaning is not invariant across the branches that read it.

## The canonical instance (A13 no_trade_band, prevented 2026-06-14)

The "obvious" port of the legacy fee-breakeven entry gate was: when the signal is too thin to clear fees, suppress the entry by publishing `out->bg_price_threshold = Money_Zero()`. The buy gate computes BOTH directions and mask-selects on `GATE_FLAG_BUY_ABOVE` (GateParameters.hpp:171-184; hot twin ExecutionCore.hpp:355-368):
- `price_below = (price < threshold)` · `price_above = (price > threshold)` · `price_ok = (price_above & buy_above) | (price_below & ~buy_above)`.
- **buy-below** (MR/DIP/EMA/ML), `threshold = 0`: `price < 0` → never true → never fires. The sentinel WORKS. ✓
- **buy-above** (Momentum — the ONLY `GATE_FLAG_BUY_ABOVE` setter, StrategyParameters.hpp:619), `threshold = 0`: `price > 0` → ALWAYS true → fires EVERY tick. The cost-safety gate becomes buy-on-every-tick. ✗

The same field (`bg_price_threshold`), the same sentinel (`0`), inverts meaning by strategy direction. The author tests on a buy-below strategy, sees suppression, ships — and a Momentum core unconditionally buys.

## The fix (structural)

The engine ALREADY has the correct primitive: `GATE_FLAG_BUY_BLOCKED` (GateParameters.hpp:178-184) — `blocked_mask = -blocked` ANDs the whole gate result to 0 **regardless of price or direction**. Direction-agnostic by construction. The ML hard-blocks (StrategyParameters.hpp:1512-1520) and the Momentum quality filters (:1702-1726) already use it as THE "do not buy this cycle" mechanism. So: **to block, set the flag; never zero the value.** A13, if wired, sets `GATE_FLAG_BUY_BLOCKED` (zero new hot-path, zero wire bump, direction-safe), never a zero threshold.

## Recurring symptom
- A "don't fire / blocked" state expressed by assigning a magic value to a field a comparison reads, rather than setting an explicit boolean control flag.
- The value works in the branch under test, but the field is read by ≥2 branches with non-identical interpretation (opposite comparison direction; a mode that treats the value differently).
- "It suppresses correctly in my test (strategy X) but fires-always / never-fires in production (strategy Y)."

## False-positive surface (M3)
- A sentinel whose effect IS identical in every branch that reads it (e.g. `bg_price_threshold = 0` on a buy-BELOW-only strategy — `price < 0` is never true in any real tick; legitimate, and the codebase uses it for EmaCross's uptrend gate + the ML hard-blocks, the latter additionally pairing `GATE_FLAG_BUY_BLOCKED`). The class fires ONLY when a SIBLING branch reads the same field with inverted meaning.
- A genuine threshold value (a real price/qty bound), not a control sentinel — not this class.
- An explicit flag that ALSO zeroes a value for hygiene — fine; the flag is the control, the value is incidental.

## Canonical reference
`E.0.10-finding-disposition-register.md` § "GATE-SUBSTRATE ARCHITECTURE" (the A-2 refutation + orchestrator code-read); `GateParameters.hpp:171-184` (the direction mask) + `:178-184` (`GATE_FLAG_BUY_BLOCKED`, the correct primitive); `StrategyParameters.hpp:619` (the sole buy-above setter) + `:1512-1520` (the canonical flag-based block). Sister: Class 47 (split-brain control authority — control keyed off the wrong field), Class 2 (display↔execution — the no_trade_band GUI badge that gates nothing), Class 43/45 (SSoT-value family). [[feedback_single_source_of_truth_discipline]].
