import re
import sqlparse
from sql_metadata import Parser
from backend.app.db.schema_metadata import schema_metadata

class SQLValidator:
    def __init__(self):
        # Compiled regex to match restricted SQL keywords as whole words
        self.forbidden_pattern = re.compile(
            r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|GRANT|REVOKE|CREATE)\b",
            re.IGNORECASE
        )
        # Limit pattern to see if query already has a LIMIT clause
        self.limit_pattern = re.compile(r"\bLIMIT\s+\d+\b", re.IGNORECASE)

    def validate_sql(self, sql: str) -> tuple[bool, str | None]:
        """
        Validates the SQL query against security and schema constraints.
        Returns (is_valid, error_reason).
        """
        if not sql:
            return False, "Query is empty."

        cleaned_sql = sql.strip()

        # Rule 1: Check for SQL comments
        if "--" in cleaned_sql or "/*" in cleaned_sql or "*/" in cleaned_sql:
            return False, "Query contains SQL comment markers (--, /* */) which are forbidden."

        # Rule 2: Case-insensitive check to ensure the query starts with SELECT
        # We also want to make sure it doesn't start with multiple statements
        if not cleaned_sql.upper().startswith("SELECT"):
            return False, "Query must be a read-only SELECT statement."

        # Rule 3: Check for stacked statements / multiple statements
        # A semicolon followed by non-whitespace is an indicator of stacked statements
        if ";" in cleaned_sql:
            # If the semicolon is not at the very end of the query, it is forbidden
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

        # Rule 5: Schema validation (tables and columns)
        try:
            parser = Parser(cleaned_sql)
            
            # Extract tables referenced in query
            referenced_tables = parser.tables
            if not referenced_tables:
                # E.g. SELECT 1 or SELECT NOW() is fine, but we expect queries to query tables
                return True, None

            valid_tables = schema_metadata.get_valid_tables()
            
            # Verify tables exist in metadata
            for table in referenced_tables:
                if table not in valid_tables:
                    return False, f"Table '{table}' is not present in the database schema."

            # Verify columns exist in metadata
            # Columns in parser.columns can be fully qualified (table.col) or simple (col)
            referenced_columns = parser.columns
            for col in referenced_columns:
                if col == "*":
                    continue
                    
                # Split fully qualified columns (e.g. "orders.order_id" -> table="orders", name="order_id")
                if "." in col:
                    parts = col.split(".", 1)
                    table_prefix = parts[0]
                    col_name = parts[1]
                    
                    if table_prefix in referenced_tables:
                        if not schema_metadata.is_valid_column(table_prefix, col_name):
                            return False, f"Column '{col_name}' does not exist on table '{table_prefix}'."
                    else:
                        # Table prefix used but table is not in referenced tables list
                        return False, f"Table prefix '{table_prefix}' in column '{col}' is not referenced in the query."
                else:
                    # Simple column name, check if it exists in AT LEAST one of the referenced tables
                    found = False
                    for table in referenced_tables:
                        if schema_metadata.is_valid_column(table, col):
                            found = True
                            break
                    if not found:
                        return False, f"Column '{col}' does not exist in any of the referenced tables: {referenced_tables}."

        except Exception as e:
            # If parsing fails, reject query out of safety
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

# Unit tests/Self-test
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
    
    validator = SQLValidator()
    
    # Test cases
    test_queries = [
        ("SELECT * FROM customers LIMIT 10", True),
        ("SELECT customer_id, customer_city FROM customers", True),
        ("SELECT customer_id, invalid_col FROM customers", False),  # Invalid column
        ("SELECT * FROM invalid_table", False),                    # Invalid table
        ("SELECT * FROM customers; DROP TABLE customers;", False), # Stacked
        ("SELECT * FROM customers -- comment", False),             # Comment
        ("INSERT INTO customers (customer_id) VALUES ('1')", False), # Insert
        ("SELECT COUNT(*) FROM orders", True),
        ("SELECT orders.order_id, customers.customer_city FROM orders JOIN customers ON orders.customer_id = customers.customer_id", True)
    ]
    
    print("Running SQL Validator Self-Tests...")
    for idx, (query, expected) in enumerate(test_queries):
        is_valid, reason = validator.validate_sql(query)
        result = "PASS" if is_valid == expected else "FAIL"
        print(f"[{result}] Test {idx+1}: '{query}' -> Valid: {is_valid} (Reason: {reason})")
