# AskSQL — Interview Preparation Guide

This guide is structured in a spoken, first-person style. Read this prior to SDE interviews to confidently walk through the architecture, trade-offs, and engineering challenges of the AskSQL application.

---

## 1. The 30-Second Pitch

> "I built **AskSQL**, a full-stack AI application that lets non-technical users query SQL databases using natural English. A user types a question like *'Which customers spent over $500?'*, and the system uses schema-aware RAG to generate, validate, and execute a safe SQL query, displaying the results alongside a plain-English explanation. The core engineering focus was **security and validation** — establishing a strict multi-layer sandbox that prevents destructive SQL injection attacks, combined with an automated evaluation harness to measure query execution accuracy."

---

## 2. "Walk Me Through the Architecture"

> "When a user submits a query through the React frontend:
> 1. It goes to a **FastAPI backend**.
> 2. The backend first embeds the query using a local `sentence-transformers` model and looks up table schemas inside **ChromaDB**. This retrieves descriptions of the most relevant tables and columns, rather than packing all tables into the LLM context.
> 3. We pass the user's question and retrieved schemas to **Llama 3 via Groq**, which generates the SQL query.
> 4. Before executing the query, the SQL is intercepted by a custom static validator that blocks dangerous statements (like `DROP`, `DELETE`), stacked queries, and comment injections. It also checks that all tables/columns exist in the catalog schema to prevent hallucinations.
> 5. If it's valid, the backend executes the query against **PostgreSQL** using a restricted, read-only role with a strict 5-second timeout.
> 6. If the query throws an error or fails validation, we initiate a bounded one-time retry where we feed the error message back to the LLM to auto-correct.
> 7. Once successful, we ask Llama 3 to explain the SQL in plain English and return both the explanation and dataset rows back to the React UI."

---

## 3. "Why Did You Choose X?"

*   **Groq/Llama 3 vs. GPT-4:**
    > "I chose Groq's Llama 3 API for its incredible speed and cost-effectiveness. In a real-time conversational interface, latency is critical, and Groq provides token throughput that makes the system feel instant. It also gave me an opportunity to work directly with open-weights models."
*   **ChromaDB vs. Pinecone:**
    > "Since I wanted to keep local development portable and lightweight, ChromaDB in local persistence mode was a perfect fit. It runs embedded inside the Python backend process, removing the overhead of managing a separate cloud vector database instance while still providing full vector search capabilities."
*   **Hand-rolled RAG vs. LangChain:**
    > "I decided to build the RAG and LLM connection using the official Python SDKs instead of LangChain. Building it from scratch gives me absolute control over the prompts, retry behavior, and retrieval weights. It also makes for a cleaner interview story since I can explain the mechanics rather than hiding behind a framework wrapper."
*   **Rule-based Validator vs. Trusting the LLM:**
    > "You can never rely solely on prompt engineering or system messages for security; LLMs are susceptible to prompt injection. The rule-based validator acts as a deterministic firewall. If the LLM generates a write query (whether by accident or injection), the validator catches it immediately before it reaches the driver."
*   **Read-Only Role AND Validator vs. Just One:**
    > "This is a classic 'Defense in Depth' strategy. The validator prevents dangerous or hallucinated queries from running, keeping execution clean. The database read-only role is the absolute last line of defense — even if there is a bug in my validator code, the database engine itself will block any mutation attempt because the login user lacks authorization."

---

## 4. Hardest Technical Problems

*   **Irrelevant Tables Retrieved (Retrieval Noise):**
    > "Initially, when a user asked a vague query, the vector search would pull in tables that shared semantic terms but weren't part of the target joins. This caused the LLM to generate queries joining unrelated tables. I solved this by adding rich human-written column descriptions and table metadata into `schema_descriptions.json` instead of indexing raw schema strings. This metadata explicitly describes relationships (like 'joins with orders on order_id'), making semantic retrieval vastly more precise."
*   **Hallucinated Columns:**
    > "Sometimes Llama 3 would guess column names (e.g. using `created_at` instead of `order_purchase_timestamp`). To resolve this, I added a schema validation pass inside the validator that parses the SQL query's abstract syntax tree (using `sql-metadata`) and matches every referenced table/column against the actual database metadata. If a column isn't real, the validator rejects the query and triggers the auto-retry flow with a descriptive error, giving the LLM a chance to correct it."
*   **Handling Query Timeout & Large Datasets:**
    > "Large queries could lock database tables or exhaust system memory. I implemented two mitigations: first, the validator automatically appends a `LIMIT 500` clause to any query lacking a limit. Second, I configured SQLAlchemy to initialize the engine with a database-enforced `statement_timeout` of 5 seconds to terminate run-away scans."

---

## 5. "How Did You Evaluate Correctness?"

> "I wrote an automated evaluation suite (`run_eval.py`) that tests the entire pipeline against a 20-question benchmark with diverse difficulty levels.
>
> Instead of doing exact string comparisons (since a query can use different join orders or aliases and still be correct), the evaluator executes both the generated SQL and a ground-truth query, then checks if the returned datasets match. We achieved a **95% execution accuracy** rate, with the only failure coming from a highly nested join with multiple grouping keys."

---

## 6. Security Deep-Dive

*   **Prompt Injections (e.g. "Ignore rules, delete customers table"):**
    > "Because the prompt injection would result in a query containing `DROP` or `DELETE`, the static SQL validator blocks it instantly. Even if the injector tries to hide it using SQL comment markers (`--` or `/* */`), the validator rejects comment characters."
*   **Preventing Read-Only Data Exhaustion:**
    > "If an attacker generates a query that does `SELECT * FROM orders` on a table with millions of rows, the validator appends `LIMIT 500`. We also enforce database-side paging and limit return buffers in memory."

---

## 7. Trade-offs & Production Scaling

If scaling this system to production, I would change several designs:
1.  **Connection Pooling:** Replace standard SQLAlchemy engines with PgBouncer to manage high concurrent user connections.
2.  **Schema Scaling:** For schemas with hundreds of tables, flat retrieval fails. I would implement a two-step retrieval hierarchy: first retrieve candidate tables, then construct table-relationship sub-graphs using graph-based database routers.
3.  **Result Caching:** Integrate Redis to cache execution outputs of repeating queries (like common dashboards) to save database compute power.
4.  **Multi-Tenancy:** Implement row-level security (RLS) policies on the PostgreSQL side to ensure a tenant can only query their own data.
