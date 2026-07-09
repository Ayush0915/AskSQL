import unittest
from backend.app.validator.sql_validator import SQLValidator
from backend.app.upload.session_manager import session_schemas

class TestSQLValidator(unittest.TestCase):
    def setUp(self):
        session_schemas.clear()
        self.session_id = "11111111-1111-1111-1111-111111111111"
        # Populate basic schema for testing
        session_schemas[self.session_id] = {
            "users": {
                "description": "User registry",
                "columns": {"user_id": "int", "username": "text", "age": "int"}
            },
            "orders": {
                "description": "Order records",
                "columns": {"order_id": "int", "user_id": "int", "amount": "float"}
            }
        }
        self.validator = SQLValidator()

    def tearDown(self):
        session_schemas.clear()

    def test_valid_select_query(self):
        query = "SELECT username, age FROM users WHERE age > 18"
        is_valid, reason = self.validator.validate_sql(query, self.session_id)
        self.assertTrue(is_valid, f"Failed on valid select: {reason}")

    def test_valid_cte_query(self):
        query = """
        WITH young_users AS (
            SELECT user_id, username FROM users WHERE age < 30
        )
        SELECT yu.username, o.amount
        FROM young_users yu
        JOIN orders o ON yu.user_id = o.user_id
        """
        is_valid, reason = self.validator.validate_sql(query, self.session_id)
        self.assertTrue(is_valid, f"Failed on valid CTE: {reason}")

    def test_valid_subquery(self):
        query = """
        SELECT username FROM users
        WHERE user_id IN (SELECT user_id FROM orders WHERE amount > 100)
        """
        is_valid, reason = self.validator.validate_sql(query, self.session_id)
        self.assertTrue(is_valid, f"Failed on valid subquery: {reason}")

    def test_reject_forbidden_write_operation(self):
        queries = [
            "DELETE FROM users WHERE user_id = 1",
            "UPDATE users SET age = 20 WHERE user_id = 1",
            "DROP TABLE users",
            "INSERT INTO users (user_id, username, age) VALUES (1, 'john', 25)",
            "SELECT * FROM users; DROP TABLE orders"
        ]
        for q in queries:
            is_valid, reason = self.validator.validate_sql(q, self.session_id)
            self.assertFalse(is_valid, f"Should have rejected write/stacked query: {q}")
