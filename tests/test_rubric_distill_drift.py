"""Tests for auto-rubric, distillation, drift monitor, integrations."""
import pytest

from judgelab import (
    AuditSuite,
    DistilledJudge,
    DriftMonitor,
    HumanLabels,
    Judge,
    distill,
    generate_rubric,
)


def _labeled_pairs():
    # winners are always longer and contain "detailed"
    pairs = []
    labels = {}
    for i in range(6):
        pairs.append(
            {
                "prompt": f"q{i}",
                "response_a": "short",
                "response_b": "a detailed and thorough response covering many aspects",
            }
        )
        labels[i] = "B"
    return pairs, HumanLabels(labels=labels)


def test_generate_rubric_heuristic_captures_length_pattern():
    pairs, labels = _labeled_pairs()
    suite = AuditSuite.from_pairs(pairs)
    draft = generate_rubric(suite.examples, labels, mode="heuristic")
    assert draft.n_examples == 6
    assert "detailed" in draft.rubric.lower() or "detail" in draft.rubric.lower()
    assert "substantive" in draft.rubric.lower() or "longer" in draft.rubric.lower()
    assert draft.signals["len_ratio"] > 1.3


def test_generate_rubric_needs_min_pairs():
    pairs = [{"prompt": "q", "response_a": "a", "response_b": "b"}]
    labels = HumanLabels(labels={0: "A"})
    suite = AuditSuite.from_pairs(pairs)
    with pytest.raises(ValueError):
        generate_rubric(suite.examples, labels)


def test_generate_rubric_llm_mode():
    pairs, labels = _labeled_pairs()
    suite = AuditSuite.from_pairs(pairs)

    def fake_llm(winners, losers, signals):
        return f"Custom rubric from {len(winners)} pairs."

    draft = generate_rubric(suite.examples, labels, mode="llm", llm_summarizer=fake_llm)
    assert draft.rubric == "Custom rubric from 6 pairs."


def test_distill_small_judge_against_teacher_labels():
    small = Judge.from_callable(lambda p, a, b: "A", name="small")
    pairs = [{"prompt": f"q{i}", "response_a": "a", "response_b": "b"} for i in range(10)]
    labels = ["A"] * 7 + ["B"] * 3
    suite = AuditSuite.from_pairs(pairs)
    distilled = distill(small, labels, suite.examples)
    assert isinstance(distilled, DistilledJudge)
    out = distilled.predict("q", "a", "b")
    assert out.verdict is not None
    assert 0.0 <= out.score <= 1.0


def test_distilled_judge_as_judge():
    small = Judge.from_callable(lambda p, a, b: "A", name="s")
    pairs = [{"prompt": "q", "response_a": "a", "response_b": "b"}] * 6
    labels = ["A"] * 4 + ["B"] * 2
    suite = AuditSuite.from_pairs(pairs)
    distilled = distill(small, labels, suite.examples)
    j = distilled.as_judge()
    r = j.pairwise("q", "a", "b")
    assert r.verdict is not None


def test_drift_monitor_categorical_flags_shift():
    m = DriftMonitor(window=10, psi_threshold=0.1)
    baseline = ["A"] * 8 + ["B"] * 2
    m.set_baseline(baseline)
    # feed a very different distribution
    for v in ["B"] * 10:
        m.observe(v)
    assert len(m.alerts) >= 1
    assert m.alerts[-1].severity in ("drifting", "severe drift")


def test_drift_monitor_numeric_stable():
    m = DriftMonitor(window=10, score_shift_threshold=1.0)
    m.set_baseline([0.5] * 10)
    for v in [0.5] * 20:
        m.observe(v)
    assert m.alerts == []


def test_deepeval_bridge_measure():
    from judgelab.integrations import to_deepeval_metric

    class TC:
        input = "q"
        actual_output = "x"
        expected_output = "y"

    judge = Judge.from_callable(lambda p, a, b: "A", name="x")
    metric = to_deepeval_metric(judge)
    score = metric.measure(TC())
    assert score == 1.0
    assert metric.is_successful()


def test_ragas_bridge_pairwise_returns_int():
    from judgelab.integrations import to_ragas_judge
    judge = Judge.from_callable(lambda p, a, b: "A", name="x")
    fn = to_ragas_judge(judge)
    assert fn("q", "a", "b") == 1
