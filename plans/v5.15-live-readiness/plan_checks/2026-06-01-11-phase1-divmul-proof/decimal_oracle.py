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


# ----------------------------------------------------------------------------
# Ship-B P1a (2026-06-10, D-100/D-177): freeze Money_Mul oracle vectors as a
# committed C++ fixture. Rows: a.v, b.v (10^8-scaled int64 money), expected .v
# after the SPEC pipeline (mul -> half-even -> closure saturate ±(2^63-1)),
# ovf flag. Edge rows include NEGATIVE ties (the gate's oracle-coverage gap),
# saturation boundary, signs, zeros, identity. Regenerate ONLY at a deliberate
# epoch (golden-master discipline) — never hand-edit the emitted header.
# ----------------------------------------------------------------------------
def emit_money_mul_vectors(path):
    LIM = (1 << 63) - 1

    def spec(a, b):
        v = oracle_mul_halfeven(a, b)
        ovf = 1 if abs(v) > LIM else 0
        v = max(-LIM, min(LIM, v))
        return v, ovf

    rows = []
    edges = [0, 1, -1, 99, -99, SCALE, -SCALE, SCALE // 2, 3 * SCALE,
             12345678, -12345678, 7000000000000, LIM, -LIM, LIM // SCALE,
             70000 * SCALE + 12345678]
    for a in edges:
        for b in edges:
            rows.append((a, b, *spec(a, b)))
    # exact-half ties, both quotient parities, all four sign combos (b=±1 => P = |a|)
    for q in [0, 1, 2, 3, 1000, 10 ** 14]:
        P = q * SCALE + SCALE // 2
        if P <= LIM:
            for a, b in [(P, 1), (-P, 1), (P, -1), (-P, -1)]:
                rows.append((a, b, *spec(a, b)))
    for _ in range(300):
        a = random.randrange(-LIM, LIM + 1) >> random.randrange(0, 60)
        b = random.randrange(-LIM, LIM + 1) >> random.randrange(0, 60)
        rows.append((a, b, *spec(a, b)))

    with open(path, "w") as f:
        f.write("// GENERATED by decimal_oracle.py emit_money_mul_vectors() — Ship-B P1a D-100 frozen fixture.\n")
        f.write("// Python decimal ROUND_HALF_EVEN is the authority; DO NOT hand-edit. Regenerate only at a\n")
        f.write("// deliberate epoch (golden-master discipline). Spec: mul -> half-even -> saturate ±(2^63-1)+flag.\n")
        f.write("#pragma once\n#include <cstdint>\n#include <cstddef>\n\n")
        f.write("struct MoneyMulVec { int64_t a, b, expected; int ovf; };\n")
        f.write("static const size_t MONEY_MUL_VECTOR_COUNT = %d;\n" % len(rows))
        f.write("static const MoneyMulVec MONEY_MUL_VECTORS[] = {\n")
        for a, b, e, o in rows:
            f.write("    { %dLL, %dLL, %dLL, %d },\n" % (a, b, e, o))
        f.write("};\n")
    print("[oracle] wrote %d Money_Mul vectors -> %s" % (len(rows), path))


# ----------------------------------------------------------------------------
# Ship-B P1b (2026-06-10, D-100): Money_Div + Money_Add references + vectors.
# Div spec: (A/1e8)/(B/1e8) = A*1e8/B, ROUND_HALF_EVEN on the value; b==0 =>
# saturate ±(2^63-1) by sign(a) + DIVZERO flag (OVERFLOW suppressed); quotient
# past the closure ceiling => saturate + OVERFLOW. Add spec: exact int sum,
# closure clamp + OVERFLOW.
# ----------------------------------------------------------------------------
def oracle_div_halfeven(A, B):
    with localcontext() as ctx:
        ctx.prec = 80
        prod = (Decimal(A) * Decimal(SCALE)) / Decimal(B)
        return int(prod.to_integral_value(rounding=ROUND_HALF_EVEN))


def emit_money_div_add_vectors(path_div, path_add):
    LIM = (1 << 63) - 1

    def spec_div(a, b):
        if b == 0:
            return (-LIM if a < 0 else LIM), 0, 1
        v = oracle_div_halfeven(a, b)
        ovf = 1 if abs(v) > LIM else 0
        return max(-LIM, min(LIM, v)), ovf, 0

    def spec_add(a, b):
        v = a + b
        ovf = 1 if abs(v) > LIM else 0
        return max(-LIM, min(LIM, v)), ovf

    drows = []
    edges = [0, 1, -1, 99, SCALE, -SCALE, 3 * SCALE, 12345678, 7000000000000, LIM, -LIM, LIM // SCALE]
    for a in edges:
        for b in edges:
            drows.append((a, b, *spec_div(a, b)))
    # exact-half ties via even divisor b = 2*SCALE (2.0): a odd => r = b/2 exactly; q parity = (a-1)/2.
    for q in [0, 1, 2, 3, 1001, 10 ** 12]:
        a = 2 * q + 1
        for sa, sb in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
            drows.append((sa * a, sb * 2 * SCALE, *spec_div(sa * a, sb * 2 * SCALE)))
    for _ in range(300):
        a = random.randrange(-LIM, LIM + 1) >> random.randrange(0, 60)
        b = 0
        while b == 0:
            b = random.randrange(-LIM, LIM + 1) >> random.randrange(0, 60)
        drows.append((a, b, *spec_div(a, b)))

    arows = []
    for a in edges:
        for b in edges:
            arows.append((a, b, *spec_add(a, b)))
    for _ in range(200):
        a = random.randrange(-LIM, LIM + 1)
        b = random.randrange(-LIM, LIM + 1)
        arows.append((a, b, *spec_add(a, b)))

    with open(path_div, "w") as f:
        f.write("// GENERATED by decimal_oracle.py emit_money_div_add_vectors() — Ship-B P1b D-100 frozen fixture.\n")
        f.write("// Python decimal ROUND_HALF_EVEN is the authority; DO NOT hand-edit; regen only at a deliberate epoch.\n")
        f.write("#pragma once\n#include <cstdint>\n#include <cstddef>\n\n")
        f.write("struct MoneyDivVec { int64_t a, b, expected; int ovf, dz; };\n")
        f.write("static const size_t MONEY_DIV_VECTOR_COUNT = %d;\n" % len(drows))
        f.write("static const MoneyDivVec MONEY_DIV_VECTORS[] = {\n")
        for a, b, e, o, z in drows:
            f.write("    { %dLL, %dLL, %dLL, %d, %d },\n" % (a, b, e, o, z))
        f.write("};\n")
    with open(path_add, "w") as f:
        f.write("// GENERATED by decimal_oracle.py emit_money_div_add_vectors() — Ship-B P1b D-100 frozen fixture.\n")
        f.write("// Python int math is the authority (exact); DO NOT hand-edit; regen only at a deliberate epoch.\n")
        f.write("#pragma once\n#include <cstdint>\n#include <cstddef>\n\n")
        f.write("struct MoneyAddVec { int64_t a, b, expected; int ovf; };\n")
        f.write("static const size_t MONEY_ADD_VECTOR_COUNT = %d;\n" % len(arows))
        f.write("static const MoneyAddVec MONEY_ADD_VECTORS[] = {\n")
        for a, b, e, o in arows:
            f.write("    { %dLL, %dLL, %dLL, %d },\n" % (a, b, e, o))
        f.write("};\n")
    print("[oracle] wrote %d div + %d add vectors" % (len(drows), len(arows)))
