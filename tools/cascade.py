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
  cascade.py registry <FOREACH_NAME>  ENUMERATE one registry macro's FULL footprint UPFRONT — role-classified
                        (DEFINITION / H15-ENROLLMENT / EXPANDER / REFERENCE), the compiler-BLIND sites
                        (tools/.githooks/) flagged, and the MetaRegistry enrollment status checked. The blast
                        radius for a registry rename/rewrite, so consumers (esp. the H15 enrollment + the
                        apparatus refs the build can't see) are found up front, not reactively.
                        Spec: DESIGN_SPECS/refactor-patterns/rename-cascade-enumeration-tooling.md § registry-mode.
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

# --- the rename token-set (RE-DERIVE per rename; this is the .E.1.1 set) -----------------------------
# Each entry is a full REGEX. Matching rule (COMPLETENESS FIX 2026-06-21, a-class audit — closes a Class-33
# under-enumeration that missed CoreSlowState, the ~50 core_<stat> field family, g_per_core_* infra, embedded
# *_core_id, the *_cores node-count family, EventLoopAggregates.hpp, guard macros, format-string keys):
# tokens match at a SUB-WORD boundary — `(?<![A-Za-z0-9])` ALLOWS a preceding `_` (so embedded compounds like
# `origin_core_id` / `g_per_core_cfg` / `saved_num_execution_cores` ARE caught) but BLOCKS a preceding alnum
# (so `score`/`record`/`encore` are NOT). FAMILY patterns (not a hand-list) so a new `core_<stat>` field or
# `Core<Word>` type cannot silently escape. PRESERVE is applied to the matched text; overlap-dedup (Class-36).
RENAME_TOKEN_RX = [
    # explicit macros / consts (longest — win the overlap-dedup for clear reporting)
    r"(?<![A-Za-z0-9])FOREACH_PER_CORE[A-Za-z0-9_]*",
    r"(?<![A-Za-z0-9])FOREACH_CORE[A-Za-z0-9_]*",
    r"(?<![A-Za-z0-9])MAX_EXECUTION_CORES",
    r"(?<![A-Za-z0-9])MAX_GUI_CORES",
    r"(?<![A-Za-z0-9])num_execution_cores",
    # family patterns — the Class-33 completeness fix
    r"(?<![A-Za-z0-9])CORE_[A-Z][A-Za-z0-9_]*",     # CORE_STATE_FLAG/_CTX/_MODEL_*/_KILL*/_BUDGET + guard macros
    r"(?<![A-Za-z0-9])PER_CORE[A-Za-z0-9_]*",        # PER_CORE_* + the PER_CORE_STATE_FLAGS_REGISTRY_HPP guard
    r"(?<![A-Za-z0-9])PerCore[A-Za-z0-9_]*",         # PerCoreCfg/Overrides/Snap/FieldDef/StateFlagsRegistry
    r"(?<![A-Za-z0-9])Core[A-Z][A-Za-z0-9_]*",       # CoreContext/CoreSlowState/CoreModelZoo/CoreSnap/CoreLatency*
    r"(?<![A-Za-z0-9])per_core[A-Za-z0-9_]*",        # per_core_* + g_per_core_* (preceded by _)
    r"(?<![A-Za-z0-9])core_[a-z][A-Za-z0-9_]*",      # core_id/idx + the ~50-member core_<stat> field family
    r"\b[A-Za-z][A-Za-z0-9_]*_cores\b",              # num_cores/effective_cores/registered_cores/n_cores/...
    r"\.cores\[",                                    # .cores[ member access
    r"core_%[0-9A-Za-z]",                            # core_%d / %score_%u operator-facing key format strings
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

_compiled = [re.compile(rx) for rx in RENAME_TOKEN_RX]


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
            # collect all matches, then Class-36 overlap-resolution: sort by (start asc, longest first),
            # greedily accept non-overlapping spans (an inner token contained in a longer one is skipped —
            # CORE_CFG_FIELD inside FOREACH_PER_CORE_CFG_FIELD; but core_id inside origin_core_id is its OWN
            # disjoint span and IS kept).
            spans = []
            for rx in _compiled:
                for m in rx.finditer(line):
                    spans.append((m.start(), m.end(), m.group(0)))
            spans.sort(key=lambda t: (t[0], -(t[1] - t[0])))
            last_end = -1
            for start, end, ident in spans:
                if start < last_end:
                    continue
                last_end = end
                if _preserved(ident):
                    preserved_n += 1
                    continue
                worklist.setdefault(_bucket(rel), {}).setdefault(rel, []).append((i, ident))
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


def _registry_footprint(name):
    """Footprint of a registry macro `name` across the FULL surface (engine + apparatus + docs).
    Returns (roles, enrolled, scanned): roles = {ROLE: [(rel, line_no, bucket, text)]} with ROLE ∈
    {DEFINITION, ENROLLMENT, EXPANDER, REFERENCE}; enrolled = has an H15 MetaRegistry `X(name, ...)`
    row; scanned = files read. Reuses the rename-mode scan infra (iter_files / _bucket / _excluded)."""
    tok_rx    = re.compile(r'(?<![A-Za-z0-9_])' + re.escape(name) + r'(?![A-Za-z0-9_])')
    def_rx    = re.compile(r'#\s*define\s+' + re.escape(name) + r'\b')
    enroll_rx = re.compile(r'\bX\s*\(\s*' + re.escape(name) + r'\s*,')   # MetaRegistry X(FOREACH_*, ...) row
    call_rx   = re.compile(re.escape(name) + r'\s*\(')                   # FOREACH_*(...) expansion / walk
    roles = {"DEFINITION": [], "ENROLLMENT": [], "EXPANDER": [], "REFERENCE": []}
    enrolled, scanned = False, 0
    for f in iter_files(include_docs=True):
        try:
            rel = str(f.relative_to(ENGINE))
        except ValueError:
            rel = str(f)
        if _excluded(rel):
            continue
        try:
            lines = f.read_text(errors="replace").splitlines()
        except Exception:
            continue
        scanned += 1
        for i, line in enumerate(lines, 1):
            if not tok_rx.search(line):
                continue
            if enroll_rx.search(line):
                role, enrolled = "ENROLLMENT", True
            elif def_rx.search(line):
                role = "DEFINITION"
            elif call_rx.search(line):
                role = "EXPANDER"
            else:
                role = "REFERENCE"
            roles[role].append((rel, i, _bucket(rel), line.strip()[:96]))
    return roles, enrolled, scanned


def cmd_registry(argv):
    name = argv[0] if argv else ""
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name):
        print("usage: cascade.py registry <FOREACH_NAME>   (a registry macro identifier)")
        return 2
    roles, enrolled, scanned = _registry_footprint(name)
    total   = sum(len(v) for v in roles.values())
    defined = bool(roles["DEFINITION"])
    print("=" * 78)
    print(f"cascade registry — upfront footprint of `{name}`  (ENUMERATE-ONLY; the human migrates)")
    print("=" * 78)
    print(f"scan: engine+apparatus+docs  ·  {scanned} file(s)  ·  {total} ref(s)")
    # H15 enrollment status — the exact thing a rename/rewrite silently drops (this session's miss)
    if defined and not enrolled:
        print("\n  XX H15: DEFINED but NOT enrolled in the MetaRegistry (no FOREACH_REGISTRY X-row) —")
        print("        test_meta_registry_coverage will FAIL. Add/fix the X(...) enrollment.")
    elif enrolled:
        print("\n  ok H15: enrolled in the MetaRegistry (FOREACH_REGISTRY).")
    else:
        print("\n  -- H15: no definition found here (a consumer-only name, or a typo).")
    for role in ("DEFINITION", "ENROLLMENT", "EXPANDER", "REFERENCE"):
        hits = roles[role]
        if not hits:
            continue
        blind = sum(1 for _, _, b, _ in hits if b == "TOOL-REGEX")
        tag = f"   <-- {blind} compiler-BLIND (the build won't catch these)" if blind else ""
        print(f"\n### {role} — {len(hits)} site(s){tag}")
        for rel, i, bucket, txt in hits:
            mark = " «BLIND»" if bucket == "TOOL-REGEX" else ""
            print(f"  {rel}:{i}{mark}  {txt}")
    print("\nNOTE: engine-source DEFINITION/EXPANDER sites are compiler-oracle'd (a rename slip red-builds).")
    print("      The «BLIND» sites (tools/.githooks/) + the H15 enrollment are the co-migrate-by-hand set.")
    print("      DERIVED names (NAME_COUNT / _AUTOPOPULATE / helper fns) are SEPARATE tokens — enumerate those too.")
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
        # (1c) NEW token-family positive controls (the a-class completeness fix — each family that closed a
        # Class-33 gap MUST be exercised, else the selftest is vacuously green for the very gap it closed)
        # + false-positive guards for the relaxed lookbehind (score/record/encore must NEVER match).
        (root / "CoreFrameworks" / "newclasses.hpp").write_text(
            "struct CoreSlowState {};\n"                          # Core[A-Z] CamelCase type
            "uint32_t core_wins; Money core_fees;\n"             # core_<stat> field family
            "int num_cores = 4; int effective_cores;\n"          # *_cores node-count family
            "int origin_core_id = ctx.core_id;\n"               # embedded *_core_id (preceded by _)
            "auto* p = &g_per_core_cfg_field_descriptors[0];\n"  # embedded per_core (g_ prefix)
            "#define CORE_MODEL_ZOO_HPP 1\n"                     # CORE_ guard macro
            'snprintf(b, n, "%s/core_%d.csv", d, c);\n'          # core_%d operator-facing format key
            "double score=1.0; int record_id=0; const char* encore=0;\n")  # FALSE-POS guards
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
        all_idents = [d for files in worklist.values() for lst in files.values() for _, d in lst]
        # (1c) NEW token-family controls — each MUST be caught (Class-33 completeness fix)
        for need in ("CoreSlowState", "core_wins", "num_cores", "CORE_MODEL_ZOO_HPP", "core_%d"):
            if not any(d == need for d in all_idents):
                failures.append(f"NEW-class control MISSED: '{need}' not flagged (token-family regression)")
        if not any(d.startswith("per_core_cfg") for d in all_idents):
            failures.append("embedded control MISSED: g_per_core_cfg_field_descriptors (per_core after '_') not flagged")
        # (1d) false-positive guards for the relaxed lookbehind: alnum-prefixed must NEVER match
        for bad in ("score", "record", "encore"):
            if any(bad in d for d in all_idents):
                failures.append(f"false positive: alnum-prefixed '{bad}' flagged (lookbehind too loose)")
        # (2) PRESERVE not flagged (no ExecutionCore/FoxML_Core/cpu_id in any bucket)
        for bad in ("ExecutionCore", "FoxML_Core", "cpu_id"):
            if any(d.startswith(bad) or d == bad for d in all_idents):
                failures.append(f"false positive: PRESERVE token '{bad}' was flagged")
        # (3) experiments/ excluded (its core_id / per_core_x must not appear)
        for b, files in worklist.items():
            for rel in files:
                if "experiments/per_core_sharding/" in rel:
                    failures.append(f"false positive: excluded path flagged ({rel})")
    # --- registry-mode teeth (the `registry` subcommand) — its OWN fixture tree ---
    with tempfile.TemporaryDirectory(dir=str(ENGINE), prefix=".cascade_regtest_") as td2:
        r2 = Path(td2)
        (r2 / "MemHeaders").mkdir(parents=True)
        (r2 / "CoreFrameworks").mkdir(parents=True)
        (r2 / "tools").mkdir(parents=True)
        (r2 / "MemHeaders" / "fakereg.hpp").write_text(
            "#define FOREACH_FAKE_REG(X) X(a,1) X(b,2)\n"
            "    FOREACH_FAKE_REG(SOME_WALKER)\n")                              # DEFINITION + EXPANDER
        (r2 / "CoreFrameworks" / "fakemeta.hpp").write_text(
            '    X(FOREACH_FAKE_REG                 , 1, FOREACH_REGISTRY, "fake") \\\n')  # ENROLLMENT (H15)
        (r2 / "tools" / "fakescan.py").write_text("# a tool that scans FOREACH_FAKE_REG via regex\n")  # BLIND
        (r2 / "MemHeaders" / "orphanreg.hpp").write_text("#define FOREACH_ORPHAN_REG(X) X(z,0)\n")   # unenrolled
        saved2 = ENGINE
        ENGINE = r2
        try:
            roles, enrolled, _ = _registry_footprint("FOREACH_FAKE_REG")
            _, orph_enrolled, _ = _registry_footprint("FOREACH_ORPHAN_REG")
        finally:
            ENGINE = saved2
        if not roles["DEFINITION"]:
            failures.append("registry: DEFINITION site not found")
        if not enrolled:
            failures.append("registry: H15 ENROLLMENT (MetaRegistry X-row) not detected")
        if not roles["EXPANDER"]:
            failures.append("registry: EXPANDER (walk) site not found")
        if not any(b == "TOOL-REGEX" for lst in roles.values() for _, _, b, _ in lst):
            failures.append("registry: compiler-BLIND tools/ ref not flagged (the unique value)")
        if orph_enrolled:
            failures.append("registry: orphan (unenrolled) reg falsely reported enrolled — H15 flag broken")
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
    if cmd == "registry":
        return cmd_registry(argv[1:])
    if cmd == "struct":
        return cmd_struct(argv[1:])
    if cmd in ("-h", "--help"):
        print(__doc__)
        return 0
    print(f"cascade.py: unknown subcommand '{cmd}' (expected: rename | registry | struct | --selftest)")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
