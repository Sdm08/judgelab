"""Judge distillation: wrap a small, cheap judge with a calibration layer
fitted against a bigger, trusted judge (or human labels).

Workflow:
    1. Collect pairs where both the big judge (or human) and small judge gave
       verdicts.
    2. Fit PlattCalibrator mapping small-judge score -> P(big-judge=A).
    3. Serve the small judge through DistilledJudge, which converts a verdict
       to a confidence score and returns a calibrated A/B/TIE verdict.
"""
from __future__ import annotations

from dataclasses import dataclass

from judgelab.calibration.platt import PlattCalibrator
from judgelab.judge import Judge, JudgeResult, Verdict


@dataclass
class DistilledJudge:
    small: Judge
    calibrator: PlattCalibrator
    tie_margin: float = 0.1
    name: str = "distilled"

    def predict(self, prompt: str, a: str, b: str) -> JudgeResult:
        raw = self.small.pairwise(prompt, a, b)
        raw_score = 1.0 if raw.verdict == Verdict.A else (0.0 if raw.verdict == Verdict.B else 0.5)
        p_a = float(self.calibrator.transform([raw_score])[0])
        if abs(p_a - 0.5) < self.tie_margin:
            v = Verdict.TIE
        else:
            v = Verdict.A if p_a >= 0.5 else Verdict.B
        return JudgeResult(verdict=v, score=p_a, raw=f"p_a={p_a:.3f}")

    def as_judge(self) -> Judge:
        return Judge.from_callable(
            lambda p, a, b: self.predict(p, a, b),
            mode="pairwise",
            name=self.name,
        )


def distill(
    small: Judge,
    teacher_labels: list,
    examples: list,
    tie_margin: float = 0.1,
    name: str = "distilled",
) -> DistilledJudge:
    """Fit a DistilledJudge from a small judge against teacher labels.

    teacher_labels[i] is "A" or "B" naming the teacher's winner.
    """
    if len(teacher_labels) != len(examples):
        raise ValueError("teacher_labels and examples must align")

    raw_scores = []
    cleaned_labels = []
    for ex, label in zip(examples, teacher_labels):
        if ex.response_a is None or ex.response_b is None:
            continue
        if label not in ("A", "B"):
            continue
        v = small.pairwise(ex.prompt, ex.response_a, ex.response_b).verdict
        if v is None:
            continue
        s = 1.0 if v == Verdict.A else (0.0 if v == Verdict.B else 0.5)
        raw_scores.append(s)
        cleaned_labels.append(label)

    cal = PlattCalibrator().fit(raw_scores, cleaned_labels)
    return DistilledJudge(small=small, calibrator=cal, tie_margin=tie_margin, name=name)
