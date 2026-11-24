"""Expose a judgelab Judge as a DeepEval GEval-style metric.

The returned object has the minimal interface DeepEval drivers need:
    .name, .measure(test_case) -> float in [0,1], .score, .reason.
"""
from __future__ import annotations

from judgelab.judge import Judge, Verdict


def to_deepeval_metric(judge: Judge, name: str | None = None):
    """Return a DeepEval-compatible metric. Does not require deepeval installed."""
    class _JudgeMetric:
        def __init__(self):
            self.name = name or f"judgelab:{judge.name}"
            self.score: float = 0.0
            self.reason: str = ""
            self.threshold: float = 0.5
            self.success: bool = False

        def measure(self, test_case) -> float:
            prompt = getattr(test_case, "input", "") or ""
            a = getattr(test_case, "actual_output", "") or ""
            b = getattr(test_case, "expected_output", "") or ""
            if judge.mode == "pairwise":
                r = judge.pairwise(prompt, a, b)
                self.score = 1.0 if r.verdict == Verdict.A else (
                    0.0 if r.verdict == Verdict.B else 0.5
                )
                self.reason = f"judge verdict: {r.verdict.value if r.verdict else 'unknown'}"
            else:
                r = judge.pointwise(prompt, a)
                self.score = float(r.score or 0.0)
                self.reason = f"judge score: {self.score:.3f}"
            self.success = self.score >= self.threshold
            return self.score

        def is_successful(self) -> bool:
            return self.success

    return _JudgeMetric()
