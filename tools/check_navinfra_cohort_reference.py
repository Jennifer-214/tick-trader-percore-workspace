#!/usr/bin/env python3
"""
check_navinfra_cohort_reference.py — M7 enforcement for the nav-infra cohort discipline.

Every skill listed in `applies_at_skills` of
  DESIGN_SPECS/audit-methodologies/adversarial-multi-agent-audit-methodology.md
MUST reach the nav-infra consult (the DAG + CODE_MAP + per-edit data-flow / downstream
blast-radius trace) — either by citing the shared Stage-0 doc
  skill-knowledge-consultation-and-auto-routing.md   (its Stage-0 item 6 IS the nav-infra consult)
OR via a direct nav-infra reference in the skill body.

A cohort skill that drops it FAILS (exit 1). This is the structural close of the M7 surface
the operator named 2026-06-11 ("this is what I've been trying to enforce ... you can only do so
much"): the artifacts (DAG / CODE_MAP / the trace skills) exist, but nothing routed the cohort
through them, so the discipline depended on a per-session operator nudge. The check takes the
human OUT of the manual-enforcement loop — drop the reference and the build goes red.

Sister: tools/check_session_docs.sh (aggregator) + /capture-audit. Canonical discipline:
DESIGN_SPECS/audit-methodologies/adversarial-multi-agent-audit-methodology.md
  § "Nav-infra is a first-class input". Codified v5.15.5.F.4d.1.E.0.10 (2026-06-11).
"""
import re
import sys
from pathlib import Path


def find_workspace_root(start: Path) -> Path:
    """The workspace root is the dir holding BOTH claude-skills/ and DESIGN_SPECS/.

    Resolve by CONTENT marker, not an assumed path: invocation can arrive via the
    engine-side `tools/` symlink (-> workspace/tools), so walk up from the resolved
    script location and verify the marker dirs exist. Avoids the Landmine-5 wrong-root
    class (a bare .resolve()/.parent that lands in the symlink's source tree).
    """
    here = start.resolve()
    for d in [here, *here.parents]:
        if (d / "claude-skills").is_dir() and (d / "DESIGN_SPECS").is_dir():
            return d
    sys.exit("check_navinfra_cohort: could not locate workspace root "
             "(a dir containing both claude-skills/ and DESIGN_SPECS/)")


ROOT = find_workspace_root(Path(__file__))
SPEC = ROOT / "DESIGN_SPECS/audit-methodologies/adversarial-multi-agent-audit-methodology.md"

# Inheritance point: citing this shared Stage-0 doc pulls in its item-6 nav-infra consult.
SHARED_STAGE0 = "skill-knowledge-consultation-and-auto-routing"
# Or a skill may reference the nav-infra directly (pickup skills do this in their own stages).
DIRECT_TOKENS = (
    "gen_code_map", "CODE_MAP", "dependency-graph",
    "dependency-chain-trace", "nav-infra", "navigation-infra", "navigation infra",
)


def applies_at_skills(spec_text: str) -> list[str]:
    m = re.search(r'^applies_at_skills:\s*\[(.*?)\]', spec_text, re.M | re.S)
    if not m:
        sys.exit("check_navinfra_cohort: applies_at_skills not found in spec frontmatter")
    return [s.strip().lstrip("/").strip() for s in m.group(1).split(",") if s.strip()]


def satisfies(skill_md: str) -> bool:
    return (SHARED_STAGE0 in skill_md) or any(tok in skill_md for tok in DIRECT_TOKENS)


def main() -> int:
    skills = applies_at_skills(SPEC.read_text(encoding="utf-8"))
    failures: list[str] = []
    missing: list[str] = []
    for name in skills:
        f = ROOT / "claude-skills" / name / "SKILL.md"
        if not f.is_file():
            missing.append(name)
            continue
        if not satisfies(f.read_text(encoding="utf-8")):
            failures.append(name)

    total = len(skills)
    ok = total - len(failures) - len(missing)
    print(f"check_navinfra_cohort_reference: {ok}/{total} cohort skills reach the nav-infra consult")
    if missing:
        print("  ⚠️  SKILL.md not found (advisory — stale applies_at_skills entry?): "
              + ", ".join("/" + m for m in missing))
    if failures:
        print("  ❌ MISSING nav-infra reference:")
        for n in failures:
            print(f"       /{n}")
        print("  Fix: have the skill cite `skill-knowledge-consultation-and-auto-routing.md`")
        print("       (Stage-0 item 6 IS the nav-infra consult) OR reference CODE_MAP / the DAG /")
        print("       /dependency-chain-trace directly. See adversarial-multi-agent-audit-methodology.md")
        print("       § 'Nav-infra is a first-class input'.")
        return 1
    print("  ✅ all cohort skills reach the nav-infra consult (DAG + CODE_MAP + per-edit data-flow/downstream)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
