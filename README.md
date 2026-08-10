# ⚖️ LexFlow — Full-Stack AI Legal Case Management & Analysis System

**LexFlow** is a full-stack legal tech application built to streamline legal case management, document text extraction, risk auditing, and multi-document AI synthesis. 

Built as a comprehensive software engineering portfolio project by **Mayank Sharma**, LexFlow demonstrates modern system design, asynchronous API development, LLM integration, OCR document pipelines, relational database optimization, and responsive frontend design.

---

## 🎯 Technical Highlights & Skills Demonstrated

- **⚡ Fast REST API & Backend Architecture**: Built with **FastAPI**, **Python 3.13**, **Pydantic v2**, and **SQLAlchemy ORM**. Implements asynchronous endpoints, strict request/response validation, and clean layered architecture (Controllers $\rightarrow$ Services $\rightarrow$ Repositories).
- **🤖 LLM Integration & Rate-Limit Resilience**: Integrates **Groq API (`llama-3.1-8b-instant`)** for document intelligence. Implements sliding token windowing (`truncate_for_llm`) and local heuristic fallbacks to prevent third-party rate limit (429) crashes on long scanned PDFs.
- **📄 Multimodal Document & OCR Pipeline**: Supports `.pdf`, `.docx`, `.doc`, `.txt`, `.png`, `.jpg`, `.jpeg` uploads (up to 20MB). Combines **PyMuPDF** for digital text extraction with **Tesseract OCR** fallback for scanned images and contracts.
- **🔐 Row-Level Security & Auth**: Full **JWT Bearer Token authentication** with bcrypt password hashing and server-side row-level data isolation (`owner_id` checks) preventing cross-account data leaks.
- **🧠 Advanced NLP & RAG Concepts**: Implements RAG vector semantic search over case documents, TF-IDF/LLM hybrid summarization, and entity-relation Knowledge Graph generation.
- **📊 Compliance Audit Trail**: Tracks all user actions (`CASE_CREATE`, `DOCUMENT_UPLOAD`, `AI_SUMMARY`) in PostgreSQL (`audit_logs`) with live security tracking.
- **🐳 Full Containerization**: Standardized **Docker Compose** orchestration running FastAPI backend, React Nginx SPA proxy, PostgreSQL 16, and Redis 7.

---

## 💻 Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Lucide Icons, Custom CSS Design System Tokens
- **Backend**: FastAPI, Python 3.13, Uvicorn, Pydantic v2, SQLAlchemy
- **Database & Caching**: PostgreSQL 16 (with indexed foreign keys), Redis 7
- **AI & OCR Engines**: Groq LLM API (`llama-3.1-8b-instant`), PyMuPDF (`fitz`), Tesseract OCR
- **DevOps & Testing**: Docker, Docker Compose, Nginx, Pytest, Mypy, Ruff

---

## 🚀 System Architecture

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

## 🛠️ Key Product Features

1. **Legal Case & Matter Management**: Create, edit, search, and track legal matters with metadata, clients, opposing parties, court jurisdictions, and priority levels.
2. **Document Processing & OCR**: Upload and parse legal contracts with automated digital text extraction and Tesseract OCR fallback.
3. **AI Legal Intelligence (6 Core Capabilities)**:
   - **Executive Summarization**: Generate concise overviews of long legal agreements.
   - **Document Classification**: Categorize contracts (NDA, Lease, Affidavit, Petition) with confidence scores.
   - **Clause & Entity Extraction**: Automatically extract parties, effective dates, governing laws, and obligations.
   - **Risk Analysis**: Audit legal risk with severity scoring (High/Medium/Low) and mitigation advice.
   - **Document Comparison**: Compare diffs and contractual variations between document versions.
   - **Multi-Document Case Synthesis**: Synthesize cross-document intelligence across an entire matter file.
4. **Interactive Analytics & Audit Trail**: Real-time risk distribution charts, document type breakdowns, and security audit logs.

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
SECRET_KEY=your_jwt_secret_key_here
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
Interactive API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173/` in your browser.

---

## 🐳 Docker Deployment (Single Command)

Run the full stack (FastAPI Backend, React Nginx Frontend, PostgreSQL 16, and Redis 7) using Docker Compose:

```bash
docker-compose up --build -d
```

- **Frontend SPA**: `http://localhost/`
- **Backend API**: `http://localhost:8000/api/v1/`
- **Swagger Docs**: `http://localhost:8000/docs`

---

## 🧪 Testing & Code Quality

Run backend unit tests and static type checking:
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

## ⚖️ Disclaimer

> **Academic / Portfolio Disclaimer**: LexFlow AI analysis outputs and document extractions are decision-support tools built for workflow automation and software engineering demonstration purposes. They do not constitute formal legal advice.

---

## 👨‍💻 Author

**Mayank Sharma**  
- GitHub: [@mayanksharma2511](https://github.com/mayanksharma2511)

---

## 📄 License
MIT License — Free for educational and personal use.
