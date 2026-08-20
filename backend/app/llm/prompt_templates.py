"""LLM prompt templates for report generation.

CRITICAL RULE: These prompts contain ONLY pre-computed deterministic statistics.
The LLM's job is to NARRATE these exact numbers - NEVER to calculate, compute,
or invent new values. All arithmetic must be done in the compute_stats() step
before the LLM sees the data.
"""


def auto_summary_prompt(stats: dict, user_intent: str = "auto_summary") -> str:
    """Generate prompt for auto-generated summary report.

    The LLM must only reference numbers from computed_stats_json.
    """
    lines = [
        "TASK: Write a concise business summary report based on the dataset.",
        "",
        "DATASET OVERVIEW:",
        f"- Total records: {stats['total_rows']}",
        f"- Columns: {', '.join(stats['columns'].keys())}",
        "",
    ]

    # Numeric column highlights
    numeric_cols = [
        col for col, info in stats.get("columns", {}).items()
        if info.get("type") == "numeric"
    ]
    if numeric_cols:
        lines.append("KEY METRICS:")
        for col in numeric_cols[:5]:
            col_stats = stats.get("numeric_summary", {}).get(col, {})
            if col_stats:
                label = col.replace("_", " ").title()
                lines.append(
                    f"  - {label}: {col_stats.get('mean', col_stats.get('median', 'N/A'))} "
                    f"(range: {col_stats.get('min', '?')} to {col_stats.get('max', '?')})"
                )

    # Period-over-period changes
    poc = stats.get("period_changes", [])
    if poc:
        latest = poc[0]
        direction = "increased" if latest["change"] > 0 else "decreased"
        lines.append(
            f"TREND: The metric has {direction} by {latest['change_pct']}% "
            f"compared to {latest['previous_period']}."
        )

    # Top performers
    top = stats.get("top_performers", [])
    if top:
        performer_descs = []
        for p in top[:3]:
            label = p["label"].replace("_", " ").title()
            performer_descs.append(f"{label}: {p['value']}")
        lines.append("TOP PERFORMERS: " + "; ".join(performer_descs))

    # Anomalies
    anomalies = stats.get("anomalies", [])
    if anomalies:
        anomaly_descs = []
        for a in anomalies[:2]:
            anomaly_descs.append(a["description"])
        lines.append("ANOMALIES: " + "; ".join(anomaly_descs))

    # Chart recommendations
    charts = stats.get("recommended_charts", [])
    if charts:
        chart_lines = []
        for c in charts[:3]:
            chart_lines.append(f"- {c['description']}")
        lines.append("CHART RECOMMENDATIONS: " + "; ".join(chart_lines))

    # User intent
    lines.append(
        f"\nUSER INTENT: {user_intent}"
    )
    lines.append(
        "\nCRITICAL: The statistics above are ALL pre-computed from the actual data. "
        "Write the narrative using ONLY these exact numbers. Do not calculate, estimate, "
        "or invent any new figures. If the data suggests a trend or pattern not reflected "
        "in the stats above, note that the stats do not capture that observation rather "
        "than inventing a number."
    )

    return "\n".join(lines)


def scheduled_report_prompt(stats: dict, frequency: str = "weekly") -> str:
    """Generate prompt for scheduled/repeated reports.

    Compares current stats to previous period's stats if available.
    """
    lines = [
        f"TASK: Generate a {frequency} business report based on the dataset.",
        "",
        "CURRENT PERIOD DATA:",
        f"- Total records: {stats['total_rows']}",
        f"- Key metrics overview: {', '.join(stats['columns'].keys())}",
        "",
    ]

    # Period-over-period changes (compare to prior period)
    poc = stats.get("period_changes", [])
    if poc:
        latest = poc[0]
        direction = "increase" if latest["change"] > 0 else "decrease"
        lines.append(
            f"PERIOD COMPARISON: The key metric {direction} by {latest['change_pct']}% "
            f"from the previous period ({latest['previous_period']})."
        )
    else:
        lines.append(
            "PERIOD COMPARISON: No prior-period comparison data available."
        )

    # Top performers
    top = stats.get("top_performers", [])
    if top:
        performer_descs = []
        for p in top[:3]:
            label = p["label"].replace("_", " ").title()
            performer_descs.append(f"{label}: {p['value']}")
        lines.append("TOP PERFORMERS: " + "; ".join(performer_descs))

    # Anomalies
    anomalies = stats.get("anomalies", [])
    if anomalies:
        anomaly_descs = []
        for a in anomalies[:2]:
            anomaly_descs.append(a["description"])
        lines.append("ANOMALIES: " + "; ".join(anomaly_descs))

    # Chart recommendations
    charts = stats.get("recommended_charts", [])
    if charts:
        chart_lines = []
        for c in charts[:3]:
            chart_lines.append(f"- {c['description']}")
        lines.append("CHART RECOMMENDATIONS: " + "; ".join(chart_lines))

    lines.append(
        f"\nREPORT FREQUENCY: {frequency}"
    )
    lines.append(
        "\nCRITICAL: All numbers above are pre-computed from the actual data. "
        "Only reference these exact figures. Never calculate new percentages, "
        "totals, or averages. If the data has changed since the last report, "
        "reference only what is in the stats above."
    )

    return "\n".join(lines)


def forecast_report_prompt(stats: dict, forecast_data: dict = None) -> str:
    """Generate prompt for forecast-focused reports.

    Includes forecast results if available, but LLM only narrates the
    pre-computed forecast statistics.
    """
    lines = [
        "TASK: Write a report summarizing the time-series forecast results.",
        "",
        "DATASET OVERVIEW:",
        f"- Total records: {stats['total_rows']}",
        f"- Analyzed columns: {', '.join(stats['columns'].keys())}",
        "",
    ]

    # Forecast-specific stats
    if forecast_data:
        f = forecast_data
        lines.append("FORECAST SUMMARY:")
        lines.append(
            f"- Forecast horizon: {f.get('horizon_periods', 'N/A')} periods"
        )
        lines.append(
            f"- Model used: {f.get('model_type', 'N/A')}"
        )
        if "latest_forecast" in f:
            latest = f["latest_forecast"]
            lines.append(
                f"- Forecasted value for next period: {latest.get('predicted_value', 'N/A')}"
            )
            if "confidence_interval" in latest:
                ci = latest["confidence_interval"]
                lines.append(
                    f"- Confidence interval: [{ci.get('lower', '?')}, {ci.get('upper', '?')}]"
                )

    # Top performers / trends
    top = stats.get("top_performers", [])
    if top:
        performer_descs = []
        for p in top[:3]:
            label = p["label"].replace("_", " ").title()
            performer_descs.append(f"{label}: {p['value']}")
        lines.append("TRENDS: " + "; ".join(performer_descs))

    # Period changes
    poc = stats.get("period_changes", [])
    if poc:
        latest = poc[0]
        direction = "increase" if latest["change"] > 0 else "decrease"
        lines.append(
            f"TREND: The metric has {direction} by {latest['change_pct']}% "
            f"over the observed period."
        )

    lines.append(
        "\nCRITICAL: All figures above are pre-computed from the actual data and "
        "forecast model output. The LLM must only narrate these exact numbers. "
        "Never extend forecasts, adjust confidence intervals, or calculate new "
        "trend percentages. If the narrative requires context not in the stats, "
        "state that the available statistics do not cover that aspect."
    )

    return "\n".join(lines)


def executive_summary_prompt(stats: dict, focus_areas: list = None) -> str:
    """Generate prompt for executive summary report.

    Focuses on high-level insights and key takeaways for leadership.
    """
    lines = [
        "TASK: Write an executive summary for leadership reviewing this dataset.",
        "",
        "DATASET SNAPSHOT:",
        f"- Total records: {stats['total_rows']}",
        f"- Primary analyzed columns: {', '.join(stats['columns'].keys())}",
        "",
    ]

    # Numeric highlights
    numeric_cols = [
        col for col, info in stats.get("columns", {}).items()
        if info.get("type") == "numeric"
    ]
    if numeric_cols:
        lines.append("KEY FINDINGS:")
        for col in numeric_cols[:3]:
            col_stats = stats.get("numeric_summary", {}).get(col, {})
            if col_stats:
                label = col.replace("_", " ").title()
                avg = col_stats.get("mean", col_stats.get("median", 0))
                lines.append(
                    f"- {label}: averaging {avg} across {stats['total_rows']} records"
                )

    # Top performers
    top = stats.get("top_performers", [])
    if top:
        performer_descs = []
        for p in top[:3]:
            label = p["label"].replace("_", " ").title()
            performer_descs.append(f"{label}: {p['value']}")
        lines.append("TOP CONTRIBUTORS: " + "; ".join(performer_descs))

    # Trends
    poc = stats.get("period_changes", [])
    if poc:
        latest = poc[0]
        direction = "growth" if latest["change"] > 0 else "decline"
        lines.append(
            f"OVERALL TREND: The data shows {direction} of {latest['change_pct']}% "
            f"over the reporting period."
        )

    # Anomalies
    anomalies = stats.get("anomalies", [])
    if anomalies:
        anomaly_descs = []
        for a in anomalies[:2]:
            anomaly_descs.append(a["description"])
        lines.append("NOTABLE ANOMALIES: " + "; ".join(anomaly_descs))

    # Focus areas if provided
    if focus_areas:
        lines.append("FOCUS AREAS: " + "; ".join(focus_areas))

    lines.append(
        "\nCRITICAL: All numbers above are pre-computed deterministic statistics. "
        "Reference only these exact figures. Do not calculate ratios, percentages, "
        "or new metrics. If the data supports inferences not captured in the stats, "
        "frame them as observations rather than stated numbers."
    )

    return "\n".join(lines)


def comparison_report_prompt(current_stats: dict, prior_stats: dict, focus: str = "overall") -> str:
    """Generate prompt for comparison reports (current vs prior period).

    Both sets of stats are pre-computed. LLM only references the diff.
    """
    lines = [
        f"TASK: Compare the current period against the prior period and write a summary report.",
        "",
        "COMPARISON CONTEXT:",
        f"- Comparison focus: {focus}",
        f"- Current period records: {current_stats['total_rows']}",
        f"- Prior period records: {prior_stats['total_rows']}",
        "",
    ]

    # Period-over-period changes from both
    current_poc = current_stats.get("period_changes", [])
    prior_poc = prior_stats.get("period_changes", [])

    if current_poc and prior_poc:
        curr = current_poc[0]
        prior = prior_poc[0]
        curr_dir = "increase" if curr["change"] > 0 else "decrease"
        prior_dir = "increase" if prior["change"] > 0 else "decrease"
        lines.append(
            f"PERIOD TREND: Current period {curr_dir} by {curr['change_pct']}% "
            f"vs prior period {prior_dir} by {abs(prior['change_pct'])}%."
        )
    elif current_poc:
        curr = current_poc[0]
        direction = "increase" if curr["change"] > 0 else "decrease"
        lines.append(
            f"PERIOD TREND: Current period {direction} by {curr['change_pct']}%. "
            "No prior-period data available for comparison."
        )
    elif prior_poc:
        prior = prior_poc[0]
        direction = "increase" if prior["change"] > 0 else "decrease"
        lines.append(
            f"PERIOD TREND: Prior period {direction} by {abs(prior['change_pct'])}%. "
            "No current-period comparison data available."
        )

    # Diff top performers
    curr_top = current_stats.get("top_performers", [])
    prior_top = prior_stats.get("top_performers", [])

    if curr_top and prior_top:
        lines.append("TOP PERFORMERS CHANGE:")
        # Simple diff: if same column appears in both
        curr_labels = {p["column"]: p["label"] for p in curr_top[:3]}
        prior_labels = {p["column"]: p["label"] for p in prior_top[:3]}
        for col in set(curr_labels.keys()) | set(prior_labels.keys()):
            curr_val = next(
                (p["value"] for p in curr_top if p["column"] == col), "N/A"
            )
            prior_val = next(
                (p["value"] for p in prior_top if p["column"] == col), "N/A"
            )
            label = col.replace("_", " ").title()
            change_pct = (
                (curr_val - prior_val) / abs(prior_val) * 100
                if prior_val != 0 and curr_val != "N/A" and prior_val != "N/A"
                else "N/A"
            )
            lines.append(
                f"- {label}: {curr_val} (vs {prior_val}, {change_pct:.1f}% change)"
            )

    # Anomalies comparison
    curr_anomalies = current_stats.get("anomalies", [])
    prior_anomalies = prior_stats.get("anomalies", [])

    if curr_anomalies or prior_anomalies:
        anomaly_descs = []
        if curr_anomalies:
            for a in curr_anomalies[:1]:
                anomaly_descs.append(f"Current: {a['description']}")
        if prior_anomalies:
            for a in prior_anomalies[:1]:
                anomaly_descs.append(f"Prior: {a['description']}")
        lines.append("ANOMALY COMPARISON: " + "; ".join(anomaly_descs))

    lines.append(
        "\nCRITICAL: All numbers above are pre-computed from their respective periods. "
        "The LLM must only reference these exact figures. Never calculate differences, "
        "percentages, or new metrics from the raw data. If computing a difference between "
        "periods, reference only the change_pct values provided above, and never derive "
        "them through arithmetic on the stated numbers."
    )

    return "\n".join(lines)