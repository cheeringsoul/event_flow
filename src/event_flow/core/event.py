"""Event system core classes for event-driven architecture.

This module provides the base Event classes and the internal EventEngine
for managing event publishing and handler execution.
"""

import asyncio

from asyncio import Queue
from collections import defaultdict
from loguru import logger
from typing import Any, Callable, Set, Dict, Type, List, Optional

from event_flow.core.tools import ensure_async


class Event:
    """Base class for all events in the event flow system.

    Events carry data and metadata that can be published and handled by
    registered event handlers.

    Attributes:
        data: The primary data payload of the event
        meta: Additional metadata dictionary for the event
    """
    def __init__(self, data: Any):
        self._data: Any = data
        self._meta = {}

    @property
    def data(self):
        return self._data

    @property
    def meta(self):
        return self._meta

    def update_meta(self, **kwargs):
        """Update the event metadata with additional key-value pairs.

        Args:
            **kwargs: Key-value pairs to add to metadata
        """
        self._meta.update(**kwargs)

    def parse(self) -> Any:
        """Parse and return the event data.

        Override this method in subclasses to provide custom parsing logic.

        Returns:
            The parsed event data
        """
        return self.data


class EventWithSource(Event):
    """Event that includes information about its source.

    Extends the base Event class to track which component or entity
    generated the event.

    Attributes:
        source: The originating source of the event
        data: The event data payload
        meta: Event metadata dictionary
    """
    def __init__(self, source, data):
        super().__init__(data)
        self._source = source

    @property
    def source(self):
        return self._source


class ExceptionEvent(Event):
    """Event representing an exception that occurred in the system.

    Used to publish and handle exceptions through the event system.

    Attributes:
        data: The exception instance
        traceback_str: String representation of the exception traceback
        meta: Event metadata dictionary
    """
    def __init__(self, exception, traceback_str):
        super().__init__(exception)
        self.traceback_str = traceback_str


class _EventEngine:
    """Internal engine for managing event publishing and handler execution.

    This class handles the event queue, dispatches events to registered handlers,
    and manages the event processing lifecycle. Not intended for direct use.

    Attributes:
        _active: Whether the engine is currently running
        _queue: Async queue for event processing
        _tasks: Set of running event handler tasks
        _handlers: Mapping of event types to their handler functions
    """
    def __init__(self):
        self._active: bool = False
        self._queue: Optional[Queue] = None
        self._tasks: Set = set()
        self._handlers: Dict[Type[Event], List[Callable]] = defaultdict(list)

    def register_handler(self, event_type: Type[Event], *handlers: Callable):
        """Register one or more handlers for a specific event type.

        Args:
            event_type: The Event class to handle
            *handlers: Handler functions (sync or async) to register
        """
        async_handlers = [ensure_async(each) for each in handlers]
        self._handlers[event_type].extend(async_handlers)

    async def pub_event(self, event: Event):
        """Publish an event to be processed by registered handlers.

        Args:
            event: The Event instance to publish
        """
        await self._queue.put(event)

    def stop(self):
        """Stop the event engine from processing events."""
        self._active = False

    async def start(self):
        """Start the event engine and begin processing events from the queue.

        Runs continuously while active, batching events of the same type
        when possible for efficient processing.
        """
        self._queue = Queue(maxsize=10)
        if self._active:
            logger.info('EventEngine is already up and running.')
            return
        self._active = True
        while self._active:
            if self._queue.empty():
                event: Event = await self._queue.get()
                self.process_event([event])
            else:
                events: Dict[Type[Event], List[Event]] = defaultdict(list)
                qsize = self._queue.qsize()
                for _ in range(qsize):
                    event = await self._queue.get()
                    events[event.__class__].append(event)
                for each in events.values():
                    self.process_event(each)

    def process_event(self, event: List[Event]):
        """Process a batch of events by invoking their registered handlers.

        Args:
            event: List of Event instances of the same type to process
        """
        if handlers := self._handlers[event[0].__class__]:
            for handler in handlers:
                t = asyncio.create_task(handler(event))
                self._tasks.add(t)
                t.add_done_callback(self._tasks.discard)
