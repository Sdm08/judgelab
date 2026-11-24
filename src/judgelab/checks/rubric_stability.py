"""Rubric / prompt stability: do judge verdicts change when the rubric is
paraphrased?

This check needs a judge *factory* rather than a frozen Judge, because we
have to reinstantiate the judge with each paraphrased rubric. The user
passes `rubric_variants=[str, ...]` — a list of equivalent rubrics — and a
`judge_factory(rubric: str) -> Judge` that builds a judge from a rubric.

We measure, per example, the fraction of rubric variants that agree with
the majority verdict. Mean across examples is the stability score.
"""
from __future__ import annotations

from collections import Counter

from judgelab.judge import Judge


def run(
    examples,
    judge: Judge,
    rubric_variants: list[str] | None = None,
    judge_factory=None,
    **_,
) -> dict:
    if not rubric_variants or judge_factory is None:
        return {
            "skipped": (
                "pass rubric_variants=[str,...] and judge_factory=callable(rubric)->Judge"
            )
        }
    if len(rubric_variants) < 2:
        return {"error": "need >=2 rubric variants"}

    stability_scores = []
    judges = [judge_factory(r) for r in rubric_variants]
    for ex in examples:
        if ex.response_a is None or ex.response_b is None:
            continue
        verdicts = []
        for j in judges:
            v = j.pairwise(ex.prompt, ex.response_a, ex.response_b).verdict
            verdicts.append(v.value if v else None)
        counts = Counter(v for v in verdicts if v is not None)
        if not counts:
            continue
        majority, maj_count = counts.most_common(1)[0]
        stability_scores.append(maj_count / len(verdicts))

    if not stability_scores:
        return {"error": "no comparable examples"}

    mean_stability = sum(stability_scores) / len(stability_scores)
    return {
        "mean_stability": mean_stability,
        "n_variants": len(rubric_variants),
        "n_examples": len(stability_scores),
        "interpretation": _interp(mean_stability),
    }


def _interp(s: float) -> str:
    if s >= 0.95:
        return "excellent — rubric paraphrases agree"
    if s >= 0.85:
        return "acceptable stability"
    if s >= 0.70:
        return "concerning — rubric wording matters"
    return "severe — judge not robust to rubric paraphrase"
