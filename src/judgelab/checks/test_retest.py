"""Test-retest reliability: run the judge N times on identical input and
measure verdict stability (pairwise) or score variance (pointwise).
"""
from __future__ import annotations

import statistics

from judgelab.judge import Judge


def run(examples, judge: Judge, repeats: int = 3, max_pairs: int = 30, **_) -> dict:
    if repeats < 2:
        return {"error": "repeats must be >= 2"}

    stabilities = []
    variances = []

    for ex in examples[:max_pairs]:
        if judge.mode == "pairwise":
            if ex.response_a is None or ex.response_b is None:
                continue
            verdicts = []
            for _ in range(repeats):
                v = judge.pairwise(ex.prompt, ex.response_a, ex.response_b).verdict
                verdicts.append(v.value if v else None)
            clean = [v for v in verdicts if v is not None]
            if not clean:
                continue
            # fraction equal to mode
            mode = max(set(clean), key=clean.count)
            stabilities.append(clean.count(mode) / len(clean))
        else:
            if ex.response is None:
                continue
            scores = []
            for _ in range(repeats):
                s = judge.pointwise(ex.prompt, ex.response).score
                if s is not None:
                    scores.append(s)
            if len(scores) < 2:
                continue
            variances.append(statistics.pvariance(scores))

    if judge.mode == "pairwise":
        if not stabilities:
            return {"error": "no comparable examples"}
        mean_stab = sum(stabilities) / len(stabilities)
        return {
            "mean_verdict_stability": mean_stab,
            "repeats": repeats,
            "n_examples": len(stabilities),
            "interpretation": _interp_stability(mean_stab),
        }
    else:
        if not variances:
            return {"error": "no comparable examples"}
        mean_var = sum(variances) / len(variances)
        return {
            "mean_score_variance": mean_var,
            "repeats": repeats,
            "n_examples": len(variances),
            "interpretation": _interp_variance(mean_var),
        }


def _interp_stability(s: float) -> str:
    if s >= 0.95:
        return "excellent — judge deterministic"
    if s >= 0.85:
        return "acceptable repeatability"
    if s >= 0.70:
        return "concerning — meaningful run-to-run noise"
    return "severe — judge non-deterministic, lower temperature"


def _interp_variance(v: float) -> str:
    if v < 0.01:
        return "excellent — scores stable"
    if v < 0.1:
        return "acceptable"
    if v < 0.5:
        return "concerning — score noise"
    return "severe — judge unstable, lower temperature"
