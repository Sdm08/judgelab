"""Judge wrapper: wraps any callable or LLM client as a pairwise or pointwise judge."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Literal, Protocol


class Verdict(str, Enum):
    A = "A"
    B = "B"
    TIE = "tie"


@dataclass
class JudgeResult:
    verdict: Verdict | None = None
    score: float | None = None
    raw: str | None = None


PairwiseFn = Callable[[str, str, str], str | Verdict | JudgeResult]
PointwiseFn = Callable[[str, str], float | JudgeResult]


class Judge:
    """Uniform interface for pairwise or pointwise judges."""

    def __init__(
        self,
        fn: PairwiseFn | PointwiseFn,
        mode: Literal["pairwise", "pointwise"] = "pairwise",
        name: str = "judge",
    ):
        self.fn = fn
        self.mode = mode
        self.name = name

    @classmethod
    def from_callable(
        cls,
        fn: PairwiseFn | PointwiseFn,
        mode: Literal["pairwise", "pointwise"] = "pairwise",
        name: str = "judge",
    ) -> "Judge":
        return cls(fn, mode=mode, name=name)

    def pairwise(self, prompt: str, a: str, b: str) -> JudgeResult:
        if self.mode != "pairwise":
            raise ValueError(f"Judge '{self.name}' is pointwise, cannot run pairwise.")
        out = self.fn(prompt, a, b)
        return _coerce_pairwise(out)

    def pointwise(self, prompt: str, response: str) -> JudgeResult:
        if self.mode != "pointwise":
            raise ValueError(f"Judge '{self.name}' is pairwise, cannot run pointwise.")
        out = self.fn(prompt, response)
        return _coerce_pointwise(out)


def _coerce_pairwise(out) -> JudgeResult:
    if isinstance(out, JudgeResult):
        return out
    if isinstance(out, Verdict):
        return JudgeResult(verdict=out)
    if isinstance(out, str):
        s = out.strip().upper()
        if s in {"A", "B"}:
            return JudgeResult(verdict=Verdict(s), raw=out)
        if s in {"TIE", "DRAW", "EQUAL"}:
            return JudgeResult(verdict=Verdict.TIE, raw=out)
        return JudgeResult(raw=out)
    raise TypeError(f"Unexpected pairwise judge output: {type(out)}")


def _coerce_pointwise(out) -> JudgeResult:
    if isinstance(out, JudgeResult):
        return out
    if isinstance(out, (int, float)):
        return JudgeResult(score=float(out))
    raise TypeError(f"Unexpected pointwise judge output: {type(out)}")
