# Changelog

## [0.1.0] - 2026-11-24

Initial release.

### Core
- `Judge` wrapper with pairwise and pointwise modes, result auto-coercion
- `AuditSuite` with JSONL dataset loader and `from_pairs` constructor
- `HumanLabels` from CSV
- HTML + JSON reports with severity interpretation
- CLI (`judgelab audit`, `judgelab ci`) with threshold gating
- `parallel_map` helper for I/O-bound judge calls

### Checks
- `position_bias` — flip rate under A/B order swap
- `verbosity_bias` — length-win correlation and rate
- `agreement` — Cohen's κ (pairwise) or Spearman ρ (pointwise)
- `self_preference` — bias toward the judge's own model
- `style_bias` — markdown, confidence, politeness axes
- `rubric_stability` — stability across paraphrased rubrics
- `test_retest` — repeatability under identical reruns

### Calibration
- `PlattCalibrator` — logistic mapping of judge score to P(human = A)
- `IsotonicCalibrator` — monotonic mapping to human scale
- `tune_threshold` — pick cutoff that maximises accuracy, F1 or Cohen's κ

### Adapters
- `openai_pairwise_judge`
- `anthropic_pairwise_judge`
- `litellm_pairwise_judge`

Backends imported lazily.

### Rubric and distillation
- `generate_rubric` — heuristic and LLM modes; infers rubric from labeled pairs
- `distill` + `DistilledJudge` — Platt-calibrated cheap judge against teacher labels

### Monitoring
- `DriftMonitor` — windowed PSI for categorical streams, mean-shift for numeric; severity-tagged alerts

### Integrations
- `to_deepeval_metric`
- `to_ragas_judge`
- `push_report_to_langfuse`

### DevOps
- GitHub Action (`action.yml`) and reusable workflow for PR-blocking audits

### Security
- Jinja2 autoescape on HTML report
- cwd sandbox for judge loading and report output (override via `JUDGELAB_ALLOW_ANY_PATH`)
- `yaml.safe_load` only
- Size limits on fields and datasets (`JUDGELAB_MAX_FIELD_CHARS`, `JUDGELAB_MAX_EXAMPLES`)
- Upper-bounded dependency versions
- Bandit, Ruff security rules, and pip-audit clean on release
