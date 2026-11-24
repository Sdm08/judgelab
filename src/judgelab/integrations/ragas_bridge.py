"""Thin wrapper letting a judgelab Judge stand in where Ragas expects a
critic callable: `fn(prompt, response) -> float in [0,1]` for pointwise or
`fn(prompt, a, b) -> int in {0,1}` for pairwise.
"""
from __future__ import annotations

from judgelab.judge import Judge, Verdict


def to_ragas_judge(judge: Judge):
    """Return a plain callable suitable for Ragas custom metrics."""
    if judge.mode == "pairwise":
        def fn(prompt: str, a: str, b: str) -> int:
            v = judge.pairwise(prompt, a, b).verdict
            return 1 if v == Verdict.A else 0
        return fn

    def fn(prompt: str, response: str) -> float:
        return float(judge.pointwise(prompt, response).score or 0.0)

    return fn
