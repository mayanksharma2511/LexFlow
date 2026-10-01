# LexFlow

[![CI](https://github.com/mayanksharma2511/LexFlow/actions/workflows/ci.yml/badge.svg)](https://github.com/mayanksharma2511/LexFlow/actions/workflows/ci.yml)

LexFlow is a web application for managing legal cases and analysing their documents with a large language model. You create a case, upload contracts or other documents (PDF, Word, text or images), and LexFlow extracts their text and can summarise them, classify them, pull out key clauses, flag risks, and compare two versions of a document.

I built it as an independent project after friends doing law internships kept sending me documents to analyse with separate AI tools for each task.

## What it does

| Feature | How it works |
|---|---|
| **Cases and documents** | Create cases, upload documents (up to 20 MB), and keep them organised per case |
| **Text extraction** | PyMuPDF reads digital PDFs; Tesseract OCR reads scanned pages and images |
| **Summary, classification, clause extraction, risk analysis** | A language model through the Groq API (by default `openai/gpt-oss-20b`), reading the **whole** document section by section |
| **Document comparison** | A text comparison finds exactly which sentences were added, removed or changed; the model only writes a short summary of them |
| **Case synthesis** | The model combines the summaries of every document in a case |
| **Search** | Keyword search across a case's documents (TF-IDF ranking of overlapping passages) |
| **Activity log** | Every upload and AI analysis is recorded for the user who ran it |

## Checking the AI's answers

A language model can write a fluent answer that the document does not support. So every clause
LexFlow extracts and every risk it flags must come with a **word-for-word quote** from the
document, and LexFlow checks each quote against the text before showing it:

- **Quote found in document**: the quote appears as written (ignoring case, spacing and curly quotes);
- **Quote found (minor differences)**: a passage matches at least 90/100 (for example one word differs);
- **Quote NOT found in document**: nothing matches, so the AI may have paraphrased or invented it.
  These findings are shown in red, with a warning to check them.

When a quote is found, the app shows the passage in the document's own wording rather than the AI's copy of it.

Clause types follow the categories of CUAD, a public dataset of contracts labelled by lawyers,
so the extractor can be evaluated against expert labels.

## Reading whole documents on a free API tier

Earlier versions sent the model only the first and last 3,500 characters of a document, so
clauses in the middle of long contracts were never analysed. LexFlow now splits documents into
overlapping sections of about 16,000 characters and analyses every section (up to about 190,000
characters in the app; longer documents are read in part, and the result says so).

On Groq's free tier (8,000 tokens per minute), LexFlow paces its calls to stay under the limit
and waits when it is rate-limited, so a long contract can take a few minutes. Each result states
how much of the document was read.

## Evaluation on lawyer-labelled contracts

`backend/evaluation/cuad_eval.py` measures clause extraction on CUAD's test contracts, comparing
the earlier input (the first and last 3,500 characters) with reading the whole contract, using the
same model and prompt. A labelled clause counts as found when LexFlow reports that clause type with
a quote that is in the document and overlaps a passage the lawyers labelled.

Across all 102 test contracts, only 169 of the 636 labelled clauses of these 14 types (27%) lie
inside the first and last 3,500 characters, so the earlier version could not have found the rest.

```bash
cd backend
python -m evaluation.cuad_eval visibility        # the figure above; no API calls
python -m evaluation.cuad_eval run --contracts 40 # resumable; fits the free tier over a few days
python -m evaluation.cuad_eval report             # writes evaluation/results/cuad_results.md
```

Every model reply is saved in `evaluation/results/responses.jsonl`, so the report can be
reproduced without calling the API.

### A trained baseline

`backend/evaluation/clause_classifier.py` trains a classifier for the same 14 clause types on
CUAD's 408 training contracts (TF-IDF features and one logistic regression per type, with each
type's threshold tuned on a validation split of the training contracts). The test contracts are
never used for training or tuning, and the classifier's findings are scored with exactly the same
rule as the LLM's.

On all 102 test contracts it finds 538 of the 636 labelled clauses (85%), in about 0.01 seconds per
contract and with no API calls. The results file also checks for near-duplicate contracts between
the training and test sets (1 found; without it the classifier finds 84%) and repeats the scoring
with a stricter matching rule (78%). Results: `evaluation/results/classifier_results.md`.
Retraining on a different machine can move these figures by about a percentage point, because
library builds differ slightly in their floating-point arithmetic.

CUAD's contracts are American commercial agreements filed with the SEC, so the classifier may do
worse on other kinds of documents (leases, court orders or contracts from other countries), which it
has never seen; the language model does not depend on these training examples.

```bash
python -m evaluation.clause_classifier   # a few minutes on a laptop; saves backend/ml/clause_classifier.joblib
```

## When the AI is unavailable

If a call still fails, LexFlow **says so** instead of inventing a result:

- a risk analysis that could not run is shown as **"Not available"**, never as low risk;
- clause extraction falls back to the trained classifier above (when it has been trained), whose findings are quote-checked like the AI's; without it, and for classification, LexFlow uses simple text rules (keywords, dates, "between X and Y", "governed by the laws of…"). Both are labelled as such and carry no confidence score;
- summaries fall back to the document's own opening lines, labelled as such;
- document comparison still lists the exact changes, without the AI summary.

The confidence shown for AI classifications, and the risk score, are the model's own judgement,
and the app labels them that way; they have not been measured.

## Access control

- Accounts use JWT authentication with bcrypt-hashed passwords.
- Each user can only see and search their own cases and documents; every case and document lookup checks the owner.
- Listing users requires an admin account.

## Tech stack

- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL, Pydantic
- **AI and text extraction:** Groq API (gpt-oss-20b by default), scikit-learn (trained clause classifier), RapidFuzz for quote checking, PyMuPDF, Tesseract OCR
- **Frontend:** React, TypeScript, Vite
- **Tooling:** pytest, Ruff, mypy, GitHub Actions, Docker Compose, Nginx

## Running locally

You need Python 3.11+, Node.js 18+, PostgreSQL (or Docker) and Tesseract.

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then set SECRET_KEY, DATABASE_URL, GROQ_API_KEY and LLM_MODEL
uvicorn app.main:app --reload # http://127.0.0.1:8000/docs

# Frontend (in another terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

With Docker, create a `.env` file next to `docker-compose.yml` containing `SECRET_KEY` and `GROQ_API_KEY`, then run `docker compose up --build`.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
SECRET_KEY=test DATABASE_URL=sqlite:///./test.db pytest
```

The tests never call the real AI service (they switch it off, so they cost no API quota). They cover
access control between users, quote checking, reading every section of a long document, merging
results, the fallbacks (a failed analysis must never look like a real result), the trained classifier,
the evaluation's scoring, document comparison and keyword search. GitHub Actions runs the tests, Ruff
and mypy for the backend, and ESLint, the TypeScript check and the build for the frontend, on every push.

## Repository structure

```
backend/app/api/        API endpoints
backend/app/services/   business logic; services/ai/ holds the LLM calls, prompts, quote checking and search
backend/app/models/     database models (SQLAlchemy; tables are created when the app starts)
backend/app/tests/      tests
backend/evaluation/     CUAD evaluation of the LLM and the trained classifier, with saved results
frontend/src/           React app (pages/, components/, api/)
```

## Disclaimer

LexFlow's AI output is an aid for reading documents, not legal advice.
