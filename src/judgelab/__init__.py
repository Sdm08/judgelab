"""judgelab — audit and calibrate LLM-as-judge pipelines."""
from judgelab.judge import Judge, JudgeResult, Verdict
from judgelab.dataset import AuditSuite, Example
from judgelab.labels import HumanLabels
from judgelab.report import Report

__version__ = "0.1.0"
__all__ = [
    "Judge",
    "JudgeResult",
    "Verdict",
    "AuditSuite",
    "Example",
    "HumanLabels",
    "Report",
]
