#!/usr/bin/env python3
"""check_index_currency.py — close-ritual index-reconciliation guard (TECH_DEBT-194).

WHY (codified 2026-06-13, .E.0.10): the sprint MASTER.md CURRENT-STATE banner's
"Pickup -> handoffs/..." pointer kept going STALE — naming a SUPERSEDED handoff while a
NEWER one was the live `status: active` singleton. It recurred across sessions (WH-2:
stale always-loaded/SSoT-index banners) and was caught only by operator prompt, never by
the mechanical floor (check_session_docs was GREEN — it never checked MASTER currency).
This guard cross-checks the two SSoTs: the MASTER banner's active-handoff pointer MUST
name the singleton `status: active` handoff. M7 escalation of WH-2 (memory/discipline
insufficient -> structural enforcement).

Composes with check_handoff_active_singleton.py: that enforces "<=1 active"; this enforces
"MASTER names it". Together: exactly-one-active AND MASTER-points-to-it.

v1 = the pointer cross-check (deterministic; the recurring failure mode). A date-staleness
check (MASTER banner date >= the latest decision-log D-entry / the active-handoff date) is
a future refinement noted for v2.

Machine-portable (.absolute() + env override, never .resolve()) per LANDMINE 5 — runs when
symlinked from the private workspace into the host. Wiring: tools/check_session_docs.sh
calls this HARD. Teeth-proof: --selftest.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

# `status: active` ONLY inside frontmatter (anchored). Body prose must not count.
ACTIVE_RE = re.compile(r'^status:\s*active\b', re.MULTILINE)
# A handoff reference: `handoffs/<basename>.md`
HANDOFF_REF_RE = re.compile(r'handoffs/([A-Za-z0-9._-]+\.md)')


def repo_root() -> Path:
    env = os.environ.get("FOXML_REPO_ROOT") or os.environ.get("FOXML_ENGINE")
    return Path(env) if env else Path(__file__).absolute().parent.parent


def plans_root(root: Path) -> Path:
    env = os.environ.get("FOXML_PLANS_DIR")
    return Path(env) if env else root / "plans"


def frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[:end] if end != -1 else ""


def find_handoffs(plans: Path):
    out = []
    if not Path(plans).is_dir():
        return out
    for dirpath, _d, filenames in os.walk(plans, followlinks=True):
        if os.path.basename(dirpath) != "handoffs":
            continue
        for fn in filenames:
            if fn.endswith(".md") and not fn.startswith("_") and fn != "README.md":
                out.append(Path(dirpath) / fn)
    return sorted(out)


def is_active(path: Path) -> bool:
    try:
        return bool(ACTIVE_RE.search(frontmatter(path.read_text(errors="replace"))))
    except OSError:
        return False


def active_handoffs(plans: Path):
    return [h for h in find_handoffs(plans) if is_active(h)]


def master_banner_pointer(master_text: str):
    """The handoff basename the MASTER CURRENT-STATE banner names as the live pickup, or
    None. Heuristic: a `handoffs/<x>.md` ref on a line mentioning 'Pickup' (the canonical
    pointer) or 'the ACTIVE one'. Banners append progress lines, so the LAST such ref wins."""
    cands = []
    for line in master_text.splitlines():
        if "handoffs/" not in line:
            continue
        up = line.upper()
        if ("PICKUP" in up) or ("ACTIVE ONE" in up):
            cands.extend(m.group(1) for m in HANDOFF_REF_RE.finditer(line))
    return cands[-1] if cands else None


def check_sprint(active: Path):
    """(status, message); status in {'ok','stale','advisory'}. MASTER is the active
    handoff's sprint sibling: plans/<sprint>/handoffs/<f> -> plans/<sprint>/MASTER.md."""
    master = active.parent.parent / "MASTER.md"
    if not master.is_file():
        return ("advisory", f"no MASTER.md at {master} — cannot cross-check")
    try:
        ptr = master_banner_pointer(master.read_text(errors="replace"))
    except OSError:
        return ("advisory", f"could not read {master}")
    if ptr is None:
        return ("advisory", f"{master} has no 'Pickup -> handoffs/...' banner pointer")
    if ptr == active.name:
        return ("ok", f"MASTER banner points to the live active handoff ({active.name})")
    return ("stale",
            f"MASTER banner is STALE — names `{ptr}` but the singleton active handoff is "
            f"`{active.name}`\n     FIX: update the MASTER CURRENT-STATE 'Pickup ->' pointer "
            f"-> {master}")


def run() -> int:
    root = repo_root()
    plans = plans_root(root)
    if not Path(plans).is_dir():
        print(f"  ⏭  index-currency: plans/ not found at {plans} — skipped")
        return 0
    actives = active_handoffs(plans)
    if len(actives) == 0:
        print("  ⚠️  index-currency: 0 active handoff — nothing to cross-check (advisory).")
        return 0
    if len(actives) > 1:
        print("  ⚠️  index-currency: >1 active handoff — the singleton guard owns this; skipping.")
        return 0
    status, msg = check_sprint(actives[0])
    if status == "ok":
        print(f"  ✅ index-currency: {msg}")
        return 0
    if status == "advisory":
        print(f"  ⚠️  index-currency: {msg} (advisory).")
        return 0
    print(f"  ❌ index-currency: {msg}")
    return 1


def selftest() -> int:
    ok = True
    with tempfile.TemporaryDirectory() as d:
        plans = Path(d) / "plans"
        hd = plans / "sprintX" / "handoffs"
        hd.mkdir(parents=True)
        master = plans / "sprintX" / "MASTER.md"

        def wh(name, status):
            body = "---\ntype: handoff\n"
            if status:
                body += f"status: {status}\n"
            body += "---\n\nbody mentions handoffs/decoy.md in prose\n"
            (hd / name).write_text(body)

        wh("2026-01-01-live.md", "active")
        wh("2026-01-01-old.md", "superseded")
        live = hd / "2026-01-01-live.md"

        master.write_text("# MASTER\n\n> **CURRENT STATE**\n"
                          "> **Pickup -> `handoffs/2026-01-01-live.md` (the ACTIVE one).**\n")
        if check_sprint(live)[0] != "ok":
            print("SELFTEST FAIL: matching pointer not 'ok'"); ok = False

        master.write_text("# MASTER\n\n> **Pickup -> `handoffs/2026-01-01-old.md` (the ACTIVE one).**\n")
        if check_sprint(live)[0] != "stale":
            print("SELFTEST FAIL: stale pointer not detected"); ok = False

        master.write_text("# MASTER\n\n> nothing here\n")
        if check_sprint(live)[0] != "advisory":
            print("SELFTEST FAIL: no-pointer not advisory"); ok = False

        # active_handoffs must find exactly the one live; superseded must not count
        if len(active_handoffs(plans)) != 1:
            print("SELFTEST FAIL: active_handoffs miscount"); ok = False

    print("SELFTEST PASS — index-currency guard has teeth." if ok else "SELFTEST FAILED.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else run())
