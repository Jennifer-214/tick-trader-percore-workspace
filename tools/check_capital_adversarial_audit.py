#!/usr/bin/env python3
"""check_capital_adversarial_audit.py — TECH_DEBT-164 part B (auto-fire failsafe).

The BINDING adversarial-default (feedback_adversarial_framing_default_for_checks + meta-
anti-pattern AR-8) cannot be self-attested: a capital test declared "verified" on a self-
check is the exact oms-ts-1 failure. `tests/` is gitignored, so a diff-based gate can't see
test changes — instead this enforces a STANDING marker invariant: every capital TEST
assertion-block (Money_Eq / Money_IsZero on a money field) carries a refute disposition
marker within ~45 lines above it, so an un-refuted capital test is CONSPICUOUS at the gate.

Convention:
  // ADV-REFUTE: <date> (<verdict / N gaps folded>)   -- an independent FIND/REFUTE ran
  // ADV-SELF: <reason>                                -- explicit opt-out, with a stated reason

Advisory by default (exit 0, reports unmarked blocks); --strict exits 1 on any unmarked
block. Existing unmarked blocks are a KNOWN, shrinking backlog (close-the-class pattern:
the guard flags the class; existing are KNOWN-PENDING; NEW capital tests must comply).

Policy: feedback_adversarial_framing_default_for_checks (binding 2026-06-11). Error-shape it
closes: meta-anti-pattern-index AR-8 (self-attested verification).
"""
import sys
import re
import glob
import os

MONEY = (r'(total_fees|total_maker_fees|total_taker_fees|realized_pnl'
         r'|core_realized|core_fees|ks_peak_balance|balance)')
ASSERT = re.compile(r'(Money_Eq|Money_IsZero)\s*\(.*' + MONEY)
MARKER = re.compile(r'ADV-REFUTE|ADV-SELF|ADVERSARIALLY[- ]REFUTED')
WINDOW = 70  # lines above a block to search for its disposition marker


def find_unmarked(files):
    unmarked = []
    for f in files:
        lines = open(f, encoding='utf-8', errors='replace').read().splitlines()
        hits = [i for i, l in enumerate(lines) if ASSERT.search(l)]
        # group consecutive-ish asserts (gap <= 8 lines) into one block
        blocks = []
        for h in hits:
            if blocks and h - blocks[-1][-1] <= 20:
                blocks[-1].append(h)
            else:
                blocks.append([h])
        for b in blocks:
            start = b[0]
            ctx = "\n".join(lines[max(0, start - WINDOW):start + 1])
            if not MARKER.search(ctx):
                unmarked.append((os.path.basename(f), start + 1, lines[start].strip()[:80]))
    return unmarked


def main():
    strict = '--strict' in sys.argv
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    targets = [a for a in sys.argv[1:] if not a.startswith('--')]
    if targets:  # explicit file(s)/dir(s) — used by the self-test (D-137)
        files = []
        for t in targets:
            if os.path.isdir(t):
                files += sorted(glob.glob(os.path.join(t, '*.cpp')))
            elif os.path.isfile(t):
                files.append(t)
    else:
        files = sorted(glob.glob(os.path.join(root, 'tests', '*.cpp')))
    unmarked = find_unmarked(files)
    if unmarked:
        tag = "FAIL" if strict else "WARN"
        print(f"[check_capital_adversarial_audit] {tag} — {len(unmarked)} capital test "
              f"assertion-block(s) with NO adversarial-refute marker (TECH_DEBT-164 / AR-8):")
        for f, ln, t in unmarked[:30]:
            print(f"    {f}:{ln}  {t}")
        if len(unmarked) > 30:
            print(f"    ... +{len(unmarked) - 30} more (KNOWN backlog — close-the-class, shrinking)")
        print("  -> after an independent FIND/REFUTE add `// ADV-REFUTE: <date> (<verdict>)` above the")
        print("     block, or `// ADV-SELF: <reason>` to opt out with a stated reason.")
        return 1 if strict else 0
    print("[check_capital_adversarial_audit] OK — every capital test block carries a refute disposition.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
