#!/usr/bin/env python3
"""
test_check_navinfra_cohort_reference.py — NEGATIVE self-test (teeth) for
check_navinfra_cohort_reference.py (D-137: a guard that's only ever GREEN could be silently broken).

Proves the nav-infra cohort guard:
  (1) goes RED (exit 1) AND names the offender when a cohort skill drops the nav-infra reference;
  (2) stays GREEN (exit 0) when every cohort skill reaches the consult (shared-Stage-0 cite OR direct ref).

Hermetic: builds a temp workspace tree (claude-skills/ + DESIGN_SPECS/ + a copy of the checker), so the
checker's content-marker root resolver lands inside the temp tree. Never touches the real repo.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CHECK = Path(__file__).resolve().parent / "check_navinfra_cohort_reference.py"
SPEC_REL = "DESIGN_SPECS/audit-methodologies/adversarial-multi-agent-audit-methodology.md"
SPEC_FRONTMATTER = "---\napplies_at_skills: [/alpha, /beta, /gamma]\n---\n\n# stub spec\n"

WITH_SHARED = "# /x\n> Stage 0 per skill-knowledge-consultation-and-auto-routing.md\n"
WITH_DIRECT = "# /x\nregen CODE_MAP via gen_code_map at pickup; load the dependency-graph DAG\n"
WITHOUT = "# /x\nno nav reference anywhere in this body\n"


def build(root: Path, skill_bodies: dict) -> None:
    (root / "DESIGN_SPECS/audit-methodologies").mkdir(parents=True)
    (root / SPEC_REL).write_text(SPEC_FRONTMATTER, encoding="utf-8")
    (root / "tools").mkdir()
    shutil.copy(CHECK, root / "tools" / CHECK.name)
    for name, body in skill_bodies.items():
        d = root / "claude-skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(body, encoding="utf-8")


def run(root: Path):
    r = subprocess.run(
        [sys.executable, str(root / "tools" / CHECK.name)],
        capture_output=True, text=True,
    )
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    fails: list[str] = []

    # Case 1 — a gap: /beta drops the reference -> expect RED + names /beta.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        build(root, {"alpha": WITH_SHARED, "beta": WITHOUT, "gamma": WITH_DIRECT})
        code, out = run(root)
        if code == 0:
            fails.append("RED case: expected exit 1 on a dropped reference, got 0")
        if "/beta" not in out:
            fails.append("RED case: offender /beta not named in output")

    # Case 2 — clean: all three reach the consult -> expect GREEN.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        build(root, {"alpha": WITH_SHARED, "beta": WITH_DIRECT, "gamma": WITH_SHARED})
        code, out = run(root)
        if code != 0:
            fails.append(f"GREEN case: expected exit 0 on a clean cohort, got {code}\n{out}")

    if fails:
        print("test_check_navinfra_cohort_reference: FAIL")
        for f in fails:
            print("  - " + f)
        return 1
    print("test_check_navinfra_cohort_reference: PASS (RED on gap + names offender; GREEN on clean)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
