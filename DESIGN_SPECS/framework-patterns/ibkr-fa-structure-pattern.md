---
type: framework-pattern
stage: 2-draft
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.7 (DEFERRED; operator-triggered if FA used)
sister_specs:
  - framework-patterns/foreach-subaccount-meta-registry-pattern.md (parent pattern)
  - framework-patterns/per-node-economic-isolation-pattern.md
tags: [framework-discipline, ibkr, financial-advisor, sub-account-hierarchy]
surface: [ibkr-adapter, multi-client-trading]
---

# IBKR Financial Advisor structure pattern (Stage 2 DRAFT)

**Pattern intent:** IBKR Financial Advisor accounts manage N client sub-accounts under one master. Per-node binds to one FA client account. Optional; only used if operator has FA structure.

## Pattern

```cpp
struct IBKRAdapter {
    // ... base fields ...

    // FA structure (optional)
    bool fa_structure_enabled;
    char fa_master_account[32];                       // "U12345"
    char fa_client_accounts[MAX_FA_CLIENTS][32];      // "U67890", "U54321", ...
    uint32_t fa_client_count;
};

// Cfg:
// fa_structure_enabled = 1
// fa_master_account = U12345
// fa_client_accounts = U67890, U54321, U99999

// Per-node binding to FA client:
// node_0/core.cfg: subaccount_id = 0  → resolves to U67890
```

## FIX message routing

```cpp
void IBKRAdapter_RouteToFA(IBKRAdapter& adapter, uint32_t subaccount_id, FIXMessage& msg) {
    if (adapter.fa_structure_enabled) {
        msg.SetField(1, adapter.fa_client_accounts[subaccount_id]);  // Account field
    }
}
```

## Stage progression

- **Stage 2 DRAFT**: reference
- **Stage 3 first canonical**: when operator runs FA structure on IBKR

## Cross-references

- Parent: `framework-patterns/foreach-subaccount-meta-registry-pattern.md`
- Sister: `framework-patterns/fix-session-management-pattern.md`
- Operator: `plans/v5.15.5.F.4d.1.E.7-ibkr-exchange.md`
