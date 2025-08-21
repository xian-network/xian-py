"""Utility helpers for running async functions synchronously.

This module exposes a single helper :func:`run_sync` which will take
an awaitable and execute it to completion, returning its result.  If
no event loop is currently running, it simply defers to
``asyncio.run()``.  If there is already an event loop running (for
example in a notebook or within an async web framework), a new
temporary loop is spun up in a background thread to avoid
``RuntimeError: This event loop is already running``.

Note: this is a best effort helper – async/await is inherently
designed for cooperative concurrency.  When possible, prefer calling
the underlying async functions directly instead of using this
function.  This helper exists to ease migration of synchronous code
paths.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Awaitable, TypeVar

T = TypeVar("T")


def run_sync(awaitable: Awaitable[T]) -> T:
    """Execute an awaitable and return its result synchronously.

    If called outside of any running event loop, this simply wraps
    :func:`asyncio.run`.  If called from within a running loop,
    the coroutine is executed in a fresh event loop within a new
    thread.  This prevents attempts to nest ``asyncio.run`` inside an
    existing loop, which would otherwise raise a ``RuntimeError``.

    Parameters
    ----------
    awaitable: Awaitable[T]
        The coroutine or awaitable object to execute.

    Returns
    -------
    T
        The result of awaiting the provided awaitable.
    """
    try:
        # If there is no running loop, we can safely call asyncio.run
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    # Running inside an event loop – spin up a separate thread
    result_container: dict[str, Any] = {}

    def _run() -> None:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            result_container["result"] = new_loop.run_until_complete(awaitable)
        finally:
            new_loop.close()

    t = threading.Thread(target=_run)
    t.start()
    t.join()
    return result_container["result"]
