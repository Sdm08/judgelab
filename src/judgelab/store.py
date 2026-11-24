"""Persistent run store: SQLite-backed history of audits for diffing.

Schema:
    runs(id, created_at, judge, dataset, n_examples, meta_json)
    metrics(run_id, check, metric, value, value_str)
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from judgelab.report import Report


DEFAULT_DB_PATH = os.environ.get("JUDGELAB_DB", ".judgelab/runs.db")


@dataclass
class RunRow:
    id: int
    created_at: str
    judge: str
    dataset: str
    n_examples: int
    metrics: dict  # {check: {metric: value}}


class RunStore:
    def __init__(self, path: str | Path = DEFAULT_DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    judge TEXT NOT NULL,
                    dataset TEXT,
                    n_examples INTEGER,
                    meta_json TEXT
                );
                CREATE TABLE IF NOT EXISTS metrics (
                    run_id INTEGER NOT NULL,
                    check_name TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    value REAL,
                    value_str TEXT,
                    FOREIGN KEY (run_id) REFERENCES runs(id)
                );
                CREATE INDEX IF NOT EXISTS ix_metrics_run ON metrics(run_id);
                """
            )
            c.commit()

    def record(self, report: Report, dataset: str = "", meta: dict | None = None) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with closing(sqlite3.connect(self.path)) as c:
            cur = c.execute(
                "INSERT INTO runs(created_at, judge, dataset, n_examples, meta_json) "
                "VALUES (?, ?, ?, ?, ?)",
                (now, report.judge_name, dataset, report.n_examples, json.dumps(meta or {})),
            )
            run_id = cur.lastrowid
            for check, data in report.checks.items():
                if not isinstance(data, dict):
                    continue
                for metric, value in data.items():
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        c.execute(
                            "INSERT INTO metrics(run_id, check_name, metric, value, value_str) "
                            "VALUES (?, ?, ?, ?, NULL)",
                            (run_id, check, metric, float(value)),
                        )
                    elif isinstance(value, str):
                        c.execute(
                            "INSERT INTO metrics(run_id, check_name, metric, value, value_str) "
                            "VALUES (?, ?, ?, NULL, ?)",
                            (run_id, check, metric, value),
                        )
            c.commit()
            return int(run_id)

    def list_runs(self, limit: int = 20) -> list[RunRow]:
        with closing(sqlite3.connect(self.path)) as c:
            rows = c.execute(
                "SELECT id, created_at, judge, dataset, n_examples "
                "FROM runs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            out = []
            for r in rows:
                metrics = self._metrics_for(c, r[0])
                out.append(
                    RunRow(
                        id=r[0],
                        created_at=r[1],
                        judge=r[2],
                        dataset=r[3] or "",
                        n_examples=r[4] or 0,
                        metrics=metrics,
                    )
                )
            return out

    def get(self, run_id: int) -> RunRow | None:
        with closing(sqlite3.connect(self.path)) as c:
            r = c.execute(
                "SELECT id, created_at, judge, dataset, n_examples FROM runs WHERE id=?",
                (run_id,),
            ).fetchone()
            if not r:
                return None
            return RunRow(
                id=r[0],
                created_at=r[1],
                judge=r[2],
                dataset=r[3] or "",
                n_examples=r[4] or 0,
                metrics=self._metrics_for(c, r[0]),
            )

    def _metrics_for(self, c, run_id: int) -> dict:
        out: dict = {}
        for check, metric, value, value_str in c.execute(
            "SELECT check_name, metric, value, value_str FROM metrics WHERE run_id=?",
            (run_id,),
        ).fetchall():
            out.setdefault(check, {})[metric] = value if value is not None else value_str
        return out

    def diff(self, a: int, b: int) -> dict:
        ra, rb = self.get(a), self.get(b)
        if ra is None or rb is None:
            raise KeyError(f"Run not found: {a if ra is None else b}")
        out = {"a": a, "b": b, "judge_a": ra.judge, "judge_b": rb.judge, "checks": {}}
        keys = set(ra.metrics) | set(rb.metrics)
        for check in keys:
            m_a = ra.metrics.get(check, {})
            m_b = rb.metrics.get(check, {})
            metric_keys = set(m_a) | set(m_b)
            diffs = {}
            for m in metric_keys:
                va = m_a.get(m)
                vb = m_b.get(m)
                if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                    diffs[m] = {"a": va, "b": vb, "delta": vb - va}
                else:
                    diffs[m] = {"a": va, "b": vb}
            out["checks"][check] = diffs
        return out
