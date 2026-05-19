---
type: skill-check
check_id: 19
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Pre-existing-work audit
established: 2026-05-18
---

# /readiness Check 19 — Pre-existing-work audit (v5.12.3+; STRENGTHENED v5.13.6+)

**STATUS:** SHIP-BLOCKING. A plan that fails Check 19 cannot ship.
Strengthened from v5.13.6 onward per operator instruction
2026-05-08 ("when writing the plans, take into account what already
exists in the code base, it will save time when actually coding
and cuts down on bugs").

**Triggers (run on EVERY plan write, not just trigger-keyword
plans):** any plan that proposes adding a cfg field, struct field,
function, X-macro entry, stamp body field, snapshot field, or any
new code surface. v5.13.5.A + v5.13.5.B (use-after-free + missing
snap fields, both v5.13.6 audit findings) prove every plan
benefits — even small UI ships extending existing structs.

## Procedure (NOT a checklist — execute these greps)

For EVERY addition the plan proposes, the agent MUST:

**Step 1 — Extract claims.** Build two lists from the plan body:
- **NEW claims** — every "we'll add X" / "create new Y" / "introduce Z"
- **REUSE claims** — every "uses existing X" / "extends Y" / "calls Z"
  (especially every file:line citation the plan makes — those are
  testable claims)

**Step 2 — Verify NEW claims (catch FALSE-NEW = the thing already exists):**

```bash
# For each claimed NEW name (function, struct field, cfg field,
# X-macro entry, has_* flag, etc.):
grep -rn "<claimed_name>" --include="*.hpp" --include="*.cpp" .

# Also grep for near-synonyms (operator-discovered patterns):
#   - "_pred" vs "_prediction" vs "_predicted"
#   - "regime_X" vs "X_regime" vs "current_X"
#   - "use_X" vs "X_enabled" vs "enable_X"
#   - cfg field with same semantics under different name

# For X-macro candidates, check the registry:
grep -A 30 "FOREACH_FEATURE\|FOREACH_TARGET\|FOREACH_SHALT\|FOREACH_STRATEGY" \
    --include="*.hpp" .

# For stamp body fields:
grep -n "has_<X>\|stamp.*<X>" ML_Headers/StampInference.hpp \
    Backtest/StampBody.hpp 2>/dev/null
```

If a NEW claim is FALSE (the thing already exists):
- Mark in audit report as **GAP — false-NEW**
- Cite file:line where the existing thing lives
- Plan must be revised to EXTEND the existing surface OR remove
  the duplicate claim before shipping

**Step 3 — Verify REUSE claims (catch FALSE-REUSE = thing missing OR signature drift):**

```bash
# For each claimed file:line citation in the plan:
sed -n '<line>p' <file>     # verify the line exists + matches claim

# For each claimed reused function:
grep -n "^.*<func_name>" --include="*.hpp" .   # verify exists
# If the plan claims a specific signature, READ the function and
# compare actual signature vs. plan's claimed signature

# For each claimed reused struct field:
grep -B2 -A2 "<field_name>" --include="*.hpp" .
```

If a REUSE claim is FALSE (function doesn't exist OR signature
differs from plan's assumption):
- Mark as **GAP — false-REUSE / signature drift**
- Plan must be updated to either (a) cite the actual current
  surface or (b) include adapter code to bridge the signature gap

**Step 4 — Stamp body / Surface G `has_*` flag pattern check:**

```bash
# When plan extends stamp body, verify the has_* pattern is used
# (NOT a raw field append, which would break legacy stamps):
grep -n "has_<new_field>\|has_engine_version\|has_feature_mask" \
    ML_Headers/StampInference.hpp Backtest/StampBody.hpp 2>/dev/null
```

If plan adds a stamp body field WITHOUT a `has_*` flag → REJECT.
Surface G discipline (CLAUDE.md item 15) is non-negotiable.

**Step 5 — X-macro append discipline:**

For plans extending FOREACH_* registries:
- Verify ONLY appending (registry order is locked; reordering
  flips REGISTRY_HASH which breaks all existing models)
- Verify the registry's expected_count assertion stays correct
- Verify all N consumer sites that read the registry will pick up
  the new entry automatically (tools/calls_graph_diff.sh helps)

**Step 6 — Dependency trace (delegate to /trace-deps for deep dives):**

For plans that:
- Add ≥3 new functions, OR
- Touch ≥5 files, OR
- Add a new function whose dependency chain isn't obvious from
  the plan body

→ Spawn `/trace-deps <plan-file>` as sub-skill. Trace returns the
full callee graph + signature verification per callee. Skill spec
at `.claude/skills/trace-deps/SKILL.md`.

For trivial plans (single file, ≤2 new functions): Steps 1-5
suffice; skip /trace-deps invocation.

## Verdict

- **PASS** ✅ — plan's NEW + REUSE claims all verified; no false-
  NEW or false-REUSE found
- **GAP — false-NEW** ⚠️ — proposed thing already exists; plan
  must extend instead
- **GAP — false-REUSE** ⚠️ — claimed pre-existing thing doesn't
  exist OR signature drifted; plan must update
- **GAP — Surface G violation** 🛑 — stamp body extended without
  `has_*` flag; SHIP BLOCKED
- **GAP — X-macro reorder** 🛑 — registry reordered (not append);
  SHIP BLOCKED (REGISTRY_HASH would flip → all models reject)

## When the work is already shipped (false-NEW resolution)

- **Update the plan** to note which earlier ship covers it
- **Reduce the new ship's scope** to only the truly-new bits
  (e.g. v5.12.3.D's "3-tier strict-mode check" was residual; the
  cfg field + pack-time gate + stamp body all shipped via
  v5.11.18+18a)
- **Mark in the master plan:** "Phase X.Y: ALREADY SHIPPED via
  vP.Q.R; this ship covers <residual scope only>" (or skip the
  ship entirely if nothing residual remains)

## Why this matters (post-mortem evidence)

- **v5.12.3.D** — original 4-5h scope; audit found cfg field +
  pack-time gate + stamp body all shipped via v5.11.18+18a; only
  3-tier strict-mode was residual; ship closed faster.
- **v5.13.0.A** — audit caught CRITICAL `buy_class_idx` aliasing
  GAP before any code was written. Without the audit:
  exit_predictor would have predicted VALLEY (class 0) instead of
  PEAK (class 1) — silent semantic inversion in production.
- **v5.13.5.A + v5.13.5.B** — both caught by `/parity-check`
  Section L (production-caller field-population audit, sister to
  Check 19). Use-after-free + uninitialized snap fields. Both
  were "extend existing struct" failures the strict procedure
  would have caught at plan time.

## Pairs with cold-pickup completeness rule #6 (stale-claim audit)

Cold-pickup rule (CLAUDE.local.md): plan citations to file:line
must resolve at write time. Check 19 is the inverse: plan
PROPOSALS must NOT already exist. Together they bracket the plan:
the things you cite must exist; the things you propose must not.

## Cross-references

- `/trace-deps` SKILL.md — invoked for deep-dive dependency
  tracing on large plans
- `/parity-check` Section L — production-caller field-population
  audit (catches the same class post-coding via grep of all
  callers of newly-extended structs)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 13 — worker-arg use-after-
  free pattern that the strengthened Check 19 + /trace-deps would
  have caught at plan-time
