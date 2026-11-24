"""Push judgelab Reports to Langfuse as scores, linked to a trace.

Supports two modes:
  - Scores attached to an existing trace_id (score-only).
  - Create a dedicated judgelab-audit trace carrying the HTML report as
    an observation plus one score per numeric metric. Returns the new
    trace_id so callers can link back.
"""
from __future__ import annotations

import json

from judgelab.report import Report


def push_report_to_langfuse(
    report: Report,
    trace_id: str | None = None,
    client=None,
    create_trace: bool = False,
    dataset: str | None = None,
) -> dict:
    """Send numeric metrics from a Report to Langfuse as scores.

    If `trace_id` given: scores attach to that trace.
    If `create_trace=True` and no `trace_id`: creates a new 'judgelab-audit'
    trace with the full report JSON as input and the HTML as output, and
    attaches scores to it.
    Returns dict with 'trace_id' and 'scores' (metric_name -> score_id).
    """
    try:
        from langfuse import Langfuse
    except ImportError as e:
        raise ImportError("pip install langfuse") from e

    client = client or Langfuse()

    new_trace_id = trace_id
    if create_trace and not trace_id:
        trace = client.trace(
            name="judgelab-audit",
            input={"judge": report.judge_name, "n_examples": report.n_examples, "dataset": dataset},
            output=json.loads(report.to_json()),
            tags=["judgelab", "audit"],
        )
        new_trace_id = getattr(trace, "id", None)

    scores: dict = {}
    for check, data in report.checks.items():
        if not isinstance(data, dict):
            continue
        for key, value in data.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            name = f"judgelab.{check}.{key}"
            kwargs = {"name": name, "value": float(value)}
            if new_trace_id:
                kwargs["trace_id"] = new_trace_id
            comment = data.get("interpretation")
            if comment:
                kwargs["comment"] = comment
            score = client.score(**kwargs)
            scores[name] = getattr(score, "id", None)

    return {"trace_id": new_trace_id, "scores": scores}
