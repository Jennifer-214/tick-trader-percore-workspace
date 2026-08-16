#!/usr/bin/env python3
"""check_meta_registry.py — codebase-wide FOREACH_REGISTRY cross-check (WIP2d-1.B.0b).

Closes Shortsighted #2 (meta-registry applied one ship early; cross-references were
documentation-only until .F.4d). This script enforces the discipline NOW: every X-macro
registry in the codebase MUST have a row in FOREACH_REGISTRY (CoreFrameworks/MetaRegistry.hpp).
Adding a new registry without registering it FAILS the build.

Pulls forward .F.4d H15 codification one ship early per CLAUDE.md item 31 framework discipline.

Checks performed:
  1. Every `#define FOREACH_\\w+\\(X\\)` in the codebase has a matching row in FOREACH_REGISTRY
  2. Every row in FOREACH_REGISTRY corresponds to an actual `#define` somewhere
  3. LEVEL/PARENT discipline: LEVEL > 0 rows have PARENT that exists in FOREACH_REGISTRY OR is ROOT_NONE

Exit codes:
  0 = all checks pass
  1 = one or more checks failed (build aborted)
  2 = script error / file missing

Best-effort heuristic: regex-based grep of #define lines. Macros defined via `#define FOREACH_<NAME>(X)`
are detected; unusual definitions (e.g., conditional compilation, macro-generated macro names) are out of
scope. Pairs with the X-macro struct generation discipline for layered defense.

Cross-references:
  - DESIGN_SPECS/meta-registry-pattern-for-codebase-registry-discipline.md
  - CoreFrameworks/MetaRegistry.hpp (the FOREACH_REGISTRY definition)
  - tools/check_per_node_registry_integrity.py (sister script for per-core surface)
"""

import re
import sys
from pathlib import Path

# Engine root = the CANONICAL machine-portable resolver from check_doc_metadata (honors $FOXML_ENGINE +
# recovers when __file__ landed WORKSPACE-side via the tools/ symlink, shape-checked on Version.hpp —
# Landmine 5; feedback_machine_portable_resolver_for_committed_tool_paths). This tool was the lone STRAGGLER
# that rolled its own `Path(__file__).parent.parent`, which false-`exit 2`'d ("MetaRegistry.hpp not found")
# when invoked via the workspace path (the workspace pre-commit) where that parent resolves to the WORKSPACE
# (no CoreFrameworks/). Switched to the SSoT resolver 2026-07-19 so it resolves identically to every other
# engine-scanning tool (check_code_tag_blocks / check_schema_version / check_cache_layout all import ENGINE).
sys.path.insert(0, str(Path(__file__).absolute().parent))
from check_doc_metadata import ENGINE               # noqa: E402  (the one engine-root SSoT)
REPO_ROOT = ENGINE
META_REG  = REPO_ROOT / "CoreFrameworks/MetaRegistry.hpp"

# Directories to scan for FOREACH_<X> macro definitions
SCAN_DIRS = [
    "CoreFrameworks",
    "MemHeaders",
    "ML_Headers",
    "Strategies",
    "DataStream",
    "Backtest",
    "FixedPoint",
    "GUI",
]

# Registries intentionally NOT registered (documented exemptions; out of scope for this CI)
EXEMPTIONS: set = set()
# Add names like {"FOREACH_HELPER_MACRO"} if they look like registries but aren't.


def fail(msg: str) -> None:
    print(f"[meta-registry-CI] ERROR: {msg}", file=sys.stderr)


def warn(msg: str) -> None:
    print(f"[meta-registry-CI] WARN: {msg}", file=sys.stderr)


def info(msg: str) -> None:
    print(f"[meta-registry-CI] {msg}")


def scan_codebase_foreach_macros() -> set:
    """Grep all #define FOREACH_<NAME>(<param>) macro definitions in scan dirs. Returns set of names."""
    # Match ANY single-identifier macro param, not just literal `X`: action-parameterized
    # meta-walkers like FOREACH_<COHORT>_COHORT(BASE_X) are real X-macro registries enrolled
    # in FOREACH_REGISTRY, so the finder must see them too — else Check 2 false-positives a
    # registered-and-real macro as "no matching #define". Fixed .E Session-4 2026-05-30:
    # FOREACH_STAMP_BOUND_DERIVED_COHORT(BASE_X) (CfgGateRegistry.hpp:227; used at 8 sites)
    # was a FALSE orphan under the old `\(X\)`-only regex (the TD-150 finding).
    pattern = re.compile(r'^#define\s+(FOREACH_\w+)\s*\(\s*\w+\s*\)', re.MULTILINE)
    macros = set()
    for d in SCAN_DIRS:
        d_path = REPO_ROOT / d
        if not d_path.is_dir():
            continue
        for f in d_path.rglob("*.hpp"):
            try:
                text = f.read_text()
            except Exception:
                continue
            for m in pattern.finditer(text):
                macros.add(m.group(1))
        for f in d_path.rglob("*.cpp"):
            try:
                text = f.read_text()
            except Exception:
                continue
            for m in pattern.finditer(text):
                macros.add(m.group(1))
    return macros


def parse_foreach_registry() -> dict:
    """Parse FOREACH_REGISTRY rows from MetaRegistry.hpp. Returns {name: (level, parent, domain)}.

    DOMAIN is QUOTED (D-421 step 5) rather than a bare token, because `RANGE:<lo,hi>` contains a
    comma and a bare-token column would split it into two columns. A row that fails to match is
    silently absent from this dict — which Check 2 would then report as a missing #define, so the
    failure mode of a regex/schema mismatch is LOUD (69 spurious names) rather than an empty pass."""
    if not META_REG.exists():
        fail(f"MetaRegistry.hpp not found at {META_REG}")
        sys.exit(2)
    text = META_REG.read_text()
    # Match: X(REGISTRY_NAME, LEVEL, PARENT, "DOMAIN", "description")
    pattern = re.compile(
        r'^\s+X\(\s*(\w+)\s*,\s*(\d+)\s*,\s*(\w+)\s*,\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\)',
        re.MULTILINE,
    )
    result = {}
    for m in pattern.finditer(text):
        name = m.group(1).strip()
        level = int(m.group(2))
        parent = m.group(3).strip()
        domain = m.group(4).strip()
        result[name] = (level, parent, domain)
    if not result:
        # A parse that yields ZERO rows is a schema/regex mismatch, never an empty registry.
        # Refusing here keeps it from degrading into "Check 1 says all 69 macros are unenrolled",
        # which is technically loud but names the wrong defect (Class 57 honesty-flattening).
        fail("FOREACH_REGISTRY parsed to ZERO rows — schema/regex mismatch, not an empty registry. "
             "Expected X(NAME, LEVEL, PARENT, \"DOMAIN\", \"description\").")
        sys.exit(2)
    return result


# --- DOMAIN vocabulary (D-421 step 5) -----------------------------------------------------------
# Prefixed forms take an argument after the colon; bare forms take none.
DOMAIN_PREFIXES = ("ENUM:", "STRUCT:", "COUNT:", "RANGE:", "FORMAT:", "PROSE:")
DOMAIN_BARE = ("SSOT",)
# Permitted ONLY for names in the shrinking baseline. Deliberately its own token rather than
# PROSE:"TODO" so an untriaged registry stays COUNTABLE instead of masquerading as a stated reason.
DOMAIN_MIGRATION = "UNCLASSIFIED"
DOMAIN_BASELINE = Path(__file__).resolve().parent / "lib" / "meta_registry_domain_baseline.txt"


def _load_domain_baseline() -> set:
    if not DOMAIN_BASELINE.exists():
        return set()
    return {ln.strip() for ln in DOMAIN_BASELINE.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")}


def evaluate_registry(codebase_macros: set, registry_entries: dict, domain_baseline: set = None):
    """Pure Check 1/2/3 comparison — the testable CORE that both `main()` and `--selftest` call (SSoT; no
    duplicated logic). Returns (failures, passes): lists of message strings; empty `failures` == clean.

    Check 1: every codebase FOREACH_<X> macro is registered (or exempted) — FATAL since .E.0.10 (the
      transition window closed; a NEW unregistered macro is a hard H15 CI failure).
    Check 2: every FOREACH_REGISTRY row has a real #define (registered-but-missing = a registry bug).
    Check 3: LEVEL/PARENT topology (LEVEL 0 => ROOT_NONE; LEVEL>0 => a real non-root parent).
    Check 4: DOMAIN declared + valid; UNCLASSIFIED only for baseline names (D-421 step 5)."""
    failures, passes = [], []
    domain_baseline = _load_domain_baseline() if domain_baseline is None else domain_baseline
    unregistered = codebase_macros - set(registry_entries) - EXEMPTIONS - {"FOREACH_REGISTRY"}
    if unregistered:
        failures += [f"Check 1 FAIL: codebase macro `{n}` not in FOREACH_REGISTRY — add a row in CoreFrameworks/MetaRegistry.hpp (or document as EXEMPTION in tools/check_meta_registry.py)" for n in sorted(unregistered)]
    else:
        passes.append("Check 1 PASS: all codebase FOREACH_<X> macros registered in FOREACH_REGISTRY (or exempted)")
    missing = set(registry_entries) - codebase_macros - {"FOREACH_REGISTRY"}
    if missing:
        failures.append(f"Check 2 FAIL: FOREACH_REGISTRY rows have no matching #define in codebase: {sorted(missing)} — delete the row OR add the missing #define")
    else:
        passes.append(f"Check 2 PASS: all {len(registry_entries)} FOREACH_REGISTRY rows match a real #define")
    issues = []
    for name, (level, parent, _domain) in registry_entries.items():
        if level == 0:
            if parent != "ROOT_NONE":
                issues.append(f"  {name}: LEVEL=0 but PARENT='{parent}' (expected ROOT_NONE for codebase-wide root)")
        else:
            if parent == "ROOT_NONE":
                issues.append(f"  {name}: LEVEL={level} but PARENT=ROOT_NONE (expected non-root parent for LEVEL > 0)")
            elif parent not in registry_entries and parent != "FOREACH_REGISTRY":
                issues.append(f"  {name}: PARENT='{parent}' not found in FOREACH_REGISTRY")
    if issues:
        failures.append("Check 3 FAIL: LEVEL/PARENT discipline violations:\n" + "\n".join(issues))
    else:
        passes.append(f"Check 3 PASS: LEVEL/PARENT discipline valid across {len(registry_entries)} rows")

    # --- Check 4: DOMAIN declared + valid (D-421 step 5) ----------------------------------------
    # The complement question, made uniform. Check 1 asks it of the CODEBASE ("is every macro
    # enrolled?"); this asks it of each registry's ROWS ("are these all the rows?") by requiring
    # each to name the set it is supposed to exhaust. Declaring NOTHING is the failure — that is the
    # whole rule, and it is what would have caught FOREACH_HALT_REASON / FOREACH_BACKTEST_METRIC /
    # FOREACH_LIVES_IN_STRUCT at introduction.
    bad, stale_baseline, unclassified = [], [], []
    for name, (_level, _parent, domain) in sorted(registry_entries.items()):
        if domain == DOMAIN_MIGRATION:
            if name in domain_baseline:
                unclassified.append(name)
            else:
                bad.append(f"  {name}: DOMAIN=UNCLASSIFIED but NOT in the migration baseline "
                           f"({DOMAIN_BASELINE.name}). A NEW registry must declare a real domain — "
                           f"SSOT / ENUM: / STRUCT: / COUNT: / RANGE: / FORMAT: / PROSE:<why-not>. "
                           f"Adding the name to the baseline to silence this is the one move that "
                           f"defeats the check; classify it instead.")
        elif domain in DOMAIN_BARE:
            pass
        elif any(domain.startswith(p) for p in DOMAIN_PREFIXES):
            if not domain.split(":", 1)[1].strip():
                bad.append(f"  {name}: DOMAIN='{domain}' has an EMPTY argument — "
                           f"'{domain.split(':', 1)[0]}:' must name the thing to diff against "
                           f"(a bare prefix is a claim no checker can act on).")
        elif not domain:
            bad.append(f"  {name}: DOMAIN is EMPTY. Declaring nothing is the failure this check "
                       f"exists for; use PROSE:<reason> if the domain genuinely is not computable.")
        else:
            bad.append(f"  {name}: DOMAIN='{domain}' is not a known form. Valid: "
                       f"{', '.join(DOMAIN_BARE)} / {' / '.join(DOMAIN_PREFIXES)} "
                       f"(+ UNCLASSIFIED for baselined migration rows only). Widening this "
                       f"vocabulary is a review decision, not a local edit.")
    # A baseline naming a registry that no longer carries UNCLASSIFIED is STALE — it silently
    # re-permits the marker if that registry ever regresses. Same shape as the partition guard's
    # STALE-EXEMPT leg: the guard's own INPUT must not be allowed to rot.
    stale_baseline = sorted(domain_baseline - {n for n, (_l, _p, d) in registry_entries.items()
                                               if d == DOMAIN_MIGRATION})
    if bad:
        failures.append("Check 4 FAIL: DOMAIN declaration violations (D-421 step 5):\n" + "\n".join(bad))
    if stale_baseline:
        failures.append(f"Check 4 FAIL: {DOMAIN_BASELINE.name} names {len(stale_baseline)} registr"
                        f"{'y' if len(stale_baseline) == 1 else 'ies'} that no longer carry "
                        f"UNCLASSIFIED — delete the line(s), the migration is done for them: "
                        f"{stale_baseline}")
    if not bad and not stale_baseline:
        classified = len(registry_entries) - len(unclassified)
        passes.append(f"Check 4 PASS: DOMAIN valid across {len(registry_entries)} rows "
                      f"({classified} classified, {len(unclassified)} baselined-pending)")
    return failures, passes


def main() -> int:
    info("scanning codebase for FOREACH_<X> macros + cross-checking against FOREACH_REGISTRY...")
    codebase_macros = scan_codebase_foreach_macros()
    info(f"  found {len(codebase_macros)} FOREACH_<X> macros in codebase")
    registry_entries = parse_foreach_registry()
    info(f"  found {len(registry_entries)} entries in FOREACH_REGISTRY")
    failures, passes = evaluate_registry(codebase_macros, registry_entries)
    for p in passes:
        info(p)
    for f in failures:
        fail(f)
    if failures:
        fail(f"meta-registry check FAILED with {len(failures)} violations")
        return 1
    info("all meta-registry structural checks PASS — codebase-wide registry discipline intact")
    return 0


def _selftest() -> int:
    """D-137 discoverable negative self-test (teeth): each Check flags its own violation + a clean set
    passes, AND the canonical ENGINE resolver LOCATES the real registry — the regression guard for the
    2026-07-19 canonical-resolver fix (the straggler that false-`exit 2`'d from the workspace path)."""
    NB = set()  # no baselined names — every fixture below declares its own domain explicitly
    clean = {"FOREACH_ROOT":  (0, "ROOT_NONE",     "SSOT"),
             "FOREACH_CHILD": (1, "FOREACH_ROOT",  "STRUCT:Foo")}
    f, _ = evaluate_registry({"FOREACH_ROOT", "FOREACH_CHILD", "FOREACH_ORPHAN"}, clean, NB)
    assert any("FOREACH_ORPHAN" in m for m in f), "Check 1 teeth: an unregistered macro was not flagged"
    f, _ = evaluate_registry({"FOREACH_ROOT"}, clean, NB)      # FOREACH_CHILD row present but no #define
    assert any("FOREACH_CHILD" in m for m in f), "Check 2 teeth: a registry row w/o #define was not flagged"
    f, _ = evaluate_registry({"FOREACH_BAD"}, {"FOREACH_BAD": (0, "NOT_ROOT_NONE", "SSOT")}, NB)
    assert any("Check 3" in m for m in f), "Check 3 teeth: a LEVEL/PARENT violation was not flagged"
    f, _ = evaluate_registry({"FOREACH_ROOT", "FOREACH_CHILD"}, clean, NB)
    assert not f, f"a clean set should PASS but flagged: {f}"

    # --- Check 4 teeth (D-421 step 5) --------------------------------------------------------
    # THE load-bearing leg: a NEW registry carrying the migration marker without being baselined
    # must RED. If this tooth ever stops firing, UNCLASSIFIED silently becomes a universal opt-out
    # and the whole column degrades into decoration — the Class-51 shape, in the check built to
    # close it.
    f, _ = evaluate_registry({"FOREACH_NEW"}, {"FOREACH_NEW": (0, "ROOT_NONE", "UNCLASSIFIED")}, NB)
    assert any("Check 4" in m for m in f), "Check 4 teeth: a NEW un-baselined UNCLASSIFIED row was not flagged"
    # ...and the SAME row IS permitted once baselined (the positive control, without which the
    # check could red on everything and still look rigorous).
    f, _ = evaluate_registry({"FOREACH_NEW"}, {"FOREACH_NEW": (0, "ROOT_NONE", "UNCLASSIFIED")}, {"FOREACH_NEW"})
    assert not f, f"a BASELINED UNCLASSIFIED row should PASS but flagged: {f}"
    # An unknown token must not slip through as if it were a domain.
    f, _ = evaluate_registry({"FOREACH_X"}, {"FOREACH_X": (0, "ROOT_NONE", "WHATEVER")}, NB)
    assert any("Check 4" in m for m in f), "Check 4 teeth: an unknown DOMAIN token was not flagged"
    # An EMPTY domain is the founding case — declaring nothing is the failure.
    f, _ = evaluate_registry({"FOREACH_X"}, {"FOREACH_X": (0, "ROOT_NONE", "")}, NB)
    assert any("Check 4" in m for m in f), "Check 4 teeth: an EMPTY DOMAIN was not flagged"
    # A bare prefix with no argument is a claim no checker can act on — `STRUCT:` names nothing.
    f, _ = evaluate_registry({"FOREACH_X"}, {"FOREACH_X": (0, "ROOT_NONE", "STRUCT:")}, NB)
    assert any("Check 4" in m for m in f), "Check 4 teeth: an empty-argument DOMAIN prefix was not flagged"
    # PROSE: with a real reason is VALID — it is the honest 'not computable', not an escape hatch.
    f, _ = evaluate_registry({"FOREACH_X"}, {"FOREACH_X": (0, "ROOT_NONE", "PROSE:no external set exists")}, NB)
    assert not f, f"PROSE:<reason> should PASS but flagged: {f}"
    # STALE baseline: a name baselined that no longer carries UNCLASSIFIED must RED. Without this,
    # the guard's own INPUT rots — a classified registry keeps a standing permission to regress.
    f, _ = evaluate_registry({"FOREACH_ROOT", "FOREACH_CHILD"}, clean, {"FOREACH_ROOT"})
    assert any("stale" in m.lower() or "no longer carry" in m for m in f), \
        "Check 4 teeth: a STALE baseline entry was not flagged"

    assert META_REG.exists(), f"ENGINE path-resolution regression: registry not found at {META_REG} (ENGINE={ENGINE}) — the 2026-07-19 canonical-resolver fix must keep locating it"
    # Non-vacuity against the REAL tree: the live regex must still parse rows, and the live baseline
    # must still name only UNCLASSIFIED rows. A schema/regex mismatch would otherwise surface as a
    # confusing Check-2 storm rather than as what it is.
    live = parse_foreach_registry()
    assert len(live) >= 60, f"real-tree non-vacuity: parsed only {len(live)} FOREACH_REGISTRY rows"
    assert all(len(v) == 3 for v in live.values()), "real-tree: rows did not parse as (level, parent, domain)"
    print("check_meta_registry.py --selftest: PASS — Check 1/2/3/4 teeth + clean-pass + "
          "baseline positive control + stale-baseline + real-tree non-vacuity + ENGINE path-resolution")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main())
