import logging
import re
from backend.app.upload.session_manager import session_schemas

logger = logging.getLogger("asksql-retriever")
logging.basicConfig(level=logging.INFO)

class SchemaRetriever:
    def __init__(self):
        pass

    def retrieve_relevant_schemas(self, question: str, session_id: str = None, top_k: int = 4) -> str:
        """
        Retrieves top_k relevant tables for a user's question within the session's schema metadata
        using a lightweight token-matching relevance score, and returns them formatted as a single context string.
        """
        # If no session_id is provided, look for the first available session or return empty.
        # This handles eval / run_eval.py script which might not pass a session_id.
        if not session_id:
            if session_schemas:
                # Use the first active session key
                session_id = list(session_schemas.keys())[0]
                logger.info(f"No session_id provided for retrieval. Falling back to active session: {session_id}")
            else:
                return "No schema context retrieved. Please upload a dataset or load the sample data first."

        schemas = session_schemas.get(session_id, {})
        if not schemas:
            return "No schema context retrieved. Please upload a dataset or load the sample data first."

        # Compute relevance scores for each table
        scored_tables = []
        q = question.lower()
        q_tokens = set(re.findall(r'\b\w+\b', q))

        for table_name, table_info in schemas.items():
            table_desc = table_info.get("description", "")
            columns = table_info.get("columns", {})

            # Calculate keyword match score
            score = 0.0

            tb_name_lower = table_name.lower()
            if tb_name_lower in q:
                score += 15.0  # Direct match of table name
            for token in q_tokens:
                if token in tb_name_lower:
                    score += 3.0

            desc_lower = table_desc.lower()
            for token in q_tokens:
                if token in desc_lower:
                    score += 1.5

            for col_name, col_desc in columns.items():
                col_name_lower = col_name.lower()
                if col_name_lower in q:
                    score += 8.0  # Column name explicitly in user question
                for token in q_tokens:
                    if token in col_name_lower:
                        score += 2.0
                    if token in col_desc.lower():
                        score += 0.5

            scored_tables.append((score, table_name, table_desc, columns))

        # Sort tables by score descending
        scored_tables.sort(key=lambda x: x[0], reverse=True)

        # Retrieve top_k tables
        retrieved = scored_tables[:top_k]

        # Format retrieved tables as context
        formatted_context = []
        for score, table_name, table_desc, columns in retrieved:
            doc_lines = [
                f"Table Name: {table_name}",
                f"Description: {table_desc}",
                "Columns:"
            ]
            for col_name, col_desc in columns.items():
                doc_lines.append(f"  - {col_name}: {col_desc}")
            
            formatted_context.append("\n".join(doc_lines))
            formatted_context.append("-" * 40)

        return "\n".join(formatted_context)
