---
type: plan-dive-synthesis
plan: subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md
gate: v5.15.5.F.4d.1.E.0
date: 2026-05-29
method: hand-audited (pre /plan-dive); this doc = first canonical /plan-dive Stage-7 output (template for dives 2-9)
verdict: RED — substantive amendment before coding
findings_index: pre-implementation-findings/CANONICAL-FINDINGS.md (E.1 slice = 25 routed + standalone-pre-.E.1 prerequisites)
---

# `.E.1` (Foundation) — plan-dive synthesis · VERDICT: RED

`.E.1` is a strong, thorough v0.1 draft (1900 lines; canonical-sister analysis; first-canonical Tests-changed section; 17 decisions). It is **RED for coding** — not because it's bad work, but because of a CRITICAL design contradiction + undesigned primitives + 0/30 findings ingested + it predates this session's decisions (D-67..D-72). This is amendment work, not a coding ship.

## Per-layer verdict

| Layer | Verdict | Note |
|---|---|---|
| 1 — Mechanical/soundness | **RED** | `FPN_Atomic*` confirmed nonexistent (undesigned); symbol-checker never run (10 `<F>` template-context false-positives + `Run.hpp` path-prefix drift); BinanceAdapter both paths exist (OK) |
| 2 — Design/SHAPE | **RED** | `conc-5` closure contradictory (below); Phase F codes the SUPERSEDED pull-model aggregator |
| 3 — Impl-detail | (not formally fired — `/blindspot-scan` at amendment) | — |
| 4 — Anti-pattern | **RED** | plan claims `conc-5` CLOSED but submit-path design relocates the multi-producer race (claimed-closed-but-reintroduced) |
| 5 — Findings-ingestion | **RED** | 0/30 sidecar findings have a fix-design; no `findings_sidecar:` wired; pre-`.E.1` foundational fixes not sequenced |
| 6 — Seam (rolling-window) | **PARTIAL** | outbound forward-promises detailed + mostly coherent; inbound (findings) unverified; submit-path contradiction destabilizes the `.E.4`/`.E.5` seams |
| intent-match | **RED** | predates D-67..D-72 (no safeguard phases / findings_sidecar / matrix rows); stale anchors (predecessor `.D`, Phase A.1 expects HEAD `61ae3cc`, "D-1..D-53") |

## Blocking findings (the punch-list)

1. **[CRITICAL] `conc-5` closure is contradictory + unbuildable as written.** `ClusterState.submit_queue` (line 587) is declared per-cluster *"MPSC-style (nodes write; adapter reads)"* — multiple producers — but `SPSCRing.hpp:12` says *"no MPMC, no MPSC, no SPMC"* (no multi-producer primitive exists). The Tests section (line 1559) asserts the opposite — per-node *single*-producer — and the sidecar `conc-5` prescribes per-node sole-producer. As written, the design **relocates** the multi-producer race the CRITICAL is about, to a primitive that doesn't exist. **Resolve the submit-path topology explicitly** (per-node SPSC sole-producer, OR design a real MPSC ring) + state the single-producer invariant as enforced-by-construction + land the invariant test as CHANGES-BY-DESIGN in `.E.1`. This is the handoff's "verify `conc-5`, don't assume" — confirmed not-closed.
2. **[HIGH] D-54 event-sourced aggregator depends on `FPN_AtomicAdd`/`FPN_AtomicLoad` — confirmed nonexistent.** FPN<64> is 24 bytes, not natively atomic; the plan hand-waves __int128 vs split-slot ("revisit at v5.16+"). Design the atomic-FPN mechanism before coding. AND: Phase F's coding steps implement the *superseded* pull-model `Aggregator_Cycle` (every-100ms scan), contradicting the chosen D-54 push model — reconcile.
3. **[HIGH] 0 of 30 sidecar findings ingested.** No `findings_sidecar:` frontmatter; no per-finding fix-designs. Several are flagged **pre-`.E.1`** (fpmem sqrt-determinism, strict-aliasing UB on the accounting path, the parity-oracle stub) — foundational fixes the plan doesn't sequence. These gate the safety net (the determinism gate + characterization tests can't be trusted until the FP-path question + parity oracle are fixed).
4. **[MED] Self-flagged H1 violation** (`std::vector` + `std::future` in boot-reconcile, lines 992-1003) left unresolved ("will codify in audit cycle" — that cycle is this).
5. **[LOW] Stale anchors + predates D-67..D-72** — predecessor `.D`→`.D.1`; Phase A.1 HEAD `61ae3cc`→`dc37b24`; "D-1..D-53"→"D-1..D-72"; no safeguard phases / matrix rows / findings_sidecar (the safeguard-distribution map assigns `.E.1`: conservation invariants, pre-trade risk gates, kill-switch hierarchy, watchdog, latency ratchet, CI-merge-gate).

## Amendment list (for `.E.1` plan body, before coding)

- [ ] Resolve the submit-path topology (#1) + state the single-producer invariant + spec the CHANGES-BY-DESIGN test.
- [ ] Design the atomic-FPN aggregator mechanism; reconcile Phase F with the D-54 push model (#2).
- [ ] Wire `findings_sidecar: E.1-findings.md` + lay a fix-design per the **deduped** `.E.1` slice of `CANONICAL-FINDINGS.md` (#3).
- [ ] Sequence the pre-`.E.1` foundational batch (fpmem sqrt-determinism + strict-aliasing + parity-oracle stub + runtime-confirm the 2 CRITICALs) BEFORE `.E.1` codes (#3).
- [ ] Add the `.E.1`-assigned safeguard phases per the distribution map + matrix rows (#5).
- [ ] Fix stale anchors (#5); resolve the H1 violation (#4).

## Calibration note (for `/plan-dive` first run)

This was hand-audited before `/plan-dive` existed. When `/plan-dive` is fired on `.E.1` to validate it, it MUST surface at least: finding #1 (conc-5 contradiction via Layer 4 + the `SPSCRing.hpp:12` grep), #2 (`FPN_Atomic*` nonexistence via Layer 1), #3 (0/30 ingestion via Layer 5). If it misses any, tune the skill.
