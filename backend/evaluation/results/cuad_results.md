# LexFlow clause extraction on CUAD

Model `openai/gpt-oss-20b` (Groq), the same prompt in both modes, run 2026-09-30.
15 contracts from CUAD's test split, in a fixed random order (seed 2027), excluding contracts over 100,000 characters.

A labelled clause counts as found when LexFlow reports that clause type with a quote that is in the
document and overlaps a passage the lawyers labelled with that type.

| Input given to the model | Labelled clauses found | Findings that match a label | Quotes not in the document | Unreadable replies |
|---|---|---|---|---|
| First and last 3,500 characters (earlier LexFlow) | 19 of 81 (23%) | 66% of 29 | 0 of 29 (0%) | 0 of 15 |
| Whole contract, in sections (LexFlow now) | 56 of 81 (69%) | 64% of 105 | 6 of 105 (6%) | 1 of 44 |

Difference in labelled clauses found (whole minus start and end): +46 percentage points (95% bootstrap interval over contracts: +27 to +60).

Only 26 of the 81 labelled clauses (32%) lie mostly inside the first and last 3,500 characters, so that is the most the earlier input could find.

## By clause type

| Clause type | Contracts with a label | Found (whole) | Found (start and end) | Visible in start and end |
|---|---|---|---|---|
| Effective Date | 11 | 73% | 45% | 64% |
| Expiration Date | 10 | 70% | 20% | 30% |
| Renewal Term | 2 | 100% | 50% | 50% |
| Governing Law | 12 | 92% | 50% | 50% |
| Termination For Convenience | 4 | 75% | 25% | 25% |
| Anti-Assignment | 10 | 80% | 10% | 10% |
| Exclusivity | 2 | 50% | 0% | 0% |
| Non-Compete | 1 | 0% | 0% | 0% |
| Cap On Liability | 5 | 40% | 0% | 0% |
| Insurance | 4 | 100% | 25% | 25% |
| Audit Rights | 5 | 80% | 0% | 0% |
| License Grant | 7 | 57% | 14% | 43% |
| Change Of Control | 3 | 33% | 33% | 33% |
| Minimum Commitment | 5 | 20% | 0% | 40% |

Notes: "Findings that match a label" is a lower bound on precision, because CUAD's lawyers did not
label every passage that could fit a category. Risk scores are not evaluated here: there are no expert
labels for them.
