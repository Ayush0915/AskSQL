# AskSQL ⚡

**One-liner:** AskSQL is a full-stack web application where users type plain-English questions (e.g., *"What are our top 5 best-selling products by quantity?"*) and get back valid, execution-safe SQL queries, a plain-English explanation, and real-time results from a PostgreSQL database — no database knowledge required.

## 1. System Architecture & Tech Stack

### Architecture Workflow
```
┌─────────────┐         ┌──────────────────────────────────────────┐
│  React UI   │────────▶│              FastAPI Backend               │
│ (Vite +     │         │                                            │
│  Tailwind)  │◀────────│  1. Schema Retriever (ChromaDB)            │
│             │         │     embeds question → top-k schema chunks  │
│             │         │                                            │
│             │         │  2. SQL Generator (Groq/Llama 3)           │
│             │         │     question + schema context → SQL        │
│             │         │                                            │
│             │         │  3. SQL Validator                          │
│             │         │     blocks non-SELECT, multi-statement,     │
│             │         │     comments, unknown tables/columns        │
│             │         │                                            │
│             │         │  4. Query Executor                         │
│             │         │     read-only role, timeout, retry (≤2x)   │
│             │         │                                            │
│             │         │  5. Explainer (Groq/Llama 3)                │
│             │         │     SQL → plain-English explanation         │
│             │         └──────────────┬─────────────────────────────┘
│             │                        │
└─────────────┘                        ▼
                             ┌───────────────────┐
                             │ PostgreSQL (read-  │
                             │ only role)         │
                             └───────────────────┘
```

### Tech Stack Table

| Layer | Choice | Notes |
|---|---|---|
| **LLM Engine** | Groq API / Llama 3 (`llama-3.3-70b-versatile`) | Fast inference, high SQL syntax accuracy. |
| **Backend** | Python + FastAPI | High-performance asynchronous API layer. |
| **Vector Store** | ChromaDB (local/embedded mode) | Semantic table schema lookup to build context. |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Local execution matching production RAG pipelines. |
| **Database** | PostgreSQL | Realistic e-commerce dataset schema. |
| **Frontend** | React (Vite) | Fast developer server startup and optimized client. |
| **Styling** | Tailwind CSS | Sleek glassmorphism style & responsive design. |
| **Container** | Docker + Docker Compose | Clean service isolation and identical dev/prod setups. |
| **CI** | GitHub Actions | Syntax lint checks, database seeds, and test runner. |

---

## 2. Security Considerations & Safety Layer

AskSQL implements a strict multi-layer defense system to block any malicious inputs, SQL injections, or unintended database updates.

### Layer 1: Static Code Rejection (SQL Validator)
Before any query touches the database, it is passed to the `SQLValidator`. A query is **rejected instantly** if:
* **Not a SELECT statement:** It must start case-insensitively with `SELECT`.
* **Contains Mutators/DDL:** Rejects any occurrence of keywords: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `GRANT`, `REVOKE`, or `CREATE`.
* **Stacked Statements:** Semicolons (`;`) followed by non-whitespace statements are blocked.
* **SQL Comments:** Disallows `--` or `/* */` markers used to bypass filters.
* **Metadata Check:** Verifies referenced tables and columns exist in `schema_descriptions.json` to prevent hallucinated columns or access to system catalog tables.

### Layer 2: Database-level Isolation (Read-Only User)
Even if static validation is bypassed:
* The application connects to PostgreSQL using a dedicated `asksql_readonly` user.
* This user only has `CONNECT`, `USAGE` on schema, and `SELECT` privilege on tables. Any write operation results in database-level termination.

### Layer 3: Query Execution Limits
* **Limit Enforcement:** Automatically appends `LIMIT 500` if the query doesn't specify limits.
* **Statement Timeout:** Connections are configured with `statement_timeout` set to 5 seconds to stop infinite/expensive scans.

---

## 3. Evaluation Results & Methodology

The pipeline was evaluated against the **20-Question E-Commerce Benchmark Suite** located at `backend/eval/eval_questions.json`.
* **Methodology:** We compare the **execution results** of generated SQL queries to ground-truth answers (rather than exact string matching, since multiple SQL queries can be valid). Floating values are rounded to 2 decimal places and rows sorted to handle set equality.
* **Execution Accuracy:** 95.00% (19/20 queries passed).
* **Breakdown by Difficulty:**
  * Simple queries: 100.00%
  * Medium queries: 100.00%
  * Complex queries: 80.00% (joins/aggregations)
* **Common Failure Modes:** Complex multi-way joins with multiple grouping expressions occasionally match incorrect key mappings if columns are named similarly.

---

## 4. Prerequisites

To run this project locally, ensure you have:
1. **Python:** Version 3.11+
2. **Node.js:** Version 20+
3. **Docker Desktop:** (Optional, for containerized run)
4. **Groq API Key:** Sign up at [console.groq.com](https://console.groq.com/) to get a free API key.

---

## 5. Local Setup

### Setup Step-by-Step (Without Docker)

1. **Clone the repository:**
   ```bash
   git clone <repo-url> asksql
   cd asksql
   ```

2. **Configure Environment Variables:**
   Copy the example environment file and fill in your details (especially `GROQ_API_KEY`):
   ```bash
   cp .env.example .env
   ```

3. **Install Backend Dependencies:**
   Create a virtual environment and install packages:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

4. **Seed the Local Database:**
   Ensure PostgreSQL is running locally, then run the database builder:
   ```bash
   # Make sure the postgres service is running and accessible
   python -m backend.data.seed_data.seed_db
   ```

5. **Generate Vector Embeddings:**
   Build the ChromaDB vector database index for the schema retriever:
   ```bash
   python -m backend.app.rag.embed_schema
   ```

6. **Install Frontend Dependencies:**
   ```bash
   cd frontend
   npm install
   ```

### Run the App Using Docker Compose

If you have Docker installed, you can skip the local environment steps and launch the entire ecosystem in one command:
```bash
# Provide the Groq API key in your terminal env
export GROQ_API_KEY="gsk_..."
docker-compose up --build
```
This automatically spins up Postgres, seeds it with e-commerce data, generates the ChromaDB embeddings, starts the FastAPI server, and launches the React client.

* **React Frontend URL:** [http://localhost:3000](http://localhost:3000)
* **FastAPI Backend Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 6. Day-to-Day Development Workflow

* **Start Backend API:** `uvicorn backend.app.main:app --reload --port 8000`
* **Start Frontend Client:** `npm run dev` (runs at http://localhost:3000)
* **Run Evaluation Suite:** `python -m backend.eval.run_eval`
* **Check SQL Validator Code:** `python -m backend.app.validator.sql_validator`

### Git Workflow
* **Branching Strategy:** Use feature branches (`feature/add-validation`).
* **Commit Conventions:** Follow clear descriptive summaries (`feat: added comment filter to SQL validator`).

---

## 7. CI Pipeline (GitHub Actions)

On every push to `main` or pull request, `.github/workflows/ci.yml` triggers to:
1. Provision a PostgreSQL test container.
2. Verify Python syntax lint rules (`flake8`).
3. Seed test database tables and build schema descriptions.
4. Execute `sql_validator` unit self-checks.
5. Run the evaluation accuracy suite if the Groq token is available.

---

## 8. Deployment (Render/Railway)

### Backend Deployment Guide
1. **Provision Database:** Set up PostgreSQL on Render/Railway.
2. **Env Variables:** Set `GROQ_API_KEY`, `DATABASE_URL` (using readonly user), and `DATABASE_ADMIN_URL` (for seeding).
3. **Seed DB:** Execute `python -m backend.data.seed_data.seed_db` against the live connection.
4. **Deploy Command:** Build using the Python environment, start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`.

### Frontend Deployment Guide
1. **Static Site Hosting:** Deploy the `frontend/` folder to Vercel/Netlify.
2. **Build Settings:** Build command `npm run build`, Output directory `dist`.
3. **Environment:** Set `VITE_API_BASE_URL` pointing to your deployed FastAPI backend URL.

---

## 9. Troubleshooting Table

| Symptom | Cause | Solution |
|---|---|---|
| **ChromaDB metadata stale** | Changes made to `schema_descriptions.json` | Re-run vector index builder: `python -m backend.app.rag.embed_schema`. |
| **Groq 429 Rate Limit** | Too many sequential LLM generation requests | Check retries loop/decrease concurrency when running evaluation scripts. |
| **Postgres connection refused** | Database is inactive or credentials mismatch | Double check postgres status. Verify role permissions and strings in `.env`. |
| **Nginx frontend loading blank page** | API Endpoint not found | Inspect browser network tab. Ensure `VITE_API_BASE_URL` is set correctly during build. |
