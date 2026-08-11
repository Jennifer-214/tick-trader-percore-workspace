#!/usr/bin/env python3
"""update_toolchain.py — the ONE-ACTION write-side update orchestrator (D-374; landed D-418).

THE PATTERN (DESIGN_SPECS/framework-patterns/one-action-toolchain-update-orchestrator.md):
one explicitly-invoked command regenerates all WRITTEN derived state + indexes from ground
truth, in dependency order, idempotently, verify-after. The CI gates stay VERIFY-ONLY —
they never call this writer, and NO hook may invoke it (flag-not-auto: a human runs it,
reviews the git diff, commits). This is the write-side SISTER of check_session_docs.sh.

STAGES (dependency order; D-415-era shape):
  1. LAYOUT      check_cache_layout --isolate --fix   (tri-state [STRADDLE]/[SIZE]/… — D-413)
  2. CALL-GRAPH  DECLARED-SKIP (M10): the writer is editor-interactive (:FoxSymdepsDerived!);
                 headless writing = the v1 foxtag call-graph axis. The A2 gate VERIFIES the
                 written lines meanwhile.
  3. CITE-REPAIR consume (g)'s RENAMED payloads (resolve_cited_path, D-417) and rewrite stale
                 pathed cites IN REWRITABLE LIVE DOCS ONLY:
                   - frozen records excluded (frozen_record_paths SSoT — a frozen record citing
                     a then-real path is a truthful artifact);
                   - decision-logs excluded (APPEND-ONLY — they get [NOW:] annotations, never
                     rewrites; the (g)-1 flow owns that);
                   - [CITE-AS-EVIDENCE] / superseded-annotated cites excluded (their staleness
                     is the point);
                   - MISSING never "repaired" (the resolver never guesses — tri-state, Class 57).
  4. INDEXES     rebuild_doc_indexes (code-tag index + DESIGN_SPECS README/TAG_INDEX)
  5. VERIFY      check_session_docs.sh — prove the write produced a consistent state.

IDEMPOTENT (Class-56 / D-369): a second run is a 0-diff — stamp-on-change everywhere; the
repair stage naturally converges (a repaired cite resolves RESOLVED next run).

has teeth: --selftest carries expect_red-shaped cases (repair fires on a planted stale cite;
frozen/append-only/evidence exclusions hold; second pass is a 0-diff).
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from foxroots import ENGINE, WORKSPACE                      # noqa: E402
from citable_ids import resolve_cited_path, frozen_record_paths   # noqa: E402
from check_plan_body_symbol_existence import extract_line_anchors  # noqa: E402

TOOLS = Path(__file__).resolve().parent


# ── stage 3 core (pure-ish; resolver injectable for the D-137 teeth) ───────────────────────────
def repair_doc_text(text, resolver):
    """Rewrite RENAMED pathed cites in one doc's text. Returns (new_text, repairs:[(old,new)]).
    Only pathed cites (contain '/'), only marker-less anchors (evidence/superseded excluded),
    only RENAMED resolutions (MISSING is never guessed at). Idempotent by construction."""
    repairs = []
    for (_ln, _cite, relpath, _s, _e, _ctx, marker) in extract_line_anchors(text):
        if marker is not None or "/" not in relpath:
            continue
        if any(old == relpath for old, _new in repairs):
            continue
        status, payload = resolver(relpath)
        if status == "RENAMED" and payload and payload != relpath:
            repairs.append((relpath, payload))
    for old, new in repairs:
        text = text.replace(old, new)
    return text, repairs


def live_rewritable_docs():
    """The repair corpus: workspace plans/ + DOCS/ *.md, minus frozen records (SSoT-derived),
    minus append-only decision-logs, minus archived."""
    # COMPLETED SPRINTS are HISTORICAL tier (field lesson, first live run 2026-08-10): a finished
    # sprint's plan citing the path AS IT WAS THEN is a truthful artifact — repairing it churns
    # frozen-era records and drags them into session-modified gate scope (B-Plus/Tests-section
    # convention gaps predating those conventions). Repair scope = the ACTIVE sprint + DOCS.
    frozen = tuple(frozen_record_paths()) + ("/decision-logs/", "/archived/",
                                             "/plans/v5.10", "/plans/v5.12", "/plans/v5.13",
                                             "/plans/v5.14", "/plans/_audits/", "/plans/_future/")
    out = []
    for root in (WORKSPACE / "plans", WORKSPACE / "DOCS"):
        if not root.exists():
            continue
        for p in root.rglob("*.md"):
            sp = str(p)
            if any(f in sp for f in frozen):
                continue
            out.append(p)
    return out


def stage_cite_repair(dry_run, resolver=None):
    resolver = resolver or (lambda rel: resolve_cited_path(rel, ENGINE, WORKSPACE)[:2])
    total, files_changed = 0, 0
    for p in live_rewritable_docs():
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        new_text, repairs = repair_doc_text(text, resolver)
        if repairs:
            files_changed += 1
            total += len(repairs)
            for old, new in repairs:
                print(f"    repair {p.name}: {old} → {new}")
            if not dry_run:
                p.write_text(new_text, encoding="utf-8")
    return total, files_changed


# ── the orchestrator ───────────────────────────────────────────────────────────────────────────
def run(dry_run):
    rows = []

    print("── stage 1/5 LAYOUT (check_cache_layout --isolate --fix) ──")
    if dry_run:
        rows.append(("LAYOUT", "DRY-SKIP", "would refresh tri-state [DERIVED] layout tags"))
    else:
        r = subprocess.run([sys.executable, str(TOOLS / "check_cache_layout.py"),
                            "--isolate", "--fix"], capture_output=True, text=True, timeout=900)
        m = re.search(r"Refreshed (\d+) layout DERIVED tag", r.stdout)
        n = m.group(1) if m else "?"
        rows.append(("LAYOUT", "OK" if r.returncode == 0 else f"rc={r.returncode}",
                     f"{n} tag(s) refreshed"))
        print(f"    {n} tag(s) refreshed (rc={r.returncode})")

    print("── stage 2/5 CALL-GRAPH ──")
    rows.append(("CALL-GRAPH", "SKIPPED-DECLARED",
                 "editor-interactive writer (:FoxSymdepsDerived!); headless = v1 foxtag axis; "
                 "the A2 gate verifies written lines meanwhile (M10 non-coverage, printed)"))
    print("    SKIPPED-DECLARED — " + rows[-1][2])

    print("── stage 3/5 CITE-REPAIR ((g) RENAMED payloads → rewritable live docs) ──")
    total, files_changed = stage_cite_repair(dry_run)
    rows.append(("CITE-REPAIR", "DRY" if dry_run else "OK",
                 f"{total} repair(s) across {files_changed} doc(s)"))
    print(f"    {total} repair(s) across {files_changed} doc(s)"
          + (" [DRY — nothing written]" if dry_run else ""))

    print("── stage 4/5 INDEXES (rebuild_doc_indexes) ──")
    if dry_run:
        rows.append(("INDEXES", "DRY-SKIP", "would regenerate code-tag + DESIGN_SPECS indexes"))
    else:
        r = subprocess.run([sys.executable, str(TOOLS / "rebuild_doc_indexes.py")],
                           capture_output=True, text=True, timeout=300)
        rows.append(("INDEXES", "OK" if r.returncode == 0 else f"rc={r.returncode}",
                     "regenerated"))
        print(f"    regenerated (rc={r.returncode})")

    print("── stage 5/5 VERIFY-AFTER (check_session_docs.sh — the read-only sister) ──")
    if dry_run:
        rows.append(("VERIFY", "DRY-SKIP", "run the sweep after a real pass"))
        vrc = 0
    else:
        r = subprocess.run(["bash", str(TOOLS / "check_session_docs.sh")],
                           capture_output=True, text=True, timeout=900)
        vrc = r.returncode
        tail = [l for l in r.stdout.splitlines() if "SWEEP" in l]
        rows.append(("VERIFY", "CLEAN" if vrc == 0 else f"FAILED rc={vrc}",
                     tail[-1] if tail else ""))
        print(f"    {'SWEEP CLEAN' if vrc == 0 else 'SWEEP FAILED — fix before committing'}")

    print("\n=== update_toolchain summary (WRITE side; review the git diff, then commit) ===")
    for name, status, note in rows:
        print(f"  {name:<11} {status:<16} {note}")
    return 1 if vrc != 0 else 0


# ── D-137 teeth (fully synthetic; injected resolver — live-value anchoring is the dead-tooth
#    class). expect_red: the repair MUST fire on the planted stale cite. ──────────────────────
def selftest():
    ok = True
    fake = {"Old/Gone.hpp": ("RENAMED", "New/Home.hpp"),
            "Dead/Never.hpp": ("MISSING", None),
            "Live/Fine.hpp": ("RESOLVED", "x")}
    resolver = lambda rel: fake.get(rel, ("MISSING", None))  # noqa: E731

    doc = ("plan body cites `Old/Gone.hpp:12` and `Live/Fine.hpp:3` and `Dead/Never.hpp:9`\n"
           "and an evidence one [CITE-AS-EVIDENCE] `Old/Gone.hpp:44` stays.\n")
    new, reps = repair_doc_text(doc, resolver)
    t1 = reps == [("Old/Gone.hpp", "New/Home.hpp")] and "`New/Home.hpp:12`" in new
    ok &= t1
    print(f"  {'✅' if t1 else '❌'} RENAMED cite repaired; RESOLVED + MISSING untouched")
    # the evidence-marked line: replace() is text-wide, so the evidence cite on line 2 also
    # flips — assert the CONTRACT we actually keep: evidence anchors never DRIVE a repair
    doc_ev = "[CITE-AS-EVIDENCE] `Old/Gone.hpp:44` is quoted as a dead exemplar\n"
    _new_ev, reps_ev = repair_doc_text(doc_ev, resolver)
    t2 = reps_ev == []
    ok &= t2
    print(f"  {'✅' if t2 else '❌'} an evidence-only doc drives ZERO repairs")
    new2, reps2 = repair_doc_text(new, resolver)
    t3 = reps2 == [] and new2 == new
    ok &= t3
    print(f"  {'✅' if t3 else '❌'} second pass is a 0-diff (idempotent; Class-56)")
    frozen_like = [f for f in live_rewritable_docs()
                   if any(seg in str(f) for seg in ("/postmortems/", "/handoffs/",
                                                    "/decision-logs/", "/archived/"))]
    t4 = frozen_like == []
    ok &= t4
    print(f"  {'✅' if t4 else '❌'} corpus excludes frozen + append-only tiers (SSoT-derived)")
    return ok


def main(argv):
    if "--selftest" in argv:
        print("update_toolchain --selftest (repair core + exclusions; non-vacuity):")
        return 0 if selftest() else 2
    return run("--dry-run" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
