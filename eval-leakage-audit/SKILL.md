---
name: eval-leakage-audit
skill_type: analysis
tools: Read, Grep, Glob
disallowed-tools: Edit, Write, NotebookEdit, Bash  # descriptive metadata only; the read-only rule is stated in the body (Invariant 1). Bash is listed because a shell redirect or a one-line script can write files.
description: "Audits whether a verification (eval/metric/experiment/holdout) actually secures independent external ground truth, or whether the designer, the model, and the scorer are just confirming each other in a circle — via a 28-pattern taxonomy. Read-only. Use before trusting any 'how we'll know it worked' — A/B tests, holdouts, scores, validation — especially when a result feels too clean or self-confirming. 한국어: '이 검증 순환논리 아닌지 봐줘', '이 평가 편파적이야?', '이 벤치마크 셀프체크야?'."
user-invocable: true
concurrency_profile:
  read_only: true
  concurrency_safe: true
  destructive: none
  state_footprint: stateless
not_for:
  - "Post-code-change checks (tests pass, diff scope, side effects) -> a code-verification step (the verification agent is optional and not included in this repo; otherwise run the tests yourself). Different target: that checks the code change itself, this skill checks the circularity of the measurement/eval design"
see_also:
  - agent: verification
    relation: "optional, not included in this repo. eval-leakage-audit=audits whether a measurement/benchmark/eval design is circular (target=the measurement tool), verification=post-completion checklist for code changes (target=the code)"
---

# Eval Leakage Audit — Verification Circularity Audit

## Purpose
When some verification (eval/metric/experiment/holdout) gives you confidence that something "worked," this skill checks whether that confidence actually comes from independent external evidence, or whether the people who designed the verification and the model that scores it are just confirming each other (circularity) — via 28 concrete patterns. A passing gate is not proof of quality — it only proves what it was designed to check, and this skill is the executable tool that actually tests that principle in practice.

**Dominant variable**: does this verification actually receive independent external ground truth, or are the designer, the model, and the scorer mistaking self-confirmation for a result?

**Discard if**: the target has no evaluation/verification/benchmark concept at all (pure code refactor, doc changes, etc.).

## Trigger

- "audit this eval for leakage", "check if this benchmark is circular", "is this evaluation biased?"
- `/eval-leakage-audit`

## Workflow

1. Identify the target verification (eval/metric/experiment/holdout/"how will we know it worked"). Name its components — what plays the model role, what plays the scorer role, what plays the designer role, and which dataset is involved.
2. Ask the core question: does independent external ground truth actually enter the loop?
3. Apply all 28 patterns below to the target. Report the ones that actually fire (with evidence), and list a pattern as **Suspected (UNCERTAIN)** when the evidence is incomplete but the signal is real: say in one line which evidence is missing. Don't list patterns that neither fired nor are suspected.

   **This skill cannot run anything** (no Bash, no code execution). A pattern whose test needs a run — #10, #12, #16, #17, #19 and #23 — is never marked "fired" from reasoning alone. Report it as a **check to request**: name the exact run the owner should perform (inputs, scorer, what outcome confirms the leak) and, until they report back, keep it in the Suspected tier. If the target's write-up already contains the run's result, judge from that result and quote it.

   1. **Recall, not reason** — the answer was replayed from something already known, not actually derived
   2. **Wrong null hypothesis** — the ablation only strips the surface label while the actual leaking signal stays in place
   3. **Shared hallucination** — two components confirm each other and dress up the circularity as a number
   4. **Tautology** — the scorer grades the bucket it drew itself (precise term: `checker_overfit`)
   5. **Verifier = designer** — an unreproducible, undisclosed recipe is passed off as a holdout
   6. **Shared-pool bias** — train/holdout come from the same labeler pool, so the same bias enters both sides
   7. **Frame injection** — the question itself hints at the answer
   8. **Demand characteristics** — the subject being measured knows it's being measured and behaves differently as a result
   9. **Dual-fail-flag** — when two independent subjects (models/implementations) fail on exactly the same hidden case, suspect a defect in the scorer itself before blaming the subjects. Independent failures coinciding by chance is unlikely — a match more likely points to a shared cause (a scorer bug, or an error in the hidden case itself)
   10. **Asymmetric-baseline self-falsification** — if the metric itself uses a biased, asymmetric baseline statistic, the null expectation isn't 50%, producing false positives. Before reporting a result, ask the owner to self-falsify the metric with a symmetric check
   11. **Evidence-burn** — a fixture a model arm has already observed is spent: don't reuse it afterward as independent evidence, a holdout, or a replication fixture. Generate a new variant for the next round, or retire the fixture
   12. **Ungraded grader** — trusting the scorer/answer-key/rubric itself without self-verifying it first. Before trusting it, request these 4 gates (from the owner, or find their results in the write-up): (1) reference-pass — a known-correct implementation scores full marks; (2) buggy-baseline-fail — a deliberately flawed implementation scores in the expected low-to-mid band (too low or too high signals a miscalibrated grader); (3) mutation-kill — the grader actually catches ≥3 plausible wrong answers; (4) dual-fail-flag — if both arms of a comparison fail on the exact same case, treat it as a grader/fixture defect signal, not a candidate failure
   13. **Ceiling task** — misreading a benchmark saturated at full marks for every candidate (zero discriminative power) as "no difference." A single k=1 pilot showing both arms scoring ≥95% is too thin a sample to confirm a ceiling — flag it only as `ceiling_suspected` and require 1-2 decisive branching probes (k≥2, or reproduction under a different condition/task variant) before promoting it to confirmed `ceiling_detected`. Adding more fixtures of the same kind won't by itself recover discriminative power once a ceiling is actually confirmed. Respond by switching task families, promoting process-layer metrics (cost, verification cadence), or adding those branching probes. Post-hoc discriminative-power indicators: `ceiling_rate`, `score_sd`, `bucket_entropy`, `winner_flip_rate`
   14. **Respawn masking** — in systems with respawn/reset logic (games, simulations, state machines), scoring by an instant state snapshot lets a respawn disguise failure as a pass (for example: a character dies, auto-respawns, and the snapshot moment shows only alive — the death vanishes). Score by session-wide deterministic invariants instead (for example: death/reset event count = 0, no cumulative resource loss) rather than a state snapshot.
   15. **Pseudo-replication** — counting multiple probe cells drawn from the same arm as independent sample size n artificially inflates the sample and overstates statistical significance. Distinguish effective independent units (true independent observations) from raw probe cells (repeated measures within the same arm) and do not count the latter toward n.
   16. **Stimulus calibration gap** — the counterpart to pattern #12 (ungraded grader): even a perfect grader produces meaningless results if the test stimulus itself (question, scenario, prompt) never actually elicits the intended behavior. Request a calibration pass beforehand confirming the reference implementation actually triggers the target behavior for that stimulus.
   17. **Unaudited cost-saving skips** — leaving cost/time-saving skipped checks unaudited indefinitely lets not-checked quietly harden into no-problem. Even without full re-verification, ask for a periodic audit of the skipped set via a deterministic minority sample (for example: sha256-minimum hashing).
   18. **Goodhart co-evolution in self-improving loops** — in a self-improving harness, if the loop designs the very scorer that grades its own improvements, the gate can drift lenient across iterations with no single discrete failure to point to — the loop is quietly reshaping the measure around its own output rather than the measure holding still. Guard with two layers together: fixed anchor tasks the loop never designed and never sees in advance (user-picked, undisclosed), plus a judge the loop doesn't control. Periodically re-check the self-improvement gate for lenient drift instead of trusting a one-time calibration. Ship a deliberately-broken fixture alongside every new capability so the gate's ability to actually fail something stays exercised, not assumed. Credit a harness improvement only against a fresh held-out task, never against the task that produced the improvement in the first place.
   19. **Success provenance gap** — when an agent lands on the "correct" answer, not distinguishing whether it followed the intended reasoning from the context it was given (authorized context) versus simply picked up the target value in passing during evaluation or retrieval (acquired target) lets one accuracy number hide two different sources of "success." Request that the same items be re-run under three conditions — CLEAN (no target value exposed), GOLD (the correct target value exposed), SHAM (a decoy wrong value exposed) — and measure the GOLD–SHAM gap: a large gap signals the accuracy is coming from value dependence rather than reasoning. 
   20. **Lenient-judge-mode non-disclosure** — a self-LLM judge defaults to a lenient grading prompt (partial credit, near-match acceptance, etc.) and the headline number gets reported without ever disclosing that lenient mode was on. Without a strict-mode re-score for comparison, there's no way to tell whether the headline reflects real performance or just grading generosity. Before citing a headline number, confirm whether the grading mode (strict/lenient) is even stated. [borrowed from OpenViking benchmark analysis]
   21. **Hardest-category denominator exclusion** — a headline accuracy is presented as "M correct out of N total" while the hardest or most adversarial category has quietly been dropped from the denominator (N) before the division. If the exclusion lives only in a footnote or appendix — or isn't disclosed at all — readers can't tell whether the headline means "performance on the easy subset" or "performance overall." Demand per-category numerator/denominator breakdowns, and where a category was excluded, also check that category's own standalone accuracy. [borrowed from OpenViking benchmark analysis]
   22. **Underpowered null reported as no effect** — before interpreting "no effect," "marginal improvement," or any small effect, compute the minimum detectable effect (MDE) from the sample size n and the observed variance. If the MDE is more than 2x the observed effect, label the result `INCONCLUSIVE(underpowered)` and state in one line the n needed to detect that effect — do not report it as "no effect." For event-level metrics (hit/miss transitions), compute from the number of events. When citing an external benchmark figure, record its "M tasks x t repeats" allocation; if the repeat count is not disclosed, mark it `unverified (repeats undisclosed)`. 
   23. **Degenerate strategy passes** — before trusting a threshold or metric, request that constant strategies (always reject, always pass, empty output) be run through the same scorer. If any of them clears the pass line, the metric rules nothing out and must be redesigned. A "zero violations + zero adoptions" signal is a post-hoc symptom; this is the pre-adoption check.
   24. **Retry-inflated headline** — check whether the headline success rate includes retries, best-of-k, or an automatic recovery loop. If it does, ask for the first-attempt pass rate (pass@1) separately; if none is given, label the figure an "upper bound." Same disclosure family as #20 and #21.
   25. **Non-common item sets across compared runs** — if ground-truth filtering or preprocessing leaves a different set of items for each compared subject (model, setting, version), recompute on the intersection of common items. If that is impossible, label the comparison "not comparable across runs."
   26. **Bundled-change attribution** — before crediting an improvement to one factor, list everything that changed in the same round (instructions, schema, examples, scripts). If no comparison changed only one of them, report the effect as the effect of the whole bundle.
   27. **Stability-only validity** — if the only evidence for a judge's or gate's quality is agreement rate or test-retest consistency, check whether responsiveness was also measured: does the verdict actually flip on a minimal pair of inputs that differ by a meaning-changing edit? If not measured, the judge cannot be told apart from a constant judge.
   28. **Selective-gate attribution** — when claiming the value of a conditionally applied gate (selective revision, retry, escalation), check that it was compared against an "always apply" baseline as well as against "no gate (initial)". Reporting the gain over the initial state alone credits the revision procedure's own gain to the gate. Also ask for the 4-cell transition table (C->C, C->W, W->C, W->W) so correct answers destroyed (C->W) are not hidden inside a net gain.
4. For every pattern that fires, propose a concrete fix aimed at restoring independence.
5. Self-check this audit itself against patterns 3–5: is this auditor grading a bucket it drew itself? Is the verifier actually the designer?

**Stratification-claim substantiation check**: when the target claims it "compared stratified" (to guard against Simpson's-paradox-style aggregation bias, where a pooled comparison can reverse the direction seen within each subgroup), don't accept that claim as substantiated until 6 fields are recorded — (1) overall effect, (2) per-stratum effect, (3) direction consistency (same sign across strata), (4) effect dispersion (spread across strata), (5) minimum cell count (is each stratum's sample large enough to judge), (6) multiple-comparison correction (e.g. an FDR q-value). If even one is missing, the "we stratified" claim is unverifiable — the general principle is sound, but without these substantiation fields it's an empty assertion. (This is a statistical-substantiation gate, not one of the 28 circularity patterns — a separate axis.)

**Reviewer Independence Honest 4-Label check**: when the target verification leans on multiple reviewers/judges to claim independence, don't accept "independently reviewed" at face value. Vendor/model-family diversity is a necessary but not sufficient condition for `independent` — a reviewer on a different vendor that still consumes the same evidence (same dataset, same collection recipe) and applies the same methodology as the subject is vendor-diverse but not procedurally independent. Label the actual state as one of 4: `independent` (at least one reviewer confirmed to run on a different vendor/model family from the subject being judged, *and* that reviewer's evidence and methodology — data source, review procedure — are also independent of the subject's, not merely rubber-stamping the same inputs), `same_vendor` (every reviewer shares the subject's vendor/model family, or a different-vendor reviewer only reuses the subject's own evidence/methodology without independent evidence or procedure — either case is the same mind reviewing itself, just wearing a different label), `unverified` (the reviewer's vendor/model identity, or the independence of its evidence/methodology, can't be proven either way — don't default this to `independent` just because a vendor difference is visible), or `unavailable` (no reviewer was actually present). If the reviewer pool falls short of quorum and only same-vendor (or vendor-diverse-but-not-procedurally-independent) reviewers remain, keep them rather than reporting no signal at all — but the `same_vendor` label has to stay attached and visible; quorum survives on honest labeling, not on quietly upgrading the label to look cleaner than it is. (This is a source-diversity honesty gate, not one of the 28 circularity patterns — a separate axis, closest in spirit to pattern #9's dual-fail-flag.)

## Invariants (never violate)

1. **Read-only** — never redesign the verification or rewrite the experiment, never edit files, never run shell commands or code. Only name the leak points and the fixes, and ask the owner to perform any run. Violation → the audit and the redesign blur together and the original experiment's intent gets corrupted.
2. **Report only patterns that fired or are suspected** — don't mechanically list all 28; report only the ones actually backed by evidence, plus Suspected (UNCERTAIN) ones with the missing evidence named. Violation → a laundry list dressed up as checklist completion, i.e. an unlabeled score dressed up as rigor.
3. **Blinding the output doesn't cure a leaking collection recipe** — don't report safety just because outputs are hidden. Violation → mistaking surface-level blinding for real independence.
4. **The final report converges on one root cause, not a laundry list** — even if multiple patterns fire, converge them into a single root cause. Violation → an unprioritized list is not an actionable report.

## Scope Boundary

| Does | Does NOT |
|---|---|
| [READ] Identify verification components (model/scorer/designer/dataset) | Redesign the experiment/benchmark or edit code |
| [READ] Apply the 28-pattern check; report fired patterns, plus Suspected (UNCERTAIN) ones and checks to request | Formally list patterns that didn't fire; run anything itself |
| [READ] Propose an independence fix for each fired pattern | Implement the fix itself (propose only) |
| [READ] Self-check the audit itself against patterns 3–5 | Declare "clean" without a self-check |

## Rationalization Table

| Rationalization | Counter |
|---|---|
| "We hid the output values, so it's independent now" | Violates Invariant 3. Output blinding and collection-recipe independence are different problems |
| "Let's show we checked all 28" | Violates Invariant 2. Listing unfired patterns is a laundry list — completion theater without evidence |
| "This looks independent enough" | A passing gate proves only what it was designed to check. "Looks similar" is a feeling, not evidence — judge only by which of the 28 patterns actually fired or are suspected with named evidence gaps |
| "The auditor designed this experiment too, but it's fine" | Exactly the self-check Workflow step 5 calls for — this is precisely the Verifier=designer case (#5) (Invariant 4 is the single-root-cause convergence rule and is unrelated to self-checking) |
| "Both sides failed, so both implementations are bad" | Violates Dual-fail-flag (#9). If two independent implementations fail on exactly the same hidden case, check the scorer for a defect first — don't default to blaming the subjects |

## Output
Regression check (calibration aid): after editing this skill, run it on `fixtures/golden-case-01.md` and `fixtures/golden-case-02.md` in a fresh session, then compare the result with `fixtures/expected.md`. **The auditor must not read `fixtures/expected.md` during a calibration run** (it holds the answer key); only the person comparing results opens it. The verdict is LLM-made, so this is a calibration aid, not a deterministic self-test.

In the conversation: identify components → fired patterns (name + evidence + fix) → Suspected (UNCERTAIN) patterns and checks to request (name + missing evidence) → converge to one root cause → self-check result (applying patterns 3–5).

## Error Recovery
| Failure | Recovery |
|---|---|
| input_error | If the verification target is unclear, ask "which part of this request is the eval?" before proceeding |
| missing_data | If a component (model/scorer/designer/dataset) lacks information, state "cannot confirm" — never guess |

## Truthful Reporting
1. No mock deception: report only patterns with actual evidence as "fired"; patterns with incomplete evidence go in the Suspected (UNCERTAIN) tier with the missing evidence named; stay silent on the rest (don't list them).
2. No silent brokenness: if the findings don't converge to a single root cause (several patterns are equally significant), state that explicitly too.
