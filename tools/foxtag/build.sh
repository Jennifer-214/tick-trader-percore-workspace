#!/usr/bin/env bash
# build.sh — build the foxtag core CLI (D-337 increment 1). Dev-plane tool; g++ only.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
g++ -std=c++20 -O2 -Wall -Wextra -Werror -o "$HERE/foxtag" "$HERE/foxtag_main.cpp"
echo "[foxtag] built: $HERE/foxtag"
