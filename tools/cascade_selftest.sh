#!/usr/bin/env bash
# cascade_selftest.sh — the D-137 negative self-test entry for cascade.py (TD-175a).
# Drives `cascade.py --selftest`: a planted stale FOREACH_PER_CORE_CFG_FIELD + a // comment-resident
# token MUST be caught (positive controls), while PRESERVE (ExecutionCore/FoxML_Core/cpu_id) +
# experiments/per_core_sharding/ MUST be spared (false-positive guards). Proves the enumerator HAS TEETH
# (non-vacuity, Class-51) — it is not a green-on-clean no-op. Run: bash tools/cascade_selftest.sh
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/cascade.py" --selftest
