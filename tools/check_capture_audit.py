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
# The accepted sentinel OPENERS come from the citable-id namespace registry (tools/lib/
# citable_id_namespaces.json), so Check 4 and the Check-14 resolver cannot drift apart.
def _dcf_regex():
    try:
        import json
        reg = json.loads((Path(__file__).absolute().parent / "lib" /
                          "citable_id_namespaces.json").read_text())
        opens = reg["namespaces"]["DECISION"].get("sentinel_open_any") or ["<!-- D/C/F:"]
    except Exception:
        opens = ["<!-- D/C/F:", "<!-- D:"]        # registry unreadable: cover both, never fewer
    alt = "|".join(re.escape(o.replace("<!--", "").strip()) for o in opens)
    return re.compile(r"<!--\s*(?:" + alt + r")\s*([\w.-]+)\s*-->")


_DCF_RE = _dcf_regex()
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
            # REWIRED 2026-07-20 to the shared defining-form spec. This line used to hardcode
            # only `<!-- D/C/F:` and therefore skipped the 19 sentinels using the shorter
            # `<!-- D:` form — D-372..D-381 among them, never once checked for a paired STATUS.
            # The registry knows both forms; there is now ONE parser for this defining form.
            m = _DCF_RE.search(ln)
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



# ============================================================================
# Check 14 — CITABLE-ID INTEGRITY (TECH_DEBT-249 / D-389 / D-399)
# ============================================================================
# FOLDED here rather than shipped standalone, and the argument is a DELETION: Check 4 below
# carried a SECOND parser over the same `<!-- D/C/F: … -->` defining form this resolver reads —
# and it hardcoded only the long sentinel form, silently skipping 19 sentinels including
# D-372..D-381, this ship's own origin decisions. Folding kills the duplicate parser and closes
# that gap as a side effect (feedback_structural_fix_over_belt_and_suspenders: the test is
# add-vs-remove moving parts).
#
# Scans the FULL corpus every run. A diff-scoped design was built and measured (~150ms vs ~14s)
# and REJECTED (D-399): the baseline already gives green-on-new, so diff-scoping bought only
# speed while making a TOTAL oracle PARTIAL — complete solely if a four-case blast-radius
# analysis is exhaustive, which is reasoning rather than a check. 14s once per commit, accepted.
from citable_ids import (defining_index, citations_in, sequence_gaps,   # noqa: E402
                         active_sites, _read, WORKSPACE)
CITABLE_BASELINE = Path(__file__).absolute().parent / "lib" / "citable_ids_baseline.txt"
CITABLE_GOLDEN   = Path(__file__).absolute().parent / "goldens" / "citable-ids.txt"

# Docs whose PROSE is scanned for citations. The predecessor resolver only looked inside CODE
# tag-blocks, which is why 8 dangling TECH_DEBT ids lived in workspace prose untouched for months.
CITATION_ROOTS = [
    WORKSPACE / "DOCS",
    WORKSPACE / "DESIGN_SPECS",
    WORKSPACE / "plans",
]

# Namespaces whose citations we VERIFY. DECISION is excluded on purpose: D-numbers restart per
# log, so a bare `D-7` cannot be resolved without knowing which log the citing doc means, and
# guessing would manufacture false positives at scale. Cross-log D-collisions are still REPORTED
# by class 2 (they are definition-side, which is unambiguous).
# Derived from the registry's `citations_verifiable` flag — DATA, not a hardcoded list, so the
# rationale lives beside the namespace it governs. Only DISTINCTIVELY-PREFIXED ids get their
# citations resolved; short letter+digit tokens collide with test ids / finding ids / work-item
# ids / forward-references, which AR-14's false-positive surface says must NOT be mechanized.
# DEFINITION-side checks (double-definition, gaps, reservations) run for EVERY namespace — those
# read the SSoT directly and carry no ambiguity.
def _verified_namespaces():
    try:
        import json
        reg = json.loads((Path(__file__).absolute().parent / "lib" /
                          "citable_id_namespaces.json").read_text())["namespaces"]
        return [ns for ns, s in reg.items() if s.get("citations_verifiable") == "true"]
    except Exception:
        return ["TECH_DEBT", "PARITY", "ANTIPATTERN"]      # the distinctive-prefix set


VERIFIED_NS = _verified_namespaces()

TOMBSTONE_RE = re.compile(r"RESERVED|TOMBSTONE|RETIRED|DEPRECATED|withdrawn|WITHDRAWN|superseded|SUPERSEDED|MOOT|renumber", re.I)


def _iter_docs():
    for root in CITATION_ROOTS:
        if root.is_dir():
            for p in sorted(root.rglob("*.md")):
                yield p


def _citable_findings(idx):
    findings = []   # (cls, severity, where, msg)

    # Read the corpus ONCE. The first cut re-read every doc inside the per-namespace gap loop —
    # O(namespaces x corpus), 17s for a check that should be ~2s. A guard slow enough to be
    # unwelcome in the gate that should host it ends up unwired, which is how a capability becomes
    # advertised-but-never-exercised. Perf here is a correctness-of-placement concern.
    docs = [(p, _read(p)) for p in _iter_docs()]
    corpus_lines = [ln for _, txt in docs for ln in txt.splitlines()]

    # ── 1. CITED-BUT-UNDEFINED (LIVE surfaces only) ──────────────────────────────────────────
    # A citation inside a FROZEN RECORD (postmortem / plan_check / superseded handoff / archived)
    # is not a claim about the present — it is a truthful artifact of what was true when written.
    # Flagging it would rewrite history to satisfy a linter, which D-390 explicitly rejected:
    # "the guard's job is to stop the corpus getting WORSE, not to rewrite history."
    try:
        import json as _json
        _frozen = tuple(_json.loads((Path(__file__).absolute().parent / "lib" /
                        "citable_id_namespaces.json").read_text()).get("frozen_record_paths", []))
    except Exception:
        _frozen = ("/postmortems/", "/plan_checks/", "/handoffs/", "/archived/")
    for p, _txt in docs:
        if any(seg in str(p) for seg in _frozen):
            continue
        cites = citations_in(_txt)
        for ns in VERIFIED_NS:
            known = idx.get(ns, {})
            if not known:
                continue                      # a namespace whose SSoT failed to load: SKIP, never
                                              # flag every citation as dangling (graceful, mirrors
                                              # the predecessor resolver's posture)
            for rid, lines in cites.get(ns, {}).items():
                if rid not in known:
                    findings.append(("cited-but-undefined", "HIGH",
                                     f"{p.relative_to(WORKSPACE)}:{lines[0]}",
                                     f"{ns} `{rid}` is CITED but has no defining row"))

    # ── 2. DEFINED-TWICE ──────────────────────────────────────────────────────────────────────
    for ns, entries in sorted(idx.items()):
        for rid, all_sites in sorted(entries.items(), key=lambda kv: str(kv[0])):
            # A definition in a SUPERSEDED doc is not a competing meaning — it is the previous
            # home of a meaning that moved. Drop those, but only while a live site survives.
            sites = active_sites(ns, all_sites)
            if len(sites) > 1:
                where = " | ".join(f"{Path(s).name}:{l}" for s, l in sites)
                findings.append(("defined-twice", "HIGH", where,
                                 f"{ns} `{rid}` defined at {len(sites)} sites — "
                                 f"one id must mean exactly one thing (H21 on the doc plane)"))

    # ── 3. SEQUENCE-GAP without a tombstone ───────────────────────────────────────────────────
    # A gap is a CANDIDATE, not a defect: retiring an id with a tombstone is the H21-correct
    # outcome. Only an UNEXPLAINED hole is reported.
    for ns in ("TECH_DEBT", "CLASS", "PARITY", "INVARIANT", "META", "TOOLCHAIN", "BLINDSPOT"):
        gaps = sequence_gaps(idx, ns)
        if not gaps:
            continue
        for n in gaps:
            pat = re.compile(rf"\b{ns}[- ]0*{n}\b", re.I) if ns != "CLASS" \
                  else re.compile(rf"\bClass 0*{n}\b", re.I)
            ctx = [ln for ln in corpus_lines if pat.search(ln)]
            if not any(TOMBSTONE_RE.search(ln) for ln in ctx):
                findings.append(("sequence-gap", "MED", f"{ns} range",
                                 f"{ns} slot `{n}` is MISSING with no tombstone/retirement note — "
                                 f"an empty reusable slot is the H21 hazard"))

    # ── 4. RESERVATION with no SSoT row ───────────────────────────────────────────────────────
    # `registry_id:` / `owns_namespace:` claim an id in frontmatter; that id must exist.
    for p in sorted((WORKSPACE / "DESIGN_SPECS").rglob("*.md")):
        head = _read(p)[:1500]
        m = re.search(r"^registry_id:\s*(\S+)", head, re.M)
        if not m:
            continue
        rid = m.group(1)
        ns = ("INVARIANT" if rid.startswith("H") else
              "META" if rid.startswith("M") else
              "TOOLCHAIN" if rid.startswith("T") else
              "BLINDSPOT" if rid.startswith("B") else None)
        if ns and rid not in idx.get(ns, {}):
            findings.append(("reservation-no-ssot", "HIGH",
                             str(p.relative_to(WORKSPACE)),
                             f"declares `registry_id: {rid}` but no defining row exists for it"))
    return findings




def check_citable_ids(quiet, workspace):
    idx = defining_index()
    total = sum(len(v) for v in idx.values())
    if total < 50:
        print(f"  [Check 14] FAIL — the defining-form index resolved only {total} ids; that is a "
              f"broken SSoT path, not a clean corpus. Refusing to report green over an empty set.")
        return 1

    # ID-SET GOLDEN (H21 on the doc plane): the citation scan only notices a REMOVED id if
    # something still cites it, so an id deleted together with its last citation would vanish
    # silently. The golden makes any disappearance a tracked diff.
    if CITABLE_GOLDEN.is_file():
        want = {l.strip() for l in CITABLE_GOLDEN.read_text().splitlines() if l.strip()}
        got = {f"{ns}|{rid}" for ns, e in idx.items() for rid in e}
        gone = sorted(want - got)
        if gone:
            print(f"  [Check 14] FAIL — {len(gone)} citable id(s) DISAPPEARED from the defining "
                  f"index with no tombstone: {gone[:8]}")
            print(f"             An id slot must be RETIRED deliberately, never dropped (H21). If "
                  f"intentional, re-bless: python3 tools/bless.py (TTY-gated)")
            return 1

    findings = _citable_findings(idx)
    base = set()
    if CITABLE_BASELINE.is_file():
        base = {l.strip() for l in CITABLE_BASELINE.read_text().splitlines()
                if l.strip() and not l.startswith("#")}
    new = [f for f in findings if f"{f[0]}|{f[3]}" not in base]
    hi = [f for f in new if f[1] == "HIGH"]

    if hi:
        print(f"  [Check 14] FAIL — {len(hi)} NEW citable-ID violation(s) "
              f"({len(findings)} total, {len(base)} baselined):")
        for _, sev, where, msg in hi[:12]:
            print(f"      [{sev}] {where} — {msg}")
        if len(hi) > 12:
            print(f"      ... and {len(hi) - 12} more")
        return 1
    if not quiet:
        med = len([f for f in new if f[1] == "MED"])
        print(f"  [Check 14] PASS — citable-ID integrity ({total} ids indexed BY DEFINING FORM; "
              f"{len(base)} baselined; {med} new MED advisory)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Mechanical half of /capture-audit (Checks 1/4/8).")
    ap.add_argument("--check", type=int, choices=[1, 4, 8, 13, 14], help="run only one check")
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
    if args.check in (None, 14):
        rc |= check_citable_ids(args.quiet, workspace)
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
