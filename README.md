# ⚖️ LexFlow — AI-Powered Legal Intelligence Platform

**LexFlow** is an enterprise-grade Legal Intelligence and Case Management System built with React, TypeScript, FastAPI, PostgreSQL, and Groq LLM AI Engine (`llama-3.1-8b-instant`). Designed for law firms and legal professionals, LexFlow streamlines matter workflows, document extraction, risk auditing, and multi-document case synthesis.

---

## 🚀 Key Features

- **⚖️ Legal Case Management**: Create, edit, track, and search matters with metadata, parties, priority levels, and chronological audit trails.
- **📁 Document Management & OCR**: PDF, Word (`.docx`/`.doc`), Text (`.txt`), and Image upload (up to 20MB) with PyMuPDF fast text extraction and Tesseract OCR fallback for scanned contracts.
- **🤖 Multimodal AI Intelligence**:
  - **Executive Summarization**: Generate concise matter overviews.
  - **Document Classification**: Categorize legal agreements (Lease, NDA, Employment, Petition, Affidavit) with confidence scoring.
  - **Clause & Entity Extraction**: Automatically extract parties, effective dates, governing laws, and key provisions.
  - **Risk Analysis & Audit**: Identify legal exposure with severity scoring and mitigation recommendations.
  - **Document Comparison**: Analyze diffs and contractual variations between versions.
  - **Multi-Document Case Synthesis**: Synthesize cross-document intelligence across entire matter files.
- **🔐 Row-Level Owner Isolation**: Server-side authorization restricting document and case access strictly to permitted accounts.
- **🛡️ Fault-Tolerant Resilience**:
  - **Smart Token Windowing (`truncate_for_llm`)**: Prevents 413/429 Groq token limit overflows on large scanned OCR documents.
  - **Local Heuristic Fallbacks**: Generates text-derived summaries and extractions when third-party AI rate limits occur, preventing 500 white-screen crashes.
  - **React Error Boundaries**: Isolates UI rendering errors without disrupting the main application shell.
  - **Automatic Task Healing**: Lifespan background service auto-heals document tasks stuck >10 minutes.
- **📊 Real-Time Analytics & Audit Trail**: Visual risk heatmaps, classification charts, and comprehensive PostgreSQL audit logs (`audit_logs`).

---

## 🏗️ System Architecture

```
                 +--------------------------------+
                 |    React + TypeScript SPA      |
                 |      (Vite + Lucide Icons)     |
                 +---------------+----------------+
                                 | REST API / WebSockets
                                 v
                 +---------------+----------------+
                 |    FastAPI Python Backend      |
                 |  (Uvicorn + Pydantic + JWT)    |
                 +-------+----------------+-------+
                         |                |
           +-------------+                +-------------+
           |                                            |
           v                                            v
+----------+----------+                      +----------+----------+
| PostgreSQL Database |                      |   Groq LLM AI Engine    |
| (SQLAlchemy Models) |                      | (llama-3.1-8b-instant)   |
+---------------------+                      +---------------------+
```

---

## 🛠️ Quick Start & Local Setup

### Prerequisites
- Node.js 18+ & npm
- Python 3.11+
- PostgreSQL 14+ (or Docker)

### 1. Environment Configuration
Create a `.env` file inside `backend/`:
```env
APP_NAME=LexFlow
APP_VERSION=1.0.0
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://postgres:postgrespassword@localhost:5432/lexflow
SECRET_KEY=production_jwt_secret_change_me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation (Swagger UI) is available at: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173/`** in your browser.

---

## 🐳 Containerized Production Deployment (Docker Compose)

Deploy the full production stack (FastAPI Backend, React Nginx Frontend, PostgreSQL 16, and Redis 7) with a single command:

```bash
docker-compose up --build -d
```

- **Frontend Application**: `http://localhost/`
- **Backend API Service**: `http://localhost:8000/api/v1/`
- **API Swagger Docs**: `http://localhost:8000/docs`

---

## 🗄️ Database Schema & Models

- **`users`**: Account credentials, hashed password, role (`LAWYER`, `PARALEGAL`, `ADMIN`).
- **`cases`**: Matter metadata, title, case number (unique), client name, opposing party, court, description, status, priority, owner FK (`index=True`).
- **`documents`**: File name, file path, extracted OCR text, category, version, status (`COMPLETED`, `ANALYSIS_PAUSED`, `FAILED_QUOTA`), case FK (`index=True`).
- **`ai_analyses`**: JSON result, analysis type (`summary`, `classification`, `clause_extraction`, `risk_analysis`, `synthesis`), document FK (`index=True`).
- **`audit_logs`**: Security & activity trail, action type, entity ID, details, user FK (`index=True`).

---

## 🧪 QA & Verification Verification Commands

Run full static analysis and unit tests:
```bash
# Backend Quality Assurance
cd backend
source venv/bin/activate
ruff check .
mypy .
pytest

# Frontend Quality Assurance
cd frontend
npx tsc --noEmit
npm run build
```

---

## ⚖️ Legal & AI Product Disclaimer

> **AI Legal Disclaimer**: LexFlow AI analysis outputs and extractions are workflow decision-support tools designed to assist legal professionals. AI outputs do not constitute formal legal advice or substitute for professional attorney evaluation and independent discovery review.

---

## 📄 License
Commercial Enterprise License — LexFlow Inc. All rights reserved.
