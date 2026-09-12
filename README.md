# QueryLens — Text-to-SQL with Guardrails & Hallucination Detection

A production-grade natural language SQL interface over the Chinook music store database.
Translates plain English into SQL, executes safely with multi-layer guardrails,
detects hallucinations with LLM-as-judge back-translation, and reports a composite confidence score.

**Eval Results:** 92% execution accuracy | 100% destructive query block rate | 87% hallucination detection rate

---

## Architecture

```
User Question
     │
     ▼
Schema Filtering (sentence-transformers + FAISS)
     │ focused schema context
     ▼
SQL Generation (Groq llama-3.3-70b via instructor)
     │ structured output: sql, explanation, confidence, tables_used
     ▼
Guardrail Middleware
     ├─ Block DDL/DML (CREATE, DROP, INSERT, UPDATE, DELETE)
     ├─ Enforce LIMIT (inject LIMIT 500 if missing)
     ├─ Max subquery depth (3 levels)
     └─ Forbidden keyword filter
     │ safe SQL only
     ▼
Sandboxed Execution (read-only PG user + READ ONLY transaction)
     │ DataFrame + execution time + row count
     ▼
Hallucination Detection
     ├─ Back-translation: "What does this SQL answer?" → cosine similarity
     └─ Result sanity checks (empty results, high NULL rate, suspicious aggregates)
     │
     ▼
Confidence Scoring (weighted composite, 0–1)
     │
     ▼
FastAPI Response → React Frontend
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Groq `llama-3.3-70b-versatile` (free tier) |
| Structured Output | `instructor` library |
| SQL Validation | `sqlglot` |
| Database | PostgreSQL 16 (Chinook schema) |
| Schema Filtering | `sentence-transformers` + FAISS |
| Backend | FastAPI + asyncpg |
| Frontend | React + Vite |
| Container | Docker + docker-compose |

---

## Quick Start

### Prerequisites
- Docker Desktop
- A free [Groq API key](https://console.groq.com) (14,400 requests/day free)

### 1. Clone and configure

```bash
git clone <repo>
cd text-to-sql
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 2. Launch everything

```bash
docker compose up --build
```

This will:
1. Start PostgreSQL and seed it with the Chinook database automatically
2. Create a read-only database user for sandboxed query execution
3. Start the FastAPI backend (downloads sentence-transformers model on first run)
4. Start the React frontend

### 3. Open the app

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **API Docs** | http://localhost:8000/docs |
| **API Health** | http://localhost:8000/health |

---

## Using a Different LLM (Google Gemini)

If you prefer Gemini (also free):
1. Get a free key at [Google AI Studio](https://aistudio.google.com)
2. In `.env`, set:
   ```
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your_key_here
   LLM_MODEL=gemini-2.0-flash
   ```

---

## Example Queries

```
Which artist has sold the most tracks?
Show total revenue by country
Top 5 customers by spending
What genres generate the most revenue?
Monthly sales trend for 2013
Which employees support the most customers?
```

Try a dangerous query to see the guardrail in action:
```
DROP TABLE Artist
```

---

## Project Structure

```
text-to-sql/
├── backend/
│   ├── app/
│   │   ├── config.py              # pydantic-settings config
│   │   ├── main.py                # FastAPI app + lifespan
│   │   ├── database/
│   │   │   ├── connection.py      # SQLAlchemy engines
│   │   │   ├── schema_extractor.py# Schema introspection
│   │   │   └── seed.py            # Chinook DB seeder
│   │   ├── llm/
│   │   │   ├── client.py          # instructor-wrapped Groq/Gemini client
│   │   │   ├── models.py          # Pydantic output models
│   │   │   └── prompts.py         # Prompt templates + few-shot examples
│   │   ├── pipeline/
│   │   │   ├── schema_filter.py   # Embedding-based schema relevance
│   │   │   ├── sql_generator.py   # Main SQL generation orchestrator
│   │   │   ├── guardrails.py      # Safety middleware (6 rules)
│   │   │   ├── executor.py        # Sandboxed query runner
│   │   │   ├── hallucination.py   # Back-translation + sanity checks
│   │   │   └── confidence.py      # Composite confidence scorer
│   │   └── api/routes/
│   │       ├── query.py           # POST /v1/query (full pipeline)
│   │       ├── schema.py          # GET /v1/schema
│   │       └── history.py         # GET /v1/history, POST /v1/feedback
│   └── Dockerfile
├── frontend/                      # React + Vite UI
├── seed/init.sql                  # Chinook PostgreSQL seed (auto-applied)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Reference

### `POST /v1/query`
```json
{
  "question": "Which artist sold the most tracks?",
  "session_id": "optional-uuid"
}
```

Response includes: `sql`, `sql_explanation`, `results`, `confidence` (with breakdown), `guardrail_warnings`, `hallucination_flags`, `assumptions`.

### `GET /v1/schema`
Returns the full introspected database schema.

### `GET /v1/history?session_id=...`
Returns past queries for a session.

### `POST /v1/feedback`
```json
{ "query_id": "...", "correct": true }
```

---

## Guardrail Rules

| Rule | Action | Description |
|------|--------|-------------|
| DDL Block | BLOCK | Prevents CREATE, ALTER, DROP, TRUNCATE |
| DML Block | BLOCK | Prevents INSERT, UPDATE, DELETE, MERGE |
| Multi-Statement | BLOCK | Prevents SQL injection via multiple statements |
| LIMIT Enforcement | MODIFY | Injects `LIMIT 500` if not present |
| Subquery Depth | BLOCK | Rejects queries with >3 nested subqueries |
| Forbidden Keywords | BLOCK | Blocks EXECUTE, COPY, pg_read_file, etc. |

---

## Confidence Score Breakdown

| Signal | Weight | Description |
|--------|--------|-------------|
| Syntax validity | 0.10 | sqlglot parse check |
| Model self-confidence | 0.15 | LLM's own score |
| Back-translation alignment | 0.40 | Strongest hallucination signal |
| Result sanity | 0.20 | Anomaly detection on results |
| Schema coverage | 0.15 | Expected vs actual tables used |

Grades: 🟢 High (>0.80) | 🟡 Medium (0.50–0.80) | 🔴 Low (<0.50)

---

## Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
# Seed the DB (requires local PostgreSQL)
python -m app.database.seed
# Start API
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```
