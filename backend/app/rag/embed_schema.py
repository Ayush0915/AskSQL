import os
import json
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path

# Fix warning for HuggingFace downloads in some environments
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Import config
from backend.app.config import config

def format_table_document(table_data: dict) -> str:
    """
    Formats the table and column metadata into a clean textual representation
    for semantic retrieval.
    """
    table_name = table_data["table_name"]
    desc = table_data["description"]
    
    doc_lines = [
        f"Table Name: {table_name}",
        f"Description: {desc}",
        "Columns:"
    ]
    
    for col_name, col_desc in table_data["columns"].items():
        doc_lines.append(f"  - {col_name}: {col_desc}")
        
    return "\n".join(doc_lines)

def embed_schema():
    backend_dir = Path(__file__).resolve().parent.parent.parent
    schema_path = backend_dir / "data" / "schema_descriptions.json"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema descriptions not found at {schema_path}")
        
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)
        
    tables = schema_data.get("tables", [])
    if not tables:
        print("No tables found in schema descriptions.")
        return
        
    print(f"Loaded metadata for {len(tables)} tables.")
    
    # Initialize ChromaDB persistent client
    persist_dir = config.CHROMA_PERSIST_DIR
    print(f"Initializing ChromaDB client at: {persist_dir}")
    client = chromadb.PersistentClient(path=persist_dir)
    
    # Define embedding function using sentence-transformers
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # Create or get collection
    # We use get_or_create to prevent duplicate creation errors, 
    # but we will clear it if it exists to avoid duplicate entries.
    collection = client.get_or_create_collection(
        name="schema_collection",
        embedding_function=emb_fn
    )
    
    # Delete existing entries in the collection if any
    existing = collection.get()
    if existing and existing.get("ids"):
        print(f"Clearing {len(existing['ids'])} existing documents from collection...")
        collection.delete(ids=existing["ids"])
        
    # Prepare documents, metadatas, and ids
    documents = []
    metadatas = []
    ids = []
    
    for idx, table in enumerate(tables):
        doc = format_table_document(table)
        documents.append(doc)
        metadatas.append({"table_name": table["table_name"]})
        ids.append(f"table_{table['table_name']}")
        
    # Add to collection
    print("Embedding and indexing schema documents...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print("Schema embedding completed successfully!")

if __name__ == "__main__":
    # Add parent directory to sys.path so we can run this script directly
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
    embed_schema()
