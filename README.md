# Event Flow

A lightweight, high-performance event-driven framework built on asyncio for building scalable Python applications.

## Overview

Event Flow is a modern Python framework that embraces event-driven architecture principles. It provides a declarative, decorator-based API for building reactive applications with automatic event routing, batch processing, and lifecycle management.

## Key Features

- **Event-Driven Architecture**: Built on asyncio with efficient queue-based event processing
- **Declarative API**: Use decorators to define event handlers, schedule tasks, and background tasks
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

# Define your custom events
class OrderPlacedEvent(Event):
    pass

class TradeEvent(Event):
    pass

# Create applications with event handlers
class OrderProcessorApp(Application):

    # Using naming convention (method starts with 'on_')
    async def on_orders(self, events: list[OrderPlacedEvent]):
        """Process orders and publish trade events"""
        for event in events:
            print(f"Processing order: {event.data}")
            # Publish a new event from within the handler
            await self.engine.pub_event(TradeEvent({
                "symbol": event.data["symbol"],
                "price": event.data["price"]
            }))

class TradeProcessorApp(Application):

    async def on_trade(self, events: list[TradeEvent]):
        """Handle trade events"""
        for event in events:
            print(f"Processing trade: {event.data}")

# Initialize the engine and add applications
engine = AppEngine()
engine.add_app(OrderProcessorApp(), TradeProcessorApp())

# Use @engine.before_start to publish initial events
@engine.before_start
async def publish_events():
    await engine.pub_event(OrderPlacedEvent({
        "symbol": "BTCUSDT",
        "price": "120000"
    }))

# Start the engine
engine.start()
```

### Schedule Tasks

Execute tasks periodically with the `@timer` decorator:

```python
from event_flow.core.application import Application
from event_flow.core.decorators import schedule


class ScheduledApp(Application):

    @schedule(interval=60, run_at_once=True)
    async def sync_data(self):
        """Runs every 60 seconds, executes immediately on startup"""
        print("Syncing data...")

    @schedule(interval=300, run_at_once=False)
    async def cleanup_cache(self):
        """Runs every 5 minutes, waits for first interval before executing"""
        print("Cleaning up cache...")
```

### Background Tasks

Run long-running tasks in the background:

```python
import asyncio
from collections import deque
from event_flow.core.application import Application, AppEngine
from event_flow.core.decorators import task

class WorkerApp(Application):

    def __init__(self):
        super().__init__()
        self.queue = deque()

    @task
    async def process_queue(self):
        """Async background task that continuously processes items"""
        while True:
            if self.queue:
                item = self.queue.popleft()
                print(f"Processing: {item}")
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(0.1)

    @task
    def blocking_monitor(self):
        """Sync function automatically runs in thread pool"""
        import time
        while True:
            print(f"Queue size: {len(self.queue)}")
            time.sleep(3)

# Start the application
engine = AppEngine()
engine.add_app(WorkerApp())
engine.start()
```

### Lifecycle Hooks

Control application behavior during startup and shutdown:

```python
import asyncio
from event_flow.core.application import Application, AppEngine

class DatabaseApp(Application):

    async def before_start(self):
        """Called before the application starts"""
        print("Connecting to database...")
        self.db = await connect_to_database()

    async def exit(self):
        """Called when the application is shutting down"""
        print("Closing database connection...")
        await self.db.close()

# You can also add engine-level hooks
engine = AppEngine()
engine.add_app(DatabaseApp())

@engine.before_start
async def engine_setup():
    print("Engine starting...")

@engine.exit
async def engine_cleanup():
    print("Engine shutting down...")

engine.start()
```

### Multi-Application Architecture

Manage multiple applications with a single engine:

```python
from event_flow.core.application import Application, AppEngine
from event_flow.core.event import Event
from event_flow.core.decorators import on_event, schedule


class OrderPlacedEvent(Event):
    pass


class OrderProcessedEvent(Event):
    pass


# API application receives orders
class APIApp(Application):

    @schedule(interval=3, run_at_once=True)
    async def simulate_incoming_orders(self):
        """Simulate receiving orders from external API"""
        await self.engine.pub_event(OrderPlacedEvent({
            "order_id": "ORD-001",
            "product": "Product-1"
        }))


# Order processor handles the orders
class OrderProcessorApp(Application):

    @on_event(OrderPlacedEvent)
    async def process_orders(self, events: list[OrderPlacedEvent]):
        """Process orders and emit completion events"""
        for event in events:
            print(f"Processing: {event.data}")
            await self.engine.pub_event(OrderProcessedEvent(event.data))


# Notification app sends notifications
class NotificationApp(Application):

    @on_event(OrderProcessedEvent)
    async def notify(self, events: list[OrderProcessedEvent]):
        """Send notifications for processed orders"""
        for event in events:
            print(f"Sending notification for: {event.data}")


# Create engine and add all apps
engine = AppEngine()
engine.add_app(APIApp(), OrderProcessorApp(), NotificationApp())

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

Any Application or SubApplication instance has access to `self.engine`, allowing you to publish events from within event handlers, schedule tasks, or background tasks.

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

Event Flow provides a Django-style settings system for managing application configuration.

#### How It Works

The framework automatically loads settings from a Python module. You can specify which module to use via the `EF_SETTINGS_MODULE` environment variable, or it defaults to `settings.py` in your current application directory.

#### Setting Up Configuration

1. **Create a settings file** (e.g., `settings.py`) in your application directory:

```python
# settings.py
DATABASE_URL = "postgresql://localhost/mydb"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
API_KEY = "your-api-key"
DEBUG = True
MAX_WORKERS = 10
```

**Note**: All configuration variables must be in UPPERCASE.

2. **Use settings in your code**:

```python
from event_flow.settings import settings

class DatabaseApp(Application):
    async def before_start(self):
        # Access settings just like Django
        db_url = settings.DATABASE_URL
        debug_mode = settings.DEBUG

        self.db = await connect_to_database(db_url)
```

#### Custom Settings Module

To use a different settings module, set the `EF_SETTINGS_MODULE` environment variable:

```bash
# Use myapp.py as settings (note: do not include .py extension)
export EF_SETTINGS_MODULE=somemodule.myapp

# Run your application
python main.py
```

Or set it programmatically before importing settings:

```python
import os
os.environ['EF_SETTINGS_MODULE'] = 'somemodule.myapp'  # References somemodule/myapp.py

from event_flow.settings import settings
```

**Important Notes:**
- The settings file must be a Python file (`.py`)
- `EF_SETTINGS_MODULE` should **not** include the `.py` extension
- Use Python module path notation (e.g., `myapp.config` for `myapp/config.py`)

#### Default Behavior

If `EF_SETTINGS_MODULE` is not set, the framework looks for `settings.py` in your current working directory.

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
|  - Schedule Tasks                                   |
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

Check out the comprehensive examples in the `example/` directory:

### Running Examples

```bash
# Run examples directly
python example/basic_event_handling.py
python example/schedule_tasks.py
python example/background_tasks.py
python example/lifecycle_hooks.py
python example/multi_app.py
```

### Available Examples

**`basic_event_handling.py`** - Event handling fundamentals
- Different ways to declare event handlers (naming convention)
- Publishing events from within Application instances using `self.engine.pub_event()`
- Event chaining (OrderPlacedEvent → TradeEvent)
- Using `@engine.before_start` decorator

**`schedule_tasks.py`** - Periodic scheduled tasks
- Using `@schedule` decorator with different intervals
- `run_at_once` parameter for immediate execution
- Both async and sync schedule functions

**`background_tasks.py`** - Long-running background workers
- Using `@task` decorator for continuous tasks
- Queue processing patterns
- Async and sync background tasks
- Multiple concurrent workers

**`lifecycle_hooks.py`** - Resource management
- `before_start()` hook for initialization
- `exit()` hook for cleanup
- Both application-level and engine-level hooks
- Database connection management example

**`multi_app.py`** - Multi-application architecture
- Multiple apps sharing a single event bus
- Inter-application communication via events
- Complete microservices-style system with:
  - API app (receives orders)
  - Order processor (processes orders)
  - Inventory management (tracks stock)
  - Notification service (sends alerts)
  - Monitoring service (health checks)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

ymy (icheeringsoul@gmail.com, icheeringsoul@163.com)