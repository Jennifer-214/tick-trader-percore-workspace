#!/usr/bin/env python3
"""bless.py — the ONE re-bless path for every committed baseline artifact (D-394).

A golden answers exactly one question: *is the output still what we blessed?* It is not an
exception list (those grandfather things that are WRONG and shrink toward zero) and not a ratchet
(that bounds a metric). A golden pins something that is RIGHT. Conflating them is how a gate
quietly stops meaning anything — hence `tools/goldens/` as its own directory, and hence this as
the only way to rewrite one.

**This module is the re-bless CONTROL, not a claim that everything it guards is a golden.** The
taxonomy above stays intact — the corpus lists are goldens, `latency_path_budgets.json` is a
ratchet, `identifier_ledger.txt` is an append-only identity ledger, and they have genuinely
different lifecycles. What they share is that each is a COMMITTED baseline whose rewrite must be
a deliberate human act, because "an agent fixed the red by re-baselining" is the one move that
makes any of them meaningless. Route a new artifact here for the control; keep its lifecycle
distinct in its own docs.

WHY THIS IS SHARED RATHER THAN PER-TOOL (TECH_DEBT-255). Two goldens already live in this tree
and they disagreed on re-bless safety: `check_identifier_retirement.py --update` rewrites the H21
tombstone ledger with NO diff and NO confirmation — so the tool enforcing "never renumber, reuse,
or drop an identifier", the Knight-Capital discipline, can have its own record silently
rubber-stamped by any caller, including a delegated agent that "fixed the red by re-baselining."
D-394 decided the opposite posture for the corpus golden. TECH_DEBT-255's trigger says it
explicitly: *build both against ONE shared bless helper rather than two, or the postures diverge
again.* This is that helper.

MODULE TIER, NOT `tools/lib/`. `tools/` = CODE (guarded); `tools/lib/` = DATA (registries,
baselines, ratchets, input lists). `check_tools_inventory.py:46-47` and
`check_import_from_core.py:74` both glob NON-recursively, so a `.py` under `tools/lib/` is exempt
from inventory enrollment AND the roll-your-own-root lint. Never put a guard where the guards
cannot see it (C-389, following D-384 #4's `toolio.py` precedent).

THE D-394 CONTRACT, in full:
  1. A TTY is REQUIRED. `--bless` shows the per-file diff, states plainly that it is overwriting
     the blessed record AND WHAT THAT RECORD CURRENTLY HOLDS, and demands a typed confirmation.
  2. Non-interactive HARD-REFUSES rc=2. CI, the D-374 update orchestrator, and any delegated
     agent get a REFUSAL — never a silent proceed, and never a block-on-stdin. It fails fast, so
     it cannot wedge a pipeline: the batchability objection is answered by refusing to be
     batched rather than by hanging.
  3. NO `--yes` / `--force` escape hatch. Adding one re-opens the hole immediately; a genuine
     automation need must earn its own decision entry.
  4. A no-op does NOT write (D-369 stamp-on-change). Re-blessing an unchanged golden must leave
     the file byte-identical, or every "run the producer, expect 0-diff" currency check breaks.

THE PROPERTY THIS BUYS: per D-385/M10 a delegated agent becomes structurally INCAPABLE of
blessing a golden. That is what keeps a golden a TOTAL acceptance oracle — the moment an agent
can re-bless on red, the golden matches by construction and proves nothing (Class-51, planted in
the guard layer itself).
"""
import os
import sys
import difflib
from pathlib import Path

MATCH, DRIFT, MISSING = "match", "drift", "missing"


def compare(golden_path, resolved):
    """(status, unified_diff_lines) for a resolved list against its golden.

    `resolved` is a list of already-serialized lines. MISSING is reported, never silently
    treated as "nothing to compare" — a consumer that passes on an absent golden plants a
    vacuously-green guard inside the layer built to close Class-51 (contract:
    `membership_pin._missing_golden_is_a_HARD_FAILURE`)."""
    p = Path(golden_path)
    if not p.is_file():
        return MISSING, []
    want = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    got = [str(x).strip() for x in resolved if str(x).strip()]
    if got == want:
        return MATCH, []
    diff = list(difflib.unified_diff(want, got, fromfile=f"{p.name} (blessed)",
                                     tofile=f"{p.name} (resolved now)", lineterm=""))
    return DRIFT, diff


def _isatty():
    """Both directions must be a terminal: stdin so a typed answer is genuinely from a human,
    stdout so the diff is actually being read rather than piped into a log nobody opens."""
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


def confirm_mutation(label, action, noun="record", out=sys.stdout):
    """The D-394 confirmation contract, as ONE implementation shared by every mutating writer.

    Returns 0 only if a human at a terminal typed the exact phrase; 2 on refusal, abort, or
    any non-interactive context.

    WHY THIS IS A FUNCTION AND NOT A COPIED BLOCK. TECH_DEBT-255 was opened because
    `check_identifier_retirement --update` rewrote the H21 ledger with no diff and no
    confirmation — the OPPOSITE posture to bless() sitting beside it. It was closed by
    migrating that one writer here. `check_tech_debt.py --close` — which MOVES entries
    between the tech-debt ledgers — was never enumerated, so the class was not actually
    closed (found 2026-07-20 by firing it accidentally during a read-only verification; it
    silently moved TECH_DEBT-016). Re-typing this prompt at each writer is what let the two
    postures diverge in the first place, so the contract lives in exactly one place.

    The CALLER must already have printed what is changing. This gates the act; it does not
    describe it — a confirmation whose reader has not been shown the change is theatre.
    """
    # non-TTY = hard refuse. Fail fast; never prompt into a pipe.
    if not _isatty():
        print(f"[bless] REFUSED (rc=2): this mutation requires an interactive terminal.\n"
              f"  D-394: the {noun} may only be rewritten by a human who has SEEN the change above.\n"
              f"  There is deliberately no --yes/--force. If you are an agent or a CI step: this\n"
              f"  is not a permission problem to route around — the refusal IS the control that\n"
              f"  keeps this {noun} a total acceptance oracle rather than something that matches\n"
              f"  by construction.", file=out)
        return 2

    # Typed confirmation — not y/n. Typing the word is the point: it cannot be fat-fingered
    # past, and it makes the act deliberate rather than reflexive.
    print(f"  Type  bless {label}  to {action}, or anything else to abort.", file=out)
    try:
        answer = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n[bless] aborted — {noun} unchanged.", file=out)
        return 2
    if answer != f"bless {label}":
        print(f"[bless] aborted — {noun} unchanged.", file=out)
        return 2
    return 0


def bless(golden_path, resolved, label, out=sys.stdout):
    """Re-bless one golden under the D-394 contract. Returns an rc — 0 wrote or was already
    current, 2 refused."""
    p = Path(golden_path)
    status, diff = compare(p, resolved)

    # (4) no-op => no write. Checked BEFORE the TTY gate on purpose: an unchanged golden needs
    # no human decision, so a CI/orchestrator invocation that changes nothing must not be
    # refused. Refusal is for MUTATION, not for a null act.
    if status == MATCH:
        print(f"[bless] {label}: already current ({len(resolved)} entries) — no write.", file=out)
        return 0

    if status == MISSING:
        print(f"[bless] {label}: NO GOLDEN at {p} — this would CREATE it "
              f"({len(resolved)} entries).", file=out)
    else:
        print(f"[bless] {label}: the blessed record and the resolved output DISAGREE.", file=out)

    # (1) state WHAT THE RECORD CURRENTLY HOLDS, not merely that it differs — a diff alone lets a
    # reader approve without ever learning what they are discarding.
    if status == DRIFT:
        want = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        # Count the SAME way on both sides. Reporting a filtered `want` against a raw `resolved`
        # made a blank-line-bearing golden look like it had gained 8 entries when it had gained
        # one — a comparison that misleads its own reader is the whole failure mode here.
        got_n = sum(1 for x in resolved if str(x).strip())
        adds = sum(1 for d in diff if d.startswith("+") and not d.startswith("+++"))
        dels = sum(1 for d in diff if d.startswith("-") and not d.startswith("---"))
        print(f"\n  currently blessed : {len(want)} entries  ({p})", file=out)
        print(f"  resolved now      : {got_n} entries", file=out)
        print(f"  change            : +{adds} / -{dels}\n", file=out)
        for d in diff:
            print(f"  {d}", file=out)
        print("", file=out)
        # A DELETE that goes unnoticed is the expensive direction: an ADD that REDs is mild
        # friction, but a file silently dropping out of the corpus stops being checked at all.
        if dels:
            print(f"  ⚠️  {dels} entr{'y' if dels == 1 else 'ies'} would be REMOVED from the "
                  f"blessed record. If that was not deliberate, answer no.\n", file=out)

    # (1)+(2) the refusal + typed confirmation, via the ONE shared implementation below.
    rc = confirm_mutation(label, "overwrite the blessed record", noun="golden", out=out)
    if rc != 0:
        return rc

    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(str(x) for x in resolved) + "\n", encoding="utf-8")
    print(f"[bless] wrote {len(resolved)} entries → {p}", file=out)
    return 0


def selftest(out=sys.stdout):
    """Non-vacuity (T5): every branch of the contract proven, including the refusals.

    A bless helper that cannot be shown to REFUSE is the worst possible thing to be wrong about —
    it is the control that makes every golden downstream a total oracle."""
    import tempfile
    ok = True

    def check(label, cond):
        nonlocal ok
        print(f"  {'✅' if cond else '❌'} {label}", file=out)
        ok &= bool(cond)

    with tempfile.TemporaryDirectory() as td:
        g = Path(td) / "g.txt"
        g.write_text("a\nb\nc\n")

        check("identical resolved list => MATCH", compare(g, ["a", "b", "c"])[0] == MATCH)
        check("changed resolved list => DRIFT", compare(g, ["a", "b", "d"])[0] == DRIFT)
        check("REORDERED list => DRIFT (order is part of the pin, not incidental)",
              compare(g, ["c", "b", "a"])[0] == DRIFT)
        check("absent golden => MISSING (never a silent 'nothing to compare')",
              compare(Path(td) / "nope.txt", ["a"])[0] == MISSING)

        # no-op => rc 0 AND byte-identical file (D-369). Both halves matter: returning 0 while
        # rewriting the file would still break every 0-diff currency check.
        before = g.read_bytes()
        rc = bless(g, ["a", "b", "c"], "test", out=open(os.devnull, "w"))
        check("no-op bless => rc=0 and file byte-IDENTICAL (D-369 stamp-on-change)",
              rc == 0 and g.read_bytes() == before)

        # non-TTY mutation => refuse, and leave the file alone.
        rc = bless(g, ["a", "b", "zzz"], "test", out=open(os.devnull, "w"))
        check("non-TTY DRIFT bless => rc=2 REFUSED and golden UNCHANGED",
              rc == 2 and g.read_bytes() == before)

        rc = bless(Path(td) / "new.txt", ["x"], "test", out=open(os.devnull, "w"))
        check("non-TTY CREATE bless => rc=2 REFUSED and no file created",
              rc == 2 and not (Path(td) / "new.txt").exists())

        # No bypass PARAMETER on the interface. Checked by introspecting the signature rather
        # than by grepping this file's own text: a source-text scan would match the docstring
        # that *documents* the absence, and a check that can pass on its own prose is exactly
        # the circular shape this codebase keeps finding (sister: add_vocab.py's post-regen
        # --check, vacuous in its calling context).
        import inspect
        params = set(inspect.signature(bless).parameters)
        check("bless() exposes no confirmation-bypass parameter",
              not (params & {"yes", "force", "assume_yes", "no_confirm", "batch", "interactive"}))

        # The SHARED contract gets its own teeth. bless()'s refusals above exercise it only
        # through one caller; check_tech_debt --close is the second, and a contract proven
        # via a single call site is how the two postures diverged before TECH_DEBT-255.
        check("confirm_mutation() non-TTY => rc=2 (the refusal, tested directly)",
              confirm_mutation("x", "do the thing", out=open(os.devnull, "w")) == 2)
        cm_params = set(inspect.signature(confirm_mutation).parameters)
        check("confirm_mutation() exposes no confirmation-bypass parameter",
              not (cm_params & {"yes", "force", "assume_yes", "no_confirm", "batch", "interactive"}))
        # Non-vacuity of the refusal itself: it must be the TTY check doing the work, not a
        # constant return. With a terminal faked, the same call must reach the PROMPT instead.
        _real_isatty = globals()["_isatty"]
        try:
            globals()["_isatty"] = lambda: True
            reached_prompt = False
            import builtins
            _real_input = builtins.input
            def _spy(*a, **k):
                nonlocal reached_prompt
                reached_prompt = True
                return "wrong answer"
            builtins.input = _spy
            rc_tty = confirm_mutation("x", "do the thing", out=open(os.devnull, "w"))
            builtins.input = _real_input
            check("confirm_mutation() with a TTY reaches the prompt and rejects a wrong phrase",
                  reached_prompt and rc_tty == 2)
        finally:
            globals()["_isatty"] = _real_isatty
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        print("bless --selftest (non-vacuity):")
        sys.exit(0 if selftest() else 2)
    print(__doc__.strip().splitlines()[0])
    print("\nThis is a LIBRARY — import `compare`/`bless`. Run --selftest to prove the contract.")
    sys.exit(0)
