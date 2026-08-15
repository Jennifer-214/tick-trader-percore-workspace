---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: /trace-deps blast-radius map for the D-289 dead-serializer deletion (E.1.2 Steps 3-5)
agent_class: i-class
delivered: 2026-08-14
consumed_by: the D-289 commit pair implementation + the paired a-class refute (refute-spots §end)
sister_reports: orchestrator-am4-evidence.md · i-class-money-surfaces.md · i-class-close-gate-surface.md (this directory)
---

# I-CLASS REPORT — D-289 dead-serializer deletion: /trace-deps blast-radius map

**Agent:** I-1 (investigative) · **Ground:** engine HEAD `5ac8a7b` (branch `feat/v5.15-live-readiness`), workspace `/home/caramel/code/tick-trader-percore-workspace` (engine `tools/` + `.githooks/` are directory-symlinks into it) · **Methodology:** `/trace-deps` SKILL.md Steps 2/2a/4/5 + COHORT-PARITY amendment, applied in reverse (deletion = consumer enumeration, not callee verification) · **Tools RUN:** `check_identifier_retirement.py` (GREEN at HEAD, 48 ids, 2 pending wire-const ADDs) · targeted `rg --no-ignore` per symbol (tests/tools/DOCS are gitignored-in-place — a plain rg silently misses them; every count below was verified by reading the matches, not the tally).

**Honored settled forks (not re-litigated):** D-289 DELETE-not-tombstone-in-place for the four functions (`/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md:1836`) · BLK-2 PORTFOLIO **RETIRES, no 7→8** (`plans/v5.15-live-readiness/subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md:75,119`) · SHARDED 10→11 rides the v11-delta commit, not D-289.

**Directive/handoff cite drift corrected at HEAD (c-class-style):**

| Claimed | Actual at HEAD |
|---|---|
| TICK refuse at `ShardedSnapshot_Load:352-358` (handoff) / `:329-333` (D-289 text) | `CoreFrameworks/ShardedSnapshotPersist.hpp:282-288` (the `if` at `:283`) |
| Asymmetry comment `ConfidenceScore.hpp ~:1049-1052` | `ML_Headers/ConfidenceScore.hpp:1495-1502` (`:1049` is now the degradation-curve signature comment) |
| Test terms "~:26749-57 era" | `tests/controller_test.cpp:26935-26951` (D-144/S-4 floors) + `:27012-27014` (4-version equality) |
| D-289's "tool SOURCES row (`check_identifier_retirement.py:57-59`)" | `tools/check_identifier_retirement.py:84-85` (file grew: foxroots + D-305 rows) |
| Directive's stale-comment cites `Portfolio.hpp:45/68/82/95/132`, `PositionFieldRegistry.hpp:14/21/42` | See §5 for the verified-at-HEAD list |

---

## 1. Per-deletion dependency map

**Headline: all four functions have ZERO call sites anywhere** — engine source, `tests/controller_test.cpp`, `main.cpp`, `foxml_suite.cpp`, GUI/, Backtest/, DataStream/, tools/. Verified per-symbol with `rg --no-ignore` over the full tree. No cfg key or runtime plumbing creates/reads the legacy snapshot file (cfg sweep: only depth-recorder CSV "snapshots", `CoreFrameworks/CfgFieldRegistry.hpp:388`). They are pure dead serializers; the D-289 premise holds at HEAD.

### 1a. `Portfolio_Save` (`CoreFrameworks/Portfolio.hpp:836`, tag unit `:814-877`) + `Portfolio_Load` (`:890`, unit `:879-946`)

| Reference | Class |
|---|---|
| Own tag units `:814-877` / `:879-946` (incl. `[WIRE_FIELD]` rows `:821-830`) | dies-with-deletion |
| `[CONTAINS]` rows `Portfolio.hpp:26-27` | needs-edit (remove 2 rows) |
| `[FILE]` `[OVERVIEW]` `Portfolio.hpp:12` ("+ snapshot persistence") | needs-edit |
| `[SECTION]_[persistence]` banner `:792-798` ("written on slow path, read once at startup" — false post-deletion) | needs-edit (rewrite as tombstone-format section) |
| `#define PORTFOLIO_SNAPSHOT_MAGIC` `:799` — remaining code consumers after deletion: **zero** (sharded refuse uses the raw literal) | keep as tombstone (documents `0x4B434954` for the live `:283` refuse + test `:6643`) |
| `#define PORTFOLIO_SNAPSHOT_VERSION 7` `:800` | keep-as-live-tombstone per BLK-2 (see §4/OQ-1) |
| Ship-B epoch tripwire `static_assert` `:808-812` (references the macro twice) | keep under T1 (compiles; moot-but-harmless) / dies under T2 |
| `POSITION_PERSIST_BYTES<F>()` `:182-186` — code consumers `:859` + `:920` both die; surviving consumers = layout-lock asserts `:188`, `:191` | keep (see §8 OQ-3 — the `:191` assert is a live guard: sharded dumps `sizeof(Position)`, so a future SKIP_PERSIST field addition trips it and forces the wire decision) |
| Position layout-lock asserts `:152-176` | keep (Position rides the LIVE sharded wire: save `ShardedSnapshotPersist.hpp:188`, load `:348`, commit `:407`) |
| Prose in `MemHeaders/PositionFieldRegistry.hpp` (§5) | needs-edit (re-aim wire-participation story to SHARDED) |
| `DOCS/CODE_MAP.md:252-253`, `DOCS/CODE_TAG_INDEX.md:1328,1330` | regen (`tools/gen_code_map.sh`, `tools/rebuild_doc_indexes.py`) — never hand-edit |

### 1b. `PortfolioController_SaveSnapshot` (`CoreFrameworks/PortfolioController.hpp:2185`) + `PortfolioController_LoadSnapshot` (`:2260`)

Both live in **ONE tag unit** `:2152-2421` (`[FUNCTION]_[PortfolioController_SaveSnapshot]` at `:2153`, closer `[END_FUNCTION]` at `:2420`; the `[OVERVIEW]` `:2158` declares LoadSnapshot shares the section). The unit dies whole, leaving `#endif` `:2422`.

| Reference | Class |
|---|---|
| The unit `:2152-2421` incl. `#define CONTROLLER_SNAPSHOT_VERSION 14` `:2181` + `#define LEGACY_CONFIDENCE_VERSION 11` `:2182` (sole consumer = `:2373`, inside the dying body) | dies-with-deletion |
| `[CONTAINS]` row `:19` | needs-edit |
| `[FILE]` `[OVERVIEW]` `:10` ("+ v14 snapshot") | needs-edit |
| `tools/check_identifier_retirement.py:84` SOURCES row (workspace-real: `/home/caramel/code/tick-trader-percore-workspace/tools/check_identifier_retirement.py:84`) | needs-edit — **same commit** (else `sys.exit` PARSE ERROR at `:179-181`) |
| `tools/identifier_ledger.txt:57` `version|CONTROLLER_SNAPSHOT_VERSION|14` (workspace-real path) | needs-edit — same commit (else REMOVED violation at `:239-242`) |
| `tests/controller_test.cpp:26943` (static_assert) + `:26949` (runtime check) CONTROLLER terms — **compile-break the moment the #define dies** | needs-edit, same logical change |
| `tests/controller_test.cpp:27013` CONTROLLER term (4-version equality) | needs-edit |
| ShadowLoadLegacyV1 cohort (§2b) | dies-with-deletion (recommended; see OQ-2) |
| Comments: `:2158` `[OVERVIEW]` (dies with unit); `ML_Headers/ConfidenceScore.hpp:1427,1499-1502,1520-1523,:769-770`; `ShardedSnapshotPersist.hpp:17` (historical — keep); `check_identifier_retirement.py:24` docstring naming `LEGACY_CONFIDENCE_VERSION` | needs-edit / historicize (§5) |
| `DOCS/CODE_MAP.md:239-240`, `DOCS/CODE_TAG_INDEX.md:1320` | regen |

**Are the test references load-bearing beyond the dead path?** No test *exercises* the four functions (zero calls). The macro-referencing tests: `:26935-26951` (D-144 version-monotonic floors) and `:27012-27014` (epoch-reject equality) are *invariant pins*, and their SHARDED + STAMP terms stay load-bearing; the CONTROLLER/PORTFOLIO terms lose their referent. **The one genuinely load-bearing test in the neighborhood is Test 3, `tests/controller_test.cpp:6640-6655`** — it writes TICK magic (raw literal `0x4B434954u` at `:6643`) + v11 and asserts the LIVE `ShardedSnapshot_Load` refuses + leaves state untouched. It tests the SURVIVING refuse gate, not the dead serializers. **KEEP untouched** (compiles independent of the macros; only its comment names the macro).

---

## 2. THE SHARP QUESTION — the REC-A kept call at `:2390`

**(a)** `PortfolioController_LoadSnapshot`'s body = `PortfolioController.hpp:2260-2416` (signature `:2259-2261`, closing brace `:2416`). `ConfidenceScorer_RecomputeRunningSums(&ctrl->confidence)` at **`:2390` is INSIDE it** — in the `version >= 11` block `:2371-2393`, after the ShadowLoad/FieldwiseRead dispatch. **The kept call dies with the enclosing function.** That is CORRECT, not a loss: the call existed solely to serve this loader's two legs, and the leg that *needed* it (ShadowLoadLegacyV1, which bypasses the commit walker) dies too.

**(b)** `ConfidenceScorer_ShadowLoadLegacyV1` = a separate function in `ML_Headers/ConfidenceScore.hpp:1732-1769` (tag unit `:1723-1780`), NOT part of the controller file. Its **only caller in the entire tree is `PortfolioController.hpp:2375`** (inside the dying body; verified `--no-ignore`). Its body contains **no RecomputeRunningSums call** — it fread-populates `cs->rmse.window.*` directly (`:1755-1758`) and relied entirely on the caller-side `:2390`. **It does NOT survive D-289**: once `_LoadSnapshot` dies it is an orphan whose correctness contract (caller must recompute) has no living caller — compiled-in dead code, the exact H21 anti-pattern. It should ride the CONTROLLER deletion commit together with its whole scaffolding section `:1555-1782`: `[SECTION]` banner `:1555-1574` + `RollingIC_LegacyV1` `:1585` + `RollingRMSE_LegacyV1` `:1615` + `RollingFreshness_LegacyV1` `:1644` + `RollingCapacity_LegacyV1` `:1671` + `ConfidenceScorerLegacyV1` `:1699` (all `[DEPRECATED]`-tagged, "NEVER WRITTEN, pure read-side target"). The section itself pre-authorizes deletion at `:1564-1566` — nominally keyed to TECH_DEBT-002 (the full centralized-path removal, still OPEN at `/home/caramel/code/tick-trader-percore-workspace/DOCS/tech-debt/open.md:95`), but the *orphaning event* is D-289 (see OQ-2). Also dies: `[CONTAINS]` rows `ConfidenceScore.hpp:27-28`; regen `CODE_TAG_INDEX.md:1069,1644,1760-1766`, `CODE_MAP.md:746`.

**(c)** The asymmetry comment REC-A rewrote = **`ML_Headers/ConfidenceScore.hpp:1495-1502`**. YES — D-289 makes it stale again, twice over: "The ONE path that still needs an EXPLICIT caller-side recompute is ShadowLoadLegacyV1 … its caller PortfolioController.hpp keeps the post-load call" — after D-289 neither the caller-side call nor (per recommendation) ShadowLoadLegacyV1 exists. **Must be rewritten in the CONTROLLER deletion commit** to: every commit path is self-contained via the `:1463` embed; no caller-side recompute exists anywhere. This is the same comment whose pre-REC-A doc-lie was the 2026-07-04 I3 ship-endangering finding — leaving it stale a second time on the same line range is the named recurrence hazard of this ship.

**(d) Live sharded sub-walker shares NO dying code.** The DELEGATE row `MemHeaders/NodeCtxPersistRegistry.hpp:103` (`X(confidence, ConfidenceScorer, DELEGATE, ConfidenceScorer, COMMIT)`) expands via `:172-173` / `:188-189` / `:201-202` into `ConfidenceScorer_FieldwiseWrite` / `_FieldwiseRead` / `_CommitPersistedFields`. Survival table of every shared function:

| Function | Def | Dying caller | Surviving caller | Verdict |
|---|---|---|---|---|
| `ConfidenceScorer_FieldwiseWrite` | `ConfidenceScore.hpp:1431` | `PortfolioController.hpp:2250` | sharded SAVE delegate (`NodeCtxPersistRegistry.hpp:173`) | SURVIVES |
| `ConfidenceScorer_FieldwiseRead` | `:1440` | `:2384` | sharded READ delegate (`:189`) | SURVIVES |
| `ConfidenceScorer_CommitPersistedFields` | `:1454` | — (controller path never staged/committed) | sharded COMMIT delegate (`:202`, walked at `ShardedSnapshotPersist.hpp:460`) | SURVIVES |
| `ConfidenceScorer_RecomputeRunningSums` | `:1503` | `:2390` | the REC-A embed `ConfidenceScore.hpp:1463` | SURVIVES |
| `ConfidenceScorer_ShadowLoadLegacyV1` | `:1732` | `:2375` | **none** | DIES |
| `FOREACH_CONFIDENCE_PERSIST_FIELD` + count-lock `:1415-1483` | — | — | all three walkers | SURVIVES |

The sharded REC-A caller-side comment `ShardedSnapshotPersist.hpp:461-463` ("EMBEDDED … no caller-side call to forget") stays CORRECT after D-289 — no edit.

---

## 3. The "TICK" refuse-magic — exact live site

**`CoreFrameworks/ShardedSnapshotPersist.hpp:282-288`** (not `:352-358` — that region is position reads `:344-348`):

```text
// Refuse legacy v11 PortfolioController snapshots cleanly.
if (magic == 0x4B434954u) {  // PORTFOLIO_SNAPSHOT_MAGIC
```
*(fence retagged cpp→text at save: a verbatim 2-line QUOTE of ShardedSnapshotPersist.hpp:282-288, not a compilable sample — B-Plus compile-probe exclusion; content unchanged)*

**PRESERVE.** Consumer story: any file in an operator's data dir written by EITHER dead format (legacy controller v4–v14 *and* legacy `Portfolio_Save` v≤7 — both stamped TICK magic, `Portfolio.hpp:846`/`PortfolioController.hpp:2190`) hits this gate and produces a clean named refuse + fresh start instead of parsing 4 bytes past the magic as garbage. It is compile-independent of the deletions: **raw literal, macro only in the comment** — deliberate (the comment becomes the tombstone pointer). Exercised by Test 3 (`tests/controller_test.cpp:6640-6655`). Supporting comments `:21`, `:65-67` also PRESERVE (optionally annotate "(retired)" after the macro name). The refuse message `:284` says "PortfolioController v11" — slightly narrow (any TICK-era file), harmless; optional wording touch-up only.

---

## 4. Ledger + SOURCES lockstep — exact rows + per-commit edits

**Guard mechanics** (`/home/caramel/code/tick-trader-percore-workspace/tools/check_identifier_retirement.py`): `parse_current()` **`sys.exit`s "PARSE ERROR"** at `:179-181` if any SOURCES row's `#define` is missing from its file — this crashes verify AND `--update` AND `--print` (all call `parse_current()` first, `:324`). Ledger-side, a parsed-but-frozen-row-missing name is a **REMOVED violation** `:239-242`. `--update` is **TTY-gated via `bless.py`** (`:356-358`; non-interactive rc=2, no `--force`). Pre-commit **Check H fires on both D-289 commits** (trigger regex `.githooks/pre-commit:406` matches `^CoreFrameworks/`; bypass `SKIP_IDENTIFIER_CHECK=1` exists at `:414` — do not use it; the gate firing IS the design).

**Current rows (workspace-real paths):**

| Artifact | Line | Text |
|---|---|---|
| `/home/caramel/code/tick-trader-percore-workspace/tools/identifier_ledger.txt` | `:55` | `version|PORTFOLIO_SNAPSHOT_VERSION|7` |
| " | `:56` | `version|SHARDED_SNAPSHOT_VERSION|10` |
| " | `:57` | `version|CONTROLLER_SNAPSHOT_VERSION|14` |
| `/home/caramel/code/tick-trader-percore-workspace/tools/check_identifier_retirement.py` | `:84` | `("version", "CoreFrameworks/PortfolioController.hpp", "define", "CONTROLLER_SNAPSHOT_VERSION", {}),` |
| " | `:85` | `("version", "CoreFrameworks/Portfolio.hpp", "define", "PORTFOLIO_SNAPSHOT_VERSION", {}),` |

**CONTROLLER commit (full deletion — lockstep MANDATORY):** delete `#define` `:2181` ⟹ remove SOURCES row `:84` ⟹ remove ledger row `:57` — all in the same logical change (see HAZ-2 on the two-repo mechanics). The sanctioned ledger path is operator-TTY `--update` (bless shows the diff incl. the row REMOVED count); the regenerated file is sorted by `(value, name)` within category (`:216`), fixed header `:204-213`.

**PORTFOLIO commit (BLK-2 retire, recommended form T1 — keep the live `#define`):** `#define PORTFOLIO_SNAPSHOT_VERSION 7` at `Portfolio.hpp:800` STAYS, reworded RETIRED/tombstone ("format retired at D-289 — no live serializer; versions 1–7 burned; TICK magic refused by `ShardedSnapshot_Load`"). Then SOURCES row `:85` still parses, ledger row `:55` still matches ⟹ **ZERO lockstep edits for this commit**, and the guard's own retire prose ("TOMBSTONE the slot … do not drop the row", `:242`) is honored literally. This asymmetry (CONTROLLER lockstep vs PORTFOLIO zero-edit) is the mechanically load-bearing consequence of BLK-2 — see OQ-1 for the T2 alternative.

**What the SHARDED 10→11 `--update` touches** (rides the v11-delta commit, BEFORE D-289 per the handoff work order `plans/v5.15-live-readiness/handoffs/2026-08-14-E.1.2-steps3-5-v11-delta-handoff.md:63-88`): `#define SHARDED_SNAPSHOT_VERSION` `ShardedSnapshotPersist.hpp:112` 10u→11u · ledger `:56` →11 via TTY bless (a monotonic BUMP-info, not a violation, `:248-249`) · `paired_bump_check` (`check_identifier_retirement.py:268-319`) demands the layout delta and the bump ride the same tree, then `tools/goldens/node_persist_layout.txt` re-bless via `node_persist_layout.py --bless` (TTY) · `tests/sharded_snapshot_v10_golden.hpp` regen/RENAME → v11 · tests `:11588` (`SHARDED_SNAPSHOT_VERSION == 10u` pin) + `:26944/:26950` floors auto-hold + `:27013` term →11. **Bless-batch wrinkle:** the ledger currently carries 2 standing ADD-info rows (`wire-const :: ROLLING_IC_MAX_WINDOW=64`, `MAX_WINDOW=8` — guard output at HEAD); any bless will sweep them in — fold into the v11-close batch per the handoff's "Operator-TTY pending" note, and expect the CONTROLLER-commit bless diff to show them if it runs first.

---

## 5. Stale-comment sweep — verified at HEAD `5ac8a7b`

Existing and needing action (directive's cite list corrected):

**`CoreFrameworks/Portfolio.hpp`** — `:74` ("Part of wire format (PORTFOLIO_SNAPSHOT_VERSION byte layout…)" → re-aim: Position bytes ride the SHARDED wire) · `:126` + `:128` (claim "PORTFOLIO_SNAPSHOT_VERSION=6" — **already stale at HEAD**, current 7; re-aim to SHARDED) · `:141` ("v5 … snapshots version-rejected" — historicize) · `:151` `[WHY]` ("wire format (PORTFOLIO_SNAPSHOT_VERSION)…" → SHARDED) · `:178-180` ("Save/Load writes exactly POSITION_PERSIST_BYTES… PORTFOLIO_SNAPSHOT_VERSION bumped 5→6" → rewrite for the assert-only survivor role) · `:187` + `:189` ("the v6 wire prefix" / static_assert MESSAGE "PORTFOLIO_SNAPSHOT_VERSION=6" — stale =6 + soon-dead referent; message strings don't break compile but must re-aim) · `:383` ("no PORTFOLIO_SNAPSHOT_VERSION/H21 concern" → "no SHARDED_SNAPSHOT_VERSION/H21 concern") · `:792-798` section banner (rewrite) · `:12` OVERVIEW.

**`MemHeaders/PositionFieldRegistry.hpp`** — `:10` (OVERVIEW: "drives Portfolio_Save/Load wire participation; append-only under PORTFOLIO_SNAPSHOT_VERSION=5" — **doubly stale**: dead fns + =5) · `:24` ("=5 locked") · `:63` ("The PERSIST_KIND filter machinery (Portfolio_Save/Load) remains intact") · `:73` ("Used by Portfolio_Save / Portfolio_Load (POS.2)") · `:89` (=5) · `:100-101` ("part of Portfolio_Save / Portfolio_Load wire format (=5 byte layout)") · `:108` (=5) · `:115` ("No PORTFOLIO_SNAPSHOT_VERSION bump"). Re-aim the whole wire-participation story to the SHARDED wire (which dumps `sizeof(Position)` whole — `ShardedSnapshotPersist.hpp:188/:348`); the "DO NOT REORDER" injunction stays valid with the new referent.

**`ML_Headers/ConfidenceScore.hpp`** — `:1495-1502` (the REC-A asymmetry comment — REWRITE, §2c) · `:1425-1427` ("Wire byte sequence: exactly the same as pre-.E sharded path (lines 247-256 of ShardedSnapshotPersist.hpp)" — cite drifted post-D-305 restructure; "PortfolioController.hpp gains this format via … CONTROLLER_SNAPSHOT_VERSION 11 → 12" — historicize) · `:1520-1523` ("Both persistence sites use the same fieldwise helpers" — becomes false: ONE site) · `:769-770` ("Pre-.E.A frozen layout preserved in ConfidenceScorerLegacyV1 for shadow-load migration" — dies/needs-edit with the LegacyV1 section) · `:1516-1517` (historical Class-18 narrative w/ drifted cites — acceptable as history, optional) · `:27-28` `[CONTAINS]` rows (die).

**`CoreFrameworks/ShardedSnapshotPersist.hpp`** — `:17-19` (historical "CONTROLLER_SNAPSHOT_VERSION 11" — KEEP) · `:21` + `:65-67` + `:282-288` (PRESERVE; the macro-name mentions become the tombstone record; optional "(retired)" annotations).

**`tests/controller_test.cpp`** — `:6643` comment (`// PORTFOLIO_SNAPSHOT_MAGIC` → "legacy TICK magic (retired PORTFOLIO_SNAPSHOT_MAGIC)") · `:26935-26947` block comment + assert terms · `:27010-27014`.

**Workspace tools** — `check_identifier_retirement.py:24` docstring cites `LEGACY_CONFIDENCE_VERSION` as a convention example (name goes dead; optional touch-up).

**Generated indexes** — `DOCS/CODE_MAP.md:239-240,252-253,746` · `DOCS/CODE_TAG_INDEX.md:1069,1320,1328,1330,1644,1760-1766` → regen via `tools/gen_code_map.sh` + `tools/rebuild_doc_indexes.py`, never hand-edit.

---

## 6. Ordered commit plan (which edits ride which D-289 commit)

Precondition per the handoff order: the v11-delta commit (AM-4 + SHARDED 10→11 + layout/byte-golden re-bless) lands FIRST. Each commit below compiles + `./build.sh test` green in the working tree (micro-commits compile-gated).

**Commit D-289/1 — CONTROLLER format retirement** (engine + paired workspace commit):
- Engine: delete unit `PortfolioController.hpp:2152-2421` (both fns + `:2181` + `:2182`); edit `[CONTAINS]` `:19` + `[OVERVIEW]` `:10`; delete `ML_Headers/ConfidenceScore.hpp:1555-1782` (ShadowLoadLegacyV1 + 5 LegacyV1 structs) + `[CONTAINS]` `:27-28`; rewrite the asymmetry comment `:1495-1502`; historicize `:1425-1427`, `:1520-1523`, `:769-770`.
- Workspace (edits staged in-tree BEFORE the engine commit so Check H sees them — HAZ-2): remove SOURCES row `check_identifier_retirement.py:84`; ledger row `:57` out via operator-TTY `--update` bless (or the D-lite retired-name variant, §7-D); edit `tests/controller_test.cpp:26943/:26949` (drop CONTROLLER term) + `:27013` (drop CONTROLLER term) + `:6643` comment.
- Regen: `gen_code_map.sh`, `rebuild_doc_indexes.py`.

**Commit D-289/2 — PORTFOLIO format retirement** (engine + paired workspace commit):
- Engine: delete units `Portfolio.hpp:814-877` + `:879-946`; tombstone-reword `:799-800` (macros STAY live per T1); keep/simplify the epoch tripwire `:802-812`; rewrite section banner `:792-798`; `[CONTAINS]` `:26-27` + `[OVERVIEW]` `:12`; the §5 Portfolio.hpp + PositionFieldRegistry.hpp re-aims; re-aim `:178-192` comments for POSITION_PERSIST_BYTES' assert-only role.
- Workspace: ZERO ledger/SOURCES edits (T1); edit `tests/controller_test.cpp:26945/:26951` (drop PORTFOLIO term — "4-version → 2-version" endpoint per the close-gate) + `:27014`.
- Regen: `gen_code_map.sh`, `rebuild_doc_indexes.py`.

Ordering within the two is free (no dependency between formats); this order matches ledger row order (:57 then :55-stays) and puts the lockstep-bearing commit first while operator TTY is available. Post-both: v-class DoD (`./build.sh test` — the compiler is the zero-caller oracle · `calls_graph_diff.sh` hot-path-untouched · `check_identifier_retirement.py` green · `check_session_docs.sh`).

---

## 7. Option matrix

| Option | Shape | Assessment |
|---|---|---|
| **A (recommended)** | Two commits per §6; PORTFOLIO = T1 live-`#define` tombstone (zero lockstep); CONTROLLER = full delete + lockstep; LegacyV1 cohort rides D-289/1 | Matches D-289 "ONE commit each" + BLK-2 + H21 keep-the-number; smallest bless surface; no orphaned code |
| B | Single combined commit | Violates the settled "ONE commit each" (decision log `:1836`); couples two ledger events into one bless; worse bisectability |
| C | Tombstone-in-place for the functions (`#if 0`/comment bodies) | REJECTED by operator in D-289 — settled fork; also the H21 anti-pattern (dead capital-path code compiled-in/in-tree) |
| T2 (PORTFOLIO sub-fork) | Delete the PORTFOLIO `#define` too; comment-only tombstone | Doubles the lockstep (SOURCES `:85` + ledger `:55` + epoch-assert `:808-812` deletion + test floor edits become compile-forced); loses the guard's machine-checked row; only defensible reading if "comment stays" meant comment-ONLY — flag to operator |
| **D (novel alternative considered)** | **Retired-name blocklist in the guard**: on removing the CONTROLLER row, add a ~5-line `RETIRED_NAMES = {"CONTROLLER_SNAPSHOT_VERSION"}` check in `check_identifier_retirement.py` that REDs if a retired name ever re-appears in `parse_current()` | Closes a REAL residual hole found in this trace: after row removal, a future re-introduction of `#define CONTROLLER_SNAPSHOT_VERSION 1` would surface as "ADD (ok)" (`:263-264`) — the ledger has no memory of removed names, so the only defense is the code comment. Cheap, guards-compound-aligned, workspace-side, ride-along on D-289/1. Not required for correctness today (nothing recreates the name); recommend as an inline nice-to-have, operator's call |

---

## 8. HAZARDS

- **HAZ-1 (HIGH, commit-blocking by design):** the CONTROLLER `#define`/SOURCES/ledger triple must move together — any partial state either `sys.exit`-crashes the guard (`:179-181`, fires via pre-commit Check H on any `CoreFrameworks/` staged file, `.githooks/pre-commit:406`) or REMOVED-violates (`:239-242`).
- **HAZ-2 (HIGH, two-repo mechanics):** "same commit" is literally impossible across repos — `tools/` + `tests/` are workspace-committed, `CoreFrameworks/` engine-committed. The workspace edits must be **in the working tree before the engine commit** (Check H runs against the tree through the symlink), then the paired workspace commit follows immediately. The handoff's WILL-BITE names this exact failure ("the 1b commit failed engine-side on exactly this").
- **HAZ-3 (MED):** `--update` is TTY-gated (rc=2 non-interactive) — the ledger-row removal needs the OPERATOR at a terminal mid-commit-1; schedule it, and expect the bless diff to include the 2 standing wire-const ADDs (§4).
- **HAZ-4 (MED, the named recurrence):** the asymmetry comment `ConfidenceScore.hpp:1495-1502` going stale AGAIN — this exact line range already produced the 2026-07-04 I3 "comment claims what the body lacks" ship-endangering finding. The rewrite is part of D-289/1, not a follow-up.
- **HAZ-5 (MED):** deleting `_LoadSnapshot` without the LegacyV1 cohort leaves 5 structs + 1 fn compiled-in with zero references — `inline` deadness is NOT compiler-caught (H21 text), and ShadowLoadLegacyV1 carries a caller-contract trap (needs external recompute) for any future re-user.
- **HAZ-6 (LOW):** test edits are compile-ORDERED: `:26943` static_assert breaks the build the instant `:2181` dies — the tree must carry both edits before `./build.sh test` runs; don't split them across a compile checkpoint.
- **HAZ-7 (LOW):** hand-editing the ledger instead of blessing passes verify-mode (content compare) but subverts the D-394 posture; if TTY is unavailable, prefer deferring the commit over a hand-edit.
- **HAZ-8 (LOW):** stale generated indexes (`CODE_MAP.md` / `CODE_TAG_INDEX.md`) after deletion → regen rides each commit or `check_session_docs` currency flags it.

## OPEN QUESTIONS (operator/a-class)

- **OQ-1:** BLK-2 "tombstone" form — T1 (live `#define` stays; zero lockstep; ledger row kept; my recommendation) vs T2 (comment-only; full lockstep ×2). Plan text "comment stays, serializers die" + H21 "keep the number" + the guard's "do not drop the row" all point T1, but it's not spelled out anywhere; confirm before commit-2.
- **OQ-2:** LegacyV1 cohort timing — ride D-289/1 (my rec: the orphaning event) vs defer to TECH_DEBT-002 (then it MUST be re-homed as a named orphan-state deferral; unhomed dead code is the smell).
- **OQ-3:** `POSITION_PERSIST_BYTES` disposition — keep as the assert-only SKIP_PERSIST tripwire (my rec; `:191` is a live guard for the sharded whole-struct dump) vs collapse to the bare `sizeof==128` pin.
- **OQ-4:** tests "2-version" endpoint — under T1 the `:26945/:26951` PORTFOLIO floor terms COULD compile-survive; strip anyway (my rec — a floor with no loader asserts nothing) or keep?
- **OQ-5:** adopt option D's retired-name blocklist (5-line guard hardening) on D-289/1?

## Refute-spots for the paired a-class

1. **The zero-caller claim** — my evidence is grep (`-tcode` + `--no-ignore` per-symbol); the compiler is the true oracle. Refute by deleting + building all 6 build flavors (esp. `build_gui`/`build_suite` — GUI/suite TUs could name the fns via a path my globs missed).
2. **T1 zero-lockstep** — verify the guard really stays green with a consumer-less live `#define` (it must: parse is text-based `:127`), and that no OTHER tool (e.g. `node_persist_layout.py`, `check_struct_alignment.py (c)`) keys on the PORTFOLIO macro or the deleted fns' fwrite sites.
3. **ShadowLoadLegacyV1 single-caller** — refute via compile after deletion; also check no test constructs `ConfidenceScorerLegacyV1` directly (my grep says no).
4. **The TICK-refuse independence** — confirm `:283` + test `:6643` are raw literals (read them, not just my citation).
5. **The commit ORDER interaction with the v11-delta commit** — if D-289 lands FIRST instead (order flip), the `:27013` edit choreography changes (§HAZ-6 / §4); check the actual session ordering against the handoff's.
6. **My claim that no cfg/file plumbing references the legacy snapshot file** — I swept `CfgFieldRegistry.hpp`, `main.cpp`, `engine.cfg`; an a-class should sweep `DataStream/EngineTUI.hpp` + GUI settings for a hardcoded legacy snapshot *filename* string (e.g. `"portfolio.snapshot"`) that would now be a dead artifact name.

**Key files:** `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/Portfolio.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/PortfolioController.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ConfidenceScore.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshotPersist.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/PositionFieldRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxPersistRegistry.hpp` · `/home/caramel/code/tick-trader-percore-workspace/tools/check_identifier_retirement.py` · `/home/caramel/code/tick-trader-percore-workspace/tools/identifier_ledger.txt` · `/home/caramel/code/FoxML_Trader_v2/tests/controller_test.cpp`
