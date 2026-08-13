#!/usr/bin/env python3
"""compile_command.py — the ONE compile-command source (TD-257 substrate; ideas §2, D-397).

Given source file(s), resolve the EXACT invocation the build database records for them —
`compile_commands.json`, discovered at the engine-root symlink (the clangd convention the
layout probes already stand on) — and emit it two ways:

  default : a terminal-pasteable line per RESOLVED file — `(cd <dir> && <command>)` — so the
            IDENTICAL command the tooling compiled with is reproducible OUTSIDE any consumer
            ("custom compiler work eventually" consumes this, never a second flag source).
  --json  : ONE `compile_command/1` toolio envelope (table `commands`: file · status ·
            directory · command) — the plugin's 0.5 asm/layout cards + any harness consume
            THIS (one command source, N consumers — D-337 applied to compiler invocations).

Tri-state honest (Class 57): a file with no db entry is a MISSING row (a header is not a TU;
the header→enclosing-TU mapping is 0.5 design work, NOT improvised here) — rc 0 includes
MISSING rows (resolution RAN; absence is a fact). An unreadable/undecodable db is a REFUSAL
(rc 2) — the tool failing is a different fact than a file lacking an entry.

The envelope carries the db path so consumers can see WHICH database answered — today the
root symlink points at build_clangd/ (editor-parity flags); the shipping-build db
(CMAKE_EXPORT_COMPILE_COMMANDS into build/) rides the build.sh 1:1-asm leaf, and this tool
takes `--db` so that cutover is a flag, not a rewrite.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent))  # .absolute() NOT .resolve() (Landmine 5: tools/ is a symlink)
from foxroots import ENGINE  # SSoT root resolver (D-375; import-from-core lint enforces)

_PRODUCER = {"tool": "compile_command", "version": "1.0", "command": "resolve", "args": []}
DEFAULT_DB = ENGINE / "compile_commands.json"   # the root symlink — the discovery convention


class Refusal(Exception):
    """The database itself could not be read — rc 2, never an empty-resolution pass."""


def load_db(db_path: Path):
    if not db_path.is_file() and not db_path.is_symlink():
        raise Refusal(f"compile database unreadable: {db_path}")
    try:
        entries = json.loads(db_path.read_text())
    except (ValueError, OSError) as e:
        raise Refusal(f"compile database undecodable: {db_path} ({e})")
    if not isinstance(entries, list):
        raise Refusal(f"compile database is not a list: {db_path}")
    return entries


def resolve_rows(files, entries):
    """[file, status, directory, command] rows — ONE ROW PER DB ENTRY for a file (a TU compiled
    into several targets — engine / engine_gui / suite — has several REAL invocations; keeping
    one silently would be the exact flag-divergence this tool exists to kill). MISSING = honest
    empties (never omitted, never guessed)."""
    by_file = {}
    for e in entries:
        f = e.get("file")
        if f:
            by_file.setdefault(str(Path(f)), []).append(e)
    rows = []
    for f in files:
        p = Path(f)
        key = str(p if p.is_absolute() else (ENGINE / p))
        matches = by_file.get(key)
        if not matches:
            rows.append([f, "MISSING", "", ""])
        else:
            for e in matches:
                rows.append([f, "RESOLVED", e.get("directory", ""), e.get("command", "")])
    return rows


def _git_head():
    try:
        return subprocess.run(["git", "-C", str(ENGINE), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10).stdout.strip() or "unknown"
    except (subprocess.SubprocessError, OSError):
        return "unknown"


def emit_json(rows, db_path: Path):
    import toolio
    env = toolio.emit("compile_command/1", {"commands": rows},
                      producer=dict(_PRODUCER, args=[str(db_path)] + [r[0] for r in rows]),
                      git_head=_git_head(), schema_version="1")
    print(json.dumps(env))


def emit_human(rows, db_path: Path):
    print(f"# db: {db_path} → {db_path.resolve()}" if db_path.is_symlink() else f"# db: {db_path}")
    for f, status, directory, command in rows:
        if status == "RESOLVED":
            print(f"(cd {directory} && {command})")
        else:
            print(f"# {f}: MISSING — no TU entry in this db (a header? the enclosing-TU mapping is 0.5 design work)")


def run(files, db_path: Path, as_json: bool) -> int:
    try:
        entries = load_db(db_path)
    except Refusal as e:
        print(f"REFUSAL (not a clean pass): {e}", file=sys.stderr)
        return 2
    rows = resolve_rows(files, entries)
    (emit_json if as_json else emit_human)(rows, db_path)
    return 0


# ── selftest (T5 non-vacuity: every claim planted + rc-checked; expect_red on refusal) ──────────

def selftest() -> int:
    teeth, failed = 0, 0

    def tooth(name, cond):
        nonlocal teeth, failed
        teeth += 1
        if not cond:
            failed += 1
            print(f"  ✗ tooth: {name}")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        db = tmp / "compile_commands.json"
        tu = str(ENGINE / "main.cpp")
        db.write_text(json.dumps([{"directory": "/b", "command": "c++ -O3 -c main.cpp",
                                   "file": tu, "output": "main.o"}]))
        rows = resolve_rows([tu, "not/a/tu.hpp"], load_db(db))
        tooth("exact TU RESOLVED with the db's verbatim command",
              rows[0][1] == "RESOLVED" and rows[0][3] == "c++ -O3 -c main.cpp" and rows[0][2] == "/b")
        tooth("no-entry file = honest MISSING row (present, empty command — never omitted)",
              rows[1][1] == "MISSING" and rows[1][3] == "")
        tooth("engine-relative input resolves to the same absolute key",
              resolve_rows(["main.cpp"], load_db(db))[0][1] == "RESOLVED")

        # multi-target TU: BOTH real invocations emitted — keeping one silently is the
        # flag-divergence this tool exists to kill
        db.write_text(json.dumps([
            {"directory": "/b", "command": "c++ -O3 -c main.cpp", "file": tu},
            {"directory": "/b2", "command": "c++ -O3 -DUSE_IMGUI_GUI -c main.cpp", "file": tu},
        ]))
        multi = resolve_rows([tu], load_db(db))
        tooth("multi-target TU emits ONE ROW PER ENTRY (2 targets → 2 rows, both verbatim)",
              len(multi) == 2 and {multi[0][2], multi[1][2]} == {"/b", "/b2"}
              and all(r[1] == "RESOLVED" for r in multi))

        db.write_text("{ not json")
        try:
            load_db(db)
            tooth("undecodable db = REFUSAL, never empty-pass", False)
        except Refusal:
            tooth("undecodable db = REFUSAL, never empty-pass", True)
        tooth("missing db file = REFUSAL rc2", run(["x"], tmp / "nope.json", False) == 2)

        # envelope round-trip through the registry (the schema row must exist + validate)
        import toolio
        env = toolio.emit("compile_command/1",
                          {"commands": [["f", "MISSING", "", ""]]},
                          producer=_PRODUCER, git_head="selftest", schema_version="1")
        rt = toolio.read(env)["commands"]
        tooth("compile_command/1 envelope round-trips with the registry schema",
              rt["schema"] == ["file", "status", "directory", "command"] and rt["rows"][0][1] == "MISSING")

    print(f"compile_command selftest: {teeth - failed}/{teeth} teeth pass")
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*", help="source file(s), absolute or engine-relative")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB,
                    help="compile database (default: the engine-root compile_commands.json symlink)")
    ap.add_argument("--json", action="store_true", help="emit ONE compile_command/1 toolio envelope")
    ap.add_argument("--selftest", action="store_true", help="teeth: planted RESOLVED/MISSING + refusal legs")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if not args.files:
        print("no files given (nothing to resolve; see --help)", file=sys.stderr)
        sys.exit(2)
    sys.exit(run(args.files, args.db, args.json))


if __name__ == "__main__":
    main()
