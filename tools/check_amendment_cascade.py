#!/usr/bin/env python3
"""check_amendment_cascade.py — CP-1 (cascade-not-propagated) mechanization.

WHY THIS EXISTS (built 2026-08-16 at E.1.2/D-421 step 6; TECH_DEBT-148 close):
When a decision / spec / definition is amended in ONE place, sibling docs that
reference it keep citing the STALE form. Every mechanical doc gate stays green
throughout, because none of them models "this claim was superseded elsewhere."

TECH_DEBT-148 deferred this tool with an explicit re-trigger: *"a CP-1 recurrence
OUTSIDE the memory corpus that the manual procedure misses."* That fired on
2026-08-16: Class 58's own detection signature was corrected (the per-bit
gate-reachability formulation was refuted by prototype), and the ACTIVE handoff,
MASTER and the D-421 STATUS block all kept instructing the next session to build
the refuted shape. `check_session_docs.sh` was green before, during and after.
The cascade was found by reading. That is the M7 signal this tool answers.

THE CENTRAL IDEA — grep the RETIRED phrasing, not the amended file.
The stale-cascade risk lives in what an amendment REMOVED or REWORDED, never in
what it added. So: take the `-` side of the diff, subtract everything still
present on the `+` side of that same file, and treat the remainder as RETIRED
PHRASINGS. Any UNTOUCHED file still carrying a retired phrasing is a candidate.
Both sets are closed and local — the diff window and the corpus — so this asks a
decidable question, unlike "is this reference semantically stale?" which is not.

M10 SCOPE — PARTIAL, and deliberately so. A green means "no untouched doc repeats
a phrasing this window retired." It does NOT mean the cascade is complete: an
amendment that only ADDS (supersedes by addition, retiring nothing textually) is
invisible here, and so is a stale reference that paraphrases rather than quotes.
Read the green as exactly that sentence and no wider. ADVISORY by design (it
fires on a window, so a HARD wiring would red every mid-session run) — same
posture as check_close_out_completeness.py.

CLASS-51 SELF-DEFENSE: REFUSES rc 2 rather than passing when the corpus resolves
to zero files, the git window will not resolve, or the historical-record filter
classifies every root as PRESERVE (which would make a pass vacuous by
construction). A guard that cannot fail is worse than no guard.

LANDMINE 19: corpus roots are named EXPLICITLY and resolved through the workspace
(never `rg <pat> .` from the engine, which is blind to the tests/tools/plans
directory symlinks and reports zero with total confidence).

Wiring: tools/check_session_docs.sh (ADVISORY) + /capture-audit Check 12
(--deep) + /precoding-audit-gate Stage 2.5. Teeth: --selftest (D-137 wrapper
check_amendment_cascade_selftest.sh).
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

from foxroots import WORKSPACE

RC_OK, RC_FINDINGS, RC_REFUSAL = 0, 1, 2

# ---------------------------------------------------------------------------
# Corpus roots — EXPLICIT (Landmine 19). Relative to WORKSPACE.
# ---------------------------------------------------------------------------
CORPUS_ROOTS = ["plans", "DOCS", "DESIGN_SPECS", "claude-skills"]

# Directories whose contents are FROZEN HISTORICAL RECORD. A retired phrasing
# living here is the point of the file, not a defect. This is CP-1's load-bearing
# false-positive surface (M3) — "truthful historical record" vs "stale
# forward-looking reference". Getting this wrong makes the tool cry wolf, and a
# detector that cries wolf costs more than the class it catches.
PRESERVE_DIR_MARKERS = (
    "/postmortems/",
    "/changelogs/",
    "/reports/",
    "/plan_checks/",
    "/capture-audit-reports/",
    "/citable-id-snapshots/",
    "/tools-staging/",
    "/archive/",
)
PRESERVE_FILE_MARKERS = (
    "CHANGELOG.md",
    "LANDMINES.md",          # landmines RECORD what was once true, by design
    "meta-anti-pattern-index.md",   # a catalog of past errors quotes them verbatim
)

# Frontmatter states that mark a doc as no-longer-live.
PRESERVE_FRONTMATTER = re.compile(
    r"^status:\s*(superseded|deferred|closed|retired)\b", re.MULTILINE
)

# ---------------------------------------------------------------------------
# Term extraction
# ---------------------------------------------------------------------------
# HIGH-SIGNAL term shapes only. Plain prose is deliberately NOT mined: it
# produces noise at a rate that gets the whole tool ignored.
_CITABLE_ID = re.compile(
    r"\b(?:D|C|F|AR|CP|WH|PL|M)-\d{1,4}\b"
    r"|\bClass\s+\d{1,3}\b"
    r"|\bTECH_DEBT-\d{1,4}\b"
    r"|\bPARITY-\d{1,4}\b"
    r"|\bH\d{1,2}\b"
)
_BACKTICKED = re.compile(r"`([A-Za-z_][A-Za-z0-9_:.<>]{3,63})`")
_HYPHENATED = re.compile(r"\b([a-z][a-z0-9]+(?:-[a-z0-9]+){1,4})\b")

# Hyphenated words common enough to be pure noise.
_STOP_TERMS = {
    "pre-commit", "read-only", "one-shot", "up-to-date", "self-test", "selftest",
    "cross-ref", "cross-refs", "file-line", "well-formed", "non-zero", "end-to-end",
    "follow-up", "trade-off", "trade-offs", "so-called", "day-to-day", "in-flight",
    "so-far", "as-built", "byte-identical", "high-level", "low-level", "long-term",
    "short-term", "per-file", "per-line", "left-to-right", "top-level",
}
_MIN_TERM_LEN = 6


def extract_retired_terms(diff_text):
    """PURE. Diff text -> the set of high-signal phrasings this diff RETIRED.

    A phrasing is RETIRED when it appears on a removed line and does NOT appear
    on any added line of the same diff. (Same-diff reappearance means the
    amendment kept the term and merely moved/reworded around it.)
    """
    removed, added = [], []
    for line in diff_text.splitlines():
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("-"):
            removed.append(line[1:])
        elif line.startswith("+"):
            added.append(line[1:])

    def harvest(lines):
        out = set()
        for ln in lines:
            for m in _CITABLE_ID.findall(ln):
                out.add(m.strip())
            for m in _BACKTICKED.findall(ln):
                if len(m) >= _MIN_TERM_LEN:
                    out.add(m)
            for m in _HYPHENATED.findall(ln):
                if len(m) >= _MIN_TERM_LEN and m not in _STOP_TERMS:
                    out.add(m)
        return out

    return harvest(removed) - harvest(added)


def classify_path(relpath, text=""):
    """PURE. relpath (posix, workspace-relative) -> 'PRESERVE' | 'CANDIDATE'."""
    p = "/" + relpath.lstrip("/")
    for marker in PRESERVE_DIR_MARKERS:
        if marker in p:
            return "PRESERVE"
    for marker in PRESERVE_FILE_MARKERS:
        if p.endswith("/" + marker) or p.endswith(marker):
            return "PRESERVE"
    # frontmatter check: only the leading block, so a `status:` mention deep in
    # prose cannot silence a live doc.
    head = text[:1200]
    if PRESERVE_FRONTMATTER.search(head):
        return "PRESERVE"
    return "CANDIDATE"


# RARITY GATE — the discriminator that makes this tool usable rather than noise.
#
# Found by dogfooding on its own first live run (2026-08-16): the run returned 6
# findings and 6 of 6 were junk — `first-order`, `sign-off`. Those are ordinary
# English hyphenations, not amendable definitions, and a stop-list for them is
# whack-a-mole. The principled discriminator is CORPUS RARITY: a term that names
# a definition someone can amend is, by construction, RARE. `gate-reachability`
# lives in ~6 files; `first-order` lives in dozens. A term spread across more
# than GENERIC_THRESHOLD live files is shared vocabulary — amending one doc does
# not make the other N stale.
#
# Citable IDs are EXEMPT from the gate: `D-421` or `Class 58` may be cited widely
# and still be exactly the thing that got amended.
GENERIC_THRESHOLD = 8


def _is_citable(term):
    return bool(_CITABLE_ID.fullmatch(term))


def find_stale_refs(terms, corpus, touched, generic_threshold=GENERIC_THRESHOLD):
    """PURE. -> sorted findings [(relpath, term, line_no, excerpt)].

    corpus: {relpath: text}. touched: set of relpaths changed in the window
    (they carry the amendment, so they are not stale by construction).
    """
    live = {p: t for p, t in corpus.items() if classify_path(p, t) == "CANDIDATE"}

    # rarity pass first, so a generic term never reaches the reporting loop
    kept = set()
    for term in terms:
        if _is_citable(term):
            kept.add(term)
            continue
        needle = term.lower()
        n = sum(1 for t in live.values() if needle in t.lower())
        if n <= generic_threshold:
            kept.add(term)

    findings = []
    for relpath, text in sorted(live.items()):
        if relpath in touched:
            continue
        findings.extend(_hits_in_file(relpath, text, kept))
    return findings


def _first_line_with(lines, needle):
    """PURE. -> (1-based line no, stripped excerpt) of the first hit, or None.

    Extracted so find_stale_refs stays 2 levels deep. Operator rule, 2026-08-16:
    no deeper than 1-2 if/else chains — a scan-for-first-match is a named helper,
    not a third nested loop.
    """
    for i, ln in enumerate(lines, 1):
        if needle in ln.lower():
            return i, ln.strip()[:150]
    return None


def _hits_in_file(relpath, text, terms):
    """PURE. -> one finding per (file, term) — members, never per-occurrence tallies."""
    lines = text.splitlines()
    out = []
    for term in sorted(terms):
        hit = _first_line_with(lines, term.lower())
        if hit:
            out.append((relpath, term, hit[0], hit[1]))
    return out


# ---------------------------------------------------------------------------
# git + filesystem wiring
# ---------------------------------------------------------------------------
def _git(args, repo):
    try:
        r = subprocess.run(["git", "-C", str(repo)] + args,
                           capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)
    if r.returncode != 0:
        return None, (r.stderr or "").strip()
    return r.stdout, None


def load_corpus(ws):
    corpus = {}
    for root in CORPUS_ROOTS:
        base = ws / root
        if not base.is_dir():
            continue
        for f in base.rglob("*.md"):
            try:
                corpus[f.relative_to(ws).as_posix()] = f.read_text(
                    encoding="utf-8", errors="replace")
            except OSError:
                continue
    return corpus


def run(since, quiet=False):
    ws = WORKSPACE
    diff, err = _git(["diff", f"{since}..HEAD", "--unified=0", "--", "*.md"], ws)
    if diff is None:
        print(f"[amendment-cascade] REFUSAL — cannot resolve window "
              f"'{since}..HEAD' in {ws}: {err}", file=sys.stderr)
        return RC_REFUSAL

    names, err = _git(["diff", "--name-only", f"{since}..HEAD", "--", "*.md"], ws)
    if names is None:
        print(f"[amendment-cascade] REFUSAL — cannot list changed files: {err}",
              file=sys.stderr)
        return RC_REFUSAL
    touched = {n.strip() for n in names.splitlines() if n.strip()}

    corpus = load_corpus(ws)
    if not corpus:
        print(f"[amendment-cascade] REFUSAL — corpus resolved to ZERO .md files "
              f"under {ws} {CORPUS_ROOTS}. A pass here would be vacuous.",
              file=sys.stderr)
        return RC_REFUSAL
    live = [p for p, t in corpus.items() if classify_path(p, t) == "CANDIDATE"]
    if not live:
        print("[amendment-cascade] REFUSAL — every corpus file classified "
              "PRESERVE; the filter cannot be that broad (Class 51).",
              file=sys.stderr)
        return RC_REFUSAL

    terms = extract_retired_terms(diff)
    findings = find_stale_refs(terms, corpus, touched)

    if not quiet:
        print(f"[amendment-cascade] window {since}..HEAD · "
              f"{len(touched)} .md changed · {len(terms)} retired phrasing(s) · "
              f"corpus {len(corpus)} files ({len(live)} live / "
              f"{len(corpus) - len(live)} preserved)")
    if not terms:
        if not quiet:
            print("[amendment-cascade] OK — this window retired no high-signal "
                  "phrasing (additions only, or reworded in place).")
        return RC_OK
    if not findings:
        if not quiet:
            print("[amendment-cascade] OK — no UNTOUCHED live doc repeats a "
                  "retired phrasing.")
        return RC_OK

    # PRECISION TIERS — measured, not assumed.
    #
    # Dogfooded 2026-08-16: the rarity gate above does NOT separate signal from
    # noise on prose terms. Measured on the live corpus (747 live files):
    #     first-order       6 files    <- noise
    #     gate-reachability 5 files    <- the real 2026-08-16 cascade
    # Equally rare. So rarity cannot discriminate, and pretending otherwise
    # would make this the confidently-wrong detector the whole arc is about.
    #
    # What IS measurable is the SHAPE of the term. A citable ID or a backticked
    # identifier is a thing someone can amend; a bare hyphenated prose word is
    # usually just English. So the output is TIERED rather than filtered — the
    # operator's eye goes to HIGH first, and LOW is a browse-list, not a claim.
    # Nothing is silently dropped, because a dropped finding is invisible and an
    # unranked one is merely tedious.
    high = [f for f in findings if _is_citable(f[1]) or "_" in f[1] or "::" in f[1]]
    low = [f for f in findings if f not in high]

    print(f"\n[amendment-cascade] {len(findings)} CANDIDATE stale reference(s) "
          f"— an untouched live doc still carries a phrasing this window retired.")
    print("  ADVISORY + PARTIAL: each needs a human read. A truthful historical "
          "mention is NOT a defect (CP-1 false-positive surface).")
    for label, group, note in (
        ("HIGH", high, "citable IDs / identifiers — a thing that can be amended"),
        ("LOW", low, "prose phrasings — frequently ordinary English; browse, don't trust"),
    ):
        if not group:
            continue
        print(f"\n  ── {label} ({len(group)}) — {note}")
        for relpath, term, line_no, excerpt in group:
            print(f"  {relpath}:{line_no}")
            print(f"      retired term : {term}")
            print(f"      still reads  : {excerpt}")
    return RC_FINDINGS


# ---------------------------------------------------------------------------
# Teeth (D-137). Drives the PURE core with synthetic input — no git needed.
# ---------------------------------------------------------------------------
def selftest():
    fails = []

    def ok(cond, msg):
        if not cond:
            fails.append(msg)

    # --- extract_retired_terms -------------------------------------------
    diff = (
        "--- a/x.md\n+++ b/x.md\n"
        "-the `gate-reachability` checker per D-421 and Class 58\n"
        "+the `emit-side-coverage` checker per D-421 and Class 58\n"
    )
    terms = extract_retired_terms(diff)
    ok("gate-reachability" in terms, "T1 retired hyphenated term not extracted")
    ok("D-421" not in terms, "T2 term present on BOTH sides must not be retired")
    ok("Class 58" not in terms, "T3 unchanged citable id must not be retired")
    ok("emit-side-coverage" not in terms, "T4 ADDED term must never be retired")

    # the live 2026-08-16 case: a struck phrase with no replacement on the + side
    diff2 = ("-enumerate the **producer set reachable** from the emit sites\n"
             "+see the SUPERSEDED box\n")
    ok("producer-set" not in extract_retired_terms(diff2),
       "T5 must not fabricate a hyphenation that was not in the text")

    # noise control
    diff3 = "-this is a read-only pre-commit follow-up\n+changed\n"
    ok(not (extract_retired_terms(diff3) & _STOP_TERMS),
       "T6 stop-terms must never be emitted")

    # --- classify_path ----------------------------------------------------
    ok(classify_path("plans/v5.15/reports/x.md") == "PRESERVE", "T7 reports/ preserve")
    ok(classify_path("DOCS/changelogs/x.md") == "PRESERVE", "T8 changelogs/ preserve")
    ok(classify_path("DOCS/LANDMINES.md") == "PRESERVE", "T9 landmines preserve")
    ok(classify_path("plans/v5.15/handoffs/live.md") == "CANDIDATE", "T10 handoff live")
    ok(classify_path("plans/a/h.md", "---\nstatus: superseded\n---\nbody") == "PRESERVE",
       "T11 superseded frontmatter preserve")
    ok(classify_path("plans/a/h.md", "---\nstatus: active\n---\nbody") == "CANDIDATE",
       "T12 active frontmatter candidate")
    ok(classify_path("plans/a/h.md", "x" * 4000 + "\nstatus: superseded\n") == "CANDIDATE",
       "T13 a `status:` deep in prose must NOT silence a live doc")

    # --- find_stale_refs --------------------------------------------------
    corpus = {
        "plans/live_handoff.md":  "build the gate-reachability checker next",
        "plans/amended_spec.md":  "the emit-side checker (was gate-reachability)",
        "plans/reports/frozen.md": "we chose gate-reachability at the time",
        "DOCS/LANDMINES.md":       "gate-reachability was the refuted shape",
    }
    f = find_stale_refs({"gate-reachability"}, corpus, touched={"plans/amended_spec.md"})
    paths = {p for p, _, _, _ in f}
    ok(paths == {"plans/live_handoff.md"},
       f"T14 expected only the untouched LIVE doc, got {sorted(paths)}")

    # non-vacuity: the detector must actually fire when nothing is touched
    f2 = find_stale_refs({"gate-reachability"}, corpus, touched=set())
    ok(len(f2) == 2, f"T15 positive control: expected 2 live hits, got {len(f2)}")

    # and must go silent on an unrelated term (no blanket-red)
    f3 = find_stale_refs({"totally-unrelated-phrase"}, corpus, touched=set())
    ok(not f3, "T16 negative control: unrelated term must yield nothing")

    # one hit per (file, term) — members not tallies
    corpus2 = {"plans/x.md": "gate-reachability\ngate-reachability\ngate-reachability"}
    ok(len(find_stale_refs({"gate-reachability"}, corpus2, set())) == 1,
       "T18 must report one finding per (file, term), not per occurrence")

    # --- rarity gate (the anti-noise discriminator) -----------------------
    # a GENERIC term spread across many live files must be suppressed...
    generic = {f"plans/p{i}.md": "this is first-order work" for i in range(12)}
    ok(not find_stale_refs({"first-order"}, generic, set()),
       "T19 a term in 12 live files is shared vocabulary — must NOT be flagged")
    # ...while the SAME term stays reportable when genuinely rare
    rare = {f"plans/p{i}.md": "this is first-order work" for i in range(3)}
    ok(len(find_stale_refs({"first-order"}, rare, set())) == 3,
       "T20 the same term in 3 files IS distinctive — must be flagged")
    # a citable ID is EXEMPT from the gate (widely cited AND amendable)
    wide = {f"plans/p{i}.md": "per D-421 we do X" for i in range(30)}
    ok(len(find_stale_refs({"D-421"}, wide, set())) == 30,
       "T21 citable IDs must bypass the rarity gate")
    # PRESERVE files must not count toward the rarity denominator
    mixed = {"plans/reports/r.md": "first-order " * 1, "plans/live.md": "first-order"}
    mixed.update({f"plans/reports/x{i}.md": "first-order" for i in range(20)})
    ok(len(find_stale_refs({"first-order"}, mixed, set())) == 1,
       "T22 frozen-record files must not inflate the rarity count")

    if fails:
        print("[amendment-cascade selftest] FAIL:")
        for m in fails:
            print("   ✗ " + m)
        return RC_FINDINGS
    print("[amendment-cascade selftest] all 22 teeth pass "
          "(extraction · both-sides · added-term · stop-terms · preserve tiers · "
          "frontmatter-depth · positive + negative controls · dedup)")
    return RC_OK


def main():
    ap = argparse.ArgumentParser(
        description="CP-1 amendment-cascade detection (TECH_DEBT-148). ADVISORY.")
    ap.add_argument("--since", default="HEAD~10", help="window start ref (default HEAD~10)")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    return run(a.since, a.quiet)


if __name__ == "__main__":
    sys.exit(main())
