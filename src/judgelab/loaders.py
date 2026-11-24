"""Alternate dataset loaders: HuggingFace, in-memory pandas, Arena-style."""
from __future__ import annotations

from judgelab.dataset import AuditSuite, Example


def from_huggingface(
    path: str,
    split: str = "train",
    revision: str | None = None,
    prompt_field: str = "prompt",
    response_a_field: str = "response_a",
    response_b_field: str = "response_b",
    meta_fields: list[str] | None = None,
    limit: int | None = None,
) -> AuditSuite:
    """Load pairwise examples from a HuggingFace dataset.

    Requires `datasets` installed: pip install 'judgelab[hf]'.

    For supply-chain safety, pass `revision=` pinning to a specific
    commit/tag so a repo takeover can't swap dataset contents under you.
    """
    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError("pip install 'judgelab[hf]'") from e

    if revision is None:
        import warnings
        warnings.warn(
            f"from_huggingface('{path}') called without revision pinning; "
            "pass revision=<commit-or-tag> to protect against upstream changes.",
            stacklevel=2,
        )
    ds = load_dataset(path, split=split, revision=revision)
    if limit is not None:
        ds = ds.select(range(min(limit, len(ds))))

    examples: list[Example] = []
    for row in ds:
        meta = {k: row[k] for k in (meta_fields or []) if k in row}
        examples.append(
            Example(
                prompt=row[prompt_field],
                response_a=row.get(response_a_field),
                response_b=row.get(response_b_field),
                meta=meta,
            )
        )
    return AuditSuite(examples)


def from_pandas(
    df,
    prompt_col: str = "prompt",
    response_a_col: str = "response_a",
    response_b_col: str = "response_b",
) -> AuditSuite:
    examples = [
        Example(
            prompt=row[prompt_col],
            response_a=row.get(response_a_col),
            response_b=row.get(response_b_col),
        )
        for _, row in df.iterrows()
    ]
    return AuditSuite(examples)
