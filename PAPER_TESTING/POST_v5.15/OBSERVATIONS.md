# POST_v5.15 — OBSERVATIONS

**Status:** Empty (ready for paper-test cycle starting 2026-05-12+)
**Mode:** Scratchpad — findings, anomalies, weird logs, questions to
bring back to Claude. Free-form; no template required.

---

## Date-stamped log entries

(scribble below — date + observation + (optional) link to log file
line or screenshot. Sort newest-first or oldest-first as you prefer.)

---

### YYYY-MM-DD — (placeholder; replace when first observation lands)

> Example entry template — delete this section when adding real entries:
>
> **Setup:** what cfg / model / data you were running
> **Observation:** what you saw
> **Expected:** what you expected (per WATCH_LIST / TRY_LIST)
> **Severity:** noise / curiosity / minor / regression / blocker
> **Next step:** investigate / ask Claude / file as bug / ignore

---

## Open questions for Claude

(if anything in the watch list isn't behaving as documented, capture
here so we can revisit together)

---

## Findings to consider for v5.16 scope

(anything that's not a regression but is worth a future ship — feature
gap, ergonomics improvement, missing observability, etc.)

---

## Sprint-ready checklist (graduation criteria)

When ALL of these are true, v5.15 is ready to graduate from paper-test:

- [ ] WATCH_LIST.md "What you should NEVER see" — all 5 items confirmed NOT seen
- [ ] TRY_LIST.md — all 10 scenarios exercised + GREEN
- [ ] ≥1 week continuous paper-test with no regressions
- [ ] (optional) ≥1 week trading_mode=shadow with no regressions
- [ ] OBSERVATIONS.md has 0 unresolved blockers / regressions
- [ ] Anything in "Findings to consider for v5.16" queued (no in-flight bugs)

Once checklist complete: ready to flip `trading_mode=live` per umbrella
postmortem deploy checklist.
