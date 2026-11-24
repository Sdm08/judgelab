"""Anthropic Claude pairwise judge factory."""
from __future__ import annotations

from judgelab.judge import Judge
from judgelab.adapters._common import DEFAULT_RUBRIC, PAIRWISE_TEMPLATE, parse_verdict


def anthropic_pairwise_judge(
    model: str = "claude-haiku-5-5",
    rubric: str = DEFAULT_RUBRIC,
    temperature: float = 0.0,
    client=None,
    name: str | None = None,
) -> Judge:
    """Return a Judge that asks Anthropic Claude for A/B/TIE.

    Requires `anthropic` installed and ANTHROPIC_API_KEY in env.
    """
    try:
        import anthropic
    except ImportError as e:
        raise ImportError("pip install 'judgelab[anthropic]'") from e

    if client is None:
        client = anthropic.Anthropic()

    def fn(prompt: str, a: str, b: str) -> str:
        msg = PAIRWISE_TEMPLATE.format(rubric=rubric, prompt=prompt, a=a, b=b)
        resp = client.messages.create(
            model=model,
            max_tokens=10,
            temperature=temperature,
            messages=[{"role": "user", "content": msg}],
        )
        text = "".join(block.text for block in resp.content if hasattr(block, "text"))
        return parse_verdict(text)

    return Judge.from_callable(fn, mode="pairwise", name=name or f"anthropic:{model}")
