# Class 57 — Emit-boundary honesty flattening (an honest partial/unknown/error state collapsed to a clean default at a seam)

> Codified 2026-08-10 during the D-413/D-414 derived-facts integrity arc (founding instance: the operator-caught NotifyState `[STRADDLE]_[none]`). Severity HIGH; 22 load-bearing sites in the founding census + 3 pipe-swallow bites (one inside a gate). Sisters: `meta-disciplines/calibration-corpus-non-vacuity-discipline.md` · `meta-disciplines/differential-to-absolute-gate-contract-widening.md` · Class 51 (vacuously-green guard) · Class 56 (writer idempotency). Per-class file per file-size-split-discipline.

**A fact-producer computes an honest partial / unknown / error state, and a downstream boundary
flattens it into a clean default — so the consumer cannot distinguish "verified none" from
"couldn't verify".** The producer was honest; the SEAM lies. One flattened emit poisons every
consumer (one-producer-N-consumers), and the corpus then carries fabricated-verified facts *at
rest* (the D-413 founding instance: `recordlayout.lua` returned `{report, partial=N}` — honest —
while `emit_record_layout.lua:66` emitted `straddlers or {}`, and `check_cache_layout --fix`
wrote a durable `[STRADDLE]_[none]` for a record the detector could NOT verify; both parity
backends AGREED on the wrong answer — agreement is not validity).

## Sub-shapes (one class, five spellings)

- **A. Flattened-partial** — `or {}` / `.get(x, [])` / `except: pass` on a FACT value; the
  honest `partial`/`unresolved` marker dies at the emit seam. (D-413 founding instance; the
  foxtag C++ port never had the marker at all.)
- **B. rc-swallow at a seam** — `out, _ = run(...)` discards the exit code; a crashed producer's
  partial output parses as truth (the `inventory()` index-laundering loop, F2).
- **C. Counted-but-not-gated** — a coverage/failure counter computed and printed but never
  reaching the verdict/exit-code (the E.1.0 "decorative div-gate"; the pre-leaf-1 "Checked N …
  all clean" counting unpoliced blocks).
- **D. Pipe-swallow `$?`** — `cmd | tail; echo $?` reads the LAST pipe stage's rc (always 0),
  converting a RED verdict into green. **THREE live bites in one arc, one INSIDE a gate**
  (hook Check A via `python | tee`; the D-414 auditor's own RED-proof reads, twice) — recurring
  DESPITE codified knowledge ⇒ M7-escalated to a PreToolUse hook
  (`tools/hooks/block_pipe_rc_read.sh`), sister to `block_rg_r_typo.sh`.
- **E. Silent-empty-input** — a gate iterating a discovered corpus PASSES vacuously when
  discovery itself failed (the B-Plus `2>/dev/null … || true` scope enumeration, F6;
  `calibration-corpus-non-vacuity-discipline` is the standing counter-doctrine).

## Detection signatures

```
rg -n "or \{\}|or \[\]|or ''" tools/ --type py --type lua     # on FACT variables, not display
rg -n ", _ = _?run|out, _ =" tools/*.py                        # rc discarded at a seam
rg -n '\|\s*(tail|tee|head|grep)[^|]*;\s*.*\$\?' tools/*.sh    # pipe then $? (no pipestatus)
rg -n "2>/dev/null.*\|\| true" tools/*.sh                      # enumerator failure flattened
```
Then TRACE: does the flattened value feed a WRITTEN fact, a gate verdict, or a report a human
trusts? Only load-bearing flows are instances.

## Structural fix

Refusal ≠ empty: a failed run returns **None/refuses** (never `{}`-as-facts); partial states
propagate END-TO-END (the written fact distinguishes `none` from `unverified:`); coverage
counters reach the VERDICT LINE (policed/unpoliced split; could-not-run row demotion; the sweep
verdict carries a COULD-NOT-RUN count); rc captured directly (`cmd > log 2>&1; RC=$?`) or via
`PIPESTATUS`. Teeth must pin the REFUSAL direction — the pre-fix teeth PINNED THE FLATTEN
(`test_foxtag_client` asserted `== {}` on failure; `test_recordlayout` asserted "Partial
excluded") and would have defended the bug against its fix.

## False-positive surface (M3)

- **Cosmetic/display fallbacks are LEGITIMATE** — `or {}` on a render-only value (a HUD label,
  a tooltip) flattens presentation, not facts.
- **Flatten-toward-STRICTER is the honest direction** — B-Plus's own two `except` handlers
  degrade toward failing-the-check; that is refusal, not flattening (cite as the in-repo
  counter-example).
- **A documented-refusal seam** (`codegen()` → None) is the FIX shape, not an instance.
- Pipelines that consult `PIPESTATUS`/`pipestatus` are correct; only bare `$?` after a pipe is
  the D sub-shape.

## Instances (2026-08-09/10 sweep — the founding census)

22 load-bearing sites (I-4 report, D-414 register): F1/F2/F3 HIGH (layout partial-flatten ×2
producers + index-laundering + clang-rc-blind) · F4-F11 MED (aggregator ✅-over-warnings,
capital-audit crash-as-coverage-claim, B-Plus empty-enumerator, isolate M-of-N, except-continue
cohort ×10, Python empty-corpus asymmetry, LSP-err ≡ zero-writers) · pipe-swallow ×3.
Closures: leaf 1/1b/2/3 (register `plan_checks/2026-08-10-D414-toolchain-sweep-finding-register.md`).
