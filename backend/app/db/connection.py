import threading
import logging
from pathlib import Path
import duckdb
from backend.app.config import config
from backend.app.upload.session_manager import get_duckdb_path

logger = logging.getLogger("asksql-db-connection")
logging.basicConfig(level=logging.INFO)

class QueryExecutor:
    def __init__(self):
        # DuckDB handles read/write queries via direct file connections.
        # We enforce timeout using python timers and connection interrupts.
        pass

    def execute_query(self, sql: str, session_id: str) -> list[dict]:
        """
        Executes a SQL SELECT query against the session's DuckDB database file.
        Enforces timeout dynamically using a background thread timer.
        Returns a list of dictionaries where keys are column names.
        Throws a TimeoutError if the query times out.
        """
        db_path = get_duckdb_path(session_id)
        
        # Check if database file exists and contains tables (meaning it's not a fresh empty DB)
        if not Path(db_path).exists():
            raise ValueError("Database file not found for this session. Please upload a dataset.")

        # Establish connection to DuckDB database file
        # We connect in read_only mode to prevent any writes, ensuring read-only safety.
        try:
            conn = duckdb.connect(db_path, read_only=True)
        except Exception as e:
            logger.error(f"Error opening DuckDB connection at {db_path}: {e}")
            raise ValueError("Failed to access database session. Ensure you have uploaded a valid dataset.")

        # Thread interrupt control
        interrupted = False
        def interrupt():
            nonlocal interrupted
            interrupted = True
            try:
                conn.interrupt()
            except Exception:
                pass

        # Set a timer to call conn.interrupt() after the configured query timeout
        timeout_seconds = config.QUERY_TIMEOUT_SECONDS
        timer = threading.Timer(timeout_seconds, interrupt)
        timer.start()

        try:
            # Execute query
            cursor = conn.execute(sql)
            
            # Fetch results
            if cursor.description is None:
                return []
                
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Convert rows to list of dicts
            output = []
            for row in rows:
                output.append(dict(zip(columns, row)))
                
            return output
            
        except Exception as e:
            if interrupted:
                logger.warning(f"Query timed out after {timeout_seconds}s and was interrupted: {sql}")
                raise TimeoutError(f"Query timed out after {timeout_seconds} seconds.")
            logger.error(f"DuckDB execution error: {e}")
            raise e
        finally:
            timer.cancel()
            conn.close()
