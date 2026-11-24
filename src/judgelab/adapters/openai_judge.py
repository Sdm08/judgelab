"""OpenAI chat-completions pairwise judge factory."""
from __future__ import annotations

from judgelab.judge import Judge
from judgelab.adapters._common import DEFAULT_RUBRIC, PAIRWISE_TEMPLATE, parse_verdict


def openai_pairwise_judge(
    model: str = "gpt-4o-mini",
    rubric: str = DEFAULT_RUBRIC,
    temperature: float = 0.0,
    client=None,
    name: str | None = None,
) -> Judge:
    """Return a Judge that asks an OpenAI chat model for A/B/TIE.

    Requires `openai` installed and OPENAI_API_KEY in env (or pass `client`).
    """
    try:
        from openai import OpenAI
    except ImportError as e:
        raise ImportError("pip install 'judgelab[openai]'") from e

    if client is None:
        client = OpenAI()

    def fn(prompt: str, a: str, b: str) -> str:
        msg = PAIRWISE_TEMPLATE.format(rubric=rubric, prompt=prompt, a=a, b=b)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": msg}],
            temperature=temperature,
            max_tokens=10,
        )
        return parse_verdict(resp.choices[0].message.content or "")

    return Judge.from_callable(fn, mode="pairwise", name=name or f"openai:{model}")
