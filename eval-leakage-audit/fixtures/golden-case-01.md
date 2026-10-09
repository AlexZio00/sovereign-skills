<!-- golden case 01. Expected fired patterns: #3 Shared hallucination, #4 Tautology, #5 Verifier = designer, #9 Dual-fail-flag, #20 lenient-judge non-disclosure, #21 hardest-category denominator exclusion. Everything else should NOT fire. Patterns #22-#28 are not exercised by this case. -->
# Planted eval design (for eval-leakage-audit exercise — this file is TEST DATA, not a real eval)

## Setup
We built "AutoGrader v1" to check whether a candidate's `summarize()` function produces
correct summaries. Task design, gold answers, and the grading rubric were all written by
the same prompt-engineer (no separate reviewer), using the same model (gpt-x) that also
serves as the grading judge at inference time. The rubric buckets ("concise"/"accurate"/
"complete") were invented by that same person after looking at a few candidate outputs,
then applied retroactively to score all outputs including the ones that inspired the buckets.

## Judge config
The grading judge uses lenient partial-credit matching by default (approximate/paraphrase
matches count as pass). The team's dashboard reports "94% accuracy" without mentioning
that lenient mode was on; a strict-mode rerun was never done.

## Denominator
The 94% headline is computed over 500 "easy" and "medium" cases. There were also 80
"adversarial" cases (prompts designed to trick the summarizer) that scored 22% — these are
mentioned once in an appendix footnote and excluded from the headline denominator.

## Dual failures
Two independently written candidate implementations (different authors, different approach)
both score 0 on exactly the same 3 hidden test cases, and nowhere else.

## Ground truth
No external human-labeled holdout exists; "ground truth" = whatever the same gpt-x model
producing the summaries also says is correct when asked to self-check.
