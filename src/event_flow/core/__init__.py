"""Core components of the event flow framework.

This package contains the fundamental building blocks for creating event-driven
applications:

- Application: Base class for creating applications
- AppEngine: Orchestrator for running multiple applications
- Event: Base event classes for the event system
- Decorators: @timer, @task, @on_event for marking special methods
- Exception classes: Custom exceptions for the framework
- Utility functions: Helper functions for async/sync compatibility

Example:
    from event_flow.core.application import Application, AppEngine
    from event_flow.core.decorators import timer, on_event
    from event_flow.core.event import Event

    class MyEvent(Event):
        pass

    class MyApp(Application):
        @timer(interval=5.0)
        async def periodic_task(self):
            await self.engine.pub_event(MyEvent("Hello"))

        @on_event(MyEvent)
        async def handle_event(self, events):
            print(f"Got {len(events)} events")

    engine = AppEngine([MyApp()])
    engine.start()
"""
