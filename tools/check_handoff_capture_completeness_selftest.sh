#!/bin/bash
# Teeth-proof selftest for check_handoff_capture_completeness.py (.E.1.0).
# Delegates to the check's --selftest mode: proves it REJECTS a missing / thin /
# placeholder Capture-completeness section and ACCEPTS a full one. A capture-
# completeness guard that can't be shown to reject a bad section is theater.
exec python3 "$(dirname "$0")/check_handoff_capture_completeness.py" --selftest
