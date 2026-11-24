"""Platt scaling: logistic regression mapping raw judge score -> calibrated
probability of human-preferred verdict.
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression


class PlattCalibrator:
    """Fits P(human=A | judge_score) via logistic regression.

    `judge_scores` should be continuous (e.g. judge's logit for A, or a
    confidence score). `human_labels` are 0/1 (or "A"/"B", auto-mapped).
    """

    def __init__(self):
        self._model: LogisticRegression | None = None

    def fit(self, judge_scores, human_labels) -> "PlattCalibrator":
        X = np.asarray(judge_scores, dtype=float).reshape(-1, 1)
        y = np.asarray([_to_int(v) for v in human_labels])
        if len(np.unique(y)) < 2:
            raise ValueError("Need both classes present in human_labels to fit Platt scaling")
        self._model = LogisticRegression(max_iter=1000)
        self._model.fit(X, y)
        return self

    def transform(self, judge_scores):
        if self._model is None:
            raise RuntimeError("Call fit() first.")
        X = np.asarray(judge_scores, dtype=float).reshape(-1, 1)
        return self._model.predict_proba(X)[:, 1]

    def params(self) -> dict:
        if self._model is None:
            return {}
        return {
            "coef": float(self._model.coef_[0, 0]),
            "intercept": float(self._model.intercept_[0]),
        }


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
