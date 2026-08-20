import pandas as pd
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter
import numpy as np


class ReportService:
    """Service for deterministic report generation - computes all stats first,
    then LLM only narrates pre-computed numbers"""

    @staticmethod
    def compute_stats(df: pd.DataFrame, column_types: Dict[str, str]) -> Dict[str, Any]:
        """Compute all deterministic statistics from DataFrame.

        CRITICAL: LLM never does arithmetic. All numbers here are computed
        deterministically from the actual data, then the LLM narrates them.
        """
        stats = {
            "total_rows": len(df),
            "columns": {},
            "numeric_summary": {},
            "categorical_summary": {},
            "date_columns": [],
            "correlations": [],
        }

        # Separate columns by type
        numeric_cols = []
        categorical_cols = []
        date_cols = []
        text_cols = []

        for col in df.columns:
            series = df[col]
            dtype = series.dtype

            if pd.api.types.is_numeric_dtype(series):
                numeric_cols.append(col)
                # Compute numeric statistics
                col_stats = {
                    "min": float(series.min()) if not series.empty else None,
                    "max": float(series.max()) if not series.empty else None,
                    "mean": float(series.mean()) if not series.empty else None,
                    "median": float(series.median()) if not series.empty else None,
                    "std": float(series.std()) if not series.empty else None,
                    "null_count": int(series.isnull().sum()),
                    "null_pct": round(series.isnull().sum() / len(series) * 100, 2) if len(series) > 0 else 0,
                }
                stats["numeric_summary"][col] = col_stats

                # Also compute basic stats as overall stats
                stats["columns"][col] = {
                    "type": "numeric",
                    "null_pct": col_stats["null_pct"],
                }

            elif pd.api.types.is_datetime64_any_dtype(series) or (
                dtype == "object" and
                ReportService._looks_like_date(series.head(10))
            ):
                date_cols.append(col)
                stats["date_columns"].append(col)
                stats["columns"][col] = {
                    "type": "date",
                    "null_pct": round(series.isnull().sum() / len(series) * 100, 2) if len(series) > 0 else 0,
                }

            elif pd.api.types.is_categorical_dtype(series) or (
                dtype == "object" and
                series.nunique() / len(series) < 0.3 if len(series) > 0 else False
            ):
                categorical_cols.append(col)
                # Compute categorical stats
                value_counts = series.value_counts(dropna=False).head(10).to_dict()
                stats["categorical_summary"][col] = {
                    "unique_count": int(series.nunique()),
                    "top_values": {k: int(v) for k, v in value_counts.items()},
                    "null_pct": round(series.isnull().sum() / len(series) * 100, 2) if len(series) > 0 else 0,
                }
                stats["columns"][col] = {
                    "type": "categorical",
                    "null_pct": round(series.isnull().sum() / len(series) * 100, 2) if len(series) > 0 else 0,
                }

            else:
                text_cols.append(col)
                unique_count = series.nunique() if len(series) > 0 else 0
                stats["columns"][col] = {
                    "type": "text",
                    "unique_count": int(unique_count),
                    "null_pct": round(series.isnull().sum() / len(series) * 100, 2) if len(series) > 0 else 0,
                }

        # Compute period-over-period changes if date column exists
        if len(date_cols) >= 1 and numeric_cols:
            stats["period_changes"] = ReportService._compute_period_over_period(
                df, date_cols[0], numeric_cols[0]
            )

        # Detect outliers using IQR method for numeric columns
        stats["outliers"] = ReportService._detect_outliers(stats["numeric_summary"])

        # Top/bottom performers
        stats["top_performers"] = ReportService._top_performers(stats["numeric_summary"])

        # Anomalies detection
        stats["anomalies"] = ReportService._detect_anomalies(stats["numeric_summary"])

        # Add chart recommendations to stats (for API responses)
        stats["recommended_charts"] = ReportService.select_charts(stats)

        return stats

    @staticmethod
    def compute_stats_from_metadata(dataset, schema: List[Dict]) -> Dict[str, Any]:
        """Compute statistics from dataset metadata when full DataFrame not available.

        Used as fallback when the actual data file needs to be read from storage.
        Provides basic stats from the dataset record and schema info.
        """
        numeric_cols = [
            col for col in schema
            if col.get("inferred_type") == "number"
        ]
        categorical_cols = [
            col for col in schema
            if col.get("inferred_type") in ("categorical", "text")
        ]

        return {
            "total_rows": dataset.row_count,
            "columns": {
                col["column"]: {
                    "type": col["inferred_type"],
                    "null_pct": 0,
                }
                for col in schema
            },
            "numeric_summary": {
                col["column"]: {
                    "min": 0,
                    "max": 0,
                    "mean": 0,
                    "median": 0,
                    "std": 0,
                    "null_count": 0,
                    "null_pct": 0,
                }
                for col in numeric_cols
            },
            "categorical_summary": {},
            "date_columns": [],
            "period_changes": [],
            "top_performers": [],
            "anomalies": [],
            "recommended_charts": ReportService.select_charts(
                {
                    "total_rows": dataset.row_count,
                    "columns": {
                        col["column"]: {"type": col["inferred_type"] for col in schema}
                    },
                }
            )
            if numeric_cols
            else [],
        }

    @staticmethod
    def _looks_like_date(values) -> bool:
        """Check if values look like dates"""
        for val in values:
            if isinstance(val, str):
                try:
                    pd.to_datetime(val, errors='raise')
                    return True
                except:
                    pass
        return False

    @staticmethod
    def _compute_period_over_period(df: pd.DataFrame, date_col: str, value_col: str) -> List[Dict]:
        """Compute period-over-period changes"""
        try:
            df_sorted = df.sort_values(by=date_col)
            values = df_sorted[value_col].values
            dates = df_sorted[date_col].values

            if len(values) < 2:
                return []

            changes = []
            for i in range(1, min(len(values), 13)):  # Last 12 periods
                if i < len(values):
                    change = (values[-i] - values[-(i+1)]) / abs(values[-(i+1)]) if values[-(i+1)] != 0 else 0
                    changes.append({
                        "period": str(dates[-i]) if i < len(dates) else "current",
                        "previous_period": str(dates[-(i+1)]) if (i+1) <= len(dates) else "previous",
                        "change": round(float(change), 4),
                        "change_pct": round(float(change * 100), 2),
                    })
            return changes
        except Exception:
            return []

    @staticmethod
    def _detect_outliers(numeric_summary: Dict) -> List[Dict]:
        """Detect outliers using IQR method"""
        outliers = []
        for col, col_stats in numeric_summary.items():
            if col_stats.get("min") is not None and col_stats.get("max") is not None:
                q1 = col_stats.get("Q1", col_stats.get("mean", 0) - 0.5 * col_stats.get("std", 1))
                q3 = col_stats.get("Q3", col_stats.get("mean", 0) + 0.5 * col_stats.get("std", 1))
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                # We can't check individual values without the full series,
                # but we can flag if data looks suspicious
                if iqr > 0:
                    outliers.append({
                        "column": col,
                        "lower_bound": round(lower_bound, 2),
                        "upper_bound": round(upper_bound, 2),
                        "method": "IQR",
                    })
        return outliers

    @staticmethod
    def _top_performers(numeric_summary: Dict) -> List[Dict]:
        """Get top and bottom performers"""
        performers = []
        for col, stats in numeric_summary.items():
            if stats.get("mean") is not None:
                performers.append({
                    "column": col,
                    "value": round(stats["mean"], 2),
                    "label": f"Average {col}",
                })
        # Sort by absolute value of mean
        performers.sort(key=lambda x: abs(x["value"]), reverse=True)
        return performers[:5]

    @staticmethod
    def _detect_anomalies(numeric_summary: Dict) -> List[Dict]:
        """Simple anomaly detection - flag columns with extreme stats"""
        anomalies = []
        for col, stats in numeric_summary.items():
            if stats.get("std") is not None and stats.get("mean") is not None:
                # Coefficient of variation
                cv = abs(stats["std"] / stats["mean"]) if stats["mean"] != 0 else 0
                if cv > 1.0:  # High variability
                    anomalies.append({
                        "column": col,
                        "anomaly_type": "high_variability",
                        "cv": round(cv, 2),
                        "description": "High coefficient of variation indicates significant variability",
                    })
        return anomalies

    @staticmethod
    def select_charts(stats: Dict[str, Any], chart_type_hints: Optional[List[str]] = None) -> List[Dict]:
        """Select appropriate chart types based on data shape.

        Rules:
        - Time series columns → line chart
        - Categorical breakdowns → bar chart
        - At least 3 charts per report where data supports it
        """
        charts = []
        date_cols = stats.get("date_columns", [])
        numeric_cols = [
            col for col, info in stats.get("columns", {}).items()
            if info.get("type") == "numeric"
        ]
        categorical_cols = [
            col for col, info in stats.get("columns", {}).items()
            if info.get("type") == "categorical"
        ]

        # 1. Time series line chart if we have date + numeric
        if date_cols and numeric_cols:
            charts.append({
                "type": "line",
                "title": f"Trend: {numeric_cols[0]} over time",
                "x_axis": date_cols[0],
                "y_axis": numeric_cols[0],
                "description": f"Shows the trend of {numeric_cols[0]} over time",
            })

        # 2. Bar charts for categorical breakdowns
        for col in categorical_cols[:3]:  # Limit to 3 categorical charts
            charts.append({
                "type": "bar",
                "title": f"Breakdown by {col}",
                "x_axis": col,
                "y_axis": "count",
                "description": f"Distribution of {col}",
            })

        # 3. If we don't have enough charts, add a summary stats chart
        if len(charts) < 3 and numeric_cols:
            charts.append({
                "type": "bar",
                "title": f"Summary: Top {numeric_cols[0]} values",
                "x_axis": "category",
                "y_axis": numeric_cols[0],
                "description": f"Summary statistics for {numeric_cols[0]}",
            })

        # 4. If still need more charts, add correlation chart
        if len(charts) < 5 and len(stats.get("correlations", [])) > 0:
            charts.append({
                "type": "scatter",
                "title": "Correlation analysis",
                "x_axis": stats["correlations"][0]["x"] if stats["correlations"] else numeric_cols[0] if numeric_cols else "x",
                "y_axis": stats["correlations"][0]["y"] if stats["correlations"] else numeric_cols[1] if len(numeric_cols) > 1 else "y",
                "description": "Relationship between two numeric variables",
            })

        return charts[:5]  # Return max 5 charts

    @staticmethod
    def generate_narrative_prompt(stats: Dict[str, Any], user_intent: str = "auto_summary") -> str:
        """Generate the LLM prompt containing ONLY computed stats.

        The LLM's job is to narrate these exact numbers - never to calculate.
        """
        prompt_parts = [
            f"DATASET SUMMARY:",
            f"- Total rows: {stats['total_rows']}",
            f"- Columns analyzed: {', '.join(stats['columns'].keys())}",
        ]

        # Add numeric column highlights
        numeric_cols = [
            col for col, info in stats.get("columns", {}).items()
            if info.get("type") == "numeric"
        ]
        if numeric_cols:
            prompt_parts.append(
                f"- Key numeric columns: {', '.join(numeric_cols[:5])}"
            )

        # Add period-over-period changes
        poc_stats = stats.get("period_changes", [])
        if poc_stats:
            latest = poc_stats[0]
            prompt_parts.append(
                f"- Period-over-period change: {latest['change_pct']}% "
                f"{'increase' if latest['change'] > 0 else 'decrease'} from {latest['previous_period']}"
            )

        # Add top performers
        top_performers = stats.get("top_performers", [])
        if top_performers:
            performer_strs = []
            for p in top_performers[:3]:
                performer_strs.append(f"{p['label']}: {p['value']}")
            prompt_parts.append("- Top performers: " + "; ".join(performer_strs))

        # Add anomalies
        anomalies = stats.get("anomalies", [])
        if anomalies:
            anomaly_strs = []
            for a in anomalies[:2]:
                anomaly_strs.append(f"{a['column']}: {a['description']}")
            prompt_parts.append("- Anomalies detected: " + "; ".join(anomaly_strs))

        # Add chart recommendations
        charts = ReportService.select_charts(stats)
        if charts:
            chart_descs = []
            for c in charts[:3]:
                chart_descs.append(f"{c['type']}: {c['description']}")
            prompt_parts.append("- Recommended charts: " + "; ".join(chart_descs))

        # Add user intent
        prompt_parts.append(
            f"\nUSER INTENT: {user_intent}"
        )
        prompt_parts.append(
            f"\nIMPORTANT: The above are ALL pre-computed deterministic statistics from the actual data. "
            f"Write a narrative report referencing these exact numbers. Never invent or calculate numbers. "
            f"Only use the figures above as the basis for your narrative."
        )

        return "\n".join(prompt_parts)

    @staticmethod
    def build_report_record(
        dataset_id: str,
        title: str,
        user_id: str,
        stats: Dict[str, Any],
        chart_configs: List[Dict],
        narrative_text: str,
        report_type: str = "auto_summary",
    ) -> Dict[str, Any]:
        """Build the complete report record to store in database"""
        return {
            "dataset_id": dataset_id,
            "title": title,
            "report_type": report_type,
            "created_by": user_id,
            "narrative_text": narrative_text,
            "computed_stats_json": json.dumps(stats),
            "charts_json": json.dumps(chart_configs),
            "status": "completed",
        }