#!/usr/bin/env python3
"""cascade.py — the change-cascade tool (rename enumeration). TD-175a / D-240.

The operator's "cascade tool," answering "if I change X, what cascades?" — ON-DEMAND, ENUMERATE-ONLY.

  cascade.py rename     ENUMERATE every site a Core->Node-style token rename must touch, across engine
                        source PLUS the apparatus dirs the compiler can't see (tools/ build.sh .githooks/),
                        classified by rename-ship-methodology Phase-3 bucket, + the #include-cascade for the
                        file-basename renames + the expected-residual allowlist. PRINTS the worklist; it does
                        NOT mutate. (Gate R1: NO --apply over code — the compiler is the totality oracle for
                        code tokens [rename-ship-methodology Phase 4: human does ONE mechanical commit +
                        red-build]; a code --apply only adds a Class-36 silent-corruption surface.)
  cascade.py struct <T>  RESERVED -> .E.1.2 (the TD-175 AST struct-byte cascade, Tool A re-cut). Not built.

Why it exists: the standing .E.1.0 gates RED-build an engine-SOURCE rename slip (compiler oracle), but a
rename in tools/ / build.sh / .githooks/ commits GREEN on a stale regex (it goes silently dead —
rename-ship-methodology Phase-3 TOOL-REGEX bucket; RBP Class 51). This enumerates that compiler-blind surface
so the cohort co-migrates in the rename commit. The STANDING net for a *future* miss rides the existing
check_ guards (check_tools_inventory.py build.sh-scan; gate R2), NOT this tool.

Engine root via Path(__file__).absolute() — NOT .resolve() (LANDMINES 5/7: tools/ is a workspace symlink;
.resolve() would hunt engine source under the workspace). FOXML_ENGINE override points the scan at a temp
tree for --selftest. Spec: DESIGN_SPECS/refactor-patterns/rename-cascade-enumeration-tooling.md (v1.2).

Exit 0 = enumeration printed (rename) / reserved-notice (struct) / teeth pass (--selftest). 1 = selftest fail.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

ENGINE = Path(os.environ.get("FOXML_ENGINE") or Path(__file__).absolute().parent.parent)

# --- scan surface -----------------------------------------------------------------------------------
ENGINE_SRC_DIRS = ["CoreFrameworks", "Strategies", "ML_Headers", "Backtest", "DataStream",
                   "FixedPoint", "MemHeaders", "GUI"]
ENGINE_SRC_ROOT_FILES = ["main.cpp", "Version.hpp", "Limits.hpp"]
APPARATUS_DIRS = ["tools", ".githooks"]          # the compiler-blind surface = the unique value
APPARATUS_ROOT_FILES = ["build.sh"]
DOC_DIRS = ["DOCS", "DESIGN_SPECS", "plans/_cross-cutting", "claude-skills"]   # --docs opt-in
SRC_EXT = (".hpp", ".cpp", ".h")
APPARATUS_EXT = (".py", ".sh", ".txt")

# --- the rename token-set (RE-DERIVE counts per rename; this is the .E.1.1 set) ----------------------
# kind: "ident"   -> match OLD at an identifier-start boundary, capture the whole identifier
#       "literal" -> match OLD verbatim (member-access / quoted cfg-key)
RENAME_TOKENS = [
    ("FOREACH_PER_CORE_CFG_FIELD", "ident"),
    ("FOREACH_CORE_STATE_FLAG", "ident"),
    ("MASK_CORE_STATE", "ident"),
    ("CORE_STATE_FLAG", "ident"),
    ("CORE_CTX", "ident"),
    ("MAX_EXECUTION_CORES", "ident"),
    ("MAX_GUI_CORES", "ident"),
    ("num_execution_cores", "ident"),
    ("CoreContext", "ident"),          # also CoreContextDisplayMeta (both rename — Class-36 anchored)
    ("CoreModelZoo", "ident"),
    ("CoreLatencyStats", "ident"),
    ("CoreCtx", "ident"),
    ("PerCore", "ident"),
    ("per_core", "ident"),
    ("core_id", "ident"),
    ("core_idx", "ident"),
    (".cores[", "literal"),
    ('"core_', "literal"),             # cfg-key literal (engine + GUI parsers)
]

# PRESERVE: a captured identifier equal to / prefixed by one of these is NOT a rename site (longest-first).
# Most preserves work by simply NOT being a token (we never match bare `Core`/`core`); this is the safety net
# + the report of what we deliberately skipped.
PRESERVE_EXACT = {"ExecutionCore", "CoreFrameworks", "MULTICORE_TUI", "FoxML_Core", "cpu_id"}
PRESERVE_PREFIX = ("ExecutionCore",)   # ExecutionCore_Tick, ExecutionCore_* — the hot-path engine

# Path substrings whose hits are EXPECTED residuals (excluded from the worklist; counted separately).
EXCLUDE_PATHS = (
    "experiments/per_core_sharding/",   # real dir, valid own tokens (8-agent PRESERVE)
    "tools/cascade.py",                 # self-ref: this tool discusses the tokens
    "tools/cascade_selftest.sh",        # self-ref: the teeth wrapper names the fixture tokens
    "rename-cascade-enumeration-tooling.md",
    "rename-cascade-enumeration-freeze",  # the frozen worklist (verbatim tool output)
    "rename-ship-methodology.md",
    "E.1.1-core-node-rename.md",        # the rename plan body
)

# The 6 file-basename renames -> the #include-cascade tooth.
FILE_RENAMES = {
    "CoreModelZoo": "NodeModelZoo",
    "CoreCtxInitRegistry": "NodeCtxInitRegistry",
    "CoreCtxSummaryFieldRegistry": "NodeCtxSummaryFieldRegistry",
    "CoreStateFlagRegistry": "NodeStateFlagRegistry",
    "PerCoreStateFlagsRegistry": "PerNodeStateFlagsRegistry",
    "CoreLatencyStats": "NodeLatencyStats",
}

# POST-rename expected residuals (informational; the V-class allowlist so a residual grep != 0 is OK).
POST_RENAME_ALLOWLIST_NOTE = "node_id x3 @ CoreFrameworks/EngineSharded/Run.hpp:202/213 (helper commit 2b8bd6c — the intended target namespace, NOT a foreign collision)"

IDENT = "A-Za-z0-9_"
_compiled = []
for old, kind in RENAME_TOKENS:
    if kind == "ident":
        # not preceded by an ident char; capture OLD + any trailing ident chars (the whole identifier)
        rx = re.compile(r"(?<![%s])(%s[%s]*)" % (IDENT, re.escape(old), IDENT))
    else:
        rx = re.compile(re.escape(old))
    _compiled.append((old, kind, rx))


def _bucket(relpath: str) -> str:
    p = relpath
    if p.startswith("tools/") or p == "build.sh" or p.startswith(".githooks/"):
        return "TOOL-REGEX"          # compiler-blind — the unique value
    if p.endswith(SRC_EXT):
        return "CODE-TOKEN"          # compiler-oracle'd
    if any(h in p for h in ("changelog", "CHANGELOG", "postmortem", "decision-log",
                            "handoffs/", "plan_checks/", "/archived/")):
        return "HISTORICAL-PRESERVE"
    if p.endswith(".md"):
        return "DOC"
    return "OTHER"


def _preserved(ident: str) -> bool:
    return ident in PRESERVE_EXACT or any(ident.startswith(pfx) for pfx in PRESERVE_PREFIX)


def _excluded(relpath: str) -> bool:
    return any(x in relpath for x in EXCLUDE_PATHS)


def iter_files(include_docs: bool):
    roots = []
    for d in ENGINE_SRC_DIRS:
        roots.append((ENGINE / d, SRC_EXT))
    for d in APPARATUS_DIRS:
        roots.append((ENGINE / d, APPARATUS_EXT))
    if include_docs:
        for d in DOC_DIRS:
            roots.append((ENGINE / d, (".md",)))
    for base, exts in roots:
        if base.exists():
            for ext in exts:
                yield from sorted(base.rglob("*" + ext))
    for f in ENGINE_SRC_ROOT_FILES + APPARATUS_ROOT_FILES:
        p = ENGINE / f
        if p.exists():
            yield p


def find_hits(include_docs: bool):
    """Return (worklist, preserved_n, excluded_n) where worklist = {bucket: {relpath: [(line_no, ident)]}}."""
    worklist, preserved_n, excluded_n = {}, 0, 0
    for f in iter_files(include_docs):
        try:
            rel = str(f.relative_to(ENGINE))
        except ValueError:
            rel = str(f)
        if _excluded(rel):
            excluded_n += 1
            continue
        try:
            lines = f.read_text(errors="replace").splitlines()
        except Exception:
            continue
        for i, raw in enumerate(lines, 1):
            line = raw   # do NOT strip comments — a token in a // or # comment IS a rename site
                         # (a stale "Walks FOREACH_PER_CORE_CFG_FIELD" comment must update). The human
                         # triages CODE vs COMMENT vs HISTORICAL per rename-ship-methodology Phase 3.
            seen = set()   # dedupe overlapping token matches at the same start (core_id ⊃ core_idx)
            for old, kind, rx in _compiled:
                for m in rx.finditer(line):
                    if m.start() in seen:
                        continue
                    seen.add(m.start())
                    ident = m.group(1) if kind == "ident" else old
                    if kind == "ident" and _preserved(ident):
                        preserved_n += 1
                        continue
                    b = _bucket(rel)
                    worklist.setdefault(b, {}).setdefault(rel, []).append((i, ident))
    return worklist, preserved_n, excluded_n


def include_cascade():
    """Find #include sites + include-guard macros for the 6 file-basename renames."""
    hits = {}
    inc_rx = re.compile(r'#\s*include\s*[<"]([^">]+)[">]')
    for f in iter_files(include_docs=False):
        try:
            rel = str(f.relative_to(ENGINE))
        except ValueError:
            rel = str(f)
        if not rel.endswith(SRC_EXT) or _excluded(rel):
            continue
        try:
            text = f.read_text(errors="replace")
        except Exception:
            continue
        for i, raw in enumerate(text.splitlines(), 1):
            m = inc_rx.search(raw)
            if m:
                inc = m.group(1)
                for base in FILE_RENAMES:
                    if base in inc:
                        hits.setdefault(base, []).append((rel, i, inc))
    return hits


def cmd_rename(include_docs: bool):
    worklist, preserved_n, excluded_n = find_hits(include_docs)
    inc = include_cascade()
    order = ["CODE-TOKEN", "TOOL-REGEX", "DOC", "HISTORICAL-PRESERVE", "OTHER"]
    total = sum(len(v) for files in worklist.values() for v in files.values())
    print("=" * 78)
    print("cascade rename — ENUMERATE-ONLY worklist (the human does the rename; this is the plan)")
    print("=" * 78)
    print(f"scan: {'engine+apparatus+docs' if include_docs else 'engine+apparatus (use --docs for doc trees)'}"
          f"  ·  {total} hit(s)  ·  {preserved_n} PRESERVE-skipped  ·  {excluded_n} file(s) excluded")
    for b in order:
        files = worklist.get(b, {})
        if not files:
            continue
        n = sum(len(v) for v in files.values())
        tag = "  <-- compiler-BLIND; co-migrate THIS COMMIT (the unique value)" if b == "TOOL-REGEX" else ""
        print(f"\n### {b} — {n} hit(s) across {len(files)} file(s){tag}")
        for rel in sorted(files):
            idents = files[rel]
            uniq = sorted(set(d for _, d in idents))
            print(f"  {rel}  ({len(idents)}): {', '.join(uniq[:8])}{' …' if len(uniq) > 8 else ''}")
    print(f"\n### #include-cascade (6 file-basename renames -> NEW)")
    if inc:
        for base in sorted(inc):
            print(f"  {base} -> {FILE_RENAMES[base]}: {len(inc[base])} include site(s)")
            for rel, i, incpath in inc[base][:12]:
                print(f"      {rel}:{i}  {incpath}")
    else:
        print("  (none found — verify the basenames exist on disk)")
    print(f"\n### expected-residual ALLOWLIST (post-rename totality = match THIS, never '=0')")
    print(f"  - {POST_RENAME_ALLOWLIST_NOTE}")
    print(f"  - excluded paths (valid own tokens / self-ref / history): {', '.join(EXCLUDE_PATHS)}")
    print(f"\nNOTE: code rename = the human's ONE mechanical commit (compiler oracle, rename-ship-methodology")
    print(f"      Phase 4); docs via check_doc_rename_classification.py (Phase 5). This tool does NOT mutate.")
    return 0


def cmd_struct(args):
    print("cascade struct — RESERVED future subcommand (.E.1.2; the TD-175 AST struct-byte cascade, Tool A).")
    print("Not built. See DESIGN_SPECS/meta-disciplines/struct-change-cascade-impact-tooling.md (re-cut).")
    return 0


def selftest():
    """Non-vacuity teeth (Class 51): a positive control MUST be caught; false-positive guards MUST be spared."""
    global ENGINE
    failures = []
    with tempfile.TemporaryDirectory(dir=str(ENGINE), prefix=".cascade_selftest_") as td:
        root = Path(td)
        # planted POSITIVE control: a stale token in a tools/-shaped file (compiler-blind apparatus)
        (root / "tools").mkdir(parents=True)
        (root / "tools" / "fake_guard.py").write_text(
            'BODY = "FOREACH_PER_CORE_CFG_FIELD"\nx = cfg.core_id\n# per_core walker\n')
        # comment-resident positive control (regression lock — a // comment token IS a rename site;
        # the comment-strip miss that under-counted StampHelper.hpp by 626 sites must never return)
        (root / "CoreFrameworks").mkdir(parents=True)
        (root / "CoreFrameworks" / "commentsite.hpp").write_text(
            "// this comment Walks FOREACH_PER_CORE_CFG_FIELD + uses CoreContext\nint ok;\n")
        # false-positive guards: PRESERVE + excluded-path tokens that must NOT be flagged
        (root / "CoreFrameworks" / "preserve.hpp").write_text(
            "struct ExecutionCore {};\n// FoxML_Core sister project\nint cpu_id;\n")
        (root / "experiments" / "per_core_sharding").mkdir(parents=True)
        (root / "experiments" / "per_core_sharding" / "x.hpp").write_text("int core_id;\nint per_core_x;\n")
        old_engine = os.environ.get("FOXML_ENGINE")
        os.environ["FOXML_ENGINE"] = str(root)
        try:
            saved = ENGINE
            ENGINE = root
            worklist, preserved_n, excluded_n = find_hits(include_docs=False)
            ENGINE = saved
        finally:
            if old_engine is None:
                os.environ.pop("FOXML_ENGINE", None)
            else:
                os.environ["FOXML_ENGINE"] = old_engine
        tool = worklist.get("TOOL-REGEX", {})
        # (1) positive control caught + classified TOOL-REGEX
        hit_idents = [d for f, lst in tool.items() for _, d in lst]
        if not any("FOREACH_PER_CORE_CFG_FIELD" in d for d in hit_idents):
            failures.append("positive control MISSED: planted FOREACH_PER_CORE_CFG_FIELD not flagged TOOL-REGEX")
        if not any(d == "core_id" for d in hit_idents):
            failures.append("positive control MISSED: planted core_id not flagged")
        # (1b) comment-resident control: a token in a // comment MUST be caught (regression lock vs the
        # comment-strip miss that under-counted by 626 sites)
        code_idents = [d for f, lst in worklist.get("CODE-TOKEN", {}).items() for _, d in lst]
        if not any("CoreContext" in d for d in code_idents):
            failures.append("comment-resident control MISSED: // comment token (CoreContext) not flagged — comment-strip regression")
        # (2) PRESERVE not flagged (no ExecutionCore/FoxML_Core/cpu_id in any bucket)
        all_idents = [d for files in worklist.values() for lst in files.values() for _, d in lst]
        for bad in ("ExecutionCore", "FoxML_Core", "cpu_id"):
            if any(d.startswith(bad) or d == bad for d in all_idents):
                failures.append(f"false positive: PRESERVE token '{bad}' was flagged")
        # (3) experiments/ excluded (its core_id / per_core_x must not appear)
        for b, files in worklist.items():
            for rel in files:
                if "experiments/per_core_sharding/" in rel:
                    failures.append(f"false positive: excluded path flagged ({rel})")
    if failures:
        print("XX cascade --selftest FAIL:")
        for f in failures:
            print("   - " + f)
        return 1
    print("OK cascade --selftest PASS — positive control caught (TOOL-REGEX); PRESERVE + experiments/ spared.")
    return 0


def main(argv):
    if not argv:
        print(__doc__.strip().splitlines()[0])
        print("usage: cascade.py {rename [--docs] | struct <T> | --selftest}")
        return 0
    cmd = argv[0]
    if cmd == "--selftest":
        return selftest()
    if cmd == "rename":
        return cmd_rename(include_docs="--docs" in argv[1:])
    if cmd == "struct":
        return cmd_struct(argv[1:])
    if cmd in ("-h", "--help"):
        print(__doc__)
        return 0
    print(f"cascade.py: unknown subcommand '{cmd}' (expected: rename | struct | --selftest)")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
