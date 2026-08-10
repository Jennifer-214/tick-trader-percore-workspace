#!/usr/bin/env python3
"""
check_tech_debt.py — automate tech-debt SURFACING so managing it needs ~zero standing thought.

THE FRICTION THIS KILLS
-----------------------
The only tech-debt enforcement was `/readiness` Check 25 — a MANUAL scan: "read the OPEN entries
(80+, 3000+ lines), match each entry's surface against your files-touched by hand, decide." Miss a
match and the debt stays hidden — the exact failure Check 25 exists to prevent. This tool mechanizes
the SURFACING: given the files a commit/ship touches, it hands you the overlapping OPEN entries. You
only DECIDE — the finding is automatic.

Wired into the pre-commit hook (`--staged`, ADVISORY/non-blocking), every commit that touches a
tracked debt surface auto-prints "you're in TECH_DEBT-N's surface — subsume / adjacent / defer?"
(per feedback_opportunistic_tech_debt_closure). You stop scanning; the system surfaces.

Closing stays HUMAN (judgment — NEVER auto-close debt; that hides unresolved work). This automates
find + flag-stale + the close-MOVE, not the decision.

MODES
  --staged            match git staged files (the pre-commit ADVISORY; non-blocking, exit 0 always)
  --surface F [F...]  match an explicit file set (a ship's files-touched)
  --diff <ref>        match files changed since <ref> (e.g. the ship's pre-tag)
  --stale [MONTHS]    OPEN entries opened > MONTHS ago (default 6) → flag for re-cost/refresh
                      (wall-clock — the superseded-in-spirit sister of --contract-stale, kept
                      for operator use; D-408 forbids KEYING enforcement on it)
  --contract-stale    (g)-4 / D-408: CONTRACT-violation-keyed staleness, never wall-clock —
                      (i) FIRED-TRIGGER: `trigger:` names a SHIPPED tag while status hasn't
                          moved (WARN); a trigger token absent from git tags AND Version.hpp
                          → INFO (unresolvable — e.g. a ship that was never cut);
                      (ii) CHURNING-STATIC: a flow-through file holding transitional-status
                          entries with no commit across the last ~3 ship closes (WARN);
                      (iii) EMPTY-TIER: a flow-through file with zero churn since its
                          creation era (INFO).
                      ADVISORY-first (exit 1 on WARN so the sweep row shows ⚠; never blocks).
  --contract-stale-selftest   D-137 teeth: planted fixtures prove each detector fires
  --close N           move TECH_DEBT-N from open.md to closed.md (stamps `closed:`), verify the move
  --dry-run           with --close: print what would move, write nothing
  (default mode: --staged)

Advisory by design: --staged/--surface/--diff ALWAYS exit 0 (inform, never block a commit). --stale
exits 1 only under --strict. Machine-portable: repo root from $FOXML_REPO_ROOT or derived; the
tech-debt dir is resolved by following the DOCS/TECH_DEBT.md symlink into the workspace.
"""
import os, re, sys, subprocess, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from foxroots import ENGINE as _FOXROOTS_ENGINE   # noqa: E402  (the ONE repo-root resolver — D-375)
# The ONE D-394 confirmation contract, shared with bless(). Imported HARD, never wrapped in a
# try/except fallback: a soft import would silently restore write-by-default the moment it broke,
# which is precisely the posture TECH_DEBT-255 exists to prevent. If this import fails, --close
# must fail too.
from bless import confirm_mutation as _confirm   # noqa: E402
# FIXED 2026-07-20 (import-from-core lint widened to the os.path spelling): a hand-rolled
# walk-up from __file__ resolves to the WORKSPACE through the `tools/` DIRECTORY SYMLINK.
# This one happened to still work because it only reads workspace-side files, but it is the
# same latent shape that broke three sibling tools outright — so it migrates rather than
# getting grandfathered (the baseline is meant to SHRINK).
REPO_ROOT = os.environ.get("FOXML_REPO_ROOT") or str(_FOXROOTS_ENGINE)


def _tech_debt_dir():
    """Resolve the tech-debt sub-file dir — it lives in the workspace; follow the DOCS/TECH_DEBT.md symlink."""
    idx = os.path.join(REPO_ROOT, "DOCS", "TECH_DEBT.md")
    if os.path.exists(idx):
        d = os.path.join(os.path.dirname(os.path.realpath(idx)), "tech-debt")
        if os.path.isdir(d):
            return d
    for cand in (os.path.join(REPO_ROOT, "DOCS", "tech-debt"), os.environ.get("FOXML_TECH_DEBT_DIR", "")):
        if cand and os.path.isdir(cand):
            return cand
    sys.exit("[tech-debt] dir not found — resolve DOCS/TECH_DEBT.md symlink or set FOXML_TECH_DEBT_DIR")


def _entries(path):
    """Parse '### TECH_DEBT-NNN — title' blocks → {id, title, tags, opened, status, body}."""
    with open(path) as f:
        text = f.read()
    parts = re.split(r'(?m)^### (TECH_DEBT-\d+)\b', text)  # [pre, id, body, id, body, ...]
    out = []
    for i in range(1, len(parts), 2):
        tid, body = parts[i], (parts[i + 1] if i + 1 < len(parts) else "")
        first = body.splitlines()[0] if body.strip() else ""
        title = first.lstrip(" —-").strip()
        tags_m = re.search(r'surface_tags:\s*\[([^\]]*)\]', body)
        tags = [t.strip() for t in tags_m.group(1).split(',') if t.strip()] if tags_m else []
        opened_m = re.search(r'opened:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})', body)
        # (?i) + \** — the ledger spells this THREE ways (`status:` / `**status:**` /
        # capital `**Status:**`); a lowercase-only match silently read capital-form entries
        # as status-less, reproducing the c-class undercount (2026-08-09).
        status_m = re.search(r'(?i)status:\**\s*([^\n]+)', body)
        out.append({"id": tid, "title": title, "tags": tags,
                    "opened": opened_m.group(1) if opened_m else "",
                    "status": status_m.group(1).strip() if status_m else "", "body": body})
    return out


_PATH_RE = re.compile(r'[\w./-]+\.(?:hpp|cpp|h|c|sh|py|md|txt)\b')


def _basenames(files):
    return {os.path.basename(f.strip()) for f in files if f.strip()}


def _cited_basenames(body):
    return {os.path.basename(t) for t in _PATH_RE.findall(body)}


def _git(args):
    r = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.strip()]


def surface(files):
    """ADVISORY: print OPEN entries whose body cites a file you touched. Always exit 0."""
    touched = _basenames(files)
    if not touched:
        return 0
    hits = []
    for e in _entries(os.path.join(_tech_debt_dir(), "open.md")):
        ov = touched & _cited_basenames(e["body"])
        if ov:
            hits.append((e, sorted(ov)))
    if not hits:
        return 0
    print(f"[tech-debt] {len(hits)} OPEN item(s) overlap your touched files — classify each "
          f"(subsume → close now / adjacent → cross-link + leave tracked / defer → confirm trigger;\n"
          f"            per feedback_opportunistic_tech_debt_closure + /readiness Check 25):")
    for e, ov in hits:
        print(f"  • {e['id']} — {e['title']}")
        print(f"      matched on: {', '.join(ov)}")
    return 0  # advisory — NEVER blocks a commit/ship


def stale(months, strict):
    cutoff = datetime.date.today() - datetime.timedelta(days=int(months) * 30)
    flagged = []
    for e in _entries(os.path.join(_tech_debt_dir(), "open.md")):
        if not e["opened"]:
            continue
        try:
            opened = datetime.date.fromisoformat(e["opened"])
        except ValueError:
            continue
        if opened < cutoff:
            flagged.append((e, (datetime.date.today() - opened).days))
    if not flagged:
        print(f"[tech-debt] no OPEN entries older than {months} months without refresh.")
        return 0
    print(f"[tech-debt] {len(flagged)} OPEN entries opened > {months} months ago — refresh cost/trigger or close:")
    for e, age in sorted(flagged, key=lambda x: -x[1]):
        print(f"  • {e['id']} ({age//30}mo) — {e['title']}")
    return 1 if strict else 0


def _status_class(e):
    """Normalized head token of the status field ('open' / 'closed' / 'in-progress' / …) —
    tolerant of the bold-row form where the capture carries the rest of the row."""
    return e["status"].split("·")[0].replace("*", "").strip().lower()


_SHIP_TOKEN_RE = re.compile(r'\b(?:v5\.\d+(?:\.[\w-]+)*|sub-ship-[.\w-]+)\b|\.[A-F]\.\d+(?:\.\d+)*(?:\.[A-Z])?\b')
_TRANSITIONAL_RE = re.compile(r'in.?progress|in.?flight|partial|transitional', re.I)


def _wgit(args, cwd):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.strip()]


def contract_stale(strict, d=None, tags_text=None, vh_text=None, ship_window_oldest=None):
    """(g)-4 / D-408 — contract-violation-keyed staleness. Injection params exist for the
    D-137 teeth (fully synthetic; live-value anchoring is the dead-tooth class)."""
    d = d or _tech_debt_dir()
    if tags_text is None:
        tags_text = "\n".join(_git(["tag", "--list"]))
    if vh_text is None:
        try:
            with open(os.path.join(REPO_ROOT, "Version.hpp")) as f:
                vh_text = f.read()
        except OSError:
            vh_text = ""
    if ship_window_oldest is None:
        dates = _git(["for-each-ref", "--sort=-creatordate",
                      "--format=%(creatordate:short)", "refs/tags"])[:3]
        ship_window_oldest = dates[-1] if len(dates) == 3 else ""
    warns, infos = [], []
    for fname in ("open.md", "in-flight.md"):
        path = os.path.join(d, fname)
        if not os.path.exists(path):
            continue
        transitional = []
        for e in _entries(path):
            sc = _status_class(e)
            if _TRANSITIONAL_RE.search(sc or ""):
                transitional.append(e["id"])
            if sc in ("closed", "resolved", "done"):
                continue
            trig_m = re.search(r'(?im)^[-\s]*\**trigger:\**\s*([^\n]+)', e["body"])
            if not trig_m:
                continue
            for tok in {t for t in _SHIP_TOKEN_RE.findall(trig_m.group(1)) if t}:
                # SHIPPED = git-tag membership ONLY, boundary-guarded: the token must appear in a
                # tag NOT followed by a further version component — else the `.E.1` UMBRELLA
                # false-fires against the `E.1.1` LEAF tag, and changelog PROSE naming a future
                # ship ("deferred to v5.16") would read as shipped. Version.hpp is only the
                # ABSENCE test (a token in neither space = unresolvable), per the decided design.
                tagged = re.search(re.escape(tok) + r"(?!\.?\d)", tags_text) is not None
                if tagged:
                    # ERA-AMBIGUITY discriminator (partial, declared): a SHORT relative token
                    # (`.E.1`) can terminally match an OLDER generation's tag (v5.15.5.E.1)
                    # while the CURRENT era's arc of the same name is still pending. Mechanical
                    # tell: a LONGER continuation of the token still named in Version.hpp
                    # (`.E.1.2` …) ⇒ the era is ambiguous → INFO for human resolution, never a
                    # standing false WARN.
                    if re.search(re.escape(tok) + r"(\.?\d|\.[A-Z]\b)", vh_text):
                        infos.append((e["id"], fname,
                                      f"ERA-AMBIGUOUS trigger token '{tok}' — terminally matches an "
                                      f"older tag, but a longer pending continuation exists in "
                                      f"Version.hpp; resolve the intended era by hand"))
                    else:
                        warns.append((e["id"], fname,
                                      f"FIRED-TRIGGER — trigger names SHIPPED '{tok}' but status is "
                                      f"'{(sc or '?')[:60]}' (the contract fired; disposition owed)"))
                elif tok not in vh_text:
                    infos.append((e["id"], fname,
                                  f"unresolvable trigger token '{tok}' — absent from git tags AND "
                                  f"Version.hpp (a ship that was never cut; re-home the trigger)"))
                # else: resolvable-but-PENDING (named in Version.hpp planning, not yet tagged) — silent
        # (ii)/(iii) — file-granularity, flow-through tier only (open.md churns constantly by design)
        if fname == "in-flight.md":
            commits = _wgit(["log", "--format=%cs", "--", os.path.basename(path)], cwd=d)
            last = commits[0] if commits else ""
            if transitional and last and ship_window_oldest and last < ship_window_oldest:
                warns.append(("(file)", fname,
                              f"CHURNING-STATIC — holds transitional entries {transitional} with no "
                              f"commit since {last}, across the last 3 ship closes (≥ {ship_window_oldest})"))
            if len(commits) <= 2 and last and ship_window_oldest and last < ship_window_oldest:
                infos.append(("(file)", fname,
                              f"EMPTY-TIER — flow-through file: {len(commits)} commit(s) ever, "
                              f"none since {last} (zero churn since the creation era)"))
    print(f"[contract-stale] D-408 contract-keyed staleness (NEVER wall-clock): "
          f"{len(warns)} WARN · {len(infos)} INFO")
    for tid, fn, why in warns:
        print(f"  ⚠ WARN {tid} ({fn}): {why}")
    for tid, fn, why in infos:
        print(f"  · INFO {tid} ({fn}): {why}")
    if not warns and not infos:
        print("  clean — no fired-trigger / churning-static / empty-tier contract violations.")
    return 1 if warns else 0


def contract_stale_selftest():
    """D-137 teeth — fully SYNTHETIC (injected tags/dates; live-value anchoring = the dead-tooth class)."""
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, "open.md"), "w") as f:
            f.write("### TECH_DEBT-901 — fired trigger case\n"
                    "- **id:** TECH_DEBT-901 · **Status:** open\n"
                    "- **Trigger:** lands at sub-ship-.T.9 (shipped)\n\n"
                    "### TECH_DEBT-902 — unresolvable trigger case\n"
                    "- **id:** TECH_DEBT-902 · **status:** open\n"
                    "- **Trigger:** lands at sub-ship-.Z.99 (never cut)\n\n"
                    "### TECH_DEBT-903 — clean (no ship token)\n"
                    "- **id:** TECH_DEBT-903 · **status:** open\n"
                    "- **Trigger:** next perf pass surfaces it\n")
        with open(os.path.join(td, "in-flight.md"), "w") as f:
            f.write("### TECH_DEBT-904 — parked transitional\n"
                    "- **id:** TECH_DEBT-904 · **Status:** in-progress\n")
        # not a git repo → (ii)/(iii) file legs see no commits and stay silent; the entry legs are
        # the teeth here. Capital **Status:** used on 901/904 ON PURPOSE (the c-class undercount pin).
        rc = contract_stale(False, d=td, tags_text="sub-ship-.T.9\n", vh_text="",
                            ship_window_oldest="2026-01-01")
        t1 = rc == 1
        ok &= t1
        print(f"  {'✅' if t1 else '❌'} fired-trigger (capital **Status:** parsed) → WARN, rc=1")
        # BOUNDARY pin: the umbrella token must NOT fire against a LEAF tag (`.T.9` vs `x.T.9.1`),
        # and a token named only in Version.hpp PROSE is pending, never fired.
        rc2 = contract_stale(False, d=td, tags_text="tag-x.T.9.1\n", vh_text="planned: sub-ship-.T.9 someday",
                             ship_window_oldest="2026-01-01")
        t2 = rc2 == 0
        ok &= t2
        print(f"  {'✅' if t2 else '❌'} umbrella-vs-leaf boundary + prose-mention → pending (no WARN), rc=0")
        # ERA-AMBIGUITY pin: token matches an OLD tag terminally BUT a longer continuation is
        # still pending in Version.hpp → demoted to INFO (never a standing false WARN).
        rc3 = contract_stale(False, d=td, tags_text="old-era.T.9\n",
                             vh_text="pending leaves: sub-ship-.T.9.2 …",
                             ship_window_oldest="2026-01-01")
        t3 = rc3 == 0
        ok &= t3
        print(f"  {'✅' if t3 else '❌'} era-ambiguous (old tag + pending continuation) → INFO, rc=0")
        # LETTER-form continuation pin (`.T.9.A` pending in Version.hpp) — same demotion
        rc4 = contract_stale(False, d=td, tags_text="old-era.T.9\n",
                             vh_text="deferred to sub-ship-.T.9.A later",
                             ship_window_oldest="2026-01-01")
        t4 = rc4 == 0
        ok &= t4
        print(f"  {'✅' if t4 else '❌'} era-ambiguous (letter-form continuation .T.9.A) → INFO, rc=0")
    return ok


def close(n, dry_run):
    d = _tech_debt_dir()
    open_p, closed_p = os.path.join(d, "open.md"), os.path.join(d, "closed.md")
    with open(open_p) as f:
        text = f.read()
    # Zero-pad tolerant: 95 of 258 defining headings are padded, so `--close 16` errored out
    # while `--close 016` silently WROTE — the safe spelling failing and the dangerous one
    # succeeding is the worst possible split. One id, one meaning, either spelling.
    d_id = int(str(n).lstrip('0') or '0')
    m = re.search(r'(?m)^### TECH_DEBT-0*' + str(d_id) + r'\b', text)
    if not m:
        sys.exit(f"[tech-debt] TECH_DEBT-{n} not found in open.md (already closed? wrong id?)")
    nxt = re.search(r'(?m)^### TECH_DEBT-\d+\b', text[m.end():])
    end = m.end() + nxt.start() if nxt else len(text)
    block = text[m.start():end].rstrip() + "\n"
    today = datetime.date.today().isoformat()
    # The ledger spells status TWO ways: a bare `status: open` line, and inline in the bold id
    # row (`· **status:** open ·`). Stamping only the bare form moved bold entries to closed.md
    # still reading `status: open` — a closed entry that every status query still counts as open.
    stamped, hits = re.subn(r'(?m)^(status:\s*)\S+', r'\1closed', block, count=1)
    if not hits:
        stamped, hits = re.subn(r'(\*\*status:\*\*\s*)\S+', r'\1closed', block, count=1)
    if not hits:
        sys.exit(f"[tech-debt] TECH_DEBT-{n}: no status field found in either spelling — "
                 f"refusing to move an entry whose status cannot be stamped.")
    stamped = stamped.rstrip() + f"\n- **Closed:** {today} (moved open → closed via check_tech_debt.py --close)\n"
    if dry_run:
        print(f"[tech-debt] DRY-RUN would move TECH_DEBT-{n} (open → closed.md), stamping closed:{today}:\n")
        print(block)
        return 0

    # D-394 confirmation — this MUTATES two ledgers and there is no undo but git. It previously
    # wrote by default with no diff and no prompt: the same posture TECH_DEBT-255 was opened
    # against for check_identifier_retirement --update, which was migrated here while THIS
    # sibling writer went unenumerated. Shown-then-confirmed, via the one shared contract.
    print(f"[tech-debt] TECH_DEBT-{d_id} would move open.md → closed.md, stamped closed:{today}.")
    print(f"  the entry being moved ({len(block.splitlines())} lines):\n")
    for ln in block.splitlines()[:12]:
        print(f"    {ln}")
    if len(block.splitlines()) > 12:
        print(f"    … {len(block.splitlines()) - 12} more lines")
    print("")
    rc = _confirm(f"close-{d_id}", "move this entry to closed.md", noun="ledger")
    if rc != 0:
        return rc

    with open(open_p, "w") as f:
        f.write(text[:m.start()] + text[end:])
    with open(closed_p, "a") as f:
        f.write("\n" + stamped)
    # verify
    moved_out = re.search(r'(?m)^### TECH_DEBT-' + re.escape(str(n)) + r'\b', open(open_p).read()) is None
    moved_in = re.search(r'(?m)^### TECH_DEBT-' + re.escape(str(n)) + r'\b', open(closed_p).read()) is not None
    if moved_out and moved_in:
        print(f"[tech-debt] TECH_DEBT-{n} moved open → closed.md (closed:{today}). Verify the closure is real before committing.")
        return 0
    sys.exit(f"[tech-debt] move of TECH_DEBT-{n} FAILED verification (out={moved_out} in={moved_in}) — inspect manually.")


def main(argv):
    strict = "--strict" in argv
    dry = "--dry-run" in argv
    if "--surface" in argv:
        i = argv.index("--surface")
        return surface([a for a in argv[i + 1:] if not a.startswith("-")])
    if "--diff" in argv:
        ref = argv[argv.index("--diff") + 1]
        return surface(_git(["diff", "--name-only", ref]))
    if "--contract-stale-selftest" in argv:
        print("check_tech_debt --contract-stale-selftest (D-408 detectors; non-vacuity):")
        return 0 if contract_stale_selftest() else 2
    if "--contract-stale" in argv:
        return contract_stale(strict)
    if "--stale" in argv:
        i = argv.index("--stale")
        months = argv[i + 1] if i + 1 < len(argv) and argv[i + 1].isdigit() else "6"
        return stale(months, strict)
    if "--close" in argv:
        return close(argv[argv.index("--close") + 1], dry)
    # default: --staged
    return surface(_git(["diff", "--cached", "--name-only"]))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
