---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: /close-session Stage 6.5.4 — adversarial review (default-REFUTED) of the D-421 steps 2+4+5 handoff
agent_class: a-class
delivered: 2026-08-15
ground: engine HEAD 49df9d2, branch feat/v5.15-live-readiness; workspace 73c98fa→7306410 during the audit
headline: REFUTED — 3 HIGH, 4 MED, 1 LOW. The conclusions are largely right; the step-6 PROOF is unsound as written and the "what is NOT yet proven" caveat is itself the false claim — it names a registry deleted 2026-05-24, cites a line that says something else, and re-opens as "a separate question" a CRITICAL that D-421 and the Class 58 file (same session) record as settled. A fresh session following it could RETIRE a live CRITICAL.
operator_decision_owed: none — every finding is the author's to fix; HIGH-1/2/3 + MED-4/5/6/7 remediated at ws 2e97c9a (see the handoff's Stage-6.5.4 verdict block)
sister_reports: []
---

> Saved VERBATIM at receipt per `feedback_save_agent_reports_verbatim` + SUBAGENT_ARMING § 6.5.
> The orchestrator's own verification of the three HIGH claims (all CONFIRMED by code-read per
> AR-11) and the remediation are recorded in the handoff, not here — this file is the agent's
> unedited output.

---

# A-CLASS ADVERSARIAL REVIEW — handoff `2026-08-15-E.1.2-D421-steps2-4-5-complement-guard-handoff.md`

**Verdict: REFUTED.** Three HIGH findings, four MED, one LOW. The handoff's *conclusions* are largely correct; its **step-6 proof is unsound as written and its "what is NOT yet proven" warning is itself the false claim in the document** — it names a registry that was deleted 2026-05-24, cites a line that says something else, and re-opens as "a separate question" a finding that both the D-421 decision log and the Class 58 file the same session authored record as settled CRITICAL. A fresh session following the NEXT ACTION section literally will burn a cycle on dead ends and may retire a live CRITICAL.

Target: `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/handoffs/2026-08-15-E.1.2-D421-steps2-4-5-complement-guard-handoff.md` (now committed at ws `73c98fa`; content byte-identical to the version reviewed, md5 `cfc7a4f1f51383df757a8064fb292d2c`). Engine HEAD `49df9d2` as stated. Workspace advanced to `7306410` during the audit.

---

## HIGH-1 — The step-6 caveat cites a registry that does not exist, and a line that says something else

Handoff lines 107-111:

> ⚠ **What is NOT yet proven, and do not inherit it as fact:** … The 36-field cfg-derived population rides a **different walker** (`FOREACH_STAMP_BOUND_CFG`, `ML_Headers/ModelInference.hpp:1817`) and whether those are affected is a separate question. Verify it; do not carry the number forward.

**Both halves are false at HEAD.**

`FOREACH_STAMP_BOUND_CFG` was deleted at `v5.15.5.F.4d.1.B.3` Step 2 (2026-05-24):
- `ls ML_Headers/StampBoundCfgRegistry.hpp` → *No such file or directory*
- `/home/caramel/code/FoxML_Trader_v2/Version.hpp:697` — `// - DELETED ML_Headers/StampBoundCfgRegistry.hpp (full file; FOREACH_STAMP_BOUND_CFG body + STAMP_CFG_AUTOPOPULATE + FOREACH_STAMP_BOUND_CFG_COUNT)`
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/MetaRegistry.hpp:82` — the `FOREACH_REGISTRY` row is a tombstone comment: `FOREACH_STAMP_BOUND_CFG row DELETED at .B.3`
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ModelInference.hpp:46` — the `#include` removal note, naming `cfg_derived::populate_stamp_cfg_from_derived<F>` as the successor

`ML_Headers/ModelInference.hpp:1817` is `r.valid = 0;` — inside the format-version-mismatch early return (`:1816-1821`), not any walker.

**Where the stale cite came from — this is AR-17, committed inside the document that codifies AR-17.** `/home/caramel/code/FoxML_Trader_v2/ML_Headers/StampHelper.hpp:229` carries the exact string:

```
    // ... wire key emission at
    // ModelInference.hpp:1817 FOREACH_STAMP_BOUND_CFG walker — REQUIRED at
    // Step 1.5 (Phase F trio NOT YET LANDED; legacy walker still active ...
    // ... Removed at Step 2 when legacy POST_CFG entry + prefixed struct field deleted atomically.
```

That comment describes a pre-Step-2 state that no longer exists. The handoff inherited it verbatim rather than resolving it — the precise failure its own Meta-harvest (line 178-181) claims to have newly caught. `StampHelper.hpp:229` is itself an owed stale-comment fix.

**The real walker, and the real answer.** The 36 cfg-derived fields are walked by `FOREACH_STAMP_BOUND_DERIVED_COHORT`, `/home/caramel/code/FoxML_Trader_v2/MemHeaders/CfgGateRegistry.hpp:285-289`. Their drift check is `cfg_derived::drift_check_from_derived` at `MemHeaders/CfgGateRegistry.hpp:517`. Its gate is a `bool stamp_has_inference_cfg` parameter:

- `MemHeaders/CfgGateRegistry.hpp:197` and `:205` — `default: return stamp_has_inference_cfg;`
- `MemHeaders/CfgGateRegistry.hpp:194` and `:202` — `return stamp_has_inference_cfg && (expr);`
- `MemHeaders/CfgGateRegistry.hpp:568` and `:588` — `const bool _trigger = stamp_has_inference_cfg & _drifted;`

And the macro that supplies it:

- `MemHeaders/CfgGateRegistry.hpp:813` — `STAMP_HAS((handle), inference_cfg),`
- caller: `ML_Headers/NodeModelZoo.hpp:304` — `DRIFT_CHECK_FROM_DERIVED(failure_flags, sr, cfg, …)`

**It is the same bit.** Not a different walker, not a separate question.

The mechanism is sharper than either document states, and I verified it end-to-end: the derived cohort records presence in **per-field `has_<name>` bytes**, never in the `has_flags` bitmap —
- populate: `MemHeaders/CfgGateRegistry.hpp:365` — `tt::cfg_populate_inf_field(cfg.name, inf.name, inf.has_##name, _gate);`
- parse: `MemHeaders/CfgGateRegistry.hpp:643` — `r.has_##name = 1;`

— while the drift gate reads the `inference_cfg` **group bit** in `has_flags` that no derived-path writer ever touches, and never reads `handle.has_<name>` at all. All 36 are gated on a bit their own walker never sets.

**Contradicts two in-repo records:**
- `plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md:2834` (D-421 ②): *"all 36 `STAMP_BOUND_CFG_DERIVED` fields are emitted, parsed, and never compared, because the gate reads a group bit whose emit-side producer was retired at the `.B.3` prefix migration while the consumer stayed."*
- `DOCS/recurring-bug-patterns/class-58-registry-complement-blindness.md:59-62` — this is the **canonical instance of sub-shape B**, written by the same session.

**Blast radius of the error.** A reader who follows "Verify it; do not carry the number forward" finds no such walker and could reasonably conclude the 36-field claim was an artifact — retiring a CRITICAL that is real. The handoff's caveat inverts the correct disposition.

**Correction:** replace lines 107-111 with —

> ⚠ **Already answered, and it is the SAME bit — not a separate question.** The 36 `STAMP_BOUND_CFG_DERIVED` fields are walked by `FOREACH_STAMP_BOUND_DERIVED_COHORT` (`MemHeaders/CfgGateRegistry.hpp:285`); their drift check is `cfg_derived::drift_check_from_derived` (`:517`), gated on `stamp_has_inference_cfg` (`:194/:197/:202/:205/:568/:588`), which the macro at `:813` supplies as `STAMP_HAS((handle), inference_cfg)` — the identical group bit — from `ML_Headers/NodeModelZoo.hpp:304`. The cohort records presence in per-field `has_<name>` bytes (`:365`, `:643`) that the gate never reads. D-421 ② and Class 58 sub-shape B stand as written. Re-derive the 36: `grep -c "^\s*X(.*STAMP_BOUND_CFG_DERIVED"` over `CoreFrameworks/CfgFieldRegistry.hpp` (31, **minus** the one `FOREACH_METADATA_BIT` row at `:1441` = 30) + `ML_Headers/MlCfgFlagRegistry.hpp` (5) + `CoreFrameworks/GateCfgFlagRegistry.hpp` (1) = **36**. The number is right and *is* re-derivable.

---

## HIGH-2 — The closing argument's quantifiers are false, and the enumeration drops the only site that decides the proof

Handoff lines 98-101:

> **`STAMP_SET` is the ONLY writer of `has_flags` tree-wide** (verified — the sole `BITMAP_SET` on it, at `StampBoundModelConstRegistry.hpp:624`), and the only `STAMP_SET(…, inference_cfg)` sites are the parser macro above and `ML_Headers/NodeModelZoo.hpp:459` …

**Clause 1 is false.** `STAMP_SET` is the only `BITMAP_SET` on `has_flags` — that half checks out (`ML_Headers/StampBoundModelConstRegistry.hpp:624` is the sole non-comment hit tree-wide). But "the only **writer**" is a different and false claim. Whole-struct writes:
- `ML_Headers/ModelInference.hpp:542` — `*m = ModelHandle<F>{};` inside `Model_Init`, whose own comment at `:535` reads *"Zero-init correctly clears: — has_flags (all 13+ stamp-derived bit positions)"*
- `ML_Headers/StampHelper.hpp:185` — `StampInferenceCfgInputs inf = {};`
- `ML_Headers/NodeModelZoo.hpp:265` — `ModelStampResult sr = {};`
- `ML_Headers/NodeModelZoo.hpp:2408` — `ModelStampResult sr = verify_model_stamp(…);` (whole-struct copy-init)

All are clearers/propagators, so the conclusion survives — but the sentence is presented as *verified* and is not.

**Clause 2 is false, and the omission is the load-bearing one.** The complete set of `STAMP_SET(…, inference_cfg)` sites is **five**, not two:

| # | Site | Named by handoff? |
|---|---|---|
| 1 | `ML_Headers/StampBoundModelConstRegistry.hpp:715` — `STAMP_AUTOPOPULATE_SET_HAS_inference_cfg(name) → STAMP_SET((inf), inference_cfg)` | **NO** |
| 2 | `ML_Headers/StampBoundModelConstRegistry.hpp:747` — parser dispatcher | yes |
| 3 | `ML_Headers/NodeModelZoo.hpp:459` — the circular handle copy | yes |
| 4 | `tests/controller_test.cpp:15572` | **NO** |
| 5 | `tests/controller_test.cpp:15646` | **NO** |

Site 1 is the **only emit-side producer** — the single site whose reachability decides the entire loop. The proof holds *only* because its parent `STAMP_MODEL_CONST_AUTOPOPULATE` is quarantined behind `static_assert(false, …)` at `ML_Headers/StampBoundModelConstRegistry.hpp:677-682` (PARITY-022). The handoff never mentions the site or the quarantine, so a reader cannot tell whether the author saw it and ruled it out or never saw it. That is the M9 failure (`feedback_enumerate_set_before_categorical_claim`) inside a step-6 proof.

**This is a regression against the record it supersedes.** The D-421 STATUS block at `decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md:2834` already enumerates **three**: *"the only three `STAMP_SET(…, inference_cfg)` sites are the parser macro, a quarantined dispatcher, and one circular site gated on `STAMP_HAS` of the same bit."* The handoff drops one of the three the log already had.

**Correction:** state all five, name the quarantine at `:677-682` as the reason site 1 is inert, and drop "ONLY writer of `has_flags`" for the accurate "the only *setter* is `STAMP_SET`; the other writers (`Model_Init` at `ModelInference.hpp:542`, the three `= {}` / copy-init sites) can only clear or propagate."

---

## HIGH-3 — Two test fixtures hand-set the group bit; the suite green-lights a chain production cannot enter

`tests/controller_test.cpp:15572` and `:15646` both do `STAMP_SET(inf, inference_cfg);` by hand, then call `stamp_write_for_model(...)` → `verify_model_stamp(...)` and assert on `STAMP_HAS(...)`. The comment immediately above the first, at `tests/controller_test.cpp:15568-15569`, reads:

```
                // ↓ This block IS the v5.9.5b wiring (mirrors
                //   Backtest_RunFullValidation):
```

**That claim is stale and load-bearing.** Production emits via `Backtest/BacktestEngine.hpp:1440` and `Backtest/BacktestPanels.hpp:4047` → `tt::Stamp_AssembleAndEmit` (`ML_Headers/StampHelper.hpp:179-414`), whose `inf` is built at `:185` and populated by `INFERENCE_CFG_POPULATE_FROM_DERIVED` (`:198`) plus **16** explicit `STAMP_SET(inf, …)` calls (`:236`-`:352`) — **none** of which is the bare group bit. The test no longer mirrors production; it manufactures the precondition production stopped producing at `.B.3` Step 1.6.5 (`StampHelper.hpp:196`).

Three consequences the handoff should carry, none of which it does:
1. **"the bit can never be 1" is false even tree-wide**, since the tests are in the tree.
2. **This is why the vacuity survived a whole release train** — the emit→parse→gate chain is exercised, so nothing looked dead. That is Class 51 (vacuously-green guard) crossed with Class 12 (wired-but-unexercised), and it belongs in the Class 58 sub-shape B detection signature: *a gate whose only producer is a test fixture*.
3. **It will bite the step-6 FIX.** Whoever fixes the gate and writes "does drift fire now?" against these fixtures gets a green for the wrong reason. Flag `:15572` / `:15646` as must-touch in the step-6 arming.

---

## MED-4 — "the bit can never be 1" is unsound: the PARSE leg's input is an external persisted file

The handoff's own PARSE row (line 95) says *"sets only if a key was read"*. Whether a key was read is not a property of this tree. The argument reasons over in-tree writers and silently treats an external artifact as if the current binary controlled it — an H21 blind spot in an H21-aware document.

**Empirically, group keys exist on disk right now:**

```
$ grep -h "inference_cfg" models/classification/*/barrier.json.stamp | sort -u
inference_cfg_barrier_blend_mode=0
inference_cfg_ml_sl_pct=0
inference_cfg_ml_tp_pct=0
inference_cfg_per_horizon_barrier_blend=0
...
```

All four are `inference_cfg`-group rows (`ML_Headers/StampBoundModelConstRegistry.hpp:460-471`) — so a stamp file that sets the bit at parse demonstrably exists.

They are neutralized by a **second, unstated** mechanism: all 16 on-disk stamps are `stamp_format_version=1`, below `STAMP_FORMAT_VERSION_EPOCH_FLOOR = 3` (`ML_Headers/ModelInference.hpp:166`), so they hard-refuse at `:1805-1812` → `sr.valid = 0` → the drift block at `ML_Headers/NodeModelZoo.hpp:294` (`if (cfg_ptr && sr.valid > 0)`) is skipped.

**Correction:** the sound claim is *"unreachable given (a) no production emit path sets the group bit — the only producer is quarantined at `StampBoundModelConstRegistry.hpp:677`, and (b) every group-key-bearing stamp on disk is pre-epoch and hard-refused at `ModelInference.hpp:1805`."* Leg (b) is a data + epoch-floor fact, not a code invariant — a hand-authored or branch-emitted **v3** stamp carrying `inference_cfg_ml_tp_pct=` would set the bit and pass the floor. Say that, because the step-6 generic checker must model it.

**Simpler/safer alternative the handoff ignored.** "Prove no writer exists tree-wide" is an unbounded negative over the tree *plus* an uncontrolled external format; it cannot be mechanized and it produced three misses in one paragraph. The positive formulation is bounded and checkable: enumerate (1) the writer set of `inf.has_flags` reachable from the two production emit call sites (`BacktestEngine.hpp:1440`, `BacktestPanels.hpp:4047`) — a closed 16-element list in `StampHelper.hpp:236-352`; and (2) the group's 9 wire keys (`StampBoundModelConstRegistry.hpp:460-489`) crossed with the epoch floor. **That producer-set-vs-consumer-set-per-gate-bit shape is what the step-6 generic checker should be**, and it is exactly the Class 58 detection signature already written at `class-58-registry-complement-blindness.md:93-95`.

---

## MED-5 — The re-derive command over-counts, via the exact defect D-421 step 0 fixed

Handoff line 102-103: *"Re-derive the gated row count with `grep -c "STAMP_HAS(\*h, inference_cfg)" ML_Headers/CfgDriftCheckRegistry.hpp`."*

Run verbatim it returns **5**. The gated rows are **4** — `ML_Headers/CfgDriftCheckRegistry.hpp:257`, `:261`, `:266`, `:332`. The 5th match is a prose line:

```
CfgDriftCheckRegistry.hpp:309:     /* For the 4 .A.7 entries, gate_when uses STAMP_HAS(*h, inference_cfg) — the existing  */
```

This is the no-comment-stripping fabrication D-421 **step 0** was written to kill (decision log `:2834`: *"no comment-stripping in the H21 consumer (a doc block could fabricate a row)"*). The handoff reintroduces it as an authoritative re-derive — an anti-pattern recurrence inside the arc that closed it.

**Correction:** `grep -c "^\s*STAMP_HAS(\*h, inference_cfg)," ML_Headers/CfgDriftCheckRegistry.hpp` → 4, or state "4 rows at `:257/:261/:266/:332`" per `feedback_name_members_never_tallies_in_docs`.

Also note: the CONSUME row (line 96) is file-level only and names just this walker. There are **two** consumers of the bit — this one (walked at `CoreFrameworks/ModelValidation.hpp:222`, 4 rows) and `drift_check_from_derived` (36 fields). Naming one made the second look like a separate question.

---

## MED-6 — "every `FOREACH_REGISTRY` row declares…" over-claims what landed

Handoff line 69-71: *"**Step 5 — the DOMAIN column** … every `FOREACH_REGISTRY` row declares what its rows are the complete set of."*

At HEAD:

```
[meta-registry-CI] Check 4 PASS: DOMAIN declared + well-formed across 69 rows (4 declared, 65 baselined-pending).
```

4 of 69. The commit message for `4abfd43` says "69 rows, 3 classified". `tools/lib/meta_registry_domain_baseline.txt` is 83 lines. The handoff *does* disclose the baseline further down (line 119), so a careful reader reconciles — but the headline sentence states the end state as the landed state.

Sharpest form of this finding: the author already caught the precision issue in the **tool** — ws commit `f0cf754` is titled *"fix(E.1.2 D-421): Check 4 says DECLARED not 'classified'"* — and left the over-claim standing in the handoff prose. Same session, same distinction, one surface fixed and one not.

**Correction:** *"every `FOREACH_REGISTRY` row must now declare a well-formed domain or sit on the shrinking baseline; 4 of 69 declared at close, 65 baselined-pending. Check 4 validates the DECLARATION, not coverage."*

---

## MED-7 — The option-(d) leaf's site list is incomplete: there is no `warming` source bit, and three hand-maintained counts go stale

Handoff line 77-81. **The zero-wire half is CORRECT and I confirm it** (see verified list below). The **site list** is not.

1. **No source bit exists.** `drift_state_flags` carries exactly two masks — `ML_Headers/ConfidenceScore.hpp:1234` (`MASK_DRIFT_BREACHED`) and `:1235` (`MASK_DRIFT_KILL_TRIPPED`). `CoreFrameworks/ShardedSnapshot.hpp:525` (the cited "existing projection") reads `MASK_DRIFT_BREACHED`. A `DRIFT_WARMING` display bit has **nothing to project from**: it needs either a third `drift_state_flags` bit (a `ConfidenceScore.hpp` change with its own writer) or a derivation from the sample count (`ConfidenceScore.hpp:1397/:1410`, the `>= 5` thresholds the exemption rationale cites). Calling it "the existing projection" understates the leaf by a whole producer.

2. **Three hand-maintained counts falsified by the "one row":**
   - `MemHeaders/PerNodeStateFlagsRegistry.hpp:10` — `[OVERVIEW]_[PerNodeSnap uint16_t state_flags SSoT — 11 pure BIT_FLAG observability rows …]`
   - `MemHeaders/PerNodeStateFlagsRegistry.hpp:68` — `[OVERVIEW]_[11 BIT_FLAG rows -> … 5 bits headroom (overflow assert at 16)]`
   - `DataStream/EngineTUI.hpp:1259` — `uint16_t state_flags;                // BIT_FLAG entries (11 of 16 used)`

   All three are accurate today (I counted 11 rows at `PerNodeStateFlagsRegistry.hpp:75-107`) and all three become false on the row-add. Leaving them is the derived-fact drift the whole D-421 arc exists to kill.

3. **Headroom is fine** — `static_assert(PER_NODE_STATE_FLAG_COUNT <= 16, …)` at `MemHeaders/PerNodeStateFlagsRegistry.hpp:126`; 11 → 12 leaves 4.

**Correction:** the leaf is ≥6 sites, not 3 — the source bit / derivation, the registry row, the 3 count comments, a NEW projection block at `ShardedSnapshot.hpp:~525`, the panel string.

---

## LOW-8 — Check Q's trigger set rests on an unstated precondition

Handoff lines 56-59 describe Check Q's trigger as keying on "the STRUCT's home … as well as the registries". Verified: `.githooks/pre-commit:527` matches exactly `CoreFrameworks/ControllerEventLoop.hpp`, `MemHeaders/NodeCtxPersistRegistry.hpp`, `MemHeaders/NodeCtxInitRegistry.hpp`; `struct alignas(64) NodeContext` is at `CoreFrameworks/ControllerEventLoop.hpp:315`.

The implicit completeness claim is *"every way a member can join `NodeContext` touches one of these three files."* True today because the body is hand-declared. It stops being true the moment any member arrives via an X-macro defined elsewhere — which is the direction H17 pushes struct bodies codebase-wide. Worth recording as a stated precondition on the guard rather than an assumption, since a silently-skipped Check Q reads identically to a passing one (Class 51).

---

## Verified TRUE — so the coverage is auditable

Everything below I resolved against HEAD `49df9d2` and it holds:

- **Cites that resolve correctly:** `ML_Headers/StampBoundModelConstRegistry.hpp:730` (`STAMP_EMIT_CHECK_HAS_inference_cfg`), `:747` (`STAMP_PARSER_SET_HAS_inference_cfg`), `:624` (`STAMP_SET` → `BITMAP_SET`); `ML_Headers/NodeModelZoo.hpp:458` (`if (STAMP_HAS(sr, inference_cfg)) {`) and `:459` (`STAMP_SET(*handle, inference_cfg);`); `CoreFrameworks/ShardedSnapshot.hpp:525` (the `MASK_DRIFT_BREACHED` projection).
- **`FOREACH_PER_NODE_STATE_FLAG` is display-only — the "verified zero-wire" claim CHECKS OUT.** It feeds `PerNodeSnap.state_flags` (`DataStream/EngineTUI.hpp:1259`, `uint16_t`), a wholly different registry from `NodeStateFlagRegistry.hpp` → `NodeContext.node_state_flags` (`CoreFrameworks/ControllerEventLoop.hpp:375`, `uint8_t`), which is the persisted one. Only the latter is H21-ledgered (`tools/identifier_ledger.txt:13-18`, `NODE_STATE_FLAG_*`); `STATE_FLAG_*` appears nowhere in the ledger. No `fwrite`/HMAC/`memcmp` path over `PerNodeSnap` found. `DRIFT_BREACHED`/`DRIFT_KILL_TRIPPED` siblings exist at `PerNodeStateFlagsRegistry.hpp:102`/`:104` — the canonical-sister framing is right.
- **Check Q live-fired on `49df9d2`** — that commit touches `MemHeaders/NodeCtxPersistRegistry.hpp`, which is in the trigger regex at `.githooks/pre-commit:527`.
- **Two HARD rows in `check_session_docs`** — both present (`node-ctx-partition` + `node-ctx-partition teeth`).
- **Every re-derive command runs clean from the engine root:** `check_session_docs.sh` → `SWEEP CLEAN` rc 0 · `check_node_ctx_partition.py` → `GREEN — all 49 tt::NodeContext<64> members accounted: 27 persisted, 22 declared-exempt` rc 0 · `--selftest` → `ALL TEETH FIRE` rc 0 · `check_meta_registry.py` → Checks 1-4 PASS rc 0 · `node_persist_layout.py` → `GREEN — 46 flattened wire rows` rc 0 · `check_identifier_retirement.py` → `GREEN — 48 persisted/wire identifiers` rc 0 · `check_always_loaded_budget.py` → rc 0 with `⚠️ CLAUDE.md 36,750 / 40,000 B (92%)`, matching the handoff's ⚠ NEAR.
- **`git -C ~/code/tick-trader-percore-workspace log 8e2473b..HEAD --oneline` works**; `8e2473b` is a valid ancestor.
- **Class 58 sister cohort claim is exact** — ws `83b54eb` touches `class-04` / `class-12` / `class-30` at 2 lines each (frontmatter) and `class-51` at 12 (prose). Matches "Classes 4, 12, 30 frontmatter; 51 a prose section" verbatim.
- **Ledger claims hold** — TECH_DEBT-196 and -167 are `status: closed` in `DOCS/tech-debt/closed.md:1608`/`:1620`; TECH_DEBT-172 is `status: open` at `open.md:3020` (correctly "not closed"); TECH_DEBT-274 stays open with the ⏩ TRIGGER FIRED block at `open.md:3888` and the `STRUCT:` subset blocker at `:3890` — the handoff's summary of it is faithful; TECH_DEBT-282 exists at `open.md:4024` with no reserved Mn number, as described; TD-249↔TD-282 are bidirectionally linked (`open.md:3605` ↔ `:4033`).
- **Memory `project_remote_push_needs_operator_password.md` exists** under `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/`.
- **WILL-BITE #2 is TRUE and worth keeping:** `tools/check_close_out_completeness.py:381` sets `repo = WORKSPACE`, and `_commit_count` (`:302-309`) returns `0` on `ValueError`, so an unresolvable engine SHA makes `run()` print *"no commits … nothing to check"* and return 0 — a silent pass having checked nothing, exactly as the handoff says.
- **"36" is correct and re-derivable** — 30 (`CoreFrameworks/CfgFieldRegistry.hpp`, 31 grep hits minus the `FOREACH_METADATA_BIT` row at `:1441`) + 5 (`ML_Headers/MlCfgFlagRegistry.hpp`) + 1 (`CoreFrameworks/GateCfgFlagRegistry.hpp:45`, `BARRIER_GATE_ENABLED`). The handoff's "do not carry the number forward" was defensible caution; the number itself is fine.
- **`FOREACH_CFG_DRIFT_CHECK` is live**, walked at `CoreFrameworks/ModelValidation.hpp:222` — the CONSUME leg is a real consumer, just not the only one.

## NOT verified — stated so the gap is visible

- **`./build.sh test` was NOT run.** I am read-only, and Landmine 18 (concurrent-build truncation) makes an unsanctioned build actively unsafe. The handoff's *"expect BUILD 0 + suite green"* and *"Suite was green and UNCHANGED at every commit of this arc"* are unverified by me. Circumstantially consistent: `node_persist_layout.py` is GREEN vs golden and `check_identifier_retirement.py` is GREEN, so the "touches no bytes" half holds.

---

## Cascade / anti-pattern summary

| Cascade | Where |
|---|---|
| **AR-17 (inherited stale `file:line` consumed into durable content)** — committed in the document that codifies AR-17 | handoff `:110` ← `ML_Headers/StampHelper.hpp:229` |
| **D-421 step-0 defect reintroduced** (grep without comment-stripping presented as an authoritative re-derive) | handoff `:103` vs `CfgDriftCheckRegistry.hpp:309` |
| **M9 / `feedback_enumerate_set_before_categorical_claim`** — unenumerated "ONLY"/"never", dropping the one site that decides the proof | handoff `:98-101` |
| **Class 51 + Class 12 hybrid, undocumented** — the only producers of the dead gate bit are two test fixtures, which is why the vacuity survived | `tests/controller_test.cpp:15572`, `:15646` |
| **Class 58 sub-shape B regression** — a settled CRITICAL re-opened as "a separate question" against the class file the same session wrote | handoff `:107-111` vs `class-58-…md:59-62` + D-421 `:2834` |
| **Derived-fact drift queued into a leaf** — 3 hand-maintained counts the "one row" falsifies | `PerNodeStateFlagsRegistry.hpp:10`, `:68`, `EngineTUI.hpp:1259` |

**Shape/seam verdict (re-cascade signal):** the step-6 **ordering and deliverable are sound** — build the generic gate-reachability check first, choose the drift-gate fix after. Do not re-litigate that; D-421 settled it. What is materially wrong is the **investigative pointer**, and it points 180° away from the answer. Fix the caveat paragraph before a fresh session reads it, and add `tests/controller_test.cpp:15572`/`:15646` plus the quarantine at `StampBoundModelConstRegistry.hpp:677` to the step-6 arming — without them the fix will be verified by a test that manufactures its own precondition.
