# `tools/goldens/` — blessed OUTPUT goldens

**One question only:** *is the output still what we blessed?*

Established `E.1.2.B` `0.2` (D-386). A golden pins a producer's OUTPUT for a FIXED input. Any
deviation REDs. Re-blessing is an **explicit act that SHOWS the per-file diff** — never a silent
regeneration, never a bare count.

## The three-way distinction — do NOT let these blur

This directory exists as a **separate directory, not a filename suffix**, because `tools/lib/`
already conflates several semantics under similar-looking names, and a golden dropped in beside
them is one `ls` away from being read as "just another baseline" and casually regenerated.

| Artifact | Question it answers | Lifecycle |
|---|---|---|
| **`tools/goldens/*`** (here) | *"Is the output still what we blessed?"* | Changes only by an explicit `--bless` that shows the diff |
| `tools/lib/*_baseline.txt` | *"Which known-bad findings are tolerated?"* | **Shrinks toward zero** as debt is paid |
| `tools/lib/latency_path_budgets.json` | *"Has this metric regressed past its ceiling?"* | **Ratchets** — monotone, re-baselined deliberately |
| `tools/lib/*.json` (schemas, contracts) | *"What are the RULES?"* | Stable; edited when the rule changes |

A golden is **not** an exception list. An exception list grandfathers things that are *wrong*; a
golden pins something that is *right*. Conflating them is how a gate quietly stops meaning anything.

## Why the corpus lists are the FIRST goldens

`corpus--validate.txt` (202) and `corpus--derived_facts.txt` (194) pin the resolved membership of
each profile in `tools/lib/corpus_contract.json`.

They were chosen as the first goldens because they are the cheapest possible proof of D-386's
mechanism: a sorted text list with **no volatile frame, no ABI dependence, no dates, and no absolute
paths** (entries are root-relative; the extra-root entries carry an explicit `$WORKSPACE/` token).
Nothing has to be normalized out, so the golden tests the *idea* rather than the plumbing.

## Why a LIST and not a COUNT

Measured from this repo's own history — commit `1da1c1c`, the Core→Node mechanical rename:

```
tracked .hpp/.cpp   BEFORE: 167   AFTER: 167   DELTA: 0
files renamed: 6    (CoreLatencyStats.hpp -> NodeLatencyStats.hpp, CoreModelZoo.hpp -> NodeModelZoo.hpp, +4)
```

**Six corpus files changed identity with zero count change.** A count pin is structurally blind to
renames, and to any swap (delete one, add one). Demonstrated non-vacuously: replaying that rename
against `corpus--validate.txt` leaves the line count identical — a count pin PASSES — while the list
diff names both moved files exactly.

The closing irony worth remembering: that same rename produced the dead `CoreLatencyStats.hpp`
citations the B-Plus advisory still reports today. **The change a count-pin would miss is precisely
the change that generates the doc-rot `0.2` (g) exists to catch.**

## Cost of the pin

Tracked `.hpp`/`.cpp` held at 166 across the last 80 commits, and was 167 a month (150 commits)
earlier — roughly **one net change per month**. So a bless fires rarely, and each firing is a real
deliberate event that should demand a nod.

The asymmetry that justifies it: **an ADD that REDs is mild friction; a DELETE that does NOT red is a
hole** — a file that silently dropped out of the corpus and stopped being checked.
