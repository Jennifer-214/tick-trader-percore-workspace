---
type: ledger-template
class_id: 40
title: Reactivatable dead code / repurposed persistence-visible identifier (Knight-Capital)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-06-02
surface_tags: [registry, wire-format, persistence, live-trading, capital-safety, dead-code]
severity: high
recurrence_count: 1
first_instance: 2026-06-02 (v5.15.5.F.4d.1.E #11 — dead `fp2_to_mag_fpn` inline helper left compiled-in after Div/Sqrt went native; the compiler does NOT warn on unused `inline`. Caught by manual full-tree grep + operator's Knight-Capital framing. No identifier-reuse instance yet — the guard is PREVENTIVE.)
closure_mechanism: `tools/check_identifier_retirement.py` + golden ledger (pre-commit Check H) freezes every persistence/wire-visible identifier->value and FAILS on renumber / value-reuse / silent-drop / version-decrease; `/dead-code-trace` (prove-then-remove) for dead code incl. inline; H21 hard invariant. Tombstone retired identifiers (RESERVED/LEGACY_/DEPRECATED), never reassign the slot.
sister_classes: [13, 18, 21]
sister_memories: [feedback_design_once_maintain_forever, feedback_backwards_compat_not_default_concern, feedback_close_the_class_vs_migrate_every_site, feedback_golden_master_over_reimplemented_oracle]
---

# Class 40 — Reactivatable dead code / repurposed persistence-visible identifier

The Knight-Capital failure mode in a capital-bearing engine. On 2012-08-01 Knight Capital reused a dormant flag ("Power Peg") whose dead code was still compiled in; one un-updated node ran it → $440M / 45 min / company dead. Three ingredients (dead code left in · identifier repurposed · state/deploy skew); two own sub-shapes here (the third — deploy/state skew — is defended by the determinism nets + snapshot versioning).

## Sub-shape A — Dead code left compiled-in
A function / branch / path no longer reached but still in the binary. **The compiler does NOT warn on unused `inline` functions** (only `static`) — header-only helpers rot silently. A dead **capital-path** (strategy / order-gate / OMS / kill-switch / fill) is the dangerous form: a `cfg`-disabled or `if(false)` trading path is a loaded gun.

**Detected:** 2026-06-02 — `fp2_to_mag_fpn` (the FPN-magnitude bridge for the *delegating* Div/Sqrt) sat dead after both went native via the extracted `udiv_q64`; zero callers, no compiler warning.

## Sub-shape B — Repurposed persistence/wire-visible identifier
A snapshot/format VERSION number, persisted/logged/wire-emitted enum CODE, persisted bitmap bit, or cfg-field name key is **renumbered, value-reused, or silently dropped**. Old persisted state, an old wire/HMAC message, or an un-updated node still carries the OLD meaning → the wrong code path activates. This is the exact Power-Peg mechanism.

## Recurring symptom
- An `inline`/header helper with no remaining callers (Sub-shape A).
- An enum value reassigned, a version reused/decreased, a bit re-meaninged, or a cfg key recycled for a new purpose (Sub-shape B).

## Closure (structural)
- **Dead code:** `/dead-code-trace` proves-then-removes (covers inline). Remove in the same ship — never "leave it for later" (leaving it is ingredient 1). Dead capital-paths removed, never gated-off.
- **Identifiers:** append-only + immutable. Retire by TOMBSTONE — RESERVED / LEGACY_ / DEPRECATED comment, keep the number, never reassign. New meaning = new identifier. Mechanized by `tools/check_identifier_retirement.py` (pre-commit Check H + golden ledger; H21).
- Reconciles with `feedback_backwards_compat_not_default_concern`: delete the dead CODE cleanly; never recycle the externally-visible SLOT.

## False-positive surface
- Purely-internal identifiers (a local enum/constant never persisted/logged/wired) — delete + reuse freely; NOT in scope.
- Display-only strings/labels (`STRATEGY_SHORT_NAMES`, regime full-names) — reword freely; only the integer CODE is frozen.
- A monotonic version BUMP is not a violation (only decrease/reuse). A new enum value APPENDED at the next dense index is not a violation (only changing an EXISTING name's value is).
- `EXP3_OP_THOMPSON_GHOST`-style semantic-reassign-at-same-number is permitted ONLY when the wire intent is preserved + documented + alias-guarded; if old state would now DO something different, allocate a new identifier.

## Canonical reference
`DESIGN_SPECS/meta-disciplines/dead-code-and-identifier-retirement-discipline.md`; CLAUDE.md H21; DOCS/DESIGN_PHILOSOPHY.md § 7.
