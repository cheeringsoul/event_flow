"""
Basic Event Handling Example

This example demonstrates the three different ways to declare event handlers
in Event Flow:
1. Using @on_event decorator
2. Using naming convention (on_* methods with type hints)
3. Combining both for flexibility
"""

import asyncio
from event_flow.core.application import Application, AppEngine
from event_flow.core.event import Event
from event_flow.core.decorators import on_event


# Define custom events
class UserCreatedEvent(Event):
    """Event triggered when a new user is created"""
    pass


class UserLoginEvent(Event):
    """Event triggered when a user logs in"""
    pass


class OrderPlacedEvent(Event):
    """Event triggered when an order is placed"""
    pass


class MyApp(Application):
    """
    Example application showing different ways to handle events
    """

    # Method 1: Using @on_event decorator
    @on_event(UserCreatedEvent)
    async def handle_user_created(self, events: list[UserCreatedEvent]):
        """
        Handler using explicit decorator.
        Note: Events are passed as a list for batch processing.
        """
        print(f"\n[Decorator Handler] Processing {len(events)} UserCreatedEvent(s)")
        for event in events:
            user_data = event.data
            print(f"  - User created: {user_data}")

    # Method 2: Using naming convention with type hints
    # The framework automatically detects methods starting with "on_"
    # and registers them based on the type hint
    async def on_user_login(self, events: list[UserLoginEvent]):
        """
        Handler using naming convention (on_* + type hint).
        Automatically registered for UserLoginEvent.
        """
        print(f"\n[Convention Handler] Processing {len(events)} UserLoginEvent(s)")
        for event in events:
            login_data = event.data
            print(f"  - User logged in: {login_data}")

    # Method 3: Custom method name with decorator
    @on_event(OrderPlacedEvent)
    async def process_new_order(self, events: list[OrderPlacedEvent]):
        """
        Custom method name using decorator.
        Useful when you want descriptive method names.
        """
        print(f"\n[Custom Handler] Processing {len(events)} OrderPlacedEvent(s)")
        for event in events:
            order_data = event.data
            print(f"  - Order placed: {order_data}")


async def main():
    """
    Main function to demonstrate event handling
    """
    print("=" * 60)
    print("Basic Event Handling Example")
    print("=" * 60)

    # Create and configure the engine
    engine = AppEngine()
    app = MyApp()
    engine.add_app(app)

    # Publish some events
    print("\n--- Publishing Events ---")

    # Single user created event
    await engine.pub_event(UserCreatedEvent({
        "user_id": 123,
        "username": "alice",
        "email": "alice@example.com"
    }))

    # Multiple user login events (will be batched)
    await engine.pub_event(UserLoginEvent({
        "user_id": 123,
        "username": "alice",
        "timestamp": "2024-10-29T10:00:00"
    }))
    await engine.pub_event(UserLoginEvent({
        "user_id": 456,
        "username": "bob",
        "timestamp": "2024-10-29T10:05:00"
    }))

    # Order events
    await engine.pub_event(OrderPlacedEvent({
        "order_id": "ORD-001",
        "user_id": 123,
        "total": 99.99
    }))

    # Give time for events to be processed
    await asyncio.sleep(0.5)

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    # For demonstration purposes, we'll run the async main function
    # In production, you would typically call engine.start()
    asyncio.run(main())
