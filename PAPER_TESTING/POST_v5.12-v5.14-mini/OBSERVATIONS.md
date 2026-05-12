# POST_v5.12-v5.14-mini — OBSERVATIONS

**Status:** Empty (paper-test pending; this dir was opened 2026-05-12 when
operator brought up the never-paper-tested v5.12-v5.14 features alongside
v5.15 paper-test prep)
**Mode:** Scratchpad — findings from working through `PUNCH_LIST.md`.
Free-form; no template required.

---

## Date-stamped log entries

(scribble below — date + feature + observation + (optional) link to log
file line or screenshot)

---

### YYYY-MM-DD — (placeholder; replace when first observation lands)

> Example entry template — delete this section when adding real entries:
>
> **Feature exercised:** which item from PUNCH_LIST (e.g. "v5.14.0 Ridge buy-side")
> **Cfg toggles:** what flags were set
> **Setup:** model / data / mode
> **Observation:** what happened
> **Expected (per PUNCH_LIST):** what should have happened
> **Severity:** noise / curiosity / minor / regression / blocker
> **Next step:** investigate / ask Claude / file as bug / ignore

---

## Suggested paper-test sequence

PUNCH_LIST has the canonical 10-step smoke test at the bottom. Recommended
execution order:

1. Baseline run (stock cfg) — establish control
2. Composite confidence + retrain
3. Risk degradation ladder
4. Ridge buy-side
5. Exit-side ML
6. Exit Ridge
7. Thompson bandit
8. WS-staleness flatten (SAFETY)
9. Reconcile STRICT mode
10. Lazy rebuild + online corr (perf)

Once all 10 are GREEN, the v5.12-v5.14 features are validated. THEN
move to `../POST_v5.15/TRY_LIST.md` to exercise v5.15-specific changes.

---

## Open questions for Claude

(anything in PUNCH_LIST that isn't behaving as documented — capture here)

---

## Findings to consider for v5.16 scope

(feature gaps, ergonomics improvements, missing observability discovered
during v5.12-v5.14 paper-test — worth a future ship but not blocking)

---

## Sprint-ready checklist (graduation criteria)

When ALL true, v5.12-v5.14 features are paper-test validated:

- [ ] Baseline stock-cfg run completes cleanly (1-2 hours)
- [ ] 10-step PUNCH_LIST smoke test all GREEN
- [ ] PUNCH_LIST "Regression watch list" — all 7 items confirmed clean
- [ ] PUNCH_LIST "Known landmines" — none stepped on
- [ ] OBSERVATIONS.md has 0 unresolved blockers / regressions
- [ ] Anything in "Findings to consider for v5.16" queued (no in-flight bugs)

Once complete: proceed to `../POST_v5.15/` for v5.15-specific paper-test.
