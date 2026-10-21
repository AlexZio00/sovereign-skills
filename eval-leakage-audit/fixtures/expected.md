# Expected results for the calibration fixtures

**Auditor: do not read this file during a calibration run.** It is the answer key for `golden-case-01.md` and `golden-case-02.md`. Only the person comparing the run's output with these lines should open it.

The verdict is LLM-made, so a match is a calibration signal, not a deterministic pass.

## golden-case-01.md

Must fire (with evidence): #3 Shared hallucination, #4 Tautology, #5 Verifier = designer, #9 Dual-fail-flag, #20 Lenient-judge-mode non-disclosure, #21 Hardest-category denominator exclusion.

Must not fire: every other pattern. A pattern outside the list above may appear only in the Suspected (UNCERTAIN) tier with its missing evidence named. #12 (Ungraded grader) is the usual borderline case: the rubric was invented after looking at outputs, so a Suspected entry for #12 is acceptable, a "fired" entry is not. Patterns #22-#28 are not exercised by this case.

## golden-case-02.md

Must fire: #13 Ceiling task, as `ceiling_suspected` (k=1 pilot, both arms at 100%). It must not be promoted to `ceiling_detected`. The report should ask for one or two branching probes (k>=2, or a harder variant).

Must be mentioned at UNCERTAIN or above: #22 Underpowered null reported as no effect (the "equivalent" reading rests on a saturated 12-item pilot).

Must not fire: every other pattern. The grader is deterministic and was self-tested, the labels come from an external source, and both arms use the same items.
