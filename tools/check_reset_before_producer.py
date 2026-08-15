#!/usr/bin/env python3
"""
check_reset_before_producer.py — a per-pass RESET must precede its PRODUCER (D-421 / Class 44 sub-B).

WHY THIS EXISTS
---------------
`strategy_halt_reason` was reset to `SHALT_OK` **59 lines BELOW** the dispatcher call that writes
it — unconditionally, same straight-line block, no intervening control flow. So the producer's
output was discarded on every rebuild, and **17 of the 20 SHALT codes could never be observed**.
Only the two written *after* the reset point survived, which is why the panel always showed
something and nobody noticed: the class hid behind its own partial success.

Born broken. `git log -S` puts the pointer-arg and the reset in the SAME commit (`bc37c62`,
2026-04-30) — placed wrong on day one and unnoticed for over three months. The in-code contract at
`StrategyInterface.hpp` said "reset to SHALT_OK **at the top of each rebuild**" the entire time; the
code contradicted its own stated contract and nothing compared the two.

**Why a comment was not enough, and why this is a tool.** The fix commit paired the two lines with
comments saying they are not interchangeable (`halt_reason`'s reset is correct BELOW its producers;
`strategy_halt_reason`'s must be ABOVE). That is the weakest available guard for an ORDERING
property — the exact thing a future "these two adjacent lines look redundant, let me merge them"
refactor gets wrong, silently, with no test failing. Both independent reviews at the D-421 close
named the same remedy: assert the reset line is LESS THAN every producer line in the same function.
One integer comparison, and it would have caught this on the day it shipped.

WHAT IT CHECKS
  For each row in RULES: inside the named function body, find (a) the RESET assignment and (b) every
  PRODUCER site. RED if any producer precedes the reset. Also RED if either side vanishes — a rule
  whose subject disappeared is a rule that can no longer fail, which is the vacuity this codebase
  treats as a bug in its own right (Class 51).

WHAT IT DELIBERATELY DOES NOT DO
  - No control-flow analysis. It compares SOURCE ORDER inside one function. That is sound for the
    straight-line "reset at the top of each pass" contract this encodes and nothing else; a reset
    guarded by an `if` is out of scope and would need a real CFG. Stated so the green is not
    over-read (M10: this check is PARTIAL by construction, not TOTAL).
  - It does not decide WHICH order is correct. `halt_reason`'s reset is correct BELOW its producers
    and `strategy_halt_reason`'s must be ABOVE — the rule row carries the intended direction,
    because that is a design fact a scanner cannot derive.

RELATION TO EXISTING TOOLS (canonical-sister check, run BEFORE writing this)
  `scan_class_44_cfg_orphan.py` is the nearest sibling and explicitly EXCLUDES this: *"NOT in scope —
  the state-field producer/consumer direction over ARBITRARY struct fields … is TECH_DEBT-175 (the
  AST struct-field produce/consume tracker)."* So this is not a duplicate — but it IS a narrow slice
  of a deliverable that is already homed. **TECH_DEBT-175 owns the general form** (an AST tracker
  that derives producer/consumer pairs); this owns a hand-declared RULES list. The trade is explicit:
  exact and cheap and it only knows what you tell it, versus general and expensive and able to find
  pairs nobody thought to declare. When TD-175 lands, these rules become its regression fixtures
  rather than a second implementation — do NOT grow this into an AST tracker.

rc: 0 = every rule holds · 1 = a violation · 2 = REFUSAL (a rule's subject not found — never a pass)
"""
import os
import re
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_doc_metadata import ENGINE   # noqa: E402  (the ONE engine-root SSoT — D-372)

# (label, file, function, reset-regex, producer-regexes, direction)
#   direction "reset_first"  — the reset must PRECEDE every producer (the per-pass contract)
#   direction "reset_last"   — the reset must FOLLOW every producer. NO LIVE RULE USES THIS today;
#                              it is kept because the inverse shape is real and is covered by a
#                              hermetic tooth, but do not read a green as evidence it was exercised.
RULES = [
    ("strategy_halt_reason reset precedes the strategy dispatcher",
     "CoreFrameworks/ControllerEventLoop.hpp", "EventLoop_RebuildOneCore",
     r"\.strategy_halt_reason\s*=\s*SHALT_OK",
     [r"Strategy_BuildParameters\s*\(", r"Strategy_AdaptPerCore\s*\("],
     "reset_first"),
    # The sibling. Both rules are reset_first — and encoding this one is what CORRECTED my own
    # misreading. I first wrote it "reset_last", from the fix commit's line that halt_reason's reset
    # "stays BELOW" — but that sentence is about its position relative to the OTHER reset, not to its
    # producers. Its producers (the zero_gate lambda) are below IT, so it is reset_first like its
    # sibling. The tool's first live run RED-ed on the wrong rule, not on wrong code; a guard whose
    # first act is to catch its author's own encoding error is the shape worth having.
    ("halt_reason reset precedes its zero-gate producers",
     "CoreFrameworks/ControllerEventLoop.hpp", "EventLoop_RebuildOneCore",
     r"\.halt_reason\s*=\s*HALT_OK",
     # The producers are a `zero_gate(HALT_*)` lambda plus ONE direct non-OK assignment; the first
     # draft of this rule guessed `halt_reason = HALT_NODE_KILL` and matched nothing, which REFUSED
     # rather than passing — the vacuity guard doing its job on its own author.
     [r"zero_gate\s*\(\s*HALT_", r"\.halt_reason\s*=\s*HALT_(?!OK)"],
     "reset_first"),
]


class Refusal(RuntimeError):
    """A rule's subject is missing. rc 2 — never rendered as a pass."""


def _function_body(text, fn):
    """(start_offset, body) for `fn`'s DEFINITION — brace-matched from its opening `{`.

    Finding the definition is the fiddly part and getting it wrong is silent. The first draft took
    the first line mentioning the name, which in this codebase is a `// - [FUNCTION]_[Name]` tag
    comment ~3000 lines above the real definition — it then brace-matched an unrelated region, found
    neither the reset nor the producer, and REFUSED. That refusal is the only reason the mistake
    surfaced instead of passing over an empty body; a check that scans the wrong region and finds
    nothing is indistinguishable from a clean one unless absence is fatal (Class 51 / Class 57).

    So: skip comment lines, and require the arg list to be followed by `{` — a call site ends in `;`
    and a declaration ends in `;` too, only a definition opens a body.
    """
    i = None
    for m in re.finditer(r"\b" + re.escape(fn) + r"\s*\(", text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        prefix = text[line_start:m.start()].lstrip()
        if prefix.startswith("//") or prefix.startswith("*"):
            continue                                    # a tag block or prose mention
        depth, k = 0, m.end() - 1
        while k < len(text):                            # walk to the matching close-paren
            if text[k] == "(":
                depth += 1
            elif text[k] == ")":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        rest = text[k + 1:k + 400].lstrip()
        if rest.startswith("{"):                        # a DEFINITION, not a call or a decl
            i = text.index("{", k + 1)
            break
    if i is None:
        raise Refusal(f"definition of {fn!r} not found (mentions exist, none opens a body)")
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return i, text[i:j]
    raise Refusal(f"unbalanced braces in {fn!r}")


def _lineno(text, off):
    return text.count("\n", 0, off) + 1


def check_rule(root, label, rel, fn, reset_re, producer_res, direction):
    path = os.path.join(root, rel)
    try:
        text = open(path).read()
    except OSError as e:
        raise Refusal(f"cannot read {rel}: {e}")
    base, body = _function_body(text, fn)

    rm = re.search(reset_re, body)
    if not rm:
        raise Refusal(f"[{label}] reset site not found in {fn} — the rule cannot fail, which is "
                      f"worse than a violation; fix the pattern or retire the rule")
    reset_line = _lineno(text, base + rm.start())

    prods = []
    for pre in producer_res:
        for pm in re.finditer(pre, body):
            prods.append((_lineno(text, base + pm.start()), pre))
    if not prods:
        raise Refusal(f"[{label}] no producer site matched in {fn} — same vacuity as above")

    bad = [(ln, pr) for ln, pr in prods
           if (direction == "reset_first" and ln < reset_line)
           or (direction == "reset_last" and ln > reset_line)]
    return reset_line, sorted(prods), bad


def run(root):
    findings, refusals = [], []
    for rule in RULES:
        label = rule[0]
        try:
            reset_line, prods, bad = check_rule(root, *rule)
        except Refusal as e:
            refusals.append(str(e)); continue
        rel_word = "before" if rule[5] == "reset_first" else "after"
        if bad:
            findings.append((label, rule[1], reset_line, rel_word, bad))
        else:
            print(f"  ok  {label} — reset @:{reset_line} {rel_word} "
                  f"{len(prods)} producer site(s) @ {', '.join(str(l) for l, _ in prods)}")
    for r in refusals:
        print(f"  REFUSAL: {r}", file=sys.stderr)
    for label, rel, reset_line, rel_word, bad in findings:
        print(f"\n❌ {label}\n   {rel}: reset at :{reset_line} is NOT {rel_word} "
              f"{len(bad)} producer site(s):", file=sys.stderr)
        for ln, pr in bad:
            print(f"     :{ln}  {pr}", file=sys.stderr)
        print("   A producer whose output the reset overwrites is Class 44 sub-shape B — the value "
              "is computed correctly and discarded before anyone can read it.", file=sys.stderr)
    if refusals:
        return 2
    if findings:
        return 1
    print("[reset-ordering] GREEN — every per-pass reset sits on the correct side of its producers.")
    return 0


# ---------------------------------------------------------------------------
FAILS = []


def _chk(name, cond):
    print(("  ✅ " if cond else "  ❌ ") + name)
    if not cond:
        FAILS.append(name)


def selftest():
    import tempfile
    src = ("void F(int x) {\n"
           "    produce(&s.f);\n"          # line 2 — producer FIRST (the bug)
           "    s.f = OK;\n"               # line 3 — reset after
           "}\n")
    good = ("void F(int x) {\n"
            "    s.f = OK;\n"              # line 2 — reset first (correct)
            "    produce(&s.f);\n"
            "}\n")
    with tempfile.TemporaryDirectory() as td:
        for name, text in (("bad.hpp", src), ("good.hpp", good)):
            open(os.path.join(td, name), "w").write(text)
        # the planted BUG must be caught
        _, _, bad = check_rule(td, "t", "bad.hpp", "F", r"s\.f = OK", [r"produce\("], "reset_first")
        _chk("planted producer-before-reset is CAUGHT", len(bad) == 1)
        # ...and the correct order must PASS, or the check would red on everything
        _, _, bad = check_rule(td, "t", "good.hpp", "F", r"s\.f = OK", [r"produce\("], "reset_first")
        _chk("correct order PASSES (the positive control)", bad == [])
        # the opposite direction is a real rule shape, not a typo
        _, _, bad = check_rule(td, "t", "bad.hpp", "F", r"s\.f = OK", [r"produce\("], "reset_last")
        _chk("reset_last direction inverts the verdict", bad == [])
        # a vanished subject must REFUSE, never pass
        for pat, why in ((r"s\.nope = OK", "reset"), (r"nosuchcall\(", "producer")):
            try:
                check_rule(td, "t", "bad.hpp", "F", pat if why == "reset" else r"s\.f = OK",
                           [pat] if why == "producer" else [r"produce\("], "reset_first")
                _chk(f"missing {why} site REFUSES", False)
            except Refusal:
                _chk(f"missing {why} site REFUSES", True)
    # real tree: both live rules must resolve (a rule pointing at nothing is a dead rule)
    for rule in RULES:
        try:
            check_rule(str(ENGINE), *rule)
            _chk(f"real tree resolves: {rule[0]}", True)
        except Refusal as e:
            _chk(f"real tree resolves: {rule[0]} ({e})", False)
    print(f"{os.path.basename(__file__)} --selftest: "
          + ("ALL TEETH FIRE" if not FAILS else "FAILURES: " + "; ".join(FAILS)))
    return 0 if not FAILS else 2


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    try:
        return run(str(ENGINE))
    except Refusal as e:
        print(f"[reset-ordering] REFUSAL — {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
