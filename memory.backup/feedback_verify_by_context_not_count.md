---
name: feedback_verify_by_context_not_count
description: "Verification means READING what the matches/refs ARE, not counting their presence/absence. A token grep-COUNT misleads BOTH ways: a symbol present can be inert (tombstone / comment / build-fingerprint); a symbol absent can be renamed/moved. Disposition flips only on reading the context, never on the count. Corollary: never bundle rg short-flags (`-rln` = `-r ln` = `--replace ln`, silently mangles output)."
metadata: 
  node_type: memory
  type: feedback
  tags: [audit-methodology, scope-discipline]
  originSessionId: 3e806606-ac69-40fd-ac33-45906443bae4
  sister_specs: [feedback_enumerate_set_before_categorical_claim.md, feedback_passing_test_is_not_verification.md, feedback_run_doc_ci_tools_first_never_hand_verify.md, feedback_tag_disposition_at_fix_time.md]
---

To verify a claim ("X is removed", "Y is closed", "Z still exists"), **read what each match/ref IS** — never conclude from the COUNT of a token. grep-count lies in *both* directions:
- **present-but-inert:** `USE_NATIVE_128` showed 8 refs after the numeric core, but every one was a build-fingerprint string or a provenance comment — the native code path was gone (`FixedPointN.hpp:1246` "the flag is inert"). Counting "8 refs" → wrong "still live"; counting "0 refs" would have been → wrong "gone." Only reading the refs gave the truth.
- **absent-but-renamed:** a symbol with 0 hits may have MOVED/renamed, not been deleted (the `.E.1` core→node rename will do exactly this to ~5,000 symbols).

**Why:** this session disposed the fpmem cluster by grep-count twice — "removed entirely," then "still present, not closed" — *both wrong*; the verified-closed answer needed reading the context. The token count is a LOCATOR, never a verdict.

**Corollary — tool-flag hygiene (recurred 4× in ONE session despite flagging):** `rg -rln "X"` parses as `-r ln` (`--replace ln`) and silently display-replaces every match with "ln" → the output LIES (catalog AR-5, evidence-destruction). Use `rg -l` (files) or `rg -n` (lines); **NEVER bundle `-rln`.** Verify the verifier's own invocation (flag parsing) before trusting surprising output. Sisters: [[feedback_run_doc_ci_tools_first_never_hand_verify]] (run the tool — but read its REAL output), [[feedback_enumerate_set_before_categorical_claim]] (AR-1, the un-enumerated-set sibling), [[feedback_tag_disposition_at_fix_time]] (disposition flips on a code READ, not an assumption).
