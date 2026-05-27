---
type: meta-discipline
stage: 3-first-canonical
version: 1.1
established: 2026-05-26
promoted_to_stage_3: 2026-05-27
tags: [meta-discipline, plan-template, framework-discipline, doc-discipline]
surface: [plan-pipeline, helper-extraction]
sister_specs:
  - structural-fix-preferred-decision-framework.md
  - canonical-sister-extension-discipline.md
  - pattern-codification-lifecycle.md
  - structural-enforcement-when-memory-insufficient.md
audit_tier: framework-pattern
applies_at_skills: [/readiness, /capture-audit, /plan-draft]
first_canonical_application: v5.15.5.F.4d.1.B.4 WIP-12 (EngineCommon_SlowPathCycleOneCore extract — body-content args enumerated at v1.7.3 helper-signature gate; HIGH-1 + N-6 sister-canonical reuse decisions captured pre-coding)
---

# Body-content arg enumeration at plan-time discipline (M6)

## Why this discipline exists

When plan body proposes extracting a helper from an inline body / lambda body / function body, the helper SIGNATURE is typically spec'd based on PROPOSED structural intent ("takes cfg + state + per-tick args") rather than enumeration of ACTUAL body content + per-callee parameter requirements.

This pattern surfaces as cascading "wait this needs more args" at coding time + risk of cryptic compile errors + amendment cycle inflation.

**Codified at v5.15.5.F.4d.1.B.4 v1.7.3** as `feedback_enumerate_helper_signature_args_before_extract` after the pattern surfaced TWICE in same ship:

- **BootPerCore v1.6 O1 (4→8 args)** — v1.5 spec'd 4 args. Phase B body extraction at v1.6 surfaced body needs caller-owned static refs (`tick_ring` + `core`) + nullable ML zoo pointers (`zoo_ptr` + `ezoo_ptr`) + caller-precomputed `core_balance`. Drops unused `oms`. Net 8 args.
- **SlowPathCycleOneCore v1.7.3 N-6 (6→9 args)** — v1.7.2 spec'd 6 args. 5-parallel-agent audit at v1.7.2 CONVERGED on body needs 4 additional inputs: `volume` + `now_tick` (distinct from `ts_us` microseconds) + depth fields wrapped in `BookSnapshot<F>`. Net 9 args.

Per `feedback_proactive_novel_alternative_consideration`: codify at 2-instance proactive threshold rather than wait for 3rd recurrence.

## How to apply

### Step 1: Read body's source line range in full

Before plan body locks helper signature for any extracted helper from inline body / lambda body / function body:
- Cite explicit `<file>.hpp:<startline>-<endline>` source range in plan body
- Read the entire source range — every line

### Step 2: Enumerate every symbol reference

For each line of the body, classify every symbol reference into one of:
- **HELPER-SIG-ARG** — input/output the helper needs to expose in its signature
- **cfg-derived** — value derivable from `cfg` arg (no separate signature arg needed)
- **state-derived** — value derivable from `state` arg
- **caller-precompute** — caller computes this BEFORE invoking helper + passes as arg
- **STAY-IN-CALLER** — LIVE-only persistence sink / threading observability / per-arch artifact that should NOT migrate to helper

### Step 3: Per-callee parameter verification

For each function call inside the body, read the CALLEE'S full signature + verify each arg the caller provides. Plan body must:
- Cite each callee's signature
- OR include a "callee signatures" subsection in the enumeration artifact

### Step 4: Generate enumeration CSV artifact

Generate at `plans/<sprint>/plan_checks/<date>-<ship>-<helper-name>-body-content-enumeration.csv` (sister to `boot-call-sequence-enumeration.csv` pattern at `.B.4` Phase A Step A.4).

Each row: symbol-reference / category / source line / rationale.

### Step 5: Cross-check helper signature against enumeration

Helper signature args list in plan body == HELPER-SIG-ARG rows in CSV. No signature args without body reads; no body reads without signature args unless STAY-IN-CALLER classified.

### Step 6: Plan body lock

Plan body lock conditional on Steps 1-5 complete. NO "etc." or "..." in helper signature arg lists.

## Recognition markers (when this rule is being violated)

- Plan body proposes "extract X body into helper Y" without enumerating body inputs
- Helper signature spec'd at "intent" level ("takes state + cfg + per-tick args") without specifying which per-tick args
- Audit catches signature args mid-amendment cycle (5+ args added at amendment vs caught at draft)
- Coding surfaces "wait this needs more args" cascade
- Spec uses "etc." or "..." in arg list

## Structural enforcement (mechanisms)

| Mechanism | Where |
|---|---|
| `/readiness` Check 33 | `claude-skills/readiness/checks/check-33-body-content-arg-enumeration.md` |
| `/capture-audit` Check 3 | Verifies CSV artifact existence for helper-extract proposals |
| Plan template "End goal" + "Decisions" sections | Forces explicit body-content claims that get audited |
| Future CI tool extension | B-Plus CI tool (`tools/check_plan_body_symbol_existence.py`) could be extended to grep helper signature args against body symbol references |

## Sister cross-references

- `memory/feedback_enumerate_helper_signature_args_before_extract.md` — operator-collaboration rule (M6 memory)
- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md` — parent meta-rule
- `DESIGN_SPECS/meta-disciplines/structural-enforcement-when-memory-insufficient.md` — M7 sister (this is M6; M7 covers structural escalation when M6 memory codification proves insufficient)
- `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md` — when extracted helper introduces new arg types, check existing canonical structs first (BookSnapshot reuse at v1.7.3 N-6 is worked example)
- `memory/feedback_verify_symbol_existence_at_plan_drafting_time.md` — sister CLASS 14 discipline at SYMBOL-EXISTENCE side
- `memory/feedback_enumerate_consumers_before_registry_row_deletion.md` — sister CLASS 18 discipline at CONSUMER side
- `tools/check_plan_body_symbol_existence.py` — B-Plus CI tool (sister Stage 6 enforcement)

## Lifecycle promotion

- **Stage 2 (current)** — DRAFT; worked examples in `.B.4` v1.6 + v1.7.3
- **Stage 3 promotion trigger** — second cohort application (next HIGH-RISK helper extract that applies this discipline)
- **Stage 4 promotion** — `/readiness` Check 33 has fired 3+ times on plan bodies
- **Stage 5 promotion** — 4-pillar audit consistently catches body-content gaps
- **Stage 6 promotion** — if recurrence pattern emerges at body-content layer DESPITE memory + audits, escalate via CI tool grep against helper signature + body symbol references

## Worked examples

### BootPerCore v1.6 O1 (4 → 8 args)

v1.5 spec'd: `(cfg, c, state, oms)`

Body extraction at v1.6 surfaced enumeration:
- `tick_rings[c]` → caller-owned static; add `tick_ring` arg (HELPER-SIG-ARG)
- `cores[c]` → caller-owned static; add `core` arg (HELPER-SIG-ARG)
- `ml_zoos[c]` → nullable per ML branch; add `zoo_ptr` arg (HELPER-SIG-ARG)
- `ml_ensemble_zoos[c]` → nullable per ML branch; add `ezoo_ptr` arg (HELPER-SIG-ARG)
- `core_balance` → caller-precomputed per O2 bytewise-identical math; add as arg (HELPER-SIG-ARG)
- `oms` → unused in body; DROP from signature

Net: 4 → 8 args (added 5, dropped 1).

### SlowPathCycleOneCore v1.7.3 N-6 (6 → 9 args)

v1.7.2 spec'd: `(cfg, c, state, oms, price, ts_us)`

5-parallel-agent audit at v1.7.2 CONVERGED on body enumeration:
- `volume` → distinct from `price`; add (HELPER-SIG-ARG)
- `now_tick` → distinct from `ts_us` (microseconds vs producer-thread counter); add (HELPER-SIG-ARG)
- `book_imb` / `book_spread` / `book_mid` → depth fields wrapped in `BookSnapshot<F>`; canonical sister at `BinanceDepth.hpp:29-41` per `feedback_audit_canonical_sister_before_new_infra`; add `const BookSnapshot<F>& depth` arg (HELPER-SIG-ARG)

Net: 6 → 9 args (added 3 distinct args + 1 struct).

## Anti-patterns this prevents

- Late-discovered missing args at coding time → amendment cycle inflation
- Cryptic compile errors when callee signature doesn't match enumerated expectations
- Helper signature drift from spec at amendment cycle (5+ args added between draft + coding)
- "etc." / "..." in spec → ambiguous about which args are required
- Helper signature reuse from sister-pattern without re-enumeration for current body
