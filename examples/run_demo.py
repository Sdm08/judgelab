"""Demo: audit a biased judge, show detection."""
import random
from pathlib import Path

from judgelab import AuditSuite, Judge

random.seed(0)


def biased_judge(prompt, a, b):
    if random.random() < 0.7:
        return "A"
    return "A" if len(a) > len(b) else "B"


judge = Judge.from_callable(biased_judge, name="mock-biased")

suite = AuditSuite.from_jsonl(Path(__file__).parent / "sample_dataset.jsonl")
report = suite.run(judge, checks=["position_bias", "verbosity_bias"])

print(report.to_json())
report.to_html(Path(__file__).parent / "report.html")
print("\nWrote report.html")
