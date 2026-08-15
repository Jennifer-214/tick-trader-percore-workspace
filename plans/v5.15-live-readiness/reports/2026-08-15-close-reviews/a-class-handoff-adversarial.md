---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: Stage 6.5.4 — ADVERSARIAL (default-REFUTED) review of the E.1.2 handoff ADDENDUM-2
agent_class: a-class
delivered: 2026-08-15
ground: engine 49244a4, workspace c46b58f (target moved mid-audit)
headline: REFUTED — 4 HIGH, 10 MED, 4 LOW. One pattern generates four of the HIGHs: supersede-by-banner without a completeness pass over what the banner orphans. The sharpest is HIGH-4, where my own Check-2 answer ("N/A, no plan body amended") asks what was WRITTEN rather than what was OWED — Class 58 producer-side complement blindness, reintroduced in the close-out ledger of the ship that codified it
operator_decision_owed: none — every finding is mine to fix; the agent's edits 1-3 are gated BEFORE push because HIGH-3 + HIGH-4 together route a fresh session's first instructed read into redoing shipped work
sister_reports: v-class-deliverable-completeness.md
---

# A-CLASS ADVERSARIAL VERDICT — Stage 6.5.4 review of `2026-08-14-E.1.2-steps3-5-v11-delta-handoff.md`

**Overall: REFUTED.** The handoff is not sound as a pickup artifact. I ran all seven attack lines plus the rigor-honesty question. **Four HIGH defects, six MED, four LOW.** Two of the HIGHs would actively mislead a fresh session into a wrong action, not merely leave it uninformed.

Ground: engine `/home/caramel/code/FoxML_Trader_v2` @ `49244a4` · workspace @ `c46b58f` (**the target moved under me mid-audit** — `c46b58f` added the Stage-6.5.2 judgment ledger at lines 54–93; all cites below are against that current text, and two of my earlier findings were partially closed by it, noted inline).

---

## ATTACK 1 — Claims false at HEAD · **PARTIALLY REFUTED**

**All 13 SHAs resolve and describe the work claimed.** Engine `b777e5d 7267c5f 7240f3d 564f099 49244a4` and workspace `0759b00 ca0c73b 3baa1a3 b04266b 859fbf2 183fc47 56604a2 8923418` (+ `406cff6`, + ADDENDUM-1's `2292c16 b692262 3637a88 66e71ba`) all exist with matching subjects. `bc37c62` is genuinely 2026-04-30. That part **survives**.

### HIGH-1 — the "both pushed" anchor is false, and was false when written
`…/handoffs/2026-08-14-E.1.2-steps3-5-v11-delta-handoff.md:21`
> `Anchors — engine 49244a4, workspace 8923418, both pushed.`

The handoff's *own commit* is `d802db9`, which is already past `8923418`. Four workspace commits followed (`95938ec` 17:44, `0d53584` 17:48, `64216ed` 17:55, `c46b58f` 18:00), and `git status -sb` in the workspace reads **`ahead 1`** — `c46b58f` is unpushed right now. `check_close_out_completeness.py` flags this itself: `[MED] workspace has 1 UNPUSHED commit(s) — a close that leaves work on one machine has not closed`.

This isn't the unavoidable chicken-and-egg (a doc can't cite its own SHA). Three of those four commits are *substantive close-out work* — `95938ec` opened TECH_DEBT-276/-277 and amended PARITY_ISSUES; `64216ed` wrote six missing reference docs. A fresh session diffing `8923418..HEAD` finds five commits the anchor says shouldn't exist.

**Fix:** state the anchor as a range with an open end (`workspace: 8923418 + the close-out commits that follow this write; re-derive with git log 8923418..HEAD`), not a point SHA plus "both pushed".

### MED-1 — the absence claim's stated evidence is false (attack 6 overlaps here)
`:34`
> `rg 'memset|calloc' CoreFrameworks/ Backtest/` returns only unrelated panel-state resets

I ran that exact command. It returns **62 hits** across 15 files. Only the `Backtest/BacktestPanels.hpp` subset are panel-state resets. The rest include:
- `CoreFrameworks/ControllerConfig.hpp:460` — `ControllerConfig() { memset(this, 0, sizeof(*this)); }`
- `CoreFrameworks/EngineSharded/Run.hpp:1266` — `memset(&g_shared, 0, sizeof(g_shared));` (in one of the two files the same bullet names as a container site)
- `CoreFrameworks/ShardedSnapshot.hpp:66`, `Reconcile.hpp:686/:732/:774`, `OrderEventLog.hpp:686/…`, `OrderManager.hpp:1155/:1908`, `Async.hpp:173`, `Notify.hpp:277`, `PortfolioController.hpp:416/:466`

The **conclusion** (nothing memsets `EventLoopState`/`NodeContext`) holds — I checked. The **stated evidence** does not. This is the §2.5 "manufactured confidence" shape at its purest: a reader who trusts the descriptor stops looking, and a reader who runs the command finds a mismatch and has to redo the whole analysis. Name the actual predicate: *"no memset/calloc in the tree targets an `EventLoopState` or `NodeContext` object — 62 hits reviewed, all other targets."*

### MED-2 — "Fixed by NSDMI on **both**" has the wrong antecedent
`:34`
> Bare `EventLoopState<F> state;` at **both container sites** (`EngineSharded/Run.hpp`, `Backtest/BacktestSharded.hpp`); … Fixed by NSDMI on **both** (sibling symmetry)

`git show 49244a4 --stat` touches 7 files; **neither named file is among them**. The fix is on the two *structs* in a third file: `CoreFrameworks/SlowPathGateRegistry.hpp:196` (`uint16_t flags = 0;` in `SlowPathGateState`) and `:208` (same in `GlobalGateState`). The nearest antecedent for "both" is the two filenames two clauses earlier; "(sibling symmetry)" is the only disambiguator and is weaker than an explicit file list. A fresh session greps `Run.hpp` / `BacktestSharded.hpp` for the fix and finds nothing.

### LOW-1 — "every other `FOREACH_SHALT` code was clobbered" over-counts by one
`:35`. `Strategies/StrategyInterface.hpp:295-315` has exactly **20** rows including `X(OK, …)`. `SHALT_OK` is the value the reset *writes*, so it was never clobbered. "Only RECOVERY and EXIT_PREDICTED survived" + "every other was clobbered" implies 18; the correct figure (and the one the commit body uses) is 17. Trivial, but it is the M9 shape inside the bullet that announces an M9 finding.

**Verified sound at HEAD:** `SHARDED_SNAPSHOT_VERSION 11u` (`ShardedSnapshotPersist.hpp:114`) · `node_persist_layout.py` GREEN 46 · `check_identifier_retirement.py` GREEN 48 · partition guard rc 2 REFUSAL · `--selftest` exactly **17** teeth, all fire · `FOREACH_OMS_PER_SLOT_FIELD` = **5** rows (so the decision log's "5→1" is accurate) · F-096 landed (`CoreFrameworks/EngineSharded/Async.hpp:921/:925` — `leg_a = Money_Mul(intended, partial_pct)`, `Money_Sub(intended, leg_a)`) · drift blind window = 4 (`ML_Headers/ConfidenceScore.hpp:1397` `if (dh->count < 5) return 0;`) · `NPF_PROJECT_POISON` genuinely absent · Class 58 genuinely not codified.

---

## ATTACK 2 — Internal contradiction · **REFUTED**

### HIGH-2 — the frontmatter both asserts and denies D and E
`:12`, one field, verbatim:
> `D + E DONE; …` … `REMAINING = D (PORTFOLIO T1 retire, no TTY) + E (F-096 Money legs) + F (close-gate: Class 58 + partition guard + NPF_PROJECT_POISON + ship ritual).`

The `HISTORICAL:` scope marker sits ~200 characters upstream and has **no terminator**, so the sentence beginning `REMAINING =` reads present-tense. `coding_status` is the one field `/accept-handoff` and `check_handoff_active_singleton.py` surface — it is the highest-traffic, lowest-context text in the document, and it self-contradicts on the two items the whole addendum exists to declare done.

It is *also* stale independently of the scoping: `F`'s list names "partition guard", which **landed** at `b04266b`. So even read as history, the enumeration is wrong.

Compounding: `:64-65` (new, from `c46b58f`) claims *"Check 5 — handoff currency … items D and E are struck as done."* They are struck in ADDENDUM-2 prose and **not** in the frontmatter. The currency check certifies a state the artifact doesn't hold.

### MED-3 — ADDENDUM-1's "REMAINING" is superseded but its *sibling* content is orphaned
`:117` REMAINING items 1–3 are correctly dead. But ADDENDUM-2 says it supersedes "everything below", and **everything below** includes three sections it does not replace:
- `:180` "Critical pickup-time reads (in order)" — still points at a banner that is now wrong (see HIGH-3)
- `:255` "TaskList (recreate at pickup)" — a fresh session is *instructed* to recreate it. Row #1 is done-except-close-gate; row #2 (`wire-const ledger --update`, 2 ADD-info rows standing) is **moot** — `check_identifier_retirement.py` at HEAD prints one line, GREEN 48, with **zero** ADD-info rows. ADDENDUM-2 supplies no replacement TaskList.
- `:263` "Re-derive at pickup" — see MED-4.

Blanket supersession without replacement is worse than leaving the old text unmarked: it marks the content untrustworthy while still being the only content there.

### MED-4 — the documented pickup re-derive block fails
`:269` `check_identifier_retirement.py # expect GREEN 48 ids + 2 wire-const ADD-info` → GREEN 48, **no ADD-info rows**.
`:270` `rg -n "SHARDED_SNAPSHOT_VERSION  10u" … # still 10 pre-delta` → **rc 1, no match** (it is `11u`).

The literal last instruction in the document, under a heading that says "Re-derive at pickup", produces an unexplained red.

---

## ATTACK 3 — Contradiction with plan body / decision log · **REFUTED — this is the worst one**

### HIGH-3 — the plan body says D and E are PENDING; the handoff sends the reader there FIRST
`plans/v5.15-live-readiness/subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md:47-48`:
```
>    - ⏳ **D — D-289/2 PORTFOLIO retirement** (T1 live-`#define` tombstone …)
>    - ⏳ **E — F-096 Money legs** (`Async.hpp:853-932` still `double`) …
```
`:43` still reads `3. Steps 3–5 — **PARTIALLY LANDED 2026-08-14 evening**` with sub-bullets A/B/C only. Grep of the whole plan body: `b777e5d` **0** hits · `7267c5f` **0** · `7240f3d` **0** · `564f099` **0** · `49244a4` **0** · `D-421` **0**. The banner's own currency stamp reads *"anchors in THIS banner verified at `a71b893` (2026-08-13)"*, and the plan frontmatter `:9` still says *"resume at the D-305 tail"*.

The handoff `:180-182` names this banner as **"Critical pickup-time reads (in order): 1."** So the document's own #1 instruction routes a fresh session to a doc that will tell them to go do D and E — which are done. `Async.hpp:921/:925` is Money at HEAD; a session following the plan body would re-open a Money conversion that already shipped.

### HIGH-4 — Check 2 declares an omission to be "N/A"
`:60-61` (new, `c46b58f`):
> **Check 2 — plan-body frontmatter completeness.** N/A this session: **no plan body was amended.** The in-flight work is tracked in the D-421 decision-log STATUS block and this handoff, **both current**.

Two failures in one bullet:

1. *"No plan body was amended"* answers the wrong question. Check 2 asks whether a stamp was **owed**, not whether one was **written**. Two ⏳ markers for work this session completed = two owed stamps, not written. **This is D-421's own complement-blindness shape** — the check asked what was written, not what was missing — asserted three sections below the addendum that codifies it. That is the single sharpest thing in this review: the session's headline meta-finding was reintroduced in the session's own close-out ledger.

2. *"both current"* is false of the decision log. `plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md`, D-421 STATUS block, contains **both** of these:
   - `**STEP 2 IN PROGRESS — the guard + the verification LANDED**; the 22 exemption ROWS are the remaining piece.`
   - `**STEP 1 LANDED** … Steps **2-7 NOT started**.`

   A new paragraph was prepended and the old sentence left standing. **This is precisely the failure mode you flagged: the sweep-for-stale-values missing a value.**

### MED-5 — three further decision-log staleness items
Same file, D-421:
- `Frozen evidence: reports/2026-08-15-complement-blindness-sweep/ (S1/S3/S5 saved; **S2/S4 pending**)` — all five (`S1…S5`) are on disk.
- Body: `47 → 48 identifiers, **pending an operator TTY --update**` — the ledger is at 48 and GREEN, and `ca0c73b` is literally *"commit the blessed STRATEGY_EMA_CROSS=4 ledger row — step 0's missing pair"*. Body contradicts its own STATUS block, which says "recorded at operator TTY".
- STATUS anchors: `ws b04266b/859fbf2/56604a2/**+splitter**` — an **unresolved placeholder** left in the SSoT, and `183fc47` is missing entirely. The handoff's table (`:29`) has all five correctly. The SSoT is the degraded copy.

### HIGH-5 — D-421 steps 3–7 are invisible
The decision log's DECIDED build order is **0→7**. Landed: 0, 1, and part of 2. The handoff frames the remainder as *"NEXT ACTION (the one concrete thing)"* and *"step 2 landed except its 22 exemption ROWS"*. Steps **3, 5, 6, 7 appear nowhere in the handoff**:
- step 5 = the **DOMAIN column on `FOREACH_REGISTRY`** — the *decided mechanization*, the reason D-421 is an Mn
- step 6 = gate-reachability check, then the drift-gate fix (the handoff's `:51` OPEN item mentions the drift gate but never connects it to step 6 or to its ordering constraint "THEN, knowing what else is dead")
- step 7 = `FORMAT:` token, then **`GUI/TradeReader.hpp`** — the ⑤ HIGH finding *"chart markers and the Equity Curve are unconditionally empty — the operator had already observed this"*

Step 4 (Class 58) survives only inside the *superseded* ADDENDUM-1 item F and the frontmatter tail. A fresh session that honors "everything below is superseded" never sees any of it.

---

## ATTACK 4 — Volatile counts · **PARTIALLY REFUTED** (and you over-worried about two of them)

`check_close_out_completeness.py` already fires **9 volatile-count findings** on this file (`29-row`, `4 findings`, `7 spec`, `9 memory`, `10→11` ×3, `829→826`, `7→8`) — all in the pre-addendum body, all committed unaddressed. Separately, **the tool is blind to every count in ADDENDUM-2**: `VOLATILE_COUNT_PATTERNS` matches `<digit> <volatile-noun>`, and *exemption / members / teeth* are not in its noun set. So the guard's green on the new content is uninformative.

| Claim | Verdict |
|---|---|
| **"22 exemption rows"** `:39` | **VOLATILE — flag it.** It is `len(NodeContext members) − len(persist-covered)`; both sides move, and the v11 delta just moved one. Worse: **there is no working re-derive path.** The tool the handoff cites (`:46`) currently **refuses before computing** and prints no member list. The only place 22 is derivable is `--selftest`'s incidental `49 - 27`, which the handoff never says. |
| **"49 members"** (decision-log STATUS) | **VOLATILE.** Any `NodeContext` field add changes it. Re-derive: `check_node_ctx_partition.py --selftest`. |
| **"17 teeth"** `:46` | **VOLATILE but LOW-harm** — it is a *usable oracle* ("expect 17 ✅ lines"). It is correct at HEAD (I counted 17) and drifts loudly, not silently. Keep, or say "all teeth fire". |
| **"3740/0"** `:12`, `:21` | **VOLATILE.** True only because engine HEAD == `49244a4`. Stale the moment the exemption rows land. Better as *"suite green at engine `49244a4`"*. |
| **"17 of 20 SHALT codes"** | **NOT in the handoff** — you already reworded it to the member form ("only `SHALT_RECOVERY` and `SHALT_EXIT_PREDICTED` survived"), which is the correct anchor form. It survives in `DOCS/SUBAGENT_ARMING.md:32`, where it is a *frozen historical* measurement and legitimate. **Don't touch it.** |
| **"5→1 rows"** (decision-log STATUS) | **LEGITIMATE.** A frozen historical measurement of a bug's effect. Verified accurate: `FOREACH_OMS_PER_SLOT_FIELD` = 5 rows at HEAD. **Don't touch it.** |
| **"3719/0", "3702/0", "829→826"** | Legitimate *as* per-commit battery records; they are already SHA-anchored in the same table cell. |

Net: **two** counts genuinely need repair (`22`, `3740/0`); one needs a re-derive command it currently can't have (`22`); two you were right to leave alone.

---

## ATTACK 5 — What a fresh session gets WRONG · **REFUTED. "Everything needed is already done" is false three ways.**

This is the highest-value attack and it lands hardest.

### HIGH-6 (composite) — following `:39-42` literally produces a RED, not a GREEN

`:40` `categories per the § verdict tables in reports/2026-08-15-nodectx-exemption-verification/{P1,P2,P3}*.md`
`:42` `the guard currently **REFUSES rc 2** ("registry not there") — writing the rows flips it to GREEN`

**(a) P3 has no category column at all.** I grepped all 14 category tokens across the three reports. `P3-substructs.md` returns **zero hits**. Its verdict table (`:28-30`) has a *Kind* column reading "Accumulator" / "Derived / process-lifetime live state" and a *Verdict* column reading "SAFE-UNPERSISTED". For `turnover`, `drift_history`, `sp_telemetry` the category must be **invented**, and `sp_telemetry` would need `DISPLAY_SINK_ONLY`, whose definition (`tools/check_node_ctx_partition.py:124-126`) demands the rationale **enumerate every reader** — a fresh code walk, not a lookup. P1 (7 fields) and P2 (12 fields) do carry the corrected vocabulary; P3 (3 fields) does not. So the claim is true for 19 of 22 and false for the 3 hardest.

**(b) `drift_history`'s row is blocked on an open operator decision — the handoff's own.** The only category that fits an accumulator reset on restart is `ACCEPTED_RESET`, defined at `:127-128` as *"the operator has accepted the behaviour change and the rationale says what degrades and for how long."* The operator has **not** accepted it: `:50` lists `drift_history` under **"OPEN — operator's, not mine"** with P-3 recommending (d)+(a) and rejecting (b)/(c). ADDENDUM-2 says the next action is unblocked and simultaneously says this input is blocked, ~10 lines apart.

**(c) `gate_state`'s verdict was invalidated by the fix in the same addendum.** P1 `:29` assigns `gate_state` → **`UNESTABLISHED_UNTIL_FIRST_PASS`**, which is a `RED_CATEGORIES` member (`check_node_ctx_partition.py:136-140`) and returns **`return 1`** (`:329`). The selftest pins exactly this: *"always-RED category is a VALID ROW (recordable)"* + *"…and still REDs (recorded is not excused)"*. But ADDENDUM-2 `:34` — three bullets above — describes fixing `gate_state` with an NSDMI, which **makes the field established** and invalidates P1's verdict. The handoff never says so. Follow `:40` literally → write the RED category → guard returns 1 → the reader, primed by `:42` to read a nonzero rc as "rows not written yet", is now debugging a guard that is working correctly.

**(d) an unnoticed refusal trap.** P1's own recommendations propose parameterized categories: `RUNTIME_POINTER(<file:line>)` (`:252`) and `POINTEE_STATE_REDERIVED(warmup-gated)` (`:34`, `:232`). The guard's parser (`:249`) does exact-set membership on the CATEGORY token — a parenthesized form raises **`PartitionRefusal` → rc 2**, indistinguishable at a glance from the "registry not there" rc 2 the handoff told them to expect.

### The `FOREACH_REGISTRY` warning — **SURVIVES, with one omission**
`:43` is correct. `tools/check_meta_registry.py:76,131,138` — Check 1 scans `SCAN_DIRS` (which includes `MemHeaders`) for `#define FOREACH_<NAME>(` and is **FATAL** since `.E.0.10`. A new registry without a row REDs. Good, load-bearing warning. Minor: the tool offers a second path the handoff omits — *"or document as EXEMPTION in tools/check_meta_registry.py"* (`:138`); `EXEMPTIONS` is currently an empty set (`:60`).

### MED-6 — three TECH_DEBT entries this session opened are absent from OPEN
`DOCS/tech-debt/open.md:3895` **TECH_DEBT-274** (med) · `:3916` **-276** (med) · `:3927` **-277** (low). `-274` was opened in `56604a2`, which is in the handoff's own anchors row `:29` — i.e. it existed **before** the handoff was written, so this is a same-session capture gap, not a post-hoc artifact.

`-274` is directly germane to the next action: *"Class 30's Barrier-2 tool does not exist; nine sites across four docs claim it does"* — a phantom-guard finding in `MemHeaders/OmsFieldRegistry.hpp`, the sibling registry file. `-276` names `intended_tp/sl/qty` as unenumerated cross-thread multi-word reads — the same three fields P2 categorizes as `DERIVED_BEFORE_ARM` in the rows about to be written.

### MED-7 — the OPEN doc-hygiene item names the wrong file and inverts the tool
`:52` *"`MEMORY.md` is near its size cap; the hook wants a compaction pass."*

`tools/check_always_loaded_budget.py` at HEAD:
```
  ⚠️  CLAUDE.md         36,750 / 40,000 B  (92% of cap)
  ✅ CLAUDE.local.md   13,210 / 40,000 B  (33% of cap)
  ✅ MEMORY.md         20,617 / 24,400 B  (84% of cap)
```
`NEAR_FRAC = 0.90` (`:39`). MEMORY.md at 84% is **`✅ OK` — the tool is not warning about it.** The doc actually carrying the `⚠️ NEAR` is **`CLAUDE.md` at 92%**, which the handoff never mentions. And `0d53584` *added* to MEMORY.md (`MEMORY_EXTENDED → MEMORY.md` promotion) at the same 20,617 figure, so it was never NEAR at write time either. A fresh session doing the deferred pass would compact a green file and leave the standing warning untouched.

---

## ATTACK 6 — Absence claims without a named search space · **PARTIALLY REFUTED**

You fixed the *scoping* of "no memset anywhere" but the *evidence descriptor* is wrong — MED-1 above. Two more:

### LOW-2 — the in-code comment reintroduced the unbounded quantifier
`CoreFrameworks/SlowPathGateRegistry.hpp:186-187`: *"default-init, no `{}`, **no memset anywhere**"*. Scoped by sentence subject, so defensible — but it is an unbounded *anywhere* written into a code comment by the same commit that widened `SUBAGENT_ARMING` §2.5 to demand quantifier enumeration. It will read as a verified global claim to the next person.

### LOW-3 — "every persist row names a real member" (decision-log STATUS, item (c))
A universal over a set, stated without the enumeration or a tool cite. It happens to be checkable (`--selftest`'s "the two sets actually overlap" tooth is weaker than this claim; the STALE-EXEMPT tooth covers the other direction), but as written it is an unbacked *every*.

**Survives:** `:34`'s *"`NODE_CTX_INIT_AUTOPOPULATE`'s five layers touch it in none, and it is a row of no `FOREACH_NODE_CTX_FIELD`"* — bounded, named, and correct.

---

## ATTACK 7 — The four gotchas · **THREE SURVIVE, ONE IS MISDIAGNOSED**

| `:97` background wrapper exit code | **SURVIVES.** Real Class-57 shape; the `block_pipe_rc_read.sh` hook fired on me twice this session, so the environment agrees. |
| `:98` clangd unreliable + the real `MASK_DRIFT_KILL_TRIPPED` ambiguity | **SURVIVES.** Properly hedged ("but *one* was real"), TECH_DEBT-092 cited. Correctly resists over-generalizing. |
| `:99` you cannot demonstrate UB in a test | **SURVIVES.** Sound reasoning, and the commit body records the failed-control attempt honestly. |
| `:100` `check_per_node_registry_integrity.py` engine-root-only | **REFUTED — right ritual, wrong mechanism, and the mechanism is what a fresh session needs.** |

### MED-8 — the tool gotcha is misdiagnosed; I falsified it in both directions

`:100` says *"must be invoked from the **engine** root … from the workspace it resolves `CoreFrameworks/` wrongly and exits 2"* — i.e. a **cwd** diagnosis. Two probes:

- **Probe A** — cwd = **engine root**, script = absolute workspace path → **rc 2**, `ERROR: file not found: /home/caramel/code/tick-trader-percore-workspace/CoreFrameworks/CfgFieldRegistry.hpp`. Falsifies "invoked from the engine root" as sufficient.
- **Probe B** — cwd = **workspace root**, script = absolute engine path → **rc 0**, all checks PASS. Falsifies "from the workspace it resolves wrongly".

The determinant is the **script path**, never the cwd. `tools/check_per_node_registry_integrity.py:40-42`:
```python
SCRIPT_DIR = Path(__file__).absolute().parent  # .absolute() not .resolve(): keep the engine path, don't follow the workspace symlink (machine-portable)
REPO_ROOT  = SCRIPT_DIR.parent
CFG_REG    = REPO_ROOT / "CoreFrameworks/CfgFieldRegistry.hpp"
```
`.absolute()` is *deliberate* (per its own comment) so it does **not** resolve through the `tools/` directory symlink — so both roots host the same file and `__file__` preserves whichever path you typed.

**The simpler, safer option the handoff ignored.** This tool is a **one-off non-conformer**. Twenty-plus tools use the codebase's canonical resolver — `check_meta_registry.py:43`: `from check_doc_metadata import ENGINE  # the one engine-root SSoT`, including `check_node_ctx_partition.py`, `check_identifier_retirement.py`, `check_struct_alignment.py`, `check_cache_layout.py`, `cascade.py`. Swapping `REPO_ROOT = SCRIPT_DIR.parent` for the shared `ENGINE` import is a **one-line structural fix that deletes the landmine permanently**. Recording a per-invocation ritual in a handoff is the weakest available fix — the handoff expires, the tool does not (`feedback_structural_fix_for_recurring_class` · M7 · `feedback_guards_compound_enforcement_is_leverage`). Also: `tools/check_capture_audit.py` uses cwd-relative resolution and may carry a related exposure — worth an `M9` enumeration rather than a second single-tool gotcha line.

---

## "Does it honestly reflect the hand-rolled close?" · **PARTIALLY — `c46b58f` closed most of this while I was auditing**

**Before `c46b58f`** the answer was a flat no: the addendum had no capture ledger, and the only one in the document was the fully-green 08-14 table at `:241-253` (nine ✅ plus *"Independent review ✅ **PAID this session**"*), sitting under a supersession banner that added no caveat. It read as a clean ritual.

**After `c46b58f`** the honesty is genuinely good: `:57-58` states *"this close was hand-rolled up to the point the operator asked for the skill"*, `:66-69` records the M7 escalation as `TECH_DEBT-278`, and `:70-74` corrects the registry-coverage spec **downward** ("Application 3's tool was never built … counted a phantom"). That is real and I concede it.

Three residual problems:

### HIGH-7 (residual) — the superseded all-green ledger still stands, unqualified
`:241-253` remains in the document with `Check 4 findings → ledger | ✅ **NO new TECH_DEBT**` and `Independent review | ✅ **PAID this session**`. It is now *two* sessions stale and describes a different session, three of whose statements are now false in this one (three TECH_DEBT opened; capture was not complete — `64216ed` found six missing reference docs 18 minutes after the handoff was written). Two capture ledgers in one document, both formatted identically, one all-green and wrong. It needs a one-line "**this table describes the 2026-08-14 session**" header, nothing more.

### MED-9 — the guard that certifies this is vacuously green (Class 51)
`python3 tools/check_handoff_capture_completeness.py` → **PASS** — *"has a substantive Capture-completeness section"*. It matched the **superseded 08-14 table**. Existence-only, session-blind. This is the exact mechanism by which the hand-rolled close stayed invisible: the mechanical half green, the judgment half unasked — the "inverted felt-need" your own `:88-90` names. The guard should key on the ledger being *current to the session*, not merely present. Class 51 at the surface built to prevent Class 51.

### MED-10 — a forward promise with no content
`:92-93` *"a v-class deliverable-completeness pass and an a-class default-REFUTED attack on this handoff both ran. **Verdicts recorded at the end of this section.**"* — `:95` is `### Gotchas`. There is no verdict text. Past-tense "both ran" + "recorded" for content that does not exist. `tools/check_forward_promise_audit.py` runs clean here (11 unrelated MED/LOW findings, none on this file), so **no tool catches it**. Fair as an in-flight placeholder — the commit body correctly holds the push — but if this were pushed as-is it is a phantom citation of the exact kind `:70-74` just corrected in the DESIGN_SPECS file.

---

## The cascade / anti-pattern I found

**One pattern generates HIGH-2, HIGH-3, HIGH-4, HIGH-5 and MED-5: supersede-by-banner without a completeness pass over what the banner orphans.** ADDENDUM-2 declares "SUPERSEDES … everything below" and then updates only the narrative. The frontmatter, the plan-body banner, the TaskList, the re-derive block, the 08-14 capture table and the decision-log STATUS are all *reachable* and all *stale*, and the supersession marker makes them look handled. The document's own `:57` diagnosis applies to itself: the mechanical half (SHAs correct, tools green) is what got swept; the judgment half (is every reachable statement still true?) is what did not.

That is **Class 58 sub-shape one — producer-side complement blindness** — reintroduced in the artifact closing the ship that codified it. The check asked *what was written*, never *what was owed*. Two of the four HIGHs (HIGH-3, HIGH-4) are literally that shape, and HIGH-4 asserts "N/A" over it.

---

## The simpler, safer alternative

Four edits, in priority order:

1. **Terminate the frontmatter's HISTORICAL scope** and delete the trailing `REMAINING =` clause (`:12`). Replace with `REMAINING = F only (close-gate: Class 58 codification + NPF_PROJECT_POISON + ship ritual) + D-421 steps 3-7.` One line; kills HIGH-2 and half of HIGH-5.
2. **Stamp the plan-body banner** — flip the two `⏳` at `subplans/…-nodestate-soa-layout.md:47-48` to `✅ LANDED` with `b777e5d`/`7267c5f`/`7240f3d`, and rewrite Check 2 (`:60`) from "N/A, none amended" to the owed-vs-written form. Kills HIGH-3 and HIGH-4. **This is the one that changes what a fresh session does.**
3. **Rewrite the NEXT ACTION honestly** (`:39-42`): "19 of 22 categories are in the P1/P2 verdict tables; **P3's three (`turnover`/`drift_history`/`sp_telemetry`) carry no category and must be assigned** — and `drift_history`'s only fitting category (`ACCEPTED_RESET`) requires the operator decision still OPEN at `:50`. **`gate_state`'s P1 verdict `UNESTABLISHED_UNTIL_FIRST_PASS` was invalidated by the NSDMI fix above — do not copy it; it is a RED category.** A parenthesized category (`RUNTIME_POINTER(file:line)`) refuses with rc 2, same code as 'registry not there'." Kills HIGH-6.
4. **Fix the tool, delete the gotcha** — swap `check_per_node_registry_integrity.py:40-42` to `from check_doc_metadata import ENGINE` like its twenty siblings, then remove `:100` entirely. Structural fix that removes a moving part rather than documenting one (`feedback_structural_fix_over_belt_and_suspenders`).

Then the MEDs: repair the anchor to a range (`:21`), name the real predicate for the memset claim (`:34`), point "both" at `SlowPathGateRegistry.hpp:196/:208` (`:34`), header the 08-14 capture table as historical (`:241`), swap MEMORY.md→CLAUDE.md in the OPEN item (`:52`), add TECH_DEBT-274/-276/-277 to OPEN, and repair the decision log's three staleness items plus the `+splitter` placeholder.

---

## What I ran and could not break

Stated because a bare pass is less useful than a named attack:

- **All 13 SHAs** resolved against both repos with matching subjects and dates — no fabricated or transposed anchor. The single most likely failure mode for a document like this, and it is clean.
- **`--selftest` teeth = 17**, all fire, count matches `:46` exactly.
- **The rc-2 refusal claim** — reproduced verbatim, and the refusal message is genuinely well-designed (it explains *why* an absent exemption registry cannot be computed against).
- **The `FOREACH_REGISTRY`/H15 warning** — traced to `check_meta_registry.py:131,138`, FATAL, `MemHeaders` in `SCAN_DIRS`. Correct and load-bearing.
- **"17 of 20 SHALT"** — arithmetically sound once `SHALT_OK` is counted among the 20 (`StrategyInterface.hpp:295-315`). I expected this to be off by one and it is not; only the adjacent "every other" phrasing is.
- **"Blind window is 4 closed ML trades, not 256"** — `ConfidenceScore.hpp:1397` `if (dh->count < 5) return 0;` and `:1410` `if (n < 5) return 0;`. Correct.
- **F-096 / item E** — genuinely done, and done in the *right* form: `Async.hpp:921/:925` uses the remainder form, and `:917`'s `⚠ NEVER rewrite leg B as Money_Mul(intended, Money_Sub(one, pct))` is a good comment that will stop the next person.
- **`FOREACH_OMS_PER_SLOT_FIELD` = 5**, `NPF_PROJECT_POISON` genuinely absent, Class 58 genuinely uncodified — three "still remaining" claims that are accurate.
- **Gotchas 1–3** — I tried to break all three and could not.

---

## Verdict table

| # | Attack | Verdict |
|---|---|---|
| 1 | Claims false at HEAD | **PARTIALLY REFUTED** — SHAs clean; HIGH-1 anchor, MED-1 evidence descriptor, MED-2 antecedent, LOW-1 quantifier |
| 2 | Internal contradiction | **REFUTED** — HIGH-2 frontmatter self-contradiction, MED-3 orphaned sections, MED-4 broken re-derive |
| 3 | Plan / MASTER / decision log | **REFUTED — worst line** — HIGH-3 plan body ⏳, HIGH-4 Check-2 "N/A", HIGH-5 steps 3–7 invisible, MED-5 three log staleness items |
| 4 | Volatile counts | **PARTIALLY REFUTED** — 2 need repair (`22`, `3740/0`), 2 you correctly left alone, tool blind to the new ones |
| 5 | Fresh-session literal-follow | **REFUTED** — HIGH-6 (a/b/c/d), MED-6 TECH_DEBT omissions, MED-7 wrong doc named |
| 6 | Unbounded absence claims | **PARTIALLY REFUTED** — MED-1, LOW-2, LOW-3 |
| 7 | The four gotchas | **1 of 4 REFUTED** — MED-8 misdiagnosed mechanism, falsified in both directions by probe |
| — | Rigor honesty | **PARTIALLY — `c46b58f` closed most of it**; HIGH-7 residual green table, MED-9 vacuous guard, MED-10 phantom verdict promise |

**Do not push until at least edits 1–3 land.** HIGH-3 and HIGH-4 together mean a fresh session's first instructed read tells it to redo shipped work, and the ledger entry that would have caught that declares itself not applicable. That is the artifact overstating its own rigor in the one place the overstatement has a cost.
