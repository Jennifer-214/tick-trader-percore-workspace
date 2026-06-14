#!/usr/bin/env python3
"""test_scan_class_44_cfg_orphan.py — NEGATIVE self-test (teeth) for the Class-44 cfg-flag-orphan
scanner (D-137). Proves, in a hermetic temp engine tree, that the scanner (a) FLAGS a synthetic flag
read ONLY on a dead path, (b) does NOT flag a flag with a live reader, (c) oracle-PASSes its cohort.
A scanner that's only ever GREEN could be silently broken — this gives it teeth.
"""
import os
import sys
import subprocess
import tempfile

TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scan_class_44_cfg_orphan.py')

REGISTRY = (
    '#define FOREACH_TEST_CFG_FLAG(X) \\\n'
    '    X(ORPHAN_FLAG, orphan_flag, "Orphan", "T", 0, "no live reader") \\\n'
    '    X(WIRED_FLAG,  wired_flag,  "Wired",  "T", 0, "has a live reader")\n'
)
DEAD = 'void legacy() { if (BITMAP_IS_SET(cfg.test_cfg_flags, MASK_TEST_CFG_ORPHAN_FLAG)) {} }\n'
LIVE = 'void sharded() { if (BITMAP_IS_SET(cfg.test_cfg_flags, MASK_TEST_CFG_WIRED_FLAG)) {} }\n'


def main():
    with tempfile.TemporaryDirectory() as td:
        cf = os.path.join(td, 'CoreFrameworks')
        os.makedirs(cf)
        open(os.path.join(cf, 'TestCfgFlagRegistry.hpp'), 'w').write(REGISTRY)
        open(os.path.join(cf, 'PortfolioController.hpp'), 'w').write(DEAD)   # DEAD reader (legacy)
        open(os.path.join(cf, 'StrategyParameters.hpp'), 'w').write(LIVE)    # LIVE reader (sharded)
        env = dict(os.environ, FOXML_ENGINE=td,
                   FOXML_ORACLE_COHORT='MASK_TEST_CFG_ORPHAN_FLAG')
        r = subprocess.run([sys.executable, TOOL], env=env, capture_output=True, text=True)
        out = r.stdout + r.stderr

        ok = True
        if 'MASK_TEST_CFG_ORPHAN_FLAG' not in out:
            print('FAIL: scanner did NOT flag the synthetic dead-only orphan (no teeth).'); ok = False
        if any('MASK_TEST_CFG_WIRED_FLAG' in ln and ('ORPHAN' in ln or 'UNUSED' in ln)
               for ln in out.splitlines()):
            print('FAIL: scanner FALSELY flagged the live-wired flag.'); ok = False
        if 'oracle PASS' not in out:
            print('FAIL: oracle did not PASS on the synthetic cohort.'); ok = False

        if ok:
            print('[test_scan_class_44_cfg_orphan] PASS — flags the dead-only orphan, spares the '
                  'live-wired flag, oracle PASS (the scanner has teeth).')
            return 0
        print('--- scanner output ---\n' + out)
        return 1


if __name__ == '__main__':
    sys.exit(main())
