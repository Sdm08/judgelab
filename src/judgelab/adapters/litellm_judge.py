"""LiteLLM universal pairwise judge factory: works with 100+ providers."""
from __future__ import annotations

from judgelab.judge import Judge
from judgelab.adapters._common import DEFAULT_RUBRIC, PAIRWISE_TEMPLATE, parse_verdict


def litellm_pairwise_judge(
    model: str = "gpt-4o-mini",
    rubric: str = DEFAULT_RUBRIC,
    temperature: float = 0.0,
    name: str | None = None,
    **extra,
) -> Judge:
    """Return a Judge that routes through LiteLLM.

    Pass any litellm.completion kwargs via **extra (api_base, api_key, etc.).
    """
    try:
        import litellm
    except ImportError as e:
        raise ImportError("pip install 'judgelab[litellm]'") from e

    def fn(prompt: str, a: str, b: str) -> str:
        msg = PAIRWISE_TEMPLATE.format(rubric=rubric, prompt=prompt, a=a, b=b)
        resp = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": msg}],
            temperature=temperature,
            max_tokens=10,
            **extra,
        )
        return parse_verdict(resp.choices[0].message.content or "")

    return Judge.from_callable(fn, mode="pairwise", name=name or f"litellm:{model}")
