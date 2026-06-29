# Class 54 — Validation asymmetry across write paths (one channel validates, a sibling silently doesn't)

> Codified 2026-06-29 at v5.15.5.F.4d.1.E.1.1 (the ③ config-compiler ship-close codification slate, D-271/D-280). Per-class file per file-size-split-discipline. **H-promotion deferred to Stage 5** per pattern-codification-lifecycle.

## Shape

A cfg/config value reaches its stored slot via **MULTIPLE write channels** — the flat registry walker, the per-node OVERRIDE capture, a legacy ARRAY parser, a manual-parsed GLOBAL, the hot-RELOAD path, the optimizer `config_override` clone — but only **SOME channels validate** (malformed-capture / range-check / gate) while sibling channels silently don't. The value can then arrive **unvalidated via the un-checked channel**, and every downstream check that assumed "this field is validated" is structurally blind to it.

This is the **founding-bug surface** of the ③ config-compiler: the flat walker malformed-captured (`CFG_FAULT_CAPITAL_MALFORMED`), but the per-node override channel, the legacy capital arrays, the hot-reload, and the optimizer clone each reached the same field WITHOUT that capture — so `risk_pct=banana` / `risk_pct=999` was caught on one path and swallowed on another. It is the per-CHANNEL sibling of Class 52 (which is the per-PRIMITIVE swallow); Class 52 says "the parse primitive coerces", Class 54 says "one channel uses the safe primitive and a sibling channel doesn't".

## Detection heuristic

For a capital/config field, enumerate **EVERY write channel** that can set it, and ask of each: does it route through the validation SSoT?
- the flat registry walker (`tt::cfg_parse_field` → `Money_FromString.flags` / `parse_double_fast_checked`);
- the per-node OVERRIDE capture (`cfg_capture_node_money_override` / `_raw_override`);
- legacy ARRAY / manual-parsed parsers (do they discard `.flags` / use unchecked `atof`/`parse_double_fast`?);
- the post-resolve out-of-range SWEEP (does it read the RESOLVED value, channel-agnostically, or only one channel's storage? — see Class 55);
- the GATE caller-coverage (does every fresh-start materialization route through `cfg_capital_gate_ok` — boot, backtest, optimizer-base, RELOAD?).

**A channel that reaches the field but skips the validation the other channels apply = this class.** Discriminator: *if the operator sets the field via path B instead of path A, is it still validated?*

## Structural fix

1. **Single-source the validation at the parse PRIMITIVE** (Class 52's fix) so every channel that writes a value inherits the malformed-refuse.
2. **A post-resolve sweep that is CHANNEL-AGNOSTIC** — it reads the RESOLVED value (`nodes[c]` after `PopulateCoresFromFlat`) + the global flat, not a single channel's raw storage, so it can't be bypassed by writing through a different channel. (The 2 legacy-array fields additionally need a flat-scalar leg because their resolved `nodes[c]` carries the 0=inherit sentinel — item-4 F1.)
3. **Caller-coverage on the gate** — every fresh-start cfg materialization routes through `cfg_capital_gate_ok` / `cfg_compile_ok` or is EXEMPT-with-reason; enforced by `tools/check_cfg_gate_caller_coverage.py` (item-6) + the no-`MANUAL_PARSER`-on-a-capital-row `static_assert`.

The config-compiler's five parts (`config-compiler-validation-pattern.md`) ARE this structural close: one fault model carried across every channel the walker can't see.

## Known instances (the ③ arc)

| Channel that skipped validation | Fix |
|---|---|
| per-node OVERRIDE + legacy-array malformed-capture (the walker captured the flat, not these) | item-2 (`890b368`/`98267be`) |
| GLOBAL-inherit out-of-range: `nodes[c]==0` inherit → the global flat un-swept (the F1 hole) | item-4 (`6981c85`) — the flat-scalar leg |
| hot-RELOAD path un-gated (`Async.hpp:321`) — a reloaded `risk_pct=999` applied live | item-5 (`d8fe6c6`) |
| optimizer `config_override` clone un-gated (`BacktestEngine.hpp:2381`) | item-4 F2 — the range-endpoint probe |
| ~47 FEATURE fields: walker captured capital, not the FPN/float branches | C1/C2 (`d8fe6c6`) |

## False-positive surface (per M3)

NOT this class: a channel that is **intentionally** un-validated because it is DOWNSTREAM of a validated input (a derived value computed from already-checked operator input — e.g. a runtime-adapted `live_breakout_mult` clamped from a validated cfg) — the asymmetry must be at the **WRITE boundary (operator input)**, not at a derived read. Nor an OBSERVABILITY channel that deliberately keeps-old on bad input (the GUI `Settings_Load`) — that is a documented exemption, not a hole.

## Closure mechanism

`tools/check_cfg_gate_caller_coverage.py` (caller-coverage half) + the `static_assert` no-`MANUAL_PARSER`-on-a-`CAPITAL_BOUND`-row (the parse-channel half) — together they make a NEW un-validated channel a build/CI failure. Sister: Class 52 (the primitive), Class 49 (distinct-bit severity), the config-compiler DESIGN_SPEC.
