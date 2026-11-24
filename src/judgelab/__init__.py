"""judgelab — audit and calibrate LLM-as-judge pipelines."""
from judgelab.judge import Judge, JudgeResult, Verdict
from judgelab.dataset import AuditSuite, Example
from judgelab.labels import HumanLabels
from judgelab.report import Report
from judgelab.parallel import parallel_map
from judgelab.rubric import generate_rubric, RubricDraft
from judgelab.distill import DistilledJudge, distill
from judgelab.drift import DriftMonitor, DriftAlert

__version__ = "0.4.0"
__all__ = [
    "Judge",
    "JudgeResult",
    "Verdict",
    "AuditSuite",
    "Example",
    "HumanLabels",
    "Report",
    "parallel_map",
    "generate_rubric",
    "RubricDraft",
    "DistilledJudge",
    "distill",
    "DriftMonitor",
    "DriftAlert",
]
