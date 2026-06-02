#!/usr/bin/env python3
"""check_always_loaded_budget.py — guard the always-loaded doc context budget.

WHY THIS EXISTS (codified v5.15.5.F.4d.1.E, 2026-06-02):
The harness auto-loads CLAUDE.md, CLAUDE.local.md, and the memory MEMORY.md index
into EVERY session's context. Each has a context-load byte budget; exceeding it makes
the harness SILENTLY TRUNCATE the doc (observed this sprint: MEMORY.md clipped
mid-file — "Only part of it was loaded"). A truncated governance/index doc =
load-bearing rules + pointers silently missing from context, with no error. This
guard fails the doc sweep when an always-loaded doc exceeds its cap, so bloat is
caught deterministically at /close-session + /accept-handoff (both run
check_session_docs.sh) instead of surfacing later as a silent gap. The guard is the
permanent leverage (per feedback_guards_compound_enforcement_is_leverage); the
compression is the one-time fix.

Caps below = the harness always-loaded context-load budgets (CLAUDE* = 40000 chars;
MEMORY = 24.4KB). Single source of truth for those numbers; tune here if the harness
budget changes. When a doc can no longer stay under cap by compression (genuinely too
many entries, not bloated entries), THAT is the trigger to split it (e.g. MEMORY.md →
hot index + an extended index loaded at /accept-handoff) — the guard is what tells you
you've reached that point.

Machine-portable per feedback_machine_portable_resolver_for_committed_tool_paths:
env override -> derived default -> glob fallback -> skip-if-absent. No $HOME hardcode,
so it runs on any clone / PC / SSH-grid node (CLAUDE.local.md + MEMORY.md are private +
may be absent on a fresh public clone -> those rows SKIP, never falsely fail).

Wiring: tools/check_session_docs.sh calls this HARD. Teeth-proof: --selftest.
"""
import os
import sys
import glob
import tempfile
from pathlib import Path

# --- caps (bytes) = harness always-loaded context-load budgets (SSoT) ---
CAP_CLAUDE = 40000      # CLAUDE.md / CLAUDE.local.md
CAP_MEMORY = 24400      # memory/MEMORY.md (24.4KB)
NEAR_FRAC = 0.90        # >=90% of cap -> advisory NEAR (trim soon, not yet failing)


def repo_root() -> Path:
    # this file lives at <repo>/tools/check_always_loaded_budget.py. Use .absolute() NOT
    # .resolve(): the tool may live in a private workspace symlinked into the repo, and
    # .resolve() would follow the symlink to the workspace + check the wrong CLAUDE.local.md.
    # env override first for explicit control. See LANDMINES Landmine 5.
    env = os.environ.get("FOXML_REPO_ROOT") or os.environ.get("FOXML_ENGINE")
    return Path(env) if env else Path(__file__).absolute().parent.parent


def resolve_memory_md(root: Path):
    """Locate the auto-loaded memory index (private; per-machine path)."""
    env = os.environ.get("CLAUDE_MEMORY_DIR")
    if env:
        p = Path(env) / "MEMORY.md"
        if p.is_file():
            return p
    # derived default: the harness encodes the project path with '/' and '_' -> '-'
    slug = str(root).replace("/", "-").replace("_", "-")
    p = Path.home() / ".claude" / "projects" / slug / "memory" / "MEMORY.md"
    if p.is_file():
        return p
    # glob fallback: a single project memory dir mentioning the repo basename
    base = root.name.replace("_", "-").split("-")[0].lower()  # e.g. "foxml"
    hits = [Path(x) for x in glob.glob(
        str(Path.home() / ".claude" / "projects" / "*" / "memory" / "MEMORY.md"))]
    named = [h for h in hits if base in str(h).lower()]
    if len(named) == 1:
        return named[0]
    if len(hits) == 1:
        return hits[0]
    return None  # absent / ambiguous -> caller SKIPs


def check(files):
    """files: list of (label, path-or-None, cap). Returns (any_over, rows)."""
    over = False
    rows = []
    for label, path, cap in files:
        if path is None or not Path(path).is_file():
            rows.append((label, None, cap, "SKIP", "(not present — skipped)"))
            continue
        n = Path(path).stat().st_size
        pct = n / cap
        if n > cap:
            st = "OVER"
            over = True
        elif pct >= NEAR_FRAC:
            st = "NEAR"
        else:
            st = "OK"
        rows.append((label, n, cap, st, f"{pct * 100:.0f}% of cap"))
    return over, rows


def fmt(rows):
    icon = {"OK": "✅", "NEAR": "⚠️ ", "OVER": "❌", "SKIP": "⏭ "}
    out = ["  always-loaded doc context budget:"]
    for label, n, cap, st, note in rows:
        if n is None:
            out.append(f"    {icon[st]} {label:<16} {note}")
        else:
            out.append(f"    {icon[st]} {label:<16} {n:>7,} / {cap:>6,} B  ({note})")
    return "\n".join(out)


def run():
    root = repo_root()
    files = [
        ("CLAUDE.md",       root / "CLAUDE.md",       CAP_CLAUDE),
        ("CLAUDE.local.md", root / "CLAUDE.local.md", CAP_CLAUDE),
        ("MEMORY.md",       resolve_memory_md(root),  CAP_MEMORY),
    ]
    over, rows = check(files)
    print(fmt(rows))
    if over:
        print("  ❌ an always-loaded doc EXCEEDS its context cap — trim it "
              "(the harness SILENTLY TRUNCATES it otherwise).")
        return 1
    return 0


def selftest():
    """Teeth-proof: over-cap MUST trip; under-cap MUST pass; absent MUST skip."""
    ok = True
    with tempfile.TemporaryDirectory() as d:
        big = Path(d) / "big.md"
        big.write_text("x" * 100)
        small = Path(d) / "small.md"
        small.write_text("x" * 10)
        over, _ = check([("BIG", big, 50)])
        if not over:
            print("SELFTEST FAIL: over-cap file did not trip")
            ok = False
        under, _ = check([("SMALL", small, 50)])
        if under:
            print("SELFTEST FAIL: under-cap file tripped")
            ok = False
        absent, rows = check([("GONE", Path(d) / "nope.md", 50)])
        if absent or rows[0][3] != "SKIP":
            print("SELFTEST FAIL: absent file did not skip cleanly")
            ok = False
    print("SELFTEST PASS — budget guard has teeth." if ok else "SELFTEST FAILED.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else run())
