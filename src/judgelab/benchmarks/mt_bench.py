"""MT-Bench style position-bias reproduction.

Zheng et al. (2023) reported LLM judges flip ~25-30% of verdicts when
A/B order is swapped. This module runs the same experiment on a judge
and reports the flip rate alongside the literature baseline.

The bundled fixture is a 20-pair sample distilled from MT-Bench style
prompts (literature-grounded; not the full benchmark). For the full
run use `load_mt_bench_fixture(variant="full")` after placing the
official file under `judgelab/benchmarks/data/mt_bench_full.jsonl`.
"""
from __future__ import annotations

from pathlib import Path

from judgelab.dataset import AuditSuite
from judgelab.judge import Judge


LITERATURE_BASELINE = {
    "gpt-4": 0.26,     # Zheng et al. 2023, Table 4
    "gpt-3.5": 0.46,
    "claude-v1": 0.48,
}


def load_mt_bench_fixture(variant: str = "sample") -> AuditSuite:
    here = Path(__file__).parent / "data"
    path = here / ("mt_bench_full.jsonl" if variant == "full" else "mt_bench_sample.jsonl")
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return AuditSuite.from_jsonl(path)


def run_mt_bench_position_bias(judge: Judge, variant: str = "sample") -> dict:
    suite = load_mt_bench_fixture(variant=variant)
    report = suite.run(judge, checks=["position_bias"])
    pb = report.checks["position_bias"]
    return {
        "judge": judge.name,
        "variant": variant,
        "n_examples": report.n_examples,
        "flip_rate": pb.get("flip_rate"),
        "positional_preference": pb.get("positional_preference"),
        "literature_baseline": LITERATURE_BASELINE,
        "interpretation": pb.get("interpretation"),
    }
