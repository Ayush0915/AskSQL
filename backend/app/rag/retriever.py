import chromadb
from chromadb.utils import embedding_functions
from backend.app.config import config
from backend.app.upload.session_manager import get_chroma_collection_name

class SchemaRetriever:
    def __init__(self):
        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
        
        # Define embedding function matching the embedding script
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

    def retrieve_relevant_schemas(self, question: str, session_id: str, top_k: int = 4) -> str:
        """
        Queries ChromaDB for top_k relevant tables for a user's question within the session's collection,
        and returns them formatted as a single context string.
        """
        coll_name = get_chroma_collection_name(session_id)
        
        try:
            collection = self.client.get_collection(
                name=coll_name,
                embedding_function=self.emb_fn
            )
        except Exception:
            return "No schema context retrieved. Please upload a dataset or load the sample data first."
            
        results = collection.query(
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
