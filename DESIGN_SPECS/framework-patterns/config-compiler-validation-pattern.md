---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-06-23
landing_ship: v5.15.5.F.4d.1.E.1.1
canonical_applications:
  - v5.15.5.F.4d.1.E.1.1 (the ③ config-compiler — capital + feature cfg validation gate)
tags: [framework-discipline, capital-safety, config-validation, ssot, structural-fix, pattern-codification]
surface: [cfg-flow, parser, boot-time, capital-allocation, multi-exchange-substrate]
sister_specs: [universal-cfg-field-registry-pattern.md, single-authority-predicate-for-mode-gating.md, hierarchical-config-validation-pattern.md, locale-determinism-discipline.md, metadata-bit-driven-derived-filter-framework.md, single-source-of-truth-discipline.md, representation-migration-completeness.md]
applies_at_skills: [/precoding-audit-gate, /readiness, /accounting-audit, /parity-check]
---

# Config-compiler validation pattern — collect-all-faults, gate-the-run, single-source-the-capture

**Established:** 2026-06-23 (v5.15.5.F.4d.1.E.1.1 — the ③ arc; "config compiler" reframe per decision-log D-242)
**Status:** **ACTIVE — Stage 3 (first-canonical).** First canonical reference = the `.E.1.1` ③ config-compiler (`ControllerConfig_Load` capital + feature validation + the N1 sibling `BinanceConfig_Load`).
**Cross-references:**
- Sister (the registry walker this EXTENDS): `universal-cfg-field-registry-pattern.md` — the `FOREACH_CFG_FIELD` walker already does KIND-driven malformed-capture for FLAT registry fields (`tt::cfg_parse_field` writes `CFG_FAULT_CAPITAL_MALFORMED` at `CfgFieldDispatch.hpp:104`). This pattern carries the SAME fault model into the channels the walker does NOT reach: the per-node OVERRIDE channel, the legacy ARRAY parsers, the manual-parsed GLOBAL fee rates, and the SIBLING boot parser. Do NOT reinvent the walker — extend its fault model outward.
- Sister (SSoT predicate): `single-authority-predicate-for-mode-gating.md` — the universal-gate part (§ 2) is a single-authority predicate over the fault bitmap, same shape as `ControllerConfig_IsLiveCapital`.
- Sister (cross-file extension): `hierarchical-config-validation-pattern.md` — the E.2 cross-reference validation (per-node references a valid cluster, credentials parseable) composes ON TOP of this pattern's per-parser fault bitmap; the boot gate refuses on the union.
- Sister (the determinism reason #4 exists): `locale-determinism-discipline.md` — `atof`/`atoi` are `LC_NUMERIC`-dependent; the checked parse primitives (`parse_double_fast_checked` / `parse_int_checked` / `Money_FromString`) are locale-immune `std::from_chars`-backed.
- Sister (single-source the computation): `single-source-of-truth-discipline.md` — #4 is the parse-primitive SSoT; #2 is the gate SSoT.
- Anti-patterns this pattern cures / sisters: **Class 52** (swallow-and-coerce — the silent `atof`/`Money_FromString().value` →0 default that #4 cures) · **Class 53** (rename-completeness-gap — sibling cfg-integrity, the `core_`→`node_` retired-prefix surface #3 refuses). *(Class 52/53 are allocated to this arc; codify at ③ ship-close per `pattern-codification-lifecycle.md`.)*
- Decision log: `plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md` — D-242 (config-compiler model) → D-253 (capital-validation FINAL) → D-254 (coding shape + the MALFORMED-gap hybrid) → D-255 (converged foundation scope; B1 unit-agnostic malformed-refuse) → D-256 (item-2 scope restoration) → forward D-257..D-26x (this arc).
- CLAUDE.md: H4 (`Money` for money math), H5 (no `atof` in parsers), H22 (per-node purity — every parser validates its OWN fields), item 19 (structural fix preferred), item 13 (X-macro registry).

---

## Problem statement

A config parser that **silently coerces a malformed or out-of-range value to a default** is a capital-safety hole. The founding instances (all code-verified at HEAD in the ③ pre-coding cascade):

| Input | Old behavior | Consequence |
|---|---|---|
| `node_0_stop_loss_pct=banana` | `Money_FromString("banana").value` → `0`, `.flags` DISCARDED | stop-loss silently **disabled** |
| `node_0_risk_pct=999` | parsed, never range-checked | 999% live allocation (`Run.hpp:924`) |
| `node_0_max_drawdown_pct=999` | parsed, never range-checked | kill-switch silently **dead** |
| `fee_rate_taker=1,5` (locale comma) | `atof`/`Money_FromString` → `0` | silent **0% fee** accounting |
| `use_testnet=banana` | `atoi` → `0` | testnet → **PRODUCTION** (`atoi` swallow) |
| `core_0_stop_loss_pct=...` | a RETIRED key prefix, silently ignored | the operator's setting **vanishes** |

The unifying failure: **`→0` is the dangerous value**, and the parse machinery throws away the signal (the malformed flag / the out-of-range condition / the unrecognized-key fact) that would have caught it. The `Money_FromString().value` form discards `.flags`; `atof`/`atoi` collapse "not a number" into `0`; an unrecognized key falls through to a no-op. Each is a *silent-disable on the money path*.

The reframe (D-242): treat cfg load as a **compile**. A verify-pass collects ALL faults; a clean compile GATES the run; a malformed/out-of-range/unknown input is a *compile ERROR*, not a silent default. The walker in `universal-cfg-field-registry-pattern.md` already does this for FLAT registry fields — but a real config has **four channels the walker never sees** (per-node overrides, legacy arrays, manual-parsed globals, a sibling parser reading the same file). The config-compiler pattern carries one fault model across all of them.

---

## Design — five composable parts

The pattern is FIVE parts. Each is independently useful; together they form the config compiler. Engine cites below are confirmed at HEAD `be5d803`.

### Part 1 — Fault-bit taxonomy (distinct bits per fault CLASS, each with a severity)

A single per-struct `uint32_t cfg_load_fault_flags` (`ControllerConfig.hpp:581`) with DISTINCT bits per fault CLASS, each carrying a severity in its definition comment (`CfgFieldRegistry.hpp:224-227`):

```cpp
// CoreFrameworks/CfgFieldRegistry.hpp:224-227  (③ D-254)
inline constexpr uint32_t CFG_FAULT_CAPITAL_MALFORMED    = 1u << 0;  // parse-point: a CAPITAL field MALFORMED/OVERFLOW (banana / 1,5 / 1.5% / saturated) — ALWAYS-FATAL
inline constexpr uint32_t CFG_FAULT_CAPITAL_OUT_OF_RANGE = 1u << 1;  // post-resolve sweep: a CAPITAL value exceeded the no-margin cap (loss>100% / gain>1000%) — ALWAYS-FATAL
inline constexpr uint32_t CFG_FAULT_UNKNOWN_KEY          = 1u << 2;  // loop-tail: an unrecognized SHARDED key (core_*/node_*) — typo / retired-prefix / out-of-range index
inline constexpr uint32_t CFG_FAULT_FEATURE_MALFORMED    = 1u << 3;  // parse-point: a non-capital FEATURE field MALFORMED — determinism-bearing, policy-call severity
```

**KEY DISCIPLINE — distinct bits, NEVER merge two severities into one bit.** A malformed *capital* value (always-fatal — a disabled stop-loss is unconditionally unsafe) and a malformed *feature* value (a determinism-bearing policy call — refuse-don't-coerce, but a different severity surface) MUST stay separable. Merging them into one bit is a **Class-49 signal-merge** (a distinguishing signal collapsed upstream of the branch that must distinguish it): a downstream policy that wants to treat feature-malformed differently from capital-malformed is *structurally blind* once the two share a bit. The comment on `CFG_FAULT_FEATURE_MALFORMED` records exactly this ("DISTINCT from CAPITAL_MALFORMED to keep the severities separable — no Class-49 merge").

**Headroom note.** `uint32_t` has 28 free bits — the widen pressure is on the SEPARATE `metadata_flags uint16_t` (the `CfgFieldDescriptor::MetadataFlag` bitmap, guarded by the overflow `static_assert` at `CfgFieldRegistry.hpp:218`), NOT this fault word. Per D-255/D-256-B1, making malformed-refuse unit-agnostic consumes ZERO fault bits, so a new fault CLASS gets its own bit cheaply.

### Part 2 — Universal gate (ONE predicate; every load path routes through it)

ONE predicate over the fault word, plus a single-source REPORT wrapper:

```cpp
// CoreFrameworks/ControllerConfig.hpp:1333  (③ D-254) — the predicate (bool; testable)
template <unsigned F>
inline bool cfg_compile_ok(const ControllerConfig<F>& cfg) {
    return cfg.cfg_load_fault_flags == 0u;
}

// CoreFrameworks/ControllerConfig.hpp:1344  (③ D-255 C-1) — single-source the gate REPORT
template <unsigned F>
inline bool cfg_capital_gate_ok(const ControllerConfig<F>& cfg, const char* who) {
    if (cfg_compile_ok(cfg)) return true;
    fprintf(stderr, "[%s] FATAL: capital cfg validation failed (flags=0x%x) -> REFUSED. ...\n",
            who, (unsigned)cfg.cfg_load_fault_flags);
    return false;
}
```

`cfg_compile_ok := (cfg_load_fault_flags == 0)` is a single-authority predicate (sister to `single-authority-predicate-for-mode-gating.md`). The wrapper `cfg_capital_gate_ok(cfg, who)` is the single-source REPORT so EVERY boot path emits the *same* reasoned FATAL line and cannot silently skip the gate. **Boot REFUSES on ANY bit set, all modes, no-margin (D2)** — a bool not an `exit()` so tests can assert it and a hot-reload typo can't kill a running engine (it responds context-appropriately: engine returns 1 / backtest fails the run / GUI keeps-old).

**THE DISCIPLINE: a cfg parser that doesn't gate is a hole.** Pre-D-255 only `main.cpp` gated → the suite/backtest ran a malformed cfg with a silently-disabled stop. Caller coverage (GAP-1, closed at `be5d803`):

| Caller | Site | Status |
|---|---|---|
| Engine boot | `main.cpp:203` | gated |
| Sharded backtest | `Backtest/BacktestSharded.hpp:125` | gated |
| Backtest optimizer (GUI suite base cfg) | `Backtest/BacktestEngine.hpp:2370` | gated (was the GAP-1 ungated caller; closed `be5d803`) |
| GUI Settings reload | (Settings_Load) | observability-not-safety (keeps-old; not a capital authority) |
| EngineTUI | (legacy) | legacy path; slated for delete |

The discipline is: enumerate EVERY cfg-load caller and route each through the gate (4 of 6 were ungated when the arc opened). A recurrence guard enforces caller-coverage going forward.

### Part 3 — Scoped loop-tail unknown-key refuse (scope to the namespace the parser EXCLUSIVELY owns)

At the parse loop tail (reached only when no handler matched — every handler `continue`s), an unrecognized key in the parser's EXCLUSIVE namespace → fault + refuse:

```cpp
// CoreFrameworks/ControllerConfig.hpp:~3135  (③ D-223/D-255, clean-break) — SCOPED loop-tail refuse
if (strncmp(key, "core_", 5) == 0) {              // RETIRED prefix (the .E.1.1 Core->Node rename)
    cfg.cfg_load_fault_flags |= CFG_FAULT_UNKNOWN_KEY;
    fprintf(stderr, "[cfg] FATAL: '%s' uses the RETIRED 'core_' key prefix -> rename to 'node_%s'. ...\n", key, key + 5);
} else if (strncmp(key, "node_", 5) == 0) {       // a typo / out-of-range index / retired field
    cfg.cfg_load_fault_flags |= CFG_FAULT_UNKNOWN_KEY;
    fprintf(stderr, "[cfg] FATAL: '%s' is an unrecognized per-node key ...\n", key);
}
```

**THE CRITICAL DISCIPLINE: scope the refuse to the namespace this parser EXCLUSIVELY owns** (here, `core_*` / `node_*`). In a multi-parser shared-cfg-file setup, a non-namespace unknown key may legitimately belong to a SIBLING parser. In the engine, `BinanceConfig_Load` AND `ControllerConfig_Load` read the SAME file (`main.cpp:75` + `:76`) — `BinanceConfig` reads `use_testnet`/`symbol`/... from it. A naive **all-unknown refuse would FALSE-REFUSE** a sibling parser's valid key and break boot.

Exclusivity MUST be verified before scoping to a namespace (the code comment records the proof for this surface): the per-node block above is the SOLE `node_` handler, NO `core_` handler survives the Core→Node rename, and `BinanceConfig` owns no `core_`/`node_` key. The **broader global-unknown-key refuse is deliberately deferred** — it requires the multi-parser UNIFICATION first (homed to E.2; ③'s scoped refuse already covers the retired-prefix + per-node hole). This is `cfg-scope-discipline.md` applied at the refuse surface: the refuse is only safe over keys the parser provably owns.

### Part 4 — Single-source-at-parse-primitives (refuse-don't-coerce, locale-immune)

Every cfg WRITE of a given KIND routes through ONE capture primitive that returns the value AND records a fault on malformed input — never the bare swallow-to-default form:

| KIND | Capture primitive | SSoT it routes through | Cite |
|---|---|---|---|
| capital money | `cfg_capture_node_money_override(cfg, key, val, pct_scale, empty_is_fault=false)` | `Money_FromString` (checks `MONEY_PARSE_MALFORMED \| MONEY_PARSE_OVERFLOW`) | `ControllerConfig.hpp:1364` |
| global fee rate (money) | same primitive, `empty_is_fault=true` (boundary-stable defaulted param) | `Money_FromString` | `ControllerConfig.hpp:2342`/`:2347` |
| raw feature (double) | `cfg_capture_node_raw_override(cfg, key, val)` | `tt::parse_double_fast_checked` | `ControllerConfig.hpp:1391` / `ParseFast.hpp:59` |
| int | `tt::parse_int_checked(s, &malformed)` | locale-immune `std::from_chars` | `ParseFast.hpp:74` |

```cpp
// CoreFrameworks/ControllerConfig.hpp:1364  (③ D-256 b/c + B) — the capital-money capture SSoT
template <unsigned F>
inline Money cfg_capture_node_money_override(ControllerConfig<F>& cfg, const char* key,
                                             const char* val, bool pct_scale, bool empty_is_fault = false) {
    MoneyParse mp = Money_FromString(val);
    bool empty = (val[0] == '\0');
    bool bad   = (mp.flags & (MONEY_PARSE_MALFORMED | MONEY_PARSE_OVERFLOW)) != 0;
    if ((bad && !empty) || (empty && empty_is_fault)) {
        cfg.cfg_load_fault_flags |= CFG_FAULT_CAPITAL_MALFORMED;
        fprintf(stderr, "[cfg] FATAL: money cfg field %s='%s' is %s -> boot REFUSED ...\n", key, val, /*reason*/);
    }
    // ... value path BYTE-IDENTICAL to the old bare-.value form for every accepted input ...
}
```

Properties:
- **ONE capture site, ONE shared fault bit** — `node_N_risk/maxdd` arrays, the `_PARSE_OV_PCT` override macro, the 3 hand-rolled money outliers (`fee_floor_mult`/`partial_exit_pct`/`tp2_mult`), and the manual-parsed global fee rates ALL route through this one primitive. No parallel mirror per channel (that would be Class-18: N capture-bodies that drift).
- **refuse-don't-coerce** — MALFORMED/OVERFLOW always faults (capital). The bare `.value` form discarded `.flags` → the founding silent-disable.
- **locale-immune** — `Money_FromString` / `parse_double_fast_checked` / `parse_int_checked` are `std::from_chars`-backed; this is the `atof`/`atoi` `LC_NUMERIC`-swallow (Class 52) that the primitives REPLACE (`locale-determinism-discipline.md`).
- **boundary-stable extension** — the `empty_is_fault` defaulted param extends one primitive to two empty-policies (per-node overrides have a documented "empty/0 = inherit" sentinel → empty is clean; a global fee rate has no inherit → empty is operator error) without forking the function.
- **EMPTY ≠ MALFORMED** — `from_chars` on empty returns clean (the "empty = default/inherit" cfg convention); only a NON-EMPTY unparseable string faults.

This beats per-channel bolt-ons (which leave N channels each needing its own fix and each able to drift). Sister: **Class 52** (the swallow-and-coerce anti-pattern this part cures).

### Part 5 — Second-parser reuse (each parser validates its OWN fields; the boot gate refuses on the UNION)

A SIBLING boot parser reading the SAME cfg file reuses the entire model — its own fault word + its own `*_ok()` predicate + a boot-gate refusal on ITS faults:

```cpp
// DataStream/BinanceCrypto.hpp  (N1 — ③ reuse)
struct BinanceConfig { ...
    uint32_t cfg_load_fault_flags = 0;  // :72  — set on a MALFORMED venue selector
};
inline constexpr uint32_t BINANCE_CFG_FAULT_VENUE_MALFORMED = 1u << 0;  // :841
// ... BinanceConfig_Load sets it via parse_int_checked on use_testnet/use_binance_us ...
inline bool binance_config_ok(const BinanceConfig& c) { return c.cfg_load_fault_flags == 0u; }  // :855

// main.cpp:207 — the boot gate refuses on the SIBLING's faults too
if (!binance_config_ok(bcfg)) { /* REFUSE — a malformed use_testnet would silently flip to PRODUCTION */ }
```

**The multi-parser config-compiler = each parser validates its own fields; the boot gate refuses on the UNION.** A malformed `use_testnet`/`use_binance_us` would silently flip testnet → PRODUCTION (the `atoi`-swallow). `BinanceConfig` carries its own per-struct fault word and `binance_config_ok()` predicate (Part 1 + Part 2, replicated per parser), parses its selectors through `parse_int_checked` (Part 4), and `main.cpp` refuses boot on either parser's faults. This is the seam that scales to `.E.1` multi-exchange: a new exchange adapter parser adds its own fault word + `*_ok()` + a clause in the union-gate, and validates its own fields — per-node-purity (H22) at the parser layer.

---

## Why these five compose (and don't overlap)

| Part | Concern | Without it |
|---|---|---|
| 1 Fault-bit taxonomy | a place to RECORD distinct fault classes with severities | merged severities → Class-49 blind branch |
| 2 Universal gate | ONE predicate every loader routes through | ungated parser = a silent-disable hole (GAP-1) |
| 3 Scoped unknown-key refuse | catch typo'd/retired keys in the OWNED namespace | operator's setting silently vanishes; or false-refuse a sibling's key |
| 4 Parse-primitive SSoT | refuse-don't-coerce at the WRITE, once per KIND | swallow-to-0 (Class 52) on N un-fixed channels |
| 5 Second-parser reuse | each parser validates its own fields; gate on the union | a sibling parser's malformed selector silently flips to the dangerous default |

Parts 1+2 are the *substrate* (record + gate). Parts 3+4+5 are the three *capture surfaces* the walker (`universal-cfg-field-registry-pattern.md`) doesn't reach: the loop-tail, the override/legacy/global channels, and the sibling parser. The walker handles FLAT registry fields and writes the same `CFG_FAULT_CAPITAL_MALFORMED` bit (`CfgFieldDispatch.hpp:104`) — so the walker is effectively a 6th surface already living inside the same fault model. **Do not reinvent the walker; extend its fault model to the channels it can't see.**

---

## The out-of-range half — the post-resolve range sweep (item-4, the founding-bug closure)

Parts 1-5 catch a MALFORMED value at the parse point. The HYBRID's other half catches a VALID-but-out-of-range value (`risk_pct=999`) at a **post-resolve sweep** — it can't be caught at parse (the value parses fine, and `0` is a legit sentinel a post-resolve sweep also can't distinguish from malformed, which is why the two are SEPARATE bits). `ControllerConfig_CapitalRangeSweep` runs in `ControllerConfig_Load` AFTER `PopulateCoresFromFlat` (nodes[c] resolved, 0=inherit collapsed) and sets `CFG_FAULT_CAPITAL_OUT_OF_RANGE`. Four reusable disciplines it adds:

- **Enumerate from the registry, dispatch on the metadata bit.** The sweep is an `if-constexpr` X-macro walk over `FOREACH_PER_NODE_CFG_FIELD` reading `nodes[c].<name>`, branching on `CAPITAL_BOUND_LOSS`/`GAIN` (mirrors `EMIT_PER_NODE_COPY`). The per-node masks (`g_per_node_cfg_capital_bound_*`) are FIELD_IDX bitmaps with NO FIELD_IDX→`nodes[c]` accessor — the walk, not a mask read, is the feasible + forward-extensible mechanism.

- **Deletable-by-construction global-flat leg.** Two fields (`risk_pct`/`max_drawdown_pct`) carry `0=inherit` in `nodes[c]` (the legacy-array channel), so an inheriting node's effective value is the GLOBAL flat — a `nodes[c]`-only sweep MISSES a global `risk_pct=999` (the founding bug via the most-common config). The global-flat checks are driven OFF `FOREACH_PER_NODE_ARRAY_OVERRIDE` (the SAME registry that defines those fields), so they AUTO-DISSOLVE when E.1.2 deletes the arrays — zero hand-cleanup ([[feedback_prefer_deletable_cascade_over_tombstone]]; D-278).

- **Exhaustiveness tripwire.** A standalone per-field `static_assert` (`ALL_CAPITAL_BOUND_VARIANTS & ~CAPITAL_BOUND_SWEEP_HANDLED`) makes a future `CAPITAL_BOUND_*` variant tagged WITHOUT a sweep branch a COMPILE ERROR — "forgot the branch" becomes a build failure (vacuous until E.1.6 widens the variant set). **Keep it STANDALONE, never inside the walk's `if-constexpr else`** — a non-dependent `static_assert` in a discarded `if constexpr` branch fires at definition (it would reject every handled field).

- **Caller coverage extends to range too.** The same gate (`cfg_capital_gate_ok`) covers the optimizer `config_override` path via a range-ENDPOINT probe (`BacktestEngine.hpp` — refuse the sweep range, don't silently skip points; `ConfigField_Set` mutates the flat without re-resolving, so the global-flat leg reading the fresh flat is what catches it).

**Boot-time → branchless EXEMPT (H7/H20).** The sweep runs once at load, so a per-field `if`+operator-FATAL diagnostic (which NAMES the bad field) is preferred over a branchless mask-accumulate (which loses the field identity). REFUSE, never clamp — clamping an out-of-range capital value is the Class-52 swallow-and-coerce this whole pattern exists to kill (D2).

---

## Robustness analysis

### What this closes

- **Silent-wrong-VALUE on capital** (the founding stop-loss-typo / 999%-risk / dead-kill-switch / 0%-fee cases) — refuse at the parse point (malformed) + the post-resolve sweep (out-of-range).
- **Silent-wrong-KEY** (typo'd / retired-prefix per-node keys) — the scoped loop-tail refuse.
- **Silent testnet→PRODUCTION** flip — the sibling parser's checked int parse + union gate.
- **Ungated callers** (GAP-1) — every fresh-start caller routes through `cfg_capital_gate_ok`.

### Trade-offs / when NOT to apply

- **Empty-is-fault is a per-field policy, not a global.** A field with a legitimate "empty = inherit/default" sentinel MUST use `empty_is_fault=false`; only a field with no inherit (a global rate) uses `true`. Getting this backwards either false-refuses a valid empty or accepts a dangerous empty. (The defaulted param keeps the decision per-call-site, visible.)
- **Scope-before-refuse is mandatory for the unknown-key part.** Never globally-refuse unknown keys in a shared-cfg-file, multi-parser setup until the parsers are unified — verify namespace exclusivity first (Part 3). The broader global refuse is a deferred E.2 item, not a ③ shortcut.
- **Don't over-narrow the malformed bit to one unit.** Per D-255/D-256-B1, malformed-refuse is unit-agnostic for all decimal-`Money` cfg (it consumes 0 extra fault bits and restores D-242's config-compiler intent); narrowing it (e.g., a `CAPITAL_BOUND_DOLLAR`-only bit) was rejected as premature.
- **Out-of-range (Part of the taxonomy, bit 1) is a SEPARATE sweep.** A MALFORMED value (`banana`→0) is caught at the parse point; an out-of-range value (`risk_pct=999`) is a VALID number and is caught at the post-resolve sweep. The two cannot be merged — a post-resolve sweep CANNOT catch malformed (0 is a valid sentinel that passes the sweep — D-254 ADDENDUM). This is why the pattern is a HYBRID: parse-point malformed-capture + post-resolve range-sweep.

### What this enables (forward)

- **`.E.1` multi-exchange** — Part 5 is the seam: per-exchange parser, per-struct fault word, union gate. No change to existing per-parser logic to add the (N+1)th (H22).
- **E.2 cross-file validation** — `hierarchical-config-validation-pattern.md` composes on top: cross-reference checks (per-node → valid cluster, credentials parseable) write into the same per-parser fault model; the boot gate refuses on the union.
- **The non-capital value-sweep** — feature fields get the same parse-point refuse via `CFG_FAULT_FEATURE_MALFORMED` (distinct bit, distinct severity); the systematic semantic sweep is E.2's extension into the same structure.

---

## Implementation checklist

When adding a config-compiler validation to a parser:

1. **Add a `uint32_t cfg_load_fault_flags` field** to the parsed struct (zero-init).
2. **Define DISTINCT fault bits** per fault CLASS with a severity comment; NEVER merge two severities into one bit (Class-49).
3. **Add a `*_compile_ok()` predicate** (`== 0`) + a `*_gate_ok(cfg, who)` single-source REPORT wrapper.
4. **Route EVERY value WRITE through a checked capture primitive** (`Money_FromString` / `parse_double_fast_checked` / `parse_int_checked`) — never `atof`/`atoi`/`.value`-discard.
5. **At the loop tail, refuse unrecognized keys SCOPED to the namespace this parser EXCLUSIVELY owns** — verify exclusivity against sibling parsers first.
6. **Enumerate EVERY caller** of the parser and route each fresh-start caller through the gate (observability-only callers keep-old).
7. **For a sibling parser on the same file**, replicate 1-6 for its fields; the boot gate refuses on the UNION of all parsers' fault words.

When adding a new cfg field of an existing KIND: it inherits the capture primitive automatically (the WRITE already routes through the SSoT) — no new validation code.

---

## Field-test plan

The ③ arc (`v5.15.5.F.4d.1.E.1.1`) is the first canonical application:
- **D-254 step 2/3** — `cfg_load_fault_flags` bitmap + parse-point flat-path malformed-capture (the walker).
- **D-255 C-1** — single-source the capital gate + wire backtest/suite.
- **item-2** — migrate the 4 capital globals into the registry; per-node override + legacy-array malformed-capture.
- **B1** — unit-agnostic malformed-refuse (decouple from the cap bit).
- **GAP-1** — gate the backtest optimizer's base cfg (caller coverage).
- **N1** — `BinanceConfig_Load` sibling-parser reuse.
- **item-4** — the post-resolve OUT_OF_RANGE sweep (`ControllerConfig_CapitalRangeSweep`): the if-constexpr walk + the deletable-by-construction global-flat leg + the exhaustiveness tripwire + the optimizer range-endpoint gate (the founding-bug closure for VALID-but-out-of-range capital; see "The out-of-range half" above; D-277).

Each sub-ship is independently build-gated (micro-commits); a V-class verify gate runs on the shipped capital path. Codify Class 52 (swallow-and-coerce) + Class 53 (rename-completeness-gap) + this spec at ③ ship-close.
