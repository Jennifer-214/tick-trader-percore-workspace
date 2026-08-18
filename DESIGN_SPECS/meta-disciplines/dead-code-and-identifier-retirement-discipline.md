---
type: meta-discipline
stage: 6-cadence-locked   # promoted 2026-08-10 at TD-254(c) closure ON EVIDENCE (the first stage-6 member, never vocab-filling): standing CI `tools/check_identifier_retirement.py` + pre-commit Check H + the golden retirement ledger + the H21 CLAUDE.md row — enforcement AND cadence both live
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

#### Rule 1a — a row retired from its PRODUCER but left in its EMITTER does not go dead, it goes LYING (added 2026-08-16)

Rule 1 assumes the thing you left behind is **inert**: dead code does nothing, so the cost is
confusion and binary size. There is a sharper sub-shape where leaving it is not inert — **the row
keeps emitting, and emits its DEFAULT as though it were a measurement.**

**Worked instance (E.1.2, 2026-08-16).** The `.B.3` prefix migration moved fee rates onto the
cfg-derived emit half — `fee_rate_maker` / `fee_rate_taker` carry `STAMP_BOUND_CFG_DERIVED`
(`CoreFrameworks/CfgFieldRegistry.hpp:788-789`) and emit the true configured values. The **old
model-const rows were left in place** (`ML_Headers/StampBoundModelConstRegistry.hpp:305`/`:307`).
Their producer went away with the migration; nothing writes `inf.inference_cfg_fee_rate_*`, and
`StampInferenceCfgInputs inf = {}` zero-inits. But the emit walk is **gated per-GROUP, not per-row**,
so the moment the `fees` group bit is set (`ML_Headers/StampHelper.hpp:253`, whenever the cost gate
is enabled) both rows print `inf->name` unconditionally.

Net result: **one HMAC-signed model-identity document carrying two contradictory fee claims** — the
canonical keys with the true rates, and the prefixed keys with `0`. It then propagates to the handle
(`ML_Headers/NodeModelZoo.hpp:474-480`) and is displayed to the operator as the model's training-time
fees (`Backtest/BacktestPanels.hpp:2314-2316`).

**Why the existing rules do not catch it.** Rule 1's "prove-then-remove" is about code with no
callers; this row HAS a caller — the emit walk — it just has no *producer*. Rule 2 protects the
identifier SLOT from reuse; nothing was reused. Rule 3 covers a dead capital PATH that could
reactivate; this path never deactivated. The gap is a fourth axis: **producer removed, consumer
retained.**

**The rule.** When a migration moves a field's source, the OLD row must be deleted or tombstoned **in
the same commit** as the new producer lands. A row whose producer is gone is not tech debt to sweep
later — from the instant of the migration it is emitting a fabricated value into whatever artifact it
feeds. Where that artifact is signed, persisted, or operator-visible, treat it at the severity of the
artifact, not the severity of "leftover code."

**Detection.** The general question is Class 58 sub-shape B one level down: not *"does this bit have a
producer"* but *"does this ROW have a producer."* Per-bit granularity is structurally blind here —
the `fees` bit HAS a producer (`StampHelper.hpp:253` sets it), so any bit-scoped completeness check
grades this GREEN while two of its rows emit zeros. **A coverage check over an emitted format must be
keyed on the WIRE KEY, not on the group that gates it.**

**Sister:** Class 58 (registry complement blindness) · `advertised-capability-never-exercised.md`
(the inverse — a capability with no *consumer*; this is a row with no *producer*) · H9 wire-byte
preservation (why the artifact's severity governs).

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

**Worked refinement — the NAME is the identifier, a non-persisted BIT is not (don't conflate name-tombstone with bit-freeze).** A bitmap-backed cfg flag carries TWO identifiers with DIFFERENT dispositions; conflating them (treating "retire the flag" as "freeze its bit forever") was made + operator-caught at the `.E.0.10` #9 cohort. Disentangle:
- The **cfg name key** (`gate_ema_enabled`) is the persisted identity (operators have old `engine.cfg` on disk) → **IMMUTABLE — tombstone the name** (the parser drops/WARNs the retired key so an old cfg can't set a reclaimed bit via the old name; never reuse the name for a new meaning).
- The **bit-index** (`0x02`) is a protected identifier ONLY IF the bitmap is persisted/wire (snapshot-saved as a raw byte, or raw-byte stamp/fingerprint-emitted). A **runtime-only** bit — reconstructed from a name-keyed cfg each boot — is NOT persisted → **reuse freely** (per the exemption above).

The gate/risk/lifecycle cfg-flag bitmaps are runtime-only (verified `.E.0.10`: the sharded snapshot READS them to interpret layout but never SAVES the bitmap — it reconstructs from `engine.cfg`; the parser is name-keyed `strcmp`; only individual STAMP_BOUND fields like `barrier_gate_enabled` are wire-emitted, **by name**, not the raw byte). So **retirement = tombstone the NAME + RECLAIM the bit** — mark the row RETIRED **in place** (bit position UNCHANGED → no renumber, no churn to sibling bits/stamps/tests; extends the existing `DEPRECATED` soft-retire marker), and the next flag-add REUSES that slot (new name, same bit). Do NOT freeze the non-persisted bit (a permanently-wasted slot) and do NOT widen the bitmap (uint8→16) to dodge retirement — both violate the DOD minimum-footprint / bit-packing ideal; **reclaim before widen**. Single-binary architecture (per-core threads run ONE binary) ⇒ no heterogeneous-deploy bit-misread; the only cross-version surfaces are the name-keyed cfg + the name-keyed stamps, both NAME-protected — which is *why* the bit is free.

**Caveats (the freeze still applies):** (1) a STAMP_BOUND flag's bit, or a genuinely snapshot-persisted raw bit, IS wire-visible → it freezes (reuse only at a deliberate epoch; this project's no-live-models makes epochs cheap). (2) Before reclaiming a SPECIFIC bit, verify it is not carried in a whole-byte cfg-fingerprint / train-serve-parity hash (if the parity hash digests the raw `gate_cfg_flags` byte rather than the named STAMP_BOUND fields, a reused bit can pass the hash with a different meaning — check, don't assume).

**Worked refinement — for a WIRE KEY the remedy INVERTS: drop the row, burn the name (added 2026-08-17, D-426).** Rule 2's headline — *"tombstone the slot, never drop the row"* — is written for an enum **CODE**, where the NUMBER is the persisted thing. On a name-keyed wire body (`key=value` lines in an HMAC-signed model stamp) the identifier is the **NAME**, and the row's ordinal is merely where that key currently sits in the emit walk. There, keeping the row is the *dangerous* option, because Rule 1a applies: a row retired from its producer but left in its emitter does not go dead, it goes **LYING** — it emits its zero-initialised default into the signed document (`fees`, and `inference_cfg_bandit_blend_ratio` three lines below it, both shipped exactly that). So:

| Identifier class | The persisted thing | Retirement remedy |
|---|---|---|
| enum CODE / snapshot VERSION / persisted bit | the **number** | keep the number — tombstone the slot in place, never reassign |
| **wire KEY** (name-keyed body) | the **name** | **DROP the row** (Rule 1a), and **BURN the name** in the guard's retired-name set |

Getting this backwards is not a style question — following the enum-shaped remedy on a wire key leaves a lying row in a signed body, which is the defect the rule exists to prevent. Guard messages must therefore be **category-aware**; a guard that prescribes an impossible remedy ("do not drop the row" on a row you are required to drop) trains the operator to discount it, which is the cry-wolf mechanism that actually costs you.

**Mechanization corollary — a name-burn must match in EVERY code shape, or it is narration.** Burning a name only helps if the guard can see the name come back. Enumerating the shapes it might return in (`#define` … and what else?) is the Class-58 complement blindness one level up: it catches only the shapes someone thought of. **MEASURED 2026-08-17:** the burn sweep matched `^\s*#\s*define\s+NAME\b` and nothing else, while **three of its four burned names could never take that shape** — two return as `X(…)` registry rows, one is an enum member. Both resurrections passed GREEN (one produced no output at all), while the tool's own comment claimed the burn made deletion *"ENFORCED rather than narrated."* For every name but one, it was narration. The correct rule is **whole-word over comment-stripped code**: a burned name is burned in code, in any shape, while a tombstone RECORD in a comment — the desired way to keep the number — stays silent. Both directions need teeth (a positive control per shape **and** a negative control proving comments don't trip it); a widened match that reds on tombstone comments has traded one defect for another.

### Rule 3 — No reactivatable dead capital-path

The dangerous subclass of Rule 1: a dead **strategy / order-gate / OMS / kill-switch / fill** path that
is still compiled in. A `cfg`-disabled or `if(false)` trading path is a loaded gun (the Power Peg shape).
These get the strictest treatment — **removed**, never merely gated off. If a capital path must be
toggleable, the toggle gates *entry into a live path*, never *which of two compiled paths runs* where one
is meant to be dead.

## Proactive complement — design for clean deletion (deletable-by-construction; D-278)

Rules 1-3 are REACTIVE — what to do when you encounter dead code or a retired identifier. The proactive complement is to **design so that as few things as possible ever NEED Rules 1-3**: make internal deletion auto-cascade, and keep the tombstone-forcing surface small.

- **Default to deletable-by-construction.** Structure internal designs (X-macro registries, derived masks, non-persisted fields) so deleting a "part" — a registry row, a field — cascades through every consumer automatically (the compiler regenerates them, or the dependent code vanishes WITH the row). Then deletion needs no tombstone and no hand-cleanup.
- **Tombstoning (Rule 2 / H21) is FORCED only by external visibility — minimize that surface.** A persisted snapshot VERSION, a persisted/wire enum CODE, an HMAC body field, an operator's cfg key physically CANNOT be clean-deleted (old state / un-updated nodes carry the old meaning). Everything else CAN. So at design time, ask whether an identifier needs to cross the wire/persist line AT ALL; the fewer that do, the fewer tombstones ever accrue.
- **The cascade should go the GOOD direction.** First canonical: item-4's global-flat capital checks ride `FOREACH_PER_NODE_ARRAY_OVERRIDE` (an internal, non-persisted registry). When E.1.2 deletes the legacy arrays, the checks VANISH for free — deleting the source registry removes its consumers, zero hand-cleanup. Contrast a hardcoded parallel list, which E.1.2 would have to find + delete by hand (and could forget).

This COMPOSES with Rule 2, it does not weaken it: Rule 2 still governs the irreducible external surface absolutely (Knight Capital). The complement just shrinks how much surface that is. → memory `feedback_prefer_deletable_cascade_over_tombstone`; decision log D-278.

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
- **⚠ Enrollment is necessary but NOT sufficient — an enrolled registry can still be PARTIALLY parsed
  (E.1.2 D-421, the complement-blindness sweep).** `StrategyId` was enrolled from the start and the ledger
  still carried only **4 of its 5** real codes for the whole of its life: `FOREACH_STRATEGY`'s fifth row
  arrives through a nested `FOREACH_STRATEGY_EMACROSS(X)` invocation
  (`Strategies/StrategyInterface.hpp:143`), and the row scanner matched only literal `X(`, so
  `STRATEGY_EMA_CROSS` was outside the guard that exists to prevent exactly its reuse. **This is worse than
  an un-enrolled registry**, because the category is present and the surface therefore READS as covered — the
  audit trail terminates at a green check. Fixed by teaching the shared parser to expand nested invocations
  (resolving `__has_include` guards the way the preprocessor does) and to anchor `X(` on a token boundary;
  4 positive-control teeth in `node_persist_layout --selftest`, each verified to FAIL against the old parser.
  **The generalized lesson: for a golden-master guard, "is the source enrolled?" and "does the parser see all
  of the source?" are two different questions, and only the first one is ever asked.**
- **Derived sentinels are guarded transitively, and that is deliberate — do not "fix" it.**
  `STRATEGY_AUTO = NUM_STRATEGIES_REAL` (`StrategyInterface.hpp:178`) is a persisted code but is declared
  OUTSIDE the X-macro, so it never enters the ledger. That is correct: it has no independently-assignable
  value, so it cannot be renumbered on its own — it moves if and only if the real-strategy count moves, and
  the count is now guarded. Adding it as a ledger row would freeze a value that is a *consequence*, and the
  first legitimate strategy addition would then red the guard for no reason.
- **Layout-coupling (the D-144 stale-state risk — "version must bump when the persisted struct changes"):**
  partially defended by the existing **R1 `sizeof`/offset `static_assert`s** on persisted structs — a layout
  change trips the assert → forces attention → bump the version + `--update` the ledger. **The predicted
  "struct-layout-fingerprint→version golden" LANDED 2026-08-14 (E.1.2 D-305/D-302) as the PAIRED-BUMP
  rule:** `tools/node_persist_layout.py` freezes the flattened `FOREACH_NODE_PERSIST_FIELD` wire walk
  (delegate-internal rows included, NAME-inclusive + order-sensitive) as a named-row golden
  (`tools/goldens/node_persist_layout.txt`, re-blessed only via the D-394 flow), and
  `check_identifier_retirement.py::paired_bump_check` REDs when the listing moved while
  `SHARDED_SNAPSHOT_VERSION` didn't bump in the same tree — closing the triple-vacuity a size-neutral
  count-neutral row swap leaves in count-locks + size guards + a same-commit-regenerated byte-golden
  (the D-208 M7 hole). Sister enrollment: persist-wire WIDTH constants (`ROLLING_IC_MAX_WINDOW` /
  `MAX_WINDOW`) as immutable `wire-const` ledger rows — a width change is listing-invisible but
  Check-H-red. AR-8 applied at build: independently adversarially reviewed pre-commit
  (report: `plans/v5.15-live-readiness/reports/2026-08-14-persist-layout-guard/`).

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
