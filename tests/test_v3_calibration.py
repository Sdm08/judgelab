"""Tests for v0.3 calibration + parallel helpers."""
import numpy as np
import pytest

from judgelab.calibration import PlattCalibrator, IsotonicCalibrator, tune_threshold
from judgelab.parallel import parallel_map


def test_platt_calibrator_learns_monotonic_mapping():
    rng = np.random.default_rng(0)
    scores = rng.normal(size=200)
    labels = (scores > 0).astype(int)
    cal = PlattCalibrator().fit(scores, labels)
    probs = cal.transform([-2, 0, 2])
    assert probs[0] < probs[1] < probs[2]
    assert 0 < probs[0] < 1 and 0 < probs[2] < 1


def test_platt_requires_both_classes():
    with pytest.raises(ValueError):
        PlattCalibrator().fit([1, 2, 3], [1, 1, 1])


def test_isotonic_calibrator_monotone():
    x = [0.1, 0.2, 0.3, 0.4, 0.5]
    y = [0.0, 0.1, 0.5, 0.8, 1.0]
    cal = IsotonicCalibrator().fit(x, y)
    out = cal.transform(x)
    # non-decreasing
    assert all(out[i] <= out[i + 1] for i in range(len(out) - 1))


def test_tune_threshold_accuracy():
    scores = [0.1, 0.2, 0.3, 0.7, 0.8, 0.9]
    labels = [0, 0, 0, 1, 1, 1]
    res = tune_threshold(scores, labels, metric="accuracy")
    assert res.score == 1.0
    assert 0.3 <= res.threshold <= 0.7


def test_tune_threshold_bad_metric():
    with pytest.raises(ValueError):
        tune_threshold([0.1, 0.9], [0, 1], metric="bogus")


def test_parallel_map_preserves_order():
    out = parallel_map(lambda x: x * 2, range(20), workers=4)
    assert out == [i * 2 for i in range(20)]


def test_parallel_map_single_worker_fallback():
    out = parallel_map(lambda x: x + 1, [10], workers=1)
    assert out == [11]


def test_parallel_map_propagates_exceptions():
    def boom(x):
        if x == 3:
            raise RuntimeError("nope")
        return x
    with pytest.raises(RuntimeError):
        parallel_map(boom, range(5), workers=2)
