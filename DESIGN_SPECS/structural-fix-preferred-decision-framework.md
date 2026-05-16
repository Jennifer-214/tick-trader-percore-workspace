# Structural fix preferred — decision framework

**Established:** 2026-05-09 (formalized; in practice since v5.14.1.B.3)
**Status:** ACTIVE
**Cross-references:**
- FoxML_Trader_v2 `CLAUDE.md` item 19 — public statement of the rule
- FoxML_Trader_v2 `CLAUDE.local.md` `feedback_structural_fix_for_recurring_class.md` — operator framing
- FoxML_Trader_v2 `CLAUDE.local.md` `feedback_overengineering_boundary_when_future_easier.md` — sibling rule
- FoxML_Trader_v2 `DOCS/RECURRING_BUG_PATTERNS.md` — bug-class catalog (input to this framework)

---

## Problem statement

When fixing a bug, two paths exist:
1. **Direct patch** — fix this instance. Smallest diff. No ripple.
2. **Structural fix** — eliminate the bug class. Bigger diff. Future instances impossible.

Most bugs warrant direct patch. But for SOME shapes, the bug recurs across instances — direct-patching each instance is recurring debt + each occurrence costs hours to debug. For these, structural fix is correct even though the upfront cost is higher.

This framework helps decide which path to take.

---

## The decision framework

### Step 1: Identify the bug shape

Read the bug + ask: **what's the CLASS of this bug?**

Examples of shape-bug-classes (FoxML_Trader_v2 catalog):
- v5.9.5b: production-caller adds field → forgets to populate → silent zero in output
- Class 18 (mirror-incomplete): code mirrored from elsewhere → reads forget some inputs → undefined behavior
- Class 11 (extensibility friction): adding next instance requires N-site update → N grows → forgot site → bug
- Class 14 (scope creep at audit time): audit finds gap → quick patch → audit doesn't re-run → drift accumulates

If a bug doesn't fit a known shape, it's a one-off. **Direct patch is correct.**

### Step 2: Check the recurrence count

If the shape has occurred 2+ times in the codebase history:
- 2 occurrences: SUSPECT recurring class. Track in DOCS/RECURRING_BUG_PATTERNS.md if not there. Direct-patch this instance; flag for structural fix on next recurrence.
- 3 occurrences: CONFIRMED recurring class. Structural fix is now the correct path even at higher upfront cost.
- 4+ occurrences: STRUCTURAL FIX MANDATORY. Direct-patching wastes time + the bug WILL recur.

The 4× threshold is empirical (FoxML_Trader_v2 v5.9.5b class recurred 4× before being structurally extinguished by `STAMP_CFG_AUTOPOPULATE`; cost: ~8h of debugging across 4 instances vs ~3h to ship the structural fix).

### Step 3: Apply the upfront-cost-vs-future-multiplier weighing

Even at recurrence count 2-3, lean toward structural fix when:
- Future-work simplification is large (1 row vs N sites for next addition)
- Upfront cost is bounded (architectural pattern is established; not novel research)
- Risk of structural fix is low (additive; backward-compat preserved)

Operator framing (Caramel 2026-05-09): "headache now > issues later. set it up to be easy to maintain going forward, even if it does add more work now."

### Step 4: Look for the ENABLING pattern

Most structural fixes use a known pattern (X-macro registry, AUTOPOPULATE companion, BITMAP_* API, etc.). If the pattern exists in DESIGN_SPECS/ already, structural fix becomes cheap.

If the pattern DOESN'T exist yet, document it via a design doc + ship the first instance + extract the pattern. Investment cost amortizes across future applications.

### Step 5: Decide + document

| Decision | When | Action |
|---|---|---|
| **Direct patch** | One-off bug; recurrence count ≤ 1 | Fix the instance; commit message references the immediate cause |
| **Direct patch + flag** | Recurrence count = 2; not yet a class | Fix; add entry to RECURRING_BUG_PATTERNS.md as candidate-class; trigger note for next ship |
| **Structural fix (pattern exists)** | Recurrence count ≥ 3 OR future-work-multiplier large | Apply existing pattern (e.g., FOREACH_X registry); migrate existing instances to pattern |
| **Structural fix + new pattern** | Recurrence count ≥ 4 OR strategic architectural moment | Develop pattern in DESIGN_SPECS; ship first instance; extract pattern doc |

---

## Examples

### Direct patch (1 occurrence; one-off)

**Bug:** v5.14.5.B feature `regime_trend_strength` had off-by-one in normalization formula (mid-coding catch).
**Decision:** Fix the formula. Single occurrence; no recurring class.
**Cost:** 1-line fix.

### Direct patch + flag (2 occurrences; potential class)

**Bug:** v5.13.4.A snapshot field added without persistence update — restart loses field.
**History:** 2nd occurrence (v5.13.5.A had same shape).
**Decision:** Direct-patch this instance; add to RECURRING_BUG_PATTERNS.md as Class candidate; trigger note "next snapshot-field addition triggers structural review".
**Cost:** 1-line fix + ~30 min ledger work.

### Structural fix (4+ occurrences; mandatory)

**Bug class:** v5.9.5b production-caller field-population gap.
**History:** 4 occurrences (PARITY-002, -003, -004, -005, -008).
**Decision:** Structural fix via STAMP_CFG_AUTOPOPULATE companion macro.
**Cost:** ~3h ship; eliminates class entirely (vs cumulative ~8h debug across 4 prior occurrences).
**Future:** all future stamp-bound cfg field additions auto-flow.

### Structural fix with new pattern (strategic moment)

**Decision:** v5.14.8.A.merged closes TECH_DEBT-006 by introducing the FOREACH_STAMP_BOUND_MODEL_CONST registry + presence-dispatch token-paste pattern.
**Why:** Architectural fields had been added manually for 8+ instances (each requiring N-site updates). Recurrence count well past threshold. Pattern (X-macro registry) was established in cfg-bound sister registry; extension to model-const fields was natural.
**Cost:** ~6-8h ship + ~2h DESIGN_SPECS extraction.
**Future:** all future architectural stamp body fields auto-flow; pattern reusable for FOREACH_FAILURE_MODE + future TECH_DEBT-013 sweeps.

---

## Trade-offs + when to apply

### Apply structural fix when:
- Recurrence count ≥ 3 in the codebase history (confirmed class)
- Future-work-multiplier is concrete + planned (next 5+ field additions visible)
- Pattern is established or low-risk to develop
- Wire-format / API stability allows additive change

### Direct-patch + flag when:
- Recurrence count = 2 (potential class; needs more data points)
- Pattern is novel + high-risk (new architectural research)
- Time pressure forces today's ship (defer structural to next sprint with explicit trigger)

### Direct-patch only when:
- One-off bug
- No clear shape / class
- Patch is mechanical + cost-bounded

### When NOT to over-apply

The framework can be MISAPPLIED. Anti-patterns:

1. **Premature abstraction** — building a registry when there are 2 instances + no pending growth. Adds complexity without proportionate benefit. Wait for triggers.

2. **Over-engineering edge cases** — the structural fix should close THE class, not generalize for hypothetical future variants. Stop at "this class is dead"; don't keep adding flexibility "for the future".

3. **Scope creep into unrelated structural work** — when fixing class A, don't also restructure class B unless they're bounded together. Each ship has scope.

---

## Reference implementations

### v5.14.1.B.3 — STAMP_CFG_AUTOPOPULATE

- Recurrence count: 4 (PARITY-002/003/004/005/008)
- Decision: structural fix (mandatory at 4× recurrence)
- Pattern: AUTOPOPULATE companion macro paired with X-macro registry
- Outcome: class extinct for cfg-bound stamp body fields

### v5.14.8.A.merged — FOREACH_STAMP_BOUND_MODEL_CONST

- Recurrence count: 8+ instances of architectural fields added manually
- Decision: structural fix + new pattern (token-paste presence dispatch)
- Pattern: extends X-macro registry to handle partial-mirror struct generation
- Outcome: class extinct for architectural stamp body fields; pattern reusable for FOREACH_FAILURE_MODE + TECH_DEBT-013 sweeps

### v5.14.2.E.1 — PostLoadSetup helpers

- Recurrence count: 4 (PARITY-009/010/011/012)
- Decision: structural fix via helper extraction
- Pattern: extract shared call-sequence into helper; mirror sites become single helper-call
- Outcome: Class 18 (mirror-incomplete) extinct for model-load surface

### v5.15.5.C.3 Phase 5.B — ShardedTradeLog helpers (smaller-scale class close)

- Recurrence count: 2-3 sites mirrored (filename format string at 3 sites; dual-write block at 2 sites)
- Decision: structural fix via two helper extractions, applied at audit time BEFORE commit
- Helpers:
  - `ShardedTradeLog_FormatPerCoreFilename(buf, n, symbol, c)` — single source of truth for the per-core filename pattern (used by `_Init`, `_Rotate`, and `EngineSharded_Run` archive copy)
  - `ShardedTradeLog_WriteRow(log, core_id, row, n)` — single chokepoint for aggregate + per-core mirror dual-write (used by `RecordEntry` + `RecordExit`; closes "next consumer forgets per-core mirror" class for any future `RecordX`)
- Pattern: prevents the recurrence class FROM FORMING — applied at first-mirror-detection (audit-time) rather than waiting for 3-4 documented recurrences
- Lesson: when an audit (e.g., pre-commit /merge-scan or design-philosophy review) catches a 2-site mirror in NEW code, the structural fix is cheap (~30 min) and pays the same future-multiplier as later-detection. Apply at audit time; don't wait for the class to recur.
- Outcome: Class 18 (mirror-incomplete) prevented for the per-core trade-log surface; future RecordX additions cannot drift

### v5.15.5.C.4 Phase F + G — Phase-separated drainer (closes transient-source-data class)

- Recurrence count: 2 (D2.C `exit_entry_notional` derive UNSAFE; D2.D `exit_total_fees` derive UNSAFE; both blocked by same-cycle Position-state overwrite race)
- Decision: structural fix via PHASE-SEPARATED DRAINER (split OrderManager_Tick into SELL-phase + BUY-phase with DrainPostFill consumer pass interleaved between)
- Pattern: source state (Position) is guaranteed in CLOSE-completed form during the close-side consumer pass; derive-from-source becomes SAFE for previously-blocked fields
- Closes: the "transient-source-data" failure mode class for the FillRecord-as-snapshot surface (3 fields unlocked: exit_net_pnl + exit_entry_notional + exit_total_fees)
- Win:
  - 1152B saved per OMS (3 FillRecord fields × 24B × 16 records)
  - FillRecord shrinks 128B → ~56B (1 cache line per record vs 2)
  - Drainer close-mask iter touches 1 cache line per slot (was 2)
  - Scales to richer maker-order lifecycle (PARTIAL_FILL / CANCELED / TIMEOUT phases)
- NEW DESIGN_SPEC: `phase-separated-drainer-for-safe-cross-temporal-derives.md`
- Pattern composition: enables `aggressive-memory-reduction-techniques.md` Technique 4 (derive vs store) for fields that previously failed safety check; reduces `slot-state-foreach-registry-with-storage-routing.md` FOREACH_FILL_RECORD_FIELD registry to a smaller set of entries

### v5.15.5.F.4c.4 — registry-coverage-ci-check-pattern.md (NEW Stage 3 ACTIVE spec; CI tooling structural-fix mechanism category)

- Recurrence count: 5 across bug-class shapes that share the "field added without registry/coverage enforcement" pattern at meta-layer — Class 18 (mirror-incomplete) + Class 19 (hardcoded enum names) + Class 21 (parallel descriptors) + Class 27 (scalar cfg-mirror) + Class 30 NEW (sibling array without registry enrollment)
- Decision: structural fix via NEW DESIGN_SPEC retroactively extracted from 3 canonical applications (Check 2 per-core cfg coverage + Check 7 scalar cfg-mirror anti-pattern + Check 8 OmsState per-slot sibling coverage). Per-variant Stage tracking inside one spec body: Shape A (positive coverage) Stage 3 ACTIVE; Shape B (anti-pattern enforcement) Stage 2 DRAFT
- Pattern: Python CI tool template + struct↔registry coverage check + explicit-exempt mechanism with rationale category + migration trigger
- Outcome: bug class structurally cannot recur at field-add-discipline layer; future per-subsystem registries get matching CI check via template cloning
- **NEW STRUCTURAL-FIX MECHANISM CATEGORY: CI tooling** — sister to compile-time `static_assert` (Class 14 `static_assert(FOREACH_X_COUNT <= sizeof(type)*8)` precedent) + helper-extraction (Class 18 PostLoadSetup precedent) + AUTOPOPULATE companion macro (Class 11 `STAMP_CFG_AUTOPOPULATE` precedent). Each mechanism enforces at a different layer; CI tooling enforces at PR/merge time with actionable error messages

---

## Lessons / gotchas

### Recurrence count discipline

Count INSTANCES of the SHAPE, not instances of the bug ID. If 4 different parity issues all stem from the same production-caller class, that's 4× recurrence.

Track in DOCS/RECURRING_BUG_PATTERNS.md per-class. Each entry includes: shape description + canonical instances + structural-fix-applied (if any).

### Sibling rules

- `feedback_structural_fix_for_recurring_class.md` — the recurring-bug case (this framework)
- `feedback_overengineering_boundary_when_future_easier.md` — applies even WITHOUT recurring bug; pure forward-looking maintainability is enough
- `feedback_no_defer_for_effort.md` — defer is last-ditch, never an effort-avoidance escape hatch
- `feedback_reduce_touch_sites.md` — boundary-stable refactors over wide cascades

These compose. Apply the most specific that fits the case.

### Trigger documentation

When deferring a structural fix to a future ship, document the TRIGGER explicitly:
- "Next ship adding 3+ cfg fields triggers FOREACH_CFG_FIELD" (TECH_DEBT-009)
- "Next ship touching PerCoreSnap layout triggers BIT_FLAG migration" (TECH_DEBT-013)
- "Next snapshot-field addition triggers structural review" (Class candidate)

Triggers prevent silent debt accumulation. Without them, deferred items get forgotten.

### Don't structural-fix without RECURRENCE_BUG_PATTERNS evidence

If the proposed structural fix would close a "class" with only ONE historical instance, it's not a class — it's a one-off. Don't pre-build infrastructure for hypothetical future bugs.

The RECURRING_BUG_PATTERNS.md catalog is the gating evidence. If a class isn't there, structural fix is premature.

### Structural fix CLOSES the class permanently

After applying a structural fix:
1. Audit existing instances; migrate to the new pattern
2. Mark TECH_DEBT entry as CLOSED (in DOCS/TECH_DEBT.md)
3. Update DOCS/RECURRING_BUG_PATTERNS.md class entry: "Extinguished by <pattern> at <ship>"
4. Cross-reference in CLAUDE.md item list (architectural rules)

If a future instance of the SAME class appears post-extinction, it's a regression — the structural fix has a gap. Audit and patch.

---

## Anti-patterns

### "We always structural-fix"

Forces over-abstraction. Direct patches are the right answer for one-offs. Don't apply this framework to every bug.

### "We never structural-fix; just patch"

Misses the win on recurring classes. After 3-4 instances of the same bug, direct-patching the 5th costs more cumulatively than the structural fix would have at instance #2.

### "Structural fix in a ship that's already large"

Bundling structural fixes into shipping ships expands blast radius. If ship X is closing 5 features, don't also structural-fix bug class Y unless X's surface area naturally includes Y. Otherwise: separate ship for Y.

### "Apply pattern Z everywhere preemptively"

After developing a pattern, the temptation is to apply it everywhere. Resist. Apply only at TRIGGERED sites (per TECH_DEBT entries). Premature application = scope creep.

---

## Cross-references

- FoxML_Trader_v2 `CLAUDE.md` item 19 — public-facing version
- FoxML_Trader_v2 `CLAUDE.local.md` `feedback_structural_fix_for_recurring_class.md` — operator framing
- FoxML_Trader_v2 `DOCS/RECURRING_BUG_PATTERNS.md` — gating evidence catalog
- FoxML_Trader_v2 `DOCS/TECH_DEBT.md` — deferral ledger with explicit triggers
- `x-macro-registry-with-presence-dispatch.md` — canonical pattern for "adding next instance" classes
- `autopopulate-pattern-for-production-caller-class.md` — canonical pattern for production-caller class
- `audit-driven-pre-coding-gate.md` — surfaces classes for structural review
