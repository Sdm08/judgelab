"""Dataset + AuditSuite: load examples, orchestrate checks."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from judgelab.judge import Judge
from judgelab.report import Report

_MAX_FIELD_CHARS = int(os.environ.get("JUDGELAB_MAX_FIELD_CHARS", "200000"))
_MAX_EXAMPLES = int(os.environ.get("JUDGELAB_MAX_EXAMPLES", "100000"))


@dataclass
class Example:
    prompt: str
    response_a: str | None = None
    response_b: str | None = None
    response: str | None = None  # for pointwise
    meta: dict = field(default_factory=dict)


class AuditSuite:
    def __init__(self, examples: list[Example]):
        if not examples:
            raise ValueError("AuditSuite needs at least one example.")
        self.examples = examples

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "AuditSuite":
        examples = []
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                if len(examples) >= _MAX_EXAMPLES:
                    raise ValueError(
                        f"Dataset exceeds JUDGELAB_MAX_EXAMPLES={_MAX_EXAMPLES}"
                    )
                d = json.loads(line)
                _validate_fields(d, lineno)
                examples.append(
                    Example(
                        prompt=d["prompt"],
                        response_a=d.get("response_a"),
                        response_b=d.get("response_b"),
                        response=d.get("response"),
                        meta=d.get("meta", {}),
                    )
                )
        return cls(examples)

    @classmethod
    def from_pairs(cls, pairs: Iterable[dict]) -> "AuditSuite":
        out = []
        for i, p in enumerate(pairs):
            if len(out) >= _MAX_EXAMPLES:
                raise ValueError(f"Dataset exceeds JUDGELAB_MAX_EXAMPLES={_MAX_EXAMPLES}")
            _validate_fields(p, i)
            out.append(Example(**p))
        return cls(out)

    def run(
        self,
        judge: Judge,
        checks: list[str] | None = None,
        human_labels=None,
        **check_kwargs,
    ) -> Report:
        from judgelab.checks import registry

        checks = checks or ["position_bias", "verbosity_bias"]
        results: dict = {}
        for name in checks:
            if name not in registry:
                raise KeyError(f"Unknown check: {name}. Available: {list(registry)}")
            results[name] = registry[name](
                self.examples, judge, human_labels=human_labels, **check_kwargs
            )
        return Report(judge_name=judge.name, n_examples=len(self.examples), checks=results)


def _validate_fields(d: dict, where) -> None:
    for key in ("prompt", "response_a", "response_b", "response"):
        v = d.get(key)
        if v is not None and not isinstance(v, str):
            raise TypeError(f"Field '{key}' must be str at {where}, got {type(v).__name__}")
        if isinstance(v, str) and len(v) > _MAX_FIELD_CHARS:
            raise ValueError(
                f"Field '{key}' at {where} exceeds JUDGELAB_MAX_FIELD_CHARS={_MAX_FIELD_CHARS}"
            )
