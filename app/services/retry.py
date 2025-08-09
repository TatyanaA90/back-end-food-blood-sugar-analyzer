"""
Backend-style retry utilities to mirror frontend retry patterns.

Features:
- retry_async: async retry with exponential backoff and optional jitter
- retry_sync: sync retry wrapper
"""
from __future__ import annotations

import asyncio
import random
from typing import Any, Awaitable, Callable, Optional, TypeVar

T = TypeVar("T")


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 5,
    base_delay_ms: int = 300,
    factor: float = 1.8,
    jitter: bool = True,
    on_attempt: Optional[Callable[[int, Optional[Exception]], None]] = None,
) -> T:
    attempt = 1
    while True:
        try:
            if on_attempt:
                on_attempt(attempt, None)
            return await fn()
        except Exception as exc:  # pylint: disable=broad-except
            if on_attempt:
                on_attempt(attempt, exc)
            if attempt >= max_attempts:
                raise
            delay = int(base_delay_ms * (factor ** (attempt - 1)))
            if jitter:
                delay += random.randint(0, 100)
            await asyncio.sleep(delay / 1000.0)
            attempt += 1


def retry_sync(
    fn: Callable[[], T],
    *,
    max_attempts: int = 5,
    base_delay_ms: int = 300,
    factor: float = 1.8,
    jitter: bool = True,
    on_attempt: Optional[Callable[[int, Optional[Exception]], None]] = None,
) -> T:
    attempt = 1
    while True:
        try:
            if on_attempt:
                on_attempt(attempt, None)
            return fn()
        except Exception as exc:  # pylint: disable=broad-except
            if on_attempt:
                on_attempt(attempt, exc)
            if attempt >= max_attempts:
                raise
            delay = int(base_delay_ms * (factor ** (attempt - 1)))
            if jitter:
                delay += random.randint(0, 100)
            # sleep in sync code
            import time
            time.sleep(delay / 1000.0)
            attempt += 1


