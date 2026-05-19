# GEMINI_FINDINGS Cross-Referenced with Existing Design Specs and Tech Debt

Reviewing the `MASTER_SORTED_BACKLOG.md` against the project's design philosophy (`CLAUDE.md`, `CLAUDE.local.md`), `DOCS/TECH_DEBT.md`, and `DESIGN_SPECS/`, several findings can be structurally resolved using established architectural patterns. 

Following the core philosophy: **"Structural fix preferred when bug class can recur" (CLAUDE.md item 19)**, we should apply these compile-time enforcement patterns rather than making direct inline patches.

## 1. Config Parsing & Struct Duplication
- **Findings:** 
  - **123. Key-Value Config Parsing Duplication:** Config parsing is duplicated across `.cfg`, `.stamp`, and `.secrets`.
  - **120. O(N) JSON Scanning Duplication:** Custom JSON extraction scattered across data streams.
- **Existing Solution / Tech Debt:**
  - **`TECH_DEBT-009` (FOREACH_CFG_FIELD registry):** Solves config duplication by centralizing non-stamp-bound config fields into an X-macro registry. 
  - **`DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md`:** Utilized alongside `FOREACH_CFG_FIELD` to completely eliminate parallel implementations and boilerplate.
  - **`TECH_DEBT-022`:** Recommends a trie-based dispatch for config parsing, replacing duplicated line-by-line `strcmp` code.

## 2. Hot-Path Branches and Logic Drift
- **Findings:** 
  - **27 & 28. Conditional Branches on Hot Path:** `active_b` and `BuyGate` conditional branches violate the zero-branch invariant.
  - **122. Gate Evaluation Logic Drift:** Duplicate evaluation logic in `ExecutionCore` and `GateParameters`.
- **Existing Solution / Tech Debt:**
  - **`DESIGN_SPECS/framework-patterns/bitmap-flag-api.md` & `TECH_DEBT-013` (Bit-packed boolean flags):** Introduce `BIT_FLAG` storage classes to turn conditional logic (`if (pass)`) into branchless mask evaluations (`flags & MASK`).
  - **`DESIGN_SPECS/framework-patterns/slow-path-gate-registry-pattern.md`:** Standardizes gate evaluation, eliminating drift between hot and slow paths by centralizing the logic.

## 3. False Sharing and Cache Line Layout Hazards
- **Findings:** 
  - **124. ParameterSlot Pad Underflow / Straddling**
  - **125. False Sharing on BinanceUserDataState Atomics**
  - **126. False Sharing on OrderEventLog Atomics**
  - **130. EventLoopState Unaligned Arrays**
- **Existing Solution / Tech Debt:**
  - **`DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md`:** This spec explicitly addresses **Cache-layout discipline**. It dictates that data domains should be split based on read/mutate cadences to avoid false sharing. Applying the "Domain Split" strategy (as seen in `TECH_DEBT-019` rejection rationale) to these structs will structurally prevent cache line bouncing and L1 cache evictions.

## 4. ODR Violations and Array Bounds Issues
- **Findings:** 
  - **133. GUI Theme Color Array Out-of-Bounds:** Array size doesn't dynamically scale with strategy IDs.
  - **134. ODR/Static Linkage Violation in Header Functions:** Local static variables causing translation unit fragmentation.
- **Existing Solution / Tech Debt:**
  - **`DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md`:** Using the X-macro registry for strategies ensures that arrays (like `strat_colors[sid]`) are dimensioned correctly at compile time according to the registry length.
  - **`DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md`:** Advocates for compile-time enforcement over direct patches, directly solving out-of-bounds risks without runtime bounds-checks.

## Summary of Actionable Next Steps
Instead of addressing the `GEMINI_FINDINGS` issues piecemeal:
1. Extract the config and gate logic into `FOREACH_` macros and `AUTOPOPULATE` definitions (`TECH_DEBT-009`, `TECH_DEBT-013`).
2. Fix all false-sharing cache issues in a single structural sweep guided by `heterogeneous-registry-pattern.md` to ensure L1/L2 cache efficiency.
3. Migrate all remaining true bugs from `MASTER_SORTED_BACKLOG.md` into `DOCS/PARITY_ISSUES.md` and technical debt into `DOCS/TECH_DEBT.md` to adhere to the ledgering rules in `CLAUDE.local.md`.