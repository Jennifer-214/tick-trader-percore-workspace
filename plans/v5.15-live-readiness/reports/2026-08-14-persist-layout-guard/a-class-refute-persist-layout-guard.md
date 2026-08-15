---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: adversarially refute the E.1.2 persist-layout guard (node_persist_layout.py + paired-bump + wiring) before commit
agent_class: a-class
delivered: 2026-08-14 (AR-8 independent review of the mid-session guard build)
consumed_by: the pre-commit punch-list (items applied same session; see orchestrator postscript)
---

# A-CLASS ADVERSARIAL VERDICT — E.1.2 persist-layout guard (`node_persist_layout.py` + paired-bump + wiring)

**Audit basis:** working tree at 2026-08-14 ~17:30 (uncommitted, workspace repo `tick-trader-percore-workspace`; engine `tools/` is a symlink). Mid-audit the builder renamed the wrapper `check_node_persist_layout_selftest.sh` → `node_persist_layout_selftest.sh` and updated `tools/check_session_docs.sh:141` to match (witnessed; renamed wrapper re-verified rc 0 from both repo paths). All other audited files unchanged across the audit (mtimes 17:14–17:16). Every claim below was **executed**, not read — repro scripts live in the session scratchpad (`refute_battery.py`, `pb_controls.py`, `tooth_proxy.py`, `final_probes.py`).

**Overall: NOT REFUTED as a ship — the D-302/A-PASS core contract holds against executing code — but 2 MUST-FIX items block the commit as-is (one is a live rc=2 RED in a sibling guard), plus 2 demonstrated latent parse-vacuity modes, 1 Class-51-C tooth, and 1 refuted docstring claim.**

## Design-contract conformance (the locked A-PASS spec, `plans/v5.15-live-readiness/plan_checks/2026-07-04-E.1.2-phaseC-step2-iclass-ground-truth.md:189-231`)

| Contract property | Verdict | Evidence |
|---|---|---|
| name-INCLUSIVE (Money→Money name swap REDs) | **HOLDS** | selftest tooth `node_persist_layout.py:329-331` + my paired-bump control A: planted `node_dd_pct`→`partner_pending_pnl` swap → VIOLATION |
| walk-INTO delegates (sub-row drop REDs) | **HOLDS** | tooth `:349-351`; real-tree 17 sub-rows verified vs `Strategies/RegimeDetector.hpp:638-645`, `ML_Headers/LinearRegression3X.hpp:102-105`, `ML_Headers/ConfidenceScore.hpp:1415-1422` |
| order-sensitive | **HOLDS** | membership-identical reorder always fires (index-prefix construction `:196-210` + demo); mixed drop+reorder fires DROPPED+REORDERED |
| paired-bump forces version+golden same-commit | **HOLDS on the tool paths** (controls A–E all fire, incl. refusal→violation and None==None→violation) — **defeated by one shell redirect** (R3-d below) | `check_identifier_retirement.py:260-307`; `pb_controls.py` output |
| REFUSAL never a pass | **HOLDS in code** (rc 2 verified via `FOXML_ENGINE` stub; malformed row / unknown kind / malformed golden all REFUSE loudly) — **one identified path to silent-WRONG instead of refusal** (R1-a) | `node_persist_layout.py:390-394`, probes |

---

## Lane verdicts

### R1 — Parse blindness: **WEAKNESS ×2 (real, demonstrated, latent), rest HOLDS**

**R1-a — comment-hijack of `_macro_body` = latent Class-51-B″ (wrong-region scan). REAL, repro'd, not live today.**
`_macro_body` (`tools/node_persist_layout.py:81-91`) `re.search`es the **raw** file text; `_strip_comments` (`:131-134`) runs only on the *extracted body* (`:176`). A comment containing the verbatim `#define FOREACH_NODE_PERSIST_FIELD(X) ...` above the real define hijacks the parse. Demonstrated: a `/* ... #define FOREACH_TEST_PERSIST_FIELD(X) X(fake_row,...) ... */` block yields a listing of `fake_row` only — the real registry is never read, **no refusal**. Kill-shot shape: a doc block quoting the FULL OLD macro (exactly what the E.1.2.A `[CODE]`-quoting doc culture might produce) → the parser reads the stale copy forever → **every subsequent registry edit diffs GREEN = permanent vacuity**. Today's `MemHeaders/NodeCtxPersistRegistry.hpp` mentions the macro name in doc lines (`:12,:42,:46`) but never with a `#define` prefix — so dormant, not live. The prefix-macro direction is SAFE (demonstrated: `#define FOREACH_TEST_PERSIST_FIELD_COUNT(X)` and a glued-suffix variant are correctly skipped; the real `FOREACH_NODE_PERSIST_FIELD_COUNT` is a `constexpr`, `NodeCtxPersistRegistry.hpp:115`, unmatchable anyway). **Fix:** newline-preserving comment-strip of the whole text before the `#define` search.

**R1-c — sub-registry lax arity = silent count-token drop under a future 2-param template. REAL, repro'd, latent.**
`_parse_sub` accepts `len(a) < 3`-only (`:159`); `_args` (`:115-128`) respects parens, **not angle brackets**. `X(inner_two, Pair<A,B>, 4)` parses as 4 args → recorded as `(inner_two, "Pair<A", "B>")` — the count token **4 is dropped from the listing**; mutating it 4→8 (wire size change) = **EMPTY DIFF, GREEN** (demonstrated). The parent is protected by exact arity (`len(a) != 5` → REFUSAL, demonstrated with the same `Pair<A,B>`). No current sub-row has a comma-bearing type (`FPN_Binary<F>` is single-param) — future-facing. **Fix:** `len(a) != 3` → `LayoutRefusal` (symmetry with the parent).

HOLDS: multi-line row mid-tuple → REFUSAL (safe; message mildly misleading — "unknown STORAGE_KIND `\ SCALAR`"); trailing `/* */` on a row line → clean; `//`-with-backslash C-splice divergence is bounded by the compile-time count-lock (`NodeCtxPersistRegistry.hpp:119` — a C-side truncation always drops rows → build RED); last-row-no-backslash → works (the live registry proves it).

### R2 — Diff blindness: **WEAKNESS (mislabel), rest HOLDS**

- **Duplicate row name → RED but mislabeled.** `_data_rows` (`:220-233`) dict-collapses duplicate paths with no refusal; a duplicated row (wire GROWS) reports as `REORDERED alpha @000 -> @007` (demonstrated) — red fires, diagnosis lies. Unreachable through compiling code for the real registry (duplicate struct-field names don't compile), so LOW — but `_data_rows` refusing on a duplicate path is a 3-line honesty fix and also hardens against a hand-mangled golden.
- Names swapping between two rows → `CHANGED` both + `REORDERED` both (demonstrated). Pure reorder can never be suppressed when membership is identical (index-prefix argument + demo). The `f" {p} "` dedup substring guard (`:259`) is not practically spoofable by current name/type vocabulary. Whitespace realignment → no false positives (args stripped). Sub count-token rename → `CHANGED` (demonstrated). SCALAR mask column invisible (0→7 GREEN, demonstrated) — benign-by-construction: all three SCALAR projections ignore `SMASK` (`NodeCtxPersistRegistry.hpp:155-156,179-180,195`). Nit only.

### R3 — Paired-bump bypass: **1 REFUTED docstring claim + 1 confirmed overclaim; architecture seams honestly declared and compensated**

- **(b) REFUTED claim:** docstring `node_persist_layout.py:33-35` — *"a size-relevant change ALWAYS changes a type or count TOKEN"* — is **false**. Changing `#define ROLLING_IC_MAX_WINDOW 64` (`ML_Headers/ConfidenceScore.hpp:84`; sibling `MAX_WINDOW 8` at `ML_Headers/LinearRegression3X.hpp:34`) changes wire size (3 arrays × 8B × delta) with the listing token verbatim-unchanged → **GREEN at Check H, no version-bump forcing at commit time**. No compile-time size pin exists (1944 appears only in comments — `CoreFrameworks/ShardedSnapshotPersist.hpp:193` + the registry `[OVERVIEW]`). The catcher is the runtime byte-golden `memcmp` (`tests/controller_test.cpp:6380-6383`) at `./build.sh test` — which pre-commit does not run. **Structural close available with existing machinery:** enroll both count tokens as `SOURCES` rows in `check_identifier_retirement.py:82-107` (a value change then REDs at Check H as a renumber, TTY-gated `--update` to accept) + correct the docstring.
- **(d) Confirmed overclaim — "a delegated agent is structurally unable to re-bless a red away" (`node_persist_layout.py:36-39`; same claim `bless.py:45-48`).** `--print` output is **byte-identical to the golden** (demonstrated: `diff` rc 0), so `node_persist_layout.py --print > tools/goldens/node_persist_layout.txt` is a complete non-TTY re-bless; with a registry edit in the same working tree, Check H is GREEN with no bump (control F). D-394 gates the *tool's write path*, not the *file*. What DOES hold (verified): the symmetric direction — a golden edited toward a future state with the live registry unchanged REDs at Check H; both repos share ONE hook (`FoxML_Trader_v2/.githooks` → workspace symlink; workspace `core.hooksPath=.githooks` confirmed), and the trigger regex (`.githooks/pre-commit:406`) covers workspace-side staged `tools/node_persist_layout.py` + the golden. **Fix = honesty, not mechanism:** soften the claim (here, in `bless.py`, and in `DOCS/TOOLS.md:62/69`) — the actual controls are the TTY-gated tool paths + golden-diff visibility at workspace commit + the symmetric red. Teaching future agents a false structural invariant is itself a hazard.
- (a) Projection-macro edits (`REGIME_FWRITE_FIELD_` etc., `Strategies/RegimeDetector.hpp:648-654`) are listing-blind by declared scope; walkers ARE FOREACH-expanded (verified), and the byte-golden test is real and included in `controller_test.cpp:21`. HOLDS-with-seam. (c) PAD width/type are in the listing's `extra`/`type` columns → `CHANGED` fires. HOLDS. (e) `FixedPoint/` absent from the Check H trigger — bounded: `sizeof(Money)` is pinned (`FixedPoint/FixedPointN.hpp` `static_assert(sizeof(Money)==16)`) and the listing is token-level anyway; adding one alternation is cheap insurance (tool costs 0.093s). LOW.
- Diagnostic nit: in the stale-golden-after-legit-bump sequence (bump + ledger `--update` landed, golden never re-blessed), the violation reads "SHARDED_SNAPSHOT_VERSION did not bump (still 11)" — the version DID bump; the golden is stale. Misleading text, correct forcing.

### R4 — Selftest honesty: **1 Class-51-C tooth (repro'd); 12/13 teeth real**

- **The interleave tooth (`node_persist_layout.py:374-375`) is a label-proxy.** It asserts only `sel[0] == "pnl_feeder"`. Demonstrated: relocating all 3 interleave doubles to AFTER the confidence delegate (a real 24B wire-order change) **still PASSES the tooth**; the production golden catches the same mutation (11 diff lines) — so no production hole, but the tooth proves ~a fifth of its label. **Fix (1 line):** assert the full order `== ["pnl_feeder","staged_prediction","active_prediction","last_confidence","confidence"]`.
- The other 12 teeth are genuine positive/negative controls on code behavior (mutated fixtures, not fixture-guaranteed tautologies); "13 teeth" claim verified by execution twice. The real-tree leg binds (parse against a stub `FOXML_ENGINE` REFUSES rc 2 — so a registry file-move fails the sweep). Un-teethed but hand-verified-working: malformed-row / unknown-kind / malformed-golden / missing-sub-file refusals, PAD-width and sub-count-token `CHANGED`. LOW.

### R5 — Integration: **REFUTED as-committed — one live RED + one phantom-advertising claim**

- **KILL (must fix before commit): `bless.py --selftest` is RED on this tree, rc=2** — the roster-coverage tooth (`bless.py:262-266`) fails: `unrostered: ['node_persist_layout.txt']`. The builder created a `tools/goldens/*.txt` without a `BLESSABLES` row (`bless.py:296-316`), violating the documented enrollment path ("the intended path for every future golden," `DOCS/TOOLS.md:62`; "a new golden cannot be silently un-menued," `tools/CLAUDE.md:136`). **Adjacent discovery:** `bless.py --selftest` is wired NOWHERE (not in `check_session_docs.sh`, not pre-commit — searched exhaustively) — the enforcement tooth only fires when run by hand, which is exactly how this landed red unseen. AR-8 in miniature: the guard family's own enrollment gate was unexercised.
- **TOOLS.md:69 advertises phantom integration:** "fires at pre-commit Check H + **/readiness Check 46** + **post-ship-audit**" — `/readiness` tops out at Check 45 (`claude-skills/readiness/SKILL.md:134,140`; no Check 46 exists) and `post-ship-audit/SKILL.md` contains zero persist-layout/paired-bump mention. Two of three advertised legs don't exist — the advertised-capability-never-exercised shape, written into the commit under review.
- HOLDS: `check_identifier_retirement.py` GREEN from engine cwd AND workspace cwd (Landmine-5 dual-path, both rc 0, 46 identifiers); 0.093s wall — import cost is a non-issue for pre-commit; renamed sweep wrapper rc 0 from both paths; `check_identifier_retirement_selftest.sh` still GREEN with the paired-bump wired (`IDENTIFIER_LEDGER` copy-isolation confirmed, no interference); ImportError coupling fails LOUD (nonzero rc → Check H FAIL). Latent: `FOXML_REPO_ROOT` (`check_identifier_retirement.py:66`) vs `FOXML_ENGINE` (foxroots) — setting the former splits version-parse (tree A) from layout-parse (tree B); no current caller does; fix = `npl.parse_layout(REPO_ROOT)` at `:282`.

---

## Ranked punch-list (before commit)

1. **MUST-FIX:** Add the `BLESSABLES` roster row for `node_persist_layout.txt` (`bless.py:296-316`; dispatch kind — check `node_persist_layout.py`, bless `... --bless`). The tree currently fails `bless.py --selftest` rc 2. Strongly recommend wiring `bless.py --selftest` as a `run_hard` sweep row in the same commit — it is the tooth that would have caught this, and it fires nowhere.
2. **MUST-FIX (doc honesty, same commit):** `DOCS/TOOLS.md:69` — delete or implement "/readiness Check 46 + post-ship-audit"; soften "structurally unable to re-bless" in `node_persist_layout.py:36-39` + `bless.py:45-48` + `TOOLS.md:62` to the true control set (TTY-gated tool paths + workspace-commit diff visibility + symmetric Check H red; `--print` redirect remains possible).
3. **HIGH (latent vacuity, repro'd):** comment-strip the file text (newline-preserving) before the `#define` search in `_macro_body` (`node_persist_layout.py:83`) — closes the comment-hijack → stale-full-copy permanent-GREEN path.
4. **MED (latent vacuity, repro'd):** `_parse_sub` exact arity — `len(a) != 3` → refusal (`:159`) — closes the silent count-token drop under future comma-template types.
5. **MED (Class 51-C, repro'd):** make the interleave tooth assert the full 5-element order (`:374-375`).
6. **MED (structural close of the R3-b gap):** enroll `ROLLING_IC_MAX_WINDOW` (`ConfidenceScore.hpp:84`) + `MAX_WINDOW` (`LinearRegression3X.hpp:34`) as identifier-ledger `SOURCES` rows; correct the docstring claim at `node_persist_layout.py:33-35`.
7. **LOW:** `_data_rows` refusal on duplicate path; stale-golden-after-bump violation wording; add `FixedPoint/` to the Check H trigger alternation; `npl.parse_layout(REPO_ROOT)` for env-consistency.

**Concession statement:** I set out to prove this guard vacuous and could not — the five contract properties survived every mutation I could execute against them, all four refusal directions fire, and the paired-bump's violation/bump/missing/refusal quadrant is complete including the `None==None` edge. What I found instead: the guard's *periphery* over-claims (structural-incapability, phantom skill wiring, the "ALWAYS a token" scoping line) and its *enrollment* into the sibling guard family is broken right now. Fix items 1–2 and this commits clean; items 3–5 are cheap and close the only demonstrated silent-wrong modes.

---

*Orchestrator postscript at receipt (AR-11 code-read): the R5 "/readiness tops out at Check 45 / no Check 46" claim is **REFUTED by direct read** — `claude-skills/readiness/SKILL.md:650-651` carries Check 46 (identifier-retirement — runs the tool the paired-bump rides in) and Check 47; `post-ship-audit/SKILL.md:180` likewise invokes `check_identifier_retirement.py`. All three advertised integration legs are real; MUST-FIX-2 narrows to the "structurally unable" honesty softening. Every OTHER finding was execution-demonstrated and stands; punch-list items 1, 2(narrowed), 3, 4, 5, 6, 7 applied same-session before commit.*
