#!/usr/bin/env python3
"""add_vocab.py — the D-365 add-vocab ONE-ACTION: insert a vocab tag into its SSoT + regen the
indexes + verify it derives, in one drift-proof command.

WHY: adding a tag is a multi-step flow — edit the right SSoT → the validators AUTO-derive (no code
edit; check_code_tag_blocks + foxtag read the fence at runtime) → regen the doc/code indexes → confirm
it derives. By hand this drifts (a forgotten `rebuild_doc_indexes` leaves the index-currency check red).
This wraps it: one action, no forgotten step, verified at the end.

Two SSoTs, by axis:
  --category NAME       → the ```category-set``` fence in in-code-documentation-schema.md (a structural
                          top-level [CATEGORY]; UPPER_SNAKE — e.g. ORIGIN, UPDATED).
  --concern tag --desc  → doc-tag-vocabulary.md CONCERN table (a [TAG] concern value; lower-hyphen).
  --surface tag --desc  → doc-tag-vocabulary.md SURFACE table (a [TAG] surface value; lower-hyphen).

The insert helpers are PURE (text→(text, err)) so `--selftest` proves them non-vacuously (adds once,
refuses a duplicate) without touching the real SSoTs.

Exit: 0 added+verified · 1 duplicate / bad format / SSoT-not-found / verify fail · 2 selftest fail.
Usage:
  python3 tools/add_vocab.py --category ORIGIN
  python3 tools/add_vocab.py --concern persistence --desc "snapshot-serialized state; wire-persist delegates"
  python3 tools/add_vocab.py --surface slow-path --desc "the per-node slow (regime/ML) thread"
  python3 tools/add_vocab.py --selftest
"""
import re
import sys
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent))
from check_code_tag_blocks import SCHEMA_PATH, load_categories   # noqa: E402  (the fence SSoT + derived set)

TOOLS = Path(__file__).absolute().parent
VOCAB_PATH = TOOLS.parent / "DESIGN_SPECS" / "meta-disciplines" / "doc-tag-vocabulary.md"
REBUILD = TOOLS / "rebuild_doc_indexes.py"

_CAT_RE = re.compile(r"^[A-Z][A-Z_]*$")            # a top-level [CATEGORY] renders UPPER_SNAKE
_TAG_RE = re.compile(r"^[a-z][a-z0-9-]*$")         # a [TAG] value stores lower-hyphen


def insert_category(text, name):
    """Append a top-level [CATEGORY] token to the ```category-set``` fence. PURE. Returns (text, err)."""
    if re.search(r"(?m)^\s*(#.*)?\b" + re.escape(name) + r"\b", _fence_body(text)):
        return text, f"[{name}] already in the category-set fence"
    m = re.search(r"(```category-set\n.*?\n)(```)", text, re.DOTALL)
    if not m:
        return text, "category-set fence not found in the schema spec"
    return text[:m.end(1)] + f"{name}\n" + text[m.end(1):], None


def _fence_body(text):
    m = re.search(r"```category-set\n(.*?)\n```", text, re.DOTALL)
    return m.group(1) if m else ""


def insert_tag_row(text, axis, tag, desc):
    """Insert `| `tag` | desc |` at the end of the CONCERN or SURFACE table. PURE. Returns (text, err)."""
    if re.search(r"(?m)^\|\s*`" + re.escape(tag) + r"`\s*\|", text):
        return text, f"[TAG] value `{tag}` already in doc-tag-vocabulary.md"
    header_re = re.compile(r"(?m)^##\s+" + ("CONCERN" if axis == "concern" else "SURFACE") + r"\s+axis\b")
    hm = header_re.search(text)
    if not hm:
        return text, f"'{axis.upper()} axis' section not found in doc-tag-vocabulary.md"
    lines = text.split("\n")
    # find the header line index, then the last contiguous table (`|`-leading) row under it
    start = text[:hm.start()].count("\n")
    i, last_row = start + 1, None
    while i < len(lines):
        if lines[i].lstrip().startswith("|"):
            last_row = i
        elif last_row is not None and lines[i].strip() == "":
            pass                                    # blank line inside/after a table — keep scanning
        elif last_row is not None:
            break                                   # non-table content after the table → stop
        elif lines[i].startswith("## "):
            return text, f"no table found under the {axis.upper()} axis header"
        i += 1
    if last_row is None:
        return text, f"no table found under the {axis.upper()} axis header"
    lines.insert(last_row + 1, f"| `{tag}` | {desc} |")
    return "\n".join(lines), None


def _regen_and_verify(axis, name):
    """Regen the indexes + confirm the new tag now DERIVES (auto-flow proof)."""
    r = subprocess.run([sys.executable, str(REBUILD)], capture_output=True, text=True)
    if r.returncode != 0:
        return f"rebuild_doc_indexes failed: {r.stderr.strip()[:200]}"
    if axis == "category":
        if name not in (load_categories() or set()):
            return f"[{name}] did not derive into the validator's category set after insert"
    else:
        from check_doc_metadata import load_vocabulary
        cv, sv = load_vocabulary()
        pool = cv if axis == "concern" else sv
        if name not in (pool or set()):
            return f"`{name}` did not derive into the {axis} vocab after insert"
    # currency: a second regen must be a no-op (indexes now stable)
    chk = subprocess.run([sys.executable, str(REBUILD), "--check"], capture_output=True, text=True)
    if chk.returncode != 0:
        return "index-currency --check still red after regen (unexpected)"
    return None


def run_selftest():
    ok = True
    # (a) category insert into a mock fence, then duplicate refusal
    mock = "prose\n```category-set\n# c\nALPHA BETA\n```\ntail\n"
    t1, e1 = insert_category(mock, "GAMMA")
    a = (e1 is None and "GAMMA\n```" in t1 and t1.count("GAMMA") == 1)
    _, e2 = insert_category(t1, "GAMMA")
    b = (e2 is not None and "already" in e2)
    _, e3 = insert_category(mock, "ALPHA")           # existing token → refused
    c = (e3 is not None)
    print(f"  {'✅' if a else '❌'} category insert appends the token to the fence")
    print(f"  {'✅' if b else '❌'} category insert refuses a duplicate (just-added)")
    print(f"  {'✅' if c else '❌'} category insert refuses an existing fence token")
    # (b) tag-row insert into a mock CONCERN table, then duplicate refusal
    vmock = ("## CONCERN axis (what)\n\n| Tag | Description |\n|---|---|\n"
             "| `alpha` | a |\n| `beta` | b |\n\n## SURFACE axis (where)\n\n| Tag | Description |\n|---|---|\n| `hot-path` | h |\n")
    v1, ve1 = insert_tag_row(vmock, "concern", "gamma", "g")
    d = (ve1 is None and "| `gamma` | g |" in v1 and v1.index("`gamma`") < v1.index("## SURFACE"))
    _, ve2 = insert_tag_row(v1, "concern", "gamma", "g")
    e = (ve2 is not None and "already" in ve2)
    v3, ve3 = insert_tag_row(vmock, "surface", "slow-path", "s")
    f = (ve3 is None and "| `slow-path` | s |" in v3 and v3.index("`slow-path`") > v3.index("## SURFACE"))
    print(f"  {'✅' if d else '❌'} concern-tag row inserts into the CONCERN table (before SURFACE)")
    print(f"  {'✅' if e else '❌'} tag-row insert refuses a duplicate")
    print(f"  {'✅' if f else '❌'} surface-tag row inserts into the SURFACE table")
    return ok and a and b and c and d and e and f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--category", metavar="NAME", help="add a top-level [CATEGORY] to the fence (UPPER_SNAKE)")
    ap.add_argument("--concern", metavar="TAG", help="add a [TAG] CONCERN value (lower-hyphen)")
    ap.add_argument("--surface", metavar="TAG", help="add a [TAG] SURFACE value (lower-hyphen)")
    ap.add_argument("--desc", default="", help="the vocab-table Description (for --concern/--surface)")
    args = ap.parse_args()

    if args.selftest:
        print("add_vocab --selftest (pure insert helpers; no SSoT touched):")
        return 0 if run_selftest() else 2

    picks = [a for a in (args.category, args.concern, args.surface) if a]
    if len(picks) != 1:
        print("give EXACTLY one of --category / --concern / --surface", file=sys.stderr)
        return 1

    if args.category:
        if not _CAT_RE.match(args.category):
            print(f"a [CATEGORY] must be UPPER_SNAKE — got [{args.category}]", file=sys.stderr)
            return 1
        text = SCHEMA_PATH.read_text(encoding="utf-8")
        new, err = insert_category(text, args.category)
        if err:
            print(f"REFUSED: {err}", file=sys.stderr)
            return 1
        SCHEMA_PATH.write_text(new, encoding="utf-8")
        axis, name = "category", args.category
    else:
        axis = "concern" if args.concern else "surface"
        tag = args.concern or args.surface
        if not _TAG_RE.match(tag):
            print(f"a [TAG] value must be lower-hyphen — got `{tag}`", file=sys.stderr)
            return 1
        if not args.desc:
            print("--concern/--surface need a --desc (the vocab-table Description)", file=sys.stderr)
            return 1
        text = VOCAB_PATH.read_text(encoding="utf-8")
        new, err = insert_tag_row(text, axis, tag, args.desc)
        if err:
            print(f"REFUSED: {err}", file=sys.stderr)
            return 1
        VOCAB_PATH.write_text(new, encoding="utf-8")
        name = tag

    verr = _regen_and_verify(axis, name)
    if verr:
        print(f"ADDED but VERIFY failed: {verr}", file=sys.stderr)
        return 1
    print(f"✅ added {axis} `{name}` → SSoT updated + indexes regen'd + it derives + currency clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
