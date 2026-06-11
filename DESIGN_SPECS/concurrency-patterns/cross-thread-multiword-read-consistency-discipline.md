---
type: concurrency-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-06-10
tags: [concurrency, data-oriented-design, framework-discipline]
surface: [oms-drainer, hot-path, slow-path, live-trading]
sister_specs: [concurrency-model-summary.md]
---

# Cross-thread multi-word read consistency discipline (reader-side)

**Established:** 2026-06-10 (v5.15.5.F.4d.1.E.0.10; adversarial 3-agent sweep — 9 sites surfaced).
**Status:** ACTIVE (discipline codified now; site remediation rides `.E.1`).

## The discipline (one line)

A non-owner thread reading **multi-word** state written by another thread — ESPECIALLY money (`Money`/`FixedPoint` is **16B = 2 machine words**) and `Position` — must read it through a **seqlock** or a **consistent-copy** (a published snapshot). A bare multi-word load/struct-assign compiles to multiple `mov`s, so a read concurrent with a write can **TEAR**: high word from one update, low word from the next → a value that never existed. Single-word/aligned ≤8B atomically-loadable fields are exempt; anything >8B is not.

## Why this is the READER side (and why the existing specs don't cover it)

The codebase already disciplines the **writer / publication / false-sharing** side: the slow→hot cfg **seqlock** (`ParameterSlot`), `alignas(64)` atomic flags for cross-thread booleans (H6), drainer-as-sole-writer for OMS submit (H3 funneling), and `cross-thread-snapshot-publish-cluster-isolation.md` (false-sharing/MESI — explicitly *not* a consistency concern). **None of them govern a non-owner thread READING drainer-written multi-word money state.** That reader-side rule is the hole this spec fills. Sisters that are adjacent-but-different: `concurrency-model-summary.md` (writer publication + single-byte flags), `cross-thread-snapshot-publish-cluster-isolation.md` (false-sharing), `phase-separated-drainer-for-safe-cross-temporal-derives.md` (intra-drainer same-cycle reuse). `DESIGN_PHILOSOPHY.md` § 6 + H3/H6 are writer-side only.

## The rule

1. **>8B + cross-thread-written ⇒ seqlock or consistent-copy.** Any field/struct larger than a single atomically-loadable word that one thread writes and another reads must not be read by a bare load. Read it via a seqlock (retry on parity change) or off a published immutable snapshot.
2. **The single-writer's published snapshot is the consistent-copy.** The drainer is the sole writer of the OMS money cluster (`balance`/`realized_pnl`/`total_fees`/`portfolio`/per-core P&L). It should publish a seqlock'd **money snapshot** (exactly the `TUISnapshot` pattern, but for the money surface); every non-drainer reader (kill switch, reconciler, save, GUI-publish) reads the snapshot, never the live fields.
3. **A comment asserting word-atomicity on a >8B field is the smell.** "x86-acceptable on an aligned word" / "torn reads unlikely" next to a 16B `Money`/`Position`/struct is the anti-pattern justification — aligned ≠ atomic for >8B.
4. **Topology change re-opens single-writer/single-producer assumptions.** When a sharded/multi-node split adds a second writer or un-parks a reader, every SPSC-ring / single-writer / "this thread only" assumption the OLD topology relied on must be re-audited; the in-code comments lag the thread model.

## The canonical instance (9 sites; 3 live capital-control)

The OMS money cluster has **no seqlock, no atomic** anywhere; every non-drainer reader reads raw 16B `Money`. The GUI consumer is the ONE site done right (reads the seqlock-published `TUISnapshot`). Worst-first (live, capital-driving):
- **LIVE reconciler** (`ReconciliationLoop`) — reads `balance` torn, then pushes a **balance correction to live capital**. A self-healing safety net firing on a torn read is **Knight-Capital-shaped** (H21 sister).
- **Global kill switch** (`EventLoop_KillSwitchEvaluate`, `Async.hpp:445` / `ControllerEventLoop.hpp:3251`) — torn `balance`/`ks_peak_balance` → false-positive (halt on garbage) or **missed** trip (guard fails to fire). The documented `KNOWN RACE` (audit 2026-04-09).
- **Per-core MTM kill switch** (`EventLoop_RebuildOneCore`, `ControllerEventLoop.hpp:2881-2896`) — torn `core_realized` + `Position.entry_price/quantity` → wrong drawdown → false/missed per-core kill.
- Plus: periodic save (`Async.hpp:431`, paper), TUI publish (`Async.hpp:484`), ANSI render (`Run.hpp:2021`), and a GUI drag-TP/SL **write**-hazard (`Async.hpp:244` — producer writes a 16B exit price the drainer concurrently reads/mutates).

## Status: DELIBERATE accepted-race; structural fix slated for `.E.1`

This is a **documented, deliberate** trade-off — not an oversight. The race was flagged at design time (in-code `Async.hpp:434` "KNOWN RACE (audit 2026-04-09)"; introduced with the original sharded OMS), tracked in `E.1-findings` (`conc-1`/`conc-5`/`conc-6`/`conc-dod-1`) + decision-log **F-2** ("aggregator-as-single-writer + seqlock-published account state closes this race structurally — free bonus") + **D-74**. The **fix rides `.E.1`** (the per-node topology rework removes the central drainer → aggregator-as-single-writer + a published money snapshot, closing the whole class structurally). **Ship B (decimal `Money` 16B) did NOT change the exposure** — `FPN_Binary<64>` was also 16B/2 words; the tear surface is byte-identical (per the Ship-B hft-audit). **Site remediation is NOT piecemeal-now — it lands as the `.E.1` topology rework.** What is owed NOW is the codification (this spec + the anti-pattern + the CI check).

## What this is NOT (the over-lump caution — its own worked example)

NOT every concurrency finding near the OMS shares this root. At `.E.0.10` an agent (me) lumped FOUR findings into "one root, one seqlock fix" — wrong:
- **`persist-8`** (paper-reset leaves a stale `ExecutionCore.active` flag) is a **stale-flag / missing-reset** (Class 5), single byte, NO tear — a seqlock does nothing for it; fix = clear the flag / park the hot thread on reset.
- **`conc-5`** (submit_queue SPSC ring pushed by 2 producer threads → lost/duplicated order) is a **producer/consumer ring race** — fix = single-producer-by-construction / MPSC, NOT a seqlock.
Only `persist-dod-1` ⊇ the kill-switch read are this spec's root. The operator's adversarial pushback ("are you making stuff up?") + a 3-agent refute caught the over-lump. **Lesson: a shared remediation EPOCH (`.E.1`) or a shared THEME (topology added a 2nd writer) is NOT a shared root MECHANISM — don't collapse distinct fixes into one.** See `adversarial-multi-agent-audit-methodology.md`.

## Anti-pattern + CI check (owed to RECURRING_BUG_PATTERNS)

Two recurring code shapes belong in `DOCS/RECURRING_BUG_PATTERNS.md` so `/bug-check` catches future instances:
- **(a) Multi-word value object (Money / FixedPoint / any struct >8B) shared cross-thread via a plain load/assign**, justified by a comment conflating struct-alignment with word-atomicity.
- **(b) An SPSC ring whose producer-push became reachable from two threads after a topology change** while the comment still asserts single-producer.
**Mechanical CI check (pre-specified):** flag any cross-thread-written field with `sizeof > 8 && !is_atomic` that is read/assigned outside a seqlock; grep "aligned word" / "x86-acceptable" near >8B fields.

## Cross-references

- Writer/publication side (the existing half): `concurrency-model-summary.md` (add a reader-side row to its Visibility rules), `cross-thread-snapshot-publish-cluster-isolation.md` (false-sharing), `phase-separated-drainer-for-safe-cross-temporal-derives.md` (intra-drainer).
- The `.E.1` structural fix: decision-log F-2 + D-74 (aggregator-as-single-writer + seqlock-published account state).
- Over-lump caution: `adversarial-multi-agent-audit-methodology.md` (the 3-agent refute that caught it).
- Knight-Capital sister (self-healing-on-torn-read): H21 / `dead-code-and-identifier-retirement-discipline.md`.
