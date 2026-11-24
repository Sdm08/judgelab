"""Report: JSON + HTML output, threshold assertions for CI."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, select_autoescape


_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>judgelab — {{ judge_name }}</title>
<style>
body { font-family: -apple-system, system-ui, sans-serif; max-width: 900px; margin: 2em auto; padding: 0 1em; color: #222; }
h1 { border-bottom: 2px solid #333; padding-bottom: .3em; }
.check { background: #f7f7f9; border-left: 4px solid #4a7; padding: 1em 1.2em; margin: 1em 0; border-radius: 4px; }
.check.warn { border-left-color: #e90; }
.check.bad { border-left-color: #c33; }
table { border-collapse: collapse; margin: .5em 0; }
td, th { padding: .3em .8em; border-bottom: 1px solid #ddd; text-align: left; }
.metric { font-family: ui-monospace, monospace; font-weight: bold; }
.interp { font-style: italic; color: #555; }
</style></head><body>
<h1>judgelab report</h1>
<p><strong>Judge:</strong> {{ judge_name }} &nbsp; | &nbsp; <strong>Examples:</strong> {{ n_examples }}</p>
{% for name, data in checks.items() %}
<div class="check {{ severity(data) }}">
<h2>{{ name }}</h2>
{% if data.get('skipped') %}
<p><em>skipped: {{ data.skipped }}</em></p>
{% elif data.get('error') %}
<p><em>error: {{ data.error }}</em></p>
{% else %}
<table>
{% for k, v in data.items() if k not in ['per_example', 'interpretation'] %}
<tr><th>{{ k }}</th><td class="metric">{{ fmt(v) }}</td></tr>
{% endfor %}
</table>
{% if data.get('interpretation') %}<p class="interp">{{ data.interpretation }}</p>{% endif %}
{% endif %}
</div>
{% endfor %}
</body></html>
"""


def _fmt(v):
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def _severity(data: dict) -> str:
    interp = str(data.get("interpretation", "")).lower()
    if "severe" in interp or "poor" in interp:
        return "bad"
    if "concerning" in interp or "fair" in interp or "mild" in interp:
        return "warn"
    return ""


@dataclass
class Report:
    judge_name: str
    n_examples: int
    checks: dict = field(default_factory=dict)

    def to_json(self, path: str | Path | None = None) -> str:
        data = {"judge": self.judge_name, "n_examples": self.n_examples, "checks": self.checks}
        s = json.dumps(data, indent=2, default=str)
        if path:
            _safe_write(path, s)
        return s

    def to_html(self, path: str | Path | None = None) -> str:
        env = Environment(autoescape=select_autoescape(default=True, default_for_string=True))
        tpl = env.from_string(_HTML)
        html = tpl.render(
            judge_name=self.judge_name,
            n_examples=self.n_examples,
            checks=self.checks,
            fmt=_fmt,
            severity=_severity,
        )
        if path:
            _safe_write(path, html)
        return html

    def assert_thresholds(self, **thresholds) -> None:
        """Raise AssertionError if any threshold breached.

        Syntax: metric__op=value
          op in {lt, le, gt, ge, eq}
          metric is a flat path, e.g. 'position_bias__flip_rate__lt=0.15'
          Simple form: '<check>__lt=value' inspects first numeric metric.
        """
        failures = []
        for key, bound in thresholds.items():
            parts = key.split("__")
            if len(parts) < 2:
                raise ValueError(f"Bad threshold key: {key}")
            op = parts[-1]
            path = parts[:-1]
            val = self._resolve(path)
            if val is None:
                failures.append(f"{key}: path not found")
                continue
            if not _cmp(val, op, bound):
                failures.append(f"{'.'.join(path)}={val} fails {op} {bound}")
        if failures:
            raise AssertionError("judgelab thresholds failed:\n  " + "\n  ".join(failures))

    def _resolve(self, path: list[str]):
        node = self.checks
        for p in path:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                # fall back: single-segment path -> first numeric metric in that check
                if len(path) == 1 and p in self.checks:
                    inner = self.checks[p]
                    for v in inner.values():
                        if isinstance(v, (int, float)):
                            return v
                return None
        return node if isinstance(node, (int, float)) else None


def _safe_write(path: str | Path, content: str) -> None:
    """Write text, refusing paths that resolve outside the current working directory
    unless JUDGELAB_ALLOW_ANY_PATH=1 is set."""
    import os
    p = Path(path).resolve()
    if os.environ.get("JUDGELAB_ALLOW_ANY_PATH") != "1":
        cwd = Path.cwd().resolve()
        try:
            p.relative_to(cwd)
        except ValueError:
            raise PermissionError(
                f"Refusing to write outside cwd: {p}. "
                "Set JUDGELAB_ALLOW_ANY_PATH=1 to override."
            )
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _cmp(val, op: str, bound) -> bool:
    return {
        "lt": val < bound,
        "le": val <= bound,
        "gt": val > bound,
        "ge": val >= bound,
        "eq": val == bound,
    }[op]
