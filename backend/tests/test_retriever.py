import unittest
from backend.app.rag.retriever import SchemaRetriever
from backend.app.upload.session_manager import session_schemas

class TestRetriever(unittest.TestCase):
    def setUp(self):
        session_schemas.clear()

    def tearDown(self):
        session_schemas.clear()

    def test_session_with_no_schema_does_not_leak_other_session_data(self):
        # Populate session A with some schema
        session_a_id = "11111111-1111-1111-1111-111111111111"
        session_b_id = "22222222-2222-2222-2222-222222222222"
        
        session_schemas[session_a_id] = {
            "secret_table": {
                "description": "Top secret session A data",
                "columns": {"id": "int", "value": "text"}
            }
        }
        
        retriever = SchemaRetriever()
        
        # Retrieve for session B (which has no data)
        context = retriever.retrieve_relevant_schemas("show secret table", session_id=session_b_id)
        
        # Assert it does NOT contain session A's data
        self.assertNotIn("secret_table", context)
        self.assertNotIn("Top secret session A data", context)
