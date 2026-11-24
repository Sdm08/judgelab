# judgelab

**You eval your model. Who evals your judge?**

`judgelab` audits LLM-as-judge pipelines for **bias**, **human agreement**, and **stability** — before you trust them in production or CI.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)

---

## Why

Modern LLM eval stacks (DeepEval, Ragas, Braintrust, LangSmith, Langfuse) all rely on **LLM-as-judge**: one model scores another model's output. But judges are biased, and nobody audits them:

- **Position bias** — prefers option A regardless of content (flip rate up to ~30% on GPT-4 judges, per MT-Bench)
- **Verbosity bias** — longer answer wins unfairly
- **Self-preference** — model rates its own output higher
- **Rubric drift** — small prompt changes flip scores
- **Low human agreement** — judge κ with humans often below 0.6

Existing tools *ship* judges. **`judgelab` audits them.** Plug it into any stack.

---

## Install

```bash
pip install judgelab
# or from source
pip install git+https://github.com/Sdm08/judgelab.git
```

Optional extras:

```bash
pip install "judgelab[openai,anthropic,litellm]"
```

---

## Quick start

### 1. Write any judge callable

```python
from judgelab import Judge

def my_judge(prompt: str, response_a: str, response_b: str) -> str:
    # call your model (OpenAI, Anthropic, local, anything)
    # return "A", "B", or "tie"
    ...

judge = Judge.from_callable(my_judge, name="gpt-4-judge")
```

### 2. Run audit

```python
from judgelab import AuditSuite

suite = AuditSuite.from_jsonl("eval.jsonl")
report = suite.run(judge, checks=["position_bias", "verbosity_bias", "agreement"])

report.to_html("report.html")
print(report.to_json())
```

### 3. Gate CI

```python
report.assert_thresholds(
    position_bias__flip_rate__lt=0.15,
    agreement__cohen_kappa__gt=0.6,
)
```

That's it. No API keys needed — judgelab makes zero LLM calls. Your judge callable does the work; judgelab just audits it.

---

## CLI

```bash
# one-shot audit
judgelab audit \
  --judge my_judge.py \
  --dataset eval.jsonl \
  --labels human.csv \
  --out report/

# CI mode — exit non-zero on threshold breach
judgelab ci --config judgelab.yaml
```

`judgelab.yaml`:

```yaml
judge: my_judge.py
dataset: eval.jsonl
labels: human.csv
checks:
  - position_bias
  - verbosity_bias
  - agreement
thresholds:
  position_bias__flip_rate__lt: 0.15
  agreement__cohen_kappa__gt: 0.6
```

---

## Checks (v0.1)

| Check | What it measures | Key metric |
|---|---|---|
| `position_bias` | Flip rate after swapping A/B order | `flip_rate`, `positional_preference` |
| `verbosity_bias` | Correlation of length with winning | `length_win_correlation`, `longer_wins_rate` |
| `agreement` | Judge vs human labels | Cohen's κ (pairwise) or Spearman ρ (pointwise) |

Every check returns a numeric score **and** a plain-English interpretation (`excellent` → `severe`).

---

## Data formats

**Dataset** — JSONL, one example per line:

```json
{"prompt": "Explain gravity.", "response_a": "Pulls things down.", "response_b": "Gravity is a fundamental force..."}
```

**Human labels** — CSV with `index,label`:

```csv
index,label
0,A
1,B
2,tie
```

Labels are optional; `agreement` check is skipped if absent.

---

## Pairwise vs pointwise

Judges come in two flavours. judgelab supports both:

```python
# pairwise: returns "A" | "B" | "tie"
Judge.from_callable(fn, mode="pairwise")

# pointwise: returns a float score
Judge.from_callable(fn, mode="pointwise")
```

Position/verbosity bias checks require **pairwise**. Agreement works for either.

---

## Reports

**HTML** — self-contained, offline-viewable, color-coded severity. Safe for sharing (full Jinja2 autoescape enabled).

**JSON** — structured output for piping into other tools (Langfuse, Grafana, Slack bots).

---

## CI integration

GitHub Actions example:

```yaml
name: judge-audit
on: [pull_request]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install judgelab
      - run: judgelab ci --config judgelab.yaml
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

Non-zero exit blocks the PR. Attach `report/report.html` as an artifact for reviewers.

---

## Positioning

- **Not** a replacement for DeepEval / Ragas / Braintrust — plugs into them.
- **Not** an eval runner — audits the judges your eval runner uses.
- **Not** a safety / red-team tool — orthogonal concern.

Think of it as the **meta-eval layer**: *eval the eval*.

---

## Security

- Zero network calls, zero LLM calls, zero required API keys.
- Judge files loaded only from inside cwd by default (RCE guard).
- HTML reports always escape user content (XSS guard).
- Dataset size + field length limited by env vars.

See [SECURITY.md](SECURITY.md) for threat model, mitigations, and reporting process.

---

## Roadmap

**v0.2**
- Self-preference bias
- Style bias (markdown, confidence hedges)
- Rubric stability (paraphrase sensitivity, few-shot shuffle)
- Test-retest reliability
- Async parallel judge calls

**v0.3**
- Calibration: Platt scaling, isotonic regression, threshold tuning
- Built-in adapters: OpenAI, Anthropic, litellm
- Integrations: DeepEval, Ragas, Langfuse

**v0.4+**
- Auto-rubric generation from human labels
- Small-model judge distillation with calibration
- Judge drift monitoring in production
- GitHub Action marketplace entry

---

## Development

```bash
git clone https://github.com/Sdm08/judgelab.git
cd judgelab
pip install -e ".[dev]"
pytest -q
```

Runs all checks (8 tests) in ~1.5s.

---

## Contributing

Issues and PRs welcome. Especially valuable:

- Bias checks grounded in published papers
- Adapters for new eval frameworks
- Reproductions of known judge biases (MT-Bench, AlpacaEval, Arena-Hard)

---

## License

MIT — see [LICENSE](LICENSE).

---

## Citation

If judgelab helps your research or product:

```bibtex
@software{judgelab,
  title = {judgelab: auditing LLM-as-judge pipelines},
  year = {2026},
  url = {https://github.com/Sdm08/judgelab}
}
```
