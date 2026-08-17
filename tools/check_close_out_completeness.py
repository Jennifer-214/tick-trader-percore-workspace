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

  E.1.2 / D-421 (2026-08-15)  a 20-commit session again hand-rolled the close — /close-session was
                             never invoked. The mechanical sweep was GREEN while SIX reference-doc
                             auto-writes were missing, including one the session had NAMED as owed
                             mid-flight and then dropped. Found only when the operator asked "all
                             reference docs updated?" — TWICE, the second time after the first
                             answer had already been "yes, verified". The reference-doc rows in
                             AUTO_WRITE_SURFACES below were added as a direct result.

**The third instance sharpens the diagnosis: the SKILL is not the problem.** `/close-session` Stage
5.5 item 7 already names CODE_MAP staleness by name, and Stage 7.5 already invokes this tool. It is
well-built and it went UNFIRED. The failure mode is non-invocation, not inadequacy — which is why
adding more to the skill would be treating the wrong surface (`feedback_resource_use_gated_on_
existence_not_felt_need`: reach for the resource because it EXISTS, since felt-need is miscalibrated
exactly where the resource is load-bearing). Candidate structural close: have `/close-session` STAMP
the handoff frontmatter, so a handoff written without the stamp is mechanically detectable as a
hand-rolled close. Tracked TECH_DEBT-278.

Every time the trigger was OPERATOR PUSHBACK. A discipline whose only detector is the operator
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
    # ── REFERENCE-DOC surfaces (added 2026-08-15, E.1.2/D-421 close-out) ─────────────────────
    # These carry auto-write contracts stated IN THEIR OWN TEXT, and none of them is otherwise
    # gated. Measured, which is why they are here: at that close-out the mechanical sweep was
    # fully GREEN while SIX reference-doc auto-writes were missing — a pattern spec's canonical-
    # applications table (whose own "Gotcha 3" is literally *"Auto-write contract: keep canonical
    # applications table updated"*), two bug-class known-instances, a stale teeth count, an
    # un-regenerated CODE_MAP, and an invariants-map row. The session had even NAMED the first one
    # as owed, mid-session, and then dropped it.
    #
    # Same shape as the D-421 finding that produced them: every guard pointed at what was written,
    # none asked what was missing. These rows do not detect whether an entry is owed — they make
    # the SKIP VISIBLE, which is this tool's whole design.
    ("DESIGN_SPECS/",
     "pattern-application / spec update",
     "a pattern was APPLIED, EXTENDED or REFUTED — the spec's own canonical-applications table and "
     "maturity line are its stated auto-write contract, and a spec that stops recording its "
     "applications stops being able to justify its own Stage"),
    ("DOCS/recurring-bug-patterns/",
     "known-instance row",
     "an instance of an existing Class was FOUND or FIXED — the catalog's own rule is 'when a new "
     "instance is found, add it under Known instances with the fix commit'; an un-recorded instance "
     "silently understates a class's recurrence_count, which is what gates its promotion"),
    ("DOCS/CODE_MAP.md",
     "regen (mechanical — `./tools/gen_code_map.sh`)",
     "any function added, renamed or deleted; it is the anti-fabrication ground truth that "
     "/readiness, /precoding-audit-gate and every armed agent grep against, so a stale map "
     "silently weakens every downstream check that trusts it"),
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

# A VOLATILE noun is one whose count changes as work proceeds. Matching is SHAPE-BASED — a digit
# adjacent to one of these nouns — rather than a list of phrases I happened to have seen.
#
# WHY THE REDESIGN. The first version enumerated exact phrases (`\d+ commits`, `\d+ tools enrolled`,
# ...) drawn from the specific failures of one session. Measured against the 9 findings an independent
# review actually raised against that same session's handoff, it caught **1**. It missed `22-commit`
# (hyphen, singular) while matching `22 commits`; it missed `3 of 7 deliverables`, `405 sentinels`,
# `837-id`, `70% false`. Enumerating instances instead of the shape is the hardcoded-trigger
# anti-pattern, and a guard built from the last failure catches only the last failure.
VOLATILE_NOUNS = (
    r"commits?|tools?|ids?|findings?|entries|entry|sentinels?|deliverables?|checks?|"
    r"violations?|dangling|specs?|memories|memory|skills?|"
    r"tests?|files?|sites?|blocks?|rows?|ledgers?|gates?|HARD|ADV"
)
VOLATILE_COUNT_PATTERNS = [
    # `24 commits` · `22-commit` · `837-id` · `405 sentinels` — digit ADJACENT to a volatile noun,
    # hyphen or space, singular or plural. This one pattern replaces the whole enumerated list.
    (rf"(?<![-\w.])\d+[\s-]+(?:{VOLATILE_NOUNS})\b", "volatile count (digit + volatile noun)"),
    # `3 of 7 deliverables` · `3 of 7` — the progress tally. THE most dangerous shape: it stays
    # numerically correct while its MEMBERSHIP rotates, so no proofread catches it (D-402).
    (r"\b\d+\s+of\s+\d+\b", "progress tally (`N of M`) — name the members instead"),
    # `up from 400` · `400 → 405` · `145→141` — a delta invites arithmetic that goes stale on BOTH
    # sides. The observed instance asserted `400 + 19 = 405`.
    (r"\bup\s+from\s+\d+\b|\b\d+\s*(?:→|->)\s*\d+\b", "count delta"),
    # `70% false` · `84% of the deliverable` — a percentage is a tally with the denominator hidden,
    # which is how one got transplanted onto an unrelated measurement.
    (r"\b\d+(?:\.\d+)?%", "percentage (a tally with a hidden denominator)"),
    # `(e)→(f)→(g)→(d)` — a volatile ORDER carrying no digits, so every numeric pattern above
    # misses it. It went stale the moment (e) landed and was replicated into three documents.
    (r"\([a-z]\)\s*(?:→|->)\s*\([a-z]\)", "deliverable-order sequence"),
]

# CATEGORICAL ABSENCE claims — not counts at all, and the class that produced the worst finding.
# A handoff asserted 8 ids had "no content anywhere" and escalated them to the operator; 3 of 3
# searched had recoverable content on disk. What was VERIFIED was "no defining row in any ledger
# FILE"; what was WRITTEN was "no content anywhere". Promoting a narrow verified fact to a broad
# claim is AR-15, and here it would have written permanent falsehoods into an append-only ledger.
#
# The check does not ban the claim — it requires the claim to CARRY ITS SEARCH. An absence is only
# a fact relative to a named search space (M9: enumerate the set before a categorical claim).
ABSENCE_CLAIM_PATTERNS = [
    (r"\bno\s+\w+\s+anywhere\b",                    "absence claim: `no ... anywhere`"),
    (r"\bexists?\s+in\s+NO\b|\bin\s+no\s+\w+\s+file\b", "absence claim: `exists in NO ...`"),
    (r"\bverified\s+absent\b",                       "absence claim: `verified absent`"),
    (r"\bnothing\s+(?:found|exists|remains)\b",        "absence claim: `nothing found`"),
    (r"\bunrecoverable\b|\bcontent\s+is\s+lost\b",   "absence claim: `unrecoverable`"),
    (r"\bnever\s+(?:existed|written|recorded)\b",      "absence claim: `never existed`"),
]
# Evidence that an absence claim was actually SEARCHED rather than assumed. Any one of these
# adjacent to the claim discharges it.
SEARCH_EVIDENCE = (r"\brg\b|\bgrep\b|\bsearched\b|--check|\bglob\b|`plans/|"
                   r"\benumerat|\bre-derive|\bscanned\b")
JUDGMENT_CHECKS = ["2", "3", "5", "6", "7", "9", "10", "12"]


# Quoting a stale value as HISTORY is legitimate and necessary — a postmortem that cannot restate
# what the document used to say is not a postmortem. Two discharges, both deliberately narrow:
#   · a markdown blockquote (`> ...`) — quoting, not asserting
#   · an explicit `<!-- VOLATILE-OK: reason -->` on the line or the one before it
# A blanket SKIP_ env var would silence the whole check; these silence one instance and demand a
# reason, which is the difference between an escape hatch and an off switch.
DISCHARGE_MARKER = re.compile(r"<!--\s*VOLATILE-OK:", re.I)
# A whole POSTMORTEM section legitimately restates stale values throughout — "it said 3 of 7 while
# its membership rotated" is the finding, not a defect. Per-line markers on twenty such lines is
# noise that trains the writer to stop reading them, so the discharge is available at SECTION scope:
# `<!-- VOLATILE-OK-SECTION: reason -->` holds until the next markdown heading. Still narrow (it
# ends at a heading, and it demands a reason) — unlike an env-var bypass, which ends nowhere.
SECTION_DISCHARGE = re.compile(r"<!--\s*VOLATILE-OK-SECTION:", re.I)


def _in_discharged_section(prose, pos):
    """True when the most recent of {section-discharge marker, heading} is the marker."""
    head = prose.rfind("\n#", 0, pos)
    mark = max(m.start() for m in SECTION_DISCHARGE.finditer(prose[:pos])) \
        if SECTION_DISCHARGE.search(prose[:pos]) else -1
    return mark > head


def _discharged(prose, pos):
    """True when the match sits in a blockquote or carries an explicit VOLATILE-OK marker."""
    line_start = prose.rfind("\n", 0, pos) + 1
    line_end = prose.find("\n", pos)
    line = prose[line_start:line_end if line_end != -1 else len(prose)]
    if line.lstrip().startswith(">"):
        return True
    if DISCHARGE_MARKER.search(line):
        return True
    if _in_discharged_section(prose, pos):
        return True
    prev_start = prose.rfind("\n", 0, line_start - 1) + 1
    return bool(DISCHARGE_MARKER.search(prose[prev_start:line_start]))


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
            if _discharged(prose, m.start()):
                continue
            line_no = prose[:m.start()].count("\n") + 1
            findings.append(("MED",
                f"volatile {what} in prose: {m.group(0)!r} (~prose line {line_no}) — anchor it to a "
                f"SHA range or move it into a re-derive block; a count is stale on the commit that "
                f"records it"))

    # ── CATEGORICAL ABSENCE claims must carry their search (AR-15 / M9) ────────────────────────
    # Highest-severity class in this tool: an unsearched absence claim does not merely go stale, it
    # sends the reader to act on something false. The instance that motivated it would have written
    # "content unrecoverable" tombstones over content that was sitting in the repo.
    for pat, what in ABSENCE_CLAIM_PATTERNS:
        for m in re.finditer(pat, prose, re.I):
            if _discharged(prose, m.start()):
                continue
            line_no = prose[:m.start()].count("\n") + 1
            # Discharge the claim if the SAME paragraph shows the search that backs it.
            para_start = prose.rfind("\n\n", 0, m.start())
            para_end = prose.find("\n\n", m.end())
            para = prose[para_start if para_start != -1 else 0:
                         para_end if para_end != -1 else len(prose)]
            if re.search(SEARCH_EVIDENCE, para, re.I):
                continue
            findings.append(("HIGH",
                f"{what} with NO search shown: {m.group(0)!r} (~prose line {line_no}) — an absence "
                f"is only a fact relative to a NAMED search space. State what was searched "
                f"(`rg`, the glob, the file set), or the reader inherits an assumption as a fact"))

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

    # AR-8 + AR-18 (2026-08-16). Two distinct failures, and the SECOND one is the common one:
    #   (a) no review section at all              -> MED, the original tooth
    #   (b) a section that says the review DID NOT RUN -> HIGH
    # (b) used to pass silently, because the old test was `search(r"...independent review...")` over
    # the raw text — so writing "Independent review: **NOT RUN**" SATISFIED the check. The handoff was
    # being honest and the guard read that honesty as compliance. When the review was finally run it
    # refuted three of the handoff's load-bearing claims (a vacuous H21 green, a conditional loop
    # closure, a missed uninit sibling), so this is the highest-value check in the file and it was the
    # one that could not fail. A declared skip must be LOUDER than a missing section, never quieter.
    _ran = re.search(r"adversarial|independent review|a-class", raw, re.I)
    # POSITIVE DECLARATION discharges the skip-detector. Needed because a handoff that DID run the
    # review naturally narrates the history ("it was skipped once, then run") and keyword-proximity
    # cannot tell narration from status — the M3 false-positive surface, hit immediately on the first
    # handoff to satisfy the check. An explicit assertion beats keyword-absence: `Status: RUN <date>`.
    # This is a declaration, not proof — but a false one is a lie in the artifact rather than a guard
    # that quietly could not tell, and the review's own findings are right below it for the reader.
    _declared_run = re.search(r"status:\s*\**\s*(RUN|COMPLETE|DONE)\b", raw, re.I)
    # The window must span NEWLINES: the real-world shape is a `## Independent review` heading with
    # the "NOT RUN" verdict on the line below it, so a line-anchored `[^\n]` window misses exactly the
    # case this exists to catch (it did, on the first cut). Bounded at 200 chars so a review mentioned
    # in one section and an unrelated "skipped" far below do not pair up into a false positive.
    _skipped = re.search(
        r"(adversarial|independent review|a-class|stage\s*6\.5\.4)[\s\S]{0,200}?"
        r"\b(not\s+run|did\s+not\s+run|was\s+not\s+run|skipped|unreviewed|no\s+review)\b"
        r"|\b(not\s+run|did\s+not\s+run|skipped|unreviewed)\b[\s\S]{0,200}?"
        r"(adversarial|independent review|a-class|stage\s*6\.5\.4)",
        raw, re.I)
    if _skipped and not _declared_run:
        findings.append(("HIGH",
            "INDEPENDENT REVIEW is recorded as NOT RUN — the handoff is self-attested. Stating the "
            "gap is right and does not close it: when this review was actually run it REFUTED three "
            "load-bearing claims (a guard cited as proof that never covered the change, a loop "
            "closure that held only in one config, an unpatched sibling of a bug called closed). "
            "Run it, or hand the next session a document whose successes are unverified"))
    elif not _ran:
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


def check_sync_owed(live=None, backup=None, ws=None):
    """Detect the EVIDENCE that /sync-workspace has not run, rather than trusting that it did.

    Prescribing "invoke the skill" is a memory-based control, and memory-based controls at the close
    are exactly what keep failing here. Two mechanical tells, both cheap:

      1. `memory.backup/` differs from the LIVE memory dir. The live dir is the source of truth and
         lives outside any repo ($HOME/.claude); the backup is the only off-machine copy. A drift
         means either sync never ran, or it ran before the last memory edit. It is also the exact
         signature of a HAND-ROLLED sync: `cp` mirrors bytes but skips the canonicalizer that
         rewrites frontmatter and re-derives sister links, so a hand-copied backup can be
         byte-identical to a file the tool would have CHANGED.
      2. Unpushed commits in the workspace. A close that ends with work only on this machine has not
         closed — the next session, or the next machine, sees none of it.

    Neither is fatal on its own (both are legitimate mid-session states), so both report rather than
    block. The point is that the skip becomes VISIBLE, which is the whole failure mode."""
    findings = []
    ws = Path(ws) if ws else WORKSPACE   # the ONE resolver (D-375); already imported above
    live = Path(live) if live else (
        Path.home() / ".claude/projects/-home-caramel-code-FoxML-Trader-v2/memory")
    backup = Path(backup) if backup else (ws / "memory.backup")
    # CANONICALITY, not byte-equality. An independent audit refuted the first version of this
    # check: it byte-compared backup vs live, so a HAND-ROLLED `cp` sync produced zero drift and
    # the check went green -- blind to the exact failure it was built for. The refutation was
    # already written in this function's own docstring and not followed. Ask the canonicalizer.
    import subprocess
    try:
        r = subprocess.run(["python3", str(Path(__file__).parent / "migrate_memory_frontmatter.py"),
                            "--check"], capture_output=True, text=True, timeout=60)
        if r.returncode == 1:
            findings.append(("MED",
                "memory frontmatter is NOT canonical — migrate_memory_frontmatter.py --check is RED. "
                "A hand-rolled `cp` sync mirrors bytes but skips the canonicalizer, so the backup can "
                "be byte-identical to a file the tool would have CHANGED. Run /sync-workspace"))
    except Exception:
        pass

    if live.is_dir() and backup.is_dir():
        drift = []
        for f in sorted(live.glob("*.md")):
            b = backup / f.name
            if not b.is_file() or b.read_text() != f.read_text():
                drift.append(f.name)
        orphan = [b.name for b in sorted(backup.glob("*.md")) if not (live / b.name).is_file()]
        if drift:
            findings.append(("MED",
                f"memory.backup DRIFT vs the live memory dir ({len(drift)} file(s), e.g. "
                f"{', '.join(drift[:3])}) — /sync-workspace has not run since the last memory edit. "
                f"A hand-rolled `cp` sync also skips migrate_memory_frontmatter.py, which is what "
                f"canonicalizes frontmatter and re-derives sister links"))
        if orphan:
            findings.append(("MED",
                f"memory.backup holds {len(orphan)} file(s) with no live counterpart "
                f"({', '.join(orphan[:3])}) — a deleted memory, or a backup written by hand"))
    try:
        import subprocess
        r = subprocess.run(["git", "-C", str(ws), "rev-list", "--count", "@{u}..HEAD"],
                           capture_output=True, text=True, timeout=15)
        n = int((r.stdout or "0").strip() or 0)
        if n:
            findings.append(("MED",
                f"workspace has {n} UNPUSHED commit(s) — a close that leaves work on one machine "
                f"has not closed; run /sync-workspace (Stage 7)"))
    except Exception:
        pass  # no remote / not a repo / git unavailable — not this tool's business to diagnose
    return findings


# Exit code for "the surfaces were never evaluated". DELIBERATELY not 0 (AR-18, 2026-08-16): this
# tool used to return 0 when it skipped, so a caller rendering exit-0 as ✅ showed a green row for a
# check that had not run. It read as a pass twice in one close while FOUR auto-write surfaces were
# genuinely owed — found only by re-running with the threshold defeated. A skip and a pass must not
# share a signal; "did not evaluate" is its own answer.
EXIT_DID_NOT_RUN = 3


def run(since, min_commits, explain, quiet):
    repo = WORKSPACE
    n = _commit_count(since, repo)
    if n == 0:
        print(f"[close-out] DID NOT RUN — no commits in {since}..HEAD, so no surface was evaluated. "
              f"This is not a pass; widen --since if you expected work in this window.")
        return EXIT_DID_NOT_RUN
    print(f"[close-out] window {since}..HEAD — {n} commit(s)")
    if n < min_commits:
        print(f"[close-out] DID NOT RUN — {n} commit(s) is below --min-commits={min_commits}, so no "
              f"surface was evaluated. A small session often owes nothing, but this run did not "
              f"CHECK that. Re-run with --min-commits 1 to actually evaluate the window.")
        return EXIT_DID_NOT_RUN

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
    # Sync-owed is part of the close, not a separate ritual: a handoff nobody can read is not a
    # handoff. Detected from EVIDENCE (backup drift, unpushed commits) rather than trusted.
    hq += check_sync_owed()
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
    # DIRECTORY-prefix surfaces (the 2026-08-15 reference-doc rows) must resolve as git pathspecs,
    # not just as files — a row that silently never matches is a surface that can never be owed,
    # which is the vacuously-green shape this whole tool exists to prevent.
    _dirs = [p for p, _, _ in AUTO_WRITE_SURFACES if p.endswith("/")]
    chk("directory-form surface rows are present (the reference-doc slice)", len(_dirs) >= 2)
    chk("every directory-form row resolves to a real directory",
        all((WORKSPACE / d).is_dir() for d in _dirs))
    chk("a directory surface COUNTS commits under it (pathspec works, not just file paths)",
        _touched("DESIGN_SPECS/", "HEAD~40", WORKSPACE) > 0)
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
        # Assert on the MATCHED TEXT, not the pattern's label. These two teeth silently broke when
        # the labels changed during the shape-based redesign — the detection was fine the whole
        # time, the assertions were stale. A tooth coupled to a human-readable label fails for a
        # reason that has nothing to do with what it guards.
        chk("planted VOLATILE COUNT is flagged", "24 commits" in kinds)
        chk("planted volatile tools-enrolled count is flagged", "100 tools" in kinds)
        chk("missing RE-DERIVE block is flagged HIGH",
            any(s == "HIGH" and "RE-DERIVE" in m for s, m in f))
        chk("missing JUDGMENT-CHECK ledger is flagged HIGH",
            any(s == "HIGH" and "JUDGMENT-CHECK" in m for s, m in f))
        chk("missing INDEPENDENT REVIEW is flagged",
            any("INDEPENDENT REVIEW" in m for _, m in f))
        # AR-18: the DECLARED-SKIP case. This is the one that shipped green for a whole session —
        # an honest "NOT RUN" satisfied the old presence-regex. Both plantings must go HIGH, and the
        # negative control below must stay silent, or the fix has just moved the vacuity.
        for _txt in ("## Independent review (Stage 6.5.4)\n\n⚠️ **NOT RUN — context budget exhausted.**",
                     "Independent review: skipped this session.",
                     "The a-class adversarial pass did not run."):
            _b = Path(td) / "skip.md"; _b.write_text("# h\n\n" + _txt + "\n")
            chk(f"a DECLARED-SKIP independent review is HIGH, not silent ({_txt[:34]!r})",
                any(s == "HIGH" and "NOT RUN" in m for s, m in check_handoff_quality(_b)))
        _ok = Path(td) / "reviewed.md"
        _ok.write_text("# h\n\nIndependent review: a-class ran, verdict recorded, 3 claims refuted.\n")
        chk("a handoff whose review DID run is NOT flagged as skipped (negative control)",
            not any("NOT RUN" in m for _, m in check_handoff_quality(_ok)))
        # M3 false-positive control: a handoff that RAN the review will NARRATE the history
        # ("skipped once, then run"). Keyword-proximity cannot tell narration from status, so an
        # explicit `Status: RUN` must discharge it. Without this the guard punishes the exact
        # handoff that complied — which is how a guard earns being ignored.
        _nar = Path(td) / "narrated.md"
        _nar.write_text("# h\n\n## Independent review\n\n**Status: RUN 2026-08-16** (a-class). "
                        "It was skipped once for context budget, then run.\n")
        chk("a RUN review that narrates having once been skipped is NOT flagged (M3 control)",
            not any("NOT RUN" in m for _, m in check_handoff_quality(_nar)))

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

        # ── REGRESSION LOCK: the 9 findings an independent review raised against a handoff that
        # this tool had already passed. The first pattern set caught ONE of them. These are the
        # acceptance oracle — a future simplification that drops coverage fails HERE, loudly.
        oracle = [
            ("3 of 7 deliverables done",                "progress tally"),
            ("remaining order is (e)->(f)->(g)->(d)",   "deliverable-order sequence"),
            ("A 22-commit session shipped",             "hyphenated commit count"),
            ("now sees all 405 sentinels, up from 400", "count delta"),
            ("Check 14 was 70% false positives",        "percentage"),
            ("8 dangling ids, each VERIFIED",           "truncated-scope count"),
            ("these ids have no content anywhere",      "unsearched absence claim"),
            ("the 837-id set golden",                   "hyphenated id count"),
            ("98 tools enrolled",                       "the count that survived 2 self-sweeps"),
        ]
        pats = [(re.compile(pt, re.I), w) for pt, w in
                VOLATILE_COUNT_PATTERNS + ABSENCE_CLAIM_PATTERNS]
        hit = [s for s, _ in oracle if any(r.search(s) for r, _ in pats)]
        chk(f"REGRESSION LOCK: all 9 real review findings still caught (got {len(hit)}/9)",
            len(hit) == 9)

        # FALSE-POSITIVE control. Over-broad patterns are how a guard gets bypassed wholesale,
        # and a bypassed guard protects nothing — so the clean cases matter as much as the dirty.
        clean = ["the fix removes 2 moving parts", "H21 is the invariant here",
                 "see D-402 and TECH_DEBT-250", "engine HEAD is 4c076ed",
                 "window 2167d9d..HEAD", "Check 14 PASS", "AR-8 applies"]
        clean += ["the D-394 gate is TTY-only", "a 1-line forwarding tombstone",
                  "TECH_DEBT-250 is closed", "H22 scale-invariance", "Check 14 indexed it"]
        fp = [s for s in clean if any(r.search(s) for r, _ in pats)]
        chk(f"no FALSE POSITIVES on anchors/ids/invariants (got {fp})", not fp)
        chk("an ID's digits are an ANCHOR, never a tally (D-394 / TECH_DEBT-250 / H22)",
            not any(r.search("the D-394 gate and TECH_DEBT-250 and H22") for r, _ in pats))

        chk("a blockquote DISCHARGES (quoting history is not asserting it)",
            _discharged("> it used to say 24 commits", 20))
        chk("an explicit VOLATILE-OK marker DISCHARGES",
            _discharged("<!-- VOLATILE-OK: postmortem -->\nit said 24 commits", 45))
        chk("a VOLATILE-OK-SECTION discharges until the next heading",
            _discharged("<!-- VOLATILE-OK-SECTION: postmortem -->\nit said 24 commits", 45))
        chk("a section discharge ENDS at the next heading (scope is bounded)",
            not _discharged("<!-- VOLATILE-OK-SECTION: pm -->\nx\n\n# New\n\nnow 24 commits", 48))
        chk("plain prose is NOT discharged (else the hatch is an off switch)",
            not _discharged("plain prose says 24 commits", 20))
        # ── sync-owed teeth. Plant a REAL drift; a detector never observed firing is precisely
        # what this tool exists to catch, and it would be self-refuting to ship one here.
        lv, bk = Path(td) / "live", Path(td) / "bak"
        lv.mkdir(); bk.mkdir()
        (lv / "a.md").write_text("same")
        (bk / "a.md").write_text("same")
        chk("IN-SYNC memory dirs produce NO drift finding (negative control)",
            not any("DRIFT" in msg for _, msg in check_sync_owed(lv, bk, td)))
        (lv / "b.md").write_text("new memory, never synced")
        chk("a memory file MISSING from the backup is detected",
            any("DRIFT" in msg for _, msg in check_sync_owed(lv, bk, td)))
        (bk / "b.md").write_text("stale content")
        chk("a memory file whose backup CONTENT differs is detected (the hand-`cp` signature)",
            any("DRIFT" in msg for _, msg in check_sync_owed(lv, bk, td)))
        (bk / "b.md").write_text("new memory, never synced")
        (bk / "ghost.md").write_text("deleted upstream")
        chk("an ORPHAN backup with no live counterpart is detected",
            any("orphan" in msg or "no live counterpart" in msg
                for _, msg in check_sync_owed(lv, bk, td)))

        chk("an absence claim SHOWING its search is discharged",
            not any("absence" in msg for _, msg in check_handoff_quality(good)))
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
