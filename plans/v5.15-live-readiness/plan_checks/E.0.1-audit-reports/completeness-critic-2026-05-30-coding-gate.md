---
type: audit-report
audit_lens: completeness-critic (Stage 3.5, HARDENED /precoding-audit-gate)
ship: v5.15.5.F.4d.1.E.0.1
plan: subplans/2026-05-29-v5.15.5.F.4d.1.E.0.1-pre-E1-foundational-fix-net.md
date: 2026-05-30
engine_head: 0b841b3
verdict_scope: false-negatives uncovered by the 7 prior lenses (find-only gaps)
disposition: PRE-CODING-BLOCKING items flagged; Caramel triages (no proceed recommendation)
---

# Completeness-Critic — `.E.0.1` coding gate (false-negative sweep)

My job: surfaces NO prior lens covered. 6 probes. **3 turn up pre-coding-blocking
gaps; 1 is document-only; 2 turn up nothing (stated plainly).**

---

## PROBE 1 — CI-WIRING completeness → **BLOCKING (the biggest hole)**

The plan promises two **standing CI gates** (determinism + replay-locale) at Tier-2
(D-70 ladder). **Neither has a specified wiring mechanism.** "Wired as a standing CI
check" (plan:130, :131, :177) is *aspirational* — no lens checked whether a CI surface
exists to wire INTO.

Ground truth of this repo's CI surface:
- **`.github/` does NOT exist** (`find .github` → empty). There is NO GitHub-Actions CI.
- ALL mechanical enforcement = the **git pre-commit hook** (`tools/hooks/pre-commit`,
  canonical source; installed via `tools/install-git-hooks.sh`). It runs 4 checks
  (A B-Plus / B fwd-promise / C doc-rename / D tests-section) — **all doc/plan-text
  checks; ZERO build/compile/test gates.**
- The hook is **shell-dispatched per staged-file glob** — adding a gate = editing the
  versioned `tools/hooks/pre-commit` + re-running the installer (the canonical-source
  discipline is documented in the hook header).

So a "standing CI gate" here means EITHER (a) a `tools/check_*.py` (or shell) added to
the pre-commit hook glob, OR (b) a `ctest`/`build.sh` target run manually. The plan
specifies **neither**. As written, both gates are one-shot harnesses no automated
surface runs → they rot exactly like the F-057 "tested≠shipped" class this ship exists
to close. **D-70 Tier-2 "actual mechanization" is unmet without a named hook/target.**

→ **Pre-coding-blocking.** Plan must name the wiring: which file gets the gate (most
likely a new `tools/check_fp_determinism.sh` + `tools/check_replay_locale.sh` added to
`tools/hooks/pre-commit` + `install-git-hooks.sh` re-run), OR an explicit decision that
these run as `ctest`/build targets gated in `build.sh` (and then `build.sh test` is the
"CI"). Note: a *compile-and-run* gate in a pre-commit hook is a new cost class for this
repo (all 4 existing checks are fast python text-scans) — that trade-off is undecided.

---

## PROBE 2 — latency-bench gap → **BLOCKING-LITE (acceptance row is vacuous)**

The hft lens flagged `calls_graph_diff.sh` is the wrong gate. I confirm the
*replacement* the plan offers is **also non-functional as an acceptance gate**:

- Plan:179 acceptance row = "**(reuse) latency ratchet** … confirm no hot-path FP
  change → hot path UNTOUCHED." There is **NO latency ratchet tool**. `rg p99|ratchet
  tools/` → only `calls_graph_diff_baseline.txt`.
- The only latency instrument is `LATENCY_BENCH` (`main.cpp:1194`): a bare
  `fprintf(stderr, "[BENCH] tick … hot: avg/min/max …")` every 10k ticks. **Eyeball
  avg/min/max — no p99 in bench mode, no threshold, no exit code, no baseline diff.**
  It cannot pass/fail anything.
- So the plan's hot-path-purity acceptance reduces to `calls_graph_diff.sh verify`
  (orphan detector — tracks no FP/latency, per hft lens) + a human reading stderr.

**However:** F-058's `_to_fp64`/`_from_fp64` ARE on the 500ns accounting loop (hft lens),
and the change is `memcpy` (provably same instruction at `-O2+`). The *risk* is NIL.
The **gap is the acceptance LANGUAGE**, not a latency danger. → **Document-only-to-fix
IF** the plan honestly relabels the row "hot-path-untouched by construction (memcpy
lowers identically; no callgraph delta)" and **deletes the phantom "latency ratchet"
reference** (citing a tool that doesn't exist is a Class-14 fabrication in the
acceptance table). The guard-matrix H8 row already says LATENCY_BENCH-as-ratchet is
`.E.1` net-new work — so claiming "(reuse) ratchet" here is forward-borrowing a gate
that isn't built. **Blocking only as a truthfulness fix to the acceptance table.**

---

## PROBE 3 — the determinism HARNESS itself → **BLOCKING (promotion under-specified)**

`determinism-gate-seed-fp_sqrt_diff.cpp` (read in full): it's a **throwaway probe**, and
its own header line 1 says so ("Disposable runtime-confirm harness … Throwaway — lives
only in the clone"). It is a single-binary dumper: `#ifdef USE_NATIVE_128` picks a tag,
prints sqrt raw-bytes for 9 inputs to stdout. **It does NOT self-compare** — divergence
is found by a human diffing two stdout runs.

Plan:181 says it's "promoted to `tools/` (or `tests/`) as the H10 gate's kernel" — but:
- The promotion is **NOT specified concretely** (which dir; what wrapper turns a
  stdout-dumper into a pass/fail; how it gets the native-vs-generic *pair* — it's ONE
  binary per build flag, so the gate needs a 2-build harness around it).
- It **hard-codes 9 inputs**; a standing determinism gate over "all FP ops byte-identical
  EXCEPT sqrt" (the v0.2-corrected gate form, plan:44) needs the **enumerated op table**,
  not just sqrt — the file only does sqrt.
- It needs `#include <cstring>` itself (has it) — fine — but as a `tests/` citizen it
  needs a return-code contract + a driver that builds it both ways and diffs.

→ **Pre-coding-blocking.** "Promoted to tools/" must specify: (a) target path, (b) the
2-build-flag driver (shell that compiles native+generic, runs both, diffs + exits
non-zero on diff — THIS is the actual gate, the `.cpp` is just its payload), (c) whether
it expands to the full op-table or stays sqrt-scoped diagnostic (plan is internally
ambiguous: :44 wants the enumerated table, :176 wants "sqrt-scoped diagnostic, NOT
blanket all-ops"). Resolve which. Ties directly to PROBE 1 (the driver IS the wiring).

---

## PROBE 4 — Net-1 / F-059 seam → **BLOCKING (Net-1 has no plan; seam is to a void)**

`.E.0.1` makes a hard forward-promise: "deterministic replay (F-054/55) is the
PRECONDITION for the golden-master exit characterization (F-059) + all PERSIST
characterization tests" (plan:232). The seam is sound **in direction** (F-054/55 land
here; F-059 consumes them in Net-1). BUT:

- **Net-1 ("ln") has NO subplan file.** `ls subplans/ | rg net-1|characteriz|persist`
  → nothing. Net-1 exists only as prose in handoffs/postmortems ("ln PERSIST GREEN —
  not started"). The apparatus-complete DoD that gates `.E.1` lists "ln GREEN" as a peer
  gate to `.E.0.1` — **but ln is undrafted.**
- Consequence: this ship's outbound seam points at an artifact that doesn't exist yet,
  so the seam can't be *verified* (the rolling-window §5 contract: "verify N satisfies
  successor" is unrunnable when N+1 isn't drafted). The ORDERING is fine (`.E.0.1`
  first); the **seam-verification is deferred to a plan that must be written before
  `.E.1` releases**. Not blocking THIS ship's *code*, but **blocking the
  apparatus-complete DoD** — flag so it isn't silently assumed satisfied.

→ **Document-now / blocks-DoD-not-code.** No code reordering needed in `.E.0.1`. But the
plan should state explicitly that F-059 + the ln plan are unwritten and that ln is a
hard predecessor-gate to `.E.1` that this ship does NOT itself satisfy.

---

## PROBE 5 — F-076 / F-107 routing soundness → **BLOCKING (F-076 is mis-routed + double-claimed)**

This is a real false-negative the find-only lenses missed: **the v0.2 plan body
CONTRADICTS its own audit synthesis on F-076, and F-076 is claimed by TWO ships.**

- v0.2 plan:48 routes F-076 OUT → `.E.0.3`, "Net-gating only if Net-1 golden-masters the
  fingerprint."
- The ship's **own fresh-audits synthesis** (`E.0.1-audit-reports/2026-05-29-…-synthesis.md`)
  says the OPPOSITE, **5× CONFIRMED**: "**Fold H1 (F-076) … into `.E.0.1` — net-gating
  per the ship's own premise**" (synth:98). parity-quorum-**B** and -**C** both verdict
  **RED → FOLD**; quorum-C calls the "fold IF Net-1 characterizes" disposition an
  **inversion of cause and effect** ("It IS the H9/H12 break, and this ship's charter is
  exactly the determinism cluster — MUST FOLD").
- **Empirical evidence in-hand** (synth): two identical-VALUE configs in differently-
  dirtied buffers → **16,961/68,224 differing hash bytes**; copy-assign still leaves 9 →
  a `_Default` memset is insufficient; consumer is concrete and partly **fatal**
  (`CoreModelZoo:2239 ComputeBundleId` → fatal compare) → trained-model lineage.
- **Closed-loop coupling the routing breaks:** synth:118 ground-truth — F-076 + the
  H2 recorder-emit (`DepthRecorder:249 %.8f`) + F-054/55-parse (`DepthReplayState:224-227`)
  are "the SAME closed loop … **must ship together**." Routing F-076 to `.E.0.3` splits a
  loop the synthesis says is atomic.
- **Double-claim:** F-076 ALSO appears in the `.E.0.3` plan scope (`E.0.3:38` —
  `Fingerprint_Canonicalize` helper). So it's simultaneously "routed to `.E.0.3`" (here)
  AND "owned by `.E.0.3`" (there) — but its GATING condition ("if Net-1 golden-masters
  the fingerprint") is **undecidable because Net-1 is undrafted** (PROBE 4). A finding
  parked on an unwritten plan's behavior is a silent HOLE.

→ **Pre-coding-blocking — the single most important triage item.** The plan's F-076
disposition was REFUTED by its own quorum but the v0.2 body wasn't reconciled to the
synthesis. Caramel must decide FOLD-here (audit consensus + closed-loop argument +
empirical) vs keep-routed (the v0.2 body) — but it **cannot stay "route IF Net-1…"**
because Net-1 doesn't exist. If folded, the recorder-emit H2 item (already IN v0.2:39)
+ F-054/55 + F-076 ship as the one loop the synthesis demands.

**F-107 routing IS sound** — output-only (calib/trade-log emit), doesn't feed the
net/replay; no lens or evidence contradicts PRE-PAPER-TEST. (Minor: plan:165 + R-rows
still cite `tt::format_double_canonical` which the synthesis L4 flags as **non-existent /
Class-14** — reword to the actual inline emit-pin. Document-only.)

---

## PROBE 6 — does `.E.0.1` close the H10 guard-matrix HOLE for `.E.1`'s DoD? → **PARTIAL (residual convention-only surface)**

H10 (matrix:98) = "SIMD scalar fallback byte-identical" → **HOLE → determinism gate.**
`.E.0.1` closes it **for the FP-op path** (native specialization set made deterministic;
the determinism gate enforces native≡generic-except-sqrt). That IS real H10 closure for
the surface `.E.1` touches. **But two residuals leave H10 convention-only in part:**

1. **The gate's enforcement is only as real as PROBE 1+3 make it.** If the determinism
   harness isn't promoted to an auto-run pass/fail gate, H10 goes from HOLE →
   **convention-only**, not → ENFORCED. The matrix would mis-record ENFORCED.
2. **AVX-512 SIMD kernels** (H10's literal text) are NOT in this ship's scope — `.E.0.1`
   covers `FPN<64>` scalar native-vs-generic, not the AVX-512-vs-scalar-fallback kernels
   H10 was originally written for. If `.E.1` touches no AVX-512 path, fine; but the
   matrix H10 row will read "closed by `.E.0.1` determinism gate" while the SIMD-kernel
   half is untouched. → the row needs a **scoped status** ("FP-op path ENFORCED;
   AVX-512-kernel fallback still TBD") not a blanket ENFORCED, or `.E.1`'s
   no-HOLE-for-touched-surfaces DoD silently over-claims.

→ **Document-only** (the matrix-row precision), **conditional on PROBE 1+3** (the
enforcement reality). No residual *FP-determinism* surface is left convention-only by the
fixes themselves — only by the un-wired gate.

---

## PROBES THAT TURNED UP NOTHING (stated plainly)

- The **F-054/55 read-side ↔ recorder-emit write-side loop** is already closed in v0.2
  (the recorder-emit H2 item is IN scope at plan:39) — no gap there beyond the F-076
  coupling (PROBE 5).
- **F-107 → PRE-PAPER-TEST** routing: sound; no contradicting evidence (PROBE 5 tail).

---

## Triage summary (Caramel decides; no proceed recommendation)

| # | Uncovered surface | Where | Blocking? |
|---|---|---|---|
| P5 | **F-076 mis-routed** — v0.2 body says route-to-`.E.0.3`; own synthesis (5×) + quorum-B/C say FOLD; closed-loop with F-054/55+recorder; gating cond. undecidable (Net-1 undrafted); double-claimed by `.E.0.3:38` | plan:48 vs synth:98/118; `E.0.3:38` | **PRE-CODING-BLOCKING** |
| P1 | **Both standing CI gates have no wiring mechanism** — no `.github/`; only surface is `tools/hooks/pre-commit` (4 text-checks, 0 build/test gates); plan says "wired" without naming the hook/target | plan:130/131/177; `tools/hooks/pre-commit` | **PRE-CODING-BLOCKING** |
| P3 | **Determinism harness promotion under-specified** — `.cpp` is a throwaway stdout-dumper (self-says "disposable"), no self-compare, sqrt-only, hard-coded inputs; "promoted to tools/" names no path/driver/op-scope; internally ambiguous (full table vs sqrt-scoped) | plan:181 vs :44 vs :176; harness file hdr | **PRE-CODING-BLOCKING** |
| P2 | **"latency ratchet" acceptance row cites a non-existent tool** — LATENCY_BENCH is eyeball avg/min/max (`main.cpp:1194`), no p99/threshold/exit; risk NIL (memcpy) but the row is a Class-14 acceptance fabrication | plan:179; `main.cpp:1194` | **BLOCKING-as-truthfulness** (relabel + drop phantom tool) |
| P4 | **Net-1 ("ln") has no plan file** — outbound seam + F-059 precondition point at an undrafted artifact; ln gates `.E.1` DoD but is unwritten; ordering fine, seam unverifiable | `ls subplans/`; plan:232 | **DOCUMENT-NOW / blocks-`.E.1`-DoD not this code** |
| P6 | **H10 matrix row over-claims if gate un-wired + AVX-512 half untouched** — needs scoped status, not blanket ENFORCED | matrix:98 | **DOCUMENT-ONLY** (cond. on P1+P3) |
| — | F-107 PRE-PAPER-TEST routing | plan:165 | sound (minor: drop `format_double_canonical` Class-14 cite) |

**The through-line:** find-only lenses verified each fix *achieves its goal*; they did
NOT verify the **gates that make the fixes STANDING actually attach to a running CI
surface** (P1/P3), nor that the **finding-routing matches the ship's own audit
consensus** (P5). Those are the false-negatives. P1+P3+P5 should be reconciled in the
plan body BEFORE coding; P2/P4/P6 are truth-in-labeling fixes.
