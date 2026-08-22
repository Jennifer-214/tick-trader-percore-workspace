#!/usr/bin/env bash
# tools/migrate_model_layout.sh — D-431 flat -> nested model-layout migration.
#
# Moves every RETIRED flat family `models/<class>/<family>_horizon_<N>/` into
# the nested form `models/<class>/<family>/horizon_<N>/`. Stamps/HMAC are
# path-free (verified: no FOREACH_STAMP_BOUND key carries a path), so this is
# a pure rename — no re-signing, no byte changes.
#
# SAFETY:
#   - refuses to run while foxml_suite / engine_gui / engine are running
#     (a live trainer writing into the tree mid-move = corruption)
#   - prints the full plan, then asks for confirmation (unless --yes)
#   - only canonical `_horizon_<digits>` names move (the same grammar the
#     loader accepts); backups named outside the grammar are untouched
set -euo pipefail
cd "$(dirname "$0")/.."

YES=0
[[ "${1:-}" == "--yes" ]] && YES=1

if pgrep -f "foxml_suite|engine_gui|/engine$" >/dev/null 2>&1; then
    echo "REFUSED: close foxml_suite / engine_gui / engine first (live writers mid-move = corruption)." >&2
    pgrep -af "foxml_suite|engine_gui|/engine$" >&2
    exit 1
fi

plan=()
for class_dir in models/*/; do
    [[ -d "$class_dir" ]] || continue
    for d in "$class_dir"*_horizon_*/; do
        [[ -d "$d" ]] || continue
        name=$(basename "$d")
        # canonical grammar only: <family>_horizon_<digits>, digits canonical
        fam="${name%_horizon_*}"
        h="${name##*_horizon_}"
        [[ "$fam" != "$name" && "$h" =~ ^[1-9][0-9]{0,6}$ ]] || continue
        plan+=("$class_dir$name -> $class_dir$fam/horizon_$h")
    done
done

if [[ ${#plan[@]} -eq 0 ]]; then
    echo "Nothing to migrate — no flat-form family dirs found."
    exit 0
fi

echo "MIGRATION PLAN (${#plan[@]} moves):"
printf '  %s\n' "${plan[@]}"
if [[ $YES -ne 1 ]]; then
    read -r -p "Proceed? [y/N] " ans
    [[ "$ans" == "y" || "$ans" == "Y" ]] || { echo "aborted."; exit 1; }
fi

for entry in "${plan[@]}"; do
    src="${entry%% -> *}"
    dst="${entry##* -> }"
    mkdir -p "$(dirname "$dst")"
    mv "$src" "$dst"
    echo "moved: $src -> $dst"
done

echo "DONE. Post-state:"
ls -d models/*/*/ 2>/dev/null | head -40
