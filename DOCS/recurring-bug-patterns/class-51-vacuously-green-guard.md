# Class 51 — Vacuously-green guard (a check reports PASS without exercising its target)

> Codified 2026-06-16 at v5.15.5.F.4d.1.E.1.0 (the H8 static latency-path conformance-analyzer build — the tool that, *being* a guard, would itself have shipped vacuously-green absent its non-vacuity self-defense; first canonical + a 5-pass independent-adversarial verification). Per-class file per file-size-split-discipline. **H-promotion deferred to Stage 5** per pattern-codification-lifecycle.

## Shape

A guard / test / CI check reports **GREEN not because the checked property HOLDS, but because the check never actually EXERCISED its target.** The green is **vacuous** — it asserts nothing, yet reads as "verified." This is the **false-NEGATIVE masquerading as a PASS**: the most dangerous guard state, because a vacuous green is indistinguishable from an earned green to everyone downstream.

Its **INVERSE** — a guard that flags *correct* code (false-RED, "the guard reproducing the disease") — is documented at `DESIGN_SPECS/meta-disciplines/mechanical-verification-of-derived-code-facts.md` § "The INVERSE failure". Both are the same root defect from opposite sides: **the guard is wrong about its target.** Class 51 = false-GREEN; the inverse = false-RED.

## Sub-shapes (the vacuity modes — each one caught during the conformance-analyzer build)

- **A — Optimized-away / non-existent target:** the guard inspects a symbol the compiler inlined-and-eliminated (the analyzer would have "passed" a budget over `RollingStats_Push`'s optimized-to-2-instruction wrapper) or a test exercises a path that is `#if`'d out → the check runs over **nothing**.
- **B — Empty-input / unreachable assertion:** the loop the assertion lives in iterates **zero times** (an empty manifest, a filtered-to-empty file list, a degenerate set) → the assert never fires → green.
- **B′ — Decorative detector (detected-but-un-gated):** a finding is computed + counted + even has TEETH, but the **top-level gate never CONSULTS it** → the count is decorative; the gate exits clean regardless. (The analyzer's **div-gate**: an integer `idiv` was detected / printed / teethed, but `main` never gated on it → a pure-integer-`idiv` function exited "clean.")
- **B″ — Wrong-region scan:** a positional / heuristic shortcut skips the region that must be checked → the scan never reaches the hazard → green over an unexamined body. (The analyzer's **cold-quartile false-green**: a `lo + 0.75·span` positional heuristic mis-classified a compute-then-delegate function's FINAL call as cold → the transitive scan skipped it.)
- **C — Trivially-satisfied proxy:** the check asserts a stand-in that is **true-by-construction** rather than the real property. (The H8-DESIGN catch, D-235: asserting `strategy_id == ML` would be vacuous because the ML-degrade *sets* that label → assert the FLAGS `MODEL_LOAD_FAILED | MODEL_CORRUPT == 0` + an inference-ran counter instead. Cf. the `price > 0` always-true sentinel, Class 48.)
- **D — Over-broad exemption:** an allow / skip list waves through more than intended. (The analyzer's **forbidden-file-level hole**: a FILE-level `allow` meant for the float/div feature-seam was also exempting `malloc`/stdio on that file → forbidden-calls must exempt by `file:line`-ONLY, never file-level.)

## Detection heuristic

Flag any guard whose **GREEN does not ENTAIL the property.** Look for:
- (a) an assertion inside a loop/branch that **can be empty or unreached**;
- (b) a target resolved by **name/symbol that may not exist** or be optimized away;
- (c) a PASS path that **does not require the checked quantity to have been computed/consulted** (the detector exists but the gate doesn't read it);
- (d) teeth that prove the check goes **RED on a violation** but **no positive-control** proving it actually RAN on the real target;
- (e) an **exemption broader than the seam** it is meant to cover.

(No single mechanical signature — the shape is "the assurance is illusory." The discriminator is always: *does a green HERE mean the property HOLDS?* — a `/trace-deps` / read of the gate's pass-path confirms.)

## Structural fix — every guard ASSERTS ITS OWN NON-VACUITY

A guard must **prove it exercised its target before it may report green:**

- **Assert the target was found + the body is non-trivial** — the analyzer's founding self-defense: symbol found + real inlined body present, else **fail LOUD** (refuse to grade an empty body), never pass silently. (Mode A.)
- **Assert the input set is non-empty** — fail-loud on an empty manifest / file-list rather than vacuously pass. (Mode B.)
- **SINGLE-SOURCE the gate** so a detected-but-un-gated finding is *structurally impossible* — the analyzer's `_hard_findings` is the ONE place that decides pass/fail, so the teeth assert the GATE, not a count. (Mode B′.)
- **Make the scan STRUCTURAL, not positional** — recurse into the actual callees; never a "last-quartile" heuristic. (Mode B″.)
- **Assert the FLAGS / the computed signal, never a self-fulfilling label-proxy.** (Mode C.)
- **Scope exemptions to the narrowest key that is correct** — forbidden-calls by `file:line`, never file-level. (Mode D.)
- **Teeth MUST include a POSITIVE control** — prove the check RAN on the real target and goes green only when the property genuinely holds — not merely a negative control that proves it CAN go red.

## The meta-lesson (why this is hard to self-catch)

The **BUILDER of a guard is MODEL-BOUNDED** — they cannot write a non-vacuity self-check for a vacuity mode they did not imagine (AR-8, `meta-anti-pattern-index.md`). So vacuously-green guards are caught by **INDEPENDENT adversarial review, not the builder's dogfood**: the conformance analyzer needed **FIVE** independent passes, each surfacing a vacuity hole the builder's own teeth had declared clean (the div-gate, the cold-quartile, the forbidden-file-level). This is why **Class 51 + AR-8 + TECH_DEBT-207** (independent-review-by-default for mid-session tool builds) are siblings — the guard catches the bug class; the review process catches the guard.

## Instances (recurrence_count = 1 canonical tool / 5 distinct vacuity modes + the documented inverse)

- **CANONICAL — the H8 static latency-path conformance analyzer** (`tools/check_latency_path_conformance.py`): a guard that, absent the self-defense, would have shipped vacuously-green. Modes **A** (the optimized-away-wrapper non-vacuity — the founding self-defense), **B′** (the decorative div-gate), **B″** (the cold-quartile false-green), **C** (the ML-degrade label-proxy — caught at DESIGN time, D-235), **D** (the forbidden-file-level exemption). Each fixed structurally; the tool now fail-louds on its own vacuity. Design + lessons: `DESIGN_SPECS/audit-methodologies/static-latency-path-conformance-analysis.md`.
- **INVERSE (documented sibling)** — `check_struct_size_budget.py` false-RED of `ExecutionCore` (the guard reproducing the disease in the other direction; `mechanical-verification-of-derived-code-facts.md` § "The INVERSE failure").

## Distinct from / sibling of

- **The INVERSE = false-RED** (correct code flagged) — `mechanical-verification-of-derived-code-facts.md` § "The INVERSE failure". Class 51 = false-GREEN, the same defect from the opposite side.
- **Class 38 (Phantom Invariant)** — Class 38 = NO guard exists (an invariant asserted in a comment, established by neither code nor guard); Class 51 = a guard EXISTS but is vacuous. Siblings: both = "the assurance is illusory."
- **Class 12 (wired-but-unexercised ML paths)** — the test-surface sibling (a path "wired" but no test exercises it); Class 51 generalizes the "exists but never actually runs" shape to GUARDS / CHECKS.
- **AR-8 (self-attested verification, meta-anti-pattern-index)** — the META sibling: a self-attested green over a vacuous guard is the *doubled* failure (the maker grades its own check, and the check tests nothing).

## Closure mechanism

- The **non-vacuity-self-assertion discipline** — every new guard must prove it exercised its target; first canonicalized by the conformance analyzer (`DESIGN_SPECS/audit-methodologies/static-latency-path-conformance-analysis.md`).
- **Independent adversarial review of guard / tool builds** (TECH_DEBT-207 — the M7 escalation; the builder's dogfood is model-bounded).
- The **"teeth include a positive control"** rule — the `--selftest` proves the check RAN on the real target, not just that it CAN go red.

## False-positive surface (per M3)

- **A genuinely-satisfied guard is NOT vacuous** — the property holds AND the check exercised the target on non-empty input. Green-because-correct ≠ green-because-vacuous; the discriminator is whether the check EXERCISED its target.
- **A forward-looking guard, green because no instance exists YET, is NOT vacuous** — *if* it would go red when one appears (a correct empty-set pass). The flag fires only when green does not entail the property EVEN WITH a violation present.
- **A narrow mechanical/consistency gate** (well-formed-citation, sister-symmetry) is not vacuous for ITS scope — it is just narrow (the AR-8 mechanical-green sub-shape: a green consistency gate ≠ content-verified, but it is not vacuous about the consistency it actually checks). Run the content pass too; don't mistake **narrow** for **vacuous**.
