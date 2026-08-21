---
name: feedback-plugin-livepath-verification-before-done
description: Plugin/apparatus work is NOT done at pure-suite green — the LIVE path (subprocess/async/window seams) must be exercised before claiming done
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9992e141-647b-421e-8a7c-529b080257d9
  modified: 2026-08-20T00:36:15.001Z
  sister_specs: [feedback_adversarial_framing_default_for_checks.md, feedback_passing_test_is_not_verification.md, feedback_process_weight_by_surface_blast_radius.md]
  tags: []
---

Operator rule (2026-08-18, verbatim): *"like any future work on the plugin we need to verify it actually works before we say its done."*

**Why:** the fox-symdeps branchtag rework shipped with the pure suite 47/47 green while the SHIPPED feature was 100% dead — the awk program string carried Lua-interpreted newlines (`'\n'` in Lua single quotes is a real newline → awk "unterminated string", exit 1; the overlay silently painted nothing). Every unit test AND a bash-side probe of the same awk program passed, because none crossed the Lua→subprocess seam. The operator caught it live within minutes of it being called done. Green proved the pure functions, not the product ([[feedback_passing_test_is_not_verification]] instantiated at the plugin plane).

**How to apply:**
- Any plugin/toolchain change touching a **subprocess, async, or window seam** ships WITH a `test_*_live.lua` suite member that drives the REAL path (fixture tree on disk, real spawn, real windows/extmarks) — precedents: `test_branchtag_live.lua`, `test_fuzzy_live.lua`.
- "Done" claims must NAME their live evidence: the live test run, a headless full-path exercise against real data, or an explicit operator dogfood.
- Headless `-l` cannot drive insert-mode typeahead (feedkeys `x!` silently ends the script) — interactive surfaces expose a **programmatic handle** (same functions the keys map to) as the test seam; that handle doubles as the programmatic API.
- Canonical home for the plugin-side statement: fox-symdeps `DOCS/DECISIONS.md` § "Live-path verification before done".

Sisters: [[feedback_passing_test_is_not_verification]] · [[feedback_adversarial_framing_default_for_checks]] · [[feedback_process_weight_by_surface_blast_radius]] (the fact-producer carve-out — a wrong overlay verdict misleads judgment on a branchless-discipline engine, so apparatus-plane lightness never excuses skipping the live check).
