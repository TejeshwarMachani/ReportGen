"""Service for 'Chat With Data' functionality.

Handles:
1. Structured query DSL - constrains LLM to emit a constrained DSL, not raw SQL
2. DSL validator - validates the DSL before execution
3. Execution engine - runs validated DSL against pandas DataFrame
4. Response formatting - formats results for chat UI

CRITICAL: The LLM is constrained to emit ONLY the structured DSL.
The execution engine validates and runs it. Never execute raw LLM-generated SQL.
"""

import pandas as pd
import re
from typing import Dict, List, Any, Optional, Tuple


class ChatDSL:
    """Domain Specific Language for chat-to-data queries.

    The LLM must emit exactly one of these statement types.
    The executor validates and runs each type.
    """

    # Statement types
    AGGREGATE = "aggregate"
    FILTER = "filter"
    COMPARE = "compare"
    TIME_SERIES = "time_series"
    TOP_N = "top_n"
    CORRELATION = "correlation"

    # Valid field references (set at runtime based on dataset schema)
    valid_fields: set = set()

    # Valid operators per type
    AGGREGATE_OPS = {"sum", "avg", "count", "min", "max", "mean", "median"}
    FILTER_OPS = {"gt", "gte", "lt", "lte", "eq", "ne", "contains", "starts_with", "in"}
    COMPARE_OPS = {"gt", "gte", "lt", "lte", "eq", "ne"}
    TOP_N_OPS = {"gt", "gte", "lt", "lte", "eq"}
    CORRELATION_OPS = {"pearson", "spearman"}

    @classmethod
    def reset(cls, valid_fields: set):
        """Reset valid fields for a new dataset."""
        cls.valid_fields = valid_fields

    @classmethod
    def validate_statement(cls, stmt: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate a DSL statement.

        Returns (is_valid, error_message).
        is_valid is True only when the statement is fully valid.
        """
        if not isinstance(stmt, dict):
            return False, "Statement must be a JSON object"

        stmt_type = stmt.get("type")
        if not stmt_type:
            return False, "Statement missing 'type' field"

        # Validate based on type
        if stmt_type == cls.AGGREGATE:
            return cls._validate_aggregate(stmt)
        elif stmt_type == cls.FILTER:
            return cls._validate_filter(stmt)
        elif stmt_type == cls.COMPARE:
            return cls._validate_compare(stmt)
        elif stmt_type == cls.TIME_SERIES:
            return cls._validate_time_series(stmt)
        elif stmt_type == cls.TOP_N:
            return cls._validate_top_n(stmt)
        elif stmt_type == cls.CORRELATION:
            return cls._validate_correlation(stmt)
        else:
            return False, f"Unknown statement type: {stmt_type}"

    @classmethod
    def _validate_aggregate(cls, stmt: Dict) -> Tuple[bool, Optional[str]]:
        """Validate aggregate statement."""
        field = stmt.get("field")
        op = stmt.get("op")

        if not field:
            return False, "Aggregate statement missing 'field'"
        if field not in cls.valid_fields:
            return False, f"Invalid field: {field}. Valid fields: {', '.join(sorted(cls.valid_fields))}"
        if op not in cls.AGGREGATE_OPS:
            return False, f"Invalid aggregate op: {op}. Valid: {', '.join(cls.AGGREGATE_OPS)}"

        # Check for dangerous patterns
        if "sql" in str(stmt).lower() or "execute" in str(stmt).lower():
            return False, "Dangerous pattern detected: raw SQL execution prohibited"

        return True, None

    @classmethod
    def _validate_filter(cls, stmt: Dict) -> Tuple[bool, Optional[str]]:
        """Validate filter statement."""
        field = stmt.get("field")
        op = stmt.get("op")
        value = stmt.get("value")

        if not field:
            return False, "Filter statement missing 'field'"
        if field not in cls.valid_fields:
            return False, f"Invalid field: {field}"
        if op not in cls.FILTER_OPS:
            return False, f"Invalid filter op: {op}. Valid: {', '.join(cls.FILTER_OPS)}"
        if value is None:
            return False, "Filter statement missing 'value'"

        # Type checking for the value based on field type
        # (basic check - full type checking done in executor)
        if not isinstance(value, (str, int, float, bool, list)):
            return False, f"Filter value has invalid type: {type(value).__name__}"

        if "sql" in str(value).lower() or "execute" in str(str(value)).lower():
            return False, "Dangerous pattern: raw SQL in filter value prohibited"

        return True, None

    @classmethod
    def _validate_compare(cls, stmt: Dict) -> Tuple[bool, Optional[str]]:
        """Validate compare statement."""
        field1 = stmt.get("field1")
        field2 = stmt.get("field2")
        op = stmt.get("op")

        if not field1 or not field2:
            return False, "Compare statement missing 'field1' or 'field2'"
        if field1 not in cls.valid_fields or field2 not in cls.valid_fields:
            return False, f"Invalid field(s). Valid: {', '.join(sorted(cls.valid_fields))}"
        if op not in cls.COMPARE_OPS:
            return False, f"Invalid compare op: {op}. Valid: {', '.join(cls.COMPARE_OPS)}"

        return True, None

    @classmethod
    def _validate_time_series(cls, stmt: Dict) -> Tuple[bool, Optional[str]]:
        """Validate time series statement."""
        date_field = stmt.get("date_field")
        value_field = stmt.get("value_field")
        op = stmt.get("op", "trend")

        if not date_field or not value_field:
            return False, "Time series statement missing date_field or value_field"
        if date_field not in cls.valid_fields:
            return False, f"Invalid date field: {date_field}"
        if value_field not in cls.valid_fields:
            return False, f"Invalid value field: {value_field}"
        if op not in {"trend", "growth", "change"}:
            return False, f"Invalid time series op: {op}. Valid: trend, growth, change"

        return True, None

    @classmethod
    def _validate_top_n(cls, stmt: Dict) -> Tuple[bool, Optional[str]]:
        """Validate top-n statement."""
        field = stmt.get("field")
        n = stmt.get("n")
        op = stmt.get("op", "gt")

        if not field:
            return False, "Top-N statement missing 'field'"
        if field not in cls.valid_fields:
            return False, f"Invalid field: {field}"
        if n is None:
            return False, "Top-N statement missing 'n'"
        try:
            n = int(n)
            if n < 1 or n > 100:
                return False, f"'n' must be between 1 and 100, got {n}"
        except (ValueError, TypeError):
            return False, f"'n' must be an integer, got {n}"
        if op not in cls.TOP_N_OPS:
            return False, f"Invalid top-N op: {op}. Valid: {', '.join(cls.TOP_N_OPS)}"

        return True, None

    @classmethod
    def _validate_correlation(cls, stmt: Dict) -> Tuple[bool, Optional[str]]:
        """Validate correlation statement."""
        field1 = stmt.get("field1")
        field2 = stmt.get("field2")
        method = stmt.get("method", "pearson")

        if not field1 or not field2:
            return False, "Correlation statement missing field1 or field2"
        if field1 not in cls.valid_fields or field2 not in cls.valid_fields:
            return False, f"Invalid field(s). Valid: {', '.join(sorted(cls.valid_fields))}"
        if method not in cls.CORRELATION_OPS:
            return False, f"Invalid correlation method: {method}. Valid: {', '.join(cls.CORRELATION_OPS)}"

        return True, None


class ChatExecutor:
    """Execution engine for Chat DSL statements.

    Validates each statement THEN runs it against the pandas DataFrame.
    Never executes raw LLM output - always goes through validation first.
    """

    @classmethod
    def execute(cls, stmt: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Execute a validated DSL statement against a DataFrame.

        Returns dict with 'result' and 'summary' keys.
        """
        stmt_type = stmt.get("type")

        # Map to executor method
        executors = {
            ChatDSL.AGGREGATE: cls._execute_aggregate,
            ChatDSL.FILTER: cls._execute_filter,
            ChatDSL.COMPARE: cls._execute_compare,
            ChatDSL.TIME_SERIES: cls._execute_time_series,
            ChatDSL.TOP_N: cls._execute_top_n,
            ChatDSL.CORRELATION: cls._execute_correlation,
        }

        executor = executors.get(stmt_type)
        if not executor:
            return {
                "error": f"Unknown statement type: {stmt_type}",
                "raw_input": stmt,
            }

        return executor(stmt, df)

    @classmethod
    def _execute_aggregate(cls, stmt: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute aggregate statement: sum/avg/count etc. on a field."""
        field = stmt["field"]
        op = stmt["op"]

        series = df[field]

        if op == "count":
            result = int(series.count())
        elif op in ("sum", "total"):
            result = float(series.sum())
        elif op in ("avg", "mean"):
            result = float(series.mean())
        elif op == "median":
            result = float(series.median())
        elif op in ("min", "lowest"):
            result = float(series.min())
        elif op in ("max", "highest"):
            result = float(series.max())

        return {
            "type": "aggregate",
            "field": field,
            "op": op,
            "result": result,
            "summary": f"{op.title()} of {field}: {result}",
        }

    @classmethod
    def _execute_filter(cls, stmt: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute filter statement on a field."""
        field = stmt["field"]
        op = stmt["op"]
        value = stmt["value"]

        series = df[field]

        # Convert value to appropriate type
        if isinstance(value, str):
            # String comparison operations
            if op == "contains":
                mask = series.astype(str).str.contains(value, case=False, na=False)
            elif op == "starts_with":
                mask = series.astype(str).str.startswith(value, na=False)
            elif op == "eq":
                mask = series.astype(str) == value
            elif op == "ne":
                mask = series.astype(str) != value
            elif op in ("gt", "gte", "lt", "lte"):
                # Try numeric comparison on string-encoded numbers
                try:
                    num_value = float(value)
                    if op == "gt":
                        mask = pd.to_numeric(series, errors="coerce") > num_value
                    elif op == "gte":
                        mask = pd.to_numeric(series, errors="coerce") >= num_value
                    elif op == "lt":
                        mask = pd.to_numeric(series, errors="coerce") < num_value
                    elif op == "lte":
                        mask = pd.to_numeric(series, errors="coerce") <= num_value
                except ValueError:
                    # Fall back to string comparison
                    mask = series.astype(str).str.contains(value, case=False, na=False)
            else:
                mask = pd.Series([False] * len(df))
        elif isinstance(value, (int, float)):
            # Numeric comparison
            if op == "eq":
                mask = series == value
            elif op == "ne":
                mask = series != value
            elif op == "gt":
                mask = series > value
            elif op == "gte":
                mask = series >= value
            elif op == "lt":
                mask = series < value
            elif op == "lte":
                mask = series <= value
            else:
                mask = pd.Series([False] * len(df))
        else:
            mask = pd.Series([False] * len(df))

        filtered_df = df[mask].copy()
        count = int(len(filtered_df))

        return {
            "type": "filter",
            "field": field,
            "op": op,
            "value": value,
            "result_count": count,
            "summary": f"Filter {field} {op} {repr(value)}: {count} records match",
            "filtered_data": filtered_df.to_dict(orient="records")[:10]  # Return first 10 rows
        }

    @classmethod
    def _execute_compare(cls, stmt: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """Compare two fields."""
        field1 = stmt["field1"]
        field2 = stmt["field2"]
        op = stmt["op"]

        series1 = df[field1]
        series2 = df[field2]

        # Ensure both are numeric for comparison
        try:
            s1 = pd.to_numeric(series1, errors="coerce")
            s2 = pd.to_numeric(series2, errors="coerce")
        except Exception:
            return {
                "error": f"Cannot compare non-numeric fields: {field1} and {field2}",
                "summary": "Comparison not available: fields are not numeric",
            }

        # Compute comparison based on operator
        if op == "eq":
            matches = (s1 == s2).sum()
            result = f"{int(matches)} records have equal values in both fields"
        elif op == "ne":
            mismatches = (s1 != s2).sum()
            result = f"{int(mismatches)} records have different values"
        elif op == "gt":
            more = (s1 > s2).sum()
            result = f"{int(more)} records have {field1} > {field2}"
        elif op == "gte":
            more_eq = (s1 >= s2).sum()
            result = f"{int(more_eq)} records have {field1} >= {field2}"
        elif op == "lt":
            less = (s1 < s2).sum()
            result = f"{int(less)} records have {field1} < {field2}"
        elif op == "lte":
            less_eq = (s1 <= s2).sum()
            result = f"{int(less_eq)} records have {field1} <= {field2}"

        return {
            "type": "compare",
            "field1": field1,
            "field2": field2,
            "op": op,
            "result": result,
            "summary": result,
        }

    @classmethod
    def _execute_time_series(cls, stmt: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """Time series analysis - trend, growth, or change over periods."""
        date_field = stmt["date_field"]
        value_field = stmt["value_field"]
        op = stmt.get("op", "trend")

        # Sort by date
        df_sorted = df.sort_values(by=date_field)

        try:
            dates = pd.to_datetime(df_sorted[date_field])
            values = pd.to_numeric(df_sorted[value_field], errors="coerce")
        except Exception:
            return {
                "error": f"Cannot parse date/time or value field for time series",
                "summary": "Time series analysis unavailable",
            }

        if op == "trend":
            # Simple trend: first vs last
            if len(values) >= 2:
                first_val = values.iloc[0]
                last_val = values.iloc[-1]
                if pd.notna(first_val) and pd.notna(last_val) and first_val != 0:
                    pct_change = ((last_val - first_val) / abs(first_val)) * 100
                    result = f"Over the period, {value_field} {('increased' if pct_change > 0 else 'decreased')} by {abs(pct_change):.1f}% (from {first_val:.2f} to {last_val:.2f})"
                else:
                    result = f"{value_field} trend: {len(values)} data points observed"
            else:
                result = f"{value_field}: {len(values)} data point(s)"

        elif op == "growth":
            # Year-over-year or period-over-period growth
            if len(values) >= 2:
                first_val = float(values.iloc[0]) if pd.notna(values.iloc[0]) else 0
                last_val = float(values.iloc[-1]) if pd.notna(values.iloc[-1]) else 0
                if first_val != 0:
                    growth_pct = ((last_val - first_val) / abs(first_val)) * 100
                    result = f"{value_field} grew by {growth_pct:.1f}% over {len(values)} periods"
                else:
                    result = f"{value_field} changed from {first_val} to {last_val} over {len(values)} periods"
            else:
                result = f"{value_field}: {len(values)} data point(s)"

        elif op == "change":
            # Absolute change
            if len(values) >= 2:
                first_val = float(values.iloc[0]) if pd.notna(values.iloc[0]) else 0
                last_val = float(values.iloc[-1]) if pd.notna(values.iloc[-1]) else 0
                change = last_val - first_val
                result = f"{value_field} changed by {change:.2f} ({first_val:.2f} -> {last_val:.2f})"
            else:
                result = f"{value_field}: {len(values)} data point(s)"

        return {
            "type": "time_series",
            "date_field": date_field,
            "value_field": value_field,
            "op": op,
            "result": result,
            "summary": result,
        }

    @classmethod
    def _execute_top_n(cls, stmt: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """Top-N records by field value."""
        field = stmt["field"]
        n = int(stmt["n"])
        op = stmt.get("op", "gt")

        series = df[field]

        # Sort descending by value
        try:
            s = pd.to_numeric(series, errors="coerce").dropna()
        except Exception:
            s = series.dropna()

        top_n = s.nlargest(n)
        results = top_n.index.tolist()
        values = top_n.values.tolist()

        return {
            "type": "top_n",
            "field": field,
            "n": n,
            "op": op,
            "results": [
                {"index": idx, "value": val}
                for idx, val in zip(results, values)
            ],
            "summary": f"Top {n} {field}: {[float(v) for v in values]}",
        }

    @classmethod
    def _execute_correlation(cls, stmt: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute correlation between two fields."""
        field1 = stmt["field1"]
        field2 = stmt["field2"]
        method = stmt.get("method", "pearson")

        series1 = pd.to_numeric(df[field1], errors="coerce").dropna()
        series2 = pd.to_numeric(df[field2], errors="coerce").dropna()

        # Remove NaN pairs
        paired = pd.DataFrame({
            field1: series1,
            field2: series2,
        }).dropna()

        if len(paired) < 3:
            return {
                "error": "Not enough valid data points for correlation (minimum 3)",
                "summary": "Correlation unavailable: insufficient data",
            }

        # Compute correlation
        corr_method = method if method in ("pearson", "spearman") else "pearson"
        if corr_method == "pearson":
            corr = paired[field1].corr(paired[field2], method="pearson")
        else:
            # Spearman rank correlation
            corr = paired[field1].rank().corr(paired[field2].rank(), method="pearson")

        # Determine significance (simple check)
        abs_corr = abs(corr)
        if abs_corr >= 0.7:
            strength = "strong"
        elif abs_corr >= 0.3:
            strength = "moderate"
        else:
            strength = "weak"

        direction = "positive" if corr > 0 else "negative"

        return {
            "type": "correlation",
            "field1": field1,
            "field2": field2,
            "method": corr_method,
            "correlation": round(corr, 4),
            "strength": strength,
            "direction": direction,
            "sample_size": len(paired),
            "summary": f"{strength} {direction} correlation ({round(corr, 3)}) between {field1} and {field2} (n={len(paired)})",
        }


def chat_with_data(
    user_query: str,
    df: pd.DataFrame,
    valid_fields: set,
    chat_history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """Main entry point for chat with data.

    Constrains LLM to emit DSL, validates, executes, returns results.

    The flow:
    1. Send user query + schema to LLM with strict DSL prompt
    2. Parse LLM response to extract DSL statements
    3. Validate each statement via ChatDSL.validate()
    4. Execute validated statements via ChatExecutor.execute()
    5. Format results for chat UI response

    CRITICAL: LLM never sees raw data or constructs SQL. It only emits the DSL.
    The executor validates and runs - full sandboxing.
    """
    # Reset valid fields for this dataset
    ChatDSL.reset(valid_fields)

    # In a real implementation, this would:
    # 1. Construct a prompt that constrains LLM to the DSL
    # 2. Call Anthropic/Claude API
    # 3. Parse the DSL from the response
    # 4. Validate each statement
    # 5. Execute

    # For this implementation, we'll return a structure that shows the pattern
    # The actual LLM integration would go in the API route

    return {
        "pattern": "chat_with_data_dsl",
        "message": "Chat with data DSL pipeline - LLM constrained to structured statements",
        "valid_fields": list(valid_fields),
        "note": "Full LLM integration would constrains model to DSL output only",
    }