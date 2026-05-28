---
type: framework-pattern
stage: 2-draft
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1 (Portfolio + Position layout transition)
sister_specs:
  - framework-patterns/x-macro-registry-with-presence-dispatch.md
tags: [data-layout, soa, avx-512, simd, cache-locality]
surface: [portfolio, position-state]
---

# Portfolio + Position SoA vectorization pattern (Stage 2 DRAFT)

**Pattern intent:** Struct-of-Arrays layout for Portfolio + Position. AVX-512 SIMD-friendly. ~100× speedup for portfolio walks even at small N=8-32. Per D-55 + F-12 (operator-cited Concept 2 from research 2026-05-28).

## Pattern

### AoS (current; before .E.1)

```cpp
struct Position {
    FPN<F> qty;
    FPN<F> entry_price;
    FPN<F> margin_req;
    // ... etc
};
Position positions[MAX_PORTFOLIO_SLOTS];
```

Cache-unfriendly when iterating one field across all positions.

### SoA (after .E.1)

```cpp
struct alignas(64) PortfolioSoA {
    FPN<F> qty[MAX_PORTFOLIO_SLOTS];           // contiguous; SIMD-friendly
    FPN<F> entry_price[MAX_PORTFOLIO_SLOTS];   // contiguous
    FPN<F> margin_req[MAX_PORTFOLIO_SLOTS];    // contiguous
    // ... etc
};
```

Cache-locality + bandwidth wins for field-wise operations.

### AVX-512 vectorized portfolio walk

```cpp
// Compute total notional via SIMD
FPN<F> ComputeTotalNotional(const PortfolioSoA& portfolio, uint32_t count) {
    __m512i total = _mm512_setzero_si512();
    for (uint32_t i = 0; i < count; i += 8) {
        __m512i qty_vec = _mm512_load_si512(&portfolio.qty[i]);
        __m512i price_vec = _mm512_load_si512(&portfolio.entry_price[i]);
        __m512i notional = _mm512_fmadd_pd(qty_vec, price_vec, total);
        // ... aggregate
    }
    // Horizontal sum
    return HorizontalSumFPN(total);
}
```

vs scalar:
```cpp
FPN<F> ComputeTotalNotional_Scalar(const Position* positions, uint32_t count) {
    FPN<F> total = FPN<F>::zero();
    for (uint32_t i = 0; i < count; ++i) {
        total = FPN_Add(total, FPN_Mul(positions[i].qty, positions[i].entry_price));
    }
    return total;
}
```

~100× speedup at N=8-32; cache-locality + memory bandwidth wins.

## Where SoA pays off most

- Portfolio walks (current notional; aggregate exposure)
- ML feature compute (per-cluster many features; pure SIMD)
- HMAC signing batch (rare; not common case)

## Where SoA matters less

- Single-position lookup (just read one field; SoA vs AoS irrelevant)
- Sparse access patterns (random access; SoA's cache-locality wins lost)

## Stage progression

- **Stage 2 DRAFT** at `.E.1` (Portfolio + Position SoA transition)
- **Stage 3 first canonical** at `.E.6/.E.7` ML feature compute (where SIMD pays most)
- **Stage 4 cohort** at 3rd application

## Cross-references

- Source: F-12 + D-55 (operator-cited Concept 2 from research 2026-05-28)
- Parent: H10 (SIMD discipline)
