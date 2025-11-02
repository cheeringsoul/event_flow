"""
Basic Event Handling Example

This example demonstrates:
1. Different ways to declare event handlers
2. How to receive socket data in a background loop
3. How to publish events from within Application instances using self.engine.pub_event()
4. How events flow through the system
"""

import asyncio
from datetime import datetime
from typing import List

from event_flow.core.application import Application, AppEngine
from event_flow.core.event import Event


# Define custom events
class SocketDataEvent(Event):
    """Event emitted when data is received from a socket"""
    pass


class OrderPlacedEvent(Event):
    """Event emitted when an order is placed"""
    pass


class EventProcessorApp(Application):

    # Using naming convention (method starts with 'on_')
    async def on_socket_data(self, events: List[SocketDataEvent]):
        """
        Handle socket data events using explicit decorator.

        This demonstrates how events published from the socket listener
        are received and processed by other applications.
        """
        for event in events:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] [Processor] SocketDataEvent From: {event.data['address']}")
            print(f"[{timestamp}] [Processor] SocketDataEvent Message: {event.data['message']}")

    async def on_orders(self, events: List[OrderPlacedEvent]):  # noqa
        """Handle order events - demonstrates batch processing"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        for each in events:
            print(f"[{timestamp}] [Processor] Processed OrderPlacedEvent {each}")


def main():
    """
    Main function demonstrating the complete event flow
    """
    # Create the engine
    engine = AppEngine()

    # Add applications
    processor_app = EventProcessorApp()

    engine.add_app(processor_app)

    @engine.before_start
    async def simulate_external_events():
        """
        Simulate events being published from external sources.

        In a real application, these might come from:
        - HTTP API endpoints
        - Message queues (RabbitMQ, Kafka, etc.)
        - Webhooks
        - Database triggers
        - etc.
        """
        await asyncio.sleep(3)  # Wait for the app to start

        print("\n" + "=" * 60)
        print("Simulating external events...")
        print("=" * 60 + "\n")

        # User creation event
        await engine.pub_event(SocketDataEvent({
            "address": "192.168.1.31",
            "message": "hi Alice",
        }))

        await asyncio.sleep(0.5)

        # Multiple user login events (will be batched)
        await engine.pub_event(OrderPlacedEvent({
            "symbol": "BTCUSDT",
            "price": "120000",
        }))

    engine.start()


if __name__ == "__main__":
    main()
