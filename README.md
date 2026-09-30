# LexFlow

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

## When the AI is unavailable

If a call still fails, LexFlow **says so** instead of inventing a result:

- a risk analysis that could not run is shown as **"Not available"**, never as low risk;
- classification and clause extraction fall back to simple text rules (keywords, dates, "between X and Y", "governed by the laws of…"), clearly labelled as rule-based and without a confidence score;
- summaries fall back to the document's own opening lines, labelled as such;
- document comparison still lists the exact changes, without the AI summary.

The confidence shown for AI classifications, and the risk score, are the model's own judgement,
and the app labels them that way; they have not been measured.

## Access control

- Accounts use JWT authentication with bcrypt-hashed passwords.
- Each user can only see and search their own cases and documents; every case and document lookup checks the owner.
- Listing users requires an admin account.

## Tech stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Pydantic
- **AI and text extraction:** Groq API (gpt-oss-20b by default), RapidFuzz for quote checking, PyMuPDF, Tesseract OCR
- **Frontend:** React, TypeScript, Vite
- **Tooling:** pytest, Ruff, mypy, Docker Compose, Nginx

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
results, the fallbacks (a failed analysis must never look like a real result), document comparison
and keyword search. The frontend is type-checked with `npx tsc --noEmit -p tsconfig.app.json`.

## Repository structure

```
backend/app/api/        API endpoints
backend/app/services/   business logic; services/ai/ holds the LLM calls, prompts, quote checking and search
backend/app/models/     database models (SQLAlchemy); migrations in backend/alembic/
backend/app/tests/      tests
frontend/src/           React app (pages/, components/, api/)
```

## Disclaimer

LexFlow's AI output is an aid for reading documents, not legal advice.
