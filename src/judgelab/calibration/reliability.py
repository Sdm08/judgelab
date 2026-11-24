"""Reliability diagram helpers.

A reliability diagram bins predicted probabilities and compares the
average prediction to the empirical frequency in each bin. A perfectly
calibrated judge lies on the diagonal.

Also exposes Expected Calibration Error (ECE) and an inline SVG
renderer suitable for embedding in HTML reports (no external deps).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ReliabilityCurve:
    bin_lower: list[float]
    bin_upper: list[float]
    avg_pred: list[float]
    empirical_rate: list[float]
    count: list[int]


def reliability_curve(probs, labels, n_bins: int = 10) -> ReliabilityCurve:
    p = np.asarray(probs, dtype=float)
    y = np.asarray([_to_int(v) for v in labels])
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    rc = ReliabilityCurve([], [], [], [], [])
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (p >= lo) & (p < hi) if i < n_bins - 1 else (p >= lo) & (p <= hi)
        rc.bin_lower.append(float(lo))
        rc.bin_upper.append(float(hi))
        if mask.sum() == 0:
            rc.avg_pred.append(float("nan"))
            rc.empirical_rate.append(float("nan"))
            rc.count.append(0)
        else:
            rc.avg_pred.append(float(p[mask].mean()))
            rc.empirical_rate.append(float(y[mask].mean()))
            rc.count.append(int(mask.sum()))
    return rc


def ece(probs, labels, n_bins: int = 10) -> float:
    rc = reliability_curve(probs, labels, n_bins=n_bins)
    total = sum(rc.count)
    if total == 0:
        return float("nan")
    gap = 0.0
    for ap, er, c in zip(rc.avg_pred, rc.empirical_rate, rc.count):
        if c == 0:
            continue
        gap += (c / total) * abs(ap - er)
    return gap


def render_reliability_svg(
    rc: ReliabilityCurve,
    width: int = 320,
    height: int = 320,
    padding: int = 30,
) -> str:
    """Return a standalone SVG string for the reliability diagram."""
    plot_w = width - 2 * padding
    plot_h = height - 2 * padding

    def x(p: float) -> float:
        return padding + p * plot_w

    def y(v: float) -> float:
        return height - padding - v * plot_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'style="font-family:system-ui,sans-serif">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>',
        f'<line x1="{x(0)}" y1="{y(0)}" x2="{x(1)}" y2="{y(1)}" '
        f'stroke="#aaa" stroke-dasharray="3,3"/>',
        f'<line x1="{padding}" y1="{height - padding}" x2="{width - padding}" '
        f'y2="{height - padding}" stroke="#333"/>',
        f'<line x1="{padding}" y1="{padding}" x2="{padding}" '
        f'y2="{height - padding}" stroke="#333"/>',
    ]
    total = sum(rc.count) or 1
    for lo, hi, ap, er, c in zip(
        rc.bin_lower, rc.bin_upper, rc.avg_pred, rc.empirical_rate, rc.count
    ):
        if c == 0 or np.isnan(ap) or np.isnan(er):
            continue
        r = 3 + 8 * (c / total)
        parts.append(
            f'<circle cx="{x(ap):.1f}" cy="{y(er):.1f}" r="{r:.1f}" '
            f'fill="#4a7" fill-opacity="0.7" stroke="#27543a"/>'
        )
    parts += [
        f'<text x="{x(0.5):.1f}" y="{height - 6}" text-anchor="middle" '
        f'font-size="11" fill="#444">predicted probability</text>',
        f'<text x="10" y="{y(0.5):.1f}" text-anchor="middle" '
        f'font-size="11" fill="#444" transform="rotate(-90 10 {y(0.5):.1f})">empirical rate</text>',
        "</svg>",
    ]
    return "".join(parts)


def _to_int(v) -> int:
    import numbers
    if isinstance(v, str):
        up = v.upper()
        if up == "A":
            return 1
        if up == "B":
            return 0
        raise ValueError(f"Cannot map label {v!r} to 0/1")
    if isinstance(v, numbers.Integral):
        return int(v)
    if isinstance(v, numbers.Real):
        return int(float(v) >= 0.5)
    raise ValueError(f"Cannot map label {v!r} to 0/1")
