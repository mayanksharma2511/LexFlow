# Trained clause classifier on CUAD

TF-IDF and logistic regression, trained on CUAD's 408 training contracts (102,631 passages). Thresholds were tuned on a validation split of the training contracts; the test contracts were not used for training or tuning. Findings are scored with the same rule as the LLM (evaluation/cuad_eval.py). No API calls; about 0.01 seconds per contract.

## All 102 test contracts

| Method | Labelled clauses found | Findings that match a label |
|---|---|---|
| Trained classifier | 538 of 636 (85%) | 69% of 861 |

## Compared with the LLM on the 15 contracts it has finished

| Method | Labelled clauses found | Findings that match a label |
|---|---|---|
| Trained classifier (no API calls) | 64 of 81 (79%) | 70% of 109 |
| LLM, first and last 3,500 characters | 19 of 81 (23%) | 66% of 29 |
| LLM, whole contract in sections | 56 of 81 (69%) | 64% of 105 |

Classifier minus LLM (whole contract), labelled clauses found: 95% bootstrap interval over contracts -5 to +28 percentage points.

## Checks

- **Near-duplicate contracts.** 1 test contract(s) closely match a training contract (cosine similarity of at least 0.9). Without them the classifier finds 84% of labelled clauses.
- **Stricter matching** (at least half of each finding must lie inside the labelled passage): the classifier finds 78% of labelled clauses on all test contracts.
  On the 15 finished contracts: classifier 72%, LLM (whole contract) 63%.
- **Finding length.** Median 235 characters per classifier finding, so it is not matching labels by returning long stretches of text.

## By clause type (all test contracts)

| Clause type | Contracts with a label | Found | Threshold | Passages per contract |
|---|---|---|---|---|
| Effective Date | 70 | 64% | 0.7 | 1 |
| Expiration Date | 78 | 91% | 0.3 | 1 |
| Renewal Term | 26 | 96% | 0.5 | 1 |
| Governing Law | 83 | 96% | 0.5 | 1 |
| Termination For Convenience | 29 | 86% | 0.9 | 2 |
| Anti-Assignment | 72 | 92% | 0.5 | 1 |
| Exclusivity | 33 | 79% | 0.8 | 2 |
| Non-Compete | 23 | 70% | 0.7 | 1 |
| Cap On Liability | 44 | 95% | 0.9 | 2 |
| Insurance | 32 | 81% | 0.9 | 1 |
| Audit Rights | 38 | 87% | 0.8 | 2 |
| License Grant | 50 | 82% | 0.9 | 1 |
| Change Of Control | 26 | 81% | 0.5 | 3 |
| Minimum Commitment | 32 | 66% | 0.9 | 1 |
