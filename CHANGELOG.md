# Changelog

## [0.1.1] - 2026-11-25

### Fixed
- `action.yml` description trimmed to 99 chars to satisfy the GitHub Marketplace 125-char limit so the Action can be listed.

## [0.1.0] - 2026-11-24

Initial release.

### Benchmarks
- `benchmarks.mt_bench` — MT-Bench style position-bias reproduction with bundled 20-prompt fixture and published flip-rate baselines (Zheng et al. 2023)
- `benchmarks.leaderboard` — Markdown leaderboard builder
- Reproduced on gemma4:4.6B via Ollama → flip_rate 0.55 vs GPT-4 lit 0.26

### Calibration diagnostics
- `reliability_curve`, `ece`, `render_reliability_svg` — inline SVG reliability diagrams for HTML reports

### Dataset loaders
- `from_huggingface(..., revision=...)` with supply-chain warning when unpinned
- `from_pandas`

### Persistence and diffing
- `RunStore` SQLite-backed run history
- CLI: `judgelab list`, `judgelab diff <a> <b>` with per-metric deltas and arrows
- `--store` flag on `audit` to persist runs

### Config generation
- `judgelab init` inspects dataset + judge and emits a tailored `judgelab.yaml`
- Auto-selects checks (adds `agreement` when labels given, `self_preference` when meta.model_a/b present)

### Langfuse integration
- `push_report_to_langfuse(report, create_trace=True)` creates a dedicated judgelab-audit trace carrying the report JSON and attaches every numeric metric as a score, with interpretation comment

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
