---
type: audit-synthesis
established: 2026-06-02
sprint: v5.15-live-readiness
audit: capital-safety + H-invariant enforcement coverage (2-agent sweep)
trigger: operator "guards are almost more important than the actual code — they scale over a lifetime"
status: in-flight (2 guards landed, 6 pending)
sister: feedback_guards_compound_enforcement_is_leverage / feedback_opportunistic_tech_debt_closure / TECH_DEBT-155
---

# Guard-coverage audit synthesis — capital-safety + H-invariant enforcement (2026-06-02)

Preserves the findings of the 2-agent sweep so the **guard-hardening pass** continues across sessions
WITHOUT the loaded context (compaction-safe). Spawned during #11 Session-9-continuation, alongside (not
part of) the Ship-A storage flip.

## Headline — the production sharded path is WELL-DEFENDED
The Knight-Capital-class risks are ALREADY guarded (do NOT re-flag):
- slot-encoded order-id reuse → id-match verified (`OrderManager.hpp:1314-1318`)
- partials slot-overflow → boot-REFUSED (`Sharded_ValidatePartialExitCfg`, ControllerEventLoop.hpp:1146)
- division → saturates to MAX, no UB (`FixedPointN.hpp:719`)
- kill-switch drawdown div-by-zero → peak-guarded (`ControllerEventLoop.hpp:3247`)
- WS-staleness double-flatten → CAS-safe (`ControllerEventLoop.hpp:3502`)
- fill core_id/slot bounds + double-close → guarded
We are NOT on a minefield. The gaps are in the **enforcement layer** — invariants held by convention with
no mechanical guard (the H21 shape: an invariant with no guard until one is built).

## H1–H21 enforcement matrix
ENFORCED (mechanical): **H9** (HMAC tamper/version/gap tests `controller_test.cpp:8921+` + determinism golden) ·
**H10** (`check_fp_determinism.sh` native==generic byte-identity, pre-commit Check F) · **H17**
(`check_per_core_registry_integrity.py` Check 2 FORBIDDEN-manual-fields, run by `build.sh:273` every build) ·
**H21** (`check_identifier_retirement.py` pre-commit Check H). Partial: H4/H5/H6/H12 (specific structs +
atof-manifest + F-076 test).

HOLES (convention-only on a capital/determinism surface — the targets):
- **H1 / H3** — no-heap / no-locks "anywhere": NO grep guard. A re-introduced `new`/`std::vector`/`std::mutex`/`sleep_for` ships silently. → guard #6.
- **H7 / H8** — branchless / latency p99 (the #1 stated invariant): NO asm/perf gate. `LATENCY_BENCH` is opt-in manual output, never pass/fail. → guard #12.
- **H13** — reinterpret_cast punning: the enforcement tool `check_storage_t_coverage.py` EXISTS but is an ORPHAN (wired into nothing). (Backstop: the X-macro walker compile-fails a missing `tt::` branch.) → wire it (fold into #9-area).
- **H15 / H19** — meta-registry coverage/topology: `check_meta_registry.py` exists + works but is ADVISORY ("NON-FATAL during transition") and run ONLY by `check_session_docs.sh` (doc-sweep, `/close-session`) — never pre-commit, never build.sh. → guard #9.
- **H16** — MetadataFlag→derived-filter coverage: NO code exists at all. → guard #10.

**DOC-INTEGRITY finding (important):** CLAUDE.md names three CI checks as ENFORCING H15/H16/H19 —
`test_meta_registry_coverage`, `test_meta_registry_topology`, `test_metadata_bit_to_derived_filter_coverage`
— **none exist as code.** The always-loaded doc claims a safety net that isn't there (a phantom-invariant
in CLAUDE.md itself). Fix in #9/#10: build/wire the real checks, then reconcile the CLAUDE.md claims.

## Capital-path findings
- **OMS submit has no qty/notional cap** — `OrderManager_Submit` (`OrderManager.hpp:901`) trusts upstream sizing entirely; `FPN_DivNoAssert` saturates a zero-price divide to MAX magnitude → failure mode = "max-size order to the exchange," not a crash. The closest LIVE sibling to Knight-Capital. → guard #11.
- **Maker/taker fee desync** — LANDED (`OMS_GuardTakerBoundFeeBasis`, `d2ee570`); real fix = TECH_DEBT-154 (re-resolve fee at fill, gated on LIMIT).
- **Bounds static_asserts** — LANDED (#7, `dad6f19`).
- **Legacy `BuyGate`/`SellGate` "prices always positive" phantom + 2-word compare** (`OrderGates.hpp:102,107-118`) — DEPRECATED single-core path only (production sharded uses sign-safe `FPN_GreaterThanOrEqual`, `ExecutionCore.hpp:429`). Real only if legacy runs with money. → guard #13 (retire or guard).
- **Snapshot body has no checksum** (`ShardedSnapshotPersist.hpp:109-388`) — contradicts H9; LOW (paper-only — load gated `!live_trading`, live reconciles from exchange, `Run.hpp:982-1004`). → guard #13 (CRC32).

## The 6 PENDING guards (implementable from here; TaskList #6/#9/#10/#11/#12/#13)
- **#6 H1/H3 forbidden-token guard** — new tool: grep engine src (CoreFrameworks/Strategies/ML_Headers/MemHeaders/FixedPoint/DataStream/Backtest) for `new`/`malloc`/`std::vector`/`std::string`/`std::function` (H1) + `std::mutex`/`condition_variable`/`sleep_for`/`pthread_rwlock` (H3); comment/string-excluded; KNOWN-PENDING baseline (shrink-never-grow, like `check_locale_determinism.sh`'s atof manifest); wire pre-commit. Account for the H1 RAII-destructor exception + display-only `std::string`.
- **#9 meta-registry enforcement + CLAUDE.md doc-fix** — wire `check_meta_registry.py` into `build.sh` (beside H17's `check_per_core_registry_integrity.py` at `:273`) and/or pre-commit; flip its Check 1 to FATAL; reconcile CLAUDE.md's 3 fictional check names. Also wire the orphan `check_storage_t_coverage.py` (H13).
- **#10 H16 check** — build `check_metadata_derived_filter_coverage.py` (or fold into check_meta_registry): every `CfgFieldDescriptor::MetadataFlag` bit (CfgFieldRegistry.hpp ~112-156) has a `FOREACH_DERIVED_FILTER` row OR a documented exemption. Wire it.
- **#11 OMS submit cap** — `qty>0 && finite && qty<=cap` at `OrderManager_Submit` (`OrderManager.hpp:901`). DECISION NEEDED: cap = cfg-driven `max_order_notional` (preferred, per-source/venue) OR a hard sane ceiling. The highest-value live-capital guard.
- **#12 H7/H8 asm branch-count gate** — new tool: `g++ -S` on the hot-path fns (`BG_Evaluate`/`SG_Evaluate`), count conditional jumps (`j*` excluding `jmp`), assert ≤ a frozen baseline. Deterministic + machine-independent; enforces H7 (branchless) + proxies H8 (latency, the #1 invariant with zero gate today). Makes the Ship-A manual `-S` check a STANDING gate.
- **#13 legacy phantom + snapshot checksum** — guard/retire the legacy `BuyGate`/`SellGate` (deprecated single-core; lowest priority — could retire with the legacy path); + CRC32 over the ShardedSnapshot body.

## Operator framing
"Guards are almost more important than the actual code — they scale over a lifetime" (memory
`feedback_guards_compound_enforcement_is_leverage`). This pass is the recurring practice that principle
endorses. Close per `feedback_opportunistic_tech_debt_closure` (subsumed → now; adjacent → tracked).
