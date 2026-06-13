---
type: data-discipline
stage: 2-draft
version: 1.0
established: 2026-06-13
tags: [capital-safety, oms-drainer, fill-path, protocol-normalization, scale-invariance, live-trading]
surface: [oms-drainer, fill-path, live-trading, persistence]
sister_specs:
  - per-node-position-ownership-model.md
  - cross-thread-multiword-read-consistency-discipline.md
  - per-node-purity-scale-invariance.md
  - decision-time-data-binding-pattern.md
parent_spec: per-node-position-ownership-model.md
living_spec: true
extends_when: "the .E.1 fill-path rework lands — backfill the reference application + promote stage 2→3; the full multi-fill handler (weighted-avg re-entry + partial-reduce) is the .E.1 deliverable, NOT built speculatively"
---

# Fill-path completeness + normalization discipline (spine 1 of the accounting-spine three-spines)

**Established:** 2026-06-13 (v5.15.5.F.4d.1.E.0.10; D-214 — the A16 fill-path cascade + the keystone-validation that produced the corrected three-spines framing). **Status:** DRAFT — the reference application is the `.E.1` fill-path rework; this spec captures the principle now so `.E.1` inherits **design**, not a forward-promise (the D-214 "named-not-designed" gap).

## Why this exists (the three-spines context)

The accounting/fill spine accumulated a cohort of capital-correctness findings (A16, the SELL-partial whole-close, A2/A4, A18, the 9-site torn-read class, A1/A24, A20/A21, the live-mode gate decoupling). A proposed single **keystone** tried to unify them as one "SSoT/ownership" problem — **REJECTED as over-lumped** (AR-6 recurrence; decision-log D-214). The corrected framing is **three orthogonal spines**, each its own discipline + structural fix, triaged per-finding by subsumption-not-adjacency:

1. **Fill-completeness / protocol-temporal-normalization** — THIS spec. The fill path's *actual* root.
2. **Cross-thread coherence** — `cross-thread-multiword-read-consistency-discipline.md` (publish-once / consume-many; the torn-read class).
3. **Per-node / per-cluster purity** — `per-node-purity-scale-invariance.md` (H22; one owner, pure derivation).

(A20 watermark-persistence + A21 reconciler-formula + the `use_real_money`/`trading_mode` live-mode gate are INDEPENDENT bugs, NOT spine members — durable-now fixes, not subsumed by the rework.)

**The hot path already lives all three disciplines** — it reads a seqlock-PUBLISHED position (one source, published once) and is a pure function of its local inputs. The accounting/fill spine is the subsystem where they were never applied; the three specs are "finish the discipline the hot path already has."

## The principle (spine 1)

**A terminal / irreversible action on the fill path MUST gate on the venue completeness signal, never on reaching a code path.** The OMS was built single-fill-synchronous-and-complete; live fills are multi-event, partial, asynchronous. Three parts:

1. **Completeness-gated terminal actions.** Free the slot / book the position / close the position / account P&L ONLY when the fill is terminal (`Order_GetState == ORDER_FILLED`, derived from the venue `order_complete` / `fill_qty == requested_qty`). A PARTIAL keeps the slot open and either books nothing (the interim loud-STOP) or accumulates correctly (the real handler). NEVER gate a terminal action on "the handler ran" / `event_log_mode`. → the anti-pattern is **RECURRING_BUG_PATTERNS Class 46** (completeness-assuming terminal action on a possibly-partial event).
2. **Protocol-agnostic normalized fill event.** The venue adapter normalizes the wire shape (WS-per-increment `"l"` / REST-cumulative `"z"` / FIX) into ONE common POD at the OMS boundary; the OMS runs ONE state machine that never knows the protocol. The anti-pattern is the protocol leaking into the protocol-agnostic core (today's A16/A2 — the OMS implicitly assumes a fill shape). Dispatch is compile-time `tt::<verb><ExchangeT>` (H13; no vtable per H2); the event is a POD (no alloc per H1); the state machine is slow-path (off the ≤500ns hot path).
3. **Reconstruct net from venue truth, NOT replay fill-by-fill.** Recovery/boot reconstructs each node's ONE net position from the venue's *current holding per symbol* (`per-node-position-ownership-model.md`), not by replaying individual fills (which collapses N→1 under the attribution-loss + overwrite bug, TECH_DEBT-072). Intra-session multi-fill accumulate (weighted-avg re-entry) is a DISTINCT problem from boot venue-net reconcile — do not conflate them (a D-214 finding).

## Latency placement (which contract)

The fill path is **POST-TRADE / async** — it lives on the **reaction-latency** contract (fill → kill-switch; the event-sourced aggregator, D-54), NOT the **critical-path** (tick → decision) contract. The hot path reads the seqlock-published position; it never touches the fill machinery (verified: zero hot-path references to OMS/account/fill state). So normalization + the state machine add **zero critical-path latency** — provided the three structural properties hold (POD no-alloc · compile-time dispatch no-vtable · slow-path off-hot). The `.E.1` design pass MUST *verify* these three, not assume them. → DESIGN_PHILOSOPHY § 4 (the three latency contracts).

## `.E.0.10` interim vs `.E.1` real handler

Live trading is gated behind the entire E-series completing, and `.E.1` relocates `ProcessFillCommand` into the per-node slow path — so building the full handler in `.E.0.10` would be throwaway. The split:

- **`.E.0.10` (durable-now, interim):** (a) a LiveReadiness REFUSE that blocks live-enable until the handler lands — keyed on `use_real_money` (not just `trading_mode`; the gate-decoupling fix) so the pin actually guards the real-order path; (b) A17 (paper/REST atomic fills set `order_complete`); (c) a minimal fail-loud assert / loud-STOP if a partial ever reaches a terminal action; (d) this spec + the Class-46 anti-pattern. NOT the full handler.
- **`.E.1` (the real handler):** per-node-owned fill consumption (central drainer absorbed) + the normalized fill event + weighted-avg re-entry + keep-slot-open + partial-reduce (SELL side) + venue-net reconcile. `.E.1` foundation items 53/54. The `.E.1` plan MUST *specify* this (currently a named-not-designed fold — D-214).

## Reference applications

- (pending) `.E.1` fill-path rework — the first canonical (backfill + promote stage 2→3 at `.E.1`).
- `.E.0.10` interim — the LiveReadiness gate + A17 + the loud-STOP/assert (Phase 4 of the D-214 plan).

## False-positive surface

- Paper/backtest synthetic fills are atomic BY CONSTRUCTION (one synthetic full-qty event); marking them `order_complete=1` (A17) is correct, not a masking of the discipline — there is no partial path in paper.
- A terminal action proven reachable only after `ORDER_FILLED` (e.g. the dedup early-return excludes re-entry) already satisfies part 1 — the discipline is about actions reachable on a PARTIAL/non-terminal path.
