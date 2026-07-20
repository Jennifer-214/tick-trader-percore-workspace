#!/usr/bin/env python3
"""rebuild_doc_indexes.py — regenerate doc-system indexes from frontmatter.

Implements `/index-rebuild` skill (DESIGN_SPECS/doc-disciplines/) mechanically.

Regenerates:
- CLAUDE.md "Skill suite" table (auto-generated from SKILL.md frontmatter `concern:`)
- DESIGN_SPECS/README.md catalog (grouped by `type:` then `stage:`)
- DESIGN_SPECS/TAG_INDEX.md (tag → files reverse-lookup snapshot)
- DOCS/CODE_TAG_INDEX.md (the CODE-side twin — [TAG] values + unit blocks across converted
  engine files, via check_code_tag_blocks' shared grammar; E.1.2.A §Propagation / task #14)

Sister to:
- tools/check_doc_metadata.py (validation; this tool generates indexes)
- tools/subdivide_design_specs.py (folder subdivision migration)

Usage:
  python3 tools/rebuild_doc_indexes.py                       # regenerate all
  python3 tools/rebuild_doc_indexes.py --target claude-md    # CLAUDE.md skill table only
  python3 tools/rebuild_doc_indexes.py --target readme       # DESIGN_SPECS/README.md only
  python3 tools/rebuild_doc_indexes.py --target tag-index    # TAG_INDEX.md only
  python3 tools/rebuild_doc_indexes.py --dry-run             # print proposed output
"""
import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).absolute().parent))   # .absolute() NOT .resolve(): resolving the tools/
# symlink gives the imported SSoT modules a WORKSPACE-side __file__, mis-deriving ENGINE (Landmines 5/7).
from foxroots import WORKSPACE, _resolve_memory_dir  # SSoT roots + memory-dir resolver (E.1.2.B 0.1; D-89)
SPECS_DIR = WORKSPACE / "DESIGN_SPECS"
SKILLS_DIR = WORKSPACE / "claude-skills"
CLAUDE_MD = WORKSPACE / "CLAUDE.md"
MEMORY_DIR = _resolve_memory_dir()

CONCERN_LABEL = {
    "pre-coding-gate": "Pre-coding plan verification",
    "shape-audit": "SHAPE audits (design-layer)",
    "impl-detail-audit": "IMPLEMENTATION-DETAIL audits",
    "domain-audit": "DOMAIN audits",
    "anti-pattern-scan": "Anti-pattern scans",
    "post-coding": "Post-coding",
    "workflow": "Workflow",
    "scaffolding": "Scaffolding",
    "recurrence": "Recurrence",
}
CONCERN_ORDER = [
    "pre-coding-gate", "shape-audit", "impl-detail-audit", "domain-audit",
    "anti-pattern-scan", "post-coding", "workflow", "scaffolding", "recurrence",
]

TYPE_ORDER = [
    "refactor-pattern", "framework-pattern", "feature-pattern",
    "audit-methodology", "data-discipline", "concurrency-pattern",
    "wire-format-pattern", "doc-discipline", "meta-discipline",
    "plan-template", "ledger-template", "architecture-overview",
    # Promoted into the canonical order 2026-07-20 (TECH_DEBT-254): these are real one-off
    # categories that the render loop was silently dropping, not typos. `north-star` in
    # particular is cited by the active plan body while being unreachable from the catalog.
    "subsystem-design", "north-star", "input-space-taxonomy",
]


def parse_frontmatter(path):
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except (IOError, OSError):
        return None
    if not content.startswith("---\n"):
        return None
    end = content.find("\n---\n", 4)
    if end == -1:
        return None
    fields = {}
    for raw in content[4:end].split("\n"):
        # TOP-LEVEL keys only. Stripping first would erase the very indentation that marks a key
        # as NESTED, so `metadata:` → `  type: feedback` in memory-template.md was read as a
        # top-level `type: feedback` and rendered a phantom spec-type into the catalog. A parser
        # that flattens structure reports fields the document never declared (TECH_DEBT-254).
        if raw[:1] in (" ", "\t"):
            continue
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                fields[key.strip()] = [i.strip() for i in val[1:-1].split(",") if i.strip()]
            else:
                fields[key.strip()] = val
    return fields


def collect_skills():
    skills = {}
    malformed = []
    for skill_md in SKILLS_DIR.rglob("SKILL.md"):
        fm = parse_frontmatter(skill_md)
        if not fm:
            # NEVER silently drop a skill. A SKILL.md with no YAML frontmatter would
            # otherwise VANISH from CLAUDE.md + TAG_INDEX with no warning (close-session
            # hit exactly this 2026-06-02 — a stray harness "Base directory for this skill:"
            # preamble line clobbered its frontmatter, so it disappeared from the suite +
            # re-broke capture-audit Check 8 every time this generator ran). Register it
            # under the default concern so it stays in the index, and warn LOUD so it gets
            # fixed. Same silent-drop class as the always-loaded-doc truncation guard (WH-5).
            malformed.append(skill_md.parent.name)
            fm = {"name": skill_md.parent.name,
                  "description": "(MALFORMED — SKILL.md has no YAML frontmatter; fix it)"}
        skill_name = fm.get("name") or skill_md.parent.name
        skills[skill_name] = fm
    if malformed:
        print(f"  ⚠️  WARNING: {len(malformed)} skill(s) have NO YAML frontmatter — kept under the "
              f"default concern so they are not dropped, but FIX their SKILL.md frontmatter: "
              f"{', '.join(sorted(malformed))}")
    return skills


def collect_specs():
    specs = {}
    for md in SPECS_DIR.rglob("*.md"):
        if md.name in {"README.md", "TAG_INDEX.md"}:
            continue
        fm = parse_frontmatter(md)
        if not fm or fm.get("type") == "skill-check":
            continue
        rel = md.relative_to(WORKSPACE)
        specs[str(rel)] = fm
    return specs


def collect_memories():
    """Memories (machine-portable dir; D-89). Flat parser surfaces metadata.tags."""
    mems = {}
    if MEMORY_DIR is None:
        return mems
    for md in sorted(MEMORY_DIR.glob("*.md")):
        if md.name == "MEMORY.md":
            continue
        fm = parse_frontmatter(md)
        if fm:
            mems[f"memory/{md.name}"] = fm
    return mems


def gen_skill_suite_table(skills):
    by_concern = defaultdict(list)
    for name, fm in skills.items():
        concern = fm.get("concern", "workflow")
        by_concern[concern].append(name)
    lines = ["| Concern | Skills |", "|---|---|"]
    for concern in CONCERN_ORDER:
        skills_list = sorted(by_concern.get(concern, []))
        if not skills_list:
            continue
        formatted = " + ".join(f"`/{s}`" for s in skills_list)
        lines.append(f"| **{CONCERN_LABEL[concern]}** | {formatted} |")
    return "\n".join(lines)


def update_claude_md_skill_table(skills):
    new_table = gen_skill_suite_table(skills)
    with open(CLAUDE_MD, encoding="utf-8") as f:
        content = f.read()
    pattern = re.compile(
        r"(## Skill suite \(audit-driven discipline\)\n\nSkills group by concern.*?\n\n)"
        r"\| Concern \| Skills \|\n\|---\|---\|\n"
        r"(?:\|.*\|\n)+",
        re.DOTALL,
    )
    m = pattern.search(content)
    if not m:
        return False, "Could not locate Skill suite table in CLAUDE.md"
    new_content = pattern.sub(m.group(1) + new_table + "\n", content)
    return True, new_content


def gen_design_specs_readme(specs):
    by_type = defaultdict(list)
    for path, fm in specs.items():
        by_type[fm.get("type", "unknown")].append((path, fm))
    lines = [
        "# DESIGN_SPECS catalog",
        "",
        "**Auto-generated** by `tools/rebuild_doc_indexes.py`. Regenerate after adding/moving specs.",
        "",
        # Count what is actually RENDERED, never a separately-derived total. `len(by_type)`
        # included the "unknown" bucket, so the header could claim a type the catalog does not
        # show — the same claimed-vs-rendered gap in miniature, and the reason "15 types / 11
        # sections" went unnoticed for so long: two numbers, two sources, neither checking the
        # other. One source of truth, computed from the render set.
        f"Total: {sum(len(v) for t, v in by_type.items() if t != 'unknown')} specs across "
        f"{len([t for t in by_type if t != 'unknown' and by_type[t]])} types.",
        "",
        "Per-type catalog grouped by lifecycle stage. Cross-ref:",
        "- `doc-frontmatter-convention.md` (frontmatter schema)",
        "- `doc-tag-vocabulary.md` (tag canonical list)",
        "- CLAUDE.md § How to find anything (grep recipes)",
        "",
    ]
    # Render the CANONICAL types first, then EVERY remaining type alphabetically. The loop used
    # to iterate TYPE_ORDER alone, so any spec whose `type:` was not in that hardcoded list was
    # SILENTLY DROPPED from the catalog — the README claimed "15 types" while rendering 11, and
    # `in-code-doc-system-north-star.md` (cited by the active plan body) was one of the dropped
    # ones. A spec that exists but is unrendered is unreachable by every documented discovery
    # path, which is the same outcome as never having written it (TECH_DEBT-254).
    if by_type.get("unknown"):
        # Named, not dropped. These are docs with no top-level `type:` — usually a TEMPLATE whose
        # frontmatter is example content meant to be copied (memory-template.md), which is why
        # giving it spec frontmatter would corrupt the thing it exists to be. They are excluded
        # from the catalog and from its totals, but the exclusion is SAID so it stays a decision.
        print(f"[rebuild_doc_indexes] NOTE — {len(by_type['unknown'])} doc(s) with no top-level "
              f"`type:`, excluded from the catalog + its totals: "
              f"{', '.join(sorted(str(p).rsplit('/', 1)[-1] for p, _ in by_type['unknown']))}")
    extra_types = sorted(t for t in by_type if t not in TYPE_ORDER and t != "unknown")
    if extra_types:
        # LOUD, not silent: an unlisted type is either a real new category that belongs in
        # TYPE_ORDER, or a typo. Either way a human should see it — the failure mode being
        # closed is precisely a drop nobody noticed.
        print(f"[rebuild_doc_indexes] NOTE — {len(extra_types)} type(s) outside TYPE_ORDER, "
              f"rendered at the end; promote to TYPE_ORDER or fix the typo: {', '.join(extra_types)}")
    for spec_type in TYPE_ORDER + extra_types:
        rows = by_type.get(spec_type, [])
        if not rows:
            continue
        lines.append(f"## {spec_type} ({len(rows)} specs)")
        lines.append("")
        lines.append("| Spec | Stage | Tags | Sister count |")
        lines.append("|---|---|---|---|")
        for path, fm in sorted(rows):
            stage = fm.get("stage", "?")
            tags = fm.get("tags", [])
            sisters = fm.get("sister_specs", [])
            name = Path(path).stem
            tag_str = ", ".join(tags[:3])
            if len(tags) > 3:
                tag_str += f", +{len(tags) - 3}"
            lines.append(f"| `{path}` | {stage} | {tag_str} | {len(sisters)} |")
        lines.append("")
    return "\n".join(lines)


def gen_tag_index(specs, skills, memories=None):
    by_tag = defaultdict(set)
    by_surface = defaultdict(set)
    for path, fm in (memories or {}).items():   # memories: concern tags only (no surface axis)
        for t in fm.get("tags", []):
            by_tag[t].add(path)
    for path, fm in specs.items():
        for t in fm.get("tags", []):
            by_tag[t].add(path)
        for s in fm.get("surface", []):
            by_surface[s].add(path)
    for name, fm in skills.items():
        rel = f"claude-skills/{name}/SKILL.md"
        for t in fm.get("tags", []):
            by_tag[t].add(rel)
        for s in fm.get("surface", []):
            by_surface[s].add(rel)
    lines = [
        "# Tag → files index (auto-generated snapshot)",
        "",
        "**Auto-generated** by `tools/rebuild_doc_indexes.py`. Canonical reverse-lookup is `rg`:",
        "",
        "```bash",
        'rg -l "^tags:.*\\bframework-discipline\\b" DESIGN_SPECS/',
        'rg -l "^surface:.*\\bhot-path\\b"',
        "```",
        "",
        "This file is a snapshot for static browsing.",
        "",
        "## CONCERN tags",
        "",
    ]
    for tag in sorted(by_tag.keys()):
        files = sorted(by_tag[tag])
        lines.append(f"### {tag} ({len(files)} files)")
        lines.append("")
        for f in files:
            lines.append(f"- `{f}`")
        lines.append("")
    lines.append("## SURFACE tags")
    lines.append("")
    for tag in sorted(by_surface.keys()):
        files = sorted(by_surface[tag])
        lines.append(f"### {tag} ({len(files)} files)")
        lines.append("")
        for f in files:
            lines.append(f"- `{f}`")
        lines.append("")
    return "\n".join(lines)


def collect_code_tags():
    """Code-side twin of collect_specs: scan the ENGINE tree for [SCHEMA]-opted-in tag-blocks.
    PREFERS the foxtag CORE via foxtag_client (D-352 — parity §2 proved the core's inventory
    IDENTICAL to the Python collector's); falls back to the Python collector
    (collect_file_tags / engine_source_files) so a foxtag-less checkout still regenerates.
    ONE grammar either way (anti-Class-18). DOCS/ + schema_golden/ are skipped — copy-source
    and fixture, not conversions; the index reports CONVERSION state.
    Returns {engine-rel path: (units, tags)} for converted files only."""
    from check_code_tag_blocks import ENGINE
    if not (ENGINE / "Version.hpp").is_file():
        # Class-51 net: a mis-derived root yields a PLAUSIBLE-but-wrong index (scanned the
        # workspace tree, found only the golden fixture — the 2026-07-15 detonation). Fail LOUD.
        # Version.hpp = the engine-root marker (the workspace mirrors CoreFrameworks/, so a
        # dir check can't discriminate).
        raise RuntimeError(f"code-tag index refused: ENGINE={ENGINE} is not the engine tree "
                           f"(no Version.hpp) — set FOXML_ENGINE")

    def _skip(parts):
        return any(part in ("DOCS", "schema_golden") for part in parts)

    def _rel(f):
        try:
            return str(Path(f).relative_to(ENGINE))
        except ValueError:
            return str(f)

    out = {}
    try:
        from foxtag_client import core_available, inventory
        use_core = core_available()
    except ImportError:
        use_core = False
    if use_core:
        units, tags = inventory()
        for (f, t, n, ln) in units:
            if _skip(Path(f).parts):
                continue
            out.setdefault(_rel(f), ([], []))[0].append((t, n, ln))
        for (f, tg) in tags:
            if _skip(Path(f).parts):
                continue
            out.setdefault(_rel(f), ([], []))[1].append(tg)
        return out
    from check_code_tag_blocks import engine_source_files, collect_file_tags
    for f in engine_source_files():
        if _skip(f.parts):
            continue
        units, tags = collect_file_tags(f)
        if units or tags:
            out[_rel(f)] = (units, tags)
    return out


def gen_code_tag_index(code_tags):
    total_units = sum(len(u) for u, _ in code_tags.values())
    lines = [
        "# Code-tag index (auto-generated snapshot)",
        "",
        "**Auto-generated** by `tools/rebuild_doc_indexes.py --target code-tag-index` — the",
        "CODE-side twin of `DESIGN_SPECS/TAG_INDEX.md`. Canonical reverse-lookup is `rg` over",
        "the engine tree:",
        "",
        "```bash",
        "rg -l '\\[TAG\\]_\\[\\[SLOW_PATH' --glob '*.hpp'   # files tagged [SLOW_PATH]",
        "rg -n '\\[FUNCTION\\]_\\['                         # converted function blocks (with lines)",
        "```",
        "",
        "Snapshot for static browsing; regen via `/index-rebuild` (the `--check` currency guard",
        "reds a stale copy). Line numbers are deliberately OMITTED — file-level granularity only,",
        "so the snapshot stales when tags/units actually change, not on unrelated line drift;",
        "`rg` gives exact locations. The DOCS/ template corpus is excluded (copy-source, not a",
        "conversion).",
        "",
        f"Converted files: {len(code_tags)} · unit blocks: {total_units}",
        "",
        "## [TAG] values → files",
        "",
    ]
    by_tag = defaultdict(set)
    for rel, (_, tags) in code_tags.items():
        for t in tags:
            by_tag[t].add(rel)
    if not by_tag:
        lines.append("*(none yet — fills as E.1.2.A conversion lands)*")
        lines.append("")
    for tag in sorted(by_tag):
        files = sorted(by_tag[tag])
        lines.append(f"### {tag} ({len(files)} files)")
        lines.append("")
        for f in files:
            lines.append(f"- `{f}`")
        lines.append("")
    lines.append("## Unit blocks by [TYPE]")
    lines.append("")
    by_type = defaultdict(set)
    for rel, (units, _) in code_tags.items():
        for utype, name, _lineno in units:
            by_type[utype].add((name, rel))
    if not by_type:
        lines.append("*(none yet)*")
        lines.append("")
    for utype in sorted(by_type):
        rows = sorted(by_type[utype])
        lines.append(f"### {utype} ({len(rows)})")
        lines.append("")
        for name, rel in rows:
            lines.append(f"- `{name}` — `{rel}`")
        lines.append("")
    return "\n".join(lines)


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--target", choices=["claude-md", "readme", "tag-index", "code-tag-index", "all"],
                   default="all")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--check", action="store_true",
                   help="CURRENCY GUARD: exit 1 if any index is STALE (a regen would change it); "
                        "writes nothing. Closes the gap where a spec is added but the index isn't rebuilt.")
    args = p.parse_args()

    skills = collect_skills()
    specs = collect_specs()
    memories = collect_memories()
    print(f"Loaded {len(skills)} skills + {len(specs)} DESIGN_SPECS + {len(memories)} memories")

    stale = []  # populated only in --check mode

    if args.target in ("claude-md", "all"):
        ok, result = update_claude_md_skill_table(skills)
        if not ok:
            print(f"ERROR: {result}", file=sys.stderr)
        elif args.check:
            if result != _read(CLAUDE_MD):
                stale.append("CLAUDE.md skill suite table")
        elif args.dry_run:
            print("\n=== CLAUDE.md skill suite (proposed) ===")
            print(gen_skill_suite_table(skills))
        else:
            with open(CLAUDE_MD, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"Updated CLAUDE.md skill suite table")

    if args.target in ("readme", "all"):
        readme_content = gen_design_specs_readme(specs)
        readme_path = SPECS_DIR / "README.md"
        if args.check:
            if readme_content != _read(readme_path):
                stale.append("DESIGN_SPECS/README.md")
        elif args.dry_run:
            print("\n=== DESIGN_SPECS/README.md (first 60 lines) ===")
            print("\n".join(readme_content.split("\n")[:60]))
        else:
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)
            print(f"Wrote {readme_path}")

    if args.target in ("tag-index", "all"):
        tag_content = gen_tag_index(specs, skills, memories)
        tag_path = SPECS_DIR / "TAG_INDEX.md"
        if args.check:
            if tag_content != _read(tag_path):
                stale.append("DESIGN_SPECS/TAG_INDEX.md")
        elif args.dry_run:
            print("\n=== TAG_INDEX.md (first 50 lines) ===")
            print("\n".join(tag_content.split("\n")[:50]))
        else:
            with open(tag_path, "w", encoding="utf-8") as f:
                f.write(tag_content)
            print(f"Wrote {tag_path}")

    if args.target in ("code-tag-index", "all"):
        ct_content = gen_code_tag_index(collect_code_tags())
        ct_path = WORKSPACE / "DOCS" / "CODE_TAG_INDEX.md"
        if args.check:
            if ct_content != _read(ct_path):
                stale.append("DOCS/CODE_TAG_INDEX.md")
        elif args.dry_run:
            print("\n=== DOCS/CODE_TAG_INDEX.md (first 40 lines) ===")
            print("\n".join(ct_content.split("\n")[:40]))
        else:
            with open(ct_path, "w", encoding="utf-8") as f:
                f.write(ct_content)
            print(f"Wrote {ct_path}")

    if args.check:
        if stale:
            print("STALE — out of date (run `python3 tools/rebuild_doc_indexes.py` to fix): "
                  + ", ".join(stale), file=sys.stderr)
            return 1
        print("✅ indexes current")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
