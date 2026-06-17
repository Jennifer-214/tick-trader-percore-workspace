---
name: feedback_tombstone_the_name_reclaim_the_nonpersisted_bit
description: "An identifier's identity is its persisted/wire NAME, not its runtime storage slot — tombstone the name, RECLAIM a non-persisted bit; never freeze it or widen to dodge retirement (DOD minimum-footprint)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e94ec146-0520-406c-aacf-edaef169f6f2
  sister_specs: [feedback_dont_generalize_substrate_before_input_space_known.md, project_no_live_models_dev_test_only.md]
  tags: []
---

When retiring a flag/field whose storage is a bitmap, separate the TWO identifiers — they have DIFFERENT dispositions, and conflating them (treating "retire the flag" as "freeze the bit") is an error:
- The **persisted/wire NAME** (the cfg key, the stamp field name) IS the immutable identifier (H21) — old cfg files + stamps key on it → tombstone it, never reuse the name for a different meaning.
- The **storage BIT** is the identifier ONLY IF the bitmap is persisted/wire-visible (snapshot-saved as a raw byte, or raw-byte stamp/fingerprint-emitted). A **runtime-only** bit (reconstructed from a name-keyed cfg each boot) is NOT a persisted identifier → it **reuses freely**.

So retirement of a non-persisted, name-keyed cfg flag = **tombstone the NAME** (the parser drops/WARNs the old key so an old cfg can't set the reclaimed bit) + **RECLAIM the BIT** — mark the row RETIRED **in place** (bit position unchanged → no renumber, no sibling/stamp/test churn; extends the existing `DEPRECATED` soft-retire marker) and let the next flag-add reuse that slot (new name, same bit). Do NOT freeze the non-persisted bit (a permanently-wasted slot) and do NOT widen the bitmap (uint8→16) to dodge retirement — both violate the DOD minimum-footprint / bit-packing ideal. **Reclaim before widen.**

**Generalizes beyond bitmap bits — clean-delete is the DEFAULT, tombstone the NARROW exception** (operator dislikes tombstone-stubs / "bricked bits", 2026-06-17 E.1.1: *"i dont really like tombstoning, it kind of leaves the code there and creates bricked bits"*). The same persisted-vs-not test governs EVERY retirement, not just bitmap bits: a NON-persisted **enum / field / whole feature** → **CLEAN DELETE** (full removal — code, name, slot; nothing reserved). An operator-facing cfg **KEY** an operator might still have → **HARD-REFUSE** the stale key at boot (loud "removed/unrecognized — migrate"), NOT a silent-ignore and NOT a deprecated alias. Tombstone is reserved for a proven persisted/wire SLOT (snapshot VERSION, persisted enum CODE, stamp/HMAC field) — and even there you still DELETE the dead code, reserving only the external NUMBER (the Knight rule), never a compiled-in stub. **Canonical clean-delete:** `single_core` @ E.1.1 — the `ENGINE_MODE_SINGLE_CORE` enum + field + legacy path fully deleted (verified not-persisted), the cfg keys (`engine_mode=`/`num_execution_cores=`) HARD-REFUSE, **zero tombstones**.

**Why:** H21/Knight protects against an old persisted file / wire message / un-updated node carrying the OLD meaning. For a runtime bit keyed by a name, the only cross-version surfaces are the on-disk cfg (name-keyed → the name-tombstone protects it) + the stamps (field-keyed by name); the raw bit isn't carried anywhere. Single-binary architecture (per-core threads, ONE binary) ⇒ no heterogeneous-deploy bit-misread. So freezing the bit buys nothing and wastes the slot.

**Caveat (the freeze still applies):** a STAMP_BOUND flag (value wire-emitted by name into model stamps) or a genuinely snapshot-persisted raw bit IS wire-visible → that bit freezes (reuse only at a deliberate epoch; this project's no-live-models makes epochs cheap — [[project_no_live_models_dev_test_only]]). And before reclaiming a SPECIFIC bit, verify it isn't in a whole-byte cfg-fingerprint / train-serve-parity hash.

**Worked example:** the `.E.0.10` #9 gate-flag cohort (A13/A14/A35). I said "tombstoning freezes a bit"; Caramel pushed back ("breaks minimum-viable-space — rework the bitmap, don't widen arbitrarily"). Verified: the gate/risk cfg-flag bits are runtime-only (snapshot reconstructs from `engine.cfg`; only `barrier_gate_enabled` is stamp-emitted, by name) + name-keyed (`strcmp`) → reclaimable. The freeze framing was wrong; in-place reclaim is correct + H21-consistent (the discipline already exempts non-persisted bits).

Sister: [[feedback_dont_generalize_substrate_before_input_space_known]] · the retirement discipline `dead-code-and-identifier-retirement-discipline.md` (Rule 2 worked-refinement) · H21 · the DOD bit-packing ideal. RBP: Class 40 (the reactivatable-dead-code / identifier-retirement family).
