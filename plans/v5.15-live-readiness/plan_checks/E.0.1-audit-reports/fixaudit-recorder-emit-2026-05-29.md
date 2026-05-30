# Fix-audit — Recorder emit locale-immunity (H2 / .E.0.1 Net-2)

**Date:** 2026-05-29 · **Engine HEAD:** 2492e43 · **Auditor:** independent adversarial fix-auditor
**Finding:** Replay determinism needs write∧read locale-immunity; plan fixes only PARSE side. Recorders WRITE locale-tainted floats via bare fprintf (`TickRecorder.hpp:186`, `DepthRecorder.hpp:249`).
**Proposed fix audited:** "Wrap the two emit bodies in canonical `newlocale/uselocale(C)` (sister to the 4 existing emit sites), NOT global setlocale."

**Verdict: the proposed fix is INCOMPLETE on two axes and picks the weaker of two structural options.**

---

## Decisive new finding (beyond the brief): the READ side is ALSO broken

GT (orchestrator) framed the parse side as "already fixed by the plan." It is NOT. Both replay readers use **`strtod`**, which is `LC_NUMERIC`-dependent — NOT `tt::parse_double_fast`:

- **Depth replay reader:** `DataStream/DepthReplayState.hpp:224-227` — `strtod(p,&p)` ×4 (bid/ask price/qty).
- **Tick replay reader:** `Backtest/BacktestEngine.hpp:88-96` — `strtod(p,&p)` for price/qty (both format branches).

`ParseFast.hpp:14` warns about exactly this hazard, yet the actual CSV-replay readers never adopted `parse_double_fast`. So under a non-C `LC_NUMERIC`, fixing only the WRITE side leaves the symmetric corruption on READ. **The net the fix is meant to enable is meaningless without closing the read side too.** Net-2 scope MUST include `strtod → tt::parse_double_fast` (or a `uselocale(C)` wrap of both bulk-load loops) at those two sites.

Cadence (verified): both readers are **bulk boot/day-boundary loads**, not per-tick — `DepthReplayState_LoadDay` (one fopen + ~7-8k-row loop, lazy on day advance) and `BacktestData_Load` (boot-time fill into `ticks[]`). So a single `uselocale(C)` wrap around each loop is effectively free, and `parse_double_fast` is strictly an upgrade.

---

## Per-question verdicts

### Q1 — uselocale-wrap vs locale-immune FORMATTER (to_chars)? → **to_chars is the BETTER, more structural option; it WINS on Caramel's gradient.**
- No `tt::format_double_canonical` / to_chars emit helper exists (confirmed; only `parse_double_fast` exists on the PARSE side — the emit-side analogue is absent).
- **`std::to_chars(buf, end, v, chars_format::fixed, 8)` is byte-identical to `printf("%.8f", v)`** — I compiled+ran it (g++ 16.1.1, `-std=c++17`) across {3.14159265, 0.1, 12345.6789, 1e-8, 99999.99999999, 0.0, 2.5}: **all SAME**. So a to_chars emit reproduces the existing wire bytes exactly (no golden churn) AND is locale-immune **by construction** — `to_chars` ignores `LC_NUMERIC` per the standard, same property that makes `from_chars` the parse primitive.
- This is the emit-side mirror of "parse side uses from_chars": **eliminate the dependency structurally** beats **pin the locale per call**. Per Caramel's gradient (structural/eliminate-dependency > pin-per-call) + single-source-of-truth, to_chars is the correct answer. A `tt::format_double_fixed(buf,cap,v,prec)` helper in `ParseFast.hpp` (renamed scope, or a sibling `FormatFast.hpp`) becomes the canonical emit primitive — symmetric to `parse_double_fast`, reusable by future recorders/CSV writers (foreseeable recurrence → framework discipline).
- Caveat: the canonical-SISTER-fidelity argument favors uselocale (4 existing sites use it). But those 4 are all rare cfg-save/stamp-emit paths; none is a per-tick hot writer, and none had a locale-immune formatter available. Adopting to_chars here ESTABLISHES the better sister rather than propagating the weaker one. Recommend codifying as the emit-side canonical (DESIGN_SPEC + note the 4 uselocale sites as candidates to migrate later — do NOT churn them in Net-2).

### Q2 — latency / per-call newlocale cost? → **REAL hazard for the uselocale option; NON-issue for to_chars.**
- All canonical sisters do `newlocale`+`freelocale` **once per save-call** wrapping a whole emit burst (`BanditLearning.hpp:462/521-523`; `ModelInference.hpp:1827/1943-1945`; `CfgFieldDispatch.hpp:188/219, 341/367`). **None caches `locale_t`** — because none runs per-tick.
- The recorders DO run per-emit: `TickRecorder_Push` per tick, `DepthRecorder_Write` per ~10Hz snapshot. A NAIVE "wrap the fprintf" applies `newlocale`+`freelocale` **per row** — each `newlocale` ALLOCATES a locale object. That is the wrong pattern: it can spike the <100μs async budget and churns the allocator on a path advertised "allocation-free per-snapshot" (`DepthRecorder.hpp:29`).
- If uselocale is chosen anyway, it MUST be a **cached `locale_t` created once in `_Init`, `uselocale`-swapped around the single fprintf, freed in `_Close`** — NOT per-call newlocale. The proposed-fix wording ("wrap the emit body … sister to the 4 sites") would, taken literally, reproduce the per-call newlocale of those sites → wrong here.
- **to_chars sidesteps this entirely**: zero allocation, no locale object, no per-call syscall — formats into the stack buffer then one `fputs`/`fwrite`. Strictly better on the async budget.

### Q3 — thread-safety / re-entrancy? → **uselocale is per-thread-safe but adds a save/restore footgun; to_chars has none.**
- Recorders run on async threads (DepthRecorder via `depth_thread`, both M5 LIVE-only). `uselocale` is per-thread, so no cross-thread contamination — fine in principle.
- BUT: if that thread does any OTHER locale-sensitive formatting between recorder calls (e.g. `fprintf(stderr, ...)` diagnostics, rotation log lines at `:101/:118`), a cached-locale design that swaps in C only around the data fprintf is correct, but a careless "swap C at first write, never restore" would silently re-locale the whole thread. Save/restore discipline (store prev, restore after) is mandatory and easy to get subtly wrong. to_chars carries **no thread-global state** → no re-entrancy surface at all. Another point for to_chars.

### Q4 — completeness of replay-feeding WRITE emits? → **GT1 CONFIRMED for writes; but see read-side gap (above).**
- Authoritative DataStream float-emit list: `TickRecorder.hpp:186`, `DepthRecorder.hpp:249` (replay-feeding); `TradeLog.hpp:92/105` (output-only log, not replayed → F-107/pre-paper-test, correctly out of net-gating scope); `BinanceOrderAPI.hpp:538/583/726` (all `stderr` diagnostics, not files). So **186 + 249 are the only replay-feeding float WRITES — GT1 holds.**
- Integer-only lines are safe (`LC_NUMERIC` affects only float radix): both readers' `strtoull/strtoll` and the writers' `%lld/%llu/%d` are unaffected.
- **Header / column-name lines are safe** (`TickRecorder.hpp:96`, `DepthRecorder.hpp:113` — pure ASCII literals) and the **`# GAP` marker** (`DepthRecorder.hpp:203`) emits only `%llu`/`%s` — no float → unaffected, and readers skip `#` lines anyway.
- Gap NOT in GT1: the **READ side strtod** (Q-decisive finding). The write-side enumeration is complete; the FINDING's scope is not.

### Q5 — is to_chars usable here (C++17 / libstdc++ float-to_chars)? → **YES, unconditionally on this toolchain.**
- Build is `CMAKE_CXX_STANDARD 17` (CMakeLists.txt). Toolchain g++ 16.1.1 / libstdc++ — float `to_chars` shipped in libstdc++ **11**; this is far past it. Compiled+ran cleanly above. No `<charconv>` float-support gap.
- (Historical note only: libstdc++ <11 lacked float `to_chars`. Irrelevant to this machine; flag only if a CI image pins an ancient gcc — verify the CI container, but the dev toolchain is fine.)

---

## RANKED recommendation (Caramel's gradient: structural/eliminate-dependency > pin-per-call; sister fidelity)

1. **WRITE side — adopt `std::to_chars(…, chars_format::fixed, 8)` via a new `tt::format_double_fixed` emit primitive** (sibling to `tt::parse_double_fast`; house in `ParseFast.hpp` or a new `FormatFast.hpp`). Byte-identical to `%.8f` (verified), locale-immune by construction, zero-alloc, no thread-global state, no per-call newlocale. Replace the float fields in `TickRecorder.hpp:186` + `DepthRecorder.hpp:249` (keep `%lld/%llu/%d` integer parts via the existing fprintf or compose into one buffer). This is the emit-side analogue of the parse side's from_chars and the structurally-correct fix.
2. **READ side (MUST be in the same Net-2 ship) — replace `strtod` with `tt::parse_double_fast` at `DepthReplayState.hpp:224-227` + `BacktestEngine.hpp:88-96`.** Without this the write-side fix is half a fix; the determinism net is the WRITE∧READ symmetry, and the read side is currently the bigger latent corruption (strtod, not parse_double_fast, on the actual replay path). Bulk-load cadence → no latency concern.
3. **Fallback if to_chars is rejected (e.g. ancient CI gcc):** uselocale — but **cached `locale_t` in `_Init`/`_Close`, save/restore prev around the single fprintf**, NEVER per-call newlocale. Inferior on every axis (alloc, thread-global footgun, sister-but-weaker) but acceptable.
4. **Do NOT** churn the 4 existing uselocale sites in Net-2 (rare paths, byte-stable, out of scope) — flag them as a later migration-to-to_chars candidate only.

**Side-effect verdict:** to_chars = no latency/thread risk. Naive uselocale-per-call = real async-budget + allocator risk (must cache).
**Completeness verdict:** write-side GT1 confirmed; finding's PARSE-side "already fixed" premise is FALSE — strtod at both readers is a co-equal net-gating gap that must ship with the write fix.
