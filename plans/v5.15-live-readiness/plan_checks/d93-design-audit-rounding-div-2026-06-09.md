---
type: design-audit-report
doc_kind: D-93 new-function design audit — cluster #4 (rounding helper) + #7 (decimal Div)
ship: "#11 Ship B (decimal money) — v5.15.5.F.4d.1.E money-numeric-core foundation"
sprint: v5.15-live-readiness
created: 2026-06-09
audited_at_head: 0e48150 (v5.15.5.F.4d.1.E.0.8)
inputs:
  - subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md (v0.4; #4 row :131, #7 row :134, S-rows :248-254, acceptance :354)
  - subplans/2026-05-31-v5.15.5.F.4d.1.E-11-new-function-designs.md (#4 :47-54; #7 stub :20-22)
  - plan_checks/2026-06-01-11-phase1-divmul-proof/ (PROOF.md + decimal_oracle.py)
  - plan_checks/2026-06-09-ship-b-money-fresh-audits-synthesis.md (S-9/S-17/S-19) + dod F2 + merge-scan five-consumers row
decision_log: decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md (D-105/D-109/D-128/D-147/D-170/D-173 audited-against)
status: COMPLETE — verdicts + required design additions below; NO code/plan edits made (Layer 2)
---

# D-93 design audit — #4 rounding helper + #7 decimal Div (2026-06-09)

Default-skeptical audit of the DESIGNS as written. Every referenced code claim re-read at HEAD 0e48150. Verdict vocabulary: DESIGN-OK / DESIGN-GAP (decision required before code) / DESIGN-WRONG.

## Verdicts

### Q1 — #4 sign handling + ceil single-sourcing → SPLIT: half-even OK; ceil variant 2 GAPS

- **Half-even sign: DESIGN-OK.** Pinned in the sidecar (#4: "Operates on the unsigned (q,r) magnitude from #3; sign reapplied after (from #2)"). Value-symmetric for negative PnL by construction: negation preserves quotient parity, and ROUND_HALF_EVEN is odd-symmetric, so magnitude-RHE + sign-out == value-RHE. The oracle's 300k signed-pair differential (`decimal_oracle.py:151-156`, A,B ∈ [−2⁶³,2⁶³)) validates exactly this composition against `Decimal` ROUND_HALF_EVEN.
- **Ceil-variant sign domain: DESIGN-GAP.** Magnitude-`(r!=0)` + sign-out = round-AWAY-FROM-ZERO on negatives; the oracle's `oracle_fee_roundup` uses `ROUND_CEILING` (toward +∞) — they DISAGREE on any negative input (engine(−2.3)=−3 vs oracle −2). Fees are nonneg by construction (notional≥0, rate≥0), which is why this is latent — but the design pins neither the nonneg precondition nor signed semantics. Required: pin fee-variant domain = nonneg (guard/flag on negative ingress) OR define signed semantics; align the oracle.
- **Ceil single-sourcing: DESIGN-GAP (decision-fold miss, the D-172c shape).** The confinement IS decided at the plan layer — S-19/dod-F2: "mode baked: half-even default; round-UP ONLY inside `Money_FeeCompute`; … one `(q,r)` round core, five consumers" + grep-CI — but the sidecar #4 section (written 2026-05-31, pre-v0.4) carries none of it: it lists three modes with no confinement structure. As written, an implementer would plausibly expose `mode` as a public parameter — every call site could pick ceil, defeating D-105 uniformity. Required fold: mode is NOT a parameter of the public surface; three named entry points (internal half-even reduce inside Mul/Div · ceil ONLY inside `Money_FeeCompute` · truncate ONLY inside quantize), one shared `(q,r)` core, five enumerated consumers (merge-scan row: decimal Mul/Div reduce, `Fee_Apply`, #5 >8dp defensive, #6 round-to-step, boundary casts), + the grep-CI line.

### Q2 — 2r overflow under the #7 generalization → DESIGN-GAP (premise verified; silent-wrong-rounding class)

#4's "no overflow" note is mul-only reasoning (`2r < 2·SCALE` ~28 bits). The #7 generalization ("2r vs DIVISOR") is asserted in both the stub (:22) and the plan (#7 row :134) with NO overflow re-derivation. Worked bound: r < b_mag ≤ 2¹²⁷ (|INT128_MIN| edge) ⇒ 2r ≤ 2¹²⁸−2 — fits **unsigned** __int128 only; in signed __int128, r ≥ 2¹²⁶ makes `2r` UB (silent wrong rounding; UBSan lane would catch in test, not in a prod build). Under a 2⁶³ operand-domain pin (Q5), 2r < 2⁶⁴ is trivially safe — but the design states no domain either. Required (pick one, recommend (b)):
- (a) Pin ALL magnitude arithmetic unsigned __int128 end-to-end (#2/#3 already are; extend the statement to #4/#7) + state the r < 2¹²⁷ precondition.
- (b) **Adopt the overflow-free form: `half = d>>1; up = (r > half) | ((r == half) & (~d & 1) & tie_rule)`** — exact for all d (d odd ⇒ 2r>d ⇔ r>half and ties impossible; d even ⇒ tie ⇔ r==half), no widening, no edge class, and it UNIFIES the SCALE case so the single-source helper has ONE body for #3 and #7 — D-105 uniformity by construction. Corollary for oracle rows: divisor ties exist ONLY for even divisors.
Also: `q+round_up` at q = 2¹²⁷−1 would overflow signed; unsigned magnitude + the Q5 domain saturate (fires at 2⁶³, far below) closes it — state the ordering (round on magnitude → domain-check → sign).

### Q3 — oracle coverage of #4 → DESIGN-GAP (and the plan's "Oracle-verified" claim is partially false)

Read `decimal_oracle.py` end-to-end:
- **Ties, positive: COVERED.** `:164-176` constructs P = q·SCALE + SCALE/2 for q ∈ [0,1000) — both parities of q. ✓
- **Ties, negative: NOT COVERED.** The tie loop is magnitude-only/positive; the signed 300k differential hits an exact tie with p ≈ 10⁻⁸×3·10⁵ ≈ 0.003 — effectively never. If the C++ deviates from abs-in/sign-out (e.g., signed q with negative r), no row catches it.
- **Venue-fee ceil variant: NOT COVERED AT ALL.** `oracle_fee_roundup` (:44-49) is defined and **never called** in `run()` — zero rows. The plan #4 row (:131) says "Oracle-verified (D-100, incl. the `2r==SCALE` ties)" — true for positive half-even ties, FALSE as a #4-coverage claim (ceil variant unexercised).
- **Div rows: absent** (acknowledged — S-9 disposition).
Required rows: negative ties (both parities, e.g. −(q·SCALE+SCALE/2) via signed mul pairs); fee-variant rows (r==0 exact, r==1 minimal, large-r, + the nonneg-domain pin per Q1); #7 Div rows per Q5/Q6 below.

### Q4 — #7 long-division shape → DESIGN-OK as a frame, 3 REQUIRED ADDITIONS

`udiv_q64` verified at `FixedPointN.hpp:1336-1346`: 256-bit remainder pair (rem_hi:rem_lo), top-128 compare, conditional-subtract (cmov), **fixed 128 trips**, MSB-first quotient; dividend hardcoded `a_mag<<64`; `b_mag==0 → all-ones (caller saturates)`. Generalization for #7: seed the remainder with the 256-bit `umul` product `a_mag·10⁸` (≤ 2¹⁵⁴ unguarded ⇒ initial rem_hi ≤ 2²⁶; ≤ 2⁹⁰ under the Q5 domain pin) instead of `(a_mag>>64, a_mag<<64)`; same 128-trip loop. **Budget OK:** identical shape to `fp2_div`, which already runs at slow/drainer cadence today; ~128 trips ≈ low-hundreds ns ≪ 100µs slow-path p99; all 4 sites are slow-path; H11 constant-trip satisfied by the fixed loop. Additions required before code:
1. **Carry the invariant proof to the new seeding** (the "certified shape generalized" claim is currently unproven for a non-power-of-2 seed): valid domain D < b·2¹²⁸ ⇒ restoring invariant (rem_top after subtract < b; after shift < 2b ≤ 2¹²⁸, no register wrap since b ≤ 2¹²⁷); overflow domain D ≥ b·2¹²⁸ ⇒ trip-0 `ge`=1 ⇒ q bit127 set ⇒ caught by the saturate (the property `fp2_div` relies on implicitly — 3 lines, must be stated).
2. **`udiv_q64` returns q ONLY — #7 needs (q, r).** Extend/extract to `udiv_qr` returning the final rem_top (r = remainder mod-DIVISOR feeding #4). A signature change to the certified primitive — name it in the design (S-19's extraction slate is the natural home).
3. State the seed-width note: under the Q5 domain pin the dividend fits 128 bits arithmetically, but keep the 256-bit certified shape (uniform, robust to domain drift).

### Q5 — quotient-overflow domain → DESIGN-GAP (required decision; the stub is silent)

Worked scaled-int math: `q_scaled = a.v·10⁸ / b.v`. With a = 10⁹ (a.v = 10¹⁷), b = 10⁻⁸ (b.v = 1): q = 10²⁵ ≈ 2⁸³ — **fits the 128-bit register, exceeds the 2⁶³ money domain** (the divmul-proof operand bound). `fp2_div`'s `of_m` saturates only at bit127 (≥ 2¹²⁷) → a 2⁸³ quotient sails through UNFLAGGED into sizing/accounting. So the guard is NOT inherited from the precedent; it must be designed:
- **Required: result-domain guard at the MONEY bound** — `|q| ≥ 2⁶³ ⇒ branchless saturate-to-domain-MAX + sticky-flag` (the S-17/dod-F1/D-147 posture: `of_mask` saturate + `__atomic_fetch_or` into the sticky flag word, FailureModeRegistry sister, boundary-checked once per cycle). Posture answer: saturate+sticky-flag, NOT hard flag-loud-and-halt inline (halt semantics live at the boundary check per D-147 Ship-B).
- **Recommended framing (closes #3 and #7 with one statement): the money-domain closure invariant** — every money op saturates its RESULT to ±(2⁶³−1) ⇒ by induction every operand of every op is in-domain ⇒ #3's magic precondition (P < 2¹²⁶ < 2¹²⁷) and #7's dividend bound hold correct-by-construction, replacing scattered per-op operand guards. Also subsumes the bit127 check (2⁶³ is stricter).
- Div-by-zero must be EXCLUDED from the same saturate path's silence (Q6 — distinct flag bit).

### Q6 — sign / div-zero / no-__udivti3 → sign OK; div-zero GAP; symbol-check mechanics GAP (false-positive verified at HEAD)

- **Sign: DESIGN-OK.** Stub pins "mirrors #2 (abs-in / sign-out)"; add the −0 canonicalization line (`fp2_div` precedent: `neg_m … & (qm != 0)`).
- **Div-by-zero: DESIGN-GAP.** Stub silent. Precedents read: `FPN_DivNoAssert` :715 = branchless safe-divisor → silent saturate-to-MAX; `FPN_DivWithAssert` :778 = debug assert + same; `udiv_q64` = all-ones → caller saturates. All 4 money sites already pre-guard zero divisors (PC:1184 `FPN_IsZero(fill_price)` return; CEL:2851 `!FPN_IsZero(entry_price)` branch; CEL:2903 peak>0 guard; CEL:3250 `!FPN_IsZero(ks_peak_balance)`), so helper-level div-zero is defensive — but the money posture must be pinned: **saturate + sticky-flag with a DISTINCT flag bit from overflow** (div-zero = logic bug, overflow = domain breach — operator triage differs). Do not replicate the NoAssert/WithAssert split: ONE money Div; the sticky flag is the loud-in-prod replacement for the debug assert.
- **no-__udivti3 mechanics: DESIGN-GAP — the acceptance as written FAILS at HEAD on a non-money site.** Verified: `FixedPointN.hpp:1603` (`FPN_FromString<64>` binary scale tail — the LIVE WS-parse path, and per S-19 the front-end #5 SHARES) computes `((unsigned __int128)frac_int << 64) / POW10[nf]` with a runtime-indexed divisor — compile-probe confirms `__udivti3` emission; it is the ONLY raw `__int128` division in production headers. A whole-binary symbol-absence check is therefore unimplementable without scoping. Required mechanics decision: (i) **probe-TU check** (compile a TU instantiating only the money op family; `nm`/`objdump` the .o for `__udivti3/__umodti3/__divti3/__modti3` relocs — recommend NOW), and (ii) disposition `:1603` explicitly — documented exemption (binary parse, pre-existing, out of Ship-B money scope) or rework (per-nf magic table) under the golden net; don't leave the acceptance row ambiguous.

### Q7 — the 4 call sites → DESIGN-OK on the 4 named; UNDER-ENUMERATED as an inventory

All 4 verified money÷money at HEAD: `PortfolioController.hpp:1186` `sized_qty = FPN_DivNoAssert(risk_amount, fill_price)`; `ControllerEventLoop.hpp:2853` `max_qty = FPN_DivNoAssert(budget_remaining, entry_price)` (divisor = `pending_params.bg_price_threshold` — MONEY under the D-170 egress lock); `:2906` `core_dd_pct = FPN_DivNoAssert(drop, core_peak_balance)`; `:3256` `dd = FPN_DivNoAssert(drop, ks_peak_balance)`. None are O-1 crossings. But:
- **Missing money÷money site:** `PortfolioController.hpp:1509` `gain_pct = FPN_DivNoAssert(gain, pos->entry_price)` (time-exit gain check; gain = money−money, entry_price = Position money field). O-1 red-builds it eventually, but per the B2 lesson (fee enumeration under-counted TWICE) the design must carry a **tool-pasted Div-site inventory with per-site domain classification** (money÷money → #7 / cross-radix → O-1 cast cohort / binary÷binary → stays `fp2_div`), not a hand-list of 4. My sweep: cross-radix candidates PC:847/:858/:1157/:1240 (signal ratios over `rolling.price_avg`/`fill_price` — O-1 cohort); binary÷binary CEL:2299/:3008/:3030, Strategies/* (slope/stddev ratios — stay binary).
- **Needs classification:** `PC:1554` `danger_range_inv = 1/(danger_warn − danger_crash)` — if the danger threshold cluster goes money under B4-egress (price-compared thresholds), this becomes a money-reciprocal (1/price dimension) — settle its domain in the inventory.
- Dimension note: :2906/:3256/:1509 produce RATIOS (vs PCT-cohort cfg, S-14), :1186/:2853 produce qty — fine in <10,8>, worth one line on expected result ranges per class.

### Cross-cutting — #6↔#7 coherence: DESIGN-GAP

Merge-scan's #4-consumers row allows #6 quantize "a plain wide divide" for the runtime per-symbol step — that emits `__udivti3`, contradicting the no-udivti3 acceptance + H11. Resolve at design: **#6's runtime-step divide routes through #7's `udiv_qr`** (one runtime-divisor primitive — canonical-sister), then #4 truncate mode (floor-to-step, oracle-pinned). This also completes the "one body, five consumers" structure.

## Minimal design additions required before code (punch list)

1. **#4 fold (S-19/dod-F2):** chokepoint structure into the sidecar — mode NOT a public param; 3 named entry points (half-even inside Mul/Div · ceil ONLY inside `Money_FeeCompute` · truncate inside quantize); five consumers enumerated; grep-CI line. Pin ceil-variant nonneg domain (or signed semantics) — oracle ROUND_CEILING vs magnitude-away-from-zero disagree on negatives.
2. **#4 tie compare rewritten overflow-free + unsigned:** `half=d>>1` form (one body serves SCALE and runtime-divisor; kills the 2r class; ties only for even d). State magnitude-arithmetic-is-unsigned + round→domain-check→sign ordering.
3. **#7 full design artifact** (stub → design): `udiv_qr` generalization (seed = `umul(a_mag, 10⁸)`; fixed 128 trips; invariant + trip-0-saturate proof carried to the new seed; returns (q,r)); **result-domain guard |q| ≥ 2⁶³ → saturate-to-domain-MAX + sticky-flag** (NOT bit127); div-zero = saturate + DISTINCT sticky bit; sign abs-in/sign-out + −0 canonicalization; the money-domain closure invariant stated once.
4. **Oracle additions:** negative ties (both parities); fee-variant rows (actually CALL `oracle_fee_roundup`; r==0/r==1/large-r + domain pin); Div rows (even-divisor ties both parities both signs, odd-divisor near-ties 2r=d±1, tiny-divisor domain-overflow→saturate+flag expectation, div-zero, the 5 production-shaped cases). Correct the plan #4 row's "Oracle-verified" claim.
5. **no-udivti3 acceptance re-scoped:** probe-TU mechanics + sibling symbols; explicit `:1603` disposition (exempt-document vs rework-under-net).
6. **Div-site inventory tool-pasted** with domain classification; add `PC:1509`; classify `PC:1554`/danger cluster; list the O-1 crossing cohort. (`check_plan_enumeration_completeness.py` source: `rg -n "FPN_Div(No|With)Assert" --glob '*.hpp' --glob '*.cpp' -g '!tests/**' -g '!FixedPoint/**'`.)
7. **#6 quantize divide routed through #7** (kill the "plain wide divide" option).

No DESIGN-WRONG findings: no decided D-NNN is contradicted by either design; the gaps are unstated decisions and un-folded plan-layer decisions, all closable as design-text amendments (paragraphs, not architecture re-opens).

**End — D-93 design audit, cluster #4 + #7 (2026-06-09).**
