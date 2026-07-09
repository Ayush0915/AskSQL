import os
import shutil
import time
import logging
import json
import uuid
from pathlib import Path
from backend.app.config import config

logger = logging.getLogger("asksql-session-manager")
logging.basicConfig(level=logging.INFO)

def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError, AttributeError):
        return False

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
    """Returns a valid Chroma collection name for this session (kept for backward compatibility)."""
    sanitized_id = "".join([c for c in session_id if c.isalnum() or c == "_"]).replace("-", "_")
    return f"schema_{sanitized_id}"[:63]

class PersistedSubDict(dict):
    def __init__(self, parent, session_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.session_id = session_id

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.parent._save_to_disk(self.session_id)

    def __delitem__(self, key):
        super().__delitem__(key)
        self.parent._save_to_disk(self.session_id)

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self.parent._save_to_disk(self.session_id)
        
    def setdefault(self, key, default=None):
        res = super().setdefault(key, default)
        self.parent._save_to_disk(self.session_id)
        return res

class SessionPersistedDict(dict):
    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename

    def _load_from_disk(self, session_id: str):
        if not super().__contains__(session_id):
            session_dir = get_session_dir(session_id)
            file_path = session_dir / self.filename
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        wrapped = PersistedSubDict(self, session_id, data)
                        super().__setitem__(session_id, wrapped)
                    else:
                        super().__setitem__(session_id, data)
                except Exception as e:
                    logger.error(f"Error loading {self.filename} for session {session_id}: {e}")

    def _save_to_disk(self, session_id: str):
        session_dir = get_session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        file_path = session_dir / self.filename
        try:
            # Load value if available
            val = super().get(session_id)
            if val is not None:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(val, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving {self.filename} for session {session_id}: {e}")

    def __getitem__(self, session_id):
        self._load_from_disk(session_id)
        return super().__getitem__(session_id)

    def get(self, session_id, default=None):
        self._load_from_disk(session_id)
        return super().get(session_id, default)

    def __setitem__(self, session_id, value):
        if isinstance(value, dict) and not isinstance(value, PersistedSubDict):
            value = PersistedSubDict(self, session_id, value)
        super().__setitem__(session_id, value)
        self._save_to_disk(session_id)

    def __contains__(self, session_id):
        self._load_from_disk(session_id)
        return super().__contains__(session_id)

    def __delitem__(self, session_id):
        if super().__contains__(session_id):
            super().__delitem__(session_id)

    def setdefault(self, session_id, default=None):
        self._load_from_disk(session_id)
        res = super().setdefault(session_id, default)
        self._save_to_disk(session_id)
        return res

# In-memory registry that auto-persists to session directories
# Structure: { session_id: { table_name: { "description": "...", "columns": {col: col_desc} } } }
session_schemas = SessionPersistedDict("schema_metadata.json")

# In-memory registry that auto-persists dynamically generated example questions per session.
# Structure: { session_id: [question1, question2, ...] }
session_questions = SessionPersistedDict("example_questions.json")

def clear_session(session_id: str):
    """Deletes the DuckDB file, clears the persisted schema files, and drops the schema cache for this session."""
    logger.info(f"Clearing session {session_id}")
    
    # 1. Clear Schema Cache & Questions
    if session_id in session_schemas:
        del session_schemas[session_id]
    if session_id in session_questions:
        del session_questions[session_id]
        
    # 2. Clear Filesystem session directory (wipes DB, JSON files, etc.)
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
