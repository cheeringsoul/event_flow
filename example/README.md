# Event Flow Examples

This directory contains comprehensive examples demonstrating the key features and capabilities of the Event Flow framework.

## Running the Examples

Each example is a standalone Python script that can be run directly:

```bash
# From the project root
python -m example.basic_event_handling
python -m example.timer_tasks
python -m example.background_tasks
python -m example.lifecycle_hooks
python -m example.multi_app
python -m example.batch_processing
```

Or run them directly:

```bash
cd example
python basic_event_handling.py
```

## Examples Overview

### 1. Basic Event Handling (`basic_event_handling.py`)

**Demonstrates:**
- Three different ways to declare event handlers
- Using `@on_event` decorator
- Using naming conventions (`on_*` methods)
- Custom handler method names

**Key Concepts:**
- Event creation and publishing
- Handler registration
- Event routing

**Run Time:** ~2 seconds

---

### 2. Timer-Based Tasks (`timer_tasks.py`)

**Demonstrates:**
- Creating periodic tasks with `@timer` decorator
- Configuring `run_at_once` behavior
- Mixing async and sync timer functions

**Key Concepts:**
- Scheduled task execution
- Timer intervals
- Automatic async/sync conversion

**Run Time:** ~15 seconds (watch timers execute)

---

### 3. Background Tasks (`background_tasks.py`)

**Demonstrates:**
- Long-running background tasks with `@task` decorator
- Queue processing patterns
- Async and sync background workers
- Multiple concurrent background tasks

**Key Concepts:**
- Continuous task execution
- Work queue management
- Thread pool for blocking operations

**Run Time:** ~12 seconds

---

### 4. Lifecycle Hooks (`lifecycle_hooks.py`)

**Demonstrates:**
- `before_start()` hook for initialization
- `exit()` hook for cleanup
- Resource management (database connections)
- Application and engine-level hooks

**Key Concepts:**
- Application lifecycle management
- Resource initialization and cleanup
- Graceful shutdown

**Run Time:** ~8 seconds

---

### 5. Multi-Application Architecture (`multi_app.py`)

**Demonstrates:**
- Multiple applications sharing a single event bus
- Inter-application communication
- Building microservices-style architecture
- Event-driven system design

**Applications in Example:**
- **APIApp**: Receives orders
- **OrderProcessorApp**: Processes orders
- **InventoryApp**: Manages inventory
- **NotificationApp**: Sends notifications
- **MonitorApp**: System health monitoring

**Key Concepts:**
- Shared event bus
- Decoupled application communication
- System composition

**Run Time:** ~20 seconds

---

### 6. Batch Processing (`batch_processing.py`)

**Demonstrates:**
- **WHY** handlers receive lists of events
- Performance comparison: one-by-one vs batch processing
- Bulk database operations
- Parallel processing

**Key Concepts:**
- Batch processing optimization
- Bulk operations
- Performance benefits
- Event grouping by type

**Run Time:** ~6 seconds

**Expected Output:** Shows significant speedup (typically 3-5x faster) when using batch operations vs processing events individually.

---

## Learning Path

If you're new to Event Flow, we recommend following this order:

1. **Start with `basic_event_handling.py`** - Learn the fundamentals
2. **Then `batch_processing.py`** - Understand why handlers use lists
3. **Move to `timer_tasks.py`** - Add periodic tasks
4. **Try `background_tasks.py`** - Continuous background work
5. **Explore `lifecycle_hooks.py`** - Resource management
6. **Finally `multi_app.py`** - Build complete systems

## Common Patterns

### Publishing Events

```python
await engine.pub_event(MyEvent(data))
```

### Event Handler Signatures

All handlers receive a list of events:

```python
async def handle_event(self, events: list[MyEvent]):
    for event in events:
        process(event.data)
```

### Accessing the Engine

Inside an application, access the engine via `self.engine`:

```python
class MyApp(Application):
    async def some_method(self):
        await self.engine.pub_event(MyEvent(data))
```

## Modifying Examples

Feel free to modify these examples to experiment:

- Change timer intervals
- Add more event types
- Create new handlers
- Combine patterns from multiple examples
- Adjust batch sizes to see performance impacts

## Tips

1. **Events are batched automatically** - When multiple events of the same type are in the queue, they're grouped together
2. **Handlers run concurrently** - Multiple handlers can process events in parallel
3. **Sync functions work too** - The framework automatically converts them to async
4. **Single events are still lists** - Even one event is passed as `[event]` for consistency

## Need Help?

- Check the main [README.md](../README.md) for full documentation
- Read the inline comments in each example
- Visit the Event Flow documentation (if available)
- Open an issue on GitHub

## Contributing Examples

Have a useful pattern or use case? Consider contributing an example:

1. Create a new file following the naming pattern
2. Include comprehensive comments
3. Add a section to this README
4. Submit a pull request
