import re
from groq import Groq
from backend.app.config import config

class SQLGenerator:
    def __init__(self):
        # The Groq client automatically uses GROQ_API_KEY from environment or config
        api_key = config.GROQ_API_KEY
        if api_key:
            self.client = Groq(api_key=api_key)
        else:
            self.client = Groq()  # Fallback to system env
            
        # Use the latest active llama model from our list
        self.model = "llama-3.3-70b-versatile"

    def clean_llm_sql(self, raw_output: str) -> str:
        """
        Cleans markdown fences, extra whitespace, and comments from the LLM output.
        """
        # Log/debug output print
        # print(f"Raw LLM Output:\n{raw_output}\n")
        
        # Remove markdown code blocks if any
        cleaned = raw_output.strip()
        
        # Matches ```sql ... ``` or ``` ... ```
        fence_match = re.match(r"^```(?:sql)?\s*(.*?)\s*```$", cleaned, re.DOTALL | re.IGNORECASE)
        if fence_match:
            cleaned = fence_match.group(1).strip()
            
        # Remove single line comments
        cleaned = re.sub(r"--.*$", "", cleaned, flags=re.MULTILINE)
        
        # Remove block comments
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        
        # Strip trailing semicolon if present (as the prompt asks not to chain statements)
        cleaned = cleaned.rstrip(";").strip()
        
        return cleaned

    def generate_sql(self, question: str, schema_context: str) -> str:
        """
        Generates SQL based on the user question and the retrieved schema.
        """
        system_message = (
            "You are a PostgreSQL expert. Given a user's question and a set of relevant table/column "
            "descriptions, generate exactly one read-only SELECT query that answers the question.\n\n"
            "Rules:\n"
            "- Output ONLY the SQL query. No explanation, no markdown formatting, no comments.\n"
            "- Use only tables and columns provided in the schema context below. Never invent columns.\n"
            "- Never use DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, GRANT, REVOKE, or CREATE.\n"
            "- Write exactly one statement. Do not use semicolons to chain multiple statements.\n"
            "- If the question cannot be answered with the given schema, output exactly: UNSUPPORTED\n\n"
            f"Schema context:\n{schema_context}"
        )
        
        user_message = f"User question: {question}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.0  # Keep it deterministic for SQL gen
        )
        
        raw_sql = response.choices[0].message.content
        return self.clean_llm_sql(raw_sql)

    def generate_retry_sql(self, question: str, schema_context: str, failed_query: str, error_message: str) -> str:
        """
        Generates a corrected SQL query after an execution failure.
        """
        system_message = (
            "You are a PostgreSQL expert. Given a user's question and a set of relevant table/column "
            "descriptions, generate exactly one read-only SELECT query that answers the question.\n\n"
            "Rules:\n"
            "- Output ONLY the SQL query. No explanation, no markdown formatting, no comments.\n"
            "- Use only tables and columns provided in the schema context below. Never invent columns.\n"
            "- Never use DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, GRANT, REVOKE, or CREATE.\n"
            "- Write exactly one statement. Do not use semicolons to chain multiple statements.\n"
            "- If the question cannot be answered with the given schema, output exactly: UNSUPPORTED\n\n"
            f"Schema context:\n{schema_context}"
        )
        
        user_message = (
            f"The following SQL query failed when executed against the database:\n\n"
            f"Query: {failed_query}\n"
            f"Error: {error_message}\n\n"
            f"Using the same schema context and original question, generate a corrected query.\n"
            f"Follow all the same rules as before. Output ONLY the corrected SQL query.\n\n"
            f"Original question: {question}"
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.0
        )
        
        raw_sql = response.choices[0].message.content
        return self.clean_llm_sql(raw_sql)

# Quick self-test script
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
    
    # Simple check
    from backend.app.rag.retriever import SchemaRetriever
    
    retriever = SchemaRetriever()
    generator = SQLGenerator()
    
    question = "How many orders were placed in total?"
    context = retriever.retrieve_relevant_schemas(question, top_k=2)
    sql = generator.generate_sql(question, context)
    
    print(f"Question: {question}")
    print(f"Generated SQL: {sql}")
