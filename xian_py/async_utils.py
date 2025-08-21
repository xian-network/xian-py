"""
Utilities for async/sync compatibility
"""
import asyncio
import functools
from typing import TypeVar, Callable, Any, Coroutine

T = TypeVar('T')


def sync_wrapper(async_func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., T]:
    """
    Decorator that creates a synchronous wrapper for an async function.
    
    This allows async functions to be called from synchronous code by
    automatically managing the event loop.
    """
    @functools.wraps(async_func)
    def wrapper(*args, **kwargs) -> T:
        try:
            # Try to get the running event loop
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop is running, so we can safely use asyncio.run
            return asyncio.run(async_func(*args, **kwargs))
        else:
            # We're already in an async context, which shouldn't happen
            # for a sync wrapper, but handle it gracefully
            raise RuntimeError(
                f"Cannot call sync wrapper for {async_func.__name__} from within "
                "an async context. Use the async version directly."
            )
    
    # Preserve the original async function as an attribute
    wrapper._async = async_func
    return wrapper


def create_sync_version(async_func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., T]:
    """
    Creates a synchronous version of an async function.
    This is an alias for sync_wrapper for clarity.
    """
    return sync_wrapper(async_func)