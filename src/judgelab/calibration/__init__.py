"""Calibrate judge outputs against human labels.

Platt scaling for binary pairwise judges, isotonic regression for pointwise
scores, and threshold tuning for pass/fail judges.
"""
from judgelab.calibration.platt import PlattCalibrator
from judgelab.calibration.isotonic import IsotonicCalibrator
from judgelab.calibration.threshold import tune_threshold

__all__ = ["PlattCalibrator", "IsotonicCalibrator", "tune_threshold"]
