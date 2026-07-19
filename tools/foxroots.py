#!/usr/bin/env python3
"""foxroots.py — the ONE machine-portable repo-root resolver for the tool family (SSoT).

Every `tools/*.py` that needs the engine / workspace / memory root imports it FROM HERE
(`from foxroots import ENGINE, WORKSPACE, MEMORY_DIR`) instead of rolling its own
`Path(__file__).parent.parent` — the D-373/E.1.2.B "one core, no reinvention" discipline
applied to path resolution. A tool that derives its own root (or hardcodes an absolute
$HOME path) is the anti-pattern the import-from-core lint REDs — the 2026-07-19
`check_meta_registry` straggler + the portability-dead `check_conversion_completeness.py`
HARD gate that ran green only by path-literal-match (D-372/D-375).

Portability (per `feedback_machine_portable_resolver_for_committed_tool_paths`):
env-override -> sibling-default -> `Version.hpp` shape-check + sibling recovery ->
`.exists()`-guard. No $HOME hardcode in a committed tool -> runs on any clone / PC /
SSH-grid node. Extracted verbatim from `check_doc_metadata.py` (the prior de-facto SSoT,
which now imports from here); the Landmine-5 symlink caveat carries over unchanged because
`foxroots.py` sits at the same `tools/` depth.

Run standalone to introspect / smoke-test: `python3 tools/foxroots.py` prints the resolved
roots and exits non-zero if the engine marker is absent (i.e. we mis-resolved).
"""
import os
from pathlib import Path

# ENGINE: $FOXML_ENGINE override -> derive from THIS file's location (<engine>/tools/foxroots.py).
# .absolute() NOT .resolve(): tools/ is symlinked from the private workspace; .resolve() would follow
# the symlink -> ENGINE becomes the WORKSPACE -> Version.hpp absent -> a vacuous mis-resolve. (Landmine 5.)
ENGINE = Path(os.environ.get("FOXML_ENGINE") or Path(__file__).absolute().parent.parent)
if not (ENGINE / "Version.hpp").is_file():
    # Shape check: Version.hpp is the engine-root SSoT marker — present at the engine root, ABSENT in the
    # workspace (which mirrors CoreFrameworks/ etc. for module-doc backups, so a dir-name check can't
    # discriminate). Failing it means __file__ landed WORKSPACE-side (an importer whose sys.path entry
    # .resolve()d the tools/ symlink, or the workspace repo's own CI aggregator run) -> the parent-derivation
    # hit the WORKSPACE. Recover via the sibling-checkout convention; FOXML_ENGINE stays the explicit
    # override for non-sibling layouts. Shape-VERIFIED — the fallback is taken only when it IS the engine.
    _sibling_engine = ENGINE.parent / "FoxML_Trader_v2"
    if (_sibling_engine / "Version.hpp").is_file():
        ENGINE = _sibling_engine


def _resolve_workspace_root():
    env = os.environ.get("FOXML_WORKSPACE")
    if env and Path(env).exists():
        return Path(env)
    sibling = ENGINE.parent / "tick-trader-percore-workspace"
    return sibling if sibling.exists() else ENGINE


WORKSPACE = _resolve_workspace_root()


def _resolve_memory_dir():
    """Resolve the Claude Code institutional-memory dir (machine-portable; D-89 fork 1).

    Order: $FOXML_MEMORY_DIR override -> the local Claude Code projects store derived from the
    engine repo path -> None if absent. A multi-machine / SSH-grid node just exports
    FOXML_MEMORY_DIR (no $HOME baked into a committed tool). Cross-node memory *sync* is a
    separate concern.
    """
    override = os.environ.get("FOXML_MEMORY_DIR")
    if override:
        p = Path(override)
        return p if p.exists() else None
    # Claude Code keys its per-project memory dir by the project's absolute path with '/' and '_'
    # both mapped to '-'. Derive from ENGINE; do not hardcode $HOME.
    project_id = str(ENGINE).replace("/", "-").replace("_", "-")
    p = Path.home() / ".claude" / "projects" / project_id / "memory"
    return p if p.exists() else None


MEMORY_DIR = _resolve_memory_dir()


if __name__ == "__main__":
    import sys
    print(f"ENGINE     = {ENGINE}")
    print(f"WORKSPACE  = {WORKSPACE}")
    print(f"MEMORY_DIR = {MEMORY_DIR}")
    # Non-vacuity smoke test: the resolved engine root MUST carry Version.hpp, else we mis-resolved.
    ok = (ENGINE / "Version.hpp").is_file()
    print(f"engine-marker Version.hpp present: {ok}")
    sys.exit(0 if ok else 2)
