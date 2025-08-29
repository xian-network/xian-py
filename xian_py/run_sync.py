from __future__ import annotations

import asyncio
import threading
from typing import Awaitable, TypeVar, Optional

T = TypeVar("T")

def run_sync(
    awaitable: Awaitable[T],
    *,
    allow_thread: bool = False,
    thread_name: str = "xian-run-sync",
) -> T:
    """
    Run an awaitable from synchronous code.

    Behavior:
    - If NO event loop is running in this thread, use `asyncio.run(awaitable)`.
    - If a loop IS running:
        * By default raise a RuntimeError (safe, matches #4’s strict wrapper stance).
        * If `allow_thread=True`, execute the awaitable on a NEW event loop in a
          dedicated background thread. This is an advanced escape hatch: mind
          contextvars, thread-affinity, and graceful shutdown.

    Returns:
        The awaitable's result or re-raises its exception.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop -> the simple, safe path.
        return asyncio.run(awaitable)

    if not allow_thread:
        raise RuntimeError(
            "run_sync() called while an event loop is running. "
            "Use the async API directly, or call run_sync(..., allow_thread=True) "
            "if you explicitly want to run this in a separate thread (advanced)."
        )

    result: Optional[T] = None
    err: Optional[BaseException] = None

    def _worker() -> None:
        nonlocal result, err
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(awaitable)
        except BaseException as e:
            err = e
        finally:
            try:
                loop.close()
            except Exception:
                pass

    t = threading.Thread(target=_worker, name=thread_name, daemon=True)
    t.start()
    t.join()

    if err:
        raise err
    return result  # type: ignore[return-value]
