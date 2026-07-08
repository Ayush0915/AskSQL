import os
import shutil
import time
import logging
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from backend.app.config import config

logger = logging.getLogger("asksql-session-manager")
logging.basicConfig(level=logging.INFO)

# In-memory registry to cache generated schema metadata for Schema Browser sidebar queries.
# Structure: { session_id: { table_name: { "description": "...", "columns": [...] } } }
session_schemas = {}

# In-memory registry to cache dynamically generated example questions per session.
# Structure: { session_id: [question1, question2, ...] }
session_questions = {}

def get_session_dir(session_id: str) -> Path:
    """Returns the absolute path to the session subdirectory."""
    # Sanitize session_id to ensure it's alphanumeric/hyphens/underscores only
    sanitized_id = "".join([c for c in session_id if c.isalnum() or c in ("-", "_")])
    return Path(config.SESSIONS_DIR) / sanitized_id

def get_duckdb_path(session_id: str) -> str:
    """Returns the path to the DuckDB database file for this session."""
    session_dir = get_session_dir(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    return str(session_dir / "asksql.db")

def get_chroma_collection_name(session_id: str) -> str:
    """Returns a valid Chroma collection name for this session."""
    # Chroma collection names must be 3-63 chars, start/end with alphanumeric, and use only alphanumeric/hyphens/underscores.
    sanitized_id = "".join([c for c in session_id if c.isalnum() or c == "_"]).replace("-", "_")
    return f"schema_{sanitized_id}"[:63]

def clear_session(session_id: str):
    """Deletes the DuckDB file, clears the Chroma collection, and drops the schema cache for this session."""
    logger.info(f"Clearing session {session_id}")
    
    # 1. Clear Schema Cache & Questions
    if session_id in session_schemas:
        del session_schemas[session_id]
    if session_id in session_questions:
        del session_questions[session_id]
        
    # 2. Clear Chroma collection
    try:
        client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
        coll_name = get_chroma_collection_name(session_id)
        # Attempt to delete collection if it exists
        try:
            client.delete_collection(name=coll_name)
            logger.info(f"Deleted Chroma collection: {coll_name}")
        except Exception:
            # Collection may not exist yet, which is fine
            pass
    except Exception as e:
        logger.error(f"Error deleting Chroma collection for session {session_id}: {e}")

    # 3. Clear Filesystem session directory
    session_dir = get_session_dir(session_id)
    if session_dir.exists():
        try:
            shutil.rmtree(session_dir)
            logger.info(f"Deleted session directory: {session_dir}")
        except Exception as e:
            logger.error(f"Error removing session directory {session_dir}: {e}")

def cleanup_inactive_sessions(max_age_seconds: int = 3600):
    """
    Wipes sessions inactive for longer than max_age_seconds (default 1 hour).
    Scans the filesystem directories and checks their last modification time.
    """
    sessions_dir = Path(config.SESSIONS_DIR)
    if not sessions_dir.exists():
        return
        
    now = time.time()
    logger.info("Running inactive session cleanup scanner...")
    
    for item in sessions_dir.iterdir():
        if item.is_dir():
            try:
                # Check modification time of the session folder
                mtime = item.stat().st_mtime
                age = now - mtime
                if age > max_age_seconds:
                    session_id = item.name
                    logger.info(f"Session {session_id} is inactive (age: {int(age)}s > {max_age_seconds}s). Purging.")
                    clear_session(session_id)
            except Exception as e:
                logger.error(f"Error cleaning up inactive session folder {item}: {e}")

def startup_cleanup():
    """Wipes all session files on startup to ensure a clean slate."""
    sessions_dir = Path(config.SESSIONS_DIR)
    if sessions_dir.exists():
        logger.info(f"Wiping sessions directory on startup: {sessions_dir}")
        try:
            shutil.rmtree(sessions_dir)
            sessions_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Startup sessions directory wipe completed.")
        except Exception as e:
            logger.error(f"Error cleaning sessions directory on startup: {e}")
    else:
        sessions_dir.mkdir(parents=True, exist_ok=True)
