---
name: eval-leakage-audit
skill_type: analysis
tools: Read, Grep, Glob
description: "Audits whether a verification (eval/metric/experiment/holdout) actually secures independent external ground truth, or whether the designer, the model, and the scorer are just confirming each other in a circle — via an 8-pattern taxonomy. Read-only. Use before trusting any 'how we'll know it worked' — A/B tests, holdouts, scores, validation — especially when a result feels too clean or self-confirming. 한국어: '이 검증 순환논리 아닌지 봐줘', '이 평가 편파적이야?', '이 벤치마크 셀프체크야?'."
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
When some verification (eval/metric/experiment/holdout) gives you confidence that something "worked," this skill checks whether that confidence actually comes from independent external evidence, or whether the people who designed the verification and the model that scores it are just confirming each other (circularity) — via 8 concrete patterns. The Gate≠Oracle principle establishes that a gate should not be read as a quality oracle, but only as a general guideline; this skill is the executable tool that actually tests that principle in practice.

**Dominant variable**: does this verification actually receive independent external ground truth, or are the designer, the model, and the scorer mistaking self-confirmation for a result?

**Discard if**: the target has no evaluation/verification/benchmark concept at all (pure code refactor, doc changes, etc.).

## Trigger

- "audit this eval for leakage", "check if this benchmark is circular", "is this evaluation biased?"
- "이 검증 순환논리 아닌지 봐줘", "이 평가 편파적이야?", "이 벤치마크 셀프체크야?"
- `/eval-leakage-audit`

## Workflow

1. Identify the target verification (eval/metric/experiment/holdout/"how will we know it worked"). Name its components — what plays the model role, what plays the scorer role, what plays the designer role, and which dataset is involved.
2. Ask the core question: does independent external ground truth actually enter the loop?
3. Apply all 8 patterns below to the target and report only the ones that actually fire (don't list patterns that didn't fire):
   1. **Recall, not reason** — the answer was replayed from something already known, not actually derived
   2. **Wrong null hypothesis** — the ablation only strips the surface label while the actual leaking signal stays in place
   3. **Shared hallucination** — two components confirm each other and dress up the circularity as a number
   4. **Tautology** — the scorer grades the bucket it drew itself (precise term: `checker_overfit`)
   5. **Verifier = designer** — an unreproducible, undisclosed recipe is passed off as a holdout
   6. **Shared-pool bias** — train/holdout come from the same labeler pool, so the same bias enters both sides
   7. **Frame injection** — the question itself hints at the answer
   8. **Demand characteristics** — the subject being measured knows it's being measured and behaves differently as a result
4. For every pattern that fires, propose a concrete fix aimed at restoring independence.
5. Self-check this audit itself against patterns 3–5: is this auditor grading a bucket it drew itself? Is the verifier actually the designer?

## Invariants (never violate)

1. **Read-only** — never redesign the verification or rewrite the experiment. Only name the leak points and the fixes. Violation → the audit and the redesign blur together and the original experiment's intent gets corrupted.
2. **Report only patterns that fired** — don't mechanically list all 8; report only the ones actually backed by evidence. Violation → a laundry list dressed up as checklist completion, i.e. an unlabeled score dressed up as rigor.
3. **Blinding the output doesn't cure a leaking collection recipe** — don't report safety just because outputs are hidden. Violation → mistaking surface-level blinding for real independence.
4. **The final report converges on one root cause, not a laundry list** — even if multiple patterns fire, converge them into a single root cause. Violation → an unprioritized list is not an actionable report.

## Scope Boundary

| Does | Does NOT |
|---|---|
| [READ] Identify verification components (model/scorer/designer/dataset) | Redesign the experiment/benchmark or edit code |
| [READ] Apply the 8-pattern check and report only the ones that fired | Formally list patterns that didn't fire |
| [READ] Propose an independence fix for each fired pattern | Implement the fix itself (propose only) |
| [READ] Self-check the audit itself against patterns 3–5 | Declare "clean" without a self-check |

## Rationalization Table

| Rationalization | Counter |
|---|---|
| "We hid the output values, so it's independent now" | Violates Invariant 3. Output blinding and collection-recipe independence are different problems |
| "Let's show we checked all 8" | Violates Invariant 2. Listing unfired patterns is a laundry list — completion theater without evidence |
| "This looks independent enough" | Violates the Gate≠Oracle principle. "Looks similar" is a feeling, not evidence — judge only by which of the 8 patterns actually fired |
| "The auditor designed this experiment too, but it's fine" | Exactly the self-check Invariant 4 calls for — this is precisely the Verifier=designer case (#5) |

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
