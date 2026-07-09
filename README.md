# AskSQL ⚡

**One-liner:** AskSQL is a memory-optimized, zero-dependency, full-stack web application that translates plain-English questions (e.g., *"Show the top 3 cities with the highest number of customers"*) into execution-safe SQL queries, runs them in an isolated DuckDB sandbox, displays tabular results, and provides plain-English explanations.

---

## 📖 In-Depth System Documentation
For details on system flow sequence diagrams, AST security layer validation, evaluation benchmark results, and memory-saving optimization architecture, please refer to:
👉 **[PROJECT_OVERVIEW.md](file:///D:/project/AskSQL/PROJECT_OVERVIEW.md)**

---

## 🛠️ Tech Stack & Optimization
*   **Backend:** Python + FastAPI + Uvicorn
*   **Database Engine:** DuckDB (Session-isolated `.db` files)
*   **LLM Model:** Llama 3 (`llama-3.3-70b-versatile`) via Groq API
*   **RAG Retrieval:** Zero-dependency token-matching algorithm
*   **Frontend:** React (Vite) + Tailwind CSS (Glassmorphism design)

> [!TIP]
> **Memory Optimized:** By replacing Pandas with DuckDB's native stream parser (`read_csv_auto`), removing heavy vector databases (ChromaDB), and avoiding local embedding models, the baseline memory footprint has been reduced to only **~60MB RAM**, making it extremely fast and lightweight for free-tier deployments.

---

## 📊 Benchmark Evaluation Results

The system is evaluated against a 20-question benchmark suite spanning different difficulty levels (`simple`, `medium`, `complex`). The metrics below were captured by running the automated evaluation script (`backend/eval/run_eval.py`):

### 1. Execution Accuracy by Difficulty
| Difficulty | Total Questions | Passed | Execution Accuracy |
| :--- | :---: | :---: | :---: |
| **Simple** | 10 | 8 | 80.00% |
| **Medium** | 7 | 3 | 42.86% |
| **Complex** | 3 | 1 | 33.33% |
| **Overall** | **20** | **12** | **60.00%** |

### 2. Average Latency Breakdown
| Pipeline Stage | Avg Latency (ms) | Description |
| :--- | :---: | :--- |
| **Schema Retrieval** | 1.16 ms | Zero-dependency token-matching algorithm |
| **SQL Generation** | 990.41 ms | Prompt & SQL synthesis via Llama 3.3 (Groq API) |
| **Query Execution** | 276.74 ms | AST validation and local DB query execution |
| **Total Pipeline** | **1268.31 ms** | **End-to-end natural language to query result** |

---

## 💻 Local Setup (Without Docker)

### Prerequisites
*   **Python:** Version 3.11+
*   **Node.js:** Version 20+
*   **Groq API Key:** Get a key from the [Groq Console](https://console.groq.com/).

### 1. Backend Setup
1.  Navigate to the project root and configure the environment variables:
    ```bash
    cp .env.example .env
    ```
    Open `.env` and fill in your `GROQ_API_KEY`.
    
2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # On Windows (PowerShell):
    .\venv\Scripts\Activate.ps1
    # On Linux/macOS:
    source venv/bin/activate
    ```
    
3.  Install backend dependencies:
    ```bash
    pip install -r backend/requirements.txt
    ```

4.  Start the FastAPI backend server:
    ```bash
    uvicorn backend.app.main:app --reload --port 8000
    ```
    *   **Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Setup
1.  Navigate to the `frontend/` directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies and start the Vite dev server:
    ```bash
    npm install
    npm run dev
    ```
    *   **React App URL:** [http://localhost:3000](http://localhost:3000)

---

## ⚙️ Development Workflow

*   **Run Integration Tests:** `python backend/eval/test_upload.py` (Verify FastAPI endpoints and DuckDB creation)
*   **Run Benchmark Evaluation:** `python -m backend.eval.run_eval` (Compare generated SQL queries against a local database)

---

## 🌐 Deployment to Render (Free Tier)

### 1. Backend Web Service
*   **Runtime:** `Python`
*   **Build Command:** `pip install -r backend/requirements.txt`
*   **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
*   **Environment Variables:**
    *   `GROQ_API_KEY`: Your Groq API key (`gsk_...`)
    *   `SESSIONS_DIR`: `./backend/sessions`
*   **Plan:** Free (512MB RAM)

### 2. Frontend Static Site
*   **Build Command:** `npm run build`
*   **Publish Directory:** `dist`
*   **Environment Variables:**
    *   `VITE_API_BASE_URL`: URL of your deployed FastAPI Backend Service.
