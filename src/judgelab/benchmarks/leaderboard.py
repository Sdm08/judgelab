"""Leaderboard builder: aggregate judge audits across multiple judges and
emit a Markdown table suitable for README or a static site.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class JudgeRunRow:
    judge: str
    flip_rate: float | None
    longer_wins_rate: float | None
    kappa: float | None = None
    notes: str = ""


def render_leaderboard(rows: Iterable[JudgeRunRow]) -> str:
    rows = sorted(rows, key=lambda r: (r.flip_rate is None, r.flip_rate or 0))
    lines = [
        "| # | Judge | Flip rate ↓ | Longer-wins | Kappa ↑ | Notes |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i} | {r.judge} | {_fmt(r.flip_rate)} | {_fmt(r.longer_wins_rate)} | "
            f"{_fmt(r.kappa)} | {r.notes} |"
        )
    return "\n".join(lines)


def _fmt(v):
    if v is None:
        return "—"
    return f"{v:.3f}" if isinstance(v, float) else str(v)
