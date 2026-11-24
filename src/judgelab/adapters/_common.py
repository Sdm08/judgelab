"""Shared helpers for adapter prompts and parsing."""
from __future__ import annotations

DEFAULT_RUBRIC = (
    "You are an impartial judge. Compare the two responses to the prompt. "
    "Reply with exactly one token: A if response A is better, B if response B "
    "is better, or TIE if they are equivalent. Ignore response order and length."
)

PAIRWISE_TEMPLATE = (
    "{rubric}\n\n"
    "Prompt:\n{prompt}\n\n"
    "Response A:\n{a}\n\n"
    "Response B:\n{b}\n\n"
    "Answer with A, B, or TIE."
)


def parse_verdict(text: str) -> str:
    up = text.strip().upper()
    # scan for first standalone A/B/TIE
    for tok in up.replace(".", " ").replace(",", " ").split():
        if tok in {"A", "B"}:
            return tok
        if tok in {"TIE", "DRAW", "EQUAL"}:
            return "TIE"
    return "TIE"
