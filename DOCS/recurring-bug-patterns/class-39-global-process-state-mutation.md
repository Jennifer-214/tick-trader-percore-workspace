# Class 39: Global process-state mutation where a scoped/thread-local discipline is the established norm

## 1. Description
Mutating global process-wide state (like `setlocale`, `chdir`, or signal handlers) in a multi-threaded or performance-critical environment where such state is expected to be stable or managed via scoped/thread-local mechanisms.

## 2. Worked Instance (setlocale race, 2026-05-30)
The GUI thread called `setlocale(LC_NUMERIC, "C")` to format a display string, assuming it was safe. In a multi-threaded engine, this causes a data race with other threads that might be parsing market data or calculating fingerprints, leading to non-deterministic execution and crashes.

## 3. Structural Fix
- **Authority:** Establish global state once at boot and forbid mutation thereafter.
- **Scoped Alternatives:** Use thread-local alternatives (e.g., `uselocale`) or state-independent primitives (e.g., `std::from_chars`) for localized needs.
- **Detection:** Use static analysis (grep-CI) to flag forbidden global mutations.
