#!/usr/bin/env python3
"""
#11 Phase-1 deliverable — divmul_pow10 exactness proof (the #1 ship risk).

GOAL: prove that the decimal reduce  C = floor(P / 10^8)  can be lowered to a
fixed-cost reciprocal-multiply  floor((P * M) >> S)  with constexpr (M, S), and
that the lowering is BIT-EXACT (== floor(P/10^8)) for every dividend P in the
proven range [0, 2^N). A wrong magic = a deterministic-but-WRONG money core, so
"deterministic" is not enough — this is the correctness gate (D-100).

METHOD (why this is a PROOF, not a spot-check):
  The dividend range is up to 2^128 — far too large to enumerate. So the proof
  is ANALYTIC (the Granlund-Montgomery round-up-reciprocal exactness inequality),
  and computation plays two roles:
    (1) VALIDATE the analytic predicate is itself correct, by checking it against
        FULLY EXHAUSTIVE ground-truth on small (d, N) where every n in [0,2^N)
        IS enumerable. If the predicate ever disagrees with brute force, it's
        wrong and we must not trust it on the big case. (enumerate-not-eyeball,
        per feedback_enumerate_set_before_categorical_claim.)
    (2) APPLY the validated predicate to d=10^8 at the target N, and additionally
        run a structured+random differential vs exact // AND vs Python `decimal`
        (the D-100 oracle's reference engine) as a redundant confidence net.

  Round-up reciprocal:  M = ceil(2^S / d).  Let e = M*d - 2^S  (0 <= e < d).
  Then for n = q*d + r (0<=r<d):   M*n/2^S = n/d + e*n/(d*2^S).
  floor(M*n/2^S) == floor(n/d) == q   iff   e*n/2^S < d - r   for all n<2^N.
  Worst case r=d-1 (d-r=1): need e*n < 2^S. SUFFICIENT (covers all n<2^N):
        e * 2^N <= 2^S        <-- the exactness predicate we pick S by.
  At S=N+ceil(log2 d) the predicate always holds (e < d <= 2^ceil(log2 d)),
  so a proven-exact magic ALWAYS exists; we take the minimal such S.
"""

from decimal import Decimal, getcontext
import random

D = 10 ** 8                  # the decimal scale (10^8) — the divisor we reduce by
random.seed(20260601)        # deterministic sample (no Math.random equiv needed; repeatable)
getcontext().prec = 80       # bignum decimal headroom for the oracle reference


# ----------------------------------------------------------------------------
# Core: derive the magic + the analytic exactness predicate
# ----------------------------------------------------------------------------
def excess(M, S, d):
    """e = M*d - 2^S, the round-up reciprocal's numerator excess."""
    return M * d - (1 << S)


def predicate_exact(M, S, d, N):
    """Analytic SUFFICIENT exactness condition for floor(M*n>>S)==floor(n/d), all n<2^N."""
    e = excess(M, S, d)
    return 0 <= e and e * (1 << N) <= (1 << S)


def find_magic(d, N):
    """Minimal S>=0 with M=ceil(2^S/d) proven exact over [0,2^N). Returns (M,S)."""
    ceil_log2_d = (d - 1).bit_length()          # ceil(log2 d)
    for S in range(N, N + ceil_log2_d + 2):     # minimal S lives in [N, N+ceil(log2 d)]
        M = ((1 << S) + d - 1) // d             # ceil(2^S / d)
        if predicate_exact(M, S, d, N):
            return M, S
    raise RuntimeError("no exact magic found (should be impossible)")


def reduce_via_magic(n, M, S):
    """The lowering the C++ core will run: floor((n * M) >> S)."""
    return (n * M) >> S


# ----------------------------------------------------------------------------
# (1) VALIDATE the predicate against fully-exhaustive ground truth
# ----------------------------------------------------------------------------
def exhaustive_holds(M, S, d, N):
    """Brute force: does floor(M*n>>S)==n//d for EVERY n in [0,2^N)?"""
    for n in range(1 << N):
        if (n * M) >> S != n // d:
            return False, n
    return True, None


def validate_predicate():
    """
    Prove the analytic predicate is SOUND: for many small (d,N), the predicate's
    verdict on the minimal-S magic must match brute force, AND we also probe
    NON-minimal / deliberately-too-small S to confirm the predicate correctly
    REJECTS inexact magics (no false 'exact').
    """
    print("=== (1) predicate validation vs EXHAUSTIVE brute force (small cases) ===")
    divisors = [3, 7, 10, 100, 1000, 9973, 100000, D % 100003 + 7]
    ok = True
    checks = 0
    for d in divisors:
        Nmax = 22 if d <= 1000 else 20          # 2^22 = 4.2M iters — tractable
        for N in range(1, Nmax + 1):
            M, S = find_magic(d, N)
            ex, cx = exhaustive_holds(M, S, d, N)
            checks += 1
            if not ex:
                ok = False
                print(f"  FAIL  d={d} N={N}: minimal-S magic NOT exact at n={cx} "
                      f"(M={M},S={S}) — predicate is UNSOUND")
            # adversarial: a too-small S must be REJECTED by predicate AND fail brute force
            if S > N:
                S_bad = S - 1
                M_bad = ((1 << S_bad) + d - 1) // d
                pred_bad = predicate_exact(M_bad, S_bad, d, N)
                ex_bad, _ = exhaustive_holds(M_bad, S_bad, d, N)
                if pred_bad and not ex_bad:
                    ok = False
                    print(f"  FAIL  d={d} N={N}: predicate said EXACT but brute force "
                          f"disagrees (S_bad={S_bad}) — FALSE POSITIVE")
    print(f"  {'PASS' if ok else 'FAIL'} — {checks} (d,N) pairs; predicate sound "
          f"(no inexact minimal-S magic; no false-positive on too-small S)")
    return ok


# ----------------------------------------------------------------------------
# (2) APPLY to d=10^8 across candidate dividend widths
# ----------------------------------------------------------------------------
def width_table():
    print("\n=== (2) d=10^8 magic across candidate dividend widths N ===")
    print("  N    S    bitlen(M)   product_bits=N+bitlen(M)   fits 256-bit mul?   M (hex)")
    rows = {}
    for N in (96, 104, 112, 120, 124, 127, 128):
        M, S = find_magic(D, N)
        bM = M.bit_length()
        pbits = N + bM
        rows[N] = (M, S, bM, pbits)
        print(f"  {N:<4} {S:<4} {bM:<11} {pbits:<25} "
              f"{'YES' if pbits <= 256 else 'NO (' + str(pbits) + ')':<18} 0x{M:x}")
    return rows


# ----------------------------------------------------------------------------
# (3) Differential vs exact // AND vs Python `decimal` (D-100 oracle reference)
# ----------------------------------------------------------------------------
def oracle_floor_div(n, d):
    """Independent reference: floor(n/d) via Python bignum `decimal` (not //)."""
    # Decimal with enough precision computes n/d exactly enough to floor correctly.
    from decimal import localcontext, ROUND_FLOOR
    with localcontext() as ctx:
        ctx.prec = max(60, len(str(n)) + 20)
        return int((Decimal(n) / Decimal(d)).to_integral_value(rounding=ROUND_FLOOR))


def differential(N):
    M, S = find_magic(D, N)
    print(f"\n=== (3) differential at N={N}  (M=0x{M:x}, S={S}) ===")
    cap = 1 << N
    # structured: the analytically-binding dividends (just-below/at multiples of d),
    # powers of ten, type boundaries, plus a heavy random sample.
    tests = set()
    for k in range(0, 2000):
        base = random.randrange(1, cap // D + 1) * D if cap > D else 0
        for off in (-1, 0, 1, D - 1):
            v = base + off
            if 0 <= v < cap:
                tests.add(v)
    for p in range(0, N):
        tests.add((1 << p) % cap)
    for p10 in range(0, 40):
        v = 10 ** p10
        if v < cap:
            tests.add(v)
    tests.update((0, 1, D - 1, D, D + 1, cap - 1, cap // 2))
    for _ in range(200000):
        tests.add(random.randrange(0, cap))

    fails = 0
    for n in tests:
        magic = reduce_via_magic(n, M, S)
        exact = n // D
        if magic != exact or magic != oracle_floor_div(n, D):
            fails += 1
            if fails <= 5:
                print(f"  MISMATCH n={n}: magic={magic} exact={exact} "
                      f"oracle={oracle_floor_div(n, D)}")
    print(f"  {'PASS' if fails == 0 else 'FAIL'} — {len(tests)} dividends "
          f"(structured binding-set + powers + {200000} random); "
          f"magic == exact// == decimal-oracle for all" if fails == 0
          else f"  {fails} MISMATCHES")
    return fails == 0


if __name__ == "__main__":
    print("#11 divmul_pow10 exactness proof — d = 10^8\n")
    v_ok = validate_predicate()
    rows = width_table()
    # Prove the differential at the two design-relevant widths:
    #   N=120 (fits the existing 256-bit wide-multiply with margin — guarded design)
    #   N=128 (full __int128 magnitude — correct-by-construction, product=257-bit)
    d120 = differential(120)
    d128 = differential(128)

    print("\n=== VERDICT ===")
    allok = v_ok and d120 and d128
    print("  PROVEN-EXACT" if allok else "  *** NOT PROVEN — investigate ***")
    M120, S120, bM120, pb120 = rows[120]
    M128, S128, bM128, pb128 = rows[128]
    print(f"  N=120: M=0x{M120:x}  S={S120}  product={pb120}-bit (fits 256 ✓)")
    print(f"  N=128: M=0x{M128:x}  S={S128}  product={pb128}-bit")
