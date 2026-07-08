import re
import io
import logging
import duckdb
from pathlib import Path
from backend.app.upload.session_manager import get_duckdb_path, get_session_dir

logger = logging.getLogger("asksql-csv-parser")
logging.basicConfig(level=logging.INFO)

# Size Limits: 50MB per file, 200MB total per session
MAX_FILE_SIZE = 50 * 1024 * 1024
MAX_SESSION_SIZE = 200 * 1024 * 1024

def sanitize_identifier(name: str, prefix: str) -> str:
    """
    Sanitizes SQL identifiers (table names, column names) to a safe format:
    - Convert to lowercase
    - Replace non-alphanumeric characters with underscores
    - Collapse multiple underscores
    - Prepend prefix if it starts with a number or is empty
    """
    # Remove file extension if present (e.g. .csv)
    name = re.sub(r'\.[cC][sS][vV]$', '', name.strip())
    
    # Replace non-alphanumeric with underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
    # Collapse multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Trim leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure it starts with a letter/underscore and is not empty
    if not sanitized or sanitized[0].isdigit():
        sanitized = f"{prefix}_{sanitized}"
        
    return sanitized

def parse_and_load_csv(session_id: str, filename: str, file_bytes: bytes = None, file_path: Path = None) -> dict:
    """
    Parses a single CSV file, sanitizes its table and column names,
    loads it into the session's DuckDB file, and returns table metadata + preview.
    Supports loading from either raw bytes (file_bytes) or a local file path (file_path).
    """
    if file_bytes is not None:
        file_size = len(file_bytes)
    elif file_path is not None:
        file_size = file_path.stat().st_size
    else:
        raise ValueError("Either file_bytes or file_path must be provided.")

    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File '{filename}' exceeds the maximum allowed size of 50MB.")

    # 1. Sanitize Table Name
    table_name = sanitize_identifier(filename, "table")
    logger.info(f"Sanitized filename '{filename}' to table name '{table_name}'")

    session_dir = get_session_dir(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)

    temp_csv_path = None
    if file_path is not None:
        target_csv_path = file_path
    else:
        # Write bytes to a temporary CSV file
        temp_csv_path = session_dir / f"temp_{table_name}.csv"
        with open(temp_csv_path, "wb") as f:
            f.write(file_bytes)
        target_csv_path = temp_csv_path

    # 2. Insert into session DuckDB using DuckDB's native read_csv_auto
    db_path = get_duckdb_path(session_id)
    conn = None
    try:
        conn = duckdb.connect(db_path)
        
        # Read the CSV into a temporary table to inspect columns
        raw_table_name = f"{table_name}_raw"
        csv_path_str = target_csv_path.as_posix()
        conn.execute(f"CREATE OR REPLACE TABLE \"{raw_table_name}\" AS SELECT * FROM read_csv_auto('{csv_path_str}')")
        
        # Get column names
        schema_info = conn.execute(f"PRAGMA table_info('{raw_table_name}')").fetchall()
        original_cols = [row[1] for row in schema_info]
        
        # 3. Sanitize Column Names
        sanitized_cols = []
        seen = set()
        for col in original_cols:
            scol = sanitize_identifier(col, "col")
            # Ensure column names are unique (append counter if duplicate)
            base_scol = scol
            counter = 1
            while scol in seen:
                scol = f"{base_scol}_{counter}"
                counter += 1
            seen.add(scol)
            sanitized_cols.append(scol)
            
        # Create final table with sanitized column names
        select_items = [f'"{orig}" AS "{san}"' for orig, san in zip(original_cols, sanitized_cols)]
        select_clause = ", ".join(select_items)
        conn.execute(f'CREATE OR REPLACE TABLE "{table_name}" AS SELECT {select_clause} FROM "{raw_table_name}"')
        
        # Drop raw temp table
        conn.execute(f'DROP TABLE "{raw_table_name}"')
        
        # Get final column types
        final_schema_info = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        columns_and_types = {row[1]: row[2] for row in final_schema_info}
        
        # Get row count
        row_count = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
        
        # 4. Generate Preview Data (First 5 rows)
        preview_cursor = conn.execute(f'SELECT * FROM "{table_name}" LIMIT 5')
        preview_cols = [desc[0] for desc in preview_cursor.description]
        preview_rows = preview_cursor.fetchall()
        
        cleaned_preview = []
        for row in preview_rows:
            cleaned_row = {}
            for col_name, val in zip(preview_cols, row):
                if val is None:
                    cleaned_row[col_name] = None
                elif isinstance(val, float) and (val != val):  # NaN check
                    cleaned_row[col_name] = None
                elif isinstance(val, (int, float, str, bool)):
                    cleaned_row[col_name] = val
                else:
                    # Convert datetimes/dates/other types to string
                    cleaned_row[col_name] = str(val)
            cleaned_preview.append(cleaned_row)
            
    except Exception as e:
        logger.error(f"DuckDB loading error for table '{table_name}': {e}")
        raise RuntimeError(f"Database insertion failed: {str(e)}")
    finally:
        if conn is not None:
            conn.close()
        # Clean up temp CSV file if it was created
        if temp_csv_path is not None and temp_csv_path.exists():
            try:
                temp_csv_path.unlink()
            except Exception as e:
                logger.error(f"Error removing temp CSV file {temp_csv_path}: {e}")

    return {
        "table_name": table_name,
        "columns": sanitized_cols,
        "types": columns_and_types,
        "preview": cleaned_preview,
        "row_count": row_count
    }
