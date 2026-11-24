"""Smoke tests for judgelab checks."""
import random

import pytest

from judgelab import AuditSuite, Judge
from judgelab.labels import HumanLabels


@pytest.fixture
def examples():
    return [
        {"prompt": f"q{i}", "response_a": "short", "response_b": "a much longer answer here"}
        for i in range(20)
    ]


def test_position_bias_detects_always_A(examples):
    judge = Judge.from_callable(lambda p, a, b: "A", name="always-A")
    suite = AuditSuite.from_pairs(examples)
    rep = suite.run(judge, checks=["position_bias"])
    data = rep.checks["position_bias"]
    # always-A under swap flips every time -> flip_rate == 1.0
    assert data["flip_rate"] == 1.0
    assert "severe" in data["interpretation"]


def test_position_bias_fair_judge(examples):
    # fair judge: deterministic based on content, order-invariant
    def fair(p, a, b):
        return "A" if a < b else "B"  # lexicographic, content-based
    judge = Judge.from_callable(fair, name="fair")
    suite = AuditSuite.from_pairs(examples)
    rep = suite.run(judge, checks=["position_bias"])
    assert rep.checks["position_bias"]["flip_rate"] == 0.0


def test_verbosity_bias_detects_longer_wins(examples):
    judge = Judge.from_callable(
        lambda p, a, b: "A" if len(a) > len(b) else "B", name="longer-wins"
    )
    suite = AuditSuite.from_pairs(examples)
    rep = suite.run(judge, checks=["verbosity_bias"])
    data = rep.checks["verbosity_bias"]
    assert data["longer_wins_rate"] == 1.0
    assert "severe" in data["interpretation"]


def test_agreement_with_perfect_human_match():
    exs = [
        {"prompt": "q1", "response_a": "x", "response_b": "y"},
        {"prompt": "q2", "response_a": "x", "response_b": "y"},
        {"prompt": "q3", "response_a": "x", "response_b": "y"},
        {"prompt": "q4", "response_a": "x", "response_b": "y"},
    ]
    judge = Judge.from_callable(lambda p, a, b: "A", name="always-A")
    labels = HumanLabels(labels={0: "A", 1: "A", 2: "B", 3: "A"})
    suite = AuditSuite.from_pairs(exs)
    rep = suite.run(judge, checks=["agreement"], human_labels=labels)
    assert rep.checks["agreement"]["accuracy"] == 0.75


def test_html_autoescape_blocks_script_injection():
    # judge_name and interpretation strings reach the HTML; ensure escaping.
    judge = Judge.from_callable(lambda p, a, b: "A", name="<script>alert(1)</script>")
    rep = AuditSuite.from_pairs(
        [{"prompt": "q", "response_a": "a", "response_b": "b"}]
    ).run(judge, checks=["position_bias"])
    html = rep.to_html()
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_field_size_limit(monkeypatch):
    import judgelab.dataset as ds
    monkeypatch.setattr(ds, "_MAX_FIELD_CHARS", 10)
    with pytest.raises(ValueError):
        AuditSuite.from_pairs([{"prompt": "x" * 100, "response_a": "a", "response_b": "b"}])


def test_report_path_sandbox(tmp_path, monkeypatch):
    judge = Judge.from_callable(lambda p, a, b: "A", name="x")
    rep = AuditSuite.from_pairs(
        [{"prompt": "q", "response_a": "a", "response_b": "b"}]
    ).run(judge, checks=["position_bias"])
    # outside cwd -> refused
    outside = tmp_path / "evil.html"
    with pytest.raises(PermissionError):
        rep.to_html(str(outside))
    # override via env
    monkeypatch.setenv("JUDGELAB_ALLOW_ANY_PATH", "1")
    rep.to_html(str(outside))
    assert outside.exists()


def test_report_thresholds():
    judge = Judge.from_callable(lambda p, a, b: "A", name="always-A")
    suite = AuditSuite.from_pairs(
        [{"prompt": "q", "response_a": "a", "response_b": "b"}] * 5
    )
    rep = suite.run(judge, checks=["position_bias"])
    with pytest.raises(AssertionError):
        rep.assert_thresholds(position_bias__flip_rate__lt=0.1)
    # loose threshold passes
    rep.assert_thresholds(position_bias__flip_rate__le=1.0)
