#!/usr/bin/env bash
# parity_check.sh — the D-337 migration gate: the C++ core must match the Python oracle
# (check_code_tag_blocks.py) EXACTLY before any CI consumer cuts over. Golden-master
# discipline: (1) validate output — header line, sorted violation lines, verdict, exit code;
# (2) unit/tag inventory — sorted U|/T| dumps; (3) grammar counts (both SSoT-derived).
# PASS = the core may be consumed; FAIL = the Python stays authoritative. Exit 0/1.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
[ -f "$ROOT/Version.hpp" ] || ROOT="$(dirname "$ROOT")/FoxML_Trader_v2"
if [ ! -f "$ROOT/Version.hpp" ]; then echo "FAIL: cannot resolve engine root"; exit 1; fi
TOOLS="$ROOT/tools"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FAIL=0

bash "$HERE/build.sh" >/dev/null

# --- 1. validate parity ------------------------------------------------------
( cd "$ROOT" && python3 "$TOOLS/check_code_tag_blocks.py" ) > "$TMP/py.out"; PY_RC=$?
( cd "$ROOT" && "$HERE/foxtag" validate ) > "$TMP/cxx.out"; CXX_RC=$?

head -1 "$TMP/py.out"  > "$TMP/py.head";  head -1 "$TMP/cxx.out" > "$TMP/cxx.head"
grep '^  ' "$TMP/py.out"  | sort > "$TMP/py.viol"  || true
grep '^  ' "$TMP/cxx.out" | sort > "$TMP/cxx.viol" || true

if ! diff -q "$TMP/py.head" "$TMP/cxx.head" >/dev/null; then
    echo "FAIL: header line differs"; diff "$TMP/py.head" "$TMP/cxx.head" || true; FAIL=1
else echo "OK  : header line identical ($(cat "$TMP/py.head"))"; fi

if ! diff -q "$TMP/py.viol" "$TMP/cxx.viol" >/dev/null; then
    echo "FAIL: violation sets differ:"; diff "$TMP/py.viol" "$TMP/cxx.viol" || true; FAIL=1
else echo "OK  : violations identical ($(wc -l < "$TMP/py.viol") line(s))"; fi

if [ "$PY_RC" != "$CXX_RC" ]; then
    echo "FAIL: exit codes differ (py=$PY_RC cxx=$CXX_RC)"; FAIL=1
else echo "OK  : exit codes identical ($PY_RC)"; fi

# --- 2. unit/tag inventory parity ---------------------------------------------
( cd "$ROOT" && python3 - <<'EOF'
import sys, pathlib
sys.path.insert(0, str(pathlib.Path("tools").absolute()))
from check_code_tag_blocks import engine_source_files, collect_file_tags
rows = []
for f in engine_source_files():
    units, tags = collect_file_tags(f)
    for (t, n, ln) in units: rows.append(f"U|{f}|{t}|{n}|{ln}")
    for tg in tags: rows.append(f"T|{f}|{tg}")
print("\n".join(sorted(rows)))
EOF
) > "$TMP/py.dump"
( cd "$ROOT" && "$HERE/foxtag" parity-dump ) > "$TMP/cxx.dump"

if ! diff -q "$TMP/py.dump" "$TMP/cxx.dump" >/dev/null; then
    echo "FAIL: unit/tag inventory differs:"; diff "$TMP/py.dump" "$TMP/cxx.dump" | head -30 || true; FAIL=1
else echo "OK  : unit/tag inventory identical ($(wc -l < "$TMP/py.dump") row(s))"; fi

# --- 3. grammar counts ---------------------------------------------------------
PY_G=$( cd "$ROOT" && python3 - <<'EOF'
import sys, pathlib
sys.path.insert(0, str(pathlib.Path("tools").absolute()))
from check_code_tag_blocks import load_categories, load_ref_subcats
from check_doc_metadata import load_vocabulary
c, s = load_vocabulary()
print(f"categories={len(load_categories())} ref_subcats={len(load_ref_subcats())} "
      f"concern={len(c)} surface={len(s)}")
EOF
)
CXX_G=$( cd "$ROOT" && "$HERE/foxtag" grammar )
if [ "$PY_G" != "$CXX_G" ]; then
    echo "FAIL: grammar counts differ (py: $PY_G | cxx: $CXX_G)"; FAIL=1
else echo "OK  : grammar counts identical ($CXX_G)"; fi

# --- 4. LAYOUT-producer parity (foxtag layout vs emit_record_layout.lua on the same TU;
# ---    needs nvim + clang++; SKIP-advisory when absent — mirrors the cache-gate's dep policy)
if command -v nvim >/dev/null 2>&1 && command -v clang++ >/dev/null 2>&1 && [ -f "$ROOT/main.cpp" ]; then
    ( cd "$ROOT" && nvim --headless --clean -u NONE -l tools/emit_record_layout.lua main.cpp ) \
        > "$TMP/lua.layout" 2>"$TMP/lua.layout.err" || true
    ( cd "$ROOT" && "$HERE/foxtag" layout main.cpp ) > "$TMP/cxx.layout" 2>"$TMP/cxx.layout.err" || true
    if [ ! -s "$TMP/lua.layout" ] || [ ! -s "$TMP/cxx.layout" ]; then
        echo "FAIL: layout producer(s) emitted nothing (lua: $(head -c120 "$TMP/lua.layout.err"); cxx: $(head -c120 "$TMP/cxx.layout.err"))"
        FAIL=1
    elif python3 - "$TMP/lua.layout" "$TMP/cxx.layout" <<'EOF'
import json, sys
a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2]))
def norm(d):
    return {k: {"size": v.get("size"), "align": v.get("align"),
                "straddlers": sorted((s["name"], s["off"], s["size"])
                                     for s in (v.get("straddlers") or []))}
            for k, v in d.items()}
na, nb = norm(a), norm(b)
if na == nb:
    print(f"OK  : layout parity ({len(na)} records, straddler-exact)"); sys.exit(0)
only_a, only_b = set(na) - set(nb), set(nb) - set(na)
diff = [k for k in set(na) & set(nb) if na[k] != nb[k]]
print(f"FAIL: layout differs — only-lua={len(only_a)} only-cxx={len(only_b)} value-diff={len(diff)}")
for k in sorted(only_a)[:5]: print("  only-lua:", k)
for k in sorted(only_b)[:5]: print("  only-cxx:", k)
for k in sorted(diff)[:5]:   print("  diff:", k, "lua=", na[k], "cxx=", nb[k])
sys.exit(1)
EOF
    then :; else FAIL=1; fi
else
    echo "SKIP: layout parity (nvim/clang++/main.cpp unavailable — advisory, mirrors the cache-gate)"
fi

# --- verdict -------------------------------------------------------------------
if [ "$FAIL" = 0 ]; then echo "PARITY: PASS — the core matches the Python oracle"; exit 0
else echo "PARITY: FAIL — the Python tools stay authoritative"; exit 1; fi
