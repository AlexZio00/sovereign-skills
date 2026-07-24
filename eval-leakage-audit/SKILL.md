---
name: eval-leakage-audit
skill_type: analysis
tools: Read, Grep, Glob
description: "Audits whether a verification (eval/metric/experiment/holdout) actually secures independent external ground truth, or whether the designer, the model, and the scorer are just confirming each other in a circle — via a 17-pattern taxonomy. Read-only. Use before trusting any 'how we'll know it worked' — A/B tests, holdouts, scores, validation — especially when a result feels too clean or self-confirming. 한국어: '이 검증 순환논리 아닌지 봐줘', '이 평가 편파적이야?', '이 벤치마크 셀프체크야?'."
user_invocable: true
concurrency_profile:
  read_only: true
  concurrency_safe: true
  destructive: none
state_footprint: stateless
not_for:
  - "Post-code-change checks (tests pass, diff scope, side effects) -> verification (different target: verification=the code change itself, this skill=the circularity of the measurement/eval design)"
see_also:
  - agent: verification
    relation: "eval-leakage-audit=audits whether a measurement/benchmark/eval design is circular (target=the measurement tool), verification=post-completion checklist for code changes (target=the code)"
---

# Eval Leakage Audit — Verification Circularity Audit

## Purpose
When some verification (eval/metric/experiment/holdout) gives you confidence that something "worked," this skill checks whether that confidence actually comes from independent external evidence, or whether the people who designed the verification and the model that scores it are just confirming each other (circularity) — via 17 concrete patterns. A passing gate is not proof of quality — it only proves what it was designed to check, and this skill is the executable tool that actually tests that principle in practice.

**Dominant variable**: does this verification actually receive independent external ground truth, or are the designer, the model, and the scorer mistaking self-confirmation for a result?

**Discard if**: the target has no evaluation/verification/benchmark concept at all (pure code refactor, doc changes, etc.).

## Trigger

- "audit this eval for leakage", "check if this benchmark is circular", "is this evaluation biased?"
- "이 검증 순환논리 아닌지 봐줘", "이 평가 편파적이야?", "이 벤치마크 셀프체크야?"
- `/eval-leakage-audit`

## Workflow

1. Identify the target verification (eval/metric/experiment/holdout/"how will we know it worked"). Name its components — what plays the model role, what plays the scorer role, what plays the designer role, and which dataset is involved.
2. Ask the core question: does independent external ground truth actually enter the loop?
3. Apply all 17 patterns below to the target and report only the ones that actually fire (don't list patterns that didn't fire):
   1. **Recall, not reason** — the answer was replayed from something already known, not actually derived
   2. **Wrong null hypothesis** — the ablation only strips the surface label while the actual leaking signal stays in place
   3. **Shared hallucination** — two components confirm each other and dress up the circularity as a number
   4. **Tautology** — the scorer grades the bucket it drew itself (precise term: `checker_overfit`)
   5. **Verifier = designer** — an unreproducible, undisclosed recipe is passed off as a holdout
   6. **Shared-pool bias** — train/holdout come from the same labeler pool, so the same bias enters both sides
   7. **Frame injection** — the question itself hints at the answer
   8. **Demand characteristics** — the subject being measured knows it's being measured and behaves differently as a result
   9. **Dual-fail-flag** — when two independent subjects (models/implementations) fail on exactly the same hidden case, suspect a defect in the scorer itself before blaming the subjects. Independent failures coinciding by chance is unlikely — a match more likely points to a shared cause (a scorer bug, or an error in the hidden case itself)
   10. **Asymmetric-baseline self-falsification** — if the metric itself uses a biased, asymmetric baseline statistic, the null expectation isn't 50%, producing false positives. Before reporting a result, self-falsify the metric with a symmetric check
   11. **Evidence-burn** — a fixture a model arm has already observed is spent: don't reuse it afterward as independent evidence, a holdout, or a replication fixture. Generate a new variant for the next round, or retire the fixture
   12. **Ungraded grader** — trusting the scorer/answer-key/rubric itself without self-verifying it first. Before trusting it, run 4 gates: (1) reference-pass — a known-correct implementation scores full marks; (2) buggy-baseline-fail — a deliberately flawed implementation scores in the expected low-to-mid band (too low or too high signals a miscalibrated grader); (3) mutation-kill — the grader actually catches ≥3 plausible wrong answers; (4) dual-fail-flag — if both arms of a comparison fail on the exact same case, treat it as a grader/fixture defect signal, not a candidate failure
   13. **Ceiling task** — misreading a benchmark saturated at full marks for every candidate (zero discriminative power) as "no difference." If a k=1 pilot shows both arms scoring ≥95%, flag `ceiling_detected` — adding more fixtures of the same kind won't recover discriminative power. Respond by switching task families, promoting process-layer metrics (cost, verification cadence), or adding 1-2 decisive branching probes. Post-hoc discriminative-power indicators: `ceiling_rate`, `score_sd`, `bucket_entropy`, `winner_flip_rate`
   14. **Respawn masking** — in systems with respawn/reset logic (games, simulations, state machines), scoring by an instant state snapshot lets a respawn disguise failure as a pass (for example: a character dies, auto-respawns, and the snapshot moment shows only alive — the death vanishes). Score by session-wide deterministic invariants instead (for example: death/reset event count = 0, no cumulative resource loss) rather than a state snapshot. [borrowed from fabulous HC3-13]
   15. **Pseudo-replication** — counting multiple probe cells drawn from the same arm as independent sample size n artificially inflates the sample and overstates statistical significance. Distinguish effective independent units (true independent observations) from raw probe cells (repeated measures within the same arm) and do not count the latter toward n. [borrowed from fabulous HC3-5]
   16. **Stimulus calibration gap** — the counterpart to pattern #12 (ungraded grader): even a perfect grader produces meaningless results if the test stimulus itself (question, scenario, prompt) never actually elicits the intended behavior. Run a calibration pass beforehand confirming the reference implementation actually triggers the target behavior for that stimulus. [borrowed from fabulous HC3-7]
   17. **Unaudited cost-saving skips** — leaving cost/time-saving skipped checks unaudited indefinitely lets not-checked quietly harden into no-problem. Even without full re-verification, periodically audit the skipped set via a deterministic minority sample (for example: sha256-minimum hashing). [borrowed from fabulous HC3-9]
4. For every pattern that fires, propose a concrete fix aimed at restoring independence.
5. Self-check this audit itself against patterns 3–5: is this auditor grading a bucket it drew itself? Is the verifier actually the designer?

**Stratification-claim substantiation check**: when the target claims it "compared stratified" (to guard against Simpson's-paradox-style aggregation bias, where a pooled comparison can reverse the direction seen within each subgroup), don't accept that claim as substantiated until 6 fields are recorded — (1) overall effect, (2) per-stratum effect, (3) direction consistency (same sign across strata), (4) effect dispersion (spread across strata), (5) minimum cell count (is each stratum's sample large enough to judge), (6) multiple-comparison correction (e.g. an FDR q-value). If even one is missing, the "we stratified" claim is unverifiable — the general principle is sound, but without these substantiation fields it's an empty assertion. (This is a statistical-substantiation gate, not one of the 17 circularity patterns — a separate axis.)

## Invariants (never violate)

1. **Read-only** — never redesign the verification or rewrite the experiment. Only name the leak points and the fixes. Violation → the audit and the redesign blur together and the original experiment's intent gets corrupted.
2. **Report only patterns that fired** — don't mechanically list all 17; report only the ones actually backed by evidence. Violation → a laundry list dressed up as checklist completion, i.e. an unlabeled score dressed up as rigor.
3. **Blinding the output doesn't cure a leaking collection recipe** — don't report safety just because outputs are hidden. Violation → mistaking surface-level blinding for real independence.
4. **The final report converges on one root cause, not a laundry list** — even if multiple patterns fire, converge them into a single root cause. Violation → an unprioritized list is not an actionable report.

## Scope Boundary

| Does | Does NOT |
|---|---|
| [READ] Identify verification components (model/scorer/designer/dataset) | Redesign the experiment/benchmark or edit code |
| [READ] Apply the 17-pattern check and report only the ones that fired | Formally list patterns that didn't fire |
| [READ] Propose an independence fix for each fired pattern | Implement the fix itself (propose only) |
| [READ] Self-check the audit itself against patterns 3–5 | Declare "clean" without a self-check |

## Rationalization Table

| Rationalization | Counter |
|---|---|
| "We hid the output values, so it's independent now" | Violates Invariant 3. Output blinding and collection-recipe independence are different problems |
| "Let's show we checked all 17" | Violates Invariant 2. Listing unfired patterns is a laundry list — completion theater without evidence |
| "This looks independent enough" | Violates the Gate≠Oracle principle. "Looks similar" is a feeling, not evidence — judge only by which of the 17 patterns actually fired |
| "The auditor designed this experiment too, but it's fine" | Exactly the self-check Invariant 4 calls for — this is precisely the Verifier=designer case (#5) |
| "Both sides failed, so both implementations are bad" | Violates Dual-fail-flag (#9). If two independent implementations fail on exactly the same hidden case, check the scorer for a defect first — don't default to blaming the subjects |

## Output
In the conversation: identify components → fired patterns (name + evidence + fix) → converge to one root cause → self-check result (applying patterns 3–5).

## Error Recovery
| Failure | Recovery |
|---|---|
| input_error | If the verification target is unclear, ask "which part of this request is the eval?" before proceeding |
| missing_data | If a component (model/scorer/designer/dataset) lacks information, state "cannot confirm" — never guess |

## Truthful Reporting
1. No mock deception: report only patterns with actual evidence as "fired"; stay silent on the rest (don't list them).
2. No silent brokenness: if the findings don't converge to a single root cause (several patterns are equally significant), state that explicitly too.
