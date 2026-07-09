import logging
from fastapi import APIRouter, HTTPException, Request
from backend.app.models.schemas import QueryRequest, QueryResponse
from backend.app.rag.retriever import SchemaRetriever
from backend.app.llm.sql_generator import SQLGenerator
from backend.app.validator.sql_validator import SQLValidator
from backend.app.db.connection import QueryExecutor
from backend.app.llm.explainer import SQLExplainer
from backend.app.upload.session_manager import is_valid_uuid
from backend.app.limiter import limiter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asksql-router")

router = APIRouter()

retriever = SchemaRetriever()
generator = SQLGenerator()
validator = SQLValidator()
executor = QueryExecutor()
explainer = SQLExplainer()

@router.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
async def process_nl_query(request: Request, payload: QueryRequest):
    question = payload.question.strip()
    session_id = payload.session_id.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID cannot be empty.")
    if not is_valid_uuid(session_id):
        raise HTTPException(status_code=400, detail="Invalid Session ID format. Must be a valid UUID.")
        
    logger.info(f"Received question: {question} for session: {session_id}")
    
    # Step 1: Retrieve schema context
    try:
        schema_context = retriever.retrieve_relevant_schemas(question, session_id=session_id, top_k=4)
        logger.info("Retrieved relevant schemas from ChromaDB.")
    except Exception as e:
        logger.error(f"Retriever error: {e}")
        return QueryResponse(success=False, error=f"Retrieval system error: {str(e)}")

    retries_used = 0
    attempt = 1
    max_attempts = 2
    
    # We will keep track of the SQL to run
    current_sql = None
    validation_error = None
    execution_error = None
    
    while attempt <= max_attempts:
        logger.info(f"Pipeline attempt {attempt}...")
        
        # Step 2: Generate SQL
        try:
            if attempt == 1:
                current_sql = generator.generate_sql(question, schema_context)
            else:
                retries_used += 1
                error_msg = execution_error or validation_error
                logger.info(f"Retrying SQL generation after error: {error_msg}")
                current_sql = generator.generate_retry_sql(
                    question=question,
                    schema_context=schema_context,
                    failed_query=current_sql,
                    error_message=str(error_msg)
                )
                
            logger.info(f"Generated SQL: {current_sql}")
        except Exception as e:
            logger.error(f"LLM SQL generator error: {e}")
            return QueryResponse(success=False, error=f"LLM generation failed: {str(e)}", retries_used=retries_used)

        # Handle UNSUPPORTED output
        if current_sql.upper() == "UNSUPPORTED":
            logger.info("LLM flagged question as UNSUPPORTED.")
            return QueryResponse(
                success=False,
                error="This question cannot be answered with the current database schema.",
                retries_used=retries_used
            )

        # Step 3: Validate SQL
        is_valid, validation_error = validator.validate_sql(current_sql, session_id=session_id)
        if not is_valid:
            logger.warning(f"SQL validation failed: {validation_error}")
            attempt += 1
            execution_error = None  # Reset execution error to force retry on validation
            continue

        # Step 4: Execute SQL (enforcing limit)
        sql_to_run = validator.enforce_limit(current_sql)
        logger.info(f"Executing SQL: {sql_to_run}")
        
        try:
            results = executor.execute_query(sql_to_run, session_id=session_id)
            logger.info(f"Query executed successfully. Retrieved {len(results)} rows.")
            
            # Step 5: Explain SQL
            try:
                explanation = explainer.explain_sql(current_sql)
                logger.info("Generated explanation.")
            except Exception as e:
                logger.error(f"Explainer error: {e}")
                explanation = "Could not generate an explanation for this query."
                
            return QueryResponse(
                success=True,
                sql=current_sql,
                explanation=explanation,
                results=results,
                retries_used=retries_used
            )
            
        except Exception as e:
            execution_error = str(e)
            logger.warning(f"Query execution failed: {execution_error}")
            validation_error = None
            attempt += 1
            
    # If we exited the loop, both attempts failed
    final_error = execution_error or validation_error or "Failed to generate a valid and executable SQL query."
    return QueryResponse(
        success=False,
        sql=current_sql,
        error=f"Pipeline error: {final_error}",
        retries_used=retries_used
    )
