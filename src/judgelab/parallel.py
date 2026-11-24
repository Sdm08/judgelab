"""Parallel execution helpers for judges.

Judges are frequently network-bound (LLM calls). Running them serially is
wasteful. `parallel_map` uses a thread pool (safe for I/O-bound callables)
to batch pairwise or pointwise judge calls.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def parallel_map(
    fn: Callable[[T], R],
    items: Iterable[T],
    workers: int = 8,
    ordered: bool = True,
) -> list[R]:
    """Map `fn` over `items` across a thread pool.

    Preserves input order when `ordered=True`.
    Exceptions propagate (first failure raises).
    """
    items = list(items)
    if workers <= 1 or len(items) <= 1:
        return [fn(x) for x in items]

    results: list[R] = [None] * len(items)  # type: ignore[list-item]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(fn, item): i for i, item in enumerate(items)}
        for fut in as_completed(futures):
            i = futures[fut]
            results[i] = fut.result()
    return results
