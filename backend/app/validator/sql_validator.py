import re
import sqlparse
from sql_metadata import Parser
from backend.app.upload.session_manager import session_schemas

class SQLValidator:
    def __init__(self):
        # Compiled regex to match restricted SQL keywords as whole words
        self.forbidden_pattern = re.compile(
            r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|GRANT|REVOKE|CREATE)\b",
            re.IGNORECASE
        )
        # Limit pattern to see if query already has a LIMIT clause
        self.limit_pattern = re.compile(r"\bLIMIT\s+\d+\b", re.IGNORECASE)

    def validate_sql(self, sql: str, session_id: str) -> tuple[bool, str | None]:
        """
        Validates the SQL query against security constraints and the session's schema metadata.
        Returns (is_valid, error_reason).
        """
        if not sql:
            return False, "Query is empty."

        cleaned_sql = sql.strip()

        # Rule 1: Check for SQL comments
        if "--" in cleaned_sql or "/*" in cleaned_sql or "*/" in cleaned_sql:
            return False, "Query contains SQL comment markers (--, /* */) which are forbidden."

        # Rule 2: Case-insensitive check to ensure the query starts with SELECT
        if not cleaned_sql.upper().startswith("SELECT"):
            return False, "Query must be a read-only SELECT statement."

        # Rule 3: Check for stacked statements / multiple statements
        if ";" in cleaned_sql:
            semicolon_index = cleaned_sql.find(";")
            if semicolon_index != -1 and semicolon_index < len(cleaned_sql) - 1:
                remainder = cleaned_sql[semicolon_index + 1:].strip()
                if remainder:
                    return False, "Multiple stacked SQL statements are forbidden."

        # Double check with sqlparse
        parsed = sqlparse.parse(cleaned_sql)
        if len(parsed) > 1:
            return False, "Multiple SQL statements detected."

        # Rule 4: Check for forbidden write/administrative keywords
        if self.forbidden_pattern.search(cleaned_sql):
            forbidden_matches = self.forbidden_pattern.findall(cleaned_sql)
            return False, f"Query contains forbidden write/administrative keywords: {', '.join(set(forbidden_matches))}."

        # Rule 5: Schema validation against session-scoped metadata
        try:
            parser = Parser(cleaned_sql)
            referenced_tables = parser.tables
            if not referenced_tables:
                return True, None

            # Get session schema
            schemas = session_schemas.get(session_id, {})
            if not schemas:
                return False, "No dataset loaded for this session. Please upload a dataset first."

            valid_tables = set(schemas.keys())
            
            # Verify tables exist in metadata
            for table in referenced_tables:
                # Strip optional quotes if present
                clean_table = table.strip('"').strip('`').strip("'")
                if clean_table not in valid_tables:
                    return False, f"Table '{clean_table}' is not present in the database schema."

            # Verify columns exist in metadata
            referenced_columns = parser.columns
            for col in referenced_columns:
                if col == "*":
                    continue
                
                # Strip optional quotes
                clean_col = col.strip('"').strip('`').strip("'")
                
                # Split fully qualified columns (e.g. "orders.order_id")
                if "." in clean_col:
                    parts = clean_col.split(".", 1)
                    table_prefix = parts[0].strip('"').strip('`').strip("'")
                    col_name = parts[1].strip('"').strip('`').strip("'")
                    
                    if table_prefix in referenced_tables:
                        # Validate col_name on table_prefix
                        table_cols = schemas.get(table_prefix, {}).get("columns", {})
                        if col_name not in table_cols:
                            return False, f"Column '{col_name}' does not exist on table '{table_prefix}'."
                    else:
                        return False, f"Table prefix '{table_prefix}' in column '{col}' is not referenced in the query."
                else:
                    # Simple column name, check if it exists in AT LEAST one of the referenced tables
                    found = False
                    for table in referenced_tables:
                        clean_table = table.strip('"').strip('`').strip("'")
                        table_cols = schemas.get(clean_table, {}).get("columns", {})
                        if clean_col in table_cols:
                            found = True
                            break
                    if not found:
                        return False, f"Column '{clean_col}' does not exist in any of the referenced tables: {referenced_tables}."

        except Exception as e:
            return False, f"SQL parsing/schema validation failed: {str(e)}"

        return True, None

    def enforce_limit(self, sql: str, default_limit: int = 500) -> str:
        """
        Auto-appends LIMIT clause if not already present.
        """
        cleaned = sql.strip().rstrip(";")
        if not self.limit_pattern.search(cleaned):
            return f"{cleaned} LIMIT {default_limit}"
        return cleaned
