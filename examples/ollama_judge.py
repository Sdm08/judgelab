"""Real pairwise judge backed by a local Ollama model.

Usage:
    judgelab audit --judge examples/ollama_judge.py --dataset examples/sample_dataset.jsonl --out report/
"""
from __future__ import annotations

import json
import os
import urllib.request

from judgelab import Judge
from judgelab.adapters._common import DEFAULT_RUBRIC, PAIRWISE_TEMPLATE, parse_verdict

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e2b-it-qat")


def _chat(messages: list[dict], model: str = MODEL, temperature: float = 0.0) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,   # disable thinking preamble for thinking-capable models
            "options": {"temperature": temperature, "num_predict": 32},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return (body.get("message") or {}).get("content", "")


def ollama_judge(prompt: str, a: str, b: str) -> str:
    msg = PAIRWISE_TEMPLATE.format(rubric=DEFAULT_RUBRIC, prompt=prompt, a=a, b=b)
    text = _chat([{"role": "user", "content": msg}])
    return parse_verdict(text)


judge = Judge.from_callable(ollama_judge, mode="pairwise", name=f"ollama:{MODEL}")
