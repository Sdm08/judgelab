# Reading judgelab output

Every `judgelab` run produces three surfaces: a **JSON report**, an **HTML report**, and a **CLI summary**. All three carry the same data; this guide tells you how to read each number, what thresholds mean, and how to turn results into decisions.

---

## 1. Top-level JSON structure

```json
{
  "judge": "mock-biased",
  "n_examples": 10,
  "checks": {
    "position_bias":  { ... },
    "verbosity_bias": { ... },
    "agreement":      { ... }
  }
}
```

| Field | Meaning |
|---|---|
| `judge` | Name you gave the judge (`Judge(..., name=...)`) |
| `n_examples` | Dataset size |
| `checks` | One block per check you ran |

Each check block always carries an `interpretation` string plus numeric metrics specific to the check.

---

## 2. `position_bias`

```json
{
  "flip_rate": 0.7,
  "positional_preference": 0.7,
  "a_wins_original": 7,
  "a_wins_swapped": 0,
  "n": 10,
  "interpretation": "severe — judge unreliable, mitigate with order averaging",
  "per_example": [{"v1":"A","v2":"B"}, ...]
}
```

| Metric | Meaning | Good |
|---|---|---|
| `flip_rate` | Fraction where verdict changed after A↔B swap | **< 0.05** |
| `positional_preference` | Net bias toward A: `(a_wins_original − a_wins_swapped) / n`, range −1..+1 | **≈ 0** |
| `a_wins_original` | A wins in normal order | — |
| `a_wins_swapped` | A wins after swap (ideally equal to above) | — |
| `per_example` | Per-row `v1` / `v2` for debugging | — |

**Severity bands**

| flip_rate | Interpretation | Action |
|---|---|---|
| `< 0.05` | excellent — order-invariant | ship |
| `< 0.15` | acceptable | ship |
| `< 0.30` | concerning — meaningful bias | mitigate |
| `≥ 0.30` | severe — judge unreliable | **do not ship** |

**Fix recipes**
- Run judge twice (A,B then B,A); keep the verdict only when both agree.
- Add explicit instruction: *"Ignore order; judge on content alone."*
- Switch to a stronger judge model.

---

## 3. `verbosity_bias`

```json
{
  "length_win_correlation": 0.18,
  "longer_wins_rate": 0.70,
  "n": 10,
  "interpretation": "severe — judge strongly prefers longer responses"
}
```

| Metric | Meaning | Fair |
|---|---|---|
| `longer_wins_rate` | Of unequal-length pairs, how often longer won | **0.45 – 0.55** |
| `length_win_correlation` | Pearson r between `(len_a − len_b)` and `A wins`, range −1..+1 | **≈ 0** |

**Severity bands**

| longer_wins_rate | Interpretation |
|---|---|
| `0.45 – 0.55` | balanced |
| `0.55 – 0.60` | mild bias |
| `0.60 – 0.70` | concerning |
| `> 0.70` | **severe** |
| `< 0.30` | inverse bias (prefers shorter) |

**Fix recipes**
- Add to rubric: *"Length is not quality. Judge on substance."*
- Truncate responses to equal length before judging.
- Report length-controlled win rate alongside raw win rate.

---

## 4a. `self_preference`

Requires each example to carry `meta.model_a` and `meta.model_b` plus a `judge_model=<id>` kwarg naming which model the judge itself uses.

```json
{
  "judge_model": "gpt-4",
  "own_win_rate": 0.72,
  "others_mean_win_rate": 0.48,
  "self_preference_delta": 0.24,
  "comparable_pairs": 100,
  "win_rates": {"gpt-4": 0.72, "claude-3": 0.48, "llama-3": 0.49},
  "interpretation": "severe self-preference — judge biased toward own model"
}
```

| `delta` | Meaning |
|---|---|
| `< 0.05` | no self-preference |
| `0.05–0.10` | mild |
| `0.10–0.20` | concerning |
| `≥ 0.20` | **severe** |

## 4b. `style_bias`

```json
{
  "markdown":   {"styled_win_rate": 0.72, "n_comparisons": 40, "interpretation": "severe — judge favours this style strongly"},
  "confidence": {"styled_win_rate": 0.50, "n_comparisons": 40, "interpretation": "neutral — no style bias"},
  "politeness": {"styled_win_rate": 0.58, "n_comparisons": 40, "interpretation": "mild bias"}
}
```

Each style axis has its own `styled_win_rate`. Fair = 0.45–0.55. Over 0.70 = severe.

## 4c. `rubric_stability`

Requires `rubric_variants=[str,...]` and `judge_factory=callable(rubric)->Judge`.

```json
{
  "mean_stability": 0.88,
  "n_variants": 5,
  "n_examples": 100,
  "interpretation": "acceptable stability"
}
```

| `mean_stability` | Meaning |
|---|---|
| `≥ 0.95` | excellent |
| `≥ 0.85` | acceptable |
| `≥ 0.70` | concerning |
| `< 0.70` | **severe** |

## 4d. `test_retest`

### Pairwise
```json
{
  "mean_verdict_stability": 0.91,
  "repeats": 3,
  "n_examples": 30,
  "interpretation": "acceptable repeatability"
}
```

### Pointwise
```json
{
  "mean_score_variance": 0.08,
  "repeats": 3,
  "n_examples": 30,
  "interpretation": "acceptable"
}
```

Fix severe non-determinism: lower temperature on the underlying judge model.

## 5. `agreement`

Requires human labels (`AuditSuite.run(..., human_labels=HumanLabels.from_csv(...))`).

### Pairwise judges

```json
{
  "n_labeled": 100,
  "cohen_kappa": 0.62,
  "accuracy": 0.78,
  "interpretation": "substantial agreement"
}
```

| Metric | Meaning | Good |
|---|---|---|
| `cohen_kappa` | Chance-corrected agreement, range −1..+1 | **≥ 0.6** |
| `accuracy` | Raw judge-vs-human match rate | > 0.75 |

**Kappa bands (Landis & Koch, standard)**

| κ | Meaning | Action |
|---|---|---|
| `≥ 0.80` | excellent | ship |
| `0.60 – 0.80` | substantial | ship |
| `0.40 – 0.60` | moderate | calibrate before ship |
| `0.20 – 0.40` | fair | unreliable |
| `< 0.20` | poor | **do not use** |

### Pointwise judges

```json
{
  "n_labeled": 100,
  "spearman_rho": 0.71,
  "spearman_p": 0.002,
  "interpretation": "strong rank correlation"
}
```

| Metric | Meaning | Good |
|---|---|---|
| `spearman_rho` | Rank correlation with human scores | **≥ 0.7** |
| `spearman_p` | Significance | **< 0.05** |

---

## 6. CLI summary

```
Auditing mock-biased on 10 examples...
Wrote report/report.html and report.json
  position_bias: severe — judge unreliable, mitigate with order averaging
  verbosity_bias: mild bias
```

One line per check with the human interpretation. For numbers open the JSON; for a shareable report open the HTML.

---

## 7. HTML report

Open `report/report.html` in any browser. Each check is a card:

- **Green border** — safe
- **Orange border** — concerning or mild bias
- **Red border** — severe or poor; blocks ship

The card shows all numeric metrics and the plain-language interpretation. The HTML is self-contained (no external assets) and all user content is Jinja2-autoescaped, so it is safe to share.

---

## 8. CI exit codes

Threshold gating via `assert_thresholds` or the `judgelab ci` command:

```
exit 0  — all thresholds passed, PR green
exit 1  — at least one threshold failed, stderr names which:
          position_bias.flip_rate=0.7 fails lt 0.15
```

Threshold syntax: `<check>__<metric>__<op>=value`
- `op` ∈ {`lt`, `le`, `gt`, `ge`, `eq`}
- Example: `agreement__cohen_kappa__gt=0.6`

---

## 9. Decision rules (practical)

| Signal | Action |
|---|---|
| `flip_rate < 0.15` **and** `cohen_kappa > 0.6` | Ship the judge |
| `flip_rate 0.15–0.30` | Patch with order-averaging, re-run audit |
| `flip_rate > 0.30` | Replace judge model or rewrite rubric |
| `longer_wins_rate > 0.65` and κ is fine | Add length-neutral clause to rubric |
| `cohen_kappa < 0.4` | Redo rubric; judge disagrees with humans |
| `cohen_kappa < 0.2` | Judge is worthless; start over |

---

## 10. Debugging with `per_example`

Each `position_bias.per_example` entry is `{"v1": "<original>", "v2": "<swap-order, mapped back>"}`. When `v1 ≠ v2` the judge flipped on that example — inspect those prompts first. Common patterns:

- Prompts with ambiguous ground truth → flips are tolerable.
- Prompts with clear right answer → flips mean real bias.

---

## 11. Cheat sheet

```
flip_rate       low  = order-invariant
longer_wins     ~0.5 = length-neutral
cohen_kappa     high = agrees with humans
spearman_rho    high = ranks like humans
"severe" / "poor" in interpretation = block ship
```
