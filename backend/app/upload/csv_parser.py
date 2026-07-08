import re
import io
import logging
import pandas as pd
import duckdb
from pathlib import Path
from backend.app.upload.session_manager import get_duckdb_path

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

def parse_and_load_csv(session_id: str, filename: str, file_bytes: bytes) -> dict:
    """
    Parses a single CSV file, sanitizes its table and column names,
    loads it into the session's DuckDB file, and returns table metadata + preview.
    """
    file_size = len(file_bytes)
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File '{filename}' exceeds the maximum allowed size of 50MB.")

    # 1. Sanitize Table Name
    table_name = sanitize_identifier(filename, "table")
    logger.info(f"Sanitized filename '{filename}' to table name '{table_name}'")

    # 2. Parse CSV using Pandas
    try:
        # Load into DataFrame
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        logger.error(f"Error parsing CSV file '{filename}': {e}")
        raise ValueError(f"Failed to parse CSV file '{filename}'. Ensure it is a valid, well-formed CSV. Error: {str(e)}")

    # 3. Sanitize Column Names
    original_cols = df.columns.tolist()
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
        
    df.columns = sanitized_cols
    logger.info(f"Sanitized columns for table '{table_name}'")

    # 4. Insert into session DuckDB
    db_path = get_duckdb_path(session_id)
    try:
        conn = duckdb.connect(db_path)
        # Register Pandas DataFrame as a temporary view in DuckDB
        conn.register("temp_df", df)
        # Create or replace table
        conn.execute(f'CREATE OR REPLACE TABLE "{table_name}" AS SELECT * FROM temp_df')
        
        # Get column types from DuckDB's schema representation
        schema_info = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        # Schema info rows format: (cid, name, type, notnull, dflt_value, pk)
        columns_and_types = {row[1]: row[2] for row in schema_info}
        conn.close()
    except Exception as e:
        logger.error(f"DuckDB loading error for table '{table_name}': {e}")
        raise RuntimeError(f"Database insertion failed: {str(e)}")

    # 5. Generate Preview Data (First 5 rows)
    preview_rows = df.head(5).to_dict(orient="records")
    # Convert non-JSON-serializable types (like timestamps or pandas NaNs) to strings/None
    cleaned_preview = []
    for row in preview_rows:
        cleaned_row = {}
        for k, v in row.items():
            if pd.isna(v):
                cleaned_row[k] = None
            elif isinstance(v, (pd.Timestamp, pd.Timedelta)):
                cleaned_row[k] = str(v)
            else:
                cleaned_row[k] = v
        cleaned_preview.append(cleaned_row)

    return {
        "table_name": table_name,
        "columns": sanitized_cols,
        "types": columns_and_types,
        "preview": cleaned_preview,
        "row_count": len(df)
    }
