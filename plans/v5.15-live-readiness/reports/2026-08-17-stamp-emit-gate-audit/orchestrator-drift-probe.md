---
type: evidence
author: orchestrator
date: 2026-08-17
engine_head: a160123
directive: "Discharge the i-class's falsifiable prediction: does the missing .B.3 parse->handle leg fire the REFUSE_STRICT drift rows?"
verdict: CONFIRMED (with a severity correction the prediction did not carry)
source: ~/.cache/foxml_probe/drift_probe.cpp
---

# Compiled probe — the missing `.B.3` parse→handle leg

The i-class ended with a falsifiable prediction it could not run (read-only, and it could
not safely produce a v3 stamp). The operator authorised running it. This is that discharge.

**Why a probe and not an engine boot:** booting the real engine reaches a live market-data
feed even in paper mode. A compiled probe calling `tt::NodeModelZoo_ValidateAgainstCfg<64>`
directly answers the same question with no network, no orders, and no engine lifecycle.
Built outside `/tmp` (noexec) at `~/.cache/foxml_probe/`; re-runnable.

**Why a zero-init handle is the correct fixture, not a rigged one:** the finding under test
is precisely that *no code path writes those fields*. Orchestrator verified independently —
`rg "handle->thompson_precision_prior|handle->thompson_precision_obs|handle->bandit_blend_ratio|handle->ml_tp_pct"`
across `ML_Headers/ CoreFrameworks/ Backtest/ GUI/ MemHeaders/` returns **empty**, and the
only `memcpy`s into a handle are char arrays (`NodeModelZoo.hpp:394,421,432,439,451`). The
i-class's own refute vector #1 (a struct-region copy elsewhere) was checked and does not exist.

## Measured output

```
=== INPUT STATE (all from ControllerConfig_Default<64>()) ===
  bandit_enabled bit          : 1     <- gate for the two REFUSE_STRICT rows
  ack_inference_cfg_drift     : 0     <- 1 would SUPPRESS the whole category
  held_out_gate_strict        : 0
  cfg.thompson_precision_prior: 1.000000
  cfg.thompson_precision_obs  : 1.000000
  cfg.thompson_mu_prior       : 0.000000   <- 0.0 => must NOT drift (control)

=== HANDLE STATE (what the load path actually leaves behind) ===
  handle.thompson_precision_prior: 0.000000
  handle.thompson_precision_obs  : 0.000000

[cfg-drift] INFERENCE_CFG WARN_ALWAYS:  node 0 role=buy_signal stamp.bandit_blend_ratio=0 cfg.bandit_blend_ratio=0.3
[cfg-drift] INFERENCE_CFG REFUSE_STRICT: node 0 role=buy_signal stamp.thompson_precision_prior=0 cfg.thompson_precision_prior=1
[cfg-drift] INFERENCE_CFG REFUSE_STRICT: node 0 role=buy_signal stamp.thompson_precision_obs=0   cfg.thompson_precision_obs=1
  … identical triple repeated for role=barrier, role=regime, role=exit …
[cfg-drift] FATAL: node 0 had 8 Tier 1 mismatch(es) in strict mode.

return code = -1                       <- PREDICTION CONFIRMED
CONTROL (ops_cfg ack bit set, strict=1) rc = 0    <- refusal really IS the INFERENCE_CFG category
SEVERITY PIN (shipped default strict=0) rc = 0    <- no refusal on the shipped default
```

`thompson_mu_prior` correctly does **not** fire (cfg default 0.0 vs handle 0 — no delta),
which is the negative control on the mechanism itself.

## What this establishes, and what it does not

**Establishes.** Two `REFUSE_STRICT` rows compare a permanently-zero handle field against a
non-zero cfg default, behind a gate that reads cfg only and defaults ON since 2026-08-16.
8 Tier-1 mismatches (2 rows × 4 roles). The positive control passing means the diagnosis is
not misattributed to some unrelated row.

**Does NOT establish** — and the prediction overstated this — that the engine refuses to boot.
At the *shipped* default (`held_out_gate_strict=0`) it returns 0. The real severity is
different in kind:

- **Off (shipped default):** every model load emits 12 guaranteed-false drift lines per node
  (3 rows × 4 roles). The cfg-drift channel — a capital safety control — is saturated with
  permanent false positives, so genuine drift arrives indistinguishable from noise. Alarm
  fatigue engineered into the guard.
- **On (`held_out_gate_strict=1`, i.e. the live-readiness posture):** every model refuses.
  The operator's rational response is to disable the gate or set the ack flag, permanently
  bypassing it. A safety control that pressures you into switching it off is the Knight shape.

So: **not a boot blocker; a drift gate that cannot be used in either position.**

## Incidental finding — a dead control parameter

The first control attempt passed `acknowledge_inference_cfg_drift=1` as a **function
argument** and had no effect. `CoreFrameworks/ModelValidation.hpp:196` explicitly discards it:

```c++
(void)acknowledge_inference_cfg_drift;  // function-param signature preserved for boundary stability
```

The live ack is read from `cfg.ops_cfg_flags` via `MASK_OPS_CFG_ACKNOWLEDGE_INFERENCE_CFG_DRIFT`
(`CfgDriftCheckRegistry.hpp:176`). So a named parameter on a capital-safety validator looks
like a control and does nothing; any caller passing it gets silence. Same
advertised-capability-never-exercised class, at the function-signature surface.

## Process note worth keeping

The first run's control **failed**, and the tempting read was "the diagnosis is wrong." The
actual cause was a mis-built control. Without a positive control the run would have produced
either a false refutation or — worse — a confirmation reported with the control quietly
dropped. This is the concrete argument for `feedback_passing_test_is_not_verification` and for
why every negative test in this tree is required to carry a positive control.
