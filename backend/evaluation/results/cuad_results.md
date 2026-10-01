# LexFlow clause extraction on CUAD

Model `openai/gpt-oss-20b` (Groq), the same prompt in both modes, run 2026-10-01.
40 contracts from CUAD's test split, in a fixed random order (seed 2027), excluding contracts over 100,000 characters.

A labelled clause counts as found when LexFlow reports that clause type with a quote that is in the
document and overlaps a passage the lawyers labelled with that type.

| Input given to the model | Labelled clauses found | Findings that match a label | Quotes not in the document | Unreadable replies |
|---|---|---|---|---|
| First and last 3,500 characters (earlier LexFlow) | 51 of 218 (23%) | 61% of 84 | 0 of 84 (0%) | 0 of 40 |
| Whole contract, in sections (LexFlow now) | 162 of 218 (74%) | 67% of 270 | 10 of 270 (4%) | 1 of 97 |

Difference in labelled clauses found (whole minus start and end): +51 percentage points (95% bootstrap interval over contracts: +42 to +59).

Only 71 of the 218 labelled clauses (33%) lie mostly inside the first and last 3,500 characters, so that is the most the earlier input could find.

## By clause type

| Clause type | Contracts with a label | Found (whole) | Found (start and end) | Visible in start and end |
|---|---|---|---|---|
| Effective Date | 27 | 78% | 52% | 74% |
| Expiration Date | 29 | 62% | 17% | 31% |
| Renewal Term | 9 | 100% | 33% | 33% |
| Governing Law | 29 | 97% | 41% | 41% |
| Termination For Convenience | 10 | 90% | 20% | 20% |
| Anti-Assignment | 27 | 89% | 26% | 30% |
| Exclusivity | 10 | 60% | 10% | 10% |
| Non-Compete | 5 | 20% | 0% | 20% |
| Cap On Liability | 12 | 58% | 8% | 8% |
| Insurance | 8 | 100% | 12% | 12% |
| Audit Rights | 12 | 75% | 8% | 8% |
| License Grant | 19 | 63% | 16% | 32% |
| Change Of Control | 8 | 62% | 12% | 25% |
| Minimum Commitment | 13 | 38% | 0% | 31% |

Notes: "Findings that match a label" is a lower bound on precision, because CUAD's lawyers did not
label every passage that could fit a category. Risk scores are not evaluated here: there are no expert
labels for them.
