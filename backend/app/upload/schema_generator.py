import json
import re
import logging
from groq import Groq
import chromadb
from chromadb.utils import embedding_functions
from backend.app.config import config
from backend.app.upload.session_manager import (
    session_schemas,
    get_chroma_collection_name
)

logger = logging.getLogger("asksql-schema-generator")
logging.basicConfig(level=logging.INFO)

# Define embedding function using sentence-transformers (matches retriever)
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

def find_relationships(session_id: str) -> list[str]:
    """
    Scans the columns of all tables loaded in the session schemas
    to identify columns ending with '_id' that share names across multiple tables.
    Returns a list of relationship strings.
    """
    schemas = session_schemas.get(session_id, {})
    col_to_tables = {}
    for table_name, table_info in schemas.items():
        for col_name in table_info["columns"].keys():
            if col_name.endswith("_id"):
                col_to_tables.setdefault(col_name, []).append(table_name)
                
    relationships = []
    for col_name, tables in col_to_tables.items():
        if len(tables) > 1:
            tbls_str = ", ".join(tables)
            relationships.append(f"Column '{col_name}' connects tables: {tbls_str}")
    return relationships

def format_table_document(table_name: str, table_desc: str, columns: dict) -> str:
    """Formats the table and column descriptions for indexing in ChromaDB."""
    doc_lines = [
        f"Table Name: {table_name}",
        f"Description: {table_desc}",
        "Columns:"
    ]
    for col_name, col_desc in columns.items():
        doc_lines.append(f"  - {col_name}: {col_desc}")
    return "\n".join(doc_lines)

def generate_schema_descriptions_llm(
    session_id: str,
    table_name: str,
    columns_and_types: dict,
    sample_rows: list
) -> dict:
    """
    Sends the table structure and sample data to Llama 3 via Groq,
    and returns a parsed JSON with descriptions for the table and each column.
    """
    api_key = config.GROQ_API_KEY
    if api_key:
        client = Groq(api_key=api_key)
    else:
        client = Groq()

    # Pre-cache/register the table structure in session_schemas so we can detect relationships
    if session_id not in session_schemas:
        session_schemas[session_id] = {}
        
    session_schemas[session_id][table_name] = {
        "description": "Pending LLM description...",
        "columns": {col: f"Type: {t}" for col, t in columns_and_types.items()}
    }

    # Find potential join relationships for this session
    join_hints = find_relationships(session_id)
    hints_text = "\n".join([f"- {h}" for h in join_hints]) if join_hints else "None detected."

    column_list_str = ", ".join([f"{col} ({t})" for col, t in columns_and_types.items()])
    sample_rows_str = json.dumps(sample_rows, indent=2)

    prompt = f"""You are documenting a database table for someone building SQL queries against it.
Given the table name, column names with inferred types, some sample rows, and suggested join relationships:
write a JSON object containing:
- "table_description": a one-sentence description of what this table represents
- "columns": a JSON object where keys are column names and values are a one-sentence description for each column (what it contains, and if it's an enum-like or status column, mention the range of values you see in the samples). If the column joins with another table based on the join relationships, explicitly mention that in the description (e.g. "Unique key of the order (joins with order_items.order_id)").

Join Relationships:
{hints_text}

Respond with ONLY valid JSON, no markdown blocks, no formatting, no preamble, and no extra text.

Format:
{{"table_description": "...", "columns": {{"column_name": "description", ...}}}}

Table name: {table_name}
Columns and types: {column_list_str}
Sample rows:
{sample_rows_str}
"""

    logger.info(f"Generating descriptions for table '{table_name}' using Llama 3...")
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a database documenter that outputs raw JSON descriptions only."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0
        )
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Clean up any potential markdown wraps
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\s*(.*?)\s*```$", r"\1", response_text, flags=re.DOTALL | re.IGNORECASE).strip()
            
        data = json.loads(response_text)
        table_desc = data.get("table_description", f"Data table for {table_name}.")
        columns_desc = data.get("columns", {})
        
        # Make sure every column has a description
        for col in columns_and_types.keys():
            if col not in columns_desc:
                columns_desc[col] = f"Column containing {col} details (Type: {columns_and_types[col]})."
                
        # Update the session schema cache with the actual descriptions
        session_schemas[session_id][table_name] = {
            "description": table_desc,
            "columns": columns_desc
        }
        
        logger.info(f"Successfully generated descriptions for '{table_name}'")
        return {
            "table_description": table_desc,
            "columns": columns_desc
        }
    except Exception as e:
        logger.error(f"Failed to generate schema descriptions for '{table_name}': {e}")
        # Fallback descriptions in case of API failure
        fallback_desc = {
            "table_description": f"User-uploaded data table: {table_name}.",
            "columns": {col: f"Column {col} (Type: {t})" for col, t in columns_and_types.items()}
        }
        session_schemas[session_id][table_name] = fallback_desc
        return fallback_desc

def embed_session_table_schema(
    session_id: str,
    table_name: str,
    table_desc: str,
    columns_desc: dict
):
    """Embeds the generated table schema description into the session-specific ChromaDB collection."""
    coll_name = get_chroma_collection_name(session_id)
    
    try:
        client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
        collection = client.get_or_create_collection(
            name=coll_name,
            embedding_function=emb_fn
        )
        
        # Format document representation
        doc = format_table_document(table_name, table_desc, columns_desc)
        
        # Remove table from collection if it was already indexed to avoid duplicates
        doc_id = f"table_{table_name}"
        try:
            collection.delete(ids=[doc_id])
        except Exception:
            pass
            
        # Add to collection
        collection.add(
            documents=[doc],
            metadatas=[{"table_name": table_name}],
            ids=[doc_id]
        )
        logger.info(f"Indexed schema for table '{table_name}' in Chroma collection '{coll_name}'")
    except Exception as e:
        logger.error(f"Error indexing schema to ChromaDB for session {session_id}: {e}")
        raise RuntimeError(f"ChromaDB indexing error: {str(e)}")

def generate_example_questions_llm(session_id: str) -> list[str]:
    """
    Queries Llama 3 on Groq with the session's active schema layout,
    and returns a list of 4-5 relevant business questions suited for the dataset.
    """
    from backend.app.upload.session_manager import session_schemas, session_questions
    
    tables = session_schemas.get(session_id, {})
    if not tables:
        return []
        
    schema_details = []
    for table_name, table_info in tables.items():
        cols = ", ".join(table_info["columns"].keys())
        schema_details.append(f"Table '{table_name}' ({table_info['description']}): columns = [{cols}]")
        
    schema_text = "\n".join(schema_details)
    
    api_key = config.GROQ_API_KEY
    if api_key:
        client = Groq(api_key=api_key)
    else:
        client = Groq()
        
    prompt = f"""You are a business analyst looking at a database schema.
Here are the tables in the database:
{schema_text}

Generate exactly 5 distinct, practical, and highly relevant business questions that can be answered using SQL SELECT queries on these tables.
Make sure the questions:
1. Cover different tables and JOINs if possible.
2. Range from simple aggregates (e.g. total counts) to deeper analysis (e.g. top categories, monthly trends).
3. Do not ask for things that aren't in the columns.
4. Keep questions concise and written in natural, friendly English.

Respond with ONLY a JSON array of strings. No markdown fences, no formatting, no preamble, and no extra text.
Example format:
["What is the total number of items sold?", "Which customer city has the most orders?"]
"""
    logger.info(f"Generating dynamic example questions for session {session_id} using Llama 3...")
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a business analyst helper. Output a raw JSON list of strings only."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3
        )
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Clean markdown wraps if any
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\s*(.*?)\s*```$", r"\1", response_text, flags=re.DOTALL | re.IGNORECASE).strip()
            
        questions = json.loads(response_text)
        if isinstance(questions, list):
            valid_questions = [str(q) for q in questions[:6]]
            session_questions[session_id] = valid_questions
            logger.info(f"Successfully generated dynamic questions for session {session_id}")
            return valid_questions
    except Exception as e:
        logger.error(f"Failed to generate example questions: {e}")
        
    # Fallback to standard generic questions
    fallback = [
        "Show a preview of the tables.",
        "How many rows are in each table?"
    ]
    session_questions[session_id] = fallback
    return fallback
