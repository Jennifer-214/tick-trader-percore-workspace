#!/usr/bin/env python3
"""check_handoff_active_singleton.py — enforce AT MOST ONE `status: active` handoff.

WHY THIS EXISTS (codified 2026-06-02):
No-arg `/accept-handoff` used to resolve the live handoff by filesystem MTIME —
fragile: a `git checkout`/`pull` resets mtimes (a whole batch was observed reset
to one timestamp), so "the newest handoff" could silently become the wrong file.
The fix is an EXPLICIT state field in each handoff's frontmatter:

    status: active       <- THE one live handoff (what /accept-handoff resolves to)
    status: deferred     <- PARKED: a different priority jumped the queue; this one
                            RESUMES (deferred -> active) when that work closes. NOT dead.
    status: superseded   <- a prior handoff a newer one replaced (same work-line). Dead.
    (no status field)    <- legacy / untagged ≡ inactive (zero retrofit of history)

The state transition is SUPERSEDE-ON-WRITE, not inactive-on-consume: the writer
(`/handoff`, `/close-session`'s handoff step) flips the prior `active` -> `superseded`
when it writes a new `active` one. A handoff must stay live across a dead session's
RE-PICKUP until a NEWER one supersedes it — flipping it inactive the first time it is
read would break the re-pickup of in-progress work.

This guard is the INVARIANT half: globally AT MOST ONE handoff may be `status: active`.
`/accept-handoff` resolves by the tag; this guard is what makes "exactly the live one"
TRUE rather than hoped-for. Two actives = a missed writer-side flip (or a manual write)
-> caught here deterministically instead of mis-resolving at pickup.

Sister: feedback_guards_compound_enforcement_is_leverage (the guard is the permanent
leverage; the frontmatter discipline is the one-time habit). The decision-log
`<!-- STATUS: decided -->` sentinels that /accept-handoff Stage 4.6 reads are the same
doc-state-read-mechanically idiom. Machine-portable (.absolute() + env override, never
.resolve()) per symlinked-tool-host-root-resolution (LANDMINE 5) — runs when symlinked
from the private workspace into the host. Teeth-proof: --selftest.

Wiring: tools/check_session_docs.sh calls this HARD.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

# Match `status: active` ONLY inside frontmatter (anchored line). Body prose that
# happens to contain "status: active" must not count.
ACTIVE_RE = re.compile(r'^status:\s*active\b', re.MULTILINE)


def repo_root() -> Path:
    # <repo>/tools/check_handoff_active_singleton.py. .absolute() NOT .resolve():
    # the tool may be symlinked from the private workspace into the host; .resolve()
    # would follow the symlink to the workspace + scan the wrong plans/. Env first.
    env = os.environ.get("FOXML_REPO_ROOT") or os.environ.get("FOXML_ENGINE")
    return Path(env) if env else Path(__file__).absolute().parent.parent


def plans_root(root: Path) -> Path:
    # plans/ is a content symlink to the workspace; following it is CORRECT here
    # (the real handoffs live there). Env override for explicit control.
    env = os.environ.get("FOXML_PLANS_DIR")
    return Path(env) if env else root / "plans"


def frontmatter(text: str) -> str:
    """The YAML frontmatter block (between the first two '---'), or '' if none."""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[:end] if end != -1 else ""


def is_active(path: Path) -> bool:
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return False
    return bool(ACTIVE_RE.search(frontmatter(text)))


# `status: deferred` = parked-will-resume (distinct from superseded = replaced-dead). Does
# NOT count toward the ≤1-active cap; but a deferred handoff with NO active one means a parked
# work-line was never resumed -> a (non-fatal) advisory so it isn't silently orphaned.
DEFERRED_RE = re.compile(r'^status:\s*deferred\b', re.MULTILINE)


def is_deferred(path: Path) -> bool:
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return False
    return bool(DEFERRED_RE.search(frontmatter(text)))


def find_handoffs(plans: Path):
    """Every handoffs/*.md under plans/ (any depth), minus templates + READMEs.

    os.walk(followlinks=True) so the top plans/ symlink + any nested symlinks are
    traversed (glob '**' is flaky across a symlinked top; the walk is robust)."""
    out = []
    if not Path(plans).is_dir():
        return out
    for dirpath, _dirnames, filenames in os.walk(plans, followlinks=True):
        if os.path.basename(dirpath) != "handoffs":
            continue
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            if fn.startswith("_") or fn == "README.md":  # templates / dir-readme
                continue
            out.append(Path(dirpath) / fn)
    return sorted(out)


def scan(plans: Path):
    return [h for h in find_handoffs(plans) if is_active(h)]


def scan_deferred(plans: Path):
    return [h for h in find_handoffs(plans) if is_deferred(h)]


def run() -> int:
    root = repo_root()
    plans = plans_root(root)
    if not Path(plans).is_dir():
        print(f"  ⏭  handoff-active singleton: plans/ not found at {plans} — skipped")
        return 0
    actives = scan(plans)
    deferred = scan_deferred(plans)
    n = len(actives)
    if n == 0:
        if deferred:
            print(f"  ⚠️  handoff-active singleton: 0 active, but {len(deferred)} DEFERRED "
                  "handoff(s) parked — resume one (deferred → active) when its blocker clears?")
            for dpath in deferred:
                try:
                    rel = dpath.relative_to(plans)
                except ValueError:
                    rel = dpath
                print(f"       parked: plans/{rel}")
        else:
            print("  ⚠️  handoff-active singleton: 0 handoffs tagged `status: active` "
                  "(sprint between handoffs, or none adopted the tag yet → /accept-handoff "
                  "falls back to mtime). Advisory; not failing.")
        return 0
    if n == 1:
        try:
            rel = actives[0].relative_to(plans)
        except ValueError:
            rel = actives[0]
        tail = f"  (+{len(deferred)} deferred parked)" if deferred else ""
        print(f"  ✅ handoff-active singleton: exactly 1 active — plans/{rel}{tail}")
        return 0
    print(f"  ❌ handoff-active singleton: {n} handoffs are `status: active` — must be ≤1.")
    print("     (the writer flips the prior active → superseded when it writes a new one)")
    for a in actives:
        try:
            rel = a.relative_to(plans)
        except ValueError:
            rel = a
        print(f"       - plans/{rel}")
    print("     FIX: set all but the live one to `status: superseded` in their frontmatter.")
    return 1


def selftest() -> int:
    ok = True
    with tempfile.TemporaryDirectory() as d:
        hd = Path(d) / "plans" / "sprintX" / "handoffs"
        hd.mkdir(parents=True)
        plans = Path(d) / "plans"

        def w(name, status):
            body = "---\ntype: handoff\n"
            if status:
                body += f"status: {status}\n"
            body += "---\n\nbody mentions status: active in prose (must NOT count)\n"
            (hd / name).write_text(body)

        # superseded + untagged + deferred ≡ NOT active → 0 active (must pass)
        w("a-old.md", "superseded")
        w("b-legacy.md", None)
        w("e-parked.md", "deferred")
        if scan(plans) != []:
            print("SELFTEST FAIL: superseded/untagged/deferred (or body prose) counted as active")
            ok = False
        if len(scan_deferred(plans)) != 1:
            print("SELFTEST FAIL: deferred handoff not detected by scan_deferred")
            ok = False
        # add the single live one → exactly 1
        w("c-live.md", "active")
        if len(scan(plans)) != 1:
            print("SELFTEST FAIL: did not find the single active")
            ok = False
        # _TEMPLATE + README with status: active must be ignored
        w("_TEMPLATE-handoff.md", "active")
        w("README.md", "active")
        if len(scan(plans)) != 1:
            print("SELFTEST FAIL: template/README counted as active")
            ok = False
        # a second real active → guard must see 2 (run() would return 1)
        w("d-second.md", "active")
        if len(scan(plans)) != 2:
            print("SELFTEST FAIL: did not detect 2 actives (guard would not trip)")
            ok = False
    print("SELFTEST PASS — handoff-active singleton guard has teeth."
          if ok else "SELFTEST FAILED.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else run())
