# Changelog

## [0.4.0] - 2026-11-24

### Added
- `generate_rubric()` with heuristic and LLM modes; infers starting rubric from labeled pairs via length, keyword-lift, and markdown signals
- `DistilledJudge` and `distill()` — calibrate a cheap judge against teacher labels with Platt scaling
- `DriftMonitor` with PSI for categorical streams, mean-shift for numeric; windowed alerts with severity
- Integrations: `to_deepeval_metric`, `to_ragas_judge`, `push_report_to_langfuse`
- GitHub Action (`action.yml`) and reusable workflow (`.github/workflows/judgelab.yml`)

## [0.3.0] - 2026-11-24

### Added
- Calibration module: `PlattCalibrator`, `IsotonicCalibrator`, `tune_threshold`
- Built-in LLM adapters: `openai_pairwise_judge`, `anthropic_pairwise_judge`, `litellm_pairwise_judge`
- Shared adapter prompt template + `parse_verdict` helper

### Changed
- `AuditSuite.run()` now forwards extra kwargs to each check (`judge_model`, `styles`, `rubric_variants`, `judge_factory`, `repeats`, ...)

## [0.2.0] - 2026-11-24

### Added
- `self_preference` check — detect judge bias toward its own model's output
- `style_bias` check — markdown, confidence, politeness axes
- `rubric_stability` check — stability across paraphrased rubrics
- `test_retest` check — repeatability under identical reruns
- `parallel_map` helper for thread-pooled I/O-bound judge calls

## [0.1.0] - 2026-11-24

### Added
- Core `Judge` wrapper, pairwise + pointwise modes
- `AuditSuite` with JSONL dataset loader
- `HumanLabels` from CSV
- Checks: `position_bias`, `verbosity_bias`, `agreement`
- HTML + JSON report with severity interpretation
- CLI (`judgelab audit`, `judgelab ci`) with threshold gating
- Security hardening: Jinja2 autoescape, cwd sandbox, size limits, pinned dep upper bounds
- `SECURITY.md` threat model
