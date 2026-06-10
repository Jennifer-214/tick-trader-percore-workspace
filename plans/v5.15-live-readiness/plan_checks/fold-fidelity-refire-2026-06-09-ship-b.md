---
type: audit-report
skill: LIGHT RE-FIRE — fold-fidelity + consistency check (Ship-B pre-coding gate, final step)
date: 2026-06-09
head: 0e48150 (v5.15.5.F.4d.1.E.0.8) — verified
fold_targets:
  - subplans/2026-05-31-v5.15.5.F.4d.1.E-11-new-function-designs.md (sidecar; #4-#7 fold blocks + fee-booking + guards/epoch NEW sections)
  - subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md (plan; v0.4 banner + acceptance + B-rows + § Ship-B execution sequence)
sources:
  - plan_checks/d93-design-audit-{rounding-div, parse-casts, quantize, fee-booking, guards-epoch}-2026-06-09.md (5 punch lists, ~38 items)
  - decision log Session-13 addendum D-168..D-174
verdict: YELLOW — fold substantively FAITHFUL (~33/38 punch items land cleanly; zero architecture contradictions vs D-97..D-174); 6 specific fixes before code (1 sidecar-internal contradiction, 1 plan-row sweep family [D-172c recurrence], 1 factual mislabel, 2 fold-made decisions needing ratification, 1 stale-frontmatter family)
---

# Fold-fidelity re-fire — Ship B D-93 fold (2026-06-09)

Layer 2; no subagents; no edits to the fold targets. Checking the FOLD, not re-auditing the designs. All code claims in Check 5 re-verified at HEAD 0e48150.

## Check 1 — Coverage (every punch-list item, 5 reports)

### rounding-div (7 items)
| # | Item | Status |
|---|---|---|
| 1 | #4 chokepoint structure + ceil nonneg pin | **(a) FOLDED** — D-174d in sidecar #4 fold (nonneg + confined inside `Money_FeeCompute` + NO public mode param). The explicit grep-CI line is absent — arguably superseded by the stronger no-public-param structure, but not stated as such. The "3 named entry points / five consumers" enumeration is distributed (SCALE/2⁶⁴/runtime in #4; ceil in D-174d; >8dp in #5; quantize = subtract-remainder, see below) rather than one list. |
| 2 | Overflow-free tie form + unsigned + round→domain→sign ordering | **(a) FOLDED** — `half = d>>1; (r>half) \| ((r==half)&((d&1)==0)&(q&1))` ≡ the report's `(~d&1)` form; "unsigned 128-bit end-to-end" stated. The explicit ordering SENTENCE (round→domain-check→sign) is absent; components present and derivable. Minor. |
| 3 | #7 full design artifact | **(a) FOLDED** — udiv_qr (q,r) signature change golden-guarded; umul(a_mag,10⁸) seed; 128 trips constant-time; trip-0 invariant RE-PROVE flagged; |q|≥2⁶³ saturate + S-17 sticky; div-zero DISTINCT bit, ONE Div fn; money-domain closure invariant stated. −0 canonicalization line not stated (inherited via "mirroring #2" → fp2_mul's certified `& (mag != 0)` body; negligible but worth one clause). |
| 4 | Oracle additions + correct plan #4 row's "Oracle-verified" claim | **PARTIAL** — oracle additions FOLDED (negative ties; `oracle_fee_roundup` actually CALLED; Div rows incl. saturate boundary + div-zero; cast rows; detail rows live in the referenced audit record — acceptable fold-by-reference). **Plan #4 row correction (c) DROPPED** — see Check 3 item 1. |
| 5 | no-__udivti3 re-scope + :1603 disposition | **(a) FOLDED** — probe-TU + siblings; :1603 dispositioned at #7, cross-referenced from #5 ("superseded by #5's shared front-end rework"). Plan acceptance :354 still says bare "no-`__udivti3` symbol check" (under-specified, not contradictory — sidecar refines). |
| 6 | Div-site inventory tool-pasted + PC:1509 + PC:1554 + O-1 cohort | **(b) DISPOSITIONED** — :1509 added; :1554 classification trigger stated (B4-egress typing); full tool-pasted inventory with domain classification = explicit P1 deliverable (B2 lesson cited). Deferral is explicit, not silent. |
| 7 | #6 divide routes through #7 | **(a) FOLDED** — #6 fold (udiv_qr, NO multiply, no `__udivti3`; #6→#7 dependency "P1 before P4 — now stated") + #7 fold ("NEVER a plain wide divide") + plan :196 fixed. Mechanism = subtract-remainder (`quantized = value − r`) vs the report's "udiv_qr then #4 truncate mode" — mathematically identical floor (value−r = q·step), and avoids a multiply. Refinement, not weakening. |

### parse-casts (9 items)
| # | Item | Status |
|---|---|---|
| 1 | Cast + >8dp rounding-mode decision | **(b) D-174a** — half-even via divisor-generalized #4; >8dp per-class (LIVE refuse per D-174c / paper round+WARN). ✓ |
| 2 | LIVE-fill degrade ratified | **(b) D-174b** + folded per-site table row. Compression note: report = re-fetch → *still bad* → halt; fold = "re-fetch + halt-entries" (reads as unconditional halt). MORE conservative, not weaker; acceptable. |
| 3 | LIVE cfg-parse failure | **(b) D-174c** — LIVE refuse-boot / paper default+warn. ✓ |
| 4 | #5 split-accumulator front-end rework | **(a) FOLDED** — `(int_part, frac_int, n_frac, flags)`; binary wrapper discards flags, byte-identical (difftest + golden); old unified-mantissa phrasing explicitly superseded. ✓ |
| 5 | 6 edge pins | **(a) FOLDED** — all six (`+` accept; 2nd `.` reject; digitless reject; overflow ≤2⁶³−1 detected PRE-wrap; >8dp per-class; scientific via bad-char). ✓ |
| 6 | Per-class ok=false table + return shape | **PARTIAL** — `(value, flags)` pinned; table carries 8 of the 9 classes. **(c) DROPPED sub-row: class-4's RUNTIME-reconcile arm** (`OrderManager.hpp:1424-1431` balance overwrite; report: skip-update + flag + halt-new-entries). The fold table has "boot reconcile → refuse" only; B6 names the runtime-reconcile RETYPE but its parse-FAILURE behavior is unassigned. |
| 7 | PCT section | **(a) FOLDED** — pre_shift=2, ONE rounding, >6dp divmod+#4, exact ×100 full-digit egress (never %.2f), wire_context carry-over. ✓ |
| 8 | Cast-pair section | **(a) FOLDED** — both mechanisms verbatim; range notes; divisor-2⁶⁴ tie nuance owned by #4 (three flavors); to_decimal saturate REQUIRED + sticky load-bearing; to_binary saturation provably UNREACHABLE, "code no dead arm"; determinism/M5/oracle rows; no-udivti3 scope covers both; producer budget net ≤0 re-verified. Cast call-site twin list lives in plan B6 (pre-existing) — (b). |
| 9 | Stale POW10_RECIP prose | **PARTIAL** — sidecar annotated with a correcting note ✓; **plan rows :132/:189 still carry the stale prose** (cosmetic; (c) for the plan half). |

### quantize (7 items)
| # | Item | Status |
|---|---|---|
| 1 | Mechanism pin + #6→#7 dependency both rows + plan :196 signature + Step-0 naming note | **(a) FOLDED** — mechanism (udiv_qr subtract-remainder, oracle pins floor + idempotence); dependency in BOTH fn rows; plan :196 fixed to `(value, step)` + "never a 10^-k-assuming decimals signature, never `__udivti3`". Step-0 note: globally covered by plan Step 0; the #6 fold still spells `FPN_Quantize` while D-174d spells `Money_FeeCompute` — mixed pre-Step-0 placeholder naming (see Check 3 item 6). |
| 2 | LoadFilters + GetBalance cohort + span variant + qty_decimals derivation | **(a) FOLDED** — all three; derivation `FRAC − trailing_zeros₁₀(step.v)` ✓. **BUT factual mislabel:** fold says "applyMinToMarket/MARKET_LOT_SIZE/**lot_max_qty** recorded as known-unparsed" — **lot_max_qty IS parsed at HEAD** (`BinanceOrderAPI.hpp:715`, verified this re-fire; declared :78; consumed NOWHERE) — the report said parsed-but-unconsumed → clamp-or-tombstone. See Check 2 item 3. |
| 3 | MIN_NOTIONAL point + counter + entry buffer + exit-dust | **(a) FOLDED** — OMS submit ALL modes (M5 hole named); skip + named FailureMode counter; ×2.0 buffer adopted; exit-dust → flatten-dust rule. ✓ |
| 4 | Emit width + round-trip row + deletion order | **MOSTLY** — width = exactly `qty_decimals` digits, `FPN_ToString`-shaped param, −1111 rationale, callers-first sequencing ✓. The explicitly-NAMED qty parse→emit→parse acceptance row is not named (generic round-trip row exists at plan :362). Minor (c). |
| 5 | FORCE-CLOSE dust termination | **(a) FOLDED** — clear bit + book residual as dust (flagged) + exclude from wait mask; B-ζ acuteness carried; orphan :77 "clean today" (report additionally wanted the same NAMED dust disposition at :77 — micro-gap). |
| 6 | tickSize decision + D-number | **(b) D-174f** — load in S-10 pass, consume nothing, non-MARKET guard until `.E.3`. ✓ |
| 7 | Paper/backtest filter source + 4 test rows | **PARTIAL** — cfg-pinned venue snapshot (decimal registry rows, BTCUSDT defaults, live override, S-12 twin bar) ✓; oracle rows non-10^-k + idempotence ✓; **(c) dust-to-zero + sub-notional-entry-skip test rows not named anywhere.** |

### fee-booking (9 items)
| # | Item | Status |
|---|---|---|
| 1 | Terminal taxonomy + parser extension + Order_IsTerminal gate/comment fix | **(a) FOLDED** — table per source (WS TRADE / WS non-TRADE→parser EXTEND / REST failure / reaper); comment-lies fix named. Picked the stronger arm (extend parser) vs the report's deferred alternative. ✓ |
| 2 | Mandatory reaper + partial-SELL decision | **(a) FOLDED w/ a THIRD option** — reaper full shape ✓ (deadline scan → book partial → TIMEOUT → free + counter + reconcile true-up). Partial-SELL: report offered (i) close-at-avg+reconcile or (ii) flatten-escalate; fold picks (iii) **book filled portion + REDUCE position qty, slot keeps remainder** (`Portfolio_CloseSlot` never called on a partial; sister = partial-exit legs, verify at code time). Coherent and arguably better (no engine/venue position divergence) — but it is a NEW design decision not in the report's menu and carries no D-number. → Check 2 item 5. |
| 3 | Accumulator spec + sizeof cascade + deplete-then-weight | **(a) FOLDED** — fields (named `acc_filled_qty`/`acc_commission_quote`/weighted-price numerator — semantics match the report's `acc_net_qty`/`acc_fee_quote`/`acc_net_notional`), `last_trade_id` in dedup bullet; `Order.hpp:403` sizeof + HOT/COLD cluster + pool footprint named; in-memory-only scope correct; identity formula VERBATIM + rounding points (per-fill #4 mul; ONE #7 Div at terminal) + P3←P1 dependency. **(c) minor:** the per-Order sticky fallback bit (`flags_packed` ≥26) is not carried (account-level FailureMode counter covers observability coarsely). |
| 4 | Paper order_complete=1 + 4 tests + total_filled note | **MOSTLY** — decision + all 4 tests + identity test ✓. **(c) minor: the `total_filled` behavior-change note** (paper orders start counting; pre-existing counter bug silently fixed; sweep consumers) is not carried. |
| 5 | Dedup + mixed-source rule | **(a) FOLDED, refined** — `last_trade_id`, drop `t ≤ last`; mixed-source = WS-primary + on-REST-use reconcile-REPLACE (book venue `cummulativeQuoteQty` per D-106), never blind-add. Report's "REST is ACK-only when WS active" generalized to replace-on-use — composes with D-174b's re-fetch arm; not a weakening. |
| 6 | Degrade carrier | **(a) FOLDED** — OMS sticky atomic (CAS sister :562) → slow path `EventLoop_ClearAllPermissions` → 2 FailureModeRegistry rows (exact names/classes/severities) → re-arm operator-explicit (D-174e). Unified with the overflow boundary action per guards-epoch's own one-helper-two-callers recommendation. ✓ |
| 7 | B2 amendment (replay fee-muls S-3-superseded) | **(c) DROPPED at the named target** — sidecar carries "the four replay fee-muls DELETE — B2 reconciled" ✓ and acceptance :351 carries "DELETE, not re-route" ✓, **but plan B2 row :249 itself is UNAMENDED**: it still enumerates `ControllerEventLoop.hpp:863/877` + `OrderEventLog.hpp:656-657/675-676` as "route through #4's helper" coverage targets with no supersede marker. → Check 3 item 2. |
| 8 | Epoch-marker binding + event-log policy + H12 pad | **(a) FOLDED** — markers-first ONE commit; FULL_FILL-only stated policy; H12 explicit-pad re-derive; fee field rides the OMSEL02 commit (consistent: that IS the markers commit). ✓ |
| 9 | Differential tolerance | **(a) FOLDED** — K·10⁻⁸ per asset case; constructible round-UP-vs-half-even fixture; fail-loud = fee-schedule-change detector. "quote exact" vs report's "K small" = tightening (safe direction). ✓ |

### guards-epoch (6 items)
| # | Item | Status |
|---|---|---|
| 1 | S-17 mechanism ¶ | **(a) FOLDED** — TLS `constinit thread_local` unconditional `\|=` of existing `of_m`; per-thread cycle-tail drain → `alignas(64)` OMS atomic `fetch_or` relaxed; drainer-tail single consumer; NOT PerCoreSnap / NOT process-global (both anti-homes carried); hot-side of-bit on TradeEvent; sticky `MASK_OMS_STATE_MONEY_OVERFLOW_TRIPPED` + ClearAllPermissions + mirror row; NOT kill-switch tier; boot-replay drains pre-grant; replay runs identical flag path; flags-never-feed-math invariant; forced-overflow unit+integration+negative-control tests incl. replay-twin row. Landed in the sidecar (plan :354 points at the pin) — acceptable home. TLS name differs (`money_op_flags` vs report's `tt::g_money_of_acc`) — placeholder, fine. TradeEvent ring-POD/epoch layout note not restated — micro. |
| 2 | S-16 flag-disposition column + FromString stays separate | **PARTIAL — CONTRADICTION INTRODUCED.** Column folded; FromString harmonized to `(value, flags)` separate-mechanism (consistent with parse-casts, supersedes this report's `(value, ok)` shorthand — fine). **BUT "ingress-cast = flag" contradicts the #5 fold's own cast block** ("saturation provably UNREACHABLE this direction … code no dead arm") and the parse-casts proof. → Check 3 item 3. |
| 3 | Trait-keyed static_asserts + MONEY_ENCODING_EPOCH | **(a) FOLDED** — per-surface co-located asserts (type flip trips; sizeof-independent); derived epoch auto-raising floors `13/9/6 + EPOCH` ≡ plan's 14/10/7; markers-first. Consistent with plan R3-B acceptance row :350. ✓ |
| 4 | OMSEL rotate + tier decision + magic AND version word + H21 | **PARTIAL** — rotate-not-append (`.pre-epoch`, forensics) ✓; loud epoch message ✓; magic-WINS bidirectional rationale ✓; H21 tombstone + ledger row ✓. **Two deviations:** (i) **tier decision folded as "boot proceeds — warm-restart state is snapshot-gated separately" — the report RECOMMENDED LIVE + non-empty pre-epoch log ⇒ refuse-boot.** Reasoned (rationale inline, B-ζ flatten + snapshot gate make it defensible) but it resolves a required decision AGAINST the audit recommendation with no D-number. → Check 2 item 4. (ii) **(c) minor: "populate a `reserved[]` version word for future SOFT bumps" (the report's "do both") not carried.** |
| 5 | Stamp floor unconditional + MIN=3/CUR=3/MAX=3 + legacy-key retire | **(a) FOLDED** — bypasses strict fork (the DESIGN-WRONG closed); `[1,2]` dispatch dead → H21 retire. Plan :350 consistent. ✓ |
| 6 | Epoch test shape | **(a) FOLDED** — synthesized old headers (no old emitter); v13 / OMSEL01 rotated-not-appended (assert both) / stamp v2 under strict=1 AND strict=0; positive control; composed warm-restart boot. ✓ (Composed boot's expected end-state inherits the item-4(i) tier decision — pins itself once that is ratified.) |

**Dropped-verbatim list (all (c) items):**
1. "Correct the plan #4 row's 'Oracle-verified' claim" (rounding-div #4) — plan :131 unchanged.
2. "Amend B2: mark them S-3-superseded; #4 routing remains for computed paths only" (fee #7) — plan :249 unchanged.
3. "Runtime reconcile: skip-update + flag + halt-new-entries" (parse-casts Q2 class-4 runtime arm).
4. "populate a `reserved[]` version word for future SOFT bumps" (guards Q6c "do both").
5. "`total_filled` behavior-change note + sweep consumers" (fee Q2).
6. "sticky fallback bit fits `flags_packed` bits ≥26" (fee Q1 accumulator).
7. "name the qty parse→emit→parse row" explicitly (quantize Q4).
8. "dust-to-zero + sub-notional entry skip" test rows (quantize #7).
9. Plan-side POW10_RECIP stale prose at :132/:189 (cosmetic; sidecar half done).
10. Micro: −0 canonicalization clause (#7 sign — inherited via the certified fp2 body); orphan-:77 named dust disposition; explicit round→domain→sign ordering sentence; grep-CI line for mode confinement (superseded by no-public-param, unstated).

## Check 2 — Fidelity (mismatches, both texts)

1. **S-16 ingress-cast flag cell (silent direction-flip).** Fold: "ingress-cast = flag · egress-cast to_decimal = flag (saturate reachable)". Parse-casts report + the sidecar's OWN #5 cast block: to_binary (ingress) "saturation provably UNREACHABLE … no flag arm needed / code no dead arm"; to_decimal (egress) saturate REQUIRED. The guards-epoch report's Q2 table ("money max ~1.7e30 > binary cap → ingress YES; egress widening — no overflow") used the pre-closure 128-bit register range and is superseded by the money-domain closure invariant (|mant| ≤ 2⁶³−1) the fold itself locks at #7; the fold corrected the egress cell to match parse-casts but kept the wrong ingress cell. **Fix: ingress-cast = no (unreachable — proof at #5 cast block).** One word.
2. **lot_max_qty mislabeled.** Fold: "applyMinToMarket/`MARKET_LOT_SIZE`/lot_max_qty recorded as known-unparsed (conservative-safe today)". Report (verified at HEAD this re-fire): `lot_max_qty` **parsed** at `BinanceOrderAPI.hpp:715`, consumed nowhere → "fold max-qty clamp into the #6 submit check or tombstone-document". The document-arm is taken but records a false fact, and a parsed-but-unconsumed field is precisely H21/dead-code territory — re-label + give it the clamp-or-tombstone disposition explicitly.
3. **OMSEL pre-epoch boot tier folded as the weaker arm.** Report Q6b: "Required decision: LIVE mode + non-empty pre-epoch log ⇒ refuse boot (operator archives explicitly); paper/backtest ⇒ rotate+warn+continue." Fold: "loud epoch message; **boot proceeds** — warm-restart state is snapshot-gated separately" (all modes). This is the refuse-folded-as-warn shape the re-fire exists to catch — mitigated by being non-silent (rationale inline) and defensible (snapshot version-reject + B-ζ mandatory pre-deploy flatten mean no stale state loads), but it is an audit-recommendation reversal on a capital/persistence surface with no D-number. **Ratify explicitly (D-17x or operator line) or adopt the report's LIVE-refuse arm.**
4. **Partial-SELL = a third option.** Report framed a binary pick (close-at-avg+reconcile vs flatten-escalate); fold designs reduce-position-keep-remainder. Better on position-consistency grounds; flagged "verify against the partial-exit leg machinery at code time". Needs the same explicit ratification as item 3 (a fold-made decision outside the audit's menu, no D-number).
5. Benign refinements (no action): quantize subtract-remainder ≡ floor (≡ "#4 truncate" result); LIVE-fill halt made unconditional-on-malformed (more conservative); REST mixed-source ACK-only → reconcile-REPLACE generalization; "quote exact" tolerance (stricter than "K small").

## Check 3 — Internal consistency

1. **Plan #4 row :131 vs sidecar #4 fold (CONTRADICTION).** :131 still carries `round_up = (2r>SCALE) | ((2r==SCALE)&(q&1))` + "Oracle-verified (D-100, incl. the 2r==SCALE ties)". The fold REPLACES the `2r` compare (signed-UB at r ≥ 2¹²⁶ under #7) and records the oracle claim as "partially false" (`oracle_fee_roundup` never called). A coder lifting the plan-row formula re-introduces the UB class the fold just closed. Same family: **plan #7 row :134** still says "the helper's `2r` vs SCALE compare generalizes to `2r` vs divisor" — exactly the generalization Q2 proved unsafe; **plan #5 row :132** still says `(value, ok)` vs the fold's `(value, flags)`.
2. **Plan B2 row :249 vs S-3/sidecar (CONTRADICTION — the seeded check).** :249 routes `CEL:863/877` + `OEL:656-657/675-676` through #4's helper; acceptance :351 + sidecar fee fold say those four muls DELETE (replay reads the event fee), not re-route. The supersede marker the fee-booking punch list required was never written into :249.
3. **Sidecar-internal: guards S-16 column vs #5 cast block** (Check 2 item 1) — the only contradiction BETWEEN fold blocks.
4. **Seeded checks that PASS:** #4 divisor-generalized form vs #7's rounding reference — consistent inside the sidecar ("#4's divisor-generalized half-even on (q,r) with d = divisor"). Per-site failure table vs D-174b/c — consistent (LIVE fill = D-173 degrade + re-fetch; LIVE cfg/exchangeInfo refuse-boot; paper default+warn). Epoch static_assert design vs plan R3-B :350 — consistent (13/9/6+EPOCH ≡ 14/10/7; trait-keyed; markers-first both). Paper order_complete=1 vs keep-slot terminal taxonomy — consistent (paper = single terminal FILLED riding the same path; V2 trap closed). Markers-first commit vs fee-field-rides-OMSEL02-commit — consistent (same commit).
5. **Stale frontmatter/footer family (drift, not design):** plan frontmatter `plan_version: v0.3` + status/decision_log "D-97..D-167 = SSoT" vs the body's v0.4 banner + D-174 citations; plan footer :398 "Remaining … = this body's per-ship `/precoding-audit-gate` … + the D-93 new-fn design audits on #4/#5/#6" — both DONE (and #7 omitted); sidecar frontmatter status "#4/#5/#6 FRAMED (D-93 design audits still owed before code); #7 … stub in body" + `decision_log: D-122..D-172` vs its own body's "[DESIGNED — D-93 fold (D-174)]" blocks. Re-stamp all three at the fix pass.
6. Cosmetic: pre-Step-0 placeholder naming is mixed (`FPN_Quantize` in #6 fold vs `Money_FeeCompute` in D-174d) — fine pending Step 0, but plan Step-0's "decide at the D-93 design pass" pointer is now stale (the pass ran; naming was NOT among D-174a-f — still open, decided at Step 0 itself).

## Check 4 — Decision alignment (D-97..D-174)

No fold text contradicts any DECIDED item. Verified against: D-105 (one divisor-parameterized rounding body = single-source by construction ✓), D-106/D-109 (venue snapshot, source-exact booking, ×fill_price ✓), D-107 (casts byte-deterministic, restated ✓), D-122/D-124 (ema ingress cast, producer budget ✓ — the #5 fold's "D-170 ingress" tag is loose shorthand for the B4 fork's ingress arm, sanctioned by D-122; not a violation of D-170's no-per-tick-cast-in-BG/SG lock), D-127 ((amount, asset) ✓), D-128 (half-even ✓), D-130/D-139/D-140 (untouched ✓), D-147 (binary keeps silent saturate ✓), D-157 (Check-F un-bypass in P5 ✓), D-170 (egress lock carried ✓), D-173 (bnbBurn boot query + runtime N guard + degrade ✓), D-174a-f (all six locked decisions folded verbatim ✓). The two fold-made decisions WITHOUT D-numbers (OMSEL boot-proceed tier; partial-SELL reduce-qty) don't contradict any D — they fill gaps D-174 left open — but per session-decision-log discipline they should be ratified/numbered (Check 2 items 3-4).

## Check 5 — Spot-verify of the fold's NEW code claims (HEAD 0e48150)

| Claim | Verdict |
|---|---|
| `OmsFieldRegistry.hpp:735-736` swallowed reject | **VERIFIED** (file lives in `MemHeaders/`): :735 `int _loaded = OrderEventLog_LoadFromDisk(…)`; :736 `if (_loaded > 0) {` — a −1 (bad magic) is silently not-taken; macro proceeds toward init/reopen. |
| `ControllerEventLoop.hpp:3196` `EventLoop_ClearAllPermissions` | **VERIFIED** — fn at :3195-3200; clears `ExecutionCore_SetPermission(core, 0)` over all registered cores (entries-only gate). |
| `OrderManager.hpp:562` CAS sister | **VERIFIED-as-anchor** — :562-569 is the WS-staleness CAS comment block; the `alignas(64) std::atomic<int> flatten_pending` itself at :570. Anchor points at the right cluster. |
| `fp2_mul` `of_m` at `FixedPointN.hpp:1300-1303` | **VERIFIED** — :1300 `ovf`, :1301 `nz`, :1302 `of_m = -(…)`, :1303 mask-saturate. (Bonus: :1307 carries the `& (mag != 0)` −0 canonicalization — the "mirroring #2" inheritance claim holds.) |
| `Order.hpp:414-421` `Order_IsTerminal` dormant + lying comment | **VERIFIED** — fn :414-422; comment :411-413 "Used by OrderManager_Tick to decide whether to free the slot" (false at HEAD — the free is unconditional). |
| `BinanceUserData.hpp:320-323` non-TRADE drop | **VERIFIED** — :320 comment "only 'TRADE' is a fill"; :323 `if (strcmp(exec_type, "TRADE") != 0) return 0;`. |
| `ShardedLiveSafety.hpp:205-208` dust skip | **VERIFIED** — :205 `if (qty_d < api->filters.lot_min_qty)`, :206-207 fprintf, :208 `continue;` — the slot's bit in the persistent active bitmap is never cleared (only the local iteration mask advances), so the :233 drain-wait stalls. |
| (extra) `BinanceOrderAPI.hpp:712-723` LoadFilters / `:755` GetBalance `"free"` / `:715` lot_max_qty | **VERIFIED** — :712-717 LOT_SIZE extracts, :720-723 NOTIONAL, :755 `binance_json_extract_double(pos, "free")`, **:715 parses `lot_max_qty`** (refuting the fold's "known-unparsed" label; only other ref = the :78 declaration). |

8/8 verified (one as comment-anchor); one fold LABEL refuted (lot_max_qty), already itemized.

## Verdict + fix list

**YELLOW — fold faithful and convergent in substance (~33/38 punch items land as written or via D-174; zero contradictions with decided D-97..D-174; all spot-checked code claims real). Six fixes before code:**

1. **[plan-row sweep — the D-172c clause recurring on itself]** Sweep the stale plan summary rows the fold superseded: :131 (#4 formula → divisor-generalized form; delete/correct "Oracle-verified"), :134 (#7 "2r vs divisor" → half=d>>1 reference), :132 ((value, ok) → (value, flags); POW10_RECIP note), :249 (B2: mark the four replay fee-muls S-3-superseded — DELETE, not #4-route), :189 (POW10_RECIP cosmetic).
2. **[sidecar one-word]** S-16 flag column: ingress-cast = **no** (saturation unreachable per the #5 cast-block proof), resolving the only inter-fold-block contradiction.
3. **[sidecar one-line]** lot_max_qty: parsed-at-:715-but-unconsumed (not "known-unparsed"); state clamp-into-#6-submit or tombstone explicitly.
4. **[ratify ×2]** OMSEL pre-epoch boot = rotate+proceed (vs the audit's LIVE refuse-boot recommendation) and partial-SELL = reduce-qty-keep-remainder (a third option outside the audit's menu) — both reasoned, neither D-numbered; operator line or D-17x each.
5. **[minor adds — one clause each, or explicitly waive]** runtime-reconcile parse-failure row; `reserved[]` version word alongside OMSEL02; `total_filled` behavior-change note; named qty parse→emit→parse row; dust-to-zero + sub-notional test rows; per-Order fallback bit (or waive for the account-level counter).
6. **[re-stamp]** plan frontmatter (v0.4; D-174) + footer :398; sidecar frontmatter status + decision_log range (..D-174).

Nothing here re-opens architecture; items 1-3 are mechanical text fixes, item 4 is two one-line ratifications, items 5-6 are hygiene. Code may start once 1-4 land (5-6 can ride the same edit pass).

**End — fold-fidelity re-fire, 2026-06-09.**
