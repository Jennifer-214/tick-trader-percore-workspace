---
name: feedback-backwards-compat-not-default-concern
description: "Backwards compatibility is NOT a default concern when proposing refactor / deletion / cleanup scope. Default to cleanest architectural answer (full surface deletion) unless operator explicitly signals backwards-compat requirement. This is an OSS personal tool Caramel built that other people happen to use; operator-flagged exceptions, not default-preserved surfaces."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 341a0b93-fa2a-4e53-9aff-936f93df9deb
---

**Default stance on backwards compatibility:** when proposing refactor / deletion / cleanup scope, do NOT pad recommendations with backwards-compat-preserving surfaces by default. Default to the cleanest architectural answer (e.g., full surface deletion, no migration warning, no preserve-and-deprecate layer). Operator (Caramel) signals explicitly when backwards-compat matters.

**Why:** Codified 2026-05-26 at `.B.4` v1.7.5 transition cycle (D18 decision) during the `engine_arch=centralized` SHARDED mode deprecation scoping. Initial proposal included REFUSE-at-boot handling + preserved cfg field + TUISnapshot field + GUI gating "for backwards compat". Operator response:

> "idk its not that important considering that this is mostly a personal tool i made OSS, that other people happen to use, im not too concerned about backwards compat tbh"
> "ill let you know when backwards compat matters"

Result: scope simplified from "preserve + deprecate" to "delete full surface" (~+300 LOC clean deletion). Cleaner code base; clearer architectural state; less mental-model overhead for future readers + maintainers.

**Context for the framing:** the codebase is `FoxML_Trader_v2` — a personal trading engine Caramel built, published OSS (AGPL-3.0) on GitHub. Has external users (~10k clones on FoxML_Trader v1). But Caramel's stance: external users using this PERSONAL OSS tool accept that the operator's architectural direction matters more than backwards compat at every refactor. This is NOT a hedge-fund product with operator-side SLA on cfg stability.

This contrasts with codebases where backwards compat IS a default concern:
- Public APIs with paying customers
- ABI-locked binary distribution
- Standard library / language runtime

For Caramel's OSS personal tool: clean architecture > preserved surface.

## How to apply

**When proposing refactor / deletion / cleanup scope:**

1. **Default proposal:** cleanest architectural answer. Delete the surface entirely if it's redundant / deprecated / overlaps with another path.
2. **DO NOT pad with preserve-and-deprecate by default.** Don't add REFUSE-at-boot handlers, deprecation warnings, migration shims, backwards-compat aliases unless operator explicitly says so.
3. **If operator wants backwards compat for a specific item, they'll say so.** Common signals: "this needs migration path for users with config X", "preserve the wire format because Y", "don't break existing models". Without these signals, default to clean deletion.
4. **Exceptions where backwards compat IS load-bearing (don't break without explicit operator signal):**
   - **Stamp body wire format** (per H9 hard invariant) — HMAC chain integrity across model versions; ALWAYS preserve byte equivalence
   - **Persistence formats** — snapshot files, calibration logs, trade logs that operators have on disk from prior runs (verify before format change; offer migration path)
   - **Model handle ABI** — stamps from prior versions need to load; H9 + forward-compat invariant
   - **Per-core override semantics already locked into operator cfgs** — verify before reshaping (e.g., `core_N_strategy` enum values are stable since v5.X)

These exceptions are NOT default-preserved-because-backwards-compat; they're preserved because they have HARD INVARIANTS or REAL PERSISTENT STATE that downstream operators depend on. Different mechanism than "default to backwards-compat-preserving surface".

## Recognition markers (when this rule is being violated)

- Proposing REFUSE-at-boot handler for a deprecated cfg value without operator signal
- Keeping a cfg field "for backwards compat" when the field is being structurally removed elsewhere
- Adding deprecation warnings for legacy values when full deletion would be cleaner
- Preserving TUISnapshot ABI fields that have no consumer post-deletion
- Adding migration shims / aliases / wrappers when the operator hasn't signaled they need migration support
- Mental tax: "X operators might have Y cfg" — if not load-bearing per the exceptions list above, ignore

## Sister memories

- [[feedback_no_defer_for_effort]] — parent meta-rule (defer is last-ditch; don't defer for "smaller scope" reasons; backwards compat surface preservation is a flavor of "smaller scope" deferral if not load-bearing)
- [[feedback_motivated_collaborator_for_caramel]] — best-software-path mindset; preserves cleanest architectural answer over preserved-surface mediocre answer
- [[feedback_surface_operator_migration_path_proactively]] — APPLIES when load-bearing exception above is met (stamp / persistence / model handle / locked cfg). Surface migration path proactively for those cases. THIS rule scopes WHEN proactive migration path matters.

## Worked example

`.B.4` v1.7.5 transition — `engine_arch=centralized` SHARDED mode deprecation:

| Component | Originally proposed | After D18 LANDED |
|---|---|---|
| 8 conditional branches in EngineSharded.hpp | DELETE | DELETE ✓ |
| 3 sister wrappers in ControllerEventLoop.hpp | DELETE (cohort per Class 18) | DELETE ✓ |
| `engine_arch` cfg field in ControllerConfig.hpp | KEEP "for backwards compat at cfg parse layer" | **DELETE** (per operator stance) |
| `engine_arch` cfg parser entry | KEEP for backwards compat | **DELETE** |
| `ENGINE_ARCH_CENTRALIZED` / `ENGINE_ARCH_PER_CORE_SLOW` constants | KEEP for value-passing | **DELETE** |
| TUISnapshot.engine_arch ABI field | KEEP for GUI display | **DELETE** + simplify GUI |
| GUI DashboardPanels `s->engine_arch == 1` gating | KEEP unconditional-true | **DELETE** branches |
| Boot REFUSE handler for `engine_arch=centralized` | ADD for migration warning | **DON'T ADD** (cfg parser handles unknown keys conventionally) |

Net: cleaner code (~+150-200 LOC additional cleanup beyond initial proposal); no preserved-surface mental tax; cfg parser's existing "unknown key handling" covers operators with stale cfg files; operator stated this is fine.

Sister-discipline: **when surface preservation IS load-bearing per the exceptions list, ALWAYS preserve + migrate proactively** (e.g., stamp body byte equivalence + HMAC chain — never broken; `feedback_surface_operator_migration_path_proactively`).

## Trade-off

Surface preservation has REAL costs that are easy to underestimate:
- Mental tax for future readers ("why is this still here?")
- Branch cardinality (every "kept for compat" branch adds complexity to all downstream code)
- Audit surface (more branches = more audit work)
- Hidden coupling (preserved surfaces accumulate quiet consumers over time)

By contrast, surface deletion has explicit, bounded cost:
- Operators using the deleted surface get an explicit error at next boot (cfg unknown key warning, missing constant compile error, etc.)
- Once resolved by operator (cfg edit), the surface is gone forever — no ongoing cost
- Code base is smaller, simpler, easier to maintain

For an OSS personal tool with no SLA, the deletion cost (operator updates cfg once) is much smaller than the preservation cost (perpetual surface complexity).

## When to surface backwards-compat as load-bearing (rare; require explicit signal)

The exceptions list above (stamp body / persistence / model handle / locked cfg semantics). When any of these surfaces matter:
- Surface explicitly: "this needs backwards-compat handling because [stamp body chain / persistence format / model handle ABI]"
- Propose migration path proactively (per `feedback_surface_operator_migration_path_proactively`)
- DO NOT delete without explicit operator approval

For everything else: default to clean deletion. Operator will flag explicitly if a specific case needs preservation.
