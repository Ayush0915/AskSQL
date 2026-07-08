from sqlalchemy import create_engine, text
from backend.app.config import config

class QueryExecutor:
    def __init__(self):
        # We connect using the read-only role URL.
        # We also pass connect_args to set a database-side statement timeout.
        # Options -c statement_timeout=5000 sets timeout to 5000 milliseconds (5s).
        self.engine = create_engine(
            config.DATABASE_URL,
            connect_args={
                "options": f"-c statement_timeout={config.QUERY_TIMEOUT_SECONDS * 1000}"
            }
        )

    def execute_query(self, sql: str) -> list[dict]:
        """
        Executes a SQL SELECT query against the read-only PostgreSQL role.
        Returns a list of dictionaries where keys are column names.
        Throws an Exception if the query fails or times out.
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            
            # If the query does not return rows (e.g. not a SELECT, though validator prevents this),
            # return an empty list.
            if not result.returns_rows:
                return []
                
            # Fetch all rows and convert to list of dicts
            rows = result.fetchall()
            keys = result.keys()
            
            output = []
            for row in rows:
                output.append(dict(zip(keys, row)))
                
            return output

# Quick self-test script
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
    
    executor = QueryExecutor()
    try:
        # Simple test query
        test_sql = "SELECT customer_id, customer_city FROM customers LIMIT 3"
        print(f"Executing: '{test_sql}'")
        results = executor.execute_query(test_sql)
        print("Results:")
        print(results)
        
        # Test statement timeout by executing a sleep
        print("\nTesting 5-second timeout with pg_sleep(6)...")
        executor.execute_query("SELECT pg_sleep(6)")
    except Exception as e:
        print(f"Expected failure/timeout error: {e}")
