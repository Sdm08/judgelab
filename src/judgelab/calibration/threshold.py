"""Threshold tuning: pick the judge score cutoff that maximises a metric
(accuracy, F1, or Cohen's kappa) against human labels.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score


@dataclass
class ThresholdResult:
    threshold: float
    metric: str
    score: float


def tune_threshold(
    judge_scores,
    human_labels,
    metric: str = "accuracy",
    n_candidates: int = 101,
) -> ThresholdResult:
    scores = np.asarray(judge_scores, dtype=float)
    y = np.asarray([_to_int(v) for v in human_labels])
    if len(np.unique(y)) < 2:
        raise ValueError("Need both classes present in human_labels")

    lo, hi = float(scores.min()), float(scores.max())
    candidates = np.linspace(lo, hi, n_candidates)

    fn = {
        "accuracy": lambda yt, yp: accuracy_score(yt, yp),
        "f1": lambda yt, yp: f1_score(yt, yp, zero_division=0),
        "kappa": lambda yt, yp: cohen_kappa_score(yt, yp),
    }
    if metric not in fn:
        raise ValueError(f"metric must be one of {list(fn)}")

    best = ThresholdResult(threshold=candidates[0], metric=metric, score=-float("inf"))
    for t in candidates:
        preds = (scores >= t).astype(int)
        s = fn[metric](y, preds)
        if s > best.score:
            best = ThresholdResult(threshold=float(t), metric=metric, score=float(s))
    return best


def _to_int(v) -> int:
    import numbers
    if isinstance(v, str):
        up = v.upper()
        if up == "A":
            return 1
        if up == "B":
            return 0
        raise ValueError(f"Cannot map label {v!r} to 0/1")
    if isinstance(v, numbers.Integral):
        return int(v)
    if isinstance(v, numbers.Real):
        return int(float(v) >= 0.5)
    raise ValueError(f"Cannot map label {v!r} to 0/1")
