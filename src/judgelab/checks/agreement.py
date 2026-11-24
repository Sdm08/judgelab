"""Agreement vs human labels: Cohen's kappa, accuracy, Spearman rho."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import cohen_kappa_score
from scipy.stats import spearmanr

from judgelab.judge import Judge


def run(examples, judge: Judge, human_labels=None, **_) -> dict:
    if human_labels is None:
        return {"skipped": "no human_labels provided"}

    judge_preds = []
    humans = []
    for i, ex in enumerate(examples):
        h = human_labels.get(i)
        if h is None:
            continue
        if judge.mode == "pairwise":
            if ex.response_a is None or ex.response_b is None:
                continue
            v = judge.pairwise(ex.prompt, ex.response_a, ex.response_b).verdict
            if v is None:
                continue
            judge_preds.append(v.value)
            humans.append(str(h).upper() if isinstance(h, str) else h)
        else:
            if ex.response is None:
                continue
            s = judge.pointwise(ex.prompt, ex.response).score
            if s is None:
                continue
            judge_preds.append(s)
            humans.append(float(h))

    if len(judge_preds) < 2:
        return {"error": "need >=2 labeled examples"}

    if judge.mode == "pairwise":
        try:
            kappa = float(cohen_kappa_score(humans, judge_preds))
        except ValueError:
            kappa = float("nan")
        accuracy = float(np.mean([a == b for a, b in zip(humans, judge_preds)]))
        return {
            "n_labeled": len(humans),
            "cohen_kappa": kappa,
            "accuracy": accuracy,
            "interpretation": _kappa_interp(kappa),
        }
    else:
        rho, p = spearmanr(humans, judge_preds)
        return {
            "n_labeled": len(humans),
            "spearman_rho": float(rho),
            "spearman_p": float(p),
            "interpretation": _rho_interp(float(rho)),
        }


def _kappa_interp(k: float) -> str:
    if k != k:  # NaN
        return "undefined — need label variance"
    if k >= 0.8:
        return "excellent agreement"
    if k >= 0.6:
        return "substantial agreement"
    if k >= 0.4:
        return "moderate agreement — consider calibration"
    if k >= 0.2:
        return "fair agreement — judge unreliable"
    return "poor agreement — do not trust judge"


def _rho_interp(r: float) -> str:
    if r >= 0.7:
        return "strong rank correlation"
    if r >= 0.4:
        return "moderate rank correlation"
    return "weak — consider calibration"
