#!/usr/bin/env python3
"""
check_handoff_capture_completeness.py — the active handoff MUST carry a SUBSTANTIVE
"Capture-completeness" section (.E.1.0 — un-bypassable enforcement of the convention).

WHY: `/handoff` Stage 1.8 runs the capture-audit pre-write gate, AND the handoff
template carries a `## Capture-completeness (this session — nothing lost)` section —
BUT both are bypassable by HAND-WRITING a handoff that omits them. The `.E.1.0` session
did exactly that: D-227 + TECH_DEBT-204 surfaced only when the operator asked, because
the hand-written handoff skipped the section + the gate. This check makes the section
MANDATORY + DETAILED so the convention can no longer be skipped (M7 escalation:
structural enforcement when discipline proves insufficient — it recurred D-220 → D-227).

DETAILED-ENOUGH (not a header-presence check): the section must ADDRESS each capture
dimension — decisions → log · findings → ledger · memories/skills → indexed — each
either enumerated OR explicitly "none this session", with no placeholders.

Exit 0 = the active handoff has a substantive capture-completeness section (OR there is
no single active handoff / no handoffs — not this check's job). Exit 1 = missing / thin /
placeholder.

Run:      python3 tools/check_handoff_capture_completeness.py [<handoff.md>]
Selftest: python3 tools/check_handoff_capture_completeness.py --selftest
"""
import os, re, sys, glob, tempfile

_HEADER = re.compile(
    r'^\s{0,3}#{2,4}\s+capture[\s\-]?completeness\b'
    r'|^\s{0,3}#{2,4}\s+captures?\s+verified\b', re.I)
_NEXT_HEADER = re.compile(r'^\s{0,3}#{1,4}\s+\S')

# Each capture dimension must be ADDRESSED in the section (enumerate OR say "none").
_DIMENSIONS = {
    "decisions → log":         re.compile(r'\bD-\d+\b|\bdecision', re.I),
    "findings → ledger":       re.compile(r'TECH_DEBT|\bTD-\d+|PARITY|\bledger\b|\bhomed\b|\bregister\b|\bfinding', re.I),
    "memories/skills → index": re.compile(r'\bmemor|\bskill|MEMORY\.md|\bindexed\b', re.I),
}
_PLACEHOLDER = re.compile(r'\bTODO\b|\bTBD\b|\bFIXME\b|\bXXX\b|<\.\.\.>', re.I)


def _active_handoff(root):
    """The single status:active handoff path, or None (0 or >1 → the singleton check's job)."""
    actives = []
    for p in glob.glob(os.path.join(root, "plans", "**", "handoffs", "*.md"), recursive=True):
        try:
            with open(p, errors="replace") as f:
                head = f.read(4000)
        except OSError:
            continue
        if re.search(r'^status:\s*active\b', head, re.M):
            actives.append(p)
    return actives[0] if len(actives) == 1 else None


def _section_body(text):
    """The capture-completeness section body (header→next-header), or None if absent."""
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if _HEADER.match(ln):
            start = i + 1
            break
    if start is None:
        return None
    body = []
    for ln in lines[start:]:
        if _NEXT_HEADER.match(ln):
            break
        body.append(ln)
    return "\n".join(body)


def check_handoff(path):
    """Return (ok, [problems])."""
    try:
        with open(path, errors="replace") as f:
            text = f.read()
    except OSError as e:
        return False, [f"cannot read {path}: {e}"]
    body = _section_body(text)
    if body is None:
        return False, ["NO 'Capture-completeness' (or 'Captures verified') section — the "
                       "convention the handoff template carries was omitted (hand-written-around)."]
    problems = []
    if len([l for l in body.splitlines() if l.strip()]) < 2:
        problems.append("section present but EMPTY/thin (< 2 content lines) — fill it, don't stub it.")
    missing = [name for name, rx in _DIMENSIONS.items() if not rx.search(body)]
    if missing:
        problems.append("does not address: " + " · ".join(missing)
                        + " — each must be enumerated OR explicitly 'none this session'.")
    if _PLACEHOLDER.search(body):
        problems.append("contains a placeholder (TODO/TBD/<...>) — finish the capture verification.")
    return (not problems), problems


def _selftest():
    GOOD = ("---\nstatus: active\n---\n# H\n## Capture-completeness (this session — nothing lost)\n"
            "- **Decisions → log:** D-227 added (the reshape).\n"
            "- **Findings → ledger:** TECH_DEBT-204 (the .githooks gap) homed.\n"
            "- **Memories/skills → indexed:** no new memories this session.\n"
            "- Verified: doc-CI sweep green.\n## Next\n")
    BAD_MISSING = "---\nstatus: active\n---\n# H\n## TL;DR\nnothing\n## Next\n"
    BAD_THIN = "---\nstatus: active\n---\n# H\n## Capture-completeness\n- nothing\n## Next\n"
    BAD_PLACEHOLDER = ("---\nstatus: active\n---\n# H\n## Capture-completeness\n"
                       "- Decisions → log: TODO\n- Findings → ledger: TECH_DEBT\n- Memories indexed\n## Next\n")
    fails = []
    for name, text, want in [("GOOD", GOOD, True), ("BAD-missing", BAD_MISSING, False),
                             ("BAD-thin", BAD_THIN, False), ("BAD-placeholder", BAD_PLACEHOLDER, False)]:
        fd, p = tempfile.mkstemp(suffix=".md"); os.close(fd)
        try:
            with open(p, "w") as f:
                f.write(text)
            ok, _ = check_handoff(p)
            if ok != want:
                fails.append(f"{name}: expected ok={want}, got {ok}")
        finally:
            os.unlink(p)
    if fails:
        print("[test-handoff-capture] FAIL:")
        for x in fails:
            print("  " + x)
        return 1
    print("[test-handoff-capture] PASS — rejects missing/thin/placeholder, accepts a full section")
    return 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    root = os.environ.get("FOXML_ENGINE") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = next((a for a in argv[1:] if not a.startswith("-")), None)
    path = target or _active_handoff(root)
    if path is None:
        print("[check-handoff-capture] SKIP — no single status:active handoff (0 or >1; not this check's job)")
        return 0
    ok, problems = check_handoff(path)
    rel = os.path.relpath(path, root)
    if ok:
        print(f"[check-handoff-capture] PASS — {rel} has a substantive Capture-completeness section")
        return 0
    print(f"[check-handoff-capture] FAIL — {rel}:")
    for p in problems:
        print(f"  - {p}")
    print("  → a handoff must verify NOTHING was lost: decisions→log · findings→ledger · memories/skills→indexed.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
