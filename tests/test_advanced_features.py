"""Tests for benchmarks, reliability, store, config-gen, Langfuse bridge."""
import json
import tempfile
from pathlib import Path

import pytest

from judgelab import AuditSuite, Judge, RunStore
from judgelab.benchmarks import (
    load_mt_bench_fixture,
    render_leaderboard,
    run_mt_bench_position_bias,
)
from judgelab.benchmarks.leaderboard import JudgeRunRow
from judgelab.calibration import ece, reliability_curve, render_reliability_svg
from judgelab.config_gen import auto_config


def test_mt_bench_fixture_loads():
    suite = load_mt_bench_fixture(variant="sample")
    assert len(suite.examples) >= 20


def test_run_mt_bench_position_bias():
    judge = Judge.from_callable(lambda p, a, b: "A", name="always-A")
    res = run_mt_bench_position_bias(judge, variant="sample")
    assert res["flip_rate"] == 1.0  # always-A flips on every swap
    assert "gpt-4" in res["literature_baseline"]


def test_leaderboard_renders_sorted():
    rows = [
        JudgeRunRow(judge="A", flip_rate=0.4, longer_wins_rate=0.6),
        JudgeRunRow(judge="B", flip_rate=0.1, longer_wins_rate=0.5, kappa=0.7),
    ]
    md = render_leaderboard(rows)
    assert md.index("| B |") < md.index("| A |")


def test_reliability_curve_perfect_calibration():
    probs = [0.1, 0.3, 0.5, 0.7, 0.9] * 20
    labels = [0 if p < 0.5 else 1 for p in probs]
    rc = reliability_curve(probs, labels, n_bins=5)
    assert len(rc.avg_pred) == 5
    assert sum(rc.count) == len(probs)


def test_ece_returns_fraction():
    probs = [0.1, 0.9] * 10
    labels = [0, 1] * 10
    e = ece(probs, labels, n_bins=5)
    assert 0.0 <= e <= 1.0


def test_reliability_svg_renders():
    rc = reliability_curve([0.1, 0.9, 0.5], [0, 1, 1])
    svg = render_reliability_svg(rc)
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")


def test_run_store_round_trip(tmp_path):
    judge = Judge.from_callable(lambda p, a, b: "A", name="j1")
    rep = AuditSuite.from_pairs(
        [{"prompt": "q", "response_a": "a", "response_b": "b"}] * 4
    ).run(judge, checks=["position_bias"])
    store = RunStore(tmp_path / "runs.db")
    rid = store.record(rep, dataset="inline")
    got = store.get(rid)
    assert got is not None
    assert got.judge == "j1"
    assert "position_bias" in got.metrics
    rows = store.list_runs()
    assert rows[0].id == rid


def test_run_store_diff(tmp_path):
    db = tmp_path / "runs.db"
    exs = [{"prompt": f"q{i}", "response_a": "aa", "response_b": "bb"} for i in range(4)]
    biased = Judge.from_callable(lambda p, a, b: "A", name="biased")
    fair = Judge.from_callable(lambda p, a, b: "A" if a < b else "B", name="fair")
    store = RunStore(db)
    r1 = store.record(AuditSuite.from_pairs(exs).run(biased, checks=["position_bias"]))
    r2 = store.record(AuditSuite.from_pairs(exs).run(fair, checks=["position_bias"]))
    d = store.diff(r1, r2)
    pb = d["checks"]["position_bias"]
    assert "flip_rate" in pb
    assert pb["flip_rate"]["a"] == 1.0  # biased flips every time
    assert pb["flip_rate"]["b"] == 0.0  # fair never flips
    assert pb["flip_rate"]["delta"] == -1.0


def test_auto_config_picks_relevant_checks(tmp_path):
    ds = tmp_path / "eval.jsonl"
    ds.write_text(
        json.dumps({"prompt": "q", "response_a": "a", "response_b": "b"}) + "\n",
        encoding="utf-8",
    )
    j = tmp_path / "judge.py"
    j.write_text("from judgelab import Judge\njudge = Judge.from_callable(lambda p,a,b:'A')\n")
    out = auto_config(dataset=ds, judge=j)
    assert "position_bias" in out
    assert "verbosity_bias" in out
    assert "agreement" not in out  # no labels


def test_auto_config_self_preference_when_meta(tmp_path):
    ds = tmp_path / "eval.jsonl"
    ds.write_text(
        json.dumps(
            {
                "prompt": "q",
                "response_a": "a",
                "response_b": "b",
                "meta": {"model_a": "X", "model_b": "Y"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    j = tmp_path / "judge.py"
    j.write_text("from judgelab import Judge\njudge = Judge.from_callable(lambda p,a,b:'A')\n")
    out = auto_config(dataset=ds, judge=j)
    assert "self_preference" in out


def test_langfuse_bridge_errors_without_lib(monkeypatch):
    from judgelab.integrations import push_report_to_langfuse

    judge = Judge.from_callable(lambda p, a, b: "A", name="x")
    rep = AuditSuite.from_pairs(
        [{"prompt": "q", "response_a": "a", "response_b": "b"}]
    ).run(judge, checks=["position_bias"])

    import builtins
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "langfuse":
            raise ImportError("fake missing")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError):
        push_report_to_langfuse(rep)
