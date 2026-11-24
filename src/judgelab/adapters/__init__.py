"""Adapters that wrap popular LLM clients as judgelab Judges.

Adapters are optional: the underlying client is imported lazily so that
users without those libraries installed are not affected.
"""
from judgelab.adapters.openai_judge import openai_pairwise_judge
from judgelab.adapters.anthropic_judge import anthropic_pairwise_judge
from judgelab.adapters.litellm_judge import litellm_pairwise_judge

__all__ = [
    "openai_pairwise_judge",
    "anthropic_pairwise_judge",
    "litellm_pairwise_judge",
]
