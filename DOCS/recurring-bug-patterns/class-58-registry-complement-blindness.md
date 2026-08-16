---
type: ledger-template
class_id: 58
title: Registry complement blindness (a guard proves the rows it HAS are right; nothing asks whether they are ALL the rows)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-08-15
surface_tags: [registry, wire-format, persistence, cfg-flow, ci-tooling, false-green, capital-safety]
severity: high
recurrence_count: 11
last_amended: 2026-08-16
first_instance: v4.7.25 (node_gross_wins / node_losses / idle_cycles — TECH_DEBT-196)
closure_mechanism: the DOMAIN column on FOREACH_REGISTRY (D-421 step 5) — every registry declares what its rows are the COMPLETE SET OF, and declaring nothing FAILS; per-registry complement guards (check_node_ctx_partition.py) for the STRUCT: shape. For the GATE-BIT (sub-shape B) surface the mechanization is EMIT-SIDE group coverage against the registry's own group COLUMN — never per-bit producer/consumer set arithmetic, which was prototyped at D-421 step 6 and came back INVERTED on both headline cases (see § Detection signatures, the 2026-08-16 correction)
sister_classes: [4, 30, 51, 12, 44]
---

## Class 58 — Registry complement blindness

**Surface:** any X-macro registry that is a COVERAGE registry — one whose rows are supposed to
exhaust a set that exists independently of the registry (a hand-declared struct's members, an
enum's values, a codebase-wide macro population, an emitted wire format's fields).

> Codified 2026-08-15 at D-421, WITH its guard rather than before one (the deliberate build order:
> the class is written from three shapes and eight instances instead of one anecdote). Severity
> HIGH — two of the founding instances are CRITICAL and one is execution-proven on a capital
> control. Per-class file per file-size-split-discipline.

**Every guard around a registry points the rows FORWARD.** A count-lock pins the number of rows. A
layout golden freezes the flattened listing. A byte golden freezes the emitted bytes. A paired-bump
rule ties a layout delta to a version bump. All four answer *"are the rows we have right?"* and
**none** answers *"are these ALL the rows there should be?"* — so a field added to the underlying
set and never enrolled is invisible to every one of them, simultaneously, while they all report
green.

The founding instance is the shape at its purest: `node_gross_wins` / `node_losses` /
`idle_cycles` were added to the per-node struct at v4.7.25 and **silently never persisted**. Stats
read $0.00 after every restart until v5.4.3 caught it — a year of a green build over a real bug,
because nothing in the tree was capable of asking the question.

**The complement is a kind of question nobody asks.** That is why this is a class and not a
one-time miss: no individual guard is wrong, and adding more forward-facing guards cannot close it.
Only an EXTERNAL enumeration of the domain — clang's real member list, the enum's real values, a
codebase scan — can reveal a row that was never written.

## Sub-shapes (one class, three directions — the fixes differ, the lesson is one)

- **A. Producer-side — a member of the domain with no row at all.** The registry is a coverage
  registry over a set that exists without it, and something joined the set without joining the
  registry. *Instances: `node_gross_wins`/`node_losses`/`idle_cycles` (v4.7.25, TECH_DEBT-196) ·
  `drift_history` in NO registry with NO stated exclusion (the D-421 origin symptom) · the 22
  `NodeContext<F>` members with no declared persist status until D-421 step 2 · 32 global cfg keys
  with no registry row, 30 of them determinism-bearing and parsed by raw `atof` with no malformed
  capture.*
- **A′. Sibling asymmetry (the sharp variant of A).** Two structurally identical things are
  treated differently, and the difference is invisible because each half is individually correct.
  *Canonical: `ic.predictions.{count,head}` persisted while `ic.actuals.{count,head}` were not. A
  perfectly-correlated predictor read **IC = −0.5238** after a warm restart plus 6 trades, and that
  IC drives `DriftHistory_CheckBreach` → `KILL_TRIPPED` — a capital control, execution-proven.*
- **B. Gate-reachability — the rows are correct and the gate reading them is unreachable.** The
  registry is complete, its consumers are wired, and the branch that would act on them can never be
  taken. *Canonical: the cfg-derived stamp↔runtime drift check is **unconditionally vacuous** — all
  36 `STAMP_BOUND_CFG_DERIVED` fields are emitted, parsed, and never compared, because the gate
  reads a group bit whose emit-side producer was retired at the `.B.3` prefix migration while the
  consumer stayed.*
- **C. Consumer-side — the registry is SSoT for a format whose readers cannot be enumerated.**
  Readers live in other binaries, other languages, or duplicate the registry's content by hand
  instead of reading it. *Instances: `GUI/TradeReader.hpp` parses the LEGACY trade-log schema, so
  chart markers and the Equity Curve are unconditionally empty (operator-observed independently) ·
  the cfg parser hardcodes `sid = 4` as a numeric literal rather than the `STRATEGY_EMA_CROSS`
  enum symbol, defeating the documented "callers fail at compile time" protection when
  `__has_include` shifts the enum's values.*

## Detection signatures

**The "no stated reason" heuristic is REFUTED as the sole discriminator.** It was 2-for-2 across
the first two shards of the D-421 sweep and then instance A′ appeared: it *had* a documented reason
— *"the two rings advance in lockstep"* — and the reason was **true of the push path and false
across the persist boundary**. A reason that is merely written down is a hypothesis. What actually
found the bug was structural:

```bash
# A/A′ — SIBLING ASYMMETRY: two structurally identical members, one enrolled and one not.
#        This is the signature that worked; lead with it.
#        (enumerate the domain EXTERNALLY, then subtract the rows — never walk the rows)
python3 tools/check_node_ctx_partition.py          # the STRUCT: shape, mechanized
python3 tools/check_meta_registry.py               # Check 1 = the codebase-macro complement

# A — a coverage registry with no external enumeration at all: grep for count-locks that are the
#     ONLY completeness claim (a count-lock is vacuous against a count-neutral swap AND against
#     a member that was never counted).
rg -n "static_assert\(.*_COUNT == [0-9]+" --type-add 'h:*.hpp' -th

# B — gate-reachability: a consumer gated on a bit/flag whose PRODUCER no longer exists.
#     Find the set-side and the read-side of every gate bit and diff them.
rg -n "STAMP_SET\(|BITMAP_SET\(" ; rg -n "STAMP_HAS\(|BITMAP_IS_SET\("
#
# B, THE SHARP VARIANT — **the only PRODUCER is a TEST FIXTURE.** Partition the producer
# set by tests/ vs production. If every non-test setter is dead, quarantined, or circular
# while a fixture hand-sets the value, the chain LOOKS exercised end-to-end and the gate
# stays green for years. This is the single highest-yield check of the sub-shape, and it
# is why the D-421 instance survived a whole release train.
rg -n "STAMP_SET\(.*<bit>" tests/ ; rg -n "STAMP_SET\(.*<bit>" --glob '!tests/'
#
# B, the formulation to PREFER — do not try to prove "no writer exists tree-wide". That is
# an unbounded negative over the tree PLUS any external persisted format the parser reads,
# it cannot be mechanized, and at D-421 it produced three errors in one paragraph.
#
# ⚠ CORRECTED 2026-08-16 — the FIRST replacement offered here was ALSO wrong, and was killed
# by a prototype rather than by argument. This block used to say: "enumerate, per gate bit,
# the PRODUCER set reachable from the production emit call sites vs the CONSUMER set; both are
# closed and checkable." An a-class pass implemented exactly that at D-421 step 6 and ran it:
#   inference_cfg  -> GREEN  (it is the founding CRITICAL — a false NEGATIVE)
#   feature_mask   -> RED    (a LIVE parity-critical REFUSE gate — a false POSITIVE that reads
#                             as an instruction to delete a working capital control)
# Both headline verdicts inverted. WHY per-bit set arithmetic cannot work here:
#   - a gate is not a BIT, it is a (struct-instance, bit) PAIR crossing a process/time boundary
#     (inf -> wire file -> r -> handle); three structs share one MASK_ namespace;
#   - the "circular producer" heuristic is SYNTACTICALLY IDENTICAL to seven CORRECT propagations
#     (NodeModelZoo.hpp :383/:409/:417/:444/:448/:474/:481) — the discriminating fact is not in
#     the SET/HAS relation at all;
#   - producers have >=5 syntactic forms (STAMP_SET / BITMAP_SET / STATE_FLAG_SET / raw |= MASK_
#     / BITMAP_ATOMIC_*) and 12 mask families are token-paste fragments no text tool resolves;
#   - a bit whose only producer is a registry-driven PARSER walk over an on-disk format has no
#     in-tree setter at all and is perfectly live (feature_mask).
#
# THE FORMULATION THAT ACTUALLY HOLDS — check the EMIT side against the registry's OWN column,
# never the reachability graph. For each distinct group/domain value G in the registry's group
# column, require >=1 literal setter of G reachable from the single production emit funnel:
#   "no production path sets G, therefore rows gated by G never leave THIS BUILD"
# That claim stays true under every input, including a hand-authored or foreign-branch file,
# because the undecidable question ("can this gate EVER fire?") is never asked. Both sides are
# closed and LOCAL: a registry column, and one funnel. Run at HEAD it found 2 vacuous groups
# with 0 false positives. The general rule: when a relation spans a process boundary, retreat to
# the narrower claim you can actually close over — do not widen the search to compensate.

# C — consumer-side: a literal where a registry symbol belongs (the hand-copied row).
rg -n "= *[0-9]+ *;.*//.*(enum|registry|STRATEGY_|SHALT_)"
```

Then ask the one question that defines the class: **what set are these rows supposed to exhaust,
and who computes that set independently of the rows?** If the answer is "nothing does", the
registry is complement-blind regardless of how green its guards are.

## Structural fix

**Declare the domain, and make declaring nothing FAIL.** The `domain` column on `FOREACH_REGISTRY`
(D-421 step 5) requires every registry to name what its rows are the complete set of — `SSOT` /
`ENUM:` / `STRUCT:` / `COUNT:` / `RANGE:` / `FORMAT:` / `CHECK:` / `PROSE:<why-not>` — so
`check_meta_registry.py` grows ONE dispatching check instead of ~8 bespoke guards. `PROSE:` is
load-bearing, not an escape hatch: a registry either declares a computable domain or states why it
cannot, and **declaring nothing is the failure**. That single rule would have caught
`FOREACH_HALT_REASON`, `FOREACH_BACKTEST_METRIC` and `FOREACH_LIVES_IN_STRUCT` at introduction.

For the `STRUCT:` shape specifically, `check_node_ctx_partition.py` is the proven mechanization:
subtract the persist rows and a `FOREACH_NODE_CTX_PERSIST_EXEMPT` sidecar from clang's REAL member
list, and RED in three directions — **UNACCOUNTED** (sub-shape A), **STALE-EXEMPT** (an exemption
naming a non-member: it protects nothing while making the partition read as accounted — the guard's
own input rotting), **CONTRADICTION** (both persisted and exempt; one declaration is false and the
tool refuses to guess which).

**The exemption must carry a FALSIFIABLE CATEGORY, not free text.** This is the direct lesson of
A′: categories are phrased so a reviewer knows what evidence would refute them (`DERIVED_EACH_PASS`
says *find me the unconditional write, and tell me what reads it before the first one*), because a
free-text reason is exactly how a red gets silenced by something that merely sounds correct. The
guard deliberately does NOT judge whether a reason is TRUE — mechanizing that would manufacture the
same false confidence A′ is made of; verification of the claims rides the pre-coding audit cascade.

## False-positive surface (M3)

- **A registry that legitimately IS the source of truth is NOT an instance.** Most X-macro
  registries here GENERATE their enum (`FOREACH_DEGRADATION_CURVE(X_GEN_ENUM)`), so no external set
  exists to diff against and `SSOT` is the correct, complete answer. Flagging these produces a
  recurrence report against correct code. The discriminator is whether the domain exists
  INDEPENDENTLY of the registry, not whether the registry has an external-looking name.
- **A deliberately-partial registry is not blind, it is scoped** — a sidecar that is sparse BY
  DESIGN (H18 override registries) exhausts nothing and is not claiming to. Its domain is the
  parent's rows, and the parent's completeness is the thing to check.
- **An un-enumerable consumer set is a stated limit, not a defect.** Sub-shape C is an instance
  only when a reader that COULD read the registry duplicates it instead. Readers in genuinely
  separate binaries (a plugin, an external dashboard) are handled by a versioned format contract +
  parity gate — that is the fix shape, not the bug.
- **A count-lock is not the offence.** Count-locks are useful and cheap; they are simply vacuous
  against this class. Their presence is not evidence of complement blindness — their presence as
  the ONLY completeness claim is.

## Distinction from Class 4 (the M3 discrimination D-421 owed at codification)

**Class 4 (snapshot save/load asymmetry) is an asymmetry between two EXISTING halves; Class 58
sub-shape A is ABSENCE from the registry entirely.**

- Class 4: the field HAS a row on one side and not the other — saved but never loaded, or loaded
  but never saved. Both halves are walkable, so the detection is a **diff of two existing walks**,
  and a `/readiness` "should this be persisted?" answer plus a version bump closes it.
- Class 58 A: the field has **no row anywhere**, so there is nothing to diff. Walking the rows —
  from either side, in any direction — can never reveal a row that was never written. Detection
  REQUIRES enumerating the domain from OUTSIDE the registry (clang member list / enum values /
  codebase scan). This is why the fix is a declared `domain` plus an external subtraction, and why
  no amount of save↔load symmetry checking would have found `node_gross_wins`.

Practical test: *if you deleted the registry entirely, would the check still know what to look
for?* Class 4's check would not (it diffs two registry-derived walks). Class 58's must.

Overlaps worth knowing: **Class 30** (sibling array without registry enrollment) is sub-shape A at
the array surface — and its own Barrier-2 tool was never built, which is TECH_DEBT-274 and itself a
phantom-guard instance. **Class 51** (vacuously-green guard) is the *effect* this class produces —
58 is why the guard is green, 51 is what green then means. **Class 12** (wired-but-unexercised) is
sub-shape B at the test surface.

## Instances (the D-421 five-shard sweep, 2026-08-15 — the founding census)

| # | Sub-shape | Severity | Instance |
|---|---|---|---|
| 1 | A | HIGH | `node_gross_wins`/`node_losses`/`idle_cycles` added v4.7.25, never persisted; $0.00 stats until v5.4.3 (TECH_DEBT-196) — **the founding instance** |
| 2 | A′ | **CRITICAL** | `ic.actuals.{count,head}` unpersisted while `ic.predictions.*` were; IC = −0.5238 after warm restart + 6 trades, driving an auto-kill capital control. **Execution-proven.** Had a stated reason; the reason was false across the persist boundary. Fixed engine `564f099` |
| 3 | B | **CRITICAL** | The cfg-derived stamp↔runtime drift check is unconditionally vacuous: 36 `STAMP_BOUND_CFG_DERIVED` fields emitted, parsed, never compared — the gate reads a group bit whose emit-side producer was retired at `.B.3` while the consumer stayed |
| 4 | A | HIGH | 32 global cfg keys with no registry row; 30 determinism-bearing, parsed by raw `atof` with no malformed capture |
| 5 | C | HIGH | `STRATEGY_AUTO`/`STRATEGY_EMA_CROSS` enum values shift with `__has_include`; the documented compile-time protection is defeated because the cfg parser hardcodes `sid = 4` as a numeric literal |
| 6 | C | HIGH | `GUI/TradeReader.hpp` parses the legacy trade-log schema → chart markers + Equity Curve unconditionally empty (operator had observed this independently) |
| 7 | A | MED | `drift_history` in NO registry with NO stated exclusion — the origin symptom the operator read correctly as *"stuff just sitting like this, its a code smell"* |
| 8 | A | MED | 22 `NodeContext<F>` members with no declared persist status; closed at D-421 step 2 (engine `587d44c`) — 49 members now = 27 persisted + 22 declared-exempt |

**Also prevented, not found:** the `[CLASS]_[58]` tag on the exemption registry itself RED-ed at
`check_code_tag_blocks` because Class 58 did not yet exist — a phantom reference caught in the very
registry built to make phantom references impossible.

### Later instances (found AFTER the founding census)

| # | Sub-shape | Severity | Instance |
|---|---|---|---|
| 9 | B | MED | **`environment_meta` is a second vacuous group**, structurally identical to #3 and missed by the five-shard sweep. 5 registry rows (`StampBoundModelConstRegistry.hpp:437-450`) gate on `inf->has_environment_meta`; the bit (`:545`) and mask (`:601`) exist; the **only** two `STAMP_SET(…, environment_meta)` sites are `#define` BODIES — `:722` (the AUTOPOPULATE family, quarantined behind `static_assert(false)` at `:677-682`, PARITY-022) and `:753` (the parser, which sets only what it already read). MED not CRITICAL: the rows are self-described *"operator audit; informational; no enforcement"*, so unlike #3 no capital control rides them. Found 2026-08-16 at D-421 step 6 by the emit-side census. |
| 10 | A | MED | **The GROUPS registry is itself complement-blind** — `FOREACH_STAMP_BOUND_MODEL_CONST_GROUPS` (`:241-247`) declares **6** groups while the `group` column uses **7** (`environment_meta` absent). Sub-shape A at one remove: any tool deriving its universe from that list inherits the gap. The prototype that did so scanned **13 of 23** bits and reported clean. *This is why the corrected detection signature above derives from the USE SITE (the column) and never from the GROUPS list.* |
| 11 | — | MED | **A phantom guard, adjacent to the class rather than an instance of it.** `StampBoundModelConstRegistry.hpp:522-523` states *"build-time test asserts STAMP_BIT_COUNT matches FOREACH_STAMP_BOUND_MODEL_CONST_GROUP_COUNT + standalone count."* No equality assert exists anywhere — only `<= 64` (capacity) and one-sided `>=` lower bounds (`tests/controller_test.cpp:23888`, `:23894`, `:23980`), which stay green when rows are DELETED (Class 51 mode C). The adjacent arithmetic at `:520-521` (*"groups first (6 bits), then standalones (7 bits) = 13 total"*) is stale against an actual 7 + 17. Recorded here because the comment is *why nobody looked*: it told every later reader the completeness question was already answered. |

**What #9-#11 add to the class.** The founding census established that complement blindness is
found by asking the unasked question. These three establish the follow-on: **the first mechanization
you reach for is itself a candidate instance.** A guard deriving its universe from a registry that
is complement-blind (#10), described by a comment promising a guard that does not exist (#11), will
report the surface clean — and #9 was sitting in that unscanned remainder the whole time.

## Meta

The METHODOLOGY gap — *the complement is a kind of question nobody asks* — is carried separately as
an Mn per the standing Class-vs-Mn split, because the fix for the class (declare the domain) is not
the fix for the gap (learn to ask). Every guard involved in the founding census was green **and
correct**; that is the whole point, and it is why this class cannot be closed by making the existing
guards stricter.

**That Mn is HOMED, not minted — TECH_DEBT-282.** Deliberately no number is reserved here. Minting
an Mn is the § 11.5 procedure (spec + skill amendment + `/readiness` Check + memory + CI tool where
mechanical), and a half-minted one is worse than none: AR-14 sub-shape (4) is precisely the
"un-promoted reservation / empty slot" hazard, where an ID minted in prose and never created lets a
later mint silently re-point every old citation. So this section says *an* Mn and cites the debt row
that owns it, rather than claiming M11 and leaving a citable slot empty.

**Cross-ref:** H15 (registry enrollment) · H21 (identifier retirement) · D-421 · TECH_DEBT-196 ·
TECH_DEBT-274 · `feedback_guards_compound_enforcement_is_leverage` ·
`feedback_enumerate_set_before_categorical_claim` (M9 — the set-enumeration discipline this class is
the registry-surface instance of) · `framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md`
(the `domain` vocabulary SSoT fence) · `framework-patterns/registry-coverage-ci-check-pattern.md`.
