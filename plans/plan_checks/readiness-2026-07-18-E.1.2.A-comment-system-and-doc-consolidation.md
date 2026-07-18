# /readiness report — E.1.2.A comment-system-and-doc-consolidation — 2026-07-18

**Scope of this pass:** coding-readiness for the NEXT ACTION — **C4 DERIVED-write increment-1 step-1**
(extend `tools/check_cache_layout.py` `refresh_derived` to INSERT `[SIZE]`/`[ALIGN]`/`[CACHE_LINES]`/`[STRADDLE]`
into an EMPTY `[DERIVED]` block, + a calibration selftest). Full ceremony (operator: *"correctness critical, it is the toolchain"*).

## What we already have (Stage 0 preamble)
- **Migration contract (D-349):** Python authoritative; `foxtag update` is a later parity-gated cutover. → step-1 goes in `check_cache_layout.py`, NOT foxtag. ✅ correct target.
- **Calibration-corpus discipline (D-362):** every guard ships a golden-broken + golden-complete selftest; fixtures SYNTHETIC/frozen. → the change ships WITH a selftest.
- **D-327 WRITTEN-vs-LIVE-PREVIEW:** STRUCT layout (`SIZE`/`ALIGN`/`CACHE_LINES`/`STRADDLE`) is the WRITTEN set (Itanium-ABI-fixed, `--fix`-owned); the codegen quartet (instr/SIMD/branches) is LIVE-PREVIEW-only, NEVER written. → the insert writes ONLY the layout quartet.
- **Anti-pattern in play:** Class 51 (vacuously-green guard) — the selftest is its structural prevention. Class 18 (parallel mirror) — extend the ONE tool, don't re-parse.
- **Invariants:** engine H1–H22 do NOT govern the dev-plane; the tool ENFORCES H6 (cross-thread straddle) / H12 (padding) / H21 (never reorder a serialized struct — writer touches ONLY comment tags).

## Standard checklist (dev-plane, comments-emitting Python tool, 1 file)
| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot-path purity | PASS | dev-plane; no engine hot path touched |
| 2 | Train-serve parity | PASS | N/A |
| 3 | Surface area | PASS | 1 tool file + selftest fixture |
| 4 | Heap/pointer lifecycle | PASS | Python |
| 5 | Backward compat | PASS | writes comment tags; no wire/snapshot version; `[DERIVED]` is non-persisted comments |
| 6 | Multi-threading | PASS | N/A |
| 7 | Test coverage | **GAP-if-omitted** | the calibration selftest IS the deliverable (see Gate 4) |
| 8 | Docs + invariants | PASS (minor) | `--fix` now inserts — a one-line `DOCS/TOOLS.md` note is worth it |
| 9 | Forward maintenance | PASS | this IS the forward-maintenance mechanism (the 1:1 DERIVED writer) |
| 10 | Rollback | PASS | git; single tool file |

Cold-pickup C.1–C.10: **GREEN** — branch (`feat/v5.15-live-readiness`), first move (`refresh_derived`), fn names + file:line (`check_cache_layout.py:134-162`), and the calibration home (`tests/schema_golden/`) are all cited + verified present.

## Dependency verification
| Claimed | Verified | Notes |
|---|---|---|
| `check_cache_layout.py` `refresh_derived` @ ~134-162 | ✅ exact | read; only `re.sub`-rewrites EXISTING tag-lines (line 151) |
| existing `run_selftest` refresh fixture | ✅ @ 191-196 | the selftest to EXTEND for the insert case |
| empty `[DERIVED]` insert targets | ✅ widespread | 324 `[STRUCT]` blocks, 81 populated `[SIZE]` → ~243 empty (e.g. `Backtest/LabelFunctions.hpp:54`) |
| `tests/schema_golden/` calibration home | ✅ 5 fixtures | golden-COMPLETE dogfood set present |
| category-set fence has SIZE/ALIGN/CACHE_LINES/STRADDLE | ✅ schema:153 | round-trip gate ground truth |
| STRUCT DERIVED axis order | ✅ schema:81 | `SIZE · ALIGN · CACHE_LINES · STRADDLE · ALIGNED_CONSUMERS · THREAD` |

## The 6 correctness gates (the teeth) — verified against real code
| # | Gate | Verdict | Finding |
|---|------|---------|---------|
| 1 | **Round-trip** — inserted tags re-parse clean through the validator | ✅ PASS | all 4 categories are in the schema `category-set` fence (schema:153); `// [SIZE]_[64B]` etc. satisfy one-category-per-line (`64B` is a value, not a category) |
| 2 | **Idempotency** — `--fix` ×2 = 0 new changes | ⚠️ **MUST-VERIFY (the one real finding)** | the current rewrite is idempotent; a NAIVE insert is NOT — a second run inserts duplicate `[SIZE]` lines (the FPN non-idempotent `--apply` → "FPN_Binary_Binary" class). Implementation MUST detect present-vs-absent: present → rewrite; absent → insert-once. Selftest MUST assert run-twice → 0 changes. |
| 3 | **H21/H12 boundary** — only comment tags touched, never field reorder | ✅ PASS by construction | `refresh_derived` edits only `TAG_LINE_RE`-matching `// [...]` comment lines; `[DERIVED]` sits in the comment region below `[END_CODE]`; the insert anchors to the `[DERIVED]` comment line, never an offset into code |
| 4 | **Selftest non-vacuity** — golden-broken FLAGGED + golden-complete CLEAN | ⚠️ REQUIRED DELIVERABLE | extend `run_selftest`: (a) empty `[DERIVED]` + mock layout → tags INSERTED (n==4); (b) run again → 0 changes (idempotency); (c) struct absent from layout → NO insert (skip) |
| 5 | **Coverage-boundedness (D-363)** — unavailable-layout structs SKIPPED, not filled wrong | ✅ PASS-if-preserved | `match_layout` returns None when absent → keep the insert INSIDE the `cur is not None` gate. Naturally satisfied: step-1 alone changes 0 real Backtest structs until step-2's probe TU makes layout available (the two-diagnosis point) |
| 6 | **Ladder/section order preserved** | ✅ PASS | insert in canonical order SIZE·ALIGN·CACHE_LINES·STRADDLE (matches the existing dict); anchor between `[DERIVED]` and its closing `====` bar; write ONLY the WRITTEN layout subset, never the codegen quartet (D-327) |

## VERDICT: 🟢 GREEN — start coding

Every dependency exists, the mechanism is confirmed against real code, and 5 of 6 correctness gates pass by construction or with a named preservation. GREEN is gated on a sharp **definition-of-done**, not a pre-fix:

### Must land IN the implementation (the DoD)
1. **Idempotency guard** (Gate 2) — present-or-insert logic; a 2nd `--fix` yields 0 changes. This is THE correctness property; a non-idempotent writer run in CI corrupts on every commit.
2. **Calibration selftest** (Gate 4) — insert + idempotency + skip-on-absent assertions, shipped in the same commit (non-vacuity discipline).
3. **Layout-availability gate** (Gate 5) — insert only when `cur is not None`; never write empty/garbage facts.
4. **Canonical order + WRITTEN-subset-only** (Gate 6, D-327) — SIZE·ALIGN·CACHE_LINES·STRADDLE; never the codegen quartet.

### Worth doing during coding
- One-line `DOCS/TOOLS.md` note that `--fix` now inserts (not only rewrites).

### Acceptable / not-blocking
- step-1 lands the CAPABILITY; the ~243 real empty-`[DERIVED]` Backtest/ML structs stay empty until step-2 (probe TU) — expected, not a gap.

## Post-verify map notes
- No new `Pattern_FunctionName` (Python tool) → no CODE_MAP regen needed for the change.
- After step-1+step-2 fill the corpus, re-run the cache-layout HARD gate — a NEW cross-thread straddle is a genuine H6 finding to triage (step-3 / §2c).
