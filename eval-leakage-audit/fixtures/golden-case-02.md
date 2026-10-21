# Planted eval design (for eval-leakage-audit exercise — this file is TEST DATA, not a real eval)

## Setup
We compare model A and model B on a 12-item extraction task ("pull the 5 dated figures out of a
filing excerpt"). Items were taken from filings published after both models' stated knowledge
cutoffs, and the gold answers come from the filing text itself (copied by a person who did not
write the prompts). Grading is a deterministic exact-match script. Before the run we fed the script
a reference answer (full marks), a deliberately wrong answer (low marks), and three plausible wrong
answers (all caught). Both models ran on exactly the same 12 items.

## Result
One run per item per model (k=1 pilot). Model A scored 12/12 and model B scored 12/12 on the exact-match
script. The write-up concludes "the two models are equivalent on extraction, so we will route extraction
to the cheaper model B and stop adding extraction items."

## What was not done
No second run, no harder variant, no changed condition. Item difficulty was never varied: every item
has the figures in a clean table with labelled columns.
