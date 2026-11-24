"""Isotonic regression: monotonic non-parametric mapping of judge pointwise
scores to human scores. Useful when judge scores are on a different scale or
compressed.
"""
from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression


class IsotonicCalibrator:
    def __init__(self, out_of_bounds: str = "clip"):
        self._model = IsotonicRegression(out_of_bounds=out_of_bounds)

    def fit(self, judge_scores, human_scores) -> "IsotonicCalibrator":
        X = np.asarray(judge_scores, dtype=float)
        y = np.asarray(human_scores, dtype=float)
        if len(X) < 2:
            raise ValueError("Need >=2 points")
        self._model.fit(X, y)
        return self

    def transform(self, judge_scores):
        X = np.asarray(judge_scores, dtype=float)
        return self._model.transform(X)
