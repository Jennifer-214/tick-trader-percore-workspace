---
type: skill-check
check_id: 30
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Predicate-contract-changed audit
established: 2026-05-18
---

# /readiness Check 30 — Predicate-contract-changed audit (v5.14.10+)

**When this fires:**
Plans that propose extending an EXISTING predicate function (`Is*Ready*`, `Has*`, `Can*`, validation predicates, gate predicates). Triggered when the plan adds a new condition to a predicate that already has callers in tests or production.

**Why this matters (v5.14.10.C lesson — Surprise 6 in postmortem):**

v5.14.10.C extended `EnsembleModelZoo_IsReadyForInference` predicate with a new check (Thompson init flag required when primary_count >= 2). This BROKE the v5.14.2.E.1 contract test which only set `initialized_bandits=1` + `initialized_exit_bandits=1` but not `initialized_thompson_bandits=1`. The test had to be updated to also set the new flag.

The class: extending a PREDICATE'S CONTRACT (not just its body) requires synchronized updates to all callers' test fixtures. Otherwise tests pass on the old contract → break unexpectedly when new code is added.

**What to verify:**

For each predicate whose body the plan modifies:

```bash
# Find all callers
rg -n "\b<PredicateName>\s*\(" --glob '*.cpp' --glob '*.hpp' | head -30

# For each caller in tests/, check if the test fixture sets the new condition
# (e.g., if the new check requires `state->new_flag == 1`, verify tests
# that call the predicate also set state->new_flag = 1 in their setup)
```

Verdict per caller:
- **PASS — caller already satisfies new contract** (e.g., test fixture already sets the new flag)
- **NEEDS UPDATE — caller's setup doesn't satisfy new contract** (test will fail when contract extension lands)
- **OUT-OF-SCOPE — production caller; adjust call-site logic if needed**

**Output:**

If any "NEEDS UPDATE" callers found, add to the /readiness report:

```
### Predicate-contract-changed findings

Predicate `<Name>` will gain new condition `<X>`.
Callers needing synchronized updates:
- `tests/controller_test.cpp:1234` — test fixture sets `initialized_bandits=1` but not `initialized_thompson_bandits=1`; test will FAIL when contract extension lands. UPDATE: also set `initialized_thompson_bandits=1` in test setup.
- ...
```

Drift items are NOT blocking but flag during coding so the test-update lands in the same commit as the contract extension.

**Effort:** 3-5 min per audit (per predicate extension). Most plans don't trigger this.
