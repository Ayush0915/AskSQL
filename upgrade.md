# AskSQL — Fix List

Concise, file-specific changes. Ordered by priority. No UI/UX restructuring included.

---

## 🔴 Critical — fixes the actual bugs you're hitting

### 1. Remove cross-session schema fallback
**File:** `backend/app/rag/retriever.py` (lines 42–47)
**File:** `backend/app/validator/sql_validator.py` (lines 64–67)

Delete this block in both files:
```python
if not schemas:
    if session_schemas:
        fallback_session_id = list(session_schemas.keys())[0]
        schemas = session_schemas.get(fallback_session_id, {})
```
Replace with returning an explicit "no dataset for this session" result instead of borrowing another session's data. In `retriever.py`, just let it fall through to `load_default_schema()` (or return the "please upload a dataset" message directly). In `sql_validator.py`, go straight to `return False, "No dataset loaded for this session. Please upload a dataset first."`

**Why:** this is the source of the random/intermittent failures — it silently uses another user's schema when yours isn't found.

---

### 2. Stop wiping all sessions on every backend restart
**File:** `backend/app/main.py` (line ~55, `startup_event`)

Remove or replace this call:
```python
startup_cleanup()  # currently does shutil.rmtree(sessions_dir)
```
Use the existing age-based cleanup instead, which already exists in `session_manager.py`:
```python
cleanup_inactive_sessions(max_age_seconds=3600)
```
This preserves sessions that are still active across a cold start/restart instead of nuking everything.

**Why:** Render's free tier spins the backend down after ~15 min idle. Every restart currently deletes every session's DuckDB file and schema, orphaning any browser tab that still holds the old `session_id`.

---

### 3. Detect a dead/expired session on the frontend
**File:** `frontend/src/App.jsx`

On load (or on a failed `/api/query`/`/api/schema` call with a "no dataset" type error), check if the backend actually has a schema for the stored `session_id`. If not, clear `sessionStorage`/`localStorage` for that ID and prompt the user to re-upload/reload the sample dataset, instead of letting the request continue and fail deep in the pipeline.

```js
// after fetchSchema() returns empty tables
if (!schemaResult.tables || schemaResult.tables.length === 0) {
  sessionStorage.removeItem('asksql_session_id')
  localStorage.removeItem(`asksql_history_${sessionId}`)
  setIsDatasetLoaded(false)
  setErrorMsg('Your session expired — please reload your data.')
}
```

---

### 4. Raise the query timeout
**File:** `.env.example` and wherever `QUERY_TIMEOUT_SECONDS` is set in your actual Render env vars

Change:
```
QUERY_TIMEOUT_SECONDS=5
```
to something realistic for a free-tier cold instance:
```
QUERY_TIMEOUT_SECONDS=15
```

**Why:** 5s is too tight for join-heavy queries against the ~62MB sample dataset on a 512MB free instance — valid queries get killed and reported as failures.

---

## 🟠 High Priority

### 5. Generate `session_id` server-side, don't trust the client's
**Files:** `backend/app/routers/query.py`, `backend/app/main.py`, `frontend/src/App.jsx`

Right now any caller can supply any `session_id` string and read/query whatever session matches it. Have the backend issue the ID (e.g., on first `/api/upload` or `/api/sample` call, generate a UUID server-side and return it) rather than trusting a client-generated value, and validate it's a UUID format before using it to look up sessions.

### 6. Add rate limiting on LLM-backed endpoints
**File:** `backend/app/main.py`, `backend/app/routers/query.py`

Add `slowapi` (or similar) and cap `/api/query` and `/api/upload` per IP/session (e.g., 10 requests/minute). Protects your Groq API quota and prevents one abusive client from starving others.

### 7. Fix CORS configuration
**File:** `backend/app/main.py` (lines 32–38)

Replace:
```python
allow_origins=["*"],
allow_credentials=True,
```
with your actual Netlify domain:
```python
allow_origins=["https://askmysql.netlify.app"],
allow_credentials=True,
```
(`"*"` + `allow_credentials=True` is invalid per the CORS spec and browsers will reject it anyway once you rely on credentials.)

### 8. Remove unused/dead dependencies
**File:** `backend/requirements.txt`, `backend/app/config.py`

Remove `sqlalchemy`, `psycopg2-binary`, `psycopg` from `requirements.txt` — nothing in the codebase uses Postgres. Also remove the dead `DATABASE_URL` / `DATABASE_ADMIN_URL` settings in `config.py`. Cuts install time and removes confusing dead config.

---

## 🟡 Medium Priority

### 9. Add retry/backoff around Groq API calls
**File:** `backend/app/llm/sql_generator.py`, `backend/app/llm/explainer.py`

Wrap `self.client.chat.completions.create(...)` calls with a retry (e.g., `tenacity`) for transient 429/5xx errors from Groq, instead of letting one flaky call fail the whole pipeline attempt.

### 10. Remove leftover debug print
**File:** `backend/app/llm/sql_generator.py` (line 61)

Delete:
```python
print(f"DEBUG: retrieved_schema_chunks value:\n{schema_context}\n--- END DEBUG ---")
```
Leaks full schema context into server logs on every request.

### 11. Deduplicate the `describe_table` closure
**File:** `backend/app/main.py`

`/api/upload` and `/api/sample` both define an identical inner `describe_table` async function. Extract it to a shared helper (e.g., in `schema_generator.py`) and call it from both endpoints.

### 12. Add unit tests for the two files that just caused your bugs
**Files (new):** `backend/tests/test_retriever.py`, `backend/tests/test_sql_validator.py`

At minimum, cover: "session with no schema returns 'no dataset' rather than another session's data" (this test would have caught bug #1 immediately) and "validator rejects/accepts known CTE/subquery patterns correctly."

---

## 🟢 Nice to Have

### 13. Move the sample dataset out of git history
**Path:** `backend/app/data/sample_datasets`

~62MB of CSVs committed to the repo. Move to a download step on deploy/setup, or Git LFS.

---

## Suggested order of execution
1 → 2 → 4 → 3 → 5 → 7 → 6 → 8 → 9 → 10 → 11 → 12 → 13

Items 1, 2, and 4 alone should eliminate the vast majority of the intermittent failures you're seeing.