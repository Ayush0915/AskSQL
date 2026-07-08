import os
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from root of project or backend directory
# Look at root first, then current file parent
root_dir = Path(__file__).resolve().parent.parent.parent
dotenv_path = root_dir / ".env"
if not dotenv_path.exists():
    dotenv_path = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(dotenv_path=dotenv_path)

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    
    # Database settings - connect using the read-only user by default for the app
    # E.g. postgresql://asksql_readonly:readonly_password@localhost:5432/asksql
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql://asksql_readonly:readonly_password@localhost:5432/asksql"
    )
    
    # Default superuser URL for seeding/eval setup if needed
    DATABASE_ADMIN_URL = os.getenv(
        "DATABASE_ADMIN_URL",
        "postgresql://postgres@localhost:5432/asksql"
    )
    
    # ChromaDB persist directory (resolved to absolute path relative to project root if relative)
    _raw_chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./backend/data/chroma")
    CHROMA_PERSIST_DIR = str(
        (root_dir / _raw_chroma_dir).resolve() if not os.path.isabs(_raw_chroma_dir) 
        else Path(_raw_chroma_dir)
    )

    
    # Port configuration
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))
    FRONTEND_API_BASE_URL = os.getenv("FRONTEND_API_BASE_URL", "http://localhost:8000")
    
    # Query enforcement
    QUERY_TIMEOUT_SECONDS = int(os.getenv("QUERY_TIMEOUT_SECONDS", 5))
    QUERY_ROW_LIMIT = int(os.getenv("QUERY_ROW_LIMIT", 500))

config = Config()
