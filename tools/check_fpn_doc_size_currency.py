#!/usr/bin/env python3
"""check_fpn_doc_size_currency.py — guard: docs stating a single FPN<...>'s byte size must match the code.

M7 structural-enforcement guard. The size of `FPN<F=64>` is a load-bearing fact that recurs across the
prose docs (CLAUDE.md hot-path discipline, DESIGN_SPECS field-layout examples, struct-field comments). When
Ship-A flipped FPN<64> 24B sign-magnitude -> 16B two's-complement (`v5.15.5.F.4d.1.E.0.7`), ~12 docs were
left stating the stale "24B" — a manual find/replace cohort, and manual convention proved insufficient at
that many sites (this is exactly the recurrence-despite-codification trigger for escalating to a CI guard
per `feedback_structural_enforcement_when_memory_insufficient` (M7)). A wrong byte-size in a doc isn't a
crash — it silently mis-teaches the next reader (human or AI) the memory layout of the money/determinism
core, which is the worst kind of doc rot on a capital-bearing surface. This guard turns "keep the FPN size
in docs current" from a no-thought-each-time convention into a mechanical class-close: a guard protects the
whole class forever; the fix is one instance.

SSoT: the canonical size is parsed FROM THE CODE — `static_assert(sizeof(FPN<64>) == N` in
`FixedPoint/FixedPointN.hpp` (the engine repo). The docs are checked against that, never against a number
hardcoded here, so the guard auto-tracks the next flip (Ship-B decimal money) with zero edits. If the
canonical assert can't be found, the guard prints WARN + exits 0 (it never false-fails on a parse miss).

What it flags: a line that states a SINGLE FPN<...>'s byte size != canonical —
  (a) struct-field comment   `FPN<...> name;  // N bytes`  /  `// NB`
  (b) prose                  `FPN<...> = NB`  /  `FPN<...> is N bytes`  /  `each FPN<...> ... N bytes`
  (c) sizeof assertion       `sizeof(FPN<...>) == N`
Only a SINGLE FPN's size is in scope: FPN PAIRS/MULTIPLES are valid (two FPN fields = 32B == 2x16), so the
byte number is restricted to a plausible-single-FPN range and `FPN<` proximity is required on the SAME line
(this is also what keeps non-FPN 24B's — ThompsonArmState[8], `3xdouble` Record, `6 x int = 24B` — out).

False-positive surface (M3 — the historical record is NEVER drift):
  - whole files: changelogs/ · postmortem · decision-log · HOT_PATH_CHANGELOG · recurring-bug-patterns ·
    LATENCY_OPTIMIZATION · CHANGELOG.md  (these document the PAST on purpose).
  - lines (or their 12-line preceding window — markers cluster at the top of a worked-example/code block):
    HISTORICAL · superseded · obsolete · former/formerly · pre-Ship-A · `was NNB`/`was NN B` ·
    an `NN -> MM`/`NN→MM` byte transition · `sign-mag →` · `(unchanged)` size-restatement, OR the old
    sign-magnitude FPN layout members in the window (`uint64_t w[`, `int32_t/int64_t sign`, `_padding`) —
    a `24` inside an old-layout code block is the origin story, not a live claim.

ROOTS (LANDMINES 5/7 — `.absolute()`, NEVER `.resolve()`; tools/ is a workspace symlink):
  - ENGINE (canonical parse): FOXML_ENGINE env, else `__file__.absolute().parent.parent` when invoked via
    the engine-side symlink (it has FixedPoint/), else the sibling `<workspace>.parent / FoxML_Trader_v2`
    when invoked from the workspace.
  - DOC scan: BOTH the engine root AND the workspace root, de-duped by realpath (the shared DESIGN_SPECS is
    a symlink — don't scan/report it twice) — the doc surface is split (CLAUDE.local.md is engine-only;
    engine DOCS/ and workspace DOCS/ are distinct trees; CLAUDE.md + DESIGN_SPECS are shared). When
    FOXML_ENGINE is set (self-test), the scan is confined to that one tree so the teeth-proof is hermetic.

Exit 0 = clean (GREEN); 1 = drift finding(s). Run: python3 tools/check_fpn_doc_size_currency.py
"""
import os
import re
import sys
from pathlib import Path

# --- Root resolution (.absolute(), NOT .resolve() — the symlink trap; LANDMINES 5/7) -------------------
_SELF = Path(__file__).absolute()
_TOOL_PARENT = _SELF.parent.parent  # whichever side we were invoked from (engine symlink or workspace real)
_FOXML_ENV = os.environ.get("FOXML_ENGINE")


def _has_fpn_header(root):
    return (root / "FixedPoint" / "FixedPointN.hpp").exists()


def _resolve_engine():
    """Engine root = where FixedPoint/FixedPointN.hpp lives. Honors FOXML_ENGINE (self-test); else finds it
    from whichever side we ran (engine-side __file__ already points at it; workspace-side -> sibling)."""
    if _FOXML_ENV:
        return Path(_FOXML_ENV)
    if _has_fpn_header(_TOOL_PARENT):  # invoked via the engine-side tools/ symlink
        return _TOOL_PARENT
    sibling = _TOOL_PARENT.parent / "FoxML_Trader_v2"  # invoked from the workspace -> sibling engine repo
    if _has_fpn_header(sibling):
        return sibling
    return _TOOL_PARENT  # last resort; parse_canonical() will WARN+exit-0 if the header isn't there


def _resolve_workspace():
    """Workspace root (holds CLAUDE.md + DOCS/ + DESIGN_SPECS/, incl. workspace-ONLY docs like LANDMINES.md
    that the engine tree doesn't symlink). Discovered the SAME way check_session_docs.sh does — FOXML_ENGINE
    self-test pins it to the temp tree; else FOXML_WORKSPACE env -> sibling `tick-trader-percore-workspace`
    -> _TOOL_PARENT. This keeps engine-side invocation (pre-commit / check_session_docs) from MISSING the
    workspace-only docs, regardless of which side __file__ lands on (the engine tools/ is a symlink)."""
    if _FOXML_ENV:  # hermetic self-test: scan only the override tree
        return Path(_FOXML_ENV)
    env_ws = os.environ.get("FOXML_WORKSPACE")
    if env_ws and Path(env_ws).is_dir():
        return Path(env_ws)
    sibling = _TOOL_PARENT.parent / "tick-trader-percore-workspace"
    if sibling.is_dir():
        return sibling
    return _TOOL_PARENT


ENGINE = _resolve_engine()
WORKSPACE = _resolve_workspace()

FPN_HEADER = ENGINE / "FixedPoint" / "FixedPointN.hpp"

# Canonical size assert in the code (SSoT). Matches `static_assert(sizeof(FPN_Binary<64>) == 16, ...`
# (accepts the pre-A.5 bare-FPN spelling too — robust across the E.0.8 rename boundary).
CANON_RE = re.compile(r'static_assert\s*\(\s*sizeof\s*\(\s*FPN(?:_Binary)?\s*<\s*64\s*>\s*\)\s*==\s*(\d+)')

# Doc scan surface (root-relative globs; applied to BOTH roots, realpath-deduped).
# A.5/S-2 widen: plans/_cross-cutting (living discipline docs — the stale-24B latency-path miss),
# claude-skills SKILL.md bodies (skills scaffold code), FEATURE_LOOKUP (workspace-root lookup doc).
SCAN_GLOBS = ["CLAUDE.md", "CLAUDE.local.md", "DOCS/**/*.md", "DESIGN_SPECS/**/*.md",
              "plans/_cross-cutting/**/*.md", "claude-skills/**/*.md", "FEATURE_LOOKUP.md"]

# Whole-file exclusions — the historical record (path substring, case-insensitive). NEVER flagged.
FILE_EXCLUDE_SUBSTR = (
    "changelogs/", "postmortem", "decision-log", "hot_path_changelog",
    "recurring-bug-patterns", "latency_optimization", "changelog.md",
)

# Plausible byte sizes for a SINGLE FPN (excludes pairs/multiples like 32B==2x16). A single FPN is 16
# (Ship-A) or 24 (pre-Ship-A sign-mag) or 20 (the hypothetical no-pad variant the worked-example weighs);
# we cap at 24 so "32B" (two FPN) / larger aggregates never get pulled in as a single-FPN claim.
PLAUSIBLE_SINGLE_FPN = {8, 12, 16, 20, 24}

# Line-level / window historical markers (a `24` here is the PAST, not a live claim).
HIST_RE = re.compile(
    r'HISTORICAL|SUPERSEDED|superseded|obsolete|OBSOLETE|formerly|former\b|pre-Ship-A|'
    r'was\s+\d+\s*B|sign-mag\s*(?:->|→)|\(unchanged\)|\d+\s*(?:->|→)\s*\d+\s*B',
    re.IGNORECASE,
)
# Old sign-magnitude FPN layout members — their presence in the window means we're inside the historical
# worked-example code block (w[N] + sign + _padding no longer exist post-Ship-A).
OLD_LAYOUT_RE = re.compile(r'uint64_t\s+w\s*\[|int(?:32|64)_t\s+sign\b|\b_padding\b')

HIST_WINDOW = 12  # preceding lines scanned for a historical marker / old-layout members

# FPN-token presence on the line (proximity gate). Accept FPN<...>/FPN_Binary<...> in any written form
# (both spellings: historical docs keep bare FPN; live docs spell FPN_Binary post-A.5).
FPN_TOKEN_RE = re.compile(r'FPN(?:_Binary)?\s*<[^>]*>')

# A byte-size token (number + B/bytes), not preceded by a word char / dot (so "0x16B" / "v1.16B" don't match).
BYTE_TOK = r'(?<![\w.])(\d+)\s*(?:B\b|bytes?\b)'

# (a) struct-field comment trailing size:  ...;  // N bytes   |   // NB
FIELD_COMMENT_RE = re.compile(r'//[^\n]*?' + BYTE_TOK)
# (c) sizeof assertion / equality:  sizeof(FPN<...>) == N  |  sizeof(FPN<...>) = N
SIZEOF_EQ_RE = re.compile(r'sizeof\s*\(\s*FPN(?:_Binary)?\s*<[^>]*>\s*\)\s*[<>=!]?=+\s*(\d+)')

# (b) prose: the byte-size must be BOUND to the FPN token, not merely co-occurring on the line (a line can
#     legitimately also mention an UNRELATED byte quantity — `8B single-word atomic width`, `8 bytes of
#     mantissa`). Two bound shapes:
#   (b1) AFTER FPN, within a short gap (≤44 chars covers `FPN<F> field address (16 bytes`): a connector
#        (`=`/`is`/`(`/`;`/`:`/`->`/`→`/whitespace, optional short words) then the FIRST byte-size token.
#        We anchor at the FPN token and take the NEAREST following byte-size (so we never reach a later,
#        unrelated quantity).
#   (b2) BEFORE FPN: a byte-size then a binding connector `for`/`per`/`each` ... `FPN<...>` within a short
#        window (`~24 B for FPN<64>`).
PROSE_AFTER_RE = re.compile(
    r'FPN(?:_Binary)?\s*<[^>]*>'           # the FPN token (both spellings)
    r'[^\n]{0,44}?'                        # short gap (non-greedy) — adjacent-ish only
    r'(?:=|\bis\b|\(|;|:|->|→|\s)\s*'      # a binding connector
    + BYTE_TOK
)
PROSE_BEFORE_RE = re.compile(
    BYTE_TOK +                              # the byte-size
    r'\s*(?:for|per|each)\b[^\n]{0,24}?'    # binding connector + short window
    r'FPN(?:_Binary)?\s*<[^>]*>'            # the FPN token (both spellings)
)


def parse_canonical():
    """Return (N, source_str) parsed from the code, or (None, reason) if not found."""
    if not FPN_HEADER.exists():
        return None, f"{FPN_HEADER} not found"
    try:
        text = FPN_HEADER.read_text(errors="replace")
    except Exception as e:  # noqa: BLE001
        return None, f"could not read {FPN_HEADER}: {e}"
    for raw in text.splitlines():
        line = raw.split("//", 1)[0]  # ignore a commented-out assert
        m = CANON_RE.search(line)
        if m:
            return int(m.group(1)), f"{FPN_HEADER.name}: {raw.strip()}"
    return None, f"no `static_assert(sizeof(FPN_Binary<64>) == N` (or pre-A.5 spelling) in {FPN_HEADER.name}"


def doc_roots():
    """The roots whose docs we scan. FOXML_ENGINE set -> ONLY that tree (hermetic self-test). Else BOTH the
    engine repo and the workspace, de-duped by realpath so a shared symlinked tree isn't scanned twice."""
    if _FOXML_ENV:
        return [ENGINE]
    roots, seen = [], set()
    for r in (ENGINE, WORKSPACE):
        rp = os.path.realpath(r)
        if rp not in seen:
            seen.add(rp)
            roots.append(r)
    return roots


def iter_doc_files():
    """Yield doc files across all roots, de-duped by realpath (CLAUDE.md / DESIGN_SPECS are shared symlinks
    — the same underlying file must not be scanned/reported twice)."""
    seen = set()
    for root in doc_roots():
        for g in SCAN_GLOBS:
            for p in sorted(root.glob(g)):
                if not p.is_file():
                    continue
                rp = os.path.realpath(p)
                if rp in seen:
                    continue
                seen.add(rp)
                yield p


def file_excluded(p):
    s = str(p).lower()
    return any(sub in s for sub in FILE_EXCLUDE_SUBSTR)


def is_historical(lines, idx):
    """True if the matched line (1-based idx) OR its preceding HIST_WINDOW lines carry a historical marker
    or the old sign-magnitude layout members (i.e. it's the origin story, not a live claim)."""
    lo = max(0, idx - HIST_WINDOW)
    window = lines[lo:idx]  # the line itself .. back HIST_WINDOW lines
    for w in window:
        if HIST_RE.search(w) or OLD_LAYOUT_RE.search(w):
            return True
    return False


def stated_sizes(line):
    """Yield every plausible-single-FPN byte size STATED-FOR-A-SINGLE-FPN on this line. The byte-size must
    be BOUND to an FPN<...> token (not merely co-occurring) — a line can legitimately mention an unrelated
    byte quantity alongside the FPN (`8B single-word atomic width`, `8 bytes of mantissa`). Combines:
      (a) struct-field trailing // comment with FPN< on the line,
      (b) prose with the size syntactically bound to FPN (after-with-connector OR before-with for/per/each),
      (c) sizeof(FPN<...>) == N."""
    if not FPN_TOKEN_RE.search(line):
        return
    found = set()

    def keep(n):
        if n in PLAUSIBLE_SINGLE_FPN:
            found.add(n)

    # (c) sizeof assertion — the most specific, FPN-bound by construction.
    for m in SIZEOF_EQ_RE.finditer(line):
        keep(int(m.group(1)))

    # (a) trailing // comment size on a struct-field line (`FPN<F> name;  // 16B`). The FPN< proximity gate
    #     above already scopes this to FPN-field lines; the comment carries the field's own size.
    cpos = line.find("//")
    if cpos != -1:
        for m in FIELD_COMMENT_RE.finditer(line[cpos:]):
            keep(int(m.group(1)))

    # (b) prose — only sizes BOUND to an FPN token (the nearest, via a connector).
    for m in PROSE_AFTER_RE.finditer(line):
        keep(int(m.group(1)))
    for m in PROSE_BEFORE_RE.finditer(line):
        keep(int(m.group(1)))

    yield from sorted(found)


def main():
    canon, src = parse_canonical()
    if canon is None:
        # S-4 hardening (A.5 gate): canon-missing is RED, never a silent skip — a guard that can go
        # blind-green is a hole (guards-compound). If the assert moved/renamed, update CANON_RE +
        # FPN_HEADER in this tool IN THE SAME COMMIT as the code change.
        print(f"check_fpn_doc_size_currency: RED — canonical binary-core size assert NOT FOUND ({src}). "
              f"Guard would be blind; fix CANON_RE/FPN_HEADER alongside the code change. (exit 1)")
        return 1

    files = list(iter_doc_files())
    scanned = [f for f in files if not file_excluded(f)]
    excluded = [f for f in files if file_excluded(f)]

    findings = []  # (file, line_no, stated_N, raw)
    for f in scanned:
        try:
            lines = f.read_text(errors="replace").splitlines()
        except Exception:  # noqa: BLE001
            continue
        for i, raw in enumerate(lines, 1):
            if not FPN_TOKEN_RE.search(raw):
                continue
            sizes = list(stated_sizes(raw))
            if not sizes:
                continue
            drift = [n for n in sizes if n != canon]
            if not drift:
                continue
            if is_historical(lines, i):
                continue
            for n in drift:
                findings.append((f, i, n, raw.strip()))

    def rel(p):
        try:
            return p.relative_to(WORKSPACE)
        except ValueError:
            return p  # engine-only file (e.g. CLAUDE.local.md) — show absolute

    print(f"check_fpn_doc_size_currency: canonical FPN<64> = {canon}B (from {src}).")
    print(f"  scanned {len(scanned)} doc file(s) "
          f"(excluded {len(excluded)} historical-record file(s)).")

    if findings:
        print(f"\n  DRIFT — doc(s) stating a single FPN<...> size != canonical {canon}B ({len(findings)}):")
        for f, i, n, snip in findings:
            print(f"    {rel(f)}:{i}  says {n}B (canonical {canon}B) -> {snip}")
        print(f"\n    FIX: match sizeof ({canon}B), OR (preferred) state it relative/symbolically + "
              f"reference the canonical (CLAUDE.md FPN<F=64> hot-path discipline).")
        print(f"\nRED - {len(findings)} stale FPN<64> size statement(s) in docs.")
        return 1

    print(f"\nGREEN - every single-FPN<...> size statement in docs matches the canonical {canon}B.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
