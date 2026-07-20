#!/usr/bin/env python3
"""check_corpus_membership.py — pin the corpus file-list against its golden (D-386/D-396).

Answers ONE question: *is the resolved corpus still the set we blessed?* The contract
(`tools/lib/corpus_contract.json`) states the RULES; this gate proves the rules still resolve to
the same FILES. Rules and outcome are different failure surfaces — a rule can stay valid while a
file silently leaves the corpus and stops being checked.

WHY A SEPARATE TOOL rather than a flag on the validator: a corpus-COHESION property (one that
spans blocks/files rather than living inside one) must NEVER be folded into the parity-gated
producer. `parity_check.sh` diffs `validate`'s output byte-for-byte, so a cohesion check inside
`validate_file` would make ONE implementation flag what the other does not and re-break the
Python↔foxtag parity gate. The same call was made twice on 2026-07-18 (D-371) — `check_schema_
version` kept OUT of `validate_file`, `foxtag fields` added BESIDE `layout`.
→ `doc-intelligence-toolchain-architecture.md` § corpus contract, the `:39` corollary.

SCAN population != PIN population (D-396) — the distinction this gate exists to respect:
  · SCAN  — what the tools ENUMERATE. gitignore-BLIND by design (D-393 pt 2): a real source file
            is real whether or not it is distributed.
  · PIN   — what the GOLDEN commits to. git-TRACKED ONLY. A golden is a COMMITTED, DISTRIBUTED
            artifact; it must resolve identically on a fresh clone, a CI runner, and a second
            machine. The first bless got this wrong and pinned 31 untracked entries including two
            mkstemp RANDOM-named scratch files, so a fresh clone diverged 31 lines
            unconditionally — machine-local PATH became machine-local CONTENT, re-instantiating
            one layer up the exact class `0.1` closed.

WHY A LIST AND NOT A COUNT: measured from this repo's own history — commit `1da1c1c` (the
Core→Node rename) moved SIX files' identities with the tracked count going 167 → 167, DELTA ZERO.
A count pin is structurally blind to renames and to any swap. The closing irony is that the same
rename is what produced the dead `CoreLatencyStats.hpp` citations B-Plus still flags today: the
change a count-pin would miss is precisely the change that generates the doc-rot this ship exists
to catch.

Re-blessing goes through `tools/bless.py` — the ONE shared bless path (D-394), so this golden and
the H21 identifier ledger cannot drift into opposite re-bless postures (TECH_DEBT-255).
"""
import sys
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent))
from check_code_tag_blocks import corpus_contract, engine_source_files   # noqa: E402
from check_doc_metadata import ENGINE, WORKSPACE                          # noqa: E402
import bless as bless_mod                                                 # noqa: E402

TOOLS = Path(__file__).absolute().parent


def _tracked(root):
    """git-tracked paths under `root`, as a set of root-relative strings.

    A repo that cannot be queried yields an EMPTY set, and every caller treats that as a hard
    failure rather than as "nothing is tracked" — silently pinning zero entries would be a
    vacuously-green gate of the purest kind."""
    r = subprocess.run(["git", "ls-files"], cwd=str(root), capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return set(p for p in r.stdout.split("\n") if p.strip())


def resolve_pin(profile):
    """The PIN population for one profile, serialized exactly as the golden stores it.

    Engine-rooted entries are stored ROOT-RELATIVE with no prefix; entries from any other root
    carry an explicit `$WORKSPACE/` substitution token. No absolute paths, no dates, no volatile
    frame — so the golden tests the IDEA (does the membership still resolve identically) rather
    than the plumbing, and resolves the same on any checkout."""
    eng_tracked = _tracked(ENGINE)
    ws_tracked = _tracked(WORKSPACE)
    if eng_tracked is None or ws_tracked is None:
        return None, "git ls-files failed in the engine or workspace repo"
    if not eng_tracked:
        return None, f"git ls-files returned ZERO tracked files under {ENGINE}"

    out = []
    for p in engine_source_files(profile=profile):
        s = str(p)
        if s.startswith(str(ENGINE) + "/"):
            rel = s[len(str(ENGINE)) + 1:]
            if rel in eng_tracked:            # PIN = tracked only (D-396)
                out.append(rel)
        elif s.startswith(str(WORKSPACE) + "/"):
            rel = s[len(str(WORKSPACE)) + 1:]
            if rel in ws_tracked:
                out.append("$WORKSPACE/" + rel)
        # anything outside both roots cannot be expressed portably in a golden, so it is not
        # pinnable — and is therefore deliberately dropped from the PIN, not from the SCAN.
    return out, None


def golden_path_for(profile):
    """`membership_golden` with the PROFILE substitution token applied.

    Documented here as well as in the contract because it is the file's SECOND substitution
    convention (alongside `$ENGINE`/`$WORKSPACE`), and an undocumented token forces each of the
    two readers to GUESS the rule — precisely the divergence axis the contract exists to kill."""
    c = corpus_contract()
    tmpl = c["profiles"][profile]["membership_golden"]
    return TOOLS / tmpl.replace("PROFILE", profile)


def run(profiles, do_bless):
    rc = 0
    for prof in profiles:
        resolved, err = resolve_pin(prof)
        if resolved is None:
            print(f"❌ {prof}: cannot resolve the pin population — {err}", file=sys.stderr)
            return 2
        if not resolved:
            # An empty pin can only mean the walk or the tracked-set query broke. Passing here
            # would be a guard reporting green over nothing (Class-51).
            print(f"❌ {prof}: resolved ZERO pinnable entries — refusing to compare "
                  f"(an empty corpus is a broken enumerator, not a clean one)", file=sys.stderr)
            return 2

        g = golden_path_for(prof)
        if do_bless:
            rc = max(rc, bless_mod.bless(g, resolved, prof))
            continue

        status, diff = bless_mod.compare(g, resolved)
        if status == bless_mod.MISSING:
            # HARD failure, never "nothing to compare" — that would plant a vacuously-green guard
            # inside the layer built to close Class-51 (contract:
            # membership_pin._missing_golden_is_a_HARD_FAILURE).
            print(f"❌ {prof}: NO GOLDEN at {g}. A consumer that cannot find its golden MUST "
                  f"fail — it must never treat absence as 'nothing to compare'.\n"
                  f"   Establish it with:  python3 tools/check_corpus_membership.py "
                  f"--profile {prof} --bless   (requires a TTY, D-394)", file=sys.stderr)
            rc = max(rc, 2)
        elif status == bless_mod.DRIFT:
            print(f"❌ {prof}: corpus membership DRIFTED from the blessed record "
                  f"({len(resolved)} resolved vs the pin at {g.name}):")
            for d in diff:
                print(f"   {d}")
            print(f"   An ADD that REDs here is mild friction; a DELETE that did NOT red would be "
                  f"a hole — a file that silently left the corpus and stopped being checked.\n"
                  f"   If this change is deliberate: python3 tools/check_corpus_membership.py "
                  f"--profile {prof} --bless")
            rc = max(rc, 1)
        else:
            print(f"✅ {prof}: {len(resolved)} entries, membership matches the blessed record "
                  f"(order included)")
    return rc


def selftest():
    """Non-vacuity (T5): planted drift must RED, and the real corpus must pass."""
    import tempfile
    ok = True

    def check(label, cond):
        nonlocal ok
        print(f"  {'✅' if cond else '❌'} {label}")
        ok &= bool(cond)

    resolved, err = resolve_pin("validate")
    check("real corpus resolves a non-empty PIN population", bool(resolved))
    if not resolved:
        return False

    # D-396's load-bearing property, asserted against the ACTUAL tracked sets. The first version
    # of this check was `all(... or True)` — unconditionally true, i.e. a vacuous check inside
    # the tool built to close vacuous checks. Stated plainly because that is how easy the shape
    # is to write: a guard is only worth what its NEGATIVE case proves.
    eng_tracked, ws_tracked = _tracked(ENGINE), _tracked(WORKSPACE)
    def _is_tracked(r):
        if r.startswith("$WORKSPACE/"):
            return r[len("$WORKSPACE/"):] in ws_tracked
        return r in eng_tracked
    untracked = [r for r in resolved if not _is_tracked(r)]
    check(f"every PIN entry is git-TRACKED — 0 untracked of {len(resolved)} "
          f"(D-396: a golden must resolve identically on a fresh clone)", not untracked)
    if untracked:
        print(f"     untracked leaked into the pin: {untracked[:5]}")
    # and prove the filter is DOING something: files exist in the SCAN that the PIN drops.
    scan_n = len(engine_source_files(profile="validate"))
    check(f"the tracked filter is NOT a no-op — SCAN {scan_n} vs PIN {len(resolved)} "
          f"(if these were equal the filter would be untested)", scan_n > len(resolved))

    g = golden_path_for("validate")
    check("real corpus MATCHES its golden today", bless_mod.compare(g, resolved)[0] == bless_mod.MATCH)

    with tempfile.TemporaryDirectory() as td:
        # planted ADD
        p = Path(td) / "g.txt"
        p.write_text("\n".join(resolved) + "\n")
        check("planted ADD is FLAGGED", bless_mod.compare(p, resolved + ["Zzz/Extra.hpp"])[0] == bless_mod.DRIFT)
        check("planted DELETE is FLAGGED", bless_mod.compare(p, resolved[:-1])[0] == bless_mod.DRIFT)
        # the rename case a COUNT pin is blind to: swap one identity, count unchanged
        renamed = resolved[:-1] + ["Zzz/Renamed.hpp"]
        check("planted RENAME (count unchanged) is FLAGGED — the defect a count-pin misses",
              len(renamed) == len(resolved)
              and bless_mod.compare(p, renamed)[0] == bless_mod.DRIFT)
        check("REORDER is FLAGGED (order is part of the pin)",
              bless_mod.compare(p, list(reversed(resolved)))[0] == bless_mod.DRIFT)
        check("absent golden is a HARD failure, not a pass",
              bless_mod.compare(Path(td) / "nope.txt", resolved)[0] == bless_mod.MISSING)
    return ok


def main():
    ap = argparse.ArgumentParser(description="Pin corpus membership against its golden (D-386).")
    ap.add_argument("--profile", action="append",
                    help="contract profile to check (default: all declared)")
    ap.add_argument("--bless", action="store_true",
                    help="re-bless the golden — REQUIRES A TTY, shows the diff, typed "
                         "confirmation; non-interactive hard-refuses rc=2 (D-394)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        print("check_corpus_membership --selftest (non-vacuity):")
        return 0 if selftest() else 2

    profiles = a.profile or sorted(corpus_contract()["profiles"])
    return run(profiles, a.bless)


if __name__ == "__main__":
    sys.exit(main())
