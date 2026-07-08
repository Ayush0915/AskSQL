from groq import Groq
from backend.app.config import config

class SQLExplainer:
    def __init__(self):
        api_key = config.GROQ_API_KEY
        if api_key:
            self.client = Groq(api_key=api_key)
        else:
            self.client = Groq()
        self.model = "llama-3.3-70b-versatile"

    def explain_sql(self, sql: str) -> str:
        """
        Explains a generated SQL SELECT query in simple English.
        """
        system_message = (
            "Explain the following SQL query in plain English, in 2-4 sentences, for someone with "
            "no SQL background. Describe what data it retrieves and any filtering/grouping/sorting "
            "it applies. Do not repeat the raw SQL syntax back to them."
        )
        
        user_message = f"Query: {sql}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3  # Slightly higher temp for natural language writing
        )
        
        explanation = response.choices[0].message.content.strip()
        return explanation

# Quick self-test script
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
    
    explainer = SQLExplainer()
    test_sql = (
        "SELECT customer_city, COUNT(customer_id) FROM customers "
        "GROUP BY customer_city ORDER BY COUNT(customer_id) DESC LIMIT 5"
    )
    explanation = explainer.explain_sql(test_sql)
    print(f"SQL: {test_sql}\n")
    print(f"Explanation: {explanation}")
