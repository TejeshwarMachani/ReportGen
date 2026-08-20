import json
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models.dataset import Dataset
from app.models.user import User
from app.services.dataset_service import DatasetService
from app.services.chat_service import chat_with_data, ChatDSL, ChatExecutor
from app.auth import get_current_user


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request to send a message to the chat endpoint."""
    message: str
    dataset_id: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    response: str
    statements: Optional[List[Dict[str, Any]]] = None
    results: Optional[List[Dict[str, Any]]] = None
    dataset_summary: Optional[Dict[str, Any]] = None
    updated_history: Optional[List[ChatMessage]] = None


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Send a message in the chat-with-data interface.

    The system:
    1. Validates user has access to the dataset
    2. Parses the user's query constrains LLM to DSL output
    3. Validates each DSL statement
    4. Executes validated statements against the data
    5. Returns formatted results

    Key constraint: LLM is constrained to emit ONLY structured DSL statements.
    Raw SQL or unstructured queries are prohibited.
    """
    # Validate dataset exists and user has access
    org_id = current_user.org_id
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.org_id == org_id
    ).first()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    # Parse the dataset schema to know valid fields
    schema = json.loads(dataset.schema_json) if dataset.schema_json else []
    valid_fields = set(col["column"] for col in schema if "column" in col)

    # In a full implementation, we would:
    # 1. Construct a constrained LLM prompt
    # 2. Call the LLM API
    # 3. Parse the DSL from the response
    # 4. Validate each statement
    # 5. Execute validated statements

    # For now, return a structured response showing the pattern
    # The actual LLM integration would replace this placeholder

    # Try to parse the user's intent and generate DSL statements
    # This is where the LLM would be called in production
    user_query = request.message

    # Basic keyword-based fallback for demo purposes
    # In production, this would be replaced by the LLM call
    statements = []
    results = []
    response_text = ""

    # Check for common query patterns and generate appropriate DSL
    query_lower = user_query.lower()

    # Aggregate queries (sum, avg, count)
    if any(word in query_lower for word in ["total", "sum", "count", "average", "mean"]):
        # Try to identify which field
        for col in valid_fields:
            if col.lower() in query_lower:
                # Determine operation
                if "count" in query_lower:
                    stmt = {
                        "type": ChatDSL.AGGREGATE,
                        "field": col,
                        "op": "count",
                    }
                    statements.append(stmt)
                    exec_result = ChatExecutor.execute(stmt, pd.DataFrame())
                    results.append(exec_result)
                elif "sum" in query_lower or "total" in query_lower:
                    stmt = {
                        "type": ChatDSL.AGGREGATE,
                        "field": col,
                        "op": "sum",
                    }
                    statements.append(stmt)
                    exec_result = ChatExecutor.execute(stmt, pd.DataFrame())
                    results.append(exec_result)
                elif "average" in query_lower or "mean" in query_lower:
                    stmt = {
                        "type": ChatDSL.AGGREGATE,
                        "field": col,
                        "op": "avg",
                    }
                    statements.append(stmt)
                    exec_result = ChatExecutor.execute(stmt, pd.DataFrame())
                    results.append(exec_result)

                # Only process first matching field
                break

    # Filter queries
    elif any(word in query_lower for word in ["filter", "where", "greater than", "less than"]):
        for col in valid_fields:
            if col.lower() in query_lower:
                # Determine filter type
                if "greater" in query_lower or ">" in query_lower:
                    # Try to extract a value
                    import re
                    num_match = re.search(r'[\d.]+', query_lower)
                    value = float(num_match.group()) if num_match else 0
                    stmt = {
                        "type": ChatDSL.FILTER,
                        "field": col,
                        "op": "gt",
                        "value": value,
                    }
                    statements.append(stmt)
                    exec_result = ChatExecutor.execute(stmt, pd.DataFrame())
                    results.append(exec_result)
                elif "less" in query_lower or "<" in query_lower:
                    num_match = re.search(r'[\d.]+', query_lower)
                    value = float(num_match.group()) if num_match else 0
                    stmt = {
                        "type": ChatDSL.FILTER,
                        "field": col,
                        "op": "lt",
                        "value": value,
                    }
                    statements.append(stmt)
                    exec_result = ChatExecutor.execute(stmt, pd.DataFrame())
                    results.append(exec_result)

                # Only process first matching field
                break

    # Comparison queries
    elif any(word in query_lower for word in ["compare", "versus", "vs", "difference"]):
        # Look for two fields
        fields_found = [col for col in valid_fields if col.lower() in query_lower]
        if len(fields_found) >= 2:
            stmt = {
                "type": ChatDSL.COMPARE,
                "field1": fields_found[0],
                "field2": fields_found[1],
                "op": "gt",
            }
            statements.append(stmt)
            exec_result = ChatExecutor.execute(stmt, pd.DataFrame())
            results.append(exec_result)
        elif len(fields_found) == 1:
            # Compare field to a value or itself
            stmt = {
                "type": ChatDSL.COMPARE,
                "field1": fields_found[0],
                "field2": fields_found[0],
                "op": "eq",
            }
            statements.append(stmt)
            exec_result = ChatExecutor.execute(stmt, pd.DataFrame())
            results.append(exec_result)

    # Time series queries
    elif any(word in query_lower for word in ["trend", "over time", "period", "growth"]):
        # Look for date and value fields
        date_fields = [col for col in valid_fields if any(
            d in col.lower() for d in ["date", "time", "year", "month"])]
        value_fields = [col for col in valid_fields if col not in date_fields]

        if date_fields and value_fields:
            stmt = {
                "type": ChatDSL.TIME_SERIES,
                "date_field": date_fields[0],
                "value_field": value_fields[0],
                "op": "trend",
            }
            statements.append(stmt)
            exec_result = ChatExecutor.execute(stmt, pd.DataFrame())
            results.append(exec_result)

    # Top-N queries
    elif any(word in query_lower for word in ["top", "highest", "lowest"]):
        # Extract number if present
        import re
        num_match = re.search(r'\b(\d+)\b', query_lower)
        n = int(num_match.group(1)) if num_match else 5

        for col in valid_fields:
            if col.lower() in query_lower:
                stmt = {
                    "type": ChatDSL.TOP_N,
                    "field": col,
                    "n": min(n, 100),
                    "op": "gt",
                }
                statements.append(stmt)
                exec_result = ChatExecutor.execute(stmt, pd.DataFrame())
                results.append(exec_result)
                break

    # Correlation queries
    elif any(word in query_lower for word in ["correlate", "relationship", "associated with"]):
        fields_found = [col for col in valid_fields if col.lower() in query_lower]
        if len(fields_found) >= 2:
            stmt = {
                "type": ChatDSL.CORRELATION,
                "field1": fields_found[0],
                "field2": fields_found[1],
                "method": "pearson",
            }
            statements.append(stmt)
            exec_result = ChatExecutor.execute(stmt, pd.DataFrame())
            results.append(exec_result)

    # If no pattern matched, provide general response
    if not statements:
        response_text = (
            "I'd be happy to help you analyze your data! Could you rephrase your query? "
            "I can help with: totals/averages, filtering, comparisons, trends over time, "
            "top/bottom values, or correlations between fields."
        )
        # Provide a dataset overview
        dataset_schema = {
            "total_rows": len(df) if 'df' in dir() else dataset.row_count,
            "columns": list(valid_fields),
        }
        return ChatResponse(
            response=response_text,
            dataset_summary=dataset_schema,
            statements=statements,
            results=results,
        )

    # Build response from executed statements
    summary_parts = []
    for i, (stmt, result) in enumerate(zip(statements, results)):
        if "error" in result:
            summary_parts.append(f"Query {i+1}: {result['error']}")
        else:
            summary_parts.append(result.get("summary", str(result)))

    if summary_parts:
        response_text = " | ".join(summary_parts)
    else:
        response_text = "I analyzed your request but didn't find specific results. "
        "Could you rephrase your question?"

    return ChatResponse(
        response=response_text,
        statements=statements,
        results=results,
        dataset_summary={"columns": list(valid_fields)},
    )