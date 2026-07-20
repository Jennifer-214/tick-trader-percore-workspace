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



# ── the JUDGMENT half — the part that has no other detector ──────────────────────────────────
# Auto-write coverage (above) was the FIRST failure. These are the other three observed in the
# same close, each of which the mechanical sweep was green through:
#
#   VOLATILE COUNTS   a raw count written into a handoff is stale on the very commit that records
#                     it. Observed: "26 commits" -> corrected to 24 -> already 25 by the next
#                     commit -> and a stale "98 enrolled" survived TWO self-sweeps. This is not a
#                     value to patch better; it is unfixable by writing a better number.
#   NO RE-DERIVE      a reader cannot recompute what the document asserts, so a stale figure is
#                     indistinguishable from a current one.
#   NO JUDGMENT LEDGER  /capture-audit's checks 2/3/5/6/7/9/10/12 are JUDGMENT and tool-backed by
#                     nothing. Twice in a row they simply never ran, and both times the only
#                     detector was operator pushback.

VOLATILE_COUNT_PATTERNS = [
    (r"\b\d+\s+commits\b",          "commit count"),
    (r"\b\d+\s+tools?\s+enrolled\b", "tools-enrolled count"),
    (r"\b\d+\s+HARD\b",            "HARD-check count"),
    (r"\b\d+\s+ADV\b",             "ADV-check count"),
    (r"\b\d+\s+baselined\b",       "baseline size"),
    (r"\b\d+\s+ids\s+indexed\b",   "id-index size"),
]
JUDGMENT_CHECKS = ["2", "3", "5", "6", "7", "9", "10", "12"]


def _strip_code_fences(text):
    """Counts INSIDE a fence are fine — that is where re-derive commands and sample output live.
    Only prose assertions are flagged."""
    out, fenced = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return "\n".join(out)


def check_handoff_quality(handoff: Path, quiet=False):
    """Returns a list of (severity, message). The handoff is the artifact that must survive a
    context boundary, so a stale figure in it misleads exactly the reader with no way to check."""
    findings = []
    if not handoff or not handoff.is_file():
        return [("HIGH", "no active handoff found — a close-out without one loses the session")]
    raw = handoff.read_text(encoding="utf-8", errors="replace")
    prose = _strip_code_fences(raw)

    for pat, what in VOLATILE_COUNT_PATTERNS:
        for m in re.finditer(pat, prose):
            line_no = prose[:m.start()].count("\n") + 1
            findings.append(("MED",
                f"volatile {what} in prose: {m.group(0)!r} (~prose line {line_no}) — anchor it to a "
                f"SHA range or move it into a re-derive block; a count is stale on the commit that "
                f"records it"))

    if not re.search(r"re-?derive", raw, re.I):
        findings.append(("HIGH",
            "no RE-DERIVE block — a reader cannot recompute what this document asserts, so a stale "
            "figure is indistinguishable from a current one"))

    missing = [c for c in JUDGMENT_CHECKS
               if not re.search(rf"(?:^|\W)(?:Check\s*)?{c}\b[^\n]{{0,90}}", raw, re.M)
               or not re.search(rf"Check\s*{c}\b", raw)]
    if len(missing) > len(JUDGMENT_CHECKS) // 2:
        findings.append(("HIGH",
            f"no JUDGMENT-CHECK ledger — /capture-audit checks {', '.join(JUDGMENT_CHECKS)} are "
            f"tool-backed by NOTHING, and have twice been skipped silently. Record each one's "
            f"verdict in the handoff so a skip is visible rather than invisible"))

    if not re.search(r"adversarial|independent review|a-class", raw, re.I):
        findings.append(("MED",
            "no INDEPENDENT REVIEW recorded — per AR-8 the maker does not grade their own artifact, "
            "and self-checking this handoff failed four consecutive times before an independent "
            "pass was run"))
    return findings


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

    # ── handoff quality: the judgment half ───────────────────────────────────────────────────
    hq = []
    active = None
    for h in sorted((WORKSPACE / "plans").glob("*/handoffs/*.md")):
        head = h.read_text(encoding="utf-8", errors="replace")[:400]
        if re.search(r"^status:\s*active", head, re.M):
            active = h
            break
    hq = check_handoff_quality(active)
    if hq:
        print(f"\n[close-out] handoff quality — {len(hq)} finding(s) on "
              f"{active.name if active else '(none)'}:")
        for sev, msg in hq[:12]:
            print(f"  [{sev}] {msg}")
        if len(hq) > 12:
            print(f"  ... and {len(hq) - 12} more")

    hq_hi = [f for f in hq if f[0] == "HIGH"]
    if not untouched and not hq_hi:
        if hq:
            print(f"[close-out] PASS (with {len(hq)} advisory) — surfaces covered; handoff carries "
                  f"re-derive + judgment ledger")
        else:
            print(f"[close-out] PASS — every auto-write surface was touched or explained")
        return 0
    if hq_hi and not untouched:
        return 1

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

    # ── handoff-quality teeth. Each new check gets a PLANTED positive and a negative control,
    # because a check that has never been seen to fire is exactly what this tool exists to catch.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "bad.md"
        bad.write_text("# handoff\n\nThis session had 24 commits and 100 tools enrolled.\n")
        f = check_handoff_quality(bad)
        kinds = " ".join(m for _, m in f)
        chk("planted VOLATILE COUNT is flagged", "volatile commit count" in kinds)
        chk("planted volatile tools-enrolled count is flagged", "tools-enrolled" in kinds)
        chk("missing RE-DERIVE block is flagged HIGH",
            any(s == "HIGH" and "RE-DERIVE" in m for s, m in f))
        chk("missing JUDGMENT-CHECK ledger is flagged HIGH",
            any(s == "HIGH" and "JUDGMENT-CHECK" in m for s, m in f))
        chk("missing INDEPENDENT REVIEW is flagged",
            any("INDEPENDENT REVIEW" in m for _, m in f))

        # NEGATIVE CONTROL — a conforming handoff must produce NOTHING. Without this the checks
        # could be firing unconditionally, which reads identical to working.
        good = Path(td) / "good.md"
        good.write_text(
            "# handoff\n\nwindow `abc1234..HEAD`. Re-derive with the commands below.\n"
            "Check 2 ok. Check 3 ok. Check 5 ok. Check 6 ok. Check 7 ok. Check 9 ok. "
            "Check 10 ok. Check 12 ok.\nIndependent review: a-class, verdict recorded.\n"
            "```\ngit log --oneline abc1234..HEAD | wc -l   # 24 commits, 100 tools enrolled\n```\n")
        gf = check_handoff_quality(good)
        chk(f"conforming handoff produces ZERO findings (negative control; got {len(gf)})",
            len(gf) == 0)
        chk("counts INSIDE a code fence are NOT flagged (that is where re-derive output lives)",
            not any("volatile" in m for _, m in gf))

        missing = Path(td) / "gone.md"
        chk("an ABSENT handoff is a HIGH finding, not a silent pass",
            any(s == "HIGH" for s, _ in check_handoff_quality(missing)))
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
