# QueryLens — Text-to-SQL with Guardrails & Hallucination Detection

QueryLens is a natural-language SQL interface over the Chinook music store database. It translates plain-English questions into SQL, executes them safely through a multi-layer guardrail system, detects potential hallucinations using LLM-based back-translation and result sanity checks, and reports a composite confidence score.

## Architecture

```text
User Question
     │
     ▼
Schema Filtering
(sentence-transformers + FAISS)
     │
     │ focused schema context
     ▼
SQL Generation
(Groq + Instructor)
     │
     │ SQL + explanation + confidence
     ▼
Guardrail Middleware
     ├─ DDL/DML blocking
     ├─ Multi-statement blocking
     ├─ LIMIT enforcement (500)
     ├─ Subquery depth limit (3)
     ├─ Forbidden keyword filtering
     └─ Comment stripping
     │
     ▼
Sandboxed Execution
(PostgreSQL read-only user + READ ONLY transaction)
     │
     ▼
Hallucination Detection
     ├─ SQL back-translation
     └─ Result sanity checks
     │
     ▼
Confidence Scoring
     │
     ▼
FastAPI → React Frontend
```

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq — `openai/gpt-oss-120b` |
| Structured Output | Instructor |
| SQL Validation | SQLGlot |
| Database | PostgreSQL 16 |
| Dataset | Chinook Music Store |
| Schema Filtering | Sentence Transformers + FAISS |
| Backend | FastAPI + asyncpg |
| Frontend | React + Vite |
| Containerization | Docker + Docker Compose |
| Configuration | Pydantic Settings |

## Key Features

- Natural-language → SQL generation
- Embedding-based schema filtering
- Structured LLM output using Pydantic + Instructor
- SQL syntax validation with SQLGlot
- DDL/DML protection
- Multi-statement query blocking
- Forbidden keyword detection
- Automatic `LIMIT 500`
- Maximum subquery depth of 3
- SQL comment stripping
- Read-only PostgreSQL execution
- LLM-based hallucination detection
- Result sanity checks
- Composite confidence scoring
- Query history and feedback
- Interactive React frontend

## Quick Start

### Prerequisites

- Docker Desktop
- Groq API key

### 1. Clone and configure

```bash
git clone <your-repository-url>
cd text-to-sql
cp .env.example .env
```

Add your API key to `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
```

> Never commit `.env` or API keys to GitHub.

### 2. Launch

```bash
docker compose up --build
```

Docker automatically:

- Starts PostgreSQL
- Initializes the Chinook database
- Creates the read-only database user
- Starts the FastAPI backend
- Downloads the sentence-transformers model on first startup
- Starts the React frontend

### 3. Open the application

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API Docs | http://localhost:8000/docs |
| API Health | http://localhost:8000/health |

These URLs are for local development.

## Example Queries

```text
Which artist sold the most tracks?
Top 5 customers by spending
What is the total revenue for each genre?
Show total revenue by country
What were the monthly sales in 2025?
Which employees support the most customers?
```

You can also test the safety system with destructive requests such as:

```text
Delete all customers from the database
```

or SQL such as:

```sql
DROP TABLE Artist;
```

Destructive operations are rejected before database execution.

## Hallucination Detection

QueryLens uses two complementary approaches:

### SQL Back-Translation

The generated SQL is sent through an LLM-as-judge step that answers:

> What question does this SQL answer?

The generated interpretation is compared with the original question to estimate semantic alignment.

### Result Sanity Checks

Execution results are checked for suspicious conditions including:

- Empty results
- High NULL rates
- Suspicious aggregates

These signals contribute to the final confidence score.

## Confidence Scoring

The final confidence score combines multiple signals:

| Signal | Weight |
|---|---:|
| Syntax validity | 0.10 |
| Model self-confidence | 0.15 |
| Back-translation alignment | 0.40 |
| Result sanity | 0.20 |
| Schema coverage | 0.15 |

Grades:

- 🟢 **High:** > 0.80
- 🟡 **Medium:** 0.50–0.80
- 🔴 **Low:** < 0.50

## Guardrail Rules

| Rule | Action | Description |
|---|---|---|
| DDL Block | BLOCK | Prevents CREATE, ALTER, DROP, etc. |
| DML Block | BLOCK | Prevents INSERT, UPDATE, DELETE, etc. |
| Multi-Statement | BLOCK | Prevents multiple SQL statements |
| LIMIT Enforcement | MODIFY | Injects LIMIT 500 when missing |
| Subquery Depth | BLOCK | Rejects queries exceeding 3 nested SELECT levels |
| Forbidden Keywords | BLOCK | Blocks EXECUTE, COPY, pg_read_file, etc. |
| Comment Stripping | MODIFY | Removes SQL comments before execution |

The guardrail layer has been directly tested against destructive SQL, multi-statement queries, dangerous PostgreSQL functions, deeply nested subqueries, comments, and queries without explicit limits.

## API Reference

### `POST /v1/query`

Converts a natural-language question into SQL and executes it through the complete pipeline.

```json
{
  "question": "Which artist sold the most tracks?",
  "session_id": "optional-session-id"
}
```

Response includes:

```text
sql
sql_explanation
results
columns
row_count
execution_time_ms
confidence
guardrail_warnings
hallucination_flags
assumptions
is_answerable
clarification_needed
error
```

### `GET /v1/schema`

Returns the introspected database schema.

### `GET /v1/history?session_id=...`

Returns query history for a session.

### `POST /v1/feedback`

Records feedback for a generated query.

```json
{
  "query_id": "...",
  "correct": true
}
```

## Project Structure

```text
text-to-sql/
├── backend/
│   ├── app/
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   ├── schema_extractor.py
│   │   │   └── seed.py
│   │   ├── llm/
│   │   │   ├── client.py
│   │   │   ├── models.py
│   │   │   └── prompts.py
│   │   ├── pipeline/
│   │   │   ├── schema_filter.py
│   │   │   ├── sql_generator.py
│   │   │   ├── guardrails.py
│   │   │   ├── executor.py
│   │   │   ├── hallucination.py
│   │   │   └── confidence.py
│   │   └── api/routes/
│   │       ├── query.py
│   │       ├── schema.py
│   │       └── history.py
│   └── Dockerfile
├── frontend/
├── seed/
│   └── init.sql
├── docker-compose.yml
├── .env.example
└── README.md
```

## Development Without Docker

### Backend

```bash
cd backend
pip install -r requirements.txt

# Requires local PostgreSQL
python -m app.database.seed

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Future Improvements

- Larger automated evaluation datasets
- More comprehensive hallucination benchmarks
- Improved schema retrieval
- Additional SQL dialect support
- Persistent query history
- Authentication and authorization
- Production deployment and observability
```
