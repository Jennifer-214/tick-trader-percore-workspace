---
type: wire-format-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-10
tags: [wire-format, fixed-point-math]
surface: [backtest, ml-inference, training]
sister_specs: [wire-format-byte-preservation-discipline.md, avx512-byte-determinism-pattern.md]
applies_at_skills: []
---

# PRNG choice for replay-determinism use

**Established:** 2026-05-10 (v5.14.10.A; Bayesian Thompson sampling bandit)
**Status:** ACTIVE
**Cross-references:**
- `avx512-byte-determinism-pattern.md` (sister pattern — byte-determinism across SIMD paths; same load-bearing concern)
- `wire-format-byte-preservation-discipline.md` (persistence of PRNG state across save/load cycles)
- CLAUDE.md item 25 (SIMD vectorization preserves byte-determinism with scalar reference path)
- `ML_Headers/ThompsonBandit.hpp` (canonical first reference)
- `plans/v5.14-foxml-port-and-maker/postmortems/2026-05-10-v5.14.10-session-postmortem.md` Pivot 3

---

## Problem statement

Replay-determinism is a load-bearing invariant in this codebase: paper-trade audits, HMAC chains over training data, cache-warm replay tests, and ML pipelines all break under non-determinism. **PRNG state is a non-trivial determinism surface** — random samples drive Thompson posterior selection, training-time data shuffling, Monte Carlo simulations, and any randomized algorithm in the slow path.

Standard library PRNG facilities are NOT all equivalent for replay-determinism:

- `std::mt19937` / `std::mt19937_64` — algorithm IS fully specified by the C++ standard. Output bytes are deterministic across compilers AND libstdc++ versions when given identical seed + identical operation sequence. **Safe for replay-determinism.** BUT the state is large (312 × 64-bit words ~ 2.5KB per generator); persisting this across save/load cycles becomes awkward when many generators exist (e.g., per-regime × per-node).

- `std::normal_distribution` / `std::uniform_int_distribution` / `std::shuffle` — algorithm is NOT specified by the C++ standard; libstdc++ implementation determines the byte output. Same seed + same input range on libstdc++ versions A and B can produce DIFFERENT samples. **UNSAFE for cross-binary replay-determinism.**

- `rand()` / `random()` — POSIX implementation-defined; depends on libc version. **UNSAFE.**

The naive choice — `std::mt19937_64` + `std::normal_distribution` — fails on the SECOND component. The "obvious fix" of switching to raw `mt19937_64::operator()` + custom Box-Muller still leaves the persistence problem: 2.5KB state per generator × NUM_REGIMES × N_cores = 12-50KB JSON serialization (or 80-300KB binary), bloating every save cycle.

This is a **PRNG choice with two simultaneous constraints**: (1) algorithm fully specified at the byte-output level (cross-compiler, cross-libstdc++ replay-determinism), AND (2) small persistable state.

## Design space explored

### Option A: `std::mt19937_64` + custom Box-Muller (operate on raw output)

**Pros:** mt19937_64 is C++-standardized → bytes deterministic. Box-Muller of two consecutive uint64_t outputs is portable math.

**Cons:** 312-word state (2.5KB) per generator × N generators in a per-regime per-node fan-out → 12-50KB JSON. Save cycle becomes slow + complex; restore validation becomes brittle.

### Option B: Own splitmix64 PRNG + own Box-Muller

**Pros:** splitmix64 algorithm is fully specified — single uint64_t state; transition function is `x = (x + 0x9e3779b97f4a7c15) ^ ((x ^ (x >> 30)) * 0xbf58476d1ce4e5b9 ^ ...)` (compact 4-line C implementation). State is ONE uint64_t; trivially serializable as `%016lx` hex string. Replay-deterministic across any compiler / libc / platform. Box-Muller via own implementation using two consecutive splitmix64 outputs as uniform inputs.

**Cons:** splitmix64 has LOWER statistical quality than mt19937_64. Passes TestU01 SmallCrush + Crush but NOT BigCrush. Not cryptographically secure. Period is 2^64 (vs mt19937_64's 2^19937).

### Option C: PCG64 / xoroshiro128+ / xorshift64* (other modern PRNGs)

**Pros:** Similar small-state benefits to splitmix64. Some (e.g., PCG64) have higher statistical quality. Algorithms are fully specified.

**Cons:** State is 2 × 64-bit words (still better than mt19937_64). Implementation has more moving parts than splitmix64. No external dependency available in this codebase (would need vendor).

### Decision: Option B — own splitmix64

Persistence is the LOAD-BEARING concern; statistical quality is secondary for **non-cryptographic, bandit-posterior-sampling use**. The Bayesian Thompson sampler doesn't need 2^19937 period or BigCrush-grade quality; it needs deterministic bytes + cheap serialization. Splitmix64 gives both.

The pattern generalizes beyond Thompson sampling: **for any replay-determinism-sensitive PRNG use case where persistence is required, prefer SIMPLE algorithm with small state over HIGH-QUALITY algorithm with large state.** When statistical quality dominates persistence (e.g., cryptographic key generation, Monte Carlo with 10^12 samples), revisit.

## The pattern (concrete shape)

```cpp
// ML_Headers/ThompsonBandit.hpp — canonical reference

namespace tt {

// splitmix64 PRNG — C++-standardized algorithm; 1 word of state.
// Reference: https://prng.di.unimi.it/splitmix64.c
struct Splitmix64 {
    uint64_t state;

    // Advance + return next 64-bit uniform sample
    inline uint64_t next() {
        uint64_t z = (state += 0x9e3779b97f4a7c15ULL);
        z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
        z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
        return z ^ (z >> 31);
    }
};

// Box-Muller via own implementation
inline double splitmix_normal(Splitmix64& rng, double mean, double stddev) {
    // Two uniform U(0,1) samples (avoid 0 in log)
    uint64_t u0_bits = rng.next();
    uint64_t u1_bits = rng.next();
    // Map uint64 → [1/2^53, 1.0] via top-53-bit float trick
    double u0 = (double)((u0_bits >> 11) | 1) * 0x1.0p-53;  // avoid 0
    double u1 = (double)((u1_bits >> 11)) * 0x1.0p-53;
    double r = sqrt(-2.0 * log(u0));
    double theta = 2.0 * M_PI * u1;
    return mean + stddev * r * cos(theta);
}

// Persistence — single uint64_t as hex string
// (locale-pinned LC_NUMERIC=C per wire-format-byte-preservation-discipline)
inline void splitmix_save(const Splitmix64& rng, FILE* fp) {
    fprintf(fp, "  \"rng_state\": \"%016lx\",\n", rng.state);
}

inline int splitmix_load(Splitmix64& rng, const char* json_value) {
    // Parse "0123abcd..." into uint64_t
    return sscanf(json_value, "%016lx", &rng.state) == 1 ? 0 : -1;
}

}  // namespace tt
```

### Seed scrambling for per-generator independence

When using multiple Splitmix64 instances (e.g., per-regime per-node), each needs a distinct seed. Naive `seed = base_seed + index` can produce correlated initial outputs (splitmix64's first sample is `state ^ (state >> 31)`).

**Recipe:** scramble the seed through splitmix64 ONCE before storing as initial state.

```cpp
inline Splitmix64 splitmix_seed_scrambled(uint64_t base_seed, int generator_idx) {
    Splitmix64 scrambler{base_seed + (uint64_t)generator_idx};
    Splitmix64 result{scrambler.next()};
    return result;
}
```

This gives ~independent generators at the byte level for the cost of one extra splitmix64 call at construction.

## SHA-256-locked sample-trace test (load-bearing for byte-determinism contract)

The test pattern enforces that splitmix64 output is byte-identical across builds:

```cpp
{
    Splitmix64 rng{0xDEADBEEF12345678ULL};
    uint8_t samples_bytes[8 * 16];
    for (int i = 0; i < 16; ++i) {
        uint64_t s = rng.next();
        for (int b = 0; b < 8; ++b) {
            samples_bytes[i * 8 + b] = (uint8_t)((s >> (b * 8)) & 0xFF);
        }
    }
    uint8_t hash[32];
    tt::sha256_bytes(samples_bytes, sizeof(samples_bytes), hash);
    char hex[65];
    for (int i = 0; i < 32; ++i) sprintf(&hex[i*2], "%02x", hash[i]);
    hex[64] = 0;
    check("PRNG sample-trace SHA-256 lock",
          strcmp(hex, "<known-good-hash-from-reference-build>") == 0);
}
```

If a future contributor "improves" splitmix64 (or replaces it with a faster variant), the SHA-256 lock fails immediately. The check is fast (microseconds) but load-bearing for cross-binary replay-determinism.

## Trade-offs + when to apply

**Apply when:**
- Replay-determinism is a load-bearing concern (paper-trade audits, training-time data shuffling that must be reproducible, Monte Carlo benchmarks)
- Persistence is required (PRNG state survives save/load cycles)
- State size matters (multiple generators in fan-out arrays)
- Cryptographic guarantees NOT required

**Skip when:**
- Cryptographic key generation, random nonces for security protocols → use a CSPRNG (ChaCha20, system-provided)
- Replay-determinism NOT required → standard library distributions are fine
- Statistical quality dominates (PRNG output drives a published research benchmark; BigCrush failure is unacceptable) → use PCG64 or xoroshiro128**
- Very high sample rate (10^9+ samples per generator) where splitmix64's 2^64 period becomes a concern

**Cost:**
- ~50 LOC for the PRNG + Box-Muller implementation
- ~10 LOC for save/load
- ~30 LOC for SHA-256-locked sample-trace test
- ~5 LOC for seed-scrambling helper

Total: ~100 LOC per generator-family. One-time cost.

**Win:**
- Cross-binary replay-determinism (libstdc++ version-invariant)
- Trivial persistence (1 uint64_t = 16 hex chars per generator)
- Compact JSON state (vs 2.5KB for mt19937_64)
- Bytewise-verifiable via SHA-256 sample-trace lock

## Reference implementations

- **First applied:** v5.14.10.A (commit `d8bae14`) — `ML_Headers/ThompsonBandit.hpp` Splitmix64 + Box-Muller for Bayesian posterior sampling. PARITY-014 resolved.
- **Sample-trace SHA-256 test:** `tests/controller_test.cpp` v5.14.10.A test block (~30 LOC; SHA-256-locked sample-trace).
- **Subsequent uses:** None yet — pattern is documented for future replay-determinism-sensitive PRNG needs (e.g., training-time data shuffling, validation-split RNG, future Monte Carlo features).

## Lessons / gotchas

1. **Don't trust `<random>` distributions for cross-binary determinism.** `std::normal_distribution` was the silent landmine in the initial v5.14.10.A plan; only the pre-coding /parity-check audit (PARITY-014) caught it. Generic ML/scientific computing guides recommend `std::normal_distribution`; that's correct for in-process generation but wrong for cross-binary replay.

2. **Seed scrambling is cheap insurance.** Without it, `seed = i + 0` and `seed = i + 1` produce highly-correlated first samples. One extra splitmix64 call removes the correlation.

3. **The SHA-256 lock test is fast — make it a hard fail.** Microseconds to compute; locks the algorithm bytes against any future "optimization" that changes output. Sister to `avx512-byte-determinism-pattern.md` Rule 7.

4. **Box-Muller has its own corners.** Don't pass U=0 to log() — the `| 1` trick in `(u0_bits >> 11) | 1` ensures the 53-bit float result is never exactly 0. Standard textbook gotcha; easy to miss.

5. **Period (2^64) is mostly irrelevant in practice.** A bandit pulling 100 samples/second × 30 days = 2.6 × 10^8 samples; still 2^36 short of period exhaustion. Don't over-think it.

## When to revisit

Re-evaluate this pattern when:
- Switching to multi-symbol mode (M × N_cores × NUM_REGIMES generators) — state size pressure may shift the trade-off
- Adding a Monte Carlo simulation that takes 10^9+ samples (period exhaustion concern)
- Cryptographic guarantees become required (e.g., signing nonces for live exchange API) — switch to CSPRNG
- Statistical quality becomes load-bearing (e.g., publishing a research benchmark that requires BigCrush-grade RNG) — switch to PCG64 or xoroshiro128**
