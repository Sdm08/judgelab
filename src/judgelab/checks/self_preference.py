"""Self-preference bias: does a judge rate its own model's output higher?

Requires examples labelled with which model produced each response:
    {"prompt": "...", "response_a": "...", "response_b": "...",
     "meta": {"model_a": "gpt-4", "model_b": "claude-3"}}

The judge's own model id must be passed via `judge_model`. We measure the
win rate of the judge's own model vs. its average win rate across the pool.
"""
from __future__ import annotations

from collections import defaultdict

from judgelab.judge import Judge, Verdict


def run(examples, judge: Judge, judge_model: str | None = None, **_) -> dict:
    if judge.mode != "pairwise":
        return {"skipped": "self_preference requires pairwise judge"}
    if not judge_model:
        return {"skipped": "pass judge_model=<id> matching meta.model_a/b to run"}

    wins = defaultdict(int)
    appearances = defaultdict(int)
    comparable = 0

    for ex in examples:
        ma = ex.meta.get("model_a") if ex.meta else None
        mb = ex.meta.get("model_b") if ex.meta else None
        if not ma or not mb or ma == mb:
            continue
        if ex.response_a is None or ex.response_b is None:
            continue
        comparable += 1
        appearances[ma] += 1
        appearances[mb] += 1
        v = judge.pairwise(ex.prompt, ex.response_a, ex.response_b).verdict
        if v == Verdict.A:
            wins[ma] += 1
        elif v == Verdict.B:
            wins[mb] += 1

    if comparable < 2 or judge_model not in appearances:
        return {
            "error": "need >=2 examples where judge_model appears",
            "comparable": comparable,
            "models_seen": sorted(appearances),
        }

    def wr(model: str) -> float:
        return wins[model] / appearances[model] if appearances[model] else 0.0

    own = wr(judge_model)
    others = [m for m in appearances if m != judge_model]
    other_mean = sum(wr(m) for m in others) / len(others) if others else 0.0
    delta = own - other_mean

    return {
        "judge_model": judge_model,
        "own_win_rate": own,
        "others_mean_win_rate": other_mean,
        "self_preference_delta": delta,
        "comparable_pairs": comparable,
        "win_rates": {m: wr(m) for m in appearances},
        "interpretation": _interp(delta),
    }


def _interp(d: float) -> str:
    if abs(d) < 0.05:
        return "no self-preference"
    if abs(d) < 0.10:
        return "mild self-preference"
    if abs(d) < 0.20:
        return "concerning self-preference"
    return "severe self-preference — judge biased toward own model"
