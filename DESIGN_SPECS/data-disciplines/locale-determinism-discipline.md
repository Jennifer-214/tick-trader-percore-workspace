---
type: data-discipline
name: locale-determinism-discipline
stage: 3-first-canonical
version: v1.0
established: 2026-05-31
sprint: v5.15-live-readiness
landing_ship: v5.15.5.F.4d.1.E.0.1
purpose: Process-wide SSoT for locale-determinism — one locale authority (the boot pin), global setlocale forbidden elsewhere, thread-local uselocale for emit defense-in-depth, and the tt:: parse + to_chars emit families as the locale-immune IO primitives. The superset that wire-format § 5b (emit-layer pinning) is one slice of.
tags: [determinism, locale, parsing, wire-format, process-state, concurrency, h5, h9]
surface: [boot-time, slow-path, ml-inference, wire-format, replay]
sister_specs:
  - wire-format-patterns/wire-format-byte-preservation-discipline.md
  - meta-disciplines/single-source-of-truth-discipline.md
  - meta-disciplines/structural-enforcement-when-memory-insufficient.md
related_classes: [Class 38 phantom-invariant, Class 39 global-process-state-mutation]
related_meta: [AR-3 documentation-accepted-as-verification]
---

# Locale-determinism discipline

**The discipline (one line).** `LC_NUMERIC` is pinned to `C` **once**, at boot, as the single
process-wide locale authority; nothing else may mutate the global locale; locale-sensitive IO uses
the locale-immune `tt::` parse family and `to_chars`/`format_double_canonical` emit; a CI guard makes
all of the above a red build if violated.

**Why it's load-bearing.** A non-`C` `LC_NUMERIC` makes `strtod`/`atof`/`printf("%f")` read and write
`0,55` instead of `0.55`. That silently (a) corrupts every replayed value vs the recorded golden
(replay determinism), (b) breaks backtest↔live parse symmetry, and (c) falsifies HMAC-signed wire
bytes (H9). It is a *global, ambient* failure: a single `setlocale` on any thread changes the meaning
of every numeric IO in the process. Determinism (the system's #2 priority after latency) cannot
tolerate an ambient global that any code can flip.

## The four rules

1. **Boot-pin authority.** `setlocale(LC_NUMERIC, "C")` runs as the first locale action of every
   **production** binary, before any thread starts or any numeric IO happens. This is the ONE place
   the global locale is set. After it, the whole process is `C` by construction — every `atof`/`strtod`
   site (migrated or not) is locale-safe *meanwhile*, which is what lets the raw-parse migration be paced
   (rule 4) rather than blocking.

2. **Global `setlocale` forbidden elsewhere.** No `setlocale(...)` outside the boot pins. A global
   `setlocale` from a non-boot (e.g. render) thread is a data race on process state AND a second locale
   authority (SSoT violation) — the exact bug `.E.0.1` closed by de-racing `StrategyQualityPanel` +
   `RunHistory`. Tests are the sole exception: they deliberately flip `LC_NUMERIC=de_DE` to *prove*
   immunity, and must therefore NOT be globally pinned.

3. **Thread-local `uselocale` for emit defense-in-depth.** Where a thread builds an HMAC/stamp body and
   wants belt-and-suspenders independent of the boot pin, use a thread-local
   `uselocale(newlocale(LC_NUMERIC_MASK,"C",0))` — scoped, race-free, redundant-but-harmless under the
   pin. This is the *only* sanctioned locale manipulation after boot.

4. **`tt::` parse + `to_chars` emit are the locale-immune IO primitives.** Parse via
   `tt::parse_double_fast` / `_advance` (and the checked int variants); emit via `std::to_chars`
   shortest-round-trip / `tt::format_double_canonical`. These are locale-immune by construction (they
   don't consult `LC_NUMERIC`), so they hold even if rules 1-2 are ever violated. The migration of the
   remaining raw `atof`/`strtod`/`atoi` sites to this family is a **deliberate, paced correctness change**
   (malformed input: silent `0` → handled) tracked as a shrinking KNOWN-PENDING manifest (TECH_DEBT-144),
   NOT a determinism blocker — the boot pin covers their locale exposure in the interim.

## Binary-specific boot-pin placement (a landmine)

The pin's placement is **binary-specific** because windowing/toolkit init can reset `LC_*`:

| Binary | Where the pin goes | Why |
|---|---|---|
| headless `engine` (`main.cpp`) | first line of `main` | nothing resets locale before it |
| `engine_gui` / `foxml_suite` | **after** `SDL_Init` (`GuiThread.hpp` / `foxml_suite.cpp`) | SDL/GTK/X11 call `setlocale(LC_ALL,"")` during init — pinning before would be clobbered |
| backtest entry / `tools/compare_scalers` | at entry, before replay | replays CSVs; same parse exposure |

(See `LANDMINES.md`.) Cross-binary `to_chars` float determinism additionally depends on libstdc++ ≥ gcc11.

## The guard (what makes it a red build, not a convention)

The convention is worthless without enforcement — the locale "engine boot pins this" comment at
`CoreModelZoo.hpp:2845` was true by *ambient-C luck* for an unknown span, with neither establishing
code nor a guard (the phantom invariant, Class 38 / AR-3). The guard is the structural answer:

- **`tools/check_locale_determinism.sh`** — (a) the boot pin is PRESENT in each production main; (b) NO
  global `setlocale` outside the boot pins + tests; (c) NO new raw `atof`/`strtod`/`atoi` beyond the
  shrinking KNOWN-PENDING baseline. Wired into **`tools/check_determinism.sh`** (the net) and **pre-commit
  Check F**.
- **`tools/check_determinism_selftest.sh`** — the negative self-test: it injects a stray `setlocale` and
  confirms the guard goes RED, so the guard is proven to have teeth (not trusted on GREEN-on-clean).

**Guard-coverage-matrix:** locale-determinism is now an **ENFORCED** row (was a HOLE/phantom) — boot-pin
presence + no-stray-global + raw-parse-baseline, all mechanically checked.

## Canonical-sister relationship

`wire-format-patterns/wire-format-byte-preservation-discipline.md` § 5b covers locale pinning **at the
emit site** for HMAC-signed wire bytes (Layer-2). This discipline is the **process-wide superset**: it
adds the boot-pin authority (rule 1), the global-`setlocale`-forbidden invariant (rule 2), and the
parse side (rule 4). § 5b's per-emit `uselocale` pins (rule 3) STAY as defense-in-depth — redundant but
harmless under the boot pin. Not a parallel registry; a strict superset (per canonical-sister-extension).

## Anti-patterns this closes

- **Class 38 — phantom invariant** (load-bearing invariant asserted in a comment, established by neither
  code nor guard): the locale boot-pin comment was the canonical instance. Closed by rules 1 + the guard.
- **Class 39 — global process-state mutation where a scoped/thread-local discipline is the norm**: closed
  by rule 2 (forbid global `setlocale`) + rule 3 (`uselocale` is the sanctioned scoped form).
- **AR-3 — documentation-accepted-as-verification** (meta): the audit-reasoning error that let the
  phantom persist. The lesson: *a load-bearing invariant gets a guard, never a comment.*
