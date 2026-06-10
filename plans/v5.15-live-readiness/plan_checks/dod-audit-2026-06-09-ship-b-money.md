# /dod-audit report — ship-b-money (money-numeric-core foundation, Ship-B remaining scope) — 2026-06-09

- **Target:** `plans/v5.15-live-readiness/subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md` (v0.3, re-audited to HEAD 0e48150 / v5.15.5.F.4d.1.E.0.8)
- **Mode:** plan-mode, focus-scoped (branchless / H12 / SSoT-rounding / tt:: dispatch / registry-fit / X-macro-cohort / cache-layout)
- **Scope discipline:** Ship-A rows SHIPPED (not audited); DECIDED items D-97..D-167 honored — mode choices (half-even D-128, 10^8 D-104, no-new-registry-at-#11, flag-loud-for-money D-147) are NOT re-flagged; findings below are about plan SHAPE on un-coded Ship-B work only.
- **Catalog:** DESIGN_SPECS walked (88 docs across 8 type dirs); focus patterns loaded in full: `branchless-dispatch-discipline.md`, `struct-padding-determinism-pattern.md`, `single-source-of-truth-discipline.md`, `type-trait-dispatch-via-tt-namespace.md`, `metadata-bit-driven-derived-filter-framework.md`, `foreach-exchange-meta-registry-pattern.md`, `x-macro-registry-with-presence-dispatch.md`, plus sidecar `2026-05-31-...-11-new-function-designs.md`.

## Summary

| Focus area | Pattern (DESIGN_SPECS) | Verdict |
|---|---|---|
| (a) Branchless on new money ops | branchless-dispatch-discipline.md (H7/H20) + branchless-math-kernel (H11) | APPLIED on #2/#3/#4; **1 HIGH spec-gap** (flag-loud mechanism) |
| (b) H12 / struct padding | struct-padding-determinism-pattern.md | APPLIED (16B no-padding holds); 1 LOW (decimal-type-level asserts) |
| (c) SSoT rounding chokepoint | single-source-of-truth-discipline.md + structural-fix-preferred | **1 MED** — mode binding is per-site convention, not compile chokepoint |
| (d) tt:: dispatch (B3) | type-trait-dispatch-via-tt-namespace.md (H13, 3-barrier) | APPLIED (design is textbook); 1 MED enumeration undercount |
| (e) Registry-fit at #11 | foreach-exchange-meta-registry-pattern.md + framework-selection | **CLEAN — no-new-registry CONFIRMED correct** |
| (f) X-macro / money cohort | metadata-bit-driven-derived-filter-framework.md + x-macro-registry | 1 LOW — type-derived cohort walk missed (do NOT add a MONEY bit) |
| (g) Cache layout in hot structs | cache-layout-discipline-for-hot-side-structs.md + decision-time-data-binding | CLEAN at 16B; **1 MED** — B4 fork has one hot-path-violating arm |

## Findings (severity-ordered)

### HIGH — F1 [spec-gap·branchless] "Flag-loud" overflow posture for Ship-B money has NO specified mechanism; the naive shape is a data-dependent branch inside money math kernels on drainer/slow paths

- **Surface (plan):** body :259 ("flag-loud = the Ship-B money posture, still live"), :128 (#3 overflow guard "out-of-range → D-106 flag, never silent wrong-magic"), :325 (acceptance: "flag-loud is the Ship-B money posture"). Sidecar #5 ":58" ("round-not-truncate + flag", "Overflow → D-106 range guard / ok=false").
- **Pattern:** `branchless-dispatch-discipline.md` (H20 invariant + decision matrix) + H11 (constant-iter, branchless within reductions) + `DESIGN_PHILOSOPHY.md` § 4.
- **Symptom:** D-147 decided the POSTURE (flag-loud for money — not re-flagged). But neither the plan body nor the #1-#6 sidecar constrains the flag's SHAPE. The money ops carrying the guard run on the drainer (fill handlers `OrderManager.hpp:1160-1210`), slow path (replay/production `ControllerEventLoop.hpp:863/877/1923/1967`), and 3 rare-entry hot muls (`ExecutionCore.hpp:543/549/570` — verified at HEAD :543-577). An `if (overflow) { log/halt }` inside `Mul<10,8>`/`Negate`/`Abs` puts a data-dependent branch inside math-kernel bodies on H20-governed paths — exactly the Class-28 shape, on capital code, under the D-77 heavier-default posture.
- **Compliant shape (one paragraph to add):** keep the existing branchless `of_mask` saturate discipline (already in the 16B core — `FixedPointN.hpp:1284-1315` mask-select, `:1298` "same of_mask discipline as FPN_Mul") AND branchlessly OR the overflow predicate into a **sticky flag word** (canonical sister: `MemHeaders/FailureModeRegistry.hpp` — `MASK_*` bitmap + `__atomic_fetch_or` multi-flag updates, ":34"; same shape as kill_switch/SHALT atomic flags). The BOUNDARY checks it once per cycle (`__builtin_expect`-rare branch = decision-matrix-sanctioned: drainer cycle end / kill-switch eval / D-100 gate). Result: saturate stays branchless per-op; loudness is a boundary event, not a per-op branch.
- **Where it lands:** the D-93 new-fn design audit on #2/#4 (already a pre-coding trigger :357) — add the branchless-sticky-flag constraint to the plan body + an acceptance row ("money overflow flag = sticky mask, branchless at op site; boundary check enumerated").
- **Effort:** plan amendment ~1 paragraph; design already has every primitive it needs.

### MED — F2 [structural·SSoT] Rounding-MODE binding is per-call-site convention; make the venue-fee mode a structural chokepoint

- **Surface (plan):** #4 (:129) "SINGLE source → uniform incl. replay (D-105) by construction" + B2 (:246) ≥9 fee sites + anti-pattern row 4 (:76) "CI/test that all money sites route through it".
- **Pattern:** `single-source-of-truth-discipline.md` ("drift would be silent" → MERGE) + `structural-fix-preferred-decision-framework.md` + `feedback_guards_compound_enforcement_is_leverage`.
- **Symptom:** #4 is ONE helper for the MATH, but it exposes TWO modes (half-even default vs venue round-UP `(r!=0)`), selected **at each call site**. At HEAD the fee sites do NOT share a chokepoint: fill handlers compute `FPN_Mul(notional, o->pre_resolved.fee_rate)` directly (`OrderManager.hpp:1163`, verified), and `Fee_Compute` (`ControllerConfig.hpp:1366-1370`) is explicitly canonical-for-tests/legacy only (its own comment forbids new per-core call sites). So Ship-B's "uniform incl. replay" guarantee rests on (i) the replay==production differential and (ii) tool-verified enumeration — TEST/convention nets. A site calling plain decimal-Mul (half-even) where round-UP was intended **compiles fine**; only differential coverage catches it.
- **Suggested fix:** bake the mode INTO what the domain exposes — decimal money Mul carries NO public per-site rounding arg (half-even baked); venue round-UP exists ONLY inside one `Money_FeeCompute(notional, rate)`-style helper that ALL B2 paper/backtest+replay fee sites call; extend the B2 enumeration check to a grep-CI asserting no raw decimal-mul at fee sites. Mode-drift becomes structurally unreachable instead of test-caught. (D-105 uniformity + D-128/D-109 mode CHOICES untouched — this is about the binding shape.)
- **Effort:** ~0 net code (the helper exists in the plan as #4's variant); plan amendment + 1 CI assertion.

### MED — F3 [enumeration·tt::] B3's "all 3 dispatchers" undercounts the typed-dispatcher family — paste the inventory

- **Surface (plan):** B3 (:247) names emit/populate/drift-compare; H3 (:212) "name all 4".
- **Pattern:** `type-trait-dispatch-via-tt-namespace.md` Barrier 3 + `feedback_paste_tool_output_dont_summarize`.
- **At HEAD (verbatim):** `CoreFrameworks/CfgFieldDispatch.hpp` has **8** tt:: entry points whose family `static_assert` excludes decimal: `cfg_parse_field :57` (assert :63), `cfg_save_field :179` (:180), `cfg_assign_field :232` (:233), `cfg_diff_field :273` (:274), `cfg_emit_field :330` (:331), `cfg_populate_inf_field :399` (:400), `cfg_drift_compare :455` (:456), `cfg_drift_format_reason :501` (:505). Plus `is_fp_binary_v` consumers in `GUI/SettingsPanel.hpp` (render path for the ~30 money cfg rows) and `tt::stamp_parse_field` (`ML_Headers/StampBoundModelConstRegistry.hpp:103`) if money stamp fields parse back decimal. Money cfg fields flow through parse/save/assign/diff (cfg-file + GUI + per-node overrides), not just the 3 wire dispatchers.
- **Why MED not HIGH:** the Ship-A disjoint-trait net makes every missed branch a **red-build** (GUARDED-BY-BUILD — the design working exactly as `type-trait-dispatch-via-tt-namespace.md` intends; B3's design itself is a textbook 3-barrier application, APPLIED). The gap is scope-sizing: each entry point needs a decimal branch with the RIGHT semantics (parse=exact `FromString` per M1; save/emit=exact decimal string; assign/diff/render; drift-compare+format). The `check_storage_t_coverage.py` extension must walk ALL of namespace tt — the plan's "every typed dispatcher" wording is correct; add the verbatim list so the both-branch assertion and the effort estimate cover 8+, not 3.

### MED — F4 [design-fork·cache/latency] B4 price-domain fork: only the thresholds-cast-at-gate-build arm preserves "hot path UNTOUCHED"

- **Surface (plan):** B4 (:248) — "price-stats stay BINARY + thresholds cast to money at gate-build (egress), OR `tick.price` casts to binary at compare. Pick one." (Genuinely open — not a decided item.)
- **Pattern:** `decision-time-data-binding-pattern.md` (pre-resolve onto the consumed object) + `branchless-dispatch-discipline.md`/H7/H8 + `cache-layout-discipline-for-hot-side-structs.md`.
- **Symptom:** the second arm (`tick.price` → binary at compare) puts a **per-tick** cross-radix conversion (a 128-bit scaling multiply) inside `BG_Evaluate`/`SG_Evaluate` (`GateParameters.hpp:171/198`) — per-tick, NOT rare-entry — contradicting the plan's own hot-path-UNTOUCHED premise (:13, :195) and eating into the ≤500ns p99 (H8) for zero benefit.
- **Suggested fix:** lock the EGRESS arm in the plan: thresholds cast binary→money once at slow-path gate-build (`ExecutionCore_SetParameters` seqlock publish) = decision-time pre-resolution; hot path compares decimal-vs-decimal (`__int128` integer compare, identical cost, zero conversion). `GateParameters`/`cached_params` money fields become `FixedPoint<10,8>` — same 16B, layout-neutral.
- **Effort:** 1-line plan decision; removes a whole hot-path risk branch from Ship-B's gate.

### LOW — F5 [guard·H12] Add decimal-type-level layout asserts co-located with the `<10,8>` specialization

- **Surface:** `FixedPoint/FixedPointN.hpp` — `<2,64>` carries `static_assert(sizeof==16)` at :44 and :89; the plan's #1 asserts "16B, 16-aligned, NO padding" for the unified storage but no acceptance row pins it on the NEW decimal specialization itself.
- **Pattern:** `struct-padding-determinism-pattern.md` (the durable lesson: verify-no-padding explicitly) + the plan's own R1 self-protecting-assert discipline (:237).
- **Fix:** `static_assert(sizeof(FixedPoint<10,8>)==16 && alignof(FixedPoint<10,8>)==16 && std::has_unique_object_representations_v<FixedPoint<10,8>>)` mirroring :89. Containing-struct ladders (`Portfolio.hpp:80-142`, `Order.hpp:148/:403`, F-076 `CfgFieldDispatch.hpp:475`) guard transitively; the direct assert closes the gap at the source. ~3 lines.

### LOW — F6 [cohort·X-macro] Money-cfg cohort should be TYPE-DERIVED via the registry walk — not a hand list, and NOT a new MONEY metadata bit

- **Surface (plan):** blast radius (:188) — "~30 of ~1,931 `FromDouble`" money cfg rows, carried as a hand-enumerated list.
- **Pattern:** `metadata-bit-driven-derived-filter-framework.md` (Option E walker reuse) + `x-macro-registry-with-presence-dispatch.md` + `single-source-of-truth-discipline.md`.
- **Assessment:** post-O-1 the registry row's TYPE column IS the money marker. A `MONEY` metadata bit would mirror information the type already carries (parallel-descriptor drift: bit says money, type says binary) — correctly NOT proposed; the plan's restraint here is CLEAN. The MISSED application is the cheap inverse: an X-macro walk keyed `if constexpr (is_fp_decimal_v<decltype(field)>)` gives a compile-time money-cohort enumeration for free → (i) the D-100 money differential can WALK decimal cfg fields mechanically instead of trusting the hand list; (ii) a one-time migration cross-check (intended-~30 list vs the trait walk) catches the residual O-1 escape: a money field consumed only among binary peers never hits a cross-domain compile error and silently stays binary (the imprecision class un-closed for that field).
- **Effort:** ~30 min; composes with existing `CFG_FIELD_FOR_EACH` infrastructure; no new bit, no new registry (H16 untouched).

## CLEAN / APPLIED (sanity rows — no action)

- **(a) core ops:** #4 rounding helper IS branchless from `(q,r)` as planned (sidecar :46-48: `round_up = (2r>SCALE) | ((2r==SCALE)&(q&1))` — pure mask arithmetic; venue variant `(r!=0)` likewise). #3 `divmul_pow10` constant-time multiply+shift, PROVEN (D-140). #2 mul branchless sign-extract/abs/of_mask per D-145 (verified `FixedPointN.hpp:1264-1315`). The error-detecting `(value, ok)` parse return (#5) is data, and rejecting a malformed venue string is a decision-matrix-sanctioned `__builtin_expect`-rare branch on the producer. APPLIED.
- **(e) registry-fit:** NO new registry at #11 CONFIRMED correct — `foreach-exchange-meta-registry-pattern.md` frontmatter pins `landing_ship: v5.15.5.F.4d.1.E.1` with first canonical at `.E.1`; a #11 registry would be the <2-entry stagnant shape the framework-selection criteria reject; `SymbolFilters` (`BinanceOrderAPI.hpp:75-82`) as the #11 precision source + the Check-29 sister-registries section (:169-177) both present. CLEAN.
- **(g) cache layout:** 16B-for-16B type flip is layout-neutral everywhere verified — `Tick` (`CoreFrameworks/Tick.hpp:32-43`, `alignas(64)`, price/volume 16B → one tick stays one cache line), ExecutionCore line-0 invariants hold (`ExecutionCore.hpp:177` `offsetof(live_sl)+sizeof≤64`, :179 `permission%64==0`, :183 `live_tp≥8`), Position/Order ladders unchanged. Cosmetic note: assert spellings `sizeof(FPN_Binary<64>)` on fields that flip to decimal should be re-typed at code time (same value; compile-visible). CLEAN.
- **(b) H12 containing structs:** 16B no-padding holds; F-076 `has_unique_object_representations_v` (`CfgFieldDispatch.hpp:475`) satisfied by the decimal struct by construction; H5/C5 acceptance rows already cover fingerprint zero-init + `is_trivially_copyable`. APPLIED (F5 is the only residue).
- **(d) dispatcher design:** disjoint traits at HEAD (`FixedPointN.hpp:97-107` + the `FPN_Binary<64>` trait extension), exhaustive family `static_assert` + `always_false` final-else + coverage-tool extension = the 3-barrier pattern verbatim. APPLIED (F3 enumeration residue only).

## Recommendations

- **Address in plan before Ship-B coding (pre-coding amendments — all are paragraphs, not code):** F1 (constrain flag-loud to branchless-sticky-flag + boundary check; route through the already-scheduled D-93 design audit), F2 (mode-baked fee chokepoint + grep-CI), F3 (paste the 8+ dispatcher inventory into B3), F4 (lock the B4 egress arm).
- **Fold into Ship-B implementation (trivial):** F5 (3-line asserts), F6 (trait-keyed cohort walk + one-time cross-check).
- **Defer:** none — nothing here is deferral-shaped; all are plan-text-now or trivially in-ship.
- **No TECH_DEBT auto-writes:** all findings are pre-coding plan amendments on an un-coded surface (operator triage first per consult-before-coding).

## Verdict: YELLOW

No CRITICAL, no architecture-killer; the Ship-B design applies the focus patterns correctly at the architecture level (the disjoint-trait net, the branchless #2/#3/#4 cores, the no-registry restraint, and the 16B layout neutrality are all genuinely sound). One HIGH (F1 — the flag-loud mechanism must be pinned branchless before the money kernels are designed) + three MED, all addressable as plan amendments inside the already-scheduled Ship-B pre-coding gate + D-93 design audits.
