"""Decorators for defining event handlers, timers, and background tasks.

This module provides decorators to mark methods in Application classes for
special behavior in the event flow framework.
"""

import asyncio
import inspect

from dataclasses import dataclass
from functools import wraps
from typing import Union, Type

from event_flow.core.event import Event


@dataclass
class TimerDetail:
    """Configuration details for a timer-based task.

    Attributes:
        interval: Time in seconds between task executions
        run_at_once: Whether to execute the task immediately on startup
    """
    interval: Union[float, int]
    run_at_once: bool = True


def timer(interval: Union[float, int], run_at_once=True):
    """Decorator to mark a method as a periodic timer task.

    The decorated method will be executed repeatedly at the specified interval.
    Can be used with both sync and async functions.

    Args:
        interval: Time in seconds between executions
        run_at_once: If True, run immediately on startup before waiting for interval

    Returns:
        Decorated function that will be executed on a timer

    Raises:
        TypeError: If interval is not a numeric type

    Example:
        @timer(interval=5.0)
        async def check_status(self):
            print("Checking status every 5 seconds")
    """
    if not isinstance(interval, (int, float,)):
        raise TypeError(f'interval must be int or float')

    def new_func(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def wrapped_func(*args, **kwargs):
                return await func(*args, **kwargs)
        else:
            @wraps(func)
            async def wrapped_func(*args, **kwargs):
                return await asyncio.to_thread(func, *args, **kwargs)
        wrapped_func.__timer__ = TimerDetail(interval, run_at_once)
        return wrapped_func

    return new_func


def task(func):
    """Decorator to mark a method as a long-running background task.

    The decorated method will be started once when the application starts
    and should run indefinitely or until completion. Can be used with both
    sync and async functions.

    Args:
        func: The function to run as a background task

    Returns:
        Decorated async function

    Example:
        @task
        async def process_queue(self):
            while True:
                await self.handle_next_item()
    """
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def wrapped_func(*args, **kwargs):
            return await func(*args, **kwargs)
    else:
        @wraps(func)
        async def wrapped_func(*args, **kwargs):
            return await asyncio.to_thread(func, *args, **kwargs)
    wrapped_func.__background_task__ = True
    return wrapped_func


def on_event(event: Type[Event]):
    """Decorator to register a method as an event handler.

    The decorated method will be called whenever an event of the specified
    type is published. Can be used with both sync and async functions.

    Args:
        event: The Event class type to listen for

    Returns:
        Decorator function that marks the method as an event handler

    Example:
        @on_event(MyCustomEvent)
        async def handle_custom_event(self, events: List[MyCustomEvent]):
            for event in events:
                print(f"Received: {event.data}")
    """
    def new_func(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def wrapped_func(*args, **kwargs):
                return await func(*args, **kwargs)
        else:
            @wraps(func)
            async def wrapped_func(*args, **kwargs):
                return await asyncio.to_thread(func, *args, **kwargs)
        wrapped_func.__related_event__ = event
        return wrapped_func

    return new_func
