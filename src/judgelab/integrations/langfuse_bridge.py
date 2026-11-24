"""Push a judgelab Report to Langfuse as scores on an existing trace or as
standalone events. Requires langfuse installed.
"""
from __future__ import annotations

from judgelab.report import Report


def push_report_to_langfuse(report: Report, trace_id: str | None = None, client=None) -> dict:
    """Send numeric metrics from a Report to Langfuse as scores.

    Returns a dict of {metric_name: score_id} or raises if langfuse missing.
    """
    try:
        from langfuse import Langfuse
    except ImportError as e:
        raise ImportError("pip install langfuse") from e

    client = client or Langfuse()
    out: dict = {}
    for check, data in report.checks.items():
        if not isinstance(data, dict):
            continue
        for key, value in data.items():
            if not isinstance(value, (int, float)):
                continue
            name = f"judgelab.{check}.{key}"
            kwargs = {"name": name, "value": float(value)}
            if trace_id:
                kwargs["trace_id"] = trace_id
            score = client.score(**kwargs)
            out[name] = getattr(score, "id", None)
    return out
