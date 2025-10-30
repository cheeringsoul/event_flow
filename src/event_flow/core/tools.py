"""Utility functions for the event flow framework.

This module provides helper functions for working with sync and async code.
"""

import asyncio
import functools
import inspect

from typing import Callable


def ensure_async(callback: Callable):
    """Convert a synchronous function to async, or return it unchanged if already async.

    This utility ensures that any callable can be awaited, wrapping synchronous
    functions to run in a thread pool executor.

    Args:
        callback: A callable function (sync or async)

    Returns:
        An async function that can be awaited

    Example:
        def sync_func():
            return "hello"

        async_func = ensure_async(sync_func)
        result = await async_func()  # Works even though original was sync
    """
    if inspect.iscoroutinefunction(callback):
        return callback

    @functools.wraps(callback)
    async def async_func(*args, **kwargs):
        return await asyncio.to_thread(callback, *args, **kwargs)

    return async_func
