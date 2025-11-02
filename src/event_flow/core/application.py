"""Core application classes and metaclasses for the event flow framework.

This module provides the main Application class, AppEngine for managing multiple
applications, and the metaclass infrastructure for automatic event handler registration.
"""

import asyncio
import dataclasses
import inspect
import threading
import typing

from abc import ABCMeta, abstractmethod
from aiohttp import web
from collections import defaultdict
from copy import copy
from loguru import logger
from typing import Callable, Dict, Optional, List, Type, Union, Set

from event_flow.core.event import Event, _EventEngine
from event_flow.core.tools import ensure_async


@dataclasses.dataclass
class TimerDetail:
    """Configuration for timer-based tasks.

    Attributes:
        interval: Seconds between executions
        run_at_once: Whether to execute immediately on startup
    """
    interval: Union[float, int]
    run_at_once: bool = True


class Registry(metaclass=ABCMeta):
    """Abstract base class for registries that store method metadata.

    Registries are used by the metaclass to track which methods should be
    called for timers, events, and other special behaviors.
    """
    @abstractmethod
    def register(self, *args, **kwargs): ...

    @abstractmethod
    def items(self): ...

    @abstractmethod
    def copy(self): ...


class TimerRegistry(Registry):
    """Registry for tracking methods decorated with @timer.

    Maps method names to their timer configuration details.
    """
    def __init__(self):
        self._registry: Dict[str, TimerDetail] = dict()

    def register(self, timer_detail: TimerDetail, method_name: str):
        self._registry[method_name] = timer_detail

    def items(self):
        return self._registry.items()

    def copy(self):
        instance = type(self)()
        instance._registry = {k: dataclasses.replace(v) for k, v in self._registry.items()}
        return instance


class CommandSignalRegistry(Registry):
    """Registry for command signal handlers (not yet implemented)."""

    def register(self, *args, **kwargs): ...

    def items(self): ...

    def copy(self): ...


class EventRegistry(Registry):
    """Registry for tracking methods that handle specific event types.

    Maps Event classes to lists of method names that should be called
    when events of that type are published.
    """

    def __init__(self):
        self._registry: Dict[Type[Event], List[str]] = defaultdict(list)

    def register(self, event_type: Type[Event], method_name: str):
        assert issubclass(event_type, Event)
        self._registry[event_type].append(method_name)

    def get_subscriptions(self):
        return list(self._registry.keys())

    def copy(self):
        instance = type(self)()
        instance._registry = defaultdict(list, {key: copy(value) for key, value in self._registry.items()})
        return instance

    def items(self):
        return self._registry.items()


class Meta(ABCMeta):
    """Metaclass that automatically discovers and registers decorated methods.

    This metaclass inspects class methods at definition time to find methods
    decorated with @timer, @task, or @on_event, and registers them in the
    appropriate registries for automatic execution.
    """
    def __new__(mcs, name, bases, kwargs):
        if not (event_registry := mcs.get_registry_from_base(bases, '__event_registry__')):
            event_registry = EventRegistry()
        if not (timer_registry := mcs.get_registry_from_base(bases, '__timer_registry__')):
            timer_registry = TimerRegistry()
        if not (run_forever_registry := mcs.get_registry_from_base(bases, '__run_forever_registry__')):
            run_forever_registry = []

        for method_name, method in kwargs.items():
            if event_type := getattr(method, '__related_event__', None):
                event_registry.register(event_type, method_name)
            elif method_name.startswith('on_'):
                params = inspect.signature(method).parameters
                if len(params) == 2:
                    args = list(params.values())[1]
                    annotation = args.annotation
                    if annotation != inspect.Parameter.empty and typing.get_origin(annotation) is list:
                        args0_type = typing.get_args(annotation)[0]
                        if issubclass(args0_type, Event):
                            event_registry.register(args0_type, method_name)
            if timer_detail := getattr(method, '__timer__', None):
                timer_registry.register(timer_detail, method_name)
            if getattr(method, '__background_task__', None):
                run_forever_registry.append(method_name)

        kwargs['__event_registry__'] = event_registry
        kwargs['__timer_registry__'] = timer_registry
        kwargs['__run_forever_registry__'] = run_forever_registry
        return super().__new__(mcs, name, bases, kwargs)

    @classmethod
    def get_registry_from_base(mcs, bases, registry_name):
        for base in bases:
            if getattr(base, registry_name):
                registry = getattr(base, registry_name)
                return registry.copy()
            return None
        return None


class ThreadWebApplication:
    """Helper class to run an aiohttp web application in a separate thread.

    Useful for running a web server alongside other application logic
    without blocking the main event loop.

    Attributes:
        app: The aiohttp Application instance
        host: Hostname to bind to
        port: Port number to listen on
    """
    def __init__(self, app: web.Application, host: str, port: int):
        self.host = host
        self.port = port
        self.app = app

    def _run(self):
        runner = web.AppRunner(self.app)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(runner.setup())
        site = web.TCPSite(runner, self.host, self.port)
        loop.run_until_complete(site.start())
        loop.run_forever()

    def run_in_thread(self):
        t = threading.Thread(target=self._run)
        t.start()


class Application(metaclass=Meta):
    """Base class for creating event-driven applications.

    Subclass this to create your application, using decorators like @timer,
    @task, and @on_event to define behavior. The metaclass automatically
    discovers and registers decorated methods.

    Attributes:
        engine: The AppEngine managing this application
        __event_registry__: Registry of event handlers (managed by metaclass)
        __timer_registry__: Registry of timer tasks (managed by metaclass)
        __run_forever_registry__: Registry of background tasks (managed by metaclass)

    Example:
        class MyApp(Application):
            @timer(interval=5.0)
            async def periodic_task(self):
                print("Running every 5 seconds")

            @on_event(MyEvent)
            async def handle_event(self, events: List[MyEvent]):
                for event in events:
                    print(f"Got event: {event.data}")
    """
    __event_registry__: Optional[EventRegistry] = None
    __timer_registry__: Optional[TimerRegistry] = None
    __run_forever_registry__: Optional[List] = None

    def __init__(self):
        self.engine: Optional[AppEngine] = None
        self._app_runner: _AppRunner = _AppRunner(self)

    async def before_start(self):
        """Hook called before the application starts.

        Override this method to perform initialization tasks.
        """
        ...

    async def exit(self):
        """Hook called when the application is exiting.

        Override this method to perform cleanup tasks.
        """
        ...

    async def start(self):
        """Start the application and run all registered tasks."""
        await self._app_runner.start()

    def set_engine(self, engine: "AppEngine"):
        self.engine = engine

    def register_handler(self):
        self._app_runner.register_handler()

    @classmethod
    def get_event_registry(cls) -> Optional[EventRegistry]:
        return cls.__event_registry__

    @classmethod
    def get_run_forever_registry(cls) -> Optional[List]:
        return cls.__run_forever_registry__

    @classmethod
    def get_timer_registry(cls) -> Optional[TimerRegistry]:
        return cls.__timer_registry__

    @classmethod
    def get_app_name(cls):
        return cls.__name__


class _AppRunner:
    """Internal helper class that manages the lifecycle of an Application.

    Responsible for building and executing timer tasks, background tasks,
    and registering event handlers. Not intended for direct use.

    Attributes:
        _app: The Application instance being managed
        _tasks: Set of running asyncio tasks
    """

    def __init__(self, app: Application):
        super().__init__()
        self._app: Application = app
        self._tasks: Set = set()

    @classmethod
    async def build_timer(cls, name: str, timer_detail: TimerDetail, callback: Callable):

        async def call():
            if inspect.iscoroutinefunction(callback):
                await callback()
            else:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, callback)

        try:
            if timer_detail.run_at_once:
                await call()
            while True:
                await asyncio.sleep(timer_detail.interval)
                await call()
        except asyncio.CancelledError:
            logger.warning(f"msg=timer task `{name}` was canceled.")
        except Exception as e:
            logger.exception(e)

    def build_schedule_tasks(self):
        tasks = []
        if timer_registry := self._app.get_timer_registry():
            for method_name, timer_detail in timer_registry.items():
                method = getattr(self._app, method_name)
                task_name = f'{self._app.get_app_name()}.{method_name}.timer({timer_detail.interval})'
                task = self.build_timer(name=task_name, timer_detail=timer_detail, callback=method)
                tasks.append(task)
        return tasks

    def build_background_tasks(self):
        tasks = []
        if run_forever_registry := self._app.get_run_forever_registry():
            for method_name in run_forever_registry:
                method = getattr(self._app, method_name)
                if inspect.iscoroutinefunction(method):
                    tasks.append(method())
                else:
                    tasks.append(asyncio.to_thread(method))
        return tasks

    def register_handler(self):
        for event_type, method_names in self._app.get_event_registry().items():
            self._app.engine.register_handler(event_type, *[getattr(self._app, each) for each in method_names])

    def build_hook_tasks(self, hook: str):
        tasks = []
        before_start = getattr(self._app, hook)
        if inspect.iscoroutinefunction(before_start):
            tasks.append(before_start())
        else:
            tasks.append(asyncio.to_thread(before_start))
        return tasks

    def build_before_start_tasks(self):
        return self.build_hook_tasks('before_start')

    def get_all_tasks(self):
        return self.build_schedule_tasks() + self.build_background_tasks()

    async def start(self):
        try:
            await asyncio.gather(*self.build_before_start_tasks())
            await asyncio.gather(*self.get_all_tasks())
        except Exception as e:
            logger.exception(e)
        finally:
            await self._app.exit()


class AppEngine:
    """Main orchestrator for running multiple Applications together.

    The AppEngine manages the event system and coordinates multiple Application
    instances, allowing them to communicate via events.

    Attributes:
        _apps: List of registered Application instances
        _event_engine: Internal event processing engine
        before_start_callbacks: Functions to run before starting
        exit_callbacks: Functions to run on exit

    Example:
        app1 = MyApp()
        app2 = AnotherApp()
        engine = AppEngine([app1, app2])
        engine.start()  # Runs all apps concurrently
    """
    def __init__(self, apps: Optional[Application] = None):
        self._apps: List[Application] = apps or []
        self._event_engine: _EventEngine = _EventEngine()
        self.set_app_engine()
        self.before_start_callbacks = []
        self.exit_callbacks = []

    async def pub_event(self, event: Event):
        """Publish an event to be handled by all registered handlers.

        Args:
            event: The Event instance to publish
        """
        await self._event_engine.pub_event(event)

    def set_app_engine(self):
        """Associate this engine with all registered applications."""
        for app in self._apps:
            app.set_engine(self)

    def add_app(self, *app: Application):
        """Add one or more applications to this engine.

        Args:
            *app: Application instances to add
        """
        for each in app:
            each.set_engine(self)
            each.register_handler()
            self._apps.append(each)

    def register_handler(self, event_type: Type[Event], *handler: Callable):
        """Register handler functions for a specific event type.

        Args:
            event_type: The Event class to handle
            *handler: Handler functions to register
        """
        self._event_engine.register_handler(event_type, *handler)

    def build_tasks(self) -> List:
        tasks = [self._event_engine.start()]
        tasks.extend([app.start() for app in self._apps])
        return tasks

    def before_start(self, func):
        """Register a callback to run before the engine starts.

        Args:
            func: Callback function (sync or async)
        """
        self.before_start_callbacks.append(ensure_async(func))

    def exit(self, func):
        """Register a callback to run when the engine exits.

        Args:
            func: Callback function to run on exit
        """
        self.exit_callbacks.append(func)

    async def run(self):
        """Run the engine and all registered applications asynchronously.

        This method starts all applications and the event engine, running them
        concurrently until completion or exception.
        """
        before_start_tasks = [each() for each in self.before_start_callbacks]
        tasks = self.build_tasks()
        try:
            await asyncio.gather(*before_start_tasks)
            await asyncio.gather(*tasks)
        except Exception as e:
            exit_tasks = [each() for each in self.exit_callbacks]
            await asyncio.gather(*exit_tasks)
            logger.exception(e)

    def start(self):
        """Start the engine synchronously.

        This is a convenience method that wraps the async run() method,
        making it easy to start the engine from synchronous code.
        """
        asyncio.run(self.run())
