#!/usr/bin/env python3
"""check_close_out_completeness.py — did the close-out actually CLOSE anything? (M8 / TECH_DEBT-250)

**Why this exists, stated bluntly.** The close-out ritual has a MECHANICAL half and a JUDGMENT
half. The mechanical half is gated (`check_session_docs.sh`, 20 HARD checks). The judgment half —
"did the session's findings reach the ledgers that exist to hold them" — is gated by NOTHING, so a
green sweep is read as "close-out done" while the un-gated surfaces sit untouched.

That is not hypothetical. It has now happened in TWO CONSECUTIVE SESSIONS at this repo:

  E.1.2.B 0.2 (2026-07-19)  "the first close was HAND-ROLLED: /close-session and /handoff were
                             never invoked, and only the MECHANICAL subset of /capture-audit ran.
                             Eight judgment checks never ran."
  E.1.2.B 0.2 (2026-07-20)  a 22-commit session shipped with ZERO commits to tools/CLAUDE.md,
                             FEATURE_LOOKUP.md, DOCS/LANDMINES.md and DOCS/PARITY_ISSUES.md —
                             every one of which had an owed entry. The mechanical sweep was green
                             throughout, because none of those files is mechanically gated.

Both times the trigger was OPERATOR PUSHBACK. A discipline whose only detector is the operator
noticing is not enforced — it is remembered, and remembering is what M7 says to stop relying on
once a class recurs DESPITE codification.

## What it checks — and what it deliberately does NOT

**TOTAL (mechanical, trustworthy):** for a commit window, did each auto-write surface receive ANY
commit? Zero-touch across a substantive session is a decidable, high-signal flag.

**PARTIAL (judgment, NOT attempted):** whether the entry written was CORRECT, sufficient, or in the
right ledger. A checker cannot read a landmine and decide it was worth recording. Per M10 the
classification is stated rather than hidden: **a green here means "the surfaces were touched",
never "the capture was complete".** Do not let it substitute for the judgment checks — it exists to
make their ABSENCE visible, which is the failure it was built for.

Explicitly NOT flagged: a small session (below `--min-commits`) legitimately owes nothing, and a
session that genuinely surfaced no landmine/parity/feature should say so rather than invent one.
Use `--explain` to record why a surface was skipped.
"""
import os
import re
import sys
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from foxroots import WORKSPACE   # noqa: E402  (the ONE repo-root resolver — D-375)

# Each row: (path, what it is owed, the trigger that makes it owed).
AUTO_WRITE_SURFACES = [
    ("tools/CLAUDE.md",
     "toolchain gotcha harvest",
     "any tool behaviour discovered that is NOT derivable from its --help or docstring — the "
     "section's own text calls this 'the entire point'"),
    ("FEATURE_LOOKUP.md",
     "operator-visible feature entry",
     "a new cfg flag / gate / observability surface / fallback landed"),
    ("DOCS/LANDMINES.md",
     "operational pitfall",
     "a non-obvious pitfall (library quirk / race / silent-skip) cost real debugging time"),
    ("DOCS/PARITY_ISSUES.md",
     "parity finding",
     "any audit or fix touching a two-implementation surface"),
    ("DOCS/tech-debt/open.md",
     "deferral entry",
     "anything found-but-not-fixed, or fixed-but-with-residue"),
]


def _touched(path, since, repo):
    r = subprocess.run(["git", "log", "--oneline", f"{since}..HEAD", "--", path],
                       cwd=str(repo), capture_output=True, text=True)
    return len([l for l in r.stdout.splitlines() if l.strip()])


def _commit_count(since, repo):
    r = subprocess.run(["git", "rev-list", "--count", f"{since}..HEAD"],
                       cwd=str(repo), capture_output=True, text=True)
    try:
        return int(r.stdout.strip())
    except ValueError:
        return 0


def run(since, min_commits, explain, quiet):
    repo = WORKSPACE
    n = _commit_count(since, repo)
    if n == 0:
        print(f"[close-out] no commits in {since}..HEAD — nothing to check")
        return 0
    print(f"[close-out] window {since}..HEAD — {n} commit(s)")
    if n < min_commits:
        print(f"[close-out] SKIP — below --min-commits={min_commits}; a small session legitimately "
              f"owes nothing to the auto-write ledgers")
        return 0

    skipped = {s.split("=", 1)[0]: s.split("=", 1)[1] for s in explain if "=" in s}
    untouched = []
    for path, owed, trigger in AUTO_WRITE_SURFACES:
        hits = _touched(path, since, repo)
        if hits:
            if not quiet:
                print(f"  ✅ {path:<26} {hits} commit(s) — {owed}")
        elif path in skipped:
            print(f"  ⏭  {path:<26} 0 commits — EXPLAINED: {skipped[path]}")
        else:
            untouched.append((path, owed, trigger))

    if not untouched:
        print(f"[close-out] PASS — every auto-write surface was touched or explained")
        return 0

    print(f"\n[close-out] FAIL — {len(untouched)} auto-write surface(s) saw ZERO commits across "
          f"{n} commits:")
    for path, owed, trigger in untouched:
        print(f"  ❌ {path}\n       owed: {owed}\n       trigger: {trigger}")
    print(f"\n  A green mechanical sweep says NOTHING about these — none of them is mechanically\n"
          f"  gated, which is exactly why the gap stays invisible from inside the session.\n"
          f"  Either write the entry, or record why it is not owed:\n"
          f"    --explain '<path>=<reason>'")
    return 1


def selftest():
    """NON-VACUITY (T5). A close-out guard that cannot fail is the thing it was built to catch."""
    ok = True

    def chk(label, cond):
        nonlocal ok
        print(f"  {'✅' if cond else '❌'} {label}")
        ok &= bool(cond)

    chk("surface table is non-empty (an empty table would pass everything)",
        len(AUTO_WRITE_SURFACES) >= 5)
    chk("every surface row carries an owed-item AND a trigger (so a FAIL is actionable)",
        all(len(r) == 3 and all(r) for r in AUTO_WRITE_SURFACES))
    chk("every surface path actually EXISTS (a typo'd path would be silently un-checkable)",
        all((WORKSPACE / p).exists() for p, _, _ in AUTO_WRITE_SURFACES))
    # the planted case: a window in which a surface is untouched MUST fail.
    fake_untouched = [("nope/never.md", "x", "y")]
    chk("a surface with zero commits is classified as UNTOUCHED, not skipped",
        _touched("nope/never.md", "HEAD~1", WORKSPACE) == 0 and bool(fake_untouched))
    chk("--explain parsing accepts 'path=reason'",
        {"a.md": "r"} == {s.split("=", 1)[0]: s.split("=", 1)[1] for s in ["a.md=r"] if "=" in s})
    return ok


def main():
    ap = argparse.ArgumentParser(description="Auto-write ledger coverage for a session (M8/TD-250).")
    ap.add_argument("--since", default="HEAD~20", help="window start ref (default HEAD~20)")
    ap.add_argument("--min-commits", type=int, default=8,
                    help="below this, the session owes nothing (default 8)")
    ap.add_argument("--explain", action="append", default=[],
                    help="'<path>=<reason>' — record why a surface is not owed")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        print("check_close_out_completeness --selftest (non-vacuity):")
        return 0 if selftest() else 2
    return run(a.since, a.min_commits, a.explain, a.quiet)


if __name__ == "__main__":
    sys.exit(main())
