---
name: feedback_moot_unreachable_disposition
description: "MOOT-UNREACHABLE — a real-in-code flaw whose trigger is structurally unreachable; pin the guarantee, don't patch"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ce648e23-8658-4181-885c-5400b8e672bb
---

A finding can be technically REAL (the code path does have the flaw) yet **functionally not a concern** because its trigger is **structurally unreachable** — guarded upstream, prevented by construction, or gated behind a misconfiguration — AND if it somehow fired, a LARGER failure is already in play (the code symptom is downstream of that bigger problem: *"if this happens, there are bigger issues than the code breaking"*). Disposition tag: **MOOT-UNREACHABLE**.

**Why:** it names a distinct, honest state. Different from REFUTED (the bug isn't real / the premise was wrong) and from OPEN (real + reachable → fix it). Marking a real-but-unreachable flaw OPEN burns effort patching a phantom; marking it REFUTED is dishonest (the flaw IS in the code). MOOT-UNREACHABLE is the true state: real, unreachable, not worth a fix — and saying so out loud beats a silent "eh, skip it."

**How to apply:**
- **REQUIRES code-demonstrated unreachability** — cite the structural prevention (the same merit bar as [[feedback_deferral_reasons_merit_not_effort_or_context]] + [[feedback_no_defer_for_effort]]). NOT a vibe ("probably won't happen") — that's exactly the effort-avoidance trap this guards against. If you can't cite WHY it's unreachable, it's OPEN.
- **The merit move is to CHARACTERIZE the guarantee** that makes it unreachable — pin it with a test so a future change can't silently make it reachable ([[feedback_golden_master_over_reimplemented_oracle]]). Lock the invariant; skip the patch.
- **Belt-and-suspenders only at the chokepoint:** if you still want defense-in-depth, the guard goes at the system-wide chokepoint (one invariant for all paths), never a per-call-site patch — and only if it clears the structural-fix bar (don't build infra for a class with zero real instances).

**First applied:** A7 (`.E.0.10`, 2026-06-11) — FlattenAll `price≤0` "phantom wipeout." Reachability disproven by code read: backtest gap=0 so the staleness flatten can't fire + the flatten gate is off-by-default (live-only) + pre-warmup guarded + `current_price` is the last-known/tick price (>0). The harmful case needs sim + gate-manually-on + an already-broken price source. ⇒ MOOT-UNREACHABLE; characterize the guarantee, don't patch. Validates the adversarial-verify default ([[feedback_adversarial_framing_default_for_checks]]) — it turned a register-asserted "MED capital bug" into its true state.
