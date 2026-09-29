# LexFlow

LexFlow is a web application for managing legal cases and analysing their documents with a large language model. You create a case, upload contracts or other documents (PDF, Word, text or images), and LexFlow extracts their text and can summarise them, classify them, pull out key clauses, flag risks, and compare two versions of a document.

I built it as an independent project after friends doing law internships kept sending me documents to analyse with separate AI tools for each task.

## What it does

| Feature | How it works |
|---|---|
| **Cases and documents** | Create cases, upload documents (up to 20 MB), and keep them organised per case |
| **Text extraction** | PyMuPDF reads digital PDFs; Tesseract OCR reads scanned pages and images |
| **Summary, classification, clause extraction, risk analysis** | Llama 3.1 8B through the Groq API, with a separate prompt for each task (and for NDAs, leases and employment contracts) |
| **Document comparison** | The model lists what was added, removed or changed between two versions |
| **Case synthesis** | The model summarises issues across all documents in a case |
| **Search** | Keyword search across a case's documents (TF-IDF ranking of overlapping passages) |
| **Activity log** | Every upload and AI analysis is recorded for the user who ran it |

## When the AI is unavailable

The Groq API has rate limits, so calls can fail. LexFlow retries, and if the call still fails it **says so** instead of inventing a result:

- a risk analysis that could not run is shown as **"Not available"**, never as low risk;
- classification and clause extraction fall back to simple text rules (keywords, dates, "between X and Y", "governed by the laws of…"), clearly labelled as rule-based and without a confidence score;
- summaries fall back to the document's own opening lines, labelled as such.

The confidence shown for AI classifications is the model's own estimate, and the app labels it that way; it has not been measured.

## Known limitation

To stay within the API's limits, LexFlow currently sends the model **only the first and last 3,500 characters** of a document. For long contracts, clauses in the middle are never analysed. Fixing this, and checking the model's answers against the document, is the next piece of work.

## Access control

- Accounts use JWT authentication with bcrypt-hashed passwords.
- Each user can only see and search their own cases and documents; every case and document lookup checks the owner.
- Listing users requires an admin account.

## Tech stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Pydantic
- **AI and text extraction:** Groq API (Llama 3.1 8B), PyMuPDF, Tesseract OCR
- **Frontend:** React, TypeScript, Vite
- **Tooling:** pytest, Ruff, mypy, Docker Compose, Nginx

## Running locally

You need Python 3.11+, Node.js 18+, PostgreSQL (or Docker) and Tesseract.

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then set SECRET_KEY, DATABASE_URL and GROQ_API_KEY
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

The tests cover the fallbacks (a failed analysis must never look like a real result), keyword search, document comparison and summarisation. The frontend is type-checked with `npx tsc --noEmit -p tsconfig.app.json`.

## Repository structure

```
backend/app/api/        API endpoints
backend/app/services/   business logic; services/ai/ holds the LLM calls, prompts and search
backend/app/models/     database models (SQLAlchemy); migrations in backend/alembic/
backend/app/tests/      tests
frontend/src/           React app (pages/, components/, api/)
```

## Disclaimer

LexFlow's AI output is an aid for reading documents, not legal advice.
