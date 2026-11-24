"""Tests for self_preference, style_bias, rubric_stability, test_retest checks."""
import pytest

from judgelab import AuditSuite, Judge


def test_self_preference_detects_bias():
    # judge always picks A; examples where model-X is always A -> X wins
    exs = [
        {
            "prompt": "q",
            "response_a": "x-out",
            "response_b": "y-out",
            "meta": {"model_a": "X", "model_b": "Y"},
        }
        for _ in range(6)
    ]
    judge = Judge.from_callable(lambda p, a, b: "A", name="X")
    rep = AuditSuite.from_pairs(exs).run(judge, checks=["self_preference"], judge_model="X")
    d = rep.checks["self_preference"]
    assert d["own_win_rate"] == 1.0
    assert d["others_mean_win_rate"] == 0.0
    assert "severe" in d["interpretation"]


def test_self_preference_skipped_without_judge_model():
    exs = [{"prompt": "q", "response_a": "a", "response_b": "b"}]
    judge = Judge.from_callable(lambda p, a, b: "A", name="X")
    rep = AuditSuite.from_pairs(exs).run(judge, checks=["self_preference"])
    assert "skipped" in rep.checks["self_preference"]


def test_style_bias_markdown_preferring_judge():
    # judge picks whichever response contains "##"
    def biased(p, a, b):
        return "A" if "##" in a else "B"
    judge = Judge.from_callable(biased, name="md-lover")
    exs = [{"prompt": f"q{i}", "response_a": "plain text"} for i in range(10)]
    rep = AuditSuite.from_pairs(exs).run(judge, checks=["style_bias"], styles=["markdown"])
    md = rep.checks["style_bias"]["markdown"]
    assert md["styled_win_rate"] == 1.0
    assert "severe" in md["interpretation"]


def test_rubric_stability_perfect():
    # judge ignores rubric, always picks A -> perfect stability
    def factory(rubric):
        return Judge.from_callable(lambda p, a, b: "A", name=f"j:{rubric[:5]}")
    exs = [{"prompt": "q", "response_a": "a", "response_b": "b"}] * 5
    rep = AuditSuite.from_pairs(exs).run(
        factory("stub"),
        checks=["rubric_stability"],
        rubric_variants=["pick best", "choose better", "which is nicer"],
        judge_factory=factory,
    )
    s = rep.checks["rubric_stability"]
    assert s["mean_stability"] == 1.0
    assert "excellent" in s["interpretation"]


def test_rubric_stability_skipped_without_variants():
    judge = Judge.from_callable(lambda p, a, b: "A", name="x")
    rep = AuditSuite.from_pairs(
        [{"prompt": "q", "response_a": "a", "response_b": "b"}]
    ).run(judge, checks=["rubric_stability"])
    assert "skipped" in rep.checks["rubric_stability"]


def test_test_retest_deterministic_pairwise():
    judge = Judge.from_callable(lambda p, a, b: "A", name="det")
    exs = [{"prompt": "q", "response_a": "a", "response_b": "b"}] * 5
    rep = AuditSuite.from_pairs(exs).run(judge, checks=["test_retest"], repeats=3)
    d = rep.checks["test_retest"]
    assert d["mean_verdict_stability"] == 1.0
    assert "excellent" in d["interpretation"]
