"""Position bias: swap A/B order, measure flip rate.

A fair judge should give the same verdict regardless of presentation order.
Flip rate = fraction of examples where verdict changes after swap.
Positional preference = P(A wins | original) - P(A wins | swapped).
"""
from __future__ import annotations

from judgelab.judge import Judge, Verdict


def run(examples, judge: Judge, **_) -> dict:
    if judge.mode != "pairwise":
        return {"skipped": "position_bias requires pairwise judge"}

    n = len(examples)
    flips = 0
    a_wins_orig = 0
    a_wins_swap = 0
    per_example = []

    for ex in examples:
        if ex.response_a is None or ex.response_b is None:
            continue
        v1 = judge.pairwise(ex.prompt, ex.response_a, ex.response_b).verdict
        # swapped: pass B as first, A as second; map result back
        v2_raw = judge.pairwise(ex.prompt, ex.response_b, ex.response_a).verdict
        v2 = _swap(v2_raw)

        if v1 == Verdict.A:
            a_wins_orig += 1
        if v2 == Verdict.A:
            a_wins_swap += 1
        if v1 != v2 and v1 is not None and v2 is not None:
            flips += 1
        per_example.append({"v1": v1.value if v1 else None, "v2": v2.value if v2 else None})

    flip_rate = flips / n if n else 0.0
    positional_pref = (a_wins_orig - a_wins_swap) / n if n else 0.0

    return {
        "flip_rate": flip_rate,
        "positional_preference": positional_pref,
        "a_wins_original": a_wins_orig,
        "a_wins_swapped": a_wins_swap,
        "n": n,
        "interpretation": _interpret(flip_rate),
        "per_example": per_example,
    }


def _swap(v: Verdict | None) -> Verdict | None:
    if v == Verdict.A:
        return Verdict.B
    if v == Verdict.B:
        return Verdict.A
    return v


def _interpret(flip_rate: float) -> str:
    if flip_rate < 0.05:
        return "excellent — judge consistent under order swap"
    if flip_rate < 0.15:
        return "acceptable"
    if flip_rate < 0.30:
        return "concerning — meaningful position bias"
    return "severe — judge unreliable, mitigate with order averaging"
