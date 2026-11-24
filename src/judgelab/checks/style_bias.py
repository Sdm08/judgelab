"""Style bias: does the judge prefer confident, formatted, or polite responses
regardless of content?

We synthesize paired variants of each response (plain vs. styled) and measure
whether the styled version wins more than 50%. For honest control we also need
a baseline where both sides are identical; those should tie or split evenly.

By default we test three style axes:
  - markdown    : wraps response in headings + bullets
  - confidence  : prefixes with confident hedges
  - politeness  : adds polite framing

Each axis runs on up to `max_pairs` examples (default 20) from the dataset.
"""
from __future__ import annotations

from judgelab.judge import Judge, Verdict


_STYLES = {
    "markdown": lambda s: f"## Answer\n\n- {s}\n- See above for details.",
    "confidence": lambda s: f"I am certain of this: {s} This is the definitive answer.",
    "politeness": lambda s: f"Thank you for the question. {s} I hope that helps!",
}


def run(examples, judge: Judge, styles: list[str] | None = None, max_pairs: int = 20, **_) -> dict:
    if judge.mode != "pairwise":
        return {"skipped": "style_bias requires pairwise judge"}

    styles = styles or list(_STYLES)
    unknown = [s for s in styles if s not in _STYLES]
    if unknown:
        return {"error": f"unknown styles: {unknown}; available: {list(_STYLES)}"}

    results: dict = {}
    for style in styles:
        transform = _STYLES[style]
        wins = 0
        n = 0
        for ex in examples[:max_pairs]:
            if ex.response_a is None:
                continue
            base = ex.response_a
            styled = transform(base)
            if base == styled:
                continue
            # Run both orderings and average to isolate style from position bias.
            v1 = judge.pairwise(ex.prompt, base, styled).verdict
            v2 = judge.pairwise(ex.prompt, styled, base).verdict
            for v, styled_is in ((v1, Verdict.B), (v2, Verdict.A)):
                if v is None:
                    continue
                n += 1
                if v == styled_is:
                    wins += 1
        rate = wins / n if n else None
        results[style] = {
            "styled_win_rate": rate,
            "n_comparisons": n,
            "interpretation": _interp(rate),
        }
    return results


def _interp(rate: float | None) -> str:
    if rate is None:
        return "insufficient data"
    if 0.45 <= rate <= 0.55:
        return "neutral — no style bias"
    if rate > 0.70:
        return "severe — judge favours this style strongly"
    if rate > 0.60:
        return "concerning — style bias present"
    if rate < 0.30:
        return "inverse — judge penalises this style"
    return "mild bias"
