"""Calibrate judge outputs against human labels.

Platt scaling for binary pairwise judges, isotonic regression for pointwise
scores, and threshold tuning for pass/fail judges.
"""
from judgelab.calibration.platt import PlattCalibrator
from judgelab.calibration.isotonic import IsotonicCalibrator
from judgelab.calibration.threshold import tune_threshold
from judgelab.calibration.reliability import reliability_curve, ece, render_reliability_svg

__all__ = [
    "PlattCalibrator",
    "IsotonicCalibrator",
    "tune_threshold",
    "reliability_curve",
    "ece",
    "render_reliability_svg",
]
