---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.5
canonical_applications:
  - v5.15.5.F.4d.1.E.5 (real Binance sub-accounts wired)
sister_specs:
  - framework-patterns/foreach-subaccount-meta-registry-pattern.md (sub-account registry)
  - framework-patterns/capital-allocation-policy-pattern.md (sister; capital management)
  - meta-disciplines/structural-fix-preferred-decision-framework.md (economic isolation IS structural fix)
tags: [framework-discipline, economic-isolation, sub-accounts, exchange-enforced, failure-domain]
surface: [per-node-state, capital-management, risk-isolation]
applies_at_skills: [/precoding-audit-gate, /dod-audit, /accounting-audit]
---

# Per-node economic isolation pattern

**Pattern intent:** Each per-node binds to its own exchange sub-account. Per-node failure domain = sub-account scope. Exchange-enforced isolation (not just engine-side). Per-node capital + rate budget independent.

## Problem statement

Multi-node engine with shared exchange account has coupling concerns:
- One node's loss debits the shared account; affects sibling nodes' capacity
- One node's rate-limit abuse exhausts shared budget; siblings starve
- One node's API key compromise = total account compromise
- One node's strategy bug = global account at risk

With per-node sub-accounts:
- Each sub-account is INDEPENDENT trading entity on Binance
- Losses isolated to that sub-account
- Rate budget independent per sub-account (1200/min EACH)
- API key compromise scoped to one sub-account
- Per-strategy isolation natural

**This is structural isolation; Binance enforces; not engine-side rule.**

## Pattern description

### Per-node binding

```cpp
// In NodeState.binding (from .E.1):
alignas(64) struct {
    uint32_t cluster_id;           // FOREACH_EXCHANGE row
    uint32_t subaccount_id;        // FOREACH_SUBACCOUNT_<EXCHANGE> row
    char client_order_id_prefix[16];   // encoded "C<cluster><sub><node>_"
} binding;

// Per-node submit uses ITS OWN sub-account credentials
template<typename F>
int NodeSlowPath_SubmitOrder(NodeState<F>& node, const SubmitCommand<F>& cmd) {
    uint32_t cluster_id = node.binding.cluster_id;
    uint32_t subaccount_id = node.binding.subaccount_id;

    // Get sub-account credentials
    SubAccountCredentials& creds = g_state.clusters[cluster_id].subaccounts.credentials[subaccount_id];

    // Submit with sub-account credentials (Binance routes to that sub-account)
    // Internal: HMAC signed with sub-account's API key + secret
    return tt::submit_order_subaccount<BinanceAdapter<F>>(adapter, creds, cmd);
}
```

### Per-node rate-limit budget (independent)

Each sub-account has independent 1200/min budget on Binance. Aggregate engine capacity = N × 1200/min for N sub-accounts.

Per-cluster rate-limit tracker maintains separate state per sub-account:

```cpp
struct ClusterRateLimits {
    SubAccountRateLimit per_subaccount[MAX_SUBACCOUNTS];
};

bool NodeSlowPath_CheckRateLimit(NodeState<F>& node) {
    uint32_t cluster_id = node.binding.cluster_id;
    uint32_t subaccount_id = node.binding.subaccount_id;
    return SubAccountRateLimit_TryAcquire(
        &g_state.clusters[cluster_id].rate_limits.per_subaccount[subaccount_id]
    );
}
```

### Per-node balance tracking

Engine-side mirror of each sub-account's balance:

```cpp
struct NodePersistState {
    FPN<F> sub_account_balance;     // engine mirror; reconciled against Binance truth
    FPN<F> sub_account_open_notional;
    FPN<F> sub_account_realized_pnl;
};
```

Reconciliation per `framework-patterns/hybrid-reconciliation-cadence-pattern.md`.

### Failure isolation worked example

**Scenario:** Sub-account 1 suspended by Binance (API abuse).

**Pre-isolation (shared account):** All trading halts. Operator must contact Binance support; await resolution; no trading until resolved.

**With isolation (per-node sub-accounts):**
- node_1 detects consecutive submit failures (cfg threshold; default 10 consecutive)
- node_1 trading halted (per-node kill flag set)
- Webhook alert to operator
- nodes 0/2/3 (other sub-accounts) UNAFFECTED; continue trading
- Operator contacts Binance support for sub-account 1; awaits resolution
- Resolution → fox-cli resume-node binance/node_1 → node_1 resumes

**Outcome:** 75% of engine capacity preserved during incident; localized resolution.

## Capital allocation per-node

Per `framework-patterns/capital-allocation-policy-pattern.md`:
- Each sub-account funded independently
- Internal-transfer plumbing for cross-sub-account capital moves
- Capital reserve + per-node cap policy enforced

## Stage progression criteria

- **Stage 3 first canonical** (`.E.5`): real sub-accounts wired
- **Stage 4 cohort** (when 2nd exchange has sub-accounts wired): pattern proven across exchanges
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **Single account; engine partitions virtually** — isolation engine-side only; Binance not enforcing
- **Shared API key** — compromise = total account loss
- **Shared rate budget** — one node spamming starves siblings

## Cross-references

- Parent: `framework-patterns/foreach-subaccount-meta-registry-pattern.md`
- Sister: `framework-patterns/capital-allocation-policy-pattern.md`
- Sister: `framework-patterns/hybrid-reconciliation-cadence-pattern.md`
- Parent meta: `meta-disciplines/structural-fix-preferred-decision-framework.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.5-real-subaccounts-capital-framework.md`
