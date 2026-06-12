#!/usr/bin/env python3
"""
check_capture_audit.py — MECHANICAL half of the /capture-audit skill, as a deterministic tool.

WHY (D-112, operator 2026-05-30): "the CI tools are unit tests for the docs; why aren't the
skills wired to them?" /capture-audit's Checks 1-10 were LLM-INTERPRETED PROSE (the agent
re-checking by hand = the exact failure mode of .E Session-4). This tool mechanizes the
genuinely-MECHANICAL, currently-tool-less checks so the skill INVOKES them instead of
prose-describing them. JUDGMENT checks (6 Stage-6 candidates / 5 handoff-currency-vs-intent /
10 currency) stay agent-driven — they can't be grepped (per feedback_independence_for_judgment_not_mechanical).

Mechanizes:
  Check 1  — MEMORY.md index sync: every memory/<f>.md has an index line in MEMORY.md (no orphans)
  Check 4  — decision-log sentinel matching: every `<!-- D/C/F: <id> -->` has a `<!-- STATUS: ... -->`
  Check 8  — skill -> CLAUDE.md suite linkage: every claude-skills/<x>/SKILL.md named in CLAUDE.md
  Check 13 — decision-log COMPLETENESS (ADVISORY, explicit-only): a new Hard-Invariant (Hnn) added to
             CLAUDE.md in the session window with NO referencing D-entry = a likely un-logged decision
             (the create->capture gap; M7 escalation of feedback_document_as_you_go). Sibling to Check 4.

Already tool-backed elsewhere (invoke those directly; NOT duplicated here):
  Check 1 frontmatter + Check 9/12 bidirectional sisters -> check_doc_metadata.py --bidirectional --memories
  Check 11 forward-promise                                -> check_forward_promise_audit.py
  plan-body symbol existence (B-Plus)                     -> check_plan_body_symbol_existence.py

CONVENTIONS (mirror check_doc_metadata.py): machine-portable resolver (env | script-loc | cwd);
exit 1 on any violation (CI-gating); minimal line-scan (no yaml dep).

USAGE
  python3 tools/check_capture_audit.py                 # default-all HARD checks (1/4/8)
  python3 tools/check_capture_audit.py --check 1|4|8|13 # one check (13 = advisory completeness)
  python3 tools/check_capture_audit.py --check 13 --since HEAD~8   # decision-completeness over a window
  python3 tools/check_capture_audit.py --selftest      # unit-test Check 13 cross-ref logic, then exit
  python3 tools/check_capture_audit.py --quiet          # only failures + summary
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def _resolve_dir(env, candidates):
    v = os.environ.get(env)
    if v and Path(v).exists():
        return Path(v)
    for c in candidates:
        if c and Path(c).exists():
            return Path(c)
    return candidates[-1] if candidates else Path.cwd()


def _resolve_workspace():
    return _resolve_dir(
        env="FOXML_WORKSPACE",
        candidates=[Path(__file__).resolve().parent.parent, Path.cwd()],
    )


def _resolve_engine():
    # engine root = tools/.. (this file lives in <engine>/tools/)
    return Path(__file__).absolute().parent.parent


def _resolve_memory_dir():
    env = os.environ.get("FOXML_MEMORY_DIR")
    if env and Path(env).exists():
        return Path(env)
    derived = Path.home() / ".claude" / "projects" / "-home-caramel-code-FoxML-Trader-v2" / "memory"
    if derived.exists():
        return derived
    return None


def _resolve_skills_dir(engine, workspace):
    # skills live in workspace/claude-skills (symlinked to <engine>/.claude/skills)
    for c in [workspace / "claude-skills", engine / ".claude" / "skills"]:
        if c.exists():
            return c
    return None


# ---------------------------------------------------------------------------
# Check 1 — MEMORY.md index sync
# ---------------------------------------------------------------------------
def check_index_sync(quiet):
    mem = _resolve_memory_dir()
    if not mem:
        print("  [Check 1] SKIP — memory dir not found (set FOXML_MEMORY_DIR)")
        return 0
    index = mem / "MEMORY.md"
    if not index.exists():
        print(f"  [Check 1] SKIP — {index} not found")
        return 0
    idx_text = index.read_text(encoding="utf-8")
    ext = mem / "MEMORY_EXTENDED.md"   # Tier-2 on-demand index (TECH_DEBT-163) — a file indexed in EITHER counts
    if ext.exists():
        idx_text += "\n" + ext.read_text(encoding="utf-8")
    orphans = []
    for f in sorted(mem.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        if not re.match(r"^(feedback_|user_|project_|reference_)", f.name):
            continue
        if f.name not in idx_text:
            orphans.append(f.name)
    if orphans:
        print(f"  [Check 1] FAIL — {len(orphans)} memory file(s) NOT indexed in MEMORY.md / MEMORY_EXTENDED.md:")
        for o in orphans:
            print(f"             orphan: {o}")
        return 1
    if not quiet:
        print("  [Check 1] PASS — memory index sync (all files indexed in MEMORY.md or MEMORY_EXTENDED.md)")
    return 0


# ---------------------------------------------------------------------------
# Check 4 — decision-log sentinel matching (D/C/F id -> STATUS)
# ---------------------------------------------------------------------------
def check_sentinels(quiet, workspace):
    # scan all decision logs in the active sprint(s); a D/C/F block must be followed by a STATUS
    dlogs = list(workspace.glob("plans/**/decision-logs/*.md"))
    if not dlogs:
        if not quiet:
            print("  [Check 4] PASS — no decision logs found (nothing to check)")
        return 0
    fails = []
    for dl in dlogs:
        lines = dl.read_text(encoding="utf-8").splitlines()
        pending_id = None
        for i, ln in enumerate(lines):
            m = re.search(r"<!--\s*D/C/F:\s*([\w.-]+)\s*-->", ln)
            if m:
                # if a previous D/C/F id is still awaiting its STATUS, it's unmatched
                if pending_id is not None:
                    fails.append((dl.name, pending_id, "no STATUS before next D/C/F marker"))
                pending_id = m.group(1)
                continue
            if pending_id is not None and re.search(r"<!--\s*STATUS:", ln):
                pending_id = None
        if pending_id is not None:
            fails.append((dl.name, pending_id, "no STATUS before end of file"))
    if fails:
        print(f"  [Check 4] FAIL — {len(fails)} decision marker(s) without a matching STATUS:")
        for fn, did, why in fails:
            print(f"             {fn}: D/C/F {did} — {why}")
        return 1
    if not quiet:
        print(f"  [Check 4] PASS — decision sentinels matched across {len(dlogs)} decision log(s)")
    return 0


# ---------------------------------------------------------------------------
# Check 8 — skill -> CLAUDE.md suite linkage
# ---------------------------------------------------------------------------
def check_skill_linkage(quiet, engine, workspace):
    skills_dir = _resolve_skills_dir(engine, workspace)
    if not skills_dir:
        print("  [Check 8] SKIP — skills dir not found")
        return 0
    claude_md = engine / "CLAUDE.md"
    if not claude_md.exists():
        print(f"  [Check 8] SKIP — {claude_md} not found")
        return 0
    cmd_text = claude_md.read_text(encoding="utf-8")
    missing = []
    for sk in sorted(skills_dir.iterdir()):
        if not (sk / "SKILL.md").exists():
            continue
        name = sk.name
        # accept "/name" or "`/name`" or bare name token in the skill-suite tables
        if f"/{name}" not in cmd_text and f"`{name}`" not in cmd_text:
            missing.append(name)
    if missing:
        print(f"  [Check 8] FAIL — {len(missing)} skill(s) not referenced in CLAUDE.md:")
        for m in missing:
            print(f"             unlinked: /{m}")
        return 1
    if not quiet:
        print(f"  [Check 8] PASS — all skills linked in CLAUDE.md ({skills_dir})")
    return 0


# ---------------------------------------------------------------------------
# Check 13 — decision-log COMPLETENESS (ADVISORY; sibling to Check 4 sentinel MATCHING)
#
# WHY (operator 2026-06-11, the .E.0.10 close): Check 4 proves a D/C/F marker is well-FORMED (has a
# STATUS). It does NOT prove the log is COMPLETE — that every decision actually MADE this session got
# an entry. The create->capture gap (feedback_document_as_you_go): a decision lands in its natural
# home (a new Hard-Invariant row in CLAUDE.md, a new DESIGN_SPEC) but never gets a D-N, so the
# planning trail silently misses it. H22 this session sat un-logged until operator pushback forced a
# retrofit (D-193). Memory codified the discipline and it STILL leaked -> M7 escalation from
# "remember to" to a firing gate.
#
# Heuristic (ADVISORY — never hard-fails; surfaces for human triage): a decision-bearing artifact
# ADDED in the window with NO referencing D-entry is a likely un-logged decision. The git-robust,
# highest-signal detector is a new Hard-Invariant `| Hnn |` row in CLAUDE.md (an invariant is ALWAYS
# a decision); new DESIGN_SPECS are reported as an informational note. Window via --since (default
# HEAD~8; a session boundary is fuzzy — hence ADVISORY + explicit-only, never a hard gate).
# ---------------------------------------------------------------------------
def _git_lines(repo, git_args):
    try:
        out = subprocess.run(["git", "-C", str(repo)] + git_args,
                             capture_output=True, text=True, timeout=20)
        return out.stdout.splitlines() if out.returncode == 0 else None
    except Exception:
        return None


def _new_invariants(workspace, since_ref):
    """Hnn identifiers added to CLAUDE.md in the window (added '| **Hnn** |' table rows)."""
    lines = _git_lines(workspace, ["diff", f"{since_ref}..HEAD", "--", "CLAUDE.md"])
    if lines is None:
        return None  # git unavailable / bad ref -> caller SKIPs
    out = []
    for ln in lines:
        if ln.startswith("+++") or not ln.startswith("+"):
            continue
        m = re.match(r"\+\s*\|\s*\*{0,2}(H\d+)\*{0,2}\s*\|", ln)
        if m:
            out.append(m.group(1))
    return sorted(set(out))


def _new_specs(workspace, since_ref):
    """DESIGN_SPECS/*.md files ADDED in the window (stems)."""
    lines = _git_lines(workspace, ["diff", "--diff-filter=A", "--name-only",
                                   f"{since_ref}..HEAD", "--", "DESIGN_SPECS/"])
    if lines is None:
        return []
    return sorted({Path(p).stem for p in lines if p.endswith(".md")})


def _unreferenced(ids, ref_text):
    """ids with no word-boundary mention in ref_text (the core cross-ref; unit-tested via --selftest)."""
    return [i for i in ids if not re.search(rf"\b{re.escape(i)}\b", ref_text)]


def check_decision_completeness(quiet, workspace, since_ref):
    invs = _new_invariants(workspace, since_ref)
    if invs is None:
        print(f"  [Check 13] SKIP — git unavailable or bad --since ref ({since_ref})")
        return 0
    dlogs = list(workspace.glob("plans/**/decision-logs/*.md"))
    ref_text = "\n".join(dl.read_text(encoding="utf-8") for dl in dlogs)
    specs = _new_specs(workspace, since_ref)
    missing_inv = _unreferenced(invs, ref_text)
    missing_spec = _unreferenced(specs, ref_text)
    if missing_inv:
        print(f"  [Check 13] FLAG — {len(missing_inv)} new Hard-Invariant(s) since {since_ref} with NO "
              f"referencing D-entry (likely un-logged decision — add a D-N, or confirm intentional):")
        for h in missing_inv:
            print(f"             {h}: added to CLAUDE.md, not referenced in any decision log")
        if missing_spec:
            print(f"             (also new spec(s) with no D-entry: {', '.join(missing_spec)})")
        return 1
    if not quiet:
        print(f"  [Check 13] PASS — decision-log completeness "
              f"({len(invs)} new invariant(s), {len(specs)} new spec(s) in window; all referenced)")
        if missing_spec:
            print(f"             note (informational): new spec(s) not yet in a D-entry: {', '.join(missing_spec)}")
    return 0


def _selftest():
    ref_with = "<!-- D/C/F: D-193 --> H22 scale-invariance / shard-independence invariant"
    ref_without = "<!-- D/C/F: D-190 --> Money_FillGross single-source"
    ok = (_unreferenced(["H22"], ref_with) == []
          and _unreferenced(["H22"], ref_without) == ["H22"]
          and _unreferenced(["H22", "H21"], ref_with) == ["H21"])
    print("  [selftest] PASS — cross-ref clears referenced ids + flags unreferenced ones"
          if ok else "  [selftest] FAIL — cross-ref logic regression")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Mechanical half of /capture-audit (Checks 1/4/8).")
    ap.add_argument("--check", type=int, choices=[1, 4, 8, 13], help="run only one check")
    ap.add_argument("--quiet", action="store_true", help="only failures + summary")
    ap.add_argument("--since", default="HEAD~8",
                    help="session window for Check 13 decision-completeness (default HEAD~8)")
    ap.add_argument("--selftest", action="store_true",
                    help="unit-test Check 13 cross-ref logic, then exit")
    args = ap.parse_args()

    if args.selftest:
        print("=== check_capture_audit.py — Check 13 selftest ===")
        sys.exit(_selftest())

    engine = _resolve_engine()
    workspace = _resolve_workspace()

    print("=== check_capture_audit.py — mechanical capture-audit checks ===")
    rc = 0
    if args.check in (None, 1):
        rc |= check_index_sync(args.quiet)
    if args.check in (None, 4):
        rc |= check_sentinels(args.quiet, workspace)
    if args.check in (None, 8):
        rc |= check_skill_linkage(args.quiet, engine, workspace)
    # Check 13 is ADVISORY + EXPLICIT-ONLY — deliberately NOT in the default-all set so the
    # aggregator's HARD `--quiet` run (Checks 1/4/8) never trips on this heuristic. Via --check 13.
    if args.check == 13:
        rc |= check_decision_completeness(args.quiet, workspace, args.since)

    if rc:
        print("=== capture-audit MECHANICAL checks FAILED ===")
        sys.exit(1)
    print("=== capture-audit MECHANICAL checks PASS ===")
    sys.exit(0)


if __name__ == "__main__":
    main()
