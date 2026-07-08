# AskSQL — Upload-Your-Own-Dataset Addendum

> **Purpose:** This document supersedes Section 4 (Dataset) of the original AskSQL build spec. AskSQL no longer ships with a fixed pre-loaded e-commerce database — instead, the user uploads their own dataset (CSV files) via the sidebar, the app infers a schema, generates schema descriptions, and the existing NL→SQL pipeline runs against that uploaded data. Everything else in the original spec (prompts, validator, safety rules, RAG retrieval pattern) stays the same — only the data source changes, from "one fixed Postgres database" to "whatever the user just uploaded."

**Assumption made (no strong preference given):** isolation uses a **per-session DuckDB file**, not dynamic tables in a shared Postgres instance. Reasoning: DuckDB is embedded (no separate server), reads CSVs natively and fast, and — critically — keeps each user's uploaded data in its own throwaway file rather than mixing untrusted user data into a shared, persistent database. If this turns out to feel limiting later, migrating to per-session Postgres schemas is a reasonable next step, but DuckDB is the right starting point for a solo 2-4 week build.

---

## 1. New User Flow

1. User opens AskSQL. Sidebar shows an **"Upload Dataset"** panel instead of a pre-built Schema Browser.
2. User uploads one or more CSV files (drag-and-drop or file picker).
3. Backend:
   - Parses each CSV, infers column types (text, integer, float, date/timestamp, boolean)
   - Creates a table per CSV in a new, session-scoped DuckDB file
   - Generates schema descriptions for each table/column (see Section 4)
   - Embeds these descriptions into a **session-scoped** ChromaDB collection (not the old global one)
4. Schema Browser sidebar now populates dynamically from the uploaded files' inferred schema (table names, column names/types, generated descriptions) — same UI pattern as before, just built from upload instead of a fixed dataset.
5. From here, the existing flow is unchanged: user asks a question → retrieval → SQL generation → validation → execution against the session's DuckDB file → explanation → results.
6. When the session ends (browser closed, explicit "Clear Dataset" action, or a timeout), the DuckDB file and its ChromaDB collection are deleted.

---

## 2. Architecture Changes

```
┌─────────────┐         ┌──────────────────────────────────────────────┐
│  React UI   │────────▶│                FastAPI Backend                 │
│             │         │                                                │
│ + Upload    │         │  0. Upload Handler (NEW)                      │
│   panel     │◀────────│     - validates file type/size                │
└─────────────┘         │     - infers column types per CSV              │
                         │     - creates session DuckDB + tables          │
                         │     - generates schema descriptions (LLM)      │
                         │     - embeds into session-scoped ChromaDB       │
                         │                                                │
                         │  1. Schema Retriever (per-session Chroma)      │
                         │  2. SQL Generator (Groq/Llama 3)               │
                         │  3. SQL Validator (Section 5 — expanded)        │
                         │  4. Query Executor (session DuckDB file)        │
                         │  5. Explainer (Groq/Llama 3)                   │
                         └──────────────┬─────────────────────────────────┘
                                        ▼
                          ┌─────────────────────────────┐
                          │ Session DuckDB file           │
                          │ (one per browser session,     │
                          │  deleted on session end)       │
                          └─────────────────────────────┘
```

**Session identity:** generate a `session_id` (UUID) on first load, stored in a cookie or returned to the frontend and sent with every request. Backend maps `session_id → duckdb_file_path` and `session_id → chroma_collection_name`. Store this mapping in a simple in-memory dict for a solo project (Redis would be the production answer, but is overkill here).

---

## 3. Upload Handling — Requirements

- **Accepted formats:** CSV only for v1 (Excel/JSON support is a stretch goal, not required)
- **Size limit:** cap uploads at a reasonable size (e.g., 50MB per file, 200MB per session total) to keep DuckDB fast and avoid abuse — reject with a clear error above this
- **Multiple files = multiple tables:** each uploaded CSV becomes one table, named after the (sanitized) filename
- **Filename/column sanitization (important, see Section 5):** strip anything that isn't alphanumeric/underscore from filenames and column headers before using them as SQL identifiers — untrusted filenames/headers must never be interpolated into SQL unsanitized
- **Type inference:** sample the first ~1000 rows of each column to guess type (int, float, date, boolean, text) — libraries like `pandas` (`pd.read_csv` + `infer_objects`) or DuckDB's own CSV auto-detection (`read_csv_auto`) can do this directly, which is simpler than hand-rolling inference
- **Preview before commit:** show the user a quick preview (first 5 rows + inferred types per column) with an option to fix a misdetected type before finalizing — nice UX touch, not strictly required for v1 if time is tight

---

## 4. Schema Description Generation (Replaces the Hand-Written `schema_descriptions.json`)

Since there's no fixed dataset anymore, schema descriptions can't be hand-written in advance — they must be generated automatically per upload.

**Approach:** for each table, send the LLM a compact prompt with the table name, column names/types, and a few sample rows, and ask it to write a one-line description per table and per column (mirrors the human-written style from the original spec, just LLM-generated instead of hand-written).

**Prompt template:**
```
You are documenting a database table for someone building SQL queries against it.
Given the table name, column names with inferred types, and a few sample rows,
write a JSON object with:
- a one-sentence description of what this table represents
- a one-sentence description for each column (what it contains, and if it's an
  enum-like column, mention the range of values you see in the samples)

Respond with ONLY valid JSON, no other text. Format:
{"table_description": "...", "columns": {"column_name": "description", ...}}

Table name: {table_name}
Columns and types: {column_list}
Sample rows: {sample_rows}
```

This runs once per uploaded table at upload time (not per query), so latency here doesn't affect query-time responsiveness. Cache the result for the session so re-asking questions doesn't regenerate descriptions.

---

## 5. Safety / Validation — What Changes and What Gets Stricter

The original validator rules (Section 8 of the main build spec — block non-SELECT, block comments, block unknown tables/columns, row limit, timeout) all still apply and matter even more now, since the schema itself is user-controlled, not a curated dataset you built yourself.

**Additional rules needed for the upload flow specifically:**
- **Identifier sanitization at upload time:** table names (from filenames) and column names (from CSV headers) must be sanitized to a safe character set (`[a-zA-Z0-9_]`, must not start with a digit) *before* they're ever used in a `CREATE TABLE` statement. This is a different attack surface than the original spec covered — there, table/column names came from a dataset you controlled; here, they come from a file someone else could hand-craft.
- **No user-supplied SQL, ever** — uploads are data only (CSV rows), never executable — this should already be true structurally (you're reading CSV values into DuckDB via a library, not executing user text as SQL), but worth stating explicitly as a design invariant.
- **Session isolation is itself a safety control** — one session's DuckDB file must never be queryable by a different session's `session_id`. Double-check this mapping can't be guessed/spoofed (use a properly random UUID, not a sequential ID).
- Keep the row limit and query timeout from the original spec — arguably more important now, since upload size (and therefore query cost) is unpredictable.

---

## 6. What Gets Removed From the Original Spec

- The hand-written `schema_descriptions.json` file and its embedding step — replaced by Section 4's dynamic generation
- The fixed Kaggle e-commerce dataset and its Postgres seed-loading step
- The dedicated `asksql_readonly` Postgres role setup — no longer needed if DuckDB is the query engine (DuckDB sessions are inherently isolated per-file, so there's no "read-only role" concept in the same way; the safety net instead comes from the validator + session isolation)
- The eval benchmark's fixed 20-30 question set **must be adapted**: since there's no fixed dataset anymore, the eval script should ship with one pre-packaged sample CSV set (e.g., keep the Olist e-commerce data as a *bundled example dataset* users can optionally load with one click, purely so the eval benchmark and demo videos still have a consistent, repeatable dataset to test against) — this is different from the app defaulting to it; it's just there as a convenient example a user can pick from an "upload" screen instead of dragging their own file in, for demo purposes.

---

## 7. UI Changes

- Replace the static Schema Browser's "8 tables" hardcoded feel with a dynamic version that starts empty and populates after upload
- Add an "Upload Dataset" panel/dropzone where the Schema Browser currently sits before any upload has happened — clear call to action ("Drag CSV files here or click to browse")
- Add a small "Try our sample dataset" link/button next to the upload zone that loads the bundled example CSVs (Section 6) with one click — gives first-time visitors/recruiters something to try immediately without needing their own file
- Add a "Clear Dataset" / "Start Over" action so a user can drop their current upload and start fresh
- Loading state during upload processing (type inference + LLM schema description generation can take a few seconds — show a clear progress indicator, not a frozen UI)
- Error states: file too large, unsupported format, parsing failure (e.g., malformed CSV) — show a clear, specific message for each

---

## 8. File Structure Changes (Additions to the Original Spec)

```
backend/
├── app/
│   ├── upload/
│   │   ├── csv_parser.py          # type inference, sanitization
│   │   ├── session_manager.py     # session_id ↔ duckdb file / chroma collection mapping
│   │   └── schema_generator.py    # LLM-based schema description generation (Section 4)
│   ├── db/
│   │   └── duckdb_connection.py   # replaces the old Postgres read-only connection.py
│   ├── data/
│   │   └── sample_datasets/       # bundled example CSVs (e.g., Olist tables) for the "Try sample dataset" button
├── sessions/                       # gitignored — runtime-created DuckDB files live here
```

Remove: `backend/data/schema_descriptions.json` (static file), `backend/data/seed_data/` (old Postgres seeding), the Postgres-role creation script.

---

## 9. Open Questions — **[ASK FIRST]**

1. Session expiry policy: clear on browser close (simplest, use `sessionStorage`-style cookie lifetime), or a timeout (e.g., 1 hour of inactivity) with a background cleanup job for abandoned DuckDB files? A timeout is more correct but adds a cleanup task; browser-close-only is simpler and fine for a portfolio project.
2. Should the bundled sample dataset (Section 6) be the Olist e-commerce set from the original spec, or something else — keeping Olist means your existing eval question bank (Section 9 of the main spec) still works unmodified against it.
3. Multi-file uploads with relationships (e.g., `orders.csv` + `customers.csv` that should join on `customer_id`) — should the app attempt to auto-detect likely join keys between uploaded tables (nice for retrieval quality), or leave that entirely to the LLM's judgment at query time without any hinting? Auto-detection improves accuracy but is extra work.

---

*End of addendum. This replaces Section 4 (Dataset) and modifies Sections 7-9 of the original AskSQL build spec — implement as one connected change, not a phased rollout.*
