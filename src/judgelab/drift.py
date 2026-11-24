"""Production judge-drift monitor.

Treats a stream of verdicts (pairwise) or scores (pointwise) as windowed
batches, flags when the distribution shifts beyond a threshold vs. a
baseline batch.
"""
from __future__ import annotations

import math
import statistics
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DriftAlert:
    at: str
    kind: str
    baseline: dict
    current: dict
    distance: float
    severity: str


@dataclass
class DriftMonitor:
    window: int = 500
    psi_threshold: float = 0.2            # population stability index
    score_shift_threshold: float = 0.5    # absolute mean-score shift
    baseline: dict | None = None
    _buffer: deque = field(default_factory=deque)
    alerts: list[DriftAlert] = field(default_factory=list)

    def set_baseline(self, sample) -> None:
        self.baseline = self._summarize(sample)

    def observe(self, value) -> None:
        self._buffer.append(value)
        while len(self._buffer) > self.window:
            self._buffer.popleft()
        if self.baseline is None:
            return
        if len(self._buffer) < self.window:
            return
        current = self._summarize(list(self._buffer))
        self._check(current)

    def _summarize(self, sample) -> dict:
        if not sample:
            return {}
        if isinstance(sample[0], str):
            counts = Counter(sample)
            total = sum(counts.values())
            return {"kind": "categorical", "p": {k: v / total for k, v in counts.items()}}
        else:
            return {
                "kind": "numeric",
                "mean": statistics.mean(sample),
                "stdev": statistics.stdev(sample) if len(sample) > 1 else 0.0,
            }

    def _check(self, current: dict) -> None:
        if not self.baseline or current.get("kind") != self.baseline.get("kind"):
            return
        now = datetime.now(timezone.utc).isoformat()
        if current["kind"] == "categorical":
            dist = _psi(self.baseline["p"], current["p"])
            if dist > self.psi_threshold:
                self.alerts.append(
                    DriftAlert(
                        at=now,
                        kind="categorical",
                        baseline=self.baseline,
                        current=current,
                        distance=dist,
                        severity=_severity(dist, self.psi_threshold),
                    )
                )
        else:
            dist = abs(current["mean"] - self.baseline["mean"])
            if dist > self.score_shift_threshold:
                self.alerts.append(
                    DriftAlert(
                        at=now,
                        kind="numeric",
                        baseline=self.baseline,
                        current=current,
                        distance=dist,
                        severity=_severity(dist, self.score_shift_threshold),
                    )
                )


def _psi(p: dict, q: dict, eps: float = 1e-4) -> float:
    keys = set(p) | set(q)
    total = 0.0
    for k in keys:
        pi = p.get(k, 0) + eps
        qi = q.get(k, 0) + eps
        total += (qi - pi) * math.log(qi / pi)
    return total


def _severity(d: float, threshold: float) -> str:
    if d < threshold:
        return "stable"
    if d < 2 * threshold:
        return "drifting"
    return "severe drift"
