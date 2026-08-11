---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt (operator directive 2026-08-10: keep every agent report under reports/<directive>/<task>; the orchestrator is the single writer — investigation agents stay read-only)
directive: AR-8 compensator — adversarial review of E.1.2.B leaves 2/3 (the close's declared-PARTIAL row)
agent_class: a-class
delivered: 2026-08-10 (pickup session)
disposition_register: ../../plan_checks/2026-08-10-D414-toolchain-sweep-finding-register.md § "AR-8 COMPENSATOR PAID"
---

# ADVERSARIAL REVIEW VERDICT — E.1.2.B leaves 2/3 (D-413/D-414 arc) — VERBATIM

Scope reviewed: engine `1cdc9a1`/`fefdac1` (committed state; uncommitted Notify.hpp edit excluded), workspace `7f5b51b`/`5afeb31`, plugin `82aacce`/`fb8e3f3`. All teeth re-run by me with direct rc capture. Two of the arc's own PreToolUse guards (`block_rg_r_typo`, `block_pipe_rc_read`) fired on my own commands during this audit — the M7 dividend is live.

## Per-claim verdicts

**Claim 1 — tri-state detector / bound math: UPHELD.** `recordlayout.lua` (`M.straddlers`, ~:143-175). The veto is dead — resolved hits append unconditionally; the MixedVeto tooth (`tests/test_recordlayout.lua:113-116,130-132`) genuinely fails if the veto returns. Bound math sound in the adversarial direction: `bound = nxt.off − f.off` (record `size − off` at tail) is a valid upper bound because depth-1 C++ members never overlap — a false-PROVEN-CLEAN would require overlapping members; unions collapse to `bound ≤ 0` → unverified (conservative). Missing-size, off≥size (the `tt::Partial` degenerate fixture), and zero-size all land conservative. Last-field bound includes tail padding — still valid (a field never extends into its own trailing padding). Boundary-touch (`off+bound-1` on the line edge) correctly not a straddle. ABI table values (mutex 40 / cond 48 / tid 8 / thread 8 / time_t 8 / sig 4) compiler-pinned by the probe tooth (skip-advisory sans clang++, honestly printed). 45/45 reproduced, rc=0.

**Claim 2 — gate/writer: UPHELD.** `check_cache_layout.py`. `[STRADDLE_EXEMPT]` parse takes the field-name token per struct block (:77-80) — blanket-struct structurally inert. `gate_struct` partial branch (:148-156) reds `straddle-unverified` unless exempt; **size-drift sits OUTSIDE the cross_thread branch (:165-169) and is evaluated on partial records** — holds by code, though no selftest leg combined partial+size-drift (tooth gap, LOW). `_fmt_straddle` (:183-190) composes hits + `unverified:` and returns `none` only when both empty — pinned by tooth (i). `--selftest` re-run: 20/20 green rc=0, each new tooth fail-capable.

**Claim 3 — exemption inventory: UPHELD on substance; the tally is wrong.** Six groups (≈17 of the actual 24 tags) spot-verified against code — **no false reason found; the highest-severity target of this review came up empty**:
- `NotifyState.cond` — TRUE: `pthread_cond_signal` under the lock at both sites (`Notify.hpp:350,378`), worker waits under lock; every cond access lock-serialized; monitoring plane.
- `ControllerConfig` ×6 — TRUE: sole steady-state writer is the operator-triggered reload `cfg = new_cfg` (`Async.hpp:~350`); no per-tick writers of the six fields; the reason honestly cross-refs the torn-READ hazard to NEW-hole-6/E.1.3 instead of laundering it.
- `TUISnapshot`/`PerNodeSnap` — TRUE: writer fills the back buffer via `TUISnapshot_Publish_Begin/End`, reader is a whole-struct copy (`EngineTUI.hpp:1594-1607`); no in-place field readers outside the helpers.
- `DepthSharedState.snapshots` — TRUE: writer touches `snapshots[back]` only, RELEASE `active_idx` flip (`BinanceDepth.hpp:397-407`).
- `OrderManagerState` ×4 — TRUE: Money is bare `__int128` (`FixedPointN.hpp:77`) → alignof 16 → 16B elements at 16-multiples cannot cross a 64B line; `orders[]` drainer-only in place (`exchange_id` written drainer-side at `OrderManager.hpp:1706` from the SPSC-carried by-value result; GUI reads only the observability atomics).
- `CandleAccumulator` — TRUE: all four access fns lock (`CandleAccumulator.hpp:128,188,268,308`).

FIND (LOW, wrong-tally): fefdac1's message says "20 field-level tags"; the diff adds **23**, corpus total at fefdac1 is **24** (incl. leaf-2's `bucket_count`). "Across 13 armed structs" also imprecise (spans 10 structs; 3 pre-armed).

**Claim 4 — SHRINK-ONLY baseline: PARTIALLY REFUTED.** The two *named* directions are enforced (:584-610): removed-key-reappears → NEW → rc 1; new finding → rc 1. Live: `--strict-new` rc=0, "0 NEW; 4 grandfathered". `--emit-baseline` manual-only (not self-blessing). **But "SHRINK-ONLY actually enforced" is FALSE as a file property**: nothing polices growth (wholesale re-bless has no diff-vs-old guard) and nothing reports orphan keys — a FIXED finding's stale key silently grandfathers any future regression of the same field **forever** (ratchet with no pawl). The cited Class-44-orphan/H21-ledger sister has lockstep enforcement; this has an intent comment. MED. Also: strict-new logic has no selftest tooth (the RED proof was one-shot live).

**Claim 5 — discriminator ORIENT-TIER-ONLY: PARTIALLY REFUTED — the headline kill-claim fails at its own motivating site.** Upheld: in-CODE `[THREAD]` neither arms nor disarms (code :69-76, tooth j, probes); zero armed-set delta TRUE (census of `4c076ed`: **zero** in-CODE `[THREAD]` tags corpus-wide); `Order.hpp:211` unarmed CORRECT (drainer-only traced). **Refuted: "last-line-wins fragility dead."** Dead only *across* the tier boundary; *within* the orient tier the overwrite survives, and the corpus contains the live fragile shape — per-REGION `[THREAD]` lines: **OrderManagerState (5 orient lines, 1 single-role — the register's own motivating site, still armed only by line order)** and **ExecutionCore (3 lines, armed today only because the 2-role line happens to be last)** (`OrderManager.hpp:263-283`, `ExecutionCore.hpp:52-61`; SPSCRing order-insensitive, all lines 2-role). Proven with the real parser: reordering REGION groups flips `cross_thread → False` silently. No tooth covers multi-orient-line blocks. The simpler/safer option was in their own register text ("orient-tier-only **or any-line-≥2**"): an OR-fold is one line, order-insensitive, loses no use case. **MED-HIGH — a cosmetic doc reorder silently disarms H6 policing on the OMS and hot-path structs.**

**Claim 6 — Check T park: UPHELD.** `.githooks/pre-commit:315-341`: default path prints PARKED and never invokes `parity_check.sh`; `FOXTAG_REARM=1` restores the full original gate. Nit: "same commit as the detector fix" cross-repo-imprecise (plugin 17:30 vs workspace 17:38); the 8-minute window contained no toolchain-staged commit — negligible.

## New holes (register vocabulary)

1. **Orient-tier last-line-wins ALIVE** (MED-HIGH → OPEN-leaf-3-residual): fix = OR-fold + multi-orient-line tooth; ExecutionCore + OrderManagerState exposed.
2. **Baseline growth/orphan unenforced** (MED → OPEN, gate plane): shrink-check (new ⊆ committed) + orphan-key report.
3. **HARD-row scope overclaim** (MED, doc-truth): "REDs any commit" true only main-TU-visible; 9/13 baseline keys + 75-unpoliced ride ADVISORY; `--isolate` in no standing row.
4. **`[STRADDLE_EXEMPT]` tier asymmetry + no field-existence validation** (LOW): honored anywhere incl. `[CODE]`; typo'd exemptions rot silently (current 24 all orient-tier + name-correct).
5. **Wrong tallies** (LOW): 23-not-20 (fefdac1), 21-not-22 files; the "27 fabricated none" figure EXACT.
6. **Selftest tooth gaps** (LOW): partial+size-drift · strict-new/baseline matching · tri-state round-trip.

## Overall

**Leaves 2/3 substantially STAND.** The fact-core (detector, bound math, emitter, writer, gate, park) is sound and its teeth are real; the exemption inventory survived a hostile spot-check with zero false reasons — no silenced real H6 hazard exists. The two refuted sub-claims are both in the leaf-3 arming/ratchet plane — neither invalidates landed facts, but both leave silent-disarm / silent-grandfather paths open in exactly the failure family this arc set out to close, and both have one-line-scale fixes named above.

---
*Post-script (orchestrator): all four holes CLOSED same session at workspace `6df91fa` — see the D-414 register § AR-8 COMPENSATOR PAID.*
