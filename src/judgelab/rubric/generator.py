"""Generate a judge rubric from human-labeled pairwise examples.

Two modes:
  - heuristic (default): extracts cheap signals from winner/loser pairs
    (length differences, keyword lift, formatting usage). No LLM required.
  - llm: calls a user-provided summarizer function with winner/loser
    excerpts and asks it to write a rubric. The LLM call is the user's;
    judgelab makes none itself.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from statistics import mean

from judgelab.dataset import Example


_WORD_RE = re.compile(r"[A-Za-z][A-Za-z\-']+")
_STOP = {
    "the", "a", "an", "is", "are", "was", "were", "and", "or", "but", "of", "in",
    "on", "at", "to", "for", "with", "that", "this", "it", "as", "by", "be", "if",
    "not", "no", "so", "than", "then", "there", "their", "they", "them", "we",
    "you", "i", "he", "she", "him", "her", "his", "hers", "its", "our", "your",
    "from", "about", "into", "over", "under", "also", "can", "will", "would",
    "should", "could", "do", "does", "did", "have", "has", "had",
}


@dataclass
class RubricDraft:
    rubric: str
    signals: dict = field(default_factory=dict)
    n_examples: int = 0

    def __str__(self) -> str:
        return self.rubric


def generate_rubric(
    examples: list[Example],
    human_labels,
    mode: str = "heuristic",
    llm_summarizer=None,
    max_keywords: int = 8,
) -> RubricDraft:
    """Return a rubric draft inferred from labeled pairs.

    `examples` and `human_labels` must align; label is "A" or "B" naming the
    winner. Rows without a label are skipped.
    """
    winners: list[str] = []
    losers: list[str] = []
    for i, ex in enumerate(examples):
        label = human_labels.get(i) if hasattr(human_labels, "get") else None
        if label not in ("A", "B"):
            continue
        if ex.response_a is None or ex.response_b is None:
            continue
        if label == "A":
            winners.append(ex.response_a)
            losers.append(ex.response_b)
        else:
            winners.append(ex.response_b)
            losers.append(ex.response_a)

    if len(winners) < 3:
        raise ValueError("Need >=3 labeled pairs to draft a rubric")

    signals = _extract_signals(winners, losers, max_keywords=max_keywords)

    if mode == "llm":
        if llm_summarizer is None:
            raise ValueError("mode='llm' requires llm_summarizer callable")
        rubric = llm_summarizer(winners, losers, signals)
    else:
        rubric = _render_heuristic(signals)

    return RubricDraft(rubric=rubric, signals=signals, n_examples=len(winners))


def _extract_signals(winners: list[str], losers: list[str], max_keywords: int) -> dict:
    w_lens = [len(w) for w in winners]
    l_lens = [len(l) for l in losers]
    len_delta = mean(w_lens) - mean(l_lens)
    len_ratio = (mean(w_lens) / mean(l_lens)) if mean(l_lens) else float("inf")

    w_words = _word_counts(winners)
    l_words = _word_counts(losers)
    lift = _keyword_lift(w_words, l_words, max_keywords=max_keywords)

    w_md = _fraction_with_markdown(winners)
    l_md = _fraction_with_markdown(losers)

    return {
        "n_pairs": len(winners),
        "mean_len_winner": mean(w_lens),
        "mean_len_loser": mean(l_lens),
        "len_delta": len_delta,
        "len_ratio": len_ratio,
        "winner_keywords": lift,
        "winner_markdown_rate": w_md,
        "loser_markdown_rate": l_md,
    }


def _word_counts(texts: list[str]) -> Counter:
    c: Counter = Counter()
    for t in texts:
        toks = [w.lower() for w in _WORD_RE.findall(t) if len(w) > 2]
        c.update(w for w in toks if w not in _STOP)
    return c


def _keyword_lift(winners: Counter, losers: Counter, max_keywords: int) -> list[tuple[str, float]]:
    total_w = sum(winners.values()) or 1
    total_l = sum(losers.values()) or 1
    scores = []
    for word, wc in winners.items():
        if wc < 2:
            continue
        pw = wc / total_w
        pl = (losers.get(word, 0) + 1) / (total_l + 1)
        lift = pw / pl
        scores.append((word, round(lift, 2)))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:max_keywords]


def _fraction_with_markdown(texts: list[str]) -> float:
    def has_md(s: str) -> bool:
        return bool(re.search(r"^\s*[-*#]|```|\*\*", s, re.MULTILINE))
    return sum(1 for t in texts if has_md(t)) / len(texts) if texts else 0.0


def _render_heuristic(sig: dict) -> str:
    lines = [
        "You are an impartial judge. Compare the two responses to the prompt and",
        "reply with exactly one token: A, B, or TIE.",
        "",
        "Favour responses that:",
    ]
    if sig["len_ratio"] > 1.3:
        lines.append(
            f"- Give substantive, detailed answers (winning responses were on"
            f" average {sig['len_ratio']:.1f}x longer in training data)."
        )
    elif sig["len_ratio"] < 0.77:
        lines.append(
            "- Are concise; avoid padding (winning responses were shorter in training data)."
        )
    else:
        lines.append("- Match the question's scope; neither padded nor truncated.")

    if sig["winner_markdown_rate"] - sig["loser_markdown_rate"] > 0.2:
        lines.append("- Use clear structure (bullet points, headings) when helpful.")

    if sig["winner_keywords"]:
        kws = ", ".join(w for w, _ in sig["winner_keywords"][:6])
        lines.append(f"- Address core aspects such as: {kws}.")

    lines += [
        "",
        "Ignore response order, author style, and absolute length.",
        "Judge on substance and correctness.",
    ]
    return "\n".join(lines)
