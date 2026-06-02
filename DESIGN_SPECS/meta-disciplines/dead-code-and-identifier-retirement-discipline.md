---
type: meta-discipline
stage: 5-claude-md
version: 1.0
established: 2026-06-02
tags: [meta-discipline, structural-fix, framework-discipline, wire-format]
surface: [registry, wire-format, live-trading, boot-time]
sister_specs: [structural-fix-preferred-decision-framework.md, single-source-of-truth-discipline.md, wire-format-byte-preservation-discipline.md, meta-registry-pattern-for-codebase-registry-discipline.md]
applies_at_skills: [/post-ship-audit, /readiness, /dead-code-trace, /bug-check]
---

# Dead-code elimination & identifier retirement — the Knight-Capital discipline

**Established:** 2026-06-02 (codified after the `fp2_to_mag_fpn` dead-inline-helper catch + operator's Knight-Capital framing)
**Status:** ACTIVE — CI-enforced (`tools/check_identifier_retirement.py`, H21)
**Cross-references:**
- `CLAUDE.md` H21 (tombstone hard invariant) + Maintenance/Design priority-gradient rows
- `DOCS/DESIGN_PHILOSOPHY.md` § 7 (structural-fix family) + § 5 (determinism family) x-ref
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 40 (reactivatable dead code / repurposed persistence-ID)
- `feedback_design_once_maintain_forever` — sister build-philosophy ("no dead code left behind" is part of "good")
- `feedback_golden_master_over_reimplemented_oracle` — the ledger is the frozen REAL state, not a reimplemented oracle

## Why this exists — the Knight Capital failure mode

On 2012-08-01, Knight Capital deployed new code to 8 servers; 1 didn't get the update. The new code
**reused a dormant flag** ("Power Peg") whose old code — a test routine that bought high / sold low —
was **still compiled in**. On the un-updated node the flag activated the dead code. **$440M, 45 minutes,
company dead.** Three ingredients combined:

1. **Dead code left in the binary** (not removed when it stopped being reached).
2. **An identifier repurposed** (a flag/value reassigned a new meaning while old code keyed to the old meaning persisted).
3. **State / deploy skew** (old state, an old message, or an un-updated node carrying the old meaning).

This is a capital-bearing per-node sharded HFT engine — *exactly* the system class where this kills.
This discipline attacks all three ingredients. **Three of the four classic ingredients are already
defended here** — snapshot versioning (the D-144 catch), the determinism nets (cross-binary / cross-node
byte-equivalence = the deploy/state-skew defense), and the `calls_graph_diff` orphan guard. The gap this
closes is **ingredient 2** — identifier reuse — plus a named home for **ingredient 1** (dead-code removal).

## The three rules

### Rule 1 — Remove dead, don't leave it (prove-then-remove)

Dead = no caller, no reachable path, no registry consumer. **PROVE** it dead (`/dead-code-trace`;
`calls_graph_diff` for registry orphans), then **REMOVE** it in the same ship — never "leave it for later."
Leaving it is ingredient 1.

- **Blind spot:** the compiler does NOT warn on unused `inline` functions (only `static`). Header-only
  helpers rot silently — exactly how `fp2_to_mag_fpn` sat dead (its delegating Div/Sqrt callers went
  native). Inline-helper deadness is **tool-driven** (`/dead-code-trace` at ship), not compiler-caught.
- Sister: `feedback_design_once_maintain_forever` (no dead code left behind is part of "good"); `feedback_no_defer_for_effort` (don't punt a proven-dead removal "to the flip").

### Rule 2 — Tombstone retired identifiers; NEVER repurpose (the Power Peg rule) — H21

**Scope: persistence/wire-visible identifiers** — the ones where an old persisted file, an old wire/HMAC
message, or an un-updated node can carry the OLD meaning:

- snapshot / format **VERSION** numbers (`*_SNAPSHOT_VERSION`, `*_FORMAT_VERSION`, `STAMP_FORMAT_VERSION_*`)
- **enum CODES** that are persisted / logged / wire-emitted (`BanditAlgorithm`, `StrategyId`, `RegimeId`, halt/SHALT codes, …)
- **bitmap bit-assignments** (bit-index → meaning) in persisted/wire bitmaps
- **cfg-field name keys** (operators have old cfg files on disk)

**The rule:** a retired identifier is **tombstoned** — the slot/value/number is retired-in-place and
**NEVER reassigned**. New meaning → **new identifier**. Append-only + immutable.

**This reconciles with `feedback_backwards_compat_not_default_concern`:** you still DELETE the dead code
and the behavior cleanly (no preserve-and-deprecate code paths). What you must never do is **recycle the
externally-visible slot** — because old persisted state or an un-updated node still references the old
number. Delete the code; tombstone the number. Purely-internal identifiers (a local enum never persisted/
wired) are exempt — delete and reuse freely.

**The codebase already practices this informally** — this discipline names + mechanizes it:
- `BanditAlgorithm` **"OPTION C wire-byte preservation"**: `EXP3_OP_THOMPSON_GHOST=2` keeps the old
  `BANDIT_ALGO_BOTH=2` wire byte; the *semantic* was reassigned (Class 24 fix) but the *number* never moved,
  + `FromString("BOTH")` legacy alias preserved. (Caveat: a semantic reassignment of a live code is itself
  delicate — preferred only when the old + new meanings are genuinely the same wire intent; otherwise allocate new.)
- `RESERVED` bit anchors: `// 1u << 0 RESERVED (was PER_CORE_OK, removed at .F.4c.3)`.
- `LEGACY_CONFIDENCE_VERSION 11` — retired version kept as a named constant with special-case load logic.
- `DEPRECATED` metadata flag — soft-retire (visible-but-obsolete in GUI; row stays in the registry).
- `StrategyInterface.hpp:165`: *"IDs are append-only — never reorder or remove. Persisted snapshots and
  trade logs reference these by integer."* — the rule, written but (until now) unenforced.

### Rule 3 — No reactivatable dead capital-path

The dangerous subclass of Rule 1: a dead **strategy / order-gate / OMS / kill-switch / fill** path that
is still compiled in. A `cfg`-disabled or `if(false)` trading path is a loaded gun (the Power Peg shape).
These get the strictest treatment — **removed**, never merely gated off. If a capital path must be
toggleable, the toggle gates *entry into a live path*, never *which of two compiled paths runs* where one
is meant to be dead.

## Mechanization — the golden identifier-ledger guard (H21 enforcement)

`tools/check_identifier_retirement.py` + `tools/identifier_ledger.txt`. Golden-master pattern
(`feedback_golden_master_over_reimplemented_oracle`): the ledger is the frozen REAL identifier→value map
parsed from source — not a reimplemented oracle that could drift.

- **FAILS (red build):** RENUMBER (an enum code changed value), VALUE-REUSE (a value now held by a
  different name), silent REMOVAL (a frozen identifier vanished — tombstone it, don't drop the row),
  version DECREASE (a format version went backwards).
- **OK (info):** ADD (a new identifier — append-only) and version BUMP (monotonic increase). Record either
  by re-running `--update` to re-freeze the ledger.
- **Coverage v1:** the 6 format VERSIONs + `BanditAlgorithm` / `StrategyId` / `RegimeId` enum codes (20
  identifiers). **Enrollment is paced** (sister to the H15 meta-registry enrollment pattern): bitmap
  bit-assignments + cfg-field name keys enroll next — add a row to `SOURCES` in the tool. The DISCIPLINE
  is complete; coverage grows. Per `feedback_close_the_class_vs_migrate_every_site` (close the class via the
  primitive + guard; pace the enrollment).
- **Layout-coupling (the D-144 stale-state risk — "version must bump when the persisted struct changes"):**
  partially defended by the existing **R1 `sizeof`/offset `static_assert`s** on persisted structs — a layout
  change trips the assert → forces attention → bump the version + `--update` the ledger. If those asserts
  prove insufficient, enroll a struct-layout-fingerprint→version golden as the next mechanization step.

**Where it fires:** pre-commit (`.githooks/pre-commit` Check H, fires on staged source touching an enrolled
file) · `/readiness` Check 46 · `/post-ship-audit` (the dead-code + identifier sweep stage) · runnable
standalone any time.

## When to apply

- **Adding** a persisted/wire identifier (version, enum code, persisted bit, cfg key) → append-only; run `--update`.
- **Retiring** one → tombstone the slot (RESERVED / LEGACY_ / DEPRECATED comment; keep the ledger row); never reassign.
- **Removing** code → prove dead (`/dead-code-trace`), remove fully; if it owned a persisted identifier, tombstone that slot.
- **At ship close** → `/post-ship-audit` dead-code + identifier sweep on the ship's touched surface.

## False-positive surface (per M3)

- **Purely-internal identifiers** (a local enum / constant never persisted, logged, or wire-emitted) are
  NOT in scope — delete + reuse freely. The guard only enrolls persistence/wire-visible surfaces; do not
  enroll internal-only identifiers (over-enrollment ossifies refactorable internals).
- **Display-only strings / labels** (`STRATEGY_SHORT_NAMES`, regime full-names) are not identifiers — they
  may be reworded freely; only the integer CODE is frozen.
- **A legitimate version bump** (monotonic increase) is NOT a violation — the guard distinguishes bump
  (OK) from decrease (violation). New enum value APPENDED at the next dense index is NOT a violation — only
  changing an EXISTING name's value is.
- **The `EXP3_OP_THOMPSON_GHOST` semantic-reassignment-at-same-number** is the one delicate pattern: it is
  permitted ONLY because the wire intent was preserved + documented + alias-guarded. A semantic reassign
  that changes what old state would *do* is a Rule-2 violation even if the number is unchanged — when in
  doubt, allocate a new identifier.

## Relationship to the other Knight-Capital defenses already in the codebase

| Ingredient | Defense (existing unless noted) |
|---|---|
| Dead code left in | Rule 1 + `/dead-code-trace` + `calls_graph_diff` orphan guard |
| Identifier repurposed | **Rule 2 + `check_identifier_retirement.py` (NEW — the gap this closes)** |
| Stale persisted state | Snapshot versioning + R1 layout asserts + Rule-2 version monotonicity |
| Deploy / node skew | The determinism nets (cross-binary / cross-node byte-equivalence) |
