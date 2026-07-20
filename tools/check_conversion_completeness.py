#!/usr/bin/env python3
"""check_conversion_completeness — verify in-code [SCHEMA] CONVERSION COMPLETENESS.

The validator (check_code_tag_blocks) verifies EXISTING blocks are well-formed; the battery
(gap_census2/det4/…) verifies bar/ladder shape. NEITHER verifies COVERAGE — that every unit which
WARRANTS a block actually HAS one, of the correct TYPE, sited as its OWN block (not lumped inside
another unit's [CODE]). That blind spot let GateControlNetwork.hpp ship green with two real structs
(GCN_input / GCN_network) buried inside [FUNCTION]_[GCN_forward] — a Class-51 vacuously-green shape
(the struct-checks never saw them because they weren't tagged [STRUCT]).

Checks (HARD):
  C1  MIS-CATEGORIZED / LUMPED — a NON-TRIVIAL struct/class OR a FOREACH registry DEFINITION lives
      inside another unit's [CODE] with NO block of its own (the GateControlNetwork class).
  C2  MISSING BLOCK — a NON-TRIVIAL struct/class OR a FOREACH registry at file scope has NO block.
  C3  MISSING [DERIVED] — a [STRUCT] block lacks its [DERIVED] section.

Proportionality (schema § Coverage): a TRIVIAL struct — <= 3 POD fields, no alignas, no method/operator —
stays terse-inline and is EXEMPT (e.g. a 2-field {q,r} return-type struct). Only NON-TRIVIAL units must
be blocked. A def that HAS its own block (by name) — including a legit tier-3 nested block (D-340) — passes.
A FUNCTION-LOCAL struct (declared inside a function's body braces — a stack impl-detail, not a navigable
unit the plugin browses) is EXEMPT too (2026-07-18); a namespace-scope struct merely sited under a mega
[FUNCTION] block (RegressionFeederX / the GCN structs, at brace-depth 0) STAYS flagged.

Non-vacuity: --selftest asserts the canonical-COMPLETE reference (ExecutionCore.hpp) scans CLEAN and the
known half-conversion (GateControlNetwork.hpp) is FLAGGED — so a broken checker cannot pass silently.

Exit: 0 = clean · 1 = coverage gap(s) · 2 = selftest failed.
"""
import re, sys, subprocess, argparse
from pathlib import Path

from foxroots import ENGINE  # SSoT resolver (E.1.2.B 0.1) — was a hardcoded absolute path: a portability-dead HARD gate (feedback_machine_portable_resolver)
sys.path.insert(0, str(Path(__file__).absolute().parent))
from check_code_tag_blocks import (corpus_contract, engine_source_files,   # noqa: E402  (corpus contract SSoT — D-393; closes TECH_DEBT-245)
                                   resolve_paths, PathResolutionError)

OPEN_RE    = re.compile(r"^\s*//\s*\[(FILE|STRUCT|FUNCTION|REGISTRY|ENUM|TYPE|MACRO|TEST|STRATEGY|ASSERT)\]_\[(.+?)\]\s*$")
END_RE     = re.compile(r"^\s*//\s*\[END_(\w+)\]_\[(.+?)\]\s*$")
CODE_RE    = re.compile(r"^\s*//\s*\[CODE\]\s*$")
ENDCODE_RE = re.compile(r"^\s*//\s*\[END_CODE\]\s*$")
DERIVED_RE = re.compile(r"^\s*//\s*\[DERIVED\]")
# a TYPE definition WITH a body (`{`), at low indent — a forward decl (`;`) is NOT a unit
TYPEDEF_RE = re.compile(r"^\s{0,4}(?:template\s*<[^;{}]*>\s*)?(?:struct|class|union)\s+(?:alignas\s*\([^)]*\)\s+)?(\w+)")
FOREACH_RE = re.compile(r"^\s{0,4}#define\s+(FOREACH_\w+)")
# a registry COUNT-helper (`#define FOREACH_X_COUNT (0 FOREACH_X(...))`) is NOT a standalone registry —
# it counts its parent's rows and rides in the parent's block. Exempt (else a huge false-positive class).
COUNT_HELPER_RE = re.compile(r"_COUNT(_\w+)?$")

def base_name(nm): return nm.split("<", 1)[0]     # FixedPoint<2,64> -> FixedPoint (template-tolerant match)

def same_registry_family(a, b):
    """Two FOREACH registries are the SAME FAMILY (a documented [SECTION] variant of one registry, not a
    mis-categorization) when they share >=2 leading name-segments — e.g. FOREACH_CFG_GATE_GLOBAL vs
    FOREACH_CFG_GATE_PER_NODE (scope variants), FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG vs its parent
    (wire-order facet). Policy (operator 2026-07-17): such variants ride the parent [REGISTRY] block."""
    sa, sb = a.replace("FOREACH_", "").split("_"), b.replace("FOREACH_", "").split("_")
    shared = 0
    for x, y in zip(sa, sb):
        if x != y: break
        shared += 1
    return shared >= 2

def is_schema_file(text): return bool(re.search(r"^// \[SCHEMA\]_\[v1", text, re.M))

def inside_function_body(lines, host_open, ln):
    """True iff the def at `ln` sits INSIDE its enclosing [FUNCTION] host's C++ body braces (a
    function-LOCAL struct — a stack impl-detail, not a navigable unit the plugin browses → EXEMPT),
    vs merely sited under the doc-block at brace-depth 0 (a real namespace-scope struct lumped in a
    mega [FUNCTION] block — RegressionFeederX / the GCN structs — which STAY flagged). Net brace count
    of the code between the host header and the def: >=1 ⇒ an unclosed function signature encloses it.
    Comments stripped; the engine corpus is well-formed C++. Fires ONLY under a [FUNCTION] host, so a
    D-340 tier-3 nested type inside a [STRUCT] host stays flagged (it IS a navigable unit)."""
    depth = 0
    for i in range(host_open + 1, ln):
        code = lines[i].split("//", 1)[0]
        depth += code.count("{") - code.count("}")
    return depth >= 1

def parse_blocks(lines):
    """Return [{type,name,base,open,end,has_derived}] — end is the matching [END_<type>]_[name] line
    (matched BY NAME, so nested blocks get correct open..end spans), or None for a header-only unit
    (FILE / MACRO / ASSERT — no closer). A def is 'owned' by a block if open < def_line < end."""
    blocks, n = [], len(lines)
    for i in range(n):
        m = OPEN_RE.match(lines[i])
        if not m: continue
        btype, bname = m.group(1), m.group(2)
        end, has_derived = None, False
        for j in range(i + 1, n):
            em = END_RE.match(lines[j])
            if em and em.group(1) == btype and em.group(2) == bname: end = j; break   # OUR named closer — scans PAST nested children (tier-3)
            if DERIVED_RE.match(lines[j]) and end is None: has_derived = True
        blocks.append({"type": btype, "name": bname, "base": base_name(bname),
                       "open": i, "end": end, "has_derived": has_derived})
    return blocks

def struct_is_trivial(lines, start):
    """<=3 POD fields, no method/operator, no alignas → trivial (terse-inline OK). Rough but robust:
    the discriminator only needs to split a 2-field {q,r} from a 6-field struct with an operator[]."""
    if "alignas" in lines[start]: return False
    depth, fields, has_method, k, n = 0, 0, False, start, len(lines)
    seen_open = False
    while k < n:
        ln = lines[k]
        depth += ln.count("{") - ln.count("}")
        if "{" in ln: seen_open = True
        if seen_open and k > start:
            body = ln.split("//", 1)[0].strip()
            if body and not body.startswith(("static_assert","using","typedef","friend","enum","struct","class","//")):
                if "(" in body: has_method = True                          # a method / operator / ctor has parens
                elif body.endswith(";"): fields += 1                        # a data member (no parens): `Type<T> f[...];`
        if seen_open and depth <= 0: break
        k += 1
    return (fields <= 3) and (not has_method)

def enumerate_defs(lines):
    """Non-trivial struct/class/union + every FOREACH registry, with (kind, name, lineno)."""
    defs, n = [], len(lines)
    for i in range(n):
        fm = FOREACH_RE.match(lines[i])
        if fm:
            if COUNT_HELPER_RE.search(fm.group(1)): continue   # `FOREACH_X_COUNT` = count-helper, not a registry
            defs.append(("REGISTRY", fm.group(1), i)); continue
        tm = TYPEDEF_RE.match(lines[i])
        if tm:
            # require a body: `{` on this or the next non-blank line (else it's a forward decl)
            nxt = lines[i+1].lstrip() if i+1 < n else ""
            if "{" not in lines[i] and not nxt.startswith("{"): continue
            if struct_is_trivial(lines, i): continue                       # proportionality exempt
            defs.append(("STRUCT", tm.group(1), i))
    return defs

def check_file(path):
    lines = path.read_text(errors="replace").split("\n")
    text = "\n".join(lines)
    if not is_schema_file(text): return []                                  # only converted files
    blocks = parse_blocks(lines)
    # containers = blocks that CAN enclose a def (have a real END; FILE-scope is not a "host" for lumping)
    containers = [b for b in blocks if b["end"] is not None and b["type"] != "FILE"]
    findings = []   # (sig, lineno, name, msg) — `name` is the STABLE baseline key (line drifts, name doesn't)
    # C3 — STRUCT blocks without DERIVED
    for b in blocks:
        if b["type"] == "STRUCT" and not b["has_derived"]:
            findings.append(("C3", b["open"] + 1, b["name"], f"[STRUCT]_[{b['name']}] has no [DERIVED]"))
    # C1 / C2 — every non-trivial def must have its OWN block (base-name match, spec/tier-3-nesting tolerant)
    for kind, name, ln in enumerate_defs(lines):
        enclosing = [b for b in containers if b["open"] < ln < b["end"]]
        if any(b["base"] == name for b in enclosing): continue             # its own block (incl. FixedPoint<2,64>)
        if enclosing:
            host = min(enclosing, key=lambda b: b["end"] - b["open"])       # innermost enclosing unit
            if kind == "REGISTRY" and host["type"] == "REGISTRY" and same_registry_family(name, host["name"]):
                continue                                                     # same-family sub-registry variant → rides the parent block (policy #1)
            if kind == "STRUCT" and host["type"] == "FUNCTION" and inside_function_body(lines, host["open"], ln):
                continue                                                     # FUNCTION-LOCAL struct (stack impl-detail, not a navigable unit) → EXEMPT (2026-07-18)
            findings.append(("C1", ln + 1, name, f"{kind.lower()} `{name}` lumped inside [{host['type']}]_[{host['name']}] — needs its own block"))
        else:
            findings.append(("C2", ln + 1, name, f"non-trivial {kind.lower()} `{name}` at file scope has NO block"))
    return sorted(findings, key=lambda f: f[1])

def converted_files():
    """The CONVERTED subset of the `validate` corpus, per the contract (D-393).

    ⚠️ CLOSES TECH_DEBT-245. This used to shell out to `rg -l` WITHOUT `--no-ignore`, so the gate
    was BLIND to gitignored-but-real source: a gitignored file was never scanned, and "0 gaps"
    therefore meant *unverified*, not *clean*. Measured at the swap: the enumerator sees 9 files
    rg did not — `Strategies/private/EmaCross.hpp` (a real, gitignored, 294-line source file),
    the 3 file-symlinked `DOCS/*TEMPLATE*.hpp`, and the 5 `schema_golden` fixtures (unreachable
    for rg because engine `tests/` is a DIRECTORY SYMLINK and rg follows neither symlink kind
    without `-L`). All 9 scan clean today, so this closes the hole without moving the baseline —
    but "clean" is now a measurement rather than an assumption.

    `.gitignore` is never an input to corpus membership (D-393 pt 2): distribution is a
    DISTRIBUTION concern, membership is a TOOLING concern, and nobody ever chose to couple them
    — it was a side effect of rg's default.

    Profile is `validate`, not `derived_facts`: this gate asks "does everything carrying tag
    grammar carry it COMPLETELY", which is the broad population including illustrative
    copy-source. `derived_facts` is declared COMPILED-reality-only and would be the wrong
    contract to read here. Keeping schema_golden in also honours the P3 catch (2026-07-15) —
    those fixtures are the format's canonical conversions and MUST stay policed.

    The selector is the contract's anchored `line_prefix`, matched with startswith(): a
    line-start literal test, deliberately expressible with NO regex engine so the C++ hand-parser
    needs no new machinery (D-393 pt 4). An UNANCHORED match also hits selftest STRING LITERALS
    and prose — it reported `foxtag_main.cpp` as converted when it is not, a FALSE finding during
    `0.1.5`."""
    sel = corpus_contract()["selectors"]["converted"]
    prefix = sel["line_prefix"]
    out = []
    for p in engine_source_files(profile="validate"):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except (IOError, OSError):
            continue
        if any(line.startswith(prefix) for line in text.splitlines()):
            out.append(p)
    return out

def selftest():
    import tempfile, os
    ok = True
    ref = ENGINE / "CoreFrameworks/ExecutionCore.hpp"
    rf = check_file(ref)
    print(f"  {'✅' if not rf else '❌'} canonical-complete ExecutionCore.hpp scans CLEAN"
          + ("" if not rf else f" — got {rf}")); ok &= not rf
    # SYNTHETIC known-bad (corpus-INDEPENDENT — survives the Phase-C cleanup of the real GateControlNetwork):
    # a non-trivial 6-field struct lumped inside a [FUNCTION] block's [CODE] must be flagged C1.
    bad_src = ("// [SCHEMA]_[v1.0]\n// [FUNCTION]_[demo_fn]\n// [CODE]\n"
               "template <unsigned F> struct DemoLumped6 {\n"
               "    int a;\n    int b;\n    int c;\n    int d;\n    int e;\n    int f;\n};\n"
               "inline void demo_fn() {}\n// [END_CODE]\n// [END_FUNCTION]_[demo_fn]\n")
    fd, p = tempfile.mkstemp(suffix=".hpp"); os.write(fd, bad_src.encode()); os.close(fd)
    bf = [f for f in check_file(Path(p)) if f[0] == "C1" and "DemoLumped6" in f[2]]
    os.unlink(p)
    print(f"  {'✅' if bf else '❌'} synthetic known-bad: a 6-field struct lumped in a [FUNCTION] block is FLAGGED (C1)"
          + ("" if bf else " — NOT flagged")); ok &= bool(bf)
    # FUNCTION-LOCAL exemption (2026-07-18): a 6-field struct declared INSIDE a function's body braces is a
    # stack impl-detail, NOT a navigable unit → must NOT be flagged (vs DemoLumped6 above, at brace-depth 0
    # under the same doc-block, which STAYS flagged — proves the exemption is scoped, not a blanket hole).
    loc_src = ("// [SCHEMA]_[v1.0]\n// [FUNCTION]_[demo_fn2]\n// [CODE]\n"
               "inline void demo_fn2() {\n"
               "    struct DemoLocal6 {\n"
               "        int a;\n        int b;\n        int c;\n        int d;\n        int e;\n        int f;\n    };\n"
               "    DemoLocal6 x{};\n    (void)x;\n}\n// [END_CODE]\n// [END_FUNCTION]_[demo_fn2]\n")
    fd2, p2 = tempfile.mkstemp(suffix=".hpp"); os.write(fd2, loc_src.encode()); os.close(fd2)
    lf = [f for f in check_file(Path(p2)) if "DemoLocal6" in f[2]]
    os.unlink(p2)
    print(f"  {'✅' if not lf else '❌'} function-LOCAL struct (inside a fn body) EXEMPT (not a navigable unit)"
          + ("" if not lf else f" — wrongly flagged {lf}")); ok &= not lf
    # a trivial 2-field return struct must NOT be flagged (proportionality)
    triv = [f for f in check_file(ENGINE / "FixedPoint/FixedPointN.hpp")
            if any(t in f[2] for t in ("u256","udiv_qr_t","divmul_qr","MoneyParse"))]
    print(f"  {'✅' if not triv else '❌'} trivial <=3-field return structs EXEMPT (FixedPointN u256/udiv_qr_t/…)"
          + ("" if not triv else f" — got {triv}")); ok &= not triv
    fam = (same_registry_family("FOREACH_CFG_GATE_GLOBAL", "FOREACH_CFG_GATE_PER_NODE")
           and same_registry_family("FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG", "FOREACH_STAMP_BOUND_MODEL_CONST")
           and not same_registry_family("FOREACH_CFG_DRIFT_CHECK", "FOREACH_FEATURE"))
    print(f"  {'✅' if fam else '❌'} same-family sub-registry variants EXEMPT, unrelated NOT (policy #1)"); ok &= fam

    # NON-VACUITY TOOTH for the TECH_DEBT-245 close: the enumerator must NOT consult .gitignore.
    # This gate used to shell out to `rg -l` without --no-ignore, so a gitignored-but-real source
    # file was never read — and a guard cannot RED on input it never reads (Class-51). Without
    # this assertion the fix is unfalsifiable: swapping back to an ignore-respecting enumerator
    # would leave every other check green.
    #
    # SYNTHETIC + frozen, per the calibration-corpus discipline — a live gitignored file gets
    # fixed and stops proving anything. Builds a throwaway tree whose .gitignore hides an
    # UN-CONVERTED lumped struct, then asserts (a) the contract walk still yields it and (b) the
    # gate FLAGS it. A tooth that only proved (a) would show the file is listed while saying
    # nothing about whether it is judged.
    # ⚠️ The ignore rule MUST be DIRECTORY-level (`private/`), not file-level. Measured: ripgrep
    # skips a gitignored DIRECTORY but still returns a file-level-ignored file, so a file-level
    # fixture makes this tooth VACUOUS — it would pass against the very rg enumerator it exists
    # to catch. Directory-level is also the real-world shape (`.gitignore:167 Strategies/private/`
    # is what hid the live instance). Verified discriminating: rg sees 0, the contract walk sees 1.
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / ".gitignore").write_text("private/\n")
        (tdp / "private").mkdir()
        (tdp / "private" / "hidden.hpp").write_text(
            "// [SCHEMA]_[v1.0]\n// [FUNCTION]_[hidden_fn]\n// [CODE]\n"
            "template <unsigned F> struct HiddenLumped6 {\n"
            "    int a;\n    int b;\n    int c;\n    int d;\n    int e;\n    int f;\n};\n"
            "inline void hidden_fn() {}\n// [END_CODE]\n// [END_FUNCTION]_[hidden_fn]\n")
        walked = [p.name for p in resolve_paths([str(tdp)], profile="validate")]
        seen = "hidden.hpp" in walked
        flagged = [f for f in check_file(tdp / "private" / "hidden.hpp")
                   if f[0] == "C1" and "HiddenLumped6" in f[2]]
        gi = seen and bool(flagged)
        print(f"  {'✅' if gi else '❌'} GITIGNORED source is still enumerated AND judged "
              f"(TECH_DEBT-245 non-vacuity: .gitignore is not a membership input, D-393 pt 2)"
              + ("" if gi else f" — enumerated={seen} flagged={bool(flagged)}")); ok &= gi
    return ok

def finding_key(rel, sig, name): return f"{rel}|{sig}|{name}"   # STABLE across line drift (name, not line)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--baseline", help="grandfathered baseline file: only findings NOT in it fail (the new-gap gate)")
    ap.add_argument("--write-baseline", help="snapshot the current findings' stable keys to this file, then exit 0")
    ap.add_argument("--paths", nargs="*")
    a = ap.parse_args()
    if a.selftest:
        print("check_conversion_completeness --selftest (non-vacuity):")
        sys.exit(0 if selftest() else 2)
    # Explicit paths route through the contract resolver. This tool was the ONLY one of the four
    # that already failed on a missing path — but via an UNCAUGHT FileNotFoundError traceback
    # (rc=1), not a stated contract. All consumers now agree: rc=2 with the same message.
    if a.paths:
        try:
            files = resolve_paths(a.paths, profile="validate")
        except PathResolutionError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        files = converted_files()
    rows = []   # (key, rel, sig, ln, name, msg)
    for f in files:
        rel = f.relative_to(ENGINE) if str(f).startswith(str(ENGINE)) else f
        for sig, ln, name, msg in check_file(f):
            rows.append((finding_key(rel, sig, name), rel, sig, ln, name, msg))
    if a.write_baseline:
        Path(a.write_baseline).write_text(
            "# check_conversion_completeness grandfathered baseline (stable file|sig|name keys).\n"
            "# A finding NOT in here fails; regenerate (--write-baseline) to SHRINK as cleanup lands.\n"
            + "\n".join(sorted(k for k, *_ in rows)) + "\n")
        print(f"wrote {len(rows)} baseline keys → {a.write_baseline}"); sys.exit(0)
    if a.baseline:                                                  # BASELINE MODE — only NEW findings fail
        try: base = {l.strip() for l in Path(a.baseline).read_text().splitlines() if l.strip() and not l.startswith("#")}
        except (IOError, OSError): base = set()
        new = sorted((r for r in rows if r[0] not in base), key=lambda r: (str(r[1]), r[3]))
        resolved = base - {r[0] for r in rows}
        for _, rel, sig, ln, name, msg in new:
            print(f"  [NEW {sig}] {rel}:{ln}  {msg}")
        print(f"\n=== baseline {len(base)} tracked · {len(rows) - len(new)} still-present · {len(new)} NEW · {len(resolved)} resolved ===")
        if resolved: print(f"  ✓ {len(resolved)} baseline finding(s) RESOLVED — regenerate to shrink (--write-baseline).")
        if new: print("  ✗ NEW coverage gap(s) — a unit was added lumped/un-blocked. Convert it (or fix the tag).")
        sys.exit(1 if new else 0)
    tot = {"C1": 0, "C2": 0, "C3": 0}                                # FULL MODE — list everything, fail on any
    for _, rel, sig, ln, name, msg in sorted(rows, key=lambda r: (str(r[1]), r[3])):
        tot[sig] += 1; print(f"  [{sig}] {rel}:{ln}  {msg}")
    hit = len({str(r[1]) for r in rows})
    print(f"\n=== {len(files)} converted file(s) · {hit} with coverage gaps ===")
    print(f"  C1 lumped: {tot['C1']} · C2 missing: {tot['C2']} · C3 no-DERIVED: {tot['C3']}")
    sys.exit(1 if rows else 0)

if __name__ == "__main__":
    main()
