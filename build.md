# AskSQL — Full Project Build Specification

> **Purpose of this document:** This is a complete implementation brief for an AI coding assistant (GitHub Copilot, Claude Code, Cursor, etc.) to build this project end-to-end. Treat every section as a requirement, not a suggestion. Flag any deviation from the locked tech stack (Section 3) with the developer (Ayush) before proceeding. Sections marked **[ASK FIRST]** require a quick check-in with the developer rather than a silent assumption.

## Table of Contents
1. Project Overview
2. Core Concept & User Flow
3. Tech Stack (Locked)
4. Dataset
5. Architecture Diagram
6. Feature List & Scope Boundaries
7. Prompt Engineering — Exact Templates
8. Safety / Validation Layer
9. Evaluation Benchmark
10. Environment Variables
11. File Structure
12. Week-by-Week Roadmap + Definition of Done
13. `README.md` Spec
14. `INTERVIEW_PREP.md` Spec
15. Open Questions Log

---

## 1. Project Overview

**Name:** AskSQL
**One-liner:** A web app where a user types a question in plain English (e.g., *"What were our top 5 best-selling products last month?"*) and gets back the generated SQL query, a plain-English explanation of that query, and the actual results from a real database — no SQL knowledge required.

**Why this project exists (context for the AI assistant):**
This is a resume/portfolio piece for SDE internship and new-grad applications — the **second flagship project** alongside an existing one called "CodeVerdict" (multi-agent RAG-based code review tool). AskSQL must demonstrate **different** skills than CodeVerdict:
- Full-stack (React + FastAPI) — CodeVerdict has no frontend
- Cloud deployment (Render/Railway) — CodeVerdict isn't deployed
- Safety/validation engineering (blocking destructive SQL) — distinct from CodeVerdict's static-analysis integration
- RAG over **structured schemas** rather than unstructured documents

**Hard constraint:** this must not read as a CodeVerdict rebuild. Different folder structure, and never describe it as "another RAG app" in any docs — the pitch is full-stack + cloud + safety-validation.

**Timeline:** 2–4 weeks, part-time, solo, 4th-year CS student — realistic scope only.

---

## 2. Core Concept & User Flow

1. User opens the app: input box + example questions + schema browser sidebar.
2. User types a question (e.g., "Show me customers who spent more than $500 total").
3. Backend embeds the question, retrieves the most relevant table/column descriptions from ChromaDB (schema-aware RAG — prevents hallucinated table/column names).
4. Groq/Llama 3 generates SQL using the retrieved schema context (see Section 7 for exact prompt).
5. **Validator** checks the SQL is read-only and safe (Section 8) before it touches the DB.
6. Valid → executes against a **read-only Postgres role** → results returned.
7. Invalid/execution error → error fed back to the LLM for one bounded retry (max 2 attempts total).
8. Response includes: results table, the generated SQL (collapsible), and a plain-English explanation of the query.
9. Query + result saved to session-based query history.

---

## 3. Tech Stack (Locked — Do Not Substitute Without Asking)

| Layer | Choice | Notes |
|---|---|---|
| LLM | Groq API, Llama 3 (`llama-3.1-70b-versatile` or latest available Llama 3.x on Groq — **verify current model name at build time**, Groq deprecates model strings periodically) | Reuses developer's CodeVerdict experience |
| Backend | Python + FastAPI | Async support |
| Vector store | ChromaDB, embedded/local mode | No separate server needed |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) | Same library as CodeVerdict |
| Database | PostgreSQL | See Section 4 |
| Frontend | React + Vite | Not Create React App |
| Styling | Tailwind CSS | Fast, clean UI |
| Containerization | Docker + Docker Compose | Local/deploy parity |
| Deployment | Render or Railway (not AWS for this build) | Faster than AWS, still a "live app"; keep portable for future AWS migration |
| CI | GitHub Actions (lint + eval script on push) | Lightweight, no full CD |

**Explicitly out of scope:** Kubernetes, Kafka/message queues, user authentication, multi-tenant support, LangChain (build RAG + LLM calls directly with the Groq SDK — stronger interview story than a framework wrapper).

---

## 4. Dataset

**Default (confirm before building — [ASK FIRST]):** Olist Brazilian E-Commerce Public Dataset on Kaggle (`olistbr/brazilian-ecommerce`). Concrete alternative if that one feels stale by build time: "E-Commerce Data" by Carrie1 (`carrie1/ecommerce-data`, UK online retailer transactions). Either works — pick whichever has cleaner multi-table structure at time of build; do not spend more than 30 minutes deciding.

**Why e-commerce over Chinook/Northwind:** business-relevant demo questions ("top selling products," "average order value by region," "customers with late deliveries") read better on a resume than a music-store schema.

**Setup requirements:**
- Load into Postgres with a documented schema, 5-8 tables (enough for interesting joins, not so many retrieval gets noisy).
- Write `schema_descriptions.json` with a real, human-written description per table/column — **not raw column names**. Description quality directly drives SQL generation accuracy. Example:
  ```json
  {
    "table": "orders",
    "description": "One row per customer order.",
    "columns": {
      "order_status": "Current status: one of 'delivered', 'shipped', 'processing', 'cancelled'.",
      "order_purchase_timestamp": "When the order was placed, UTC timestamp."
    }
  }
  ```
- Create a read-only Postgres role (`asksql_readonly`, `GRANT SELECT` only). App connects through this role — never the owner/superuser role.

---

## 5. Architecture Diagram

```
┌─────────────┐         ┌──────────────────────────────────────────┐
│  React UI   │────────▶│              FastAPI Backend               │
│ (Vite +     │         │                                            │
│  Tailwind)  │◀────────│  1. Schema Retriever (ChromaDB)            │
└─────────────┘         │     embeds question → top-k schema chunks  │
                         │                                            │
                         │  2. SQL Generator (Groq/Llama 3)           │
                         │     question + schema context → SQL        │
                         │                                            │
                         │  3. SQL Validator                          │
                         │     blocks non-SELECT, multi-statement,     │
                         │     comments, unknown tables/columns        │
                         │                                            │
                         │  4. Query Executor                         │
                         │     read-only role, timeout, retry (≤2x)   │
                         │                                            │
                         │  5. Explainer (Groq/Llama 3)                │
                         │     SQL → plain-English explanation         │
                         └──────────────┬─────────────────────────────┘
                                        ▼
                              ┌───────────────────┐
                              │ PostgreSQL (read-  │
                              │ only role)         │
                              └───────────────────┘
```

---

## 6. Feature List & Scope Boundaries

### Must-have (Weeks 1-3)
1. NL → SQL generation via schema-aware RAG
2. SQL safety validator
3. Query execution → results rendered as a table
4. Plain-English query explanation
5. Bounded retry loop on execution failure
6. React UI: input, results table, collapsible SQL, loading/error states
7. `docker-compose up` runs the whole stack

### Should-have (Weeks 3-4, differentiators)
8. Session-based query history sidebar
9. 20-30 question eval benchmark measuring execution accuracy (mirrors CodeVerdict's eval rigor)
10. Schema browser sidebar

### Nice-to-have (only if ahead of schedule — never at the cost of deployment)
11. Auto-chart result sets that look chart-worthy
12. Standalone "explain this SQL" mode (paste SQL, no NL question needed)
13. Persistent (DB-backed) query history

### Explicitly do not build
User authentication, multi-database support, manual SQL editing mode, admin dashboard. These add scope without adding resume value for a 2-4 week solo project.

---

## 7. Prompt Engineering — Exact Templates

This was previously left vague ("write the SQL generation prompt") — that's the single highest-leverage piece of engineering in this project and needs a concrete starting point, not a blank page.

### 7.1 SQL Generation Prompt (system message)
```
You are a PostgreSQL expert. Given a user's question and a set of relevant table/column
descriptions, generate exactly one read-only SELECT query that answers the question.

Rules:
- Output ONLY the SQL query. No explanation, no markdown formatting, no comments.
- Use only tables and columns provided in the schema context below. Never invent columns.
- Never use DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, GRANT, REVOKE, or CREATE.
- Write exactly one statement. Do not use semicolons to chain multiple statements.
- If the question cannot be answered with the given schema, output exactly: UNSUPPORTED

Schema context:
{retrieved_schema_chunks}

User question: {user_question}
```

### 7.2 Retry Prompt (on execution failure)
```
The following SQL query failed when executed against the database:

Query: {failed_query}
Error: {db_error_message}

Using the same schema context and original question, generate a corrected query.
Follow all the same rules as before. Output ONLY the corrected SQL query.

Schema context:
{retrieved_schema_chunks}

Original question: {user_question}
```

### 7.3 Explanation Prompt
```
Explain the following SQL query in plain English, in 2-4 sentences, for someone with
no SQL background. Describe what data it retrieves and any filtering/grouping/sorting
it applies. Do not repeat the raw SQL syntax back to them.

Query: {generated_sql}
```

**Implementation note:** log the raw LLM output before any parsing during development — Llama 3 occasionally wraps SQL in markdown code fences despite instructions not to; strip ` ```sql ` / ` ``` ` fences defensively in the generator code rather than relying on the prompt alone.

---

## 8. Safety / Validation Layer

This is the project's core differentiator — build carefully, test thoroughly, document clearly.

**Reject the generated query if any of the following are true:**
- Not a single `SELECT` statement (case-insensitive check; reject on any `;` followed by non-whitespace, which indicates stacked statements)
- Contains any of: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `GRANT`, `REVOKE`, `CREATE`
- Contains SQL comment markers (`--`, `/* */`) — these can hide malicious query segments
- References a table/column not present in the known schema metadata (also catches hallucinations, not just malicious input)

**Defense in depth (both layers, not one):**
- Layer 1: static text validation (above)
- Layer 2: DB-level enforcement — connection uses the `asksql_readonly` role with `SELECT`-only grants, so even a validator bypass can't mutate data

**Additional guards:**
- Auto-append `LIMIT 500` if the generated query has no limit clause
- 5-second query execution timeout

Document this as a "Security Considerations" section in the README (Section 13) — don't bury it, it's the strongest interview talking point in the project.

---

## 9. Evaluation Benchmark

1. Hand-write 20-30 NL questions with known-correct ("ground truth") SQL against the chosen dataset. Cover a spread of difficulty: simple single-table filters, aggregations, multi-table joins (2 and 3+ tables), date-range questions.
2. For each: run through the full pipeline, compare **execution accuracy** (does the generated query's result set match the ground truth's result set — not exact string match, since two queries can be equally correct).
3. Report: overall accuracy %, breakdown by question difficulty, common failure modes, mitigation notes.
4. Resume bullet template (fill in real numbers once measured):
   > "Built and ran a 25-question NL→SQL evaluation benchmark, achieving X% execution accuracy, with documented failure-mode analysis across join complexity and date-range queries."

**[ASK FIRST]** Confirm exact CodeVerdict eval bullet wording if matching tone/style matters before finalizing this one.

**Seed question bank (starter set — expand to 20-30, adjust to whichever dataset is chosen):**
- "How many orders were placed in total?"
- "What are the top 5 best-selling products by quantity?"
- "Which customers have spent more than $500 total?"
- "What is the average order value by month?"
- "Which product category has the most orders?"
- "How many orders were delivered late (delivered after the estimated delivery date)?"
- "What is the total revenue by customer region/state?"
- "Which customers placed more than 3 orders?"

---

## 10. Environment Variables

Document these in `.env.example` (values blank/placeholder, never commit real secrets):

```
GROQ_API_KEY=
DATABASE_URL=postgresql://asksql_readonly:<password>@localhost:5432/asksql
CHROMA_PERSIST_DIR=./data/chroma
BACKEND_PORT=8000
FRONTEND_API_BASE_URL=http://localhost:8000
QUERY_TIMEOUT_SECONDS=5
QUERY_ROW_LIMIT=500
```

`.gitignore` must exclude: `.env`, `node_modules/`, `__pycache__/`, `*.pyc`, any local DB dumps, `data/chroma/` (Chroma's local persistence directory).

---

## 11. File Structure

```
asksql/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db/
│   │   │   ├── connection.py        # read-only role connection
│   │   │   └── schema_metadata.py   # loads schema_descriptions.json
│   │   ├── rag/
│   │   │   ├── embed_schema.py
│   │   │   └── retriever.py
│   │   ├── llm/
│   │   │   ├── sql_generator.py     # Section 7.1/7.2 prompts
│   │   │   └── explainer.py         # Section 7.3 prompt
│   │   ├── validator/
│   │   │   └── sql_validator.py     # Section 8
│   │   ├── routers/
│   │   │   └── query.py             # POST /query
│   │   └── models/
│   │       └── schemas.py
│   ├── data/
│   │   ├── schema_descriptions.json
│   │   └── seed_data/
│   ├── eval/
│   │   ├── eval_questions.json
│   │   └── run_eval.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── QueryInput.jsx
│   │   │   ├── ResultsTable.jsx
│   │   │   ├── SqlDisplay.jsx
│   │   │   ├── QueryHistory.jsx
│   │   │   └── SchemaBrowser.jsx
│   │   ├── App.jsx
│   │   └── api.js
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .github/workflows/ci.yml
├── .env.example
└── README.md
```

---

## 12. Week-by-Week Roadmap + Definition of Done

### Week 1 — Data + Core Pipeline
- [ ] Dataset chosen and loaded into local Postgres
- [ ] `schema_descriptions.json` written with real descriptions
- [ ] ChromaDB set up, schema embedded
- [ ] Retriever returns relevant chunks for a test question
- [ ] SQL generation prompt (7.1) wired to Groq, producing SQL for 5-10 sample questions manually reviewed

**Definition of done:** typing a question in a script/notebook produces plausible SQL referencing real tables — no execution or safety layer yet.

### Week 2 — Safety + Execution
- [ ] SQL validator built with unit tests covering every rejection case in Section 8
- [ ] Read-only Postgres role created and used by the app
- [ ] Query execution + retry loop (7.2) wired up
- [ ] Explanation call (7.3) wired up
- [ ] Eval question bank drafted (20-30 pairs, Section 9)

**Definition of done:** a validator unit test suite passes for every attack pattern in Section 8; a full question → validated SQL → executed result → explanation round-trip works end-to-end via API calls (Postman/curl is fine, no UI yet).

### Week 3 — Frontend + Integration
- [ ] React app scaffolded, all components built
- [ ] Frontend wired to `/query` endpoint
- [ ] Loading/error states handled
- [ ] Query history + schema browser sidebars working
- [ ] Eval script run, accuracy recorded, prompt/retrieval iterated on if low

**Definition of done:** a person with no SQL knowledge can open the app, ask a question from the seed bank, and see correct results with zero backend intervention.

### Week 4 — Polish + Deploy
- [ ] Full stack Dockerized, `docker-compose up` verified end-to-end
- [ ] Deployed to Render or Railway (backend + Postgres + frontend)
- [ ] GitHub Actions CI running lint + eval on push
- [ ] README written (Section 13)
- [ ] INTERVIEW_PREP.md written (Section 14), using real specifics from the actual build
- [ ] Demo GIF/video recorded
- [ ] Resume bullet finalized with real eval accuracy number

**Definition of done:** the live deployment link works from a fresh browser with no local setup; README instructions, followed exactly by someone else, produce a working local copy.

---

## 13. `README.md` Spec (Canonical — Single Source of Truth)

Include, in this order:

1. Project name, one-line description, demo GIF/screenshot
2. Architecture diagram (Section 5) + tech stack table (Section 3)
3. **Security Considerations** — expanded Section 8, don't bury it
4. **Evaluation Results** — accuracy %, methodology, failure modes (Section 9)
5. **Prerequisites** — Python version, Node version, Docker version, Groq API key + where to get one
6. **Local setup (first-time clone)** — exact steps:
   - `git clone`, create `.env` from `.env.example` (Section 10), install backend deps, install frontend deps, load seed dataset into Postgres (exact command), embed schema into ChromaDB (exact command + when to re-run), `docker-compose up` for full stack, plus separate run instructions for backend/frontend without Docker
7. **Day-to-day dev workflow** — `uvicorn app.main:app --reload`, `npm run dev`, `python eval/run_eval.py` (and how to read output), lint/test commands
8. **Git workflow** — branch naming (`feature/query-validator`), commit conventions, `git checkout -b`, `git push -u origin <branch>`, `git pull origin main`, basic conflict resolution, PR-even-when-solo practice
9. **CI** — what GitHub Actions checks on push
10. **Deployment (Render/Railway)** — backend deploy steps (env vars, build/start commands), Postgres provisioning + seed load, frontend deploy steps (build command, output dir, backend URL env var), smoke-test checklist, redeploy behavior (auto vs manual), rollback steps
11. **Troubleshooting table** — e.g. "Chroma embeddings stale after schema change → re-run `embed_schema.py`"; "Groq rate limit hit → check retry/backoff logic"; "Postgres connection refused → check read-only role credentials in `.env`"
12. Live deployment link

Write this **after** the app works (end of Week 3 / start of Week 4) so it reflects reality, not the plan.

---

## 14. `INTERVIEW_PREP.md` Spec

Standalone doc, first-person, spoken-style — something to read almost verbatim before an interview. Written after the app works, using real specifics encountered during the build (prompt the developer for actual friction points rather than leaving these generic).

1. **30-second pitch**
2. **"Walk me through the architecture"** — narrated the way you'd say it on a screen-share, not a repeat of the diagram
3. **"Why did you choose X?"** — Groq/Llama 3 vs GPT-4, ChromaDB vs Pinecone, hand-rolled RAG vs LangChain, PostgreSQL vs NoSQL, rule-based validator vs trusting the LLM, read-only role AND validator vs just one
4. **"What was the hardest technical problem?"** — 2-3 real issues actually hit (e.g., retrieval returning irrelevant tables on ambiguous questions, hallucinated columns, multi-join accuracy, timeout tuning) and how each was diagnosed/fixed
5. **"How did you evaluate correctness?"** — methodology + real accuracy number + real failure modes
6. **Security deep-dive** — "what if someone tries a prompt injection for a DROP TABLE?", "what stops a query returning a million rows?", "what's your defense in depth?"
7. **Trade-offs / what you'd change at scale** — no persistent history, single-DB only, no auth, no caching; what production-readiness would require (caching repeated questions, connection pooling, rate limiting, multi-tenant schema isolation, managed vector DB)
8. **Curveball questions** — "how would this handle a 200-table schema?", "how do you stop a question containing SQL-like text from confusing the pipeline?", "how would you safely extend this to writes?" — each with a brief answer direction

---

## 15. Open Questions Log

Resolve these with the developer during the build rather than guessing silently:
1. **[ASK FIRST]** Final dataset pick between the two Section 4 options (or another, if both feel unsuitable once inspected).
2. Reuse CodeVerdict's prompt-engineering style/patterns, or write fresh ones for this project?
3. Exact resume bullet wording/tone to match CodeVerdict's.
4. Is persistent (DB-backed) query history worth the extra time vs. session-based, given the timeline?
5. Record a demo video? If yes, which seed questions to showcase?

---

*End of specification. Build section by section. Flag any deviation from the locked tech stack (Section 3) before implementing.*