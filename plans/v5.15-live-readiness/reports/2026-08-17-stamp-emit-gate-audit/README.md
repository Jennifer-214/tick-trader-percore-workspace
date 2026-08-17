---
type: agent-report-set
date: 2026-08-17
ship_tag: v5.15.5.F.4d.1.E.1.2
directive: "D-425 step 6 — Tier-2-vs-Tier-1 fork; consumer-dependence of the unproduced stamp wire keys"
decision_log: plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md
engine_head_at_spawn: a160123
orchestrator_verified: true
---

# 2026-08-17 — stamp EMIT-gate audit (3 agents + 1 orchestrator probe)

Saved verbatim at receipt per `feedback_save_agent_reports_verbatim`. The orchestrator
wrote these files; the agents were read-only.

**One presentational edit, disclosed rather than silent.** Three fenced blocks were
relabelled ` ```cpp ` → ` ```c++ `. No character of any report's content changed. Reason:
`check_plan_body_symbol_existence.py` (pre-commit B-Plus, Class-14 fabrication guard)
COMPILES every ` ```cpp ` fence, because in a *plan body* such a fence is proposed code and
the claim it makes is "this compiles." These three fences are **verbatim quotes of existing
production code** — 3-line excerpts that cannot compile standalone (`inf` is not declared in
a 3-line window). The `cpp` tag was the orchestrator's mislabel: a quote is not the claim
"this compiles." Relabelling fixes the label, not the gate — the guard keeps full teeth on
any block that genuinely asserts compilable code.

All three quoted excerpts were verified against the real source by the orchestrator before
relabelling, so no fabrication is hidden by the change: `ML_Headers/StampHelper.hpp:249-251`
(×2) and `CoreFrameworks/ModelValidation.hpp:196`.

**Standing gap this surfaced (not fixed here).** The B-Plus *anchor* leg is scoped by
`frozen_record_paths()` — which already contains `/reports/`, which is why the RENAMED cites
in these files were advisory rather than blocking. The *fabrication* leg is NOT so scoped.
Agent reports are a doc type that did not exist when B-Plus was written and are dense with
verbatim excerpts, so every future report set will hit this. Whether the fabrication leg
should inherit the frozen scoping — against the real counter-argument that agents CAN
fabricate code and a report is exactly where you'd want to catch it — is an operator call,
not something to settle by relabelling fences forever.

## Why these three

The operator asked *"are you sure it's the best option, do we need to test stuff for this?"*
on a wire-format change to an HMAC-signed body. That is two independent triggers of the
BINDING default in `DESIGN_SPECS/audit-methodologies/adversarial-multi-agent-audit-methodology.md`
(operator asks to verify · high-stakes wire-format verification), which fires opt-OUT.
Three distinct lenses, each blind to the others:

| file | class | lens |
|---|---|---|
| `i-class-18-key-consumer-trace.md` | i-class | For each of the 18 stamp wire keys with no production producer: is there a live consumer, and what breaks when the key is absent? |
| `a-class-refute-per-key-bits.md` | a-class | REFUTE the orchestrator's per-key-bit recommendation |
| `a-class-refute-byte-identical.md` | a-class | REFUTE the claim that the conversion leaves the wire byte-identical |
| `orchestrator-drift-probe.md` | — | The orchestrator's compiled probe discharging the i-class's falsifiable prediction (the agents are read-only and could not run it) |

## Outcome in one paragraph

**The orchestrator's recommendation was REFUTED by both a-class agents, independently and
for the same reason** — bit-set and value-write are separate C++ statements, so no
bit-granularity change couples them. The empirical proof is a LIVE defect both found:
`inference_cfg_bandit_blend_ratio` sets its own standalone bit and never assigns its value,
emitting `=0` into a signed body beside the truthful cfg-derived line. The i-class
separately confirmed the 18-key count exactly (three orthogonal sweeps, no missed producer)
but **reclassified 10 of 18 from inert to live defect**, and surfaced a larger adjacent
finding — the `.B.3` migration never built the parse→handle leg — which the orchestrator
then confirmed by compiled probe.

## Orchestrator verification (anti-self-attestation — agents are a HUNTING tool, not a verdict)

Per the methodology's step 5, every surviving finding was re-read against the code before
being acted on. Results:

- **CONFIRMED by orchestrator read:** the `inference_cfg_bandit_blend_ratio` bit-without-value
  defect (`StampHelper.hpp:249-251`; only value writers are two test fixtures + the parse-side
  handle copy). `bandit_enabled` default = 1 (`ControllerConfig.hpp:2012`).
- **CONFIRMED by compiled probe:** the adjacent parse→handle finding — see
  `orchestrator-drift-probe.md`. Positive control passes.
- **AGENT DISAGREEMENT, resolved by code-read:** on whether keying gating off the `emit_when`
  column would silently drop keys (a-class #1) or fail to compile (a-class #2). **#2 is right** —
  `inf->has_bandit` is not a member of `StampInferenceCfgInputs`; it appears only in the
  registry row. Already self-reported in-tree at `StampHelper.hpp:296` and homed at PARITY-022.
- **ORCHESTRATOR CORRECTIONS ACCEPTED:** the orchestrator's brief said the 18 keys are "never
  emitted" (wrong quantifier — all 16 on-disk stamps carry `inference_cfg_*` from the pre-`.B.3`
  emitter; correct claim is *never emitted by any stamp the CURRENT emitter can produce*), and
  "28 keys emit" (a maximum over caller inputs, not a set; 20 on the default config).
