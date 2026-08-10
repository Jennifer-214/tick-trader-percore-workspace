---
type: ledger-template
parent_index: DOCS/TECH_DEBT.md
covers: IN-FLIGHT-status TECH_DEBT entries (being addressed in an active sub-ship)
established: 2026-05-18
---

# TECH_DEBT — IN-FLIGHT entries

Sub-file for TECH_DEBT entries with `IN-FLIGHT` or `IN PROGRESS` status — actively being addressed by the in-flight sub-ship. Entries here should flip to CLOSED (and move to `closed.md`) at sub-ship close.

External cross-refs use canonical ID format `TECH_DEBT-NNN`. The ID is preserved across sub-files; `rg "TECH_DEBT-NNN"` finds the canonical entry in the appropriate sub-file automatically.

---

## Issues

*(EMPTY as of 2026-08-10 — both former residents re-homed to `open.md` at the (g)-4 contract-stale EXEMPLAR fix: neither was in any active sub-ship; TD-063's `.F.4e` trigger-ship was never cut, TD-092's `.A`-lands claim never landed. The tier stays for genuinely in-flight entries; `check_tech_debt.py --contract-stale` now guards against silent parking.)*
