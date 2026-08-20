"""Celery task for report generation and export.

The task pipeline is deterministic: stats are computed first, then a
narrative is written strictly from those numbers (see ReportService).
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from celery import shared_task

from app.database import SessionLocal
from app.models.dataset import Dataset
from app.models.report import Report
from app.services.report_service import ReportService


@shared_task(bind=True, max_retries=3)
def generate_report_task(
    self,
    dataset_id: str,
    title: str,
    user_id: str,
    report_type: str = "auto_summary",
    export_format: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a business report for a dataset and persist it."""
    session = SessionLocal()
    try:
        dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

        schema = json.loads(dataset.schema_json) if dataset.schema_json else []
        stats = ReportService.compute_stats_from_metadata(dataset, schema)
        chart_configs = ReportService.select_charts(stats)
        narrative_text = _generate_narrative(stats, report_type)
        export_result = None
        if export_format == "pdf":
            export_result = _render_pdf(stats, chart_configs, narrative_text)
        elif export_format == "docx":
            export_result = _render_docx(stats, chart_configs, narrative_text)

        report = Report(
            org_id=dataset.org_id,
            dataset_id=dataset_id,
            created_by=user_id,
            title=title,
            report_type=report_type,
            narrative_text=narrative_text,
            computed_stats_json=json.dumps(stats),
            charts_json=json.dumps(chart_configs),
            status="completed",
            export_format=export_format,
            export_result=json.dumps(export_result) if export_result else None,
            generated_at=datetime.utcnow(),
        )
        session.add(report)
        session.commit()
        session.refresh(report)

        return {
            "report_id": report.id,
            "title": report.title,
            "status": report.status,
            "charts_count": len(chart_configs),
            "narrative_length": len(narrative_text),
        }
    except Exception as exc:
        session.rollback()
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
    finally:
        session.close()


def _generate_narrative(stats: dict, report_type: str = "auto_summary") -> str:
    """Write a short narrative using ONLY numbers present in stats."""
    lines = []
    total = stats.get("total_rows", 0)
    numeric = stats.get("numeric_summary", {})
    categorical = stats.get("categorical_summary", {})

    prefix = "Executive summary: " if report_type == "executive" else ""
    if numeric:
        first_col, col_stats = next(iter(numeric.items()))
        if col_stats.get("mean") is not None:
            lines.append(
                f"{prefix}This report covers {total} records. The average value of "
                f"{first_col} is {col_stats['mean']:.2f}, ranging from "
                f"{col_stats['min']:.2f} to {col_stats['max']:.2f}."
            )
        if col_stats.get("null_pct", 0) > 0:
            lines.append(f"{col_stats['null_pct']:.1f}% of values in {first_col} are missing.")
    else:
        lines.append(f"This report covers {total} records with no numeric columns detected.")

    top_col = next(iter(categorical.items()), None)
    if top_col:
        col, cat_stats = top_col
        top_values = cat_stats.get("top_values", {})
        if top_values:
            mode, mode_count = next(iter(top_values.items()))
            lines.append(
                f"The most common value in {col} is '{mode}' "
                f"({mode_count} of {total} records)."
            )

    anomalies = stats.get("anomalies", [])
    if anomalies:
        lines.append(
            f"Watch-outs: {len(anomalies)} column(s) flagged for high variability"
            f" ({', '.join(a['column'] for a in anomalies[:3])})."
        )
    else:
        lines.append("No significant anomalies detected in the data.")

    return "\n".join(lines)


def _render_pdf(
    stats: dict,
    chart_configs: list,
    narrative_text: str,
) -> dict:
    """Render report to PDF.

    ponytail: full PDF layout (WeasyPrint/HTML) is a later upgrade;
    returning a placeholder keeps the export endpoint functional.
    """
    return {
        "format": "pdf",
        "status": "placeholder",
        "message": "PDF generation would use WeasyPrint with an HTML template",
    }


def _render_docx(
    stats: dict,
    chart_configs: list,
    narrative_text: str,
) -> dict:
    """Render report to DOCX.

    ponytail: full DOCX layout (python-docx) is a later upgrade.
    """
    return {
        "format": "docx",
        "status": "placeholder",
        "message": "DOCX generation would use python-docx with a formatted template",
    }
