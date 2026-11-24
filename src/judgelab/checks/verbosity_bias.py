"""Verbosity bias: does the longer response win more than length-neutral baseline?

Measured on *decisive* verdicts only (ties carry no length signal and are
excluded from both the correlation and the longer-wins rate).

Positive correlation => longer wins more often.
"""
from __future__ import annotations

import numpy as np

from judgelab.judge import Judge, Verdict


def run(examples, judge: Judge, **_) -> dict:
    if judge.mode != "pairwise":
        return {"skipped": "verbosity_bias requires pairwise judge"}

    length_deltas = []
    a_wins = []
    n_total = 0
    n_ties = 0
    for ex in examples:
        if ex.response_a is None or ex.response_b is None:
            continue
        v = judge.pairwise(ex.prompt, ex.response_a, ex.response_b).verdict
        if v is None:
            continue
        n_total += 1
        if v == Verdict.TIE:
            n_ties += 1
            continue
        length_deltas.append(len(ex.response_a) - len(ex.response_b))
        a_wins.append(1 if v == Verdict.A else 0)

    if len(length_deltas) < 2:
        return {
            "error": "need >=2 non-tie examples with valid verdicts",
            "n_total": n_total,
            "n_ties": n_ties,
        }

    x = np.array(length_deltas, dtype=float)
    y = np.array(a_wins, dtype=float)

    if x.std() == 0 or y.std() == 0:
        corr = 0.0
    else:
        corr = float(np.corrcoef(x, y)[0, 1])

    comparable = sum(1 for d in length_deltas if d != 0)
    longer_wins = sum(
        1 for d, w in zip(length_deltas, a_wins) if (d > 0 and w == 1) or (d < 0 and w == 0)
    )
    longer_win_rate = longer_wins / comparable if comparable else None

    return {
        "length_win_correlation": corr,
        "longer_wins_rate": longer_win_rate,
        "n_decisive": len(length_deltas),
        "n_ties": n_ties,
        "n_total": n_total,
        "interpretation": _interpret(longer_win_rate),
    }


def _interpret(rate: float | None) -> str:
    if rate is None:
        return "insufficient non-tie data to judge verbosity bias"
    if 0.45 <= rate <= 0.55:
        return "balanced — no clear verbosity bias"
    if rate > 0.70:
        return "severe — judge strongly prefers longer responses"
    if rate > 0.60:
        return "concerning — verbosity bias present"
    if rate < 0.30:
        return "inverse bias — judge prefers shorter responses"
    return "mild bias"
