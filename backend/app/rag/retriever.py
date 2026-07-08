import chromadb
from chromadb.utils import embedding_functions
from backend.app.config import config

class SchemaRetriever:
    def __init__(self):
        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
        
        # Define embedding function matching the embedding script
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get collection
        self.collection = self.client.get_collection(
            name="schema_collection",
            embedding_function=self.emb_fn
        )

    def retrieve_relevant_schemas(self, question: str, top_k: int = 4) -> str:
        """
        Queries ChromaDB for top_k relevant tables for a user's question,
        and returns them formatted as a single context string.
        """
        results = self.collection.query(
            query_texts=[question],
            n_results=top_k
        )
        
        # Extract the documents
        documents = results.get("documents", [])
        if not documents or len(documents[0]) == 0:
            return "No schema context retrieved."
            
        # Format list of retrieved documents
        retrieved_docs = documents[0]
        formatted_context = []
        for doc in retrieved_docs:
            formatted_context.append(doc)
            formatted_context.append("-" * 40)
            
        return "\n".join(formatted_context)

# Quick self-test script
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
    
    retriever = SchemaRetriever()
    test_question = "What are the top 5 best selling products by quantity?"
    print(f"Test Question: '{test_question}'\n")
    context = retriever.retrieve_relevant_schemas(test_question, top_k=2)
    print("Retrieved Context:")
    print(context)
