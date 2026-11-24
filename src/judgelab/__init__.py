"""judgelab — audit and calibrate LLM-as-judge pipelines."""
from judgelab.judge import Judge, JudgeResult, Verdict
from judgelab.dataset import AuditSuite, Example
from judgelab.labels import HumanLabels
from judgelab.report import Report
from judgelab.parallel import parallel_map

__version__ = "0.3.0"
__all__ = [
    "Judge",
    "JudgeResult",
    "Verdict",
    "AuditSuite",
    "Example",
    "HumanLabels",
    "Report",
    "parallel_map",
]
