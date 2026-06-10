#!/usr/bin/env python3
"""check_storage_t_coverage.py — STORAGE_T variant coverage in tt:: dispatch.

Implements meta-discipline M4 / Pillar B6 from DESIGN_SPECS/implementation-layer-blindspot-taxonomy.md.

When master cfg registries add a NEW STORAGE_T variant (e.g., `char[N]` for KIND_STRING),
consumer template fns `tt::cfg_*_field<T>` must have a branch covering the new variant —
otherwise X-macro walker hits the row and compile fails at the missing branch.

This script verifies that every STORAGE_T variant used in FOREACH_PER_CORE_CFG_FIELD +
FOREACH_GLOBAL_CFG_FIELD has a covering branch in CfgFieldDispatch.hpp's tt:: family.

Checks performed:
  1. Extract all unique STORAGE_T variants from master cfg registries (col 0 of each X-macro row)
  2. For each variant, verify presence of `if constexpr (std::is_same_v<T, <variant>>` or
     equivalent type-trait branch in CfgFieldDispatch.hpp's template fns
  3. Report uncovered variants

Exit codes:
  0 = every STORAGE_T variant in master registries has a covering branch
  1 = at least one variant is uncovered
  2 = script error / file missing

Cross-references:
  - DESIGN_SPECS/implementation-layer-blindspot-taxonomy.md § B6
  - DESIGN_PHILOSOPHY.md § 11.5 meta-discipline M4
  - claude-skills/blindspot-scan/SKILL.md Pillar B6
  - CoreFrameworks/CfgFieldDispatch.hpp — tt:: family
"""

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).absolute().parent  # .absolute() not .resolve(): keep the engine path, don't follow the workspace symlink (machine-portable)
REPO_ROOT  = SCRIPT_DIR.parent

REGISTRY_FILES = [
    (REPO_ROOT / "CoreFrameworks/CfgFieldRegistry.hpp", "FOREACH_PER_CORE_CFG_FIELD"),
    (REPO_ROOT / "CoreFrameworks/CfgFieldRegistry.hpp", "FOREACH_GLOBAL_CFG_FIELD"),
]

DISPATCH_FILE = REPO_ROOT / "CoreFrameworks/CfgFieldDispatch.hpp"


def extract_storage_t_variants(file_path, foreach_name):
    """Walk file_path; extract STORAGE_T variants (col 0 of FOREACH_<foreach_name> rows)."""
    if not file_path.exists():
        print(f"[FAIL] registry file missing: {file_path}", file=sys.stderr)
        return None

    variants = set()
    in_macro = False
    define_pat = re.compile(rf"^#define\s+{foreach_name}\s*\(X\)")

    with file_path.open() as f:
        for line in f:
            if define_pat.match(line):
                in_macro = True
                continue
            if in_macro:
                stripped = line.strip()
                if not stripped.endswith("\\") and not stripped.startswith("X("):
                    if stripped == "" or stripped.startswith("//"):
                        continue
                    in_macro = False
                    continue
                if stripped.startswith("X("):
                    m = re.match(r"X\s*\(([^,]+),", stripped)
                    if m:
                        variants.add(m.group(1).strip())

    return variants


def variant_has_branch(variant, dispatch_text):
    """Heuristic: check if dispatch_text contains a type-trait branch covering `variant`.

    Looks for patterns like:
      - `std::is_same_v<T, <variant>>`
      - `is_fp_binary_v<T>`  (for FPN_Binary<F=64>; pre-A.5 spelling was is_FPN_v)
      - `std::is_integral_v<T>`  (for int / uint{8,16,32,64}_t)
      - Direct mention of <variant> in if constexpr context
    """
    # FPN_Binary<F> family (post-A.5 registry spelling; bare FPN< accepted across the rename boundary)
    if variant.startswith(("FPN_Binary<", "FPN<")):
        return ("is_fp_binary_v<T>" in dispatch_text) or ("std::is_same_v<T, FPN_Binary" in dispatch_text)

    # Bool family (int / uint8_t for KIND_BOOL per H13)
    # Catch-all for integer widths
    if variant in ("int", "uint8_t", "uint16_t", "uint32_t", "uint64_t",
                   "int8_t", "int16_t", "int32_t", "int64_t"):
        # Integer dispatch usually via std::is_integral_v or explicit per-type
        if "std::is_integral_v<T>" in dispatch_text:
            return True
        return f"std::is_same_v<T, {variant}>" in dispatch_text or f", {variant}>" in dispatch_text

    # char[N] family (KIND_STRING; future)
    if variant.startswith("char[") or "[]" in variant or "[N]" in variant:
        return ("std::is_array_v<T>" in dispatch_text) or ("char[" in dispatch_text)

    # Direct match fallback
    return variant in dispatch_text


DUAL_TYPE_DISPATCHERS = ("cfg_drift_compare", "cfg_drift_format_reason")

# Single-T wire dispatchers that must each carry an is_fp_decimal_v branch once the
# decimal money type lands (Ship-B P2; activated via --require-decimal-branches).
SINGLE_T_DISPATCHERS = ("cfg_parse_field", "cfg_save_field", "cfg_assign_field",
                        "cfg_diff_field", "cfg_emit_field", "cfg_populate_inf_field")


def _fn_body(dispatch_text, fn_name):
    """Slice the fn DEFINITION body: anchor on `name(` (comments mention the name without a
    juxtaposed paren), back up to its template<> header, end at the next template<> decl."""
    call = dispatch_text.find(fn_name + "(")
    if call < 0:
        return None
    start = dispatch_text.rfind("template <typename", 0, call)
    if start < 0:
        start = call
    nxt = dispatch_text.find("template <typename", call)
    return dispatch_text[start:nxt if nxt > 0 else len(dispatch_text)]


def check_dual_type_dispatcher_guards(dispatch_text):
    """Ship-B P0 (S-5/V5): the two-template drift dispatchers must family-assert BOTH
    params AND end their if-constexpr chain with an always_false_v exhaustive else —
    otherwise an unmatched (StampT, CfgT) pair compiles into a silent no-drift."""
    failures = []
    for fn in DUAL_TYPE_DISPATCHERS:
        body = _fn_body(dispatch_text, fn)
        if body is None:
            failures.append(f"{fn}: NOT FOUND in dispatch file")
            continue
        if "is_fp_binary_v<StampT>" not in body:
            failures.append(f"{fn}: missing StampT family static_assert")
        if "is_fp_binary_v<CfgT>" not in body:
            failures.append(f"{fn}: missing CfgT family static_assert (the V5 silent-no-drift hole)")
        if "always_false_v<StampT, CfgT>" not in body:
            failures.append(f"{fn}: missing always_false_v exhaustive-else (chain can fall through)")
    return failures


def check_decimal_branches(dispatch_text):
    """Ship-B P2 gate (--require-decimal-branches): every wire dispatcher carries an
    is_fp_decimal_v branch so decimal money cannot red-build-bypass via a missed fn."""
    failures = []
    for fn in SINGLE_T_DISPATCHERS + DUAL_TYPE_DISPATCHERS:
        body = _fn_body(dispatch_text, fn)
        if body is None:
            failures.append(f"{fn}: NOT FOUND in dispatch file")
        elif "is_fp_decimal_v" not in body:
            failures.append(f"{fn}: no is_fp_decimal_v branch (decimal money unhandled)")
    return failures


def main():
    print("[storage-t-coverage-CI] scanning master cfg registries for STORAGE_T variants...")
    all_variants = set()
    for file_path, foreach_name in REGISTRY_FILES:
        variants = extract_storage_t_variants(file_path, foreach_name)
        if variants is None:
            return 2
        print(f"  {foreach_name}: {len(variants)} unique variants — {sorted(variants)}")
        all_variants |= variants

    if not DISPATCH_FILE.exists():
        print(f"[FAIL] dispatch file missing: {DISPATCH_FILE}", file=sys.stderr)
        return 2

    dispatch_text = DISPATCH_FILE.read_text()

    uncovered = []
    for variant in sorted(all_variants):
        if not variant_has_branch(variant, dispatch_text):
            uncovered.append(variant)

    if uncovered:
        print("[storage-t-coverage-CI] FAIL: STORAGE_T variants without tt:: branch:")
        for v in uncovered:
            print(f"  {v}")
        print()
        print("Resolution per DESIGN_SPECS/implementation-layer-blindspot-taxonomy.md § B6:")
        print("  - Add `if constexpr (std::is_same_v<T, <variant>>)` branch to:")
        print("    tt::cfg_parse_field<T> / tt::cfg_emit_field<T> / tt::cfg_drift_compare<T> / tt::cfg_set_field<T>")
        print("  - Each tt:: family member MUST cover the new variant; X-macro walker will hit it")
        return 1

    dual_failures = check_dual_type_dispatcher_guards(dispatch_text)
    if dual_failures:
        print("[storage-t-coverage-CI] FAIL: dual-type dispatcher guards incomplete (Ship-B P0, S-5/V5):")
        for f in dual_failures:
            print(f"  {f}")
        return 1
    print("[storage-t-coverage-CI] dual-type drift dispatchers: both-param asserts + exhaustive-else verified")

    if "--require-decimal-branches" in sys.argv:
        dec_failures = check_decimal_branches(dispatch_text)
        if dec_failures:
            print("[storage-t-coverage-CI] FAIL: decimal branch coverage (Ship-B P2 gate):")
            for f in dec_failures:
                print(f"  {f}")
            return 1
        print("[storage-t-coverage-CI] decimal branches: all wire dispatchers covered")

    print(f"[storage-t-coverage-CI] PASS: all {len(all_variants)} STORAGE_T variants covered in tt:: family")
    print("[storage-t-coverage-CI] meta-discipline M4 / Pillar B6 verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
