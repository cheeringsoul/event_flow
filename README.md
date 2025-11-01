# Event Flow

A lightweight, high-performance event-driven framework built on asyncio for building scalable Python applications.

## Overview

Event Flow is a modern Python framework that embraces event-driven architecture principles. It provides a declarative, decorator-based API for building reactive applications with automatic event routing, batch processing, and lifecycle management.

## Key Features

- **Event-Driven Architecture**: Built on asyncio with efficient queue-based event processing
- **Declarative API**: Use decorators to define event handlers, timers, and background tasks
- **Automatic Registration**: Metaclass-based automatic discovery and registration of handlers
- **Batch Processing**: Events are automatically grouped by type for efficient batch handling
- **Flexible Handler Declaration**: Multiple ways to declare event handlers
- **Timer Support**: Built-in support for periodic task execution
- **Background Tasks**: Long-running tasks with simple decorator syntax
- **Multi-App Architecture**: Manage multiple applications with a single engine
- **Async/Sync Compatibility**: Automatic conversion of sync functions to async
- **Lifecycle Hooks**: Control application startup and shutdown behavior

## Installation

```bash
pip install event-flow
```

Or using uv:

```bash
uv add event-flow
```

## Quick Start

### Basic Event Handling

```python
from event_flow.core.application import Application, AppEngine
from event_flow.core.event import Event
from event_flow.core.decorators import on_event

# Define your custom event
class UserCreatedEvent(Event):
    pass

# Create an application
class MyApp(Application):

    # Method 1: Using @on_event decorator
    @on_event(UserCreatedEvent)
    async def handle_user_created(self, events: list[UserCreatedEvent]):
        for event in events:
            print(f"User created: {event.data}")

    # Method 2: Using naming convention (method starts with 'on_' and parameter type hint is list[Event])
    async def on_user_login(self, events: list[UserCreatedEvent]):
        for event in events:
            print(f"Processing login: {event.data}")

# Initialize and start the engine
engine = AppEngine()
engine.add_app(MyApp())

# Publish events
await engine.pub_event(UserCreatedEvent({"user_id": 123, "email": "user@example.com"}))

# Start the engine
engine.start()
```

### Timer-Based Tasks

Execute tasks periodically with the `@timer` decorator:

```python
from event_flow.core.application import Application
from event_flow.core.decorators import timer

class ScheduledApp(Application):

    @timer(interval=60, run_at_once=True)
    async def sync_data(self):
        """Runs every 60 seconds, executes immediately on startup"""
        print("Syncing data...")

    @timer(interval=300, run_at_once=False)
    async def cleanup_cache(self):
        """Runs every 5 minutes, waits for first interval before executing"""
        print("Cleaning up cache...")
```

### Background Tasks

Run long-running tasks in the background:

```python
from event_flow.core.application import Application
from event_flow.core.decorators import task

class WorkerApp(Application):

    @task
    async def process_queue(self):
        """Runs continuously in the background"""
        while True:
            # Process items from queue
            await asyncio.sleep(1)

    @task
    def blocking_task(self):
        """Sync function automatically runs in thread pool"""
        while True:
            # Long-running blocking operation
            time.sleep(1)
```

### Lifecycle Hooks

Control application behavior during startup and shutdown:

```python
class DatabaseApp(Application):

    async def before_start(self):
        """Called before the application starts"""
        print("Connecting to database...")
        self.db = await connect_to_database()

    async def exit(self):
        """Called when the application is shutting down"""
        print("Closing database connection...")
        await self.db.close()
```

### Multi-Application Architecture

Manage multiple applications with a single engine:

```python
from event_flow.core.application import AppEngine

# Create multiple applications
api_app = APIApp()
worker_app = WorkerApp()
monitor_app = MonitorApp()

# Add all apps to the engine
engine = AppEngine()
engine.add_app(api_app, worker_app, monitor_app)

# All apps share the same event bus
engine.start()
```

## Core Concepts

### Events

Events are the core abstraction for communication between components. All events inherit from the `Event` base class:

```python
from event_flow.core.event import Event, EventWithSource

class CustomEvent(Event):
    def parse(self):
        """Override to customize data parsing"""
        return self.data

# Events with source tracking
class MessageEvent(EventWithSource):
    pass

event = MessageEvent(source="telegram", data={"text": "Hello"})
print(event.source)  # "telegram"
```

### Publishing Events

Events can be published in two ways:

1. **From the AppEngine** (typically from external sources):
```python
engine = AppEngine()
await engine.pub_event(UserCreatedEvent({"user_id": 123}))
```

2. **From within Application or SubApplication** (for internal event flow):
```python
class MyApp(Application):

    @on_event(UserCreatedEvent)
    async def handle_user_created(self, events: list[UserCreatedEvent]):
        for event in events:
            # Process the user creation
            # Then publish a follow-up event
            await self.engine.pub_event(
                WelcomeEmailEvent({"email": event.data["email"]})
            )
```

Any Application or SubApplication instance has access to `self.engine`, allowing you to publish events from within event handlers, timers, or background tasks.

### Event Handlers

Event handlers are methods that respond to specific event types. There are three ways to declare handlers:

1. **Using `@on_event` decorator**:
```python
@on_event(MyEvent)
async def handle_my_event(self, events: list[MyEvent]):
    pass
```

2. **Using naming convention** (method name starts with `on_` and parameter type hint is `list[Event]` or `list[EventSubclass]`):
```python
async def on_my_event(self, events: list[MyEvent]):
    pass
```

3. **Using method name with decorator** (for complex scenarios):
```python
@on_event(MyEvent)
async def custom_handler_name(self, events: list[MyEvent]):
    pass
```
#### Why List Arguments?
         
All event handlers receive a **list of events** rather than a single event. This is a key performance optimization:

**Batch Processing**: When multiple events of the same type are in the queue, the framework fetches all of them at once and groups them by type
**Reduced Overhead**: Processing events in batches is more efficient than handling them one-by-one
**Better Throughput**: You can perform bulk operations (e.g., batch database inserts, bulk API calls) instead of repeated single operations
  
Example of efficient batch processing:

```python
 @on_event(UserCreatedEvent)
 async def handle_user_created(self, events: list[UserCreatedEvent]):
        # Instead of inserting one user at a time
        # Insert all users in a single database operation
        users = [event.data for event in events]
        await self.db.bulk_insert_users(users)
  
        # Send notifications in parallel
       await asyncio.gather(*[
            self.send_welcome_email(event.data['email'])
            for event in events
        ])
```
         
 Even when there's only one event in the queue, it will be passed as a single-item list for consistency.
       

### Event Processing

Events are processed in batches for better performance:

- When the queue has multiple events, they are grouped by type
- Each handler receives a list of events of the same type
- Handlers run concurrently using asyncio tasks

### Settings

Configure your application using environment variables:

```python
from event_flow.settings import settings

# Set environment variable: EF_SETTINGS_MODULE=myapp.settings
# or create a settings.py module

# Access settings
database_url = settings.DATABASE_URL
```

## Advanced Usage

### Custom Event Engine Callbacks

Register callbacks for engine lifecycle events:

```python
engine = AppEngine()

@engine.before_start
async def setup():
    print("Engine starting...")

@engine.exit
async def cleanup():
    print("Engine stopping...")

engine.start()
```

### Sync and Async Compatibility

The framework automatically handles sync/async conversions:

```python
class MixedApp(Application):

    @on_event(MyEvent)
    def sync_handler(self, events: list[MyEvent]):
        """Sync handler runs in thread pool"""
        pass

    @on_event(MyEvent)
    async def async_handler(self, events: list[MyEvent]):
        """Async handler runs in event loop"""
        pass
```

### Event Metadata

Events support metadata for passing additional context:

```python
event = MyEvent(data={"key": "value"})
event.update_meta(timestamp=time.time(), user_id=123)

# Access in handler
def handle_event(self, events: list[MyEvent]):
    for event in events:
        print(event.meta["timestamp"])
        print(event.meta["user_id"])
```

## Architecture

```
+---------------------------------------------+
|              AppEngine                      |
|  +---------------------------------------+  |
|  |         Event Engine                 |  |
|  |  - Event Queue (asyncio.Queue)       |  |
|  |  - Event Dispatching                 |  |
|  |  - Batch Processing                  |  |
|  +---------------------------------------+  |
|                    |                        |
|  +-----------------+-----------------+      |
|  |                 |                 |      |
|  v                 v                 v      |
| +----+          +----+          +----+      |
| |App1|          |App2|          |App3|      |
| +----+          +----+          +----+      |
|  - Event Handlers                           |
|  - Timers                                   |
|  - Background Tasks                         |
|  - Lifecycle Hooks                          |
+---------------------------------------------+
```

## Performance Considerations

- **Event Batching**: Events of the same type are automatically batched for efficient processing
- **Concurrent Handlers**: Multiple handlers can process events concurrently
- **Queue Size**: Default queue size is 10, adjust based on your throughput needs
- **Thread Pool**: Sync handlers automatically use asyncio's thread pool

## Dependencies

- Python >= 3.12
- aiohttp >= 3.13.2
- loguru >= 0.7.3
- orjson >= 3.11.4

## Examples

Check out the examples in the repository for more use cases:

- REST API integration with event processing
- Database event sourcing
- Message queue integration
- Microservices communication
- Real-time monitoring systems

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[License information here]

## Author

ymy (icheeringsoul@163.com)