"""Human labels for agreement scoring."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HumanLabels:
    """Maps example index (0-based) -> label ('A' | 'B' | 'tie' | score)."""

    labels: dict[int, str | float]

    @classmethod
    def from_csv(cls, path: str | Path) -> "HumanLabels":
        """CSV with columns: index,label."""
        out: dict[int, str | float] = {}
        with open(path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                idx = int(row["index"])
                val = row["label"].strip()
                try:
                    out[idx] = float(val)
                except ValueError:
                    out[idx] = val.upper() if val.upper() in {"A", "B"} else val.lower()
        return cls(out)

    def get(self, idx: int):
        return self.labels.get(idx)
