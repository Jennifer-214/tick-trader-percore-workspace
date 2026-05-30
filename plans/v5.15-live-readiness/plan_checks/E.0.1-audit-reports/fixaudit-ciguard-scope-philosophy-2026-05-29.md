# Adversarial Audit — CI guard + SCOPE (D-73 net-gating) + Philosophy 4th-check

**Date:** 2026-05-29
**Auditor:** Independent adversarial (no subagents). Default skeptical; proposer drifted pragmatic-patch 3× this session.
**Engine HEAD:** 2492e43
**Target:** `.E.0.1` determinism-cluster locale findings — (a) replay PARSE [F-054/55, in plan], (b) recorder EMIT `%f` [H2], (c) cfg `atof` MIXED-parser [H3]; proposed categorical CI guard; SCOPE (net-gating vs PRE-PAPER-TEST).

---

## Ground-truth re-verification (I re-ran every GT claim)

| Claim | Verified? | Evidence |
|---|---|---|
| Net loads cfg via FILE-parse (atof path) in SOME tests | **YES** | `tests/controller_test.cpp:35` `ControllerConfig_Load<FP>("/tmp/test_controller.cfg")`; `tests/parity_harness.cpp:115` `ControllerConfig_Load<BACKTEST_FP>(config_path)` |
| Many other tests use programmatic Default (no parse) | **YES** | controller_test.cpp:262/308/355/400/498/552/607… all `ControllerConfig_Default<FP>()` |
| MIXED parser — migrated fields locale-immune, unmigrated use atof | **YES** | Dispatch path `CfgFieldDispatch.hpp:75,82` calls `parse_double_fast`; manual `CFG_PARSE_FPN/PCT/POS` + inline branches at `ControllerConfig.hpp:2149,2157,2178,2239,2244,2308-2357,2399,2597-2628,2814,2825,2903-2904,3070` use `atof` |
| `parse_double_fast` is locale-immune | **YES** | `ParseFast.hpp:45-51` wraps `std::from_chars` (standard mandates `.` decimal; locale-independent) |
| Dispatch pins per-thread uselocale | PARTIAL — only on SAVE | `CfgFieldDispatch.hpp:188` `newlocale(LC_NUMERIC_MASK,"C")` + `uselocale` is in `cfg_save_field` (emit). The PARSE path is locale-immune by `from_chars`, not by uselocale — so the "uselocale at :188" framing in the brief is the SAVE wrap, not the parse wrap. Net effect identical (migrated parse is immune) but mechanism differs. |
| Recorder EMIT is locale-tainted `%f` | **YES** | `TickRecorder.hpp:186` `fprintf(..."%lld,%.8f,%.8f,%d\n")`; `DepthRecorder.hpp:249` `fprintf(..."%llu,%llu,%.8f,%.8f,%.8f,%.8f\n")`; `TradeLog.hpp:92,105` same |
| No existing atof/strtod/locale grep-CI tool | **YES** | `tools/check_*.py` = 10 tools (doc_metadata, field_name_uniqueness, forward_promise, meta_registry, per_core_registry, plan_body_symbol, plan_body_tests, storage_t, struct_field). None scan for atof/strtod/locale. Proposed Class-37 grep-CI is the first. |

**NEW ground-truth I surfaced (load-bearing):**

- **GT-NEW-1 (recorder↔replay is a CLOSED locale-fragile loop, fragile on BOTH ends).** `DepthReplayState.hpp:224-227` parses with **bare `strtod`** (`bid_p = strtod(p,&p)` ×4) exactly the bytes `DepthRecorder.hpp:249` emitted with `%.8f`. So the replay surface is locale-tainted at emit AND at parse. F-054/55 (parse) + H2 (emit) are the **same** determinism loop, not two unrelated findings.
- **GT-NEW-2 (existing locale test does NOT cover cfg-parse).** The v5.11.4.A locale-immunity test (`controller_test.cpp:15180-15260`) tests `parse_double_fast` **in isolation** under de_DE — it never `ControllerConfig_Load`s a cfg file under de_DE and asserts parsed values. So the net today has **zero** cross-locale cfg-parse coverage.
- **GT-NEW-3 (the test deliberately calls `atof`).** `controller_test.cpp:15205,15209` calls `atof` to assert `parse_double_fast` matches it. A naive "forbid atof" guard would **red-build the very test that proves the guard's premise.**
- **GT-NEW-4 (legitimate global `setlocale` already in tree).** `GUI/StrategyQualityPanel.hpp:186,232` uses global `setlocale(LC_NUMERIC,"C")` save/restore around display-log `strtod`. Tests (`controller_test.cpp:1457-1464,9371-9386,15241-15250`) deliberately `setlocale(de_DE)`. A blanket "forbid global setlocale" guard red-builds correct existing code + the determinism tests themselves.
- **GT-NEW-5 (no clean directory discriminator).** `DataStream/` holds BOTH determinism-critical recorders (TickRecorder/DepthRecorder/DepthReplayState) AND pure-display TUIAnsi.hpp (~30 `%f` ANSI-escape sites at TUIAnsi.hpp:408,442,505,…). Directory scoping cannot separate them.

---

## TASK 1 — Categorical CI guard: buildability + false-positive discriminator

### Verdict: BUILDABLE, but NOT as a blanket grep, and NOT for `setlocale`. Build a NARROW allowlist-inverted guard over an EXPLICIT determinism-path manifest. Demote `setlocale` from "forbid" to "require-paired-restore-or-uselocale" (or drop it).

**Why a blanket grep is unbuildable-as-categorical:** the false-positive surface is large and legitimate per H4 ("display-only float OK"):
- `DataStream/TUIAnsi.hpp` — ~30 `%f` display sites (ANSI-coded), all H4-legal.
- `GUI/SettingsPanel.hpp:899,918,934,1323,1713` — GUI prefs + per-core display `atof`/`%f`.
- `Backtest/BacktestPanels.hpp:792-854` — ~15 `(float)atof` parsing a *display* metrics sidecar (already `(float)` — explicitly display per H4).
- `GUI/StrategyQualityPanel.hpp:186,232` — global `setlocale` save/restore (CORRECT pattern for a display-log reader).
- `controller_test.cpp:15205,15209` — `atof` used as the *oracle* for the immunity test.

A grep that fires on all of these either (a) nags constantly → operators add blanket suppressions → guard rots (the classic broken-windows failure), or (b) gets a hand-maintained ignore list that drifts. Neither is the structural closure the gradient wants.

**The discriminator that DOES work — explicit determinism-path manifest (allowlist-inverted):**
Maintain a small manifest of files/regions that are determinism/wire/replay surfaces, and run the guard **only inside them**, forbidding `atof`/`strtod`/`%[.0-9]*[fge]`-emit **except** `parse_double_fast*` / `from_chars` / a per-thread-`uselocale`-wrapped `snprintf`. The manifest is the SSoT discriminator — not a fragile directory glob, not 200 inline annotations.

Initial manifest (verified determinism surfaces):
```
CoreFrameworks/ControllerConfig.hpp        # cfg-file parse  (atof → migrate or wrap)
DataStream/TickRecorder.hpp                # CSV emit %f
DataStream/DepthRecorder.hpp               # CSV emit %f
DataStream/DepthReplayState.hpp            # CSV parse strtod
DataStream/TradeLog.hpp                    # trade-log emit %f  (verify replay-fed before adding)
CoreFrameworks/CfgFieldDispatch.hpp        # already compliant — guard asserts it STAYS so
```
Display files (TUIAnsi, GUI panels, BacktestPanels, EngineTUI) are simply **never in the manifest** → zero false positives, zero annotations needed. New determinism code is added to the manifest the same way you add a registry row (1 line). This is the categorical move: the *manifest* is the structural artifact, the grep is its enforcement.

Secondary (cheaper, weaker) discriminator if a manifest is rejected: a **positive** per-line `// locale-ok` escape that the guard requires for any `atof`/`%f` it finds in determinism dirs only. Inferior — annotations drift, and you still need a dir list. Manifest dominates.

**`setlocale` sub-finding (IMPORTANT):** forbidding *global* `setlocale` outright is WRONG — `GUI/StrategyQualityPanel.hpp:186` uses it correctly (save/restore) and the tests need it. The guard should forbid *unbalanced* global `setlocale` (a set with no restore on the same scope) OR simply not police `setlocale` at all and rely on the from_chars/uselocale positive-pattern requirement, which makes locale-state irrelevant on the hot determinism paths regardless of global locale. Recommend: **drop `setlocale` from the guard**; the emit/parse positive-pattern requirement is the real invariant (it's immune to whatever global locale is set, which is exactly why `from_chars` was chosen).

### Tier check: is grep-CI the right tier?
grep-CI is the **right** tier here and matches the gradient (compile-time/CI > runtime > convention). A compile-time check isn't reachable (`atof`/`fprintf` are library calls, no type-level hook). A clang-tidy AST matcher would be more precise but is heavier infra than the 10 existing `check_*.py` greps and not yet in this repo's toolchain. grep-over-manifest is proportionate (matches `check_field_name_uniqueness.py` etc.). **Not too blunt once manifest-scoped.** Blunt only if left as a blanket grep.

---

## TASK 2 — SCOPE (D-73 net-gating): is H3 cfg-atof net-gating for `.E.0.1`?

**The net-gating question (D-73):** fix ONLY what the no-reintroduction NET (CI/tests on the *current* codebase) is meaningless without. Everything else routes PRE-PAPER-TEST behind the guard. So: **does `.E.0.1`'s golden-master/characterization actually DEPEND on cross-locale cfg-parse immunity?**

**Reason from what the golden-master diffs:**
- `.E.0.1`'s determinism guarantee = freeze the REAL output of the FP path + backtest/depth replay, diff under CI. The golden-master is produced by *replaying recorded tick/depth CSVs* and checking byte-identical engine output (per `feedback_golden_master_over_reimplemented_oracle`, D-74).
- That pipeline's locale-sensitive surfaces are: **recorder EMIT** (`%f`) → **replay PARSE** (`strtod`/`parse_double_fast`). This is GT-NEW-1's closed loop. If either end is locale-fragile, the golden bytes differ across locales → the net is a **lie** (passes on the dev box's C locale, would diverge on a de_DE box). **This is exactly what the net is meaningless without.**
- cfg-parse (`ControllerConfig_Load`) feeds the run *configuration* (thresholds, risk_pct, fee_rate…). The net DOES call it (GT4: controller_test.cpp:35, parity_harness.cpp:115). BUT: the CI runs under a **fixed locale** (C). Under fixed-C, `atof` and `from_chars` produce **identical** bytes (proven at controller_test.cpp:15209 — they match on representative values under C). So the golden-master is **byte-stable under the CI's own locale regardless of whether cfg uses atof or from_chars.** The cfg-atof fragility only manifests if the operator/CI runs under a non-C locale — which the net does not do for cfg (GT-NEW-2: no test loads cfg under de_DE).

**Therefore the dependency is asymmetric:**
- Recorder-emit + replay-parse (H2 + F-054/55): the golden bytes **change identity** if these aren't locale-immune, because the replay loop *is* the thing being characterized. **NET-GATING.**
- cfg-atof (H3): under the CI's fixed locale the golden bytes are **identical** with or without the migration. The cross-locale cfg hazard is real but the net **doesn't exercise it** and doesn't need to in order to be a truthful no-reintroduction guarantee for the FP/replay path. **NOT net-gating → PRE-PAPER-TEST behind the guard.**

### Per-finding net-gating verdict

| Finding | Net-gating for `.E.0.1`? | Reasoning |
|---|---|---|
| **H2 recorder EMIT (`%f`)** `TickRecorder.hpp:186` / `DepthRecorder.hpp:249` | **YES — net-gating** | The golden-master replays recorded CSVs; if emit is locale-tainted the recorded bytes (and thus the frozen golden) differ across locales → the net silently lies. The net is meaningless without this. Fix = wrap the recorder `fprintf` in per-thread `uselocale(C)` (sister to `CfgFieldDispatch.hpp:188`, `RunHistory.hpp:72`). Pairs with replay-parse below. |
| **Replay PARSE (F-054/55)** `DepthReplayState.hpp:224-227` bare `strtod` | **YES — net-gating** (already in plan) | Same closed loop. strtod→parse_double_fast (from_chars). Without it the parse end of the golden loop is locale-fragile. **Note: brief lists F-054/55 as "replay PARSE" but the tick path; DepthReplayState’s strtod is the DEPTH parse — verify both tick AND depth replay parse are covered, not just tick.** |
| **H3 cfg-atof** `ControllerConfig.hpp` (~35 sites) | **NO — route PRE-PAPER-TEST behind the guard** | Under CI's fixed locale, atof≡from_chars byte-for-byte (controller_test.cpp:15209). The net doesn't load cfg under a foreign locale (GT-NEW-2). Real hazard, but not what *this* net depends on. Routing it is D-73-correct, NOT effort-avoidance — provided the guard + a PRE-PAPER-TEST migration ship actually exist (see Task 3). |
| **The CI guard itself** | **PARTIAL — net-gating ONLY for the H2/replay manifest entries; the cfg-atof manifest entry is PRE-PAPER-TEST** | The guard locking-in the recorder-emit + replay-parse compliance IS net-gating (it's the no-reintroduction net for the bytes the golden depends on). The guard's cfg-atof coverage is the PRE-PAPER-TEST half. Build the guard now (it's the net mechanism for H2/replay), seed its manifest with cfg as a KNOWN-PENDING (allowlisted-with-TODO) entry so the guard ships green now and tightens when cfg migrates. |

**One caveat that could FLIP H3 to net-gating:** if any net test loads cfg under a non-C locale (it does not today, GT-NEW-2) OR if `.E.0.1` adds a cross-locale cfg-parse characterization test as part of its determinism charter, then cfg-atof becomes net-gating. **If the determinism charter intends to assert "cfg parse is locale-immune," that assertion is the net, and H3 must be fixed now.** Recommend Caramel decide: is cross-locale *cfg* immunity in `.E.0.1`'s stated guarantee, or only tick/depth replay? The honest reading of the surfaced cluster is replay-only → H3 routes.

---

## TASK 3 — Philosophy 4th-check (drift in EITHER direction)

Proposer already corrected global-setlocale→per-thread-uselocale after pushback (3rd PL-1: defaulting lighter). Checking the CURRENT re-aligned proposals for a 4th drift OR an over-correction.

### Re-aligned proposals examined
1. uselocale-wrap H2 recorder emit — **ALIGNED.** This is the structural fix (sister to existing :188 / RunHistory:72). Net-gating. Correct weight.
2. registry-migrate a *net-gating subset* of H3 — **OVER-CORRECTION RISK (the 4th drift, opposite direction).** Per Task 2, **zero** cfg fields are net-gating under fixed-C CI. So "migrate the net-gating subset" has an **empty** subset. Migrating *any* cfg field "for the net" now is migrating fields the net doesn't need → past D-73 net-gating scope, and into framework-diminishing-returns (registry-migration is the right *eventual* answer, but doing it under the `.E.0.1` correctness ship is scope-creep dressed as rigor). **The honest call: migrate NONE for `.E.0.1`; route ALL cfg-atof to a dedicated PRE-PAPER-TEST migration ship behind the guard.** If the proposer is proposing to migrate even a "subset" now, that is the over-correction — flag it.
   - Counter-check (am I wrong?): is there a *single* cfg field whose value changes the recorder/replay golden bytes? cfg feeds run config, not the recorded CSV content; the recorder writes raw tick/depth, not cfg-derived values. So no cfg field is in the golden-byte loop. Subset = ∅. Confirmed.
3. Categorical CI guard — **ALIGNED IN INTENT, mis-scoped as specced.** Building it now is correct (it's the net mechanism for H2/replay). BUT as specced (blanket grep forbidding atof/strtod/%f + global setlocale) it's simultaneously **too blunt** (false-positives on TUIAnsi/GUI/test-oracle/GUI-setlocale — Task 1) AND, if it tries to forbid cfg-atof immediately, it **forces** the over-correction in #2 (you can't ship green with 35 atof sites unless you either migrate them all NOW or allowlist them). The manifest-scoped design (Task 1) resolves both: cfg enters the manifest as KNOWN-PENDING, guard ships green, cfg migration is a separate PRE-PAPER-TEST ship. **Without the manifest design, the guard quietly drags the whole 35-field migration into `.E.0.1` — that's the trap.**
4. Field-wise fingerprint — **PROBABLE OVER-ENGINEERING for `.E.0.1`.** A per-field cfg fingerprint is a determinism asset, but if its purpose is to catch cfg-parse locale drift, Task 2 says the net doesn't depend on cfg-parse immunity yet. A whole-cfg (or whole-golden-output) hash is sufficient for the net; per-FIELD granularity is a PRE-PAPER-TEST nicety. Defer field-wise; ship coarse golden-hash now. (If field-wise fingerprint serves a *different* already-net-gating purpose — e.g. stamp-binding — that's separate; but as a cfg-locale guard it's past net-gating.)
5. Enumerated-acceptance — **ALIGNED.** Enumerating the determinism-surface set explicitly (the manifest) is exactly the discipline that catches "I assumed the rest are immune" (`feedback_enumerate_set_before_categorical_claim`, R1). This is the GOOD direction. Keep it; it IS the Task-1 discriminator.

### The honest 4th-drift / over-correction summary
- **4th PL-1 (lighter-than-implied)?** NOT in #1 (correctly heavy). Latent in #3-as-specced ONLY if the guard is left blanket and cfg gets allowlisted with no follow-up ship — that would be "convention" (a TODO comment) where the gradient wants a *scheduled structural migration*. Mitigation: the PRE-PAPER-TEST cfg-migration ship must be a real ledgered item, not a guard-suppression.
- **OVER-correction (heavier-than-net-needs)?** **YES, and this is the dominant risk this round.** #2 (migrate a "net-gating subset" — subset is empty) + #4 (field-wise fingerprint) + #3 (guard forcing the full migration now) all pull the 35-field cfg-atof migration into `.E.0.1` when D-73 says it routes PRE-PAPER-TEST. The proposer, having been pushed on going-too-light 3×, is now at risk of the symmetric error: doing the *whole* locale-hardening now because it "feels rigorous," past net-gating + into framework-diminishing-returns. **Name it: cfg-atof migration is PRE-PAPER-TEST, not `.E.0.1`. The net-gating fix is exactly two things — uselocale-wrap the recorder emit (H2) + strtod→from_chars the replay parse (F-054/55, BOTH tick and depth) — plus a manifest-scoped guard that ships green with cfg as KNOWN-PENDING.**

### Gradient-anchored bottom line
- latency: untouched (none of this is hot path).
- **determinism (the priority that's load-bearing here):** satisfied by the H2+replay-parse pair under fixed-C CI; cfg-atof is a *cross-locale* determinism asset the net doesn't yet assert.
- maintainability / structural-fix / SSoT: served by the **manifest** (SSoT discriminator) + uselocale sister-pattern reuse, NOT by an eager 35-field migration.
- D-73 net-gating: respected ONLY if cfg-atof routes out. The "migrate the net-gating subset" framing should be corrected to "the net-gating subset is empty; migrate zero now."

---

## Recommended `.E.0.1` scope (net-gating only)
1. **uselocale-wrap recorder emit** — TickRecorder.hpp:186, DepthRecorder.hpp:249 (and TradeLog.hpp:92,105 *iff* replay-fed; verify). Sister: CfgFieldDispatch.hpp:188.
2. **Replay parse → from_chars** — DepthReplayState.hpp:224-227 (depth) + the tick replay parse (verify F-054/55 covers tick path; depth strtod is a separate site I found — ensure BOTH).
3. **Manifest-scoped grep-CI guard** (`tools/check_locale_determinism.py`, the 11th check) — forbids atof/strtod/bare-`%f`-emit inside the determinism manifest only; cfg listed as KNOWN-PENDING; `setlocale` NOT policed. Class-37.
4. **Coarse golden-master hash** of replay output (not per-field).

## Routed PRE-PAPER-TEST (behind the guard, ledgered — NOT effort-avoidance)
- H3: migrate ~35 `ControllerConfig.hpp` `atof` sites to registry / from_chars; then tighten the guard manifest (remove cfg KNOWN-PENDING).
- Field-wise cfg fingerprint (if still wanted after migration).
- (Optional) cross-locale cfg-parse characterization test — the thing that would have made H3 net-gating.

---

**Auditor note on my own posture:** I defaulted skeptical and tried to *break* each proposal. The one place I could not find a heavier obligation is cfg-atof-for-the-net (the net genuinely doesn't depend on it under fixed-C). The one place I found the proposer at real risk is the symmetric over-correction. Both directions named per the task. Real file:line throughout; GT-NEW-1..5 are reproducible greps.
