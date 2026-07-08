import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import query
from backend.app.db.schema_metadata import schema_metadata

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

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/schema")
async def get_schema_browser():
    """
    Returns the table schemas and columns to populate the schema browser sidebar in the frontend.
    """
    formatted_schema = []
    for table_name, table_info in schema_metadata.tables.items():
        formatted_schema.append({
            "table_name": table_name,
            "description": table_info["description"],
            "columns": list(table_info["columns"])
        })
    return {"tables": formatted_schema}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
