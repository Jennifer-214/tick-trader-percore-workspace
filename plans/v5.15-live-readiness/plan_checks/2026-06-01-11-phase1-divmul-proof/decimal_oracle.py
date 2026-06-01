#!/usr/bin/env python3
"""
#11 Phase-1 deliverable #2 — the D-100 decimal oracle (reference engine).

WHAT THIS IS: an INDEPENDENT exact-decimal reference for the money op-set the
step-5 sidecar designed (#3 divmul reduce / #4 half-even round / #5 exact
FromString / #6 quantize + fee round-up). The C++ `FixedPoint<10,8>` core (Ship
A/B) will diff its output against this oracle — golden-master discipline
(feedback_golden_master_over_reimplemented_oracle): the oracle computes via
Python `decimal`/bignum (the authority), NEVER by re-deriving the engine's
branchless tricks, so it cannot share a bug with the thing it checks.

WHAT IT GATES (the #1 ship risk, D-100): a deterministic-but-WRONG money core.
Determinism is necessary but not sufficient — these references pin CORRECTNESS.

Phase-1 scope: this module is runnable + SELF-VALIDATING now (it cross-checks the
proven divmul magic from divmul_pow10_proof.py, and cross-checks the branchless
(q,r) half-even formula against Decimal's ROUND_HALF_EVEN). At Ship-A/B it grows
a recorded/Binance-testnet-fill differential (real fills decoded both ways).
"""

from decimal import Decimal, localcontext, ROUND_HALF_EVEN, ROUND_CEILING, ROUND_FLOOR
import random
from divmul_pow10_proof import find_magic, reduce_via_magic   # reuse the PROVEN magic

SCALE = 10 ** 8                  # <10,8> decimal scale (D-104)
FRAC = 8
random.seed(20260601)


# ----------------------------------------------------------------------------
# Oracle references — computed via Decimal (the authority), independent of the
# engine's branchless lowerings. These are the ground truth.
# ----------------------------------------------------------------------------
def oracle_mul_halfeven(A, B):
    """Reference for #2/#3/#4: (A/1e8)*(B/1e8) reduced to <10,8>, round half-even.
       A, B are 10^8-scaled signed ints. Result is a 10^8-scaled signed int."""
    with localcontext() as ctx:
        ctx.prec = 80
        prod = (Decimal(A) * Decimal(B)) / Decimal(SCALE)      # exact value * 1e8
        return int(prod.to_integral_value(rounding=ROUND_HALF_EVEN))


def oracle_fee_roundup(notional, rate):
    """Reference for #4 venue-fee variant (D-109): ceil-at-precision (round UP)."""
    with localcontext() as ctx:
        ctx.prec = 80
        prod = (Decimal(notional) * Decimal(rate)) / Decimal(SCALE)
        return int(prod.to_integral_value(rounding=ROUND_CEILING))


def oracle_from_string(s):
    """Reference for #5: exact decimal string -> 10^8-scaled int. (value, ok).
       Models the VENUE decimal-string contract: alphabet [+-0-9.] only (a venue
       never emits scientific notation / whitespace), then exact value via Decimal.
       The alphabet gate is the contract, NOT the engine's accumulate (value still
       comes from Decimal => independence preserved)."""
    if not s or any(c not in '+-0123456789.' for c in s):
        return None, False
    try:
        with localcontext() as ctx:
            ctx.prec = 80
            d = Decimal(s)
            scaled = d * SCALE
            if scaled != scaled.to_integral_value():           # >FRAC dp -> not exact
                return None, False
            return int(scaled), True
    except Exception:
        return None, False


def oracle_quantize(value_scaled, step_scaled):
    """Reference for #6: round value DOWN to a multiple of step (venue step/tick)."""
    return (value_scaled // step_scaled) * step_scaled


# ----------------------------------------------------------------------------
# The engine's branchless lowerings (what Ship A/B will implement) — mirrored
# here ONLY to cross-check them against the oracle now, before C++ exists.
# ----------------------------------------------------------------------------
def engine_halfeven_from_qr(q, r):
    """#4 branchless half-even from divmul's (q, r), 0<=r<SCALE. result magnitude."""
    round_up = (2 * r > SCALE) or (2 * r == SCALE and (q & 1))
    return q + (1 if round_up else 0)


def engine_mul_reduce(A, B, M, S):
    """#2+#3+#4 on the MAGNITUDE path: abs -> wide product -> divmul -> half-even
       -> reapply sign. Mirrors the sidecar's value-equivalent-by-construction mul."""
    sign = -1 if (A < 0) ^ (B < 0) else 1
    P = abs(A) * abs(B)                       # the wide (<=2N-bit) product (#2)
    q = reduce_via_magic(P, M, S)             # floor(P / 1e8) via PROVEN magic (#3)
    r = P - q * SCALE                         # remainder feeds rounding (#3 returns q,r)
    mag = engine_halfeven_from_qr(q, r)       # #4 banker's round
    return sign * mag


def engine_from_string(s):
    """#5 single-pass digit-accumulate (pure integer; locale-immune). (value, ok)."""
    if not s:
        return None, False
    i, n = 0, len(s)
    neg = False
    if s[0] in '+-':
        neg = (s[0] == '-')
        i = 1
    mant = 0
    seen_dot = False
    frac = 0
    saw_digit = False
    while i < n:
        c = s[i]
        if c == '.':
            if seen_dot:
                return None, False
            seen_dot = True
        elif '0' <= c <= '9':
            saw_digit = True
            mant = mant * 10 + (ord(c) - 48)
            if seen_dot:
                frac += 1
        else:
            return None, False
        i += 1
    if not saw_digit or frac > FRAC:           # >8dp can't occur for a supported venue (D-106 guard)
        return None, False                     # money path SURFACES the error, never silent-zero
    mant *= 10 ** (FRAC - frac)                # scale-adjust to 1e8
    return (-mant if neg else mant), True


# ----------------------------------------------------------------------------
# Differential self-validation (the Phase-1 cross-check; the Ship-A/B gate seed)
# ----------------------------------------------------------------------------
def random_money_scaled():
    """A plausible 10^8-scaled money magnitude: value in [0, ~1e11), 8dp."""
    whole = random.randrange(0, 10 ** 11)
    frac = random.randrange(0, SCALE)
    return whole * SCALE + frac


def run():
    N = 127                                    # the recommended proven width
    M, S = find_magic(SCALE, N)
    print(f"D-100 oracle self-validation (engine lowering vs Decimal authority)")
    print(f"  using PROVEN magic N={N}: M=0x{M:x} S={S}\n")

    # --- mul + half-even reduce: engine vs oracle ---
    fails = 0
    cap_operand = 1 << 63                      # each operand < 2^63 => P < 2^126 < 2^127
    samples = 300000
    for _ in range(samples):
        A = random.randrange(-cap_operand, cap_operand)
        B = random.randrange(-cap_operand, cap_operand)
        if abs(A) * abs(B) >= (1 << N):        # overflow-guard domain (correct-by-construction)
            continue
        if engine_mul_reduce(A, B, M, S) != oracle_mul_halfeven(A, B):
            fails += 1
            if fails <= 5:
                print(f"  MUL MISMATCH A={A} B={B}: "
                      f"engine={engine_mul_reduce(A,B,M,S)} oracle={oracle_mul_halfeven(A,B)}")
    print(f"  #2+#3+#4 mul/half-even:  {'PASS' if fails==0 else 'FAIL'} "
          f"({samples} signed operand pairs)")

    # --- half-even tie cases explicitly (2r == SCALE boundary) ---
    tie_fails = 0
    for q in range(0, 1000):
        r = SCALE // 2                          # exact half
        # construct P with this (q,r): P = q*SCALE + r
        P = q * SCALE + r
        qq = reduce_via_magic(P, M, S)
        rr = P - qq * SCALE
        ref = int((Decimal(P) / Decimal(SCALE)).to_integral_value(rounding=ROUND_HALF_EVEN))
        if engine_halfeven_from_qr(qq, rr) != ref:
            tie_fails += 1
    print(f"  #4 half-even TIES (2r==SCALE): {'PASS' if tie_fails==0 else 'FAIL'} "
          f"(1000 exact-half cases; banker's round-to-even)")

    # --- exact FromString: engine single-pass vs Decimal ---
    s_fails = 0
    strings = ["50000.50", "0.00006150", "1", "0.1", "123456.78901234"[:9+8],
               "-0.00000001", "99999999999.99999999", "0.00000000", "+12.5"]
    for _ in range(50000):
        whole = random.randrange(0, 10 ** 11)
        frac = random.randrange(0, SCALE)
        strings.append(f"{'-' if random.random()<0.5 else ''}{whole}.{frac:08d}")
    for s in strings:
        ev, eok = engine_from_string(s)
        ov, ook = oracle_from_string(s)
        if (eok, ev) != (ook, ov):
            s_fails += 1
            if s_fails <= 5:
                print(f"  STR MISMATCH {s!r}: engine=({eok},{ev}) oracle=({ook},{ov})")
    print(f"  #5 exact FromString:     {'PASS' if s_fails==0 else 'FAIL'} "
          f"({len(strings)} venue-shaped strings)")

    # --- malformed / >8dp rejection (money path surfaces errors, never silent-zero) ---
    bad = ["", "1.2.3", "12x", "0.000000001", "abc", "1e5", " 12", "--1"]
    rej_ok = all(not engine_from_string(b)[1] and not oracle_from_string(b)[1] for b in bad)
    print(f"  #5 malformed/>8dp reject: {'PASS' if rej_ok else 'FAIL'} "
          f"({len(bad)} bad inputs both reject)")

    # --- quantize to venue step (#6) ---
    q_fails = 0
    for _ in range(50000):
        v = random_money_scaled()
        step = random.choice([10 ** k for k in range(0, FRAC + 1)]) or 1
        # engine quantize = floor-to-step (same as oracle here; pins the contract)
        if oracle_quantize(v, step) % step != 0 or oracle_quantize(v, step) > v:
            q_fails += 1
    print(f"  #6 quantize-to-step:     {'PASS' if q_fails==0 else 'FAIL'} (50000 cases)")

    allok = (fails == 0 and tie_fails == 0 and s_fails == 0 and rej_ok and q_fails == 0)
    print(f"\n  === ORACLE {'CLEAN — engine lowerings match the decimal authority' if allok else 'FAILED'} ===")
    return allok


if __name__ == "__main__":
    run()
