"""Auto-generate a judgelab.yaml from a dataset and optional judge."""
from __future__ import annotations

from pathlib import Path

import yaml

from judgelab.dataset import AuditSuite


def auto_config(
    dataset: str | Path,
    judge: str | Path,
    labels: str | Path | None = None,
    include_optional: bool = False,
) -> str:
    """Return a judgelab.yaml string derived by inspecting the dataset.

    Chooses checks that make sense given the data: position + verbosity
    always; agreement if labels given; self-preference if meta.model_a/b
    present; style_bias + test_retest only when include_optional=True.
    Thresholds use defaults grounded in each check's severity bands.
    """
    suite = AuditSuite.from_jsonl(dataset)
    has_pairs = any(
        ex.response_a is not None and ex.response_b is not None for ex in suite.examples
    )
    has_model_meta = any(
        (ex.meta or {}).get("model_a") and (ex.meta or {}).get("model_b")
        for ex in suite.examples
    )

    checks = ["position_bias", "verbosity_bias"] if has_pairs else []
    if labels:
        checks.append("agreement")
    if has_model_meta:
        checks.append("self_preference")
    if include_optional and has_pairs:
        checks += ["style_bias", "test_retest"]

    thresholds = {
        "position_bias__flip_rate__lt": 0.15,
        "verbosity_bias__longer_wins_rate__le": 0.60,
    }
    if "agreement" in checks:
        thresholds["agreement__cohen_kappa__gt"] = 0.60
    if "self_preference" in checks:
        thresholds["self_preference__self_preference_delta__lt"] = 0.10

    cfg = {
        "judge": str(judge),
        "dataset": str(dataset),
        **({"labels": str(labels)} if labels else {}),
        "checks": checks,
        "thresholds": thresholds,
    }
    return yaml.safe_dump(cfg, sort_keys=False)
