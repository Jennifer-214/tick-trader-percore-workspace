---
name: feedback_rename_enumerator_is_world2_aid_compiler_is_world1
description: "A rename-enumeration tool de-risks the COMPILER-BLIND surface (apparatus/docs); the COMPILER is the code-consumer-completeness oracle — budget a red→green loop for the enumerator's narrow spots, don't expect it to be code-complete."
metadata: 
  node_type: memory
  type: feedback
  tags: [audit-methodology, enumeration-discipline, refactor-discipline, structural-fix]
  sister_specs: [DESIGN_SPECS/refactor-patterns/rename-cascade-enumeration-tooling.md, DESIGN_SPECS/refactor-patterns/rename-ship-methodology.md, feedback_capture_and_check_are_model_bounded.md]
  originSessionId: e6c2096e-4638-4f6a-85ad-a529d9b9bd31
---

A rename-enumeration tool (`cascade.py` / the frozen worklist) is a **World-2 planning aid** — it enumerates the **compiler-BLIND** surface (`tools/` regexes, `build.sh`, `.githooks/`, and the build/doc-CI-bound DATA docs: `MANUAL_FIELDS_INVENTORY.md`, `DOCS/TOOLS.md`, skill `SKILL.md` tool-refs, plan citations). It is NOT a code-completeness guarantor. The **COMPILER is the World-1 oracle** for code consumers: a half-renamed code tree won't compile, so red→build→green IS code-consumer-completeness — *independent of how complete the enumerator is*.

**Why** (E.1.1 Core→Node, 3645 sites): the cascade matcher had systematic narrow spots — `.cores[` matched only dot-access (missed the `cores[16]` decl, `->cores[` arrow, bare `cores` array/param); `core_[a-z]` missed regex-metachar `core_` (`core_\w+`, `"core_"` parser prefix, `core_<digit>` filenames); the scan scope omitted `tests/`. The compiler caught EVERY code one (a 7-round red→green loop); the build + doc-CI gates caught the apparatus + doc-data-file ones (the integrity check's stale Section-A, the renamed-tool refs in 6 skills + CLAUDE.md). An a-class audit even found the matcher ~42% short BEFORE the rename — yet even a "complete" enumerator wouldn't have been *code*-complete; only the compiler is.

**How to apply:**
1. **Build the enumerator for the compiler-BLIND surface** (its unique value); do NOT over-invest in making it code-complete.
2. **Budget a red→green compile loop** — the enumerator's narrow spots (bare-field/decl/arrow access, regex-metachar tokens, scope-gaps like `tests/`) surface there; that's *expected*, not failure.
3. **The build + doc-CI gates are the backstop** for apparatus + build-bound **doc-data-files** — co-migrate those WITH the code (a distinct bucket from the Phase-5 narrative-doc sweep, which preserves history).
4. **Adversarially verify the enumerator's completeness for its OWN (World-2) scope** (the a-class / `freeze ⊇ raw-rg`), but know the compiler owns World-1. The enumerator's gaps are model-bounded — the builder can't enumerate what they didn't imagine; the compiler + gates are the EXTERNAL check ([[feedback_capture_and_check_are_model_bounded]]).
