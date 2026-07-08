import os
import asyncio
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import query
from backend.app.upload.session_manager import (
    session_schemas,
    session_questions,
    clear_session,
    cleanup_inactive_sessions,
    startup_cleanup
)
from backend.app.upload.csv_parser import parse_and_load_csv
from backend.app.upload.schema_generator import (
    generate_schema_descriptions_llm,
    embed_session_table_schema,
    generate_example_questions_llm
)
from pathlib import Path

logger = logging.getLogger("asksql-main")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AskSQL API",
    description="Natural Language to SQL pipeline with schema-aware RAG, safety validation, and plain English explanation.",
    version="1.0.0"
)

# Add CORS middleware to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include query router
app.include_router(query.router, prefix="/api")

# Repeated background cleanup loop
async def session_cleanup_loop():
    while True:
        try:
            cleanup_inactive_sessions(max_age_seconds=3600)
        except Exception as e:
            logger.error(f"Error in inactive session cleanup loop: {e}")
        await asyncio.sleep(600)  # Sleep for 10 minutes

@app.on_event("startup")
async def startup_event():
    # 1. Clean leftover session files
    startup_cleanup()
    # 2. Start session cleanup daemon task
    asyncio.create_task(session_cleanup_loop())

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/schema")
async def get_schema_browser(session_id: str):
    """
    Returns the table schemas, columns, and custom sample questions to populate the UI for this session.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")
        
    formatted_schema = []
    schemas = session_schemas.get(session_id, {})
    
    for table_name, table_info in schemas.items():
        formatted_schema.append({
            "table_name": table_name,
            "description": table_info["description"],
            "columns": list(table_info["columns"].keys())
        })
        
    # Retrieve or generate custom business questions for this database layout
    questions = session_questions.get(session_id, [])
    if formatted_schema and not questions:
        questions = await generate_example_questions_llm(session_id)
        
    return {
        "tables": formatted_schema,
        "example_questions": questions
    }

@app.post("/api/upload")
async def upload_dataset(session_id: str = Form(...), files: list[UploadFile] = File(...)):
    """
    Handles CSV uploads, sanitizes table/column names, infers column data types,
    loads the data into the session's DuckDB file, generates schema descriptions,
    and indexes them in the session's ChromaDB collection.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    processed_tables = []
    total_size = 0

    # 1. Read files and check overall session size limit (200MB)
    file_payloads = []
    for file in files:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail=f"Unsupported file format for '{file.filename}'. Only CSV files are accepted.")
        
        content = await file.read()
        total_size += len(content)
        if total_size > 200 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Total uploaded dataset size exceeds session limit of 200MB.")
        file_payloads.append((file.filename, content))

    # 2. Parse, load, and generate schemas
    tables_to_describe = []
    for filename, content in file_payloads:
        try:
            # Step 2a: Parse CSV, infer types, and load into DuckDB (done sequentially to avoid DB locks)
            load_data = parse_and_load_csv(session_id, filename, content)
            
            tables_to_describe.append({
                "table_name": load_data["table_name"],
                "columns_and_types": load_data["types"],
                "preview": load_data["preview"]
            })
            
            processed_tables.append({
                "table_name": load_data["table_name"],
                "row_count": load_data["row_count"],
                "columns": load_data["columns"]
            })
        except Exception as e:
            logger.error(f"Error processing file '{filename}': {e}")
            raise HTTPException(status_code=500, detail=f"Error processing file '{filename}': {str(e)}")

    # Step 2b: Generate table/column descriptions using Llama 3 concurrently
    async def describe_table(table):
        try:
            desc_data = await generate_schema_descriptions_llm(
                session_id=session_id,
                table_name=table["table_name"],
                columns_and_types=table["columns_and_types"],
                sample_rows=table["preview"]
            )
            embed_session_table_schema(
                session_id=session_id,
                table_name=table["table_name"],
                table_desc=desc_data["table_description"],
                columns_desc=desc_data["columns"]
            )
        except Exception as e:
            logger.error(f"Error generating descriptions for '{table['table_name']}': {e}")

    if tables_to_describe:
        await asyncio.gather(*(describe_table(t) for t in tables_to_describe))

    # Generate custom sample business questions for this newly uploaded dataset
    questions = await generate_example_questions_llm(session_id)
    return {"status": "success", "tables": processed_tables, "example_questions": questions}

@app.post("/api/clear")
async def clear_dataset(payload: dict):
    """
    Clears the session dataset (deletes DuckDB file, wipes ChromaDB, and drops memory cache).
    """
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")
        
    clear_session(session_id)
    return {"status": "success"}

@app.post("/api/sample")
async def load_sample_dataset(payload: dict):
    """
    Mounts the pre-packaged Olist e-commerce sample CSV dataset into the user's session.
    """
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")

    # Locate pre-packaged datasets directory
    sample_dir = Path(__file__).resolve().parent / "data" / "sample_datasets"
    if not sample_dir.exists():
        raise HTTPException(status_code=500, detail="Pre-packaged sample dataset files not found on server.")

    processed_tables = []
    
    # List of expected Olist tables
    sample_files = list(sample_dir.glob("*.csv"))
    if not sample_files:
        raise HTTPException(status_code=500, detail="No CSV files found in the sample datasets folder.")

    logger.info(f"Loading {len(sample_files)} sample CSV files for session {session_id}...")

    # Load all sample CSVs
    tables_to_describe = []
    for file_path in sample_files:
        filename = file_path.name
        try:
            # Parse CSV and load into DuckDB directly from file path (done sequentially to avoid DB locks)
            load_data = parse_and_load_csv(session_id, filename, file_path=file_path)
            
            tables_to_describe.append({
                "table_name": load_data["table_name"],
                "columns_and_types": load_data["types"],
                "preview": load_data["preview"]
            })
            
            processed_tables.append({
                "table_name": load_data["table_name"],
                "row_count": load_data["row_count"],
                "columns": load_data["columns"]
            })
        except Exception as e:
            logger.error(f"Error loading sample file '{filename}': {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load sample file '{filename}': {str(e)}")

    # Generate table/column descriptions using Llama 3 concurrently
    async def describe_table(table):
        try:
            desc_data = await generate_schema_descriptions_llm(
                session_id=session_id,
                table_name=table["table_name"],
                columns_and_types=table["columns_and_types"],
                sample_rows=table["preview"]
            )
            embed_session_table_schema(
                session_id=session_id,
                table_name=table["table_name"],
                table_desc=desc_data["table_description"],
                columns_desc=desc_data["columns"]
            )
        except Exception as e:
            logger.error(f"Error generating sample descriptions for '{table['table_name']}': {e}")

    if tables_to_describe:
        await asyncio.gather(*(describe_table(t) for t in tables_to_describe))

    # Generate custom sample business questions for this sample dataset
    questions = await generate_example_questions_llm(session_id)
    return {"status": "success", "tables": processed_tables, "example_questions": questions}
