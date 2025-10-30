"""
Batch Processing Example

This example demonstrates WHY event handlers receive a list of events
instead of a single event. It shows the performance benefits of batch
processing when multiple events accumulate in the queue.
"""

import asyncio
import time
from datetime import datetime
from event_flow.core.application import Application, AppEngine
from event_flow.core.event import Event
from event_flow.core.decorators import on_event


class UserRegistrationEvent(Event):
    """Event emitted when a user registers"""
    pass


class DatabaseService:
    """Simulated database service with bulk operations"""

    async def insert_single(self, data: dict):
        """Insert a single record (slower)"""
        await asyncio.sleep(0.1)  # Simulate network latency + processing
        return f"Inserted: {data['email']}"

    async def bulk_insert(self, data_list: list[dict]):
        """Insert multiple records in one operation (faster)"""
        # Bulk insert only pays the network latency once
        await asyncio.sleep(0.1 + 0.01 * len(data_list))  # Base latency + small per-item cost
        return f"Bulk inserted {len(data_list)} records"


class EmailService:
    """Simulated email service with bulk sending"""

    async def send_single(self, email: str):
        """Send a single email (slower)"""
        await asyncio.sleep(0.05)
        return f"Sent email to {email}"

    async def send_bulk(self, emails: list[str]):
        """Send emails in parallel (faster)"""
        # Can send multiple emails concurrently
        await asyncio.sleep(0.05)  # Same time regardless of count (parallel sending)
        return f"Sent {len(emails)} emails in parallel"


class InefficientApp(Application):
    """
    Inefficient approach: Processing events one at a time
    (This is what you'd have to do if handlers received single events)
    """

    def __init__(self):
        super().__init__()
        self.db = DatabaseService()
        self.email = EmailService()
        self.processing_times = []

    @on_event(UserRegistrationEvent)
    async def handle_registration_inefficient(self, events: list[UserRegistrationEvent]):
        """
        Even though we receive a list, process them one by one (inefficient)
        """
        start_time = time.time()

        for event in events:
            user_data = event.data

            # Insert one at a time
            await self.db.insert_single(user_data)

            # Send email one at a time
            await self.email.send_single(user_data['email'])

        elapsed = time.time() - start_time
        self.processing_times.append(elapsed)

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [Inefficient] Processed {len(events)} events in {elapsed:.3f}s")


class EfficientApp(Application):
    """
    Efficient approach: Taking advantage of batch processing
    """

    def __init__(self):
        super().__init__()
        self.db = DatabaseService()
        self.email = EmailService()
        self.processing_times = []

    @on_event(UserRegistrationEvent)
    async def handle_registration_efficient(self, events: list[UserRegistrationEvent]):
        """
        Process the batch of events efficiently using bulk operations
        """
        start_time = time.time()

        # Extract all user data
        users = [event.data for event in events]

        # Bulk database insert (single network round-trip)
        await self.db.bulk_insert(users)

        # Send all emails in parallel
        emails = [user['email'] for user in users]
        await self.email.send_bulk(emails)

        elapsed = time.time() - start_time
        self.processing_times.append(elapsed)

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [Efficient] Processed {len(events)} events in {elapsed:.3f}s")


async def demo_inefficient():
    """Demonstrate inefficient one-by-one processing"""
    print("\n" + "=" * 60)
    print("INEFFICIENT APPROACH: Processing events one-by-one")
    print("=" * 60 + "\n")

    engine = AppEngine()
    app = InefficientApp()
    engine.add_app(app)

    # Start the engine
    engine_task = asyncio.create_task(app.start())
    await asyncio.sleep(0.1)  # Let engine start

    # Publish multiple events quickly
    print("Publishing 10 registration events...")
    for i in range(10):
        await engine.pub_event(UserRegistrationEvent({
            "user_id": i,
            "email": f"user{i}@example.com",
            "name": f"User {i}"
        }))

    # Wait for processing
    await asyncio.sleep(3)

    engine_task.cancel()
    try:
        await engine_task
    except asyncio.CancelledError:
        pass

    total_time = sum(app.processing_times)
    print(f"\nTotal processing time: {total_time:.3f}s")

    return total_time


async def demo_efficient():
    """Demonstrate efficient batch processing"""
    print("\n" + "=" * 60)
    print("EFFICIENT APPROACH: Batch processing with bulk operations")
    print("=" * 60 + "\n")

    engine = AppEngine()
    app = EfficientApp()
    engine.add_app(app)

    # Start the engine
    engine_task = asyncio.create_task(app.start())
    await asyncio.sleep(0.1)  # Let engine start

    # Publish multiple events quickly
    print("Publishing 10 registration events...")
    for i in range(10):
        await engine.pub_event(UserRegistrationEvent({
            "user_id": i,
            "email": f"user{i}@example.com",
            "name": f"User {i}"
        }))

    # Wait for processing
    await asyncio.sleep(1)

    engine_task.cancel()
    try:
        await engine_task
    except asyncio.CancelledError:
        pass

    total_time = sum(app.processing_times)
    print(f"\nTotal processing time: {total_time:.3f}s")

    return total_time


async def main():
    """
    Compare inefficient vs efficient processing
    """
    print("\n" + "=" * 60)
    print("Batch Processing Performance Comparison")
    print("=" * 60)
    print("\nThis example demonstrates why event handlers receive")
    print("a LIST of events instead of single events.")
    print("\nWhen multiple events accumulate in the queue, the")
    print("framework groups them by type and passes them all")
    print("at once, enabling efficient batch operations.")

    # Run demos
    inefficient_time = await demo_inefficient()
    efficient_time = await demo_efficient()

    # Compare results
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    print(f"Inefficient (one-by-one): {inefficient_time:.3f}s")
    print(f"Efficient (batch):        {efficient_time:.3f}s")
    print(f"Speedup:                  {inefficient_time / efficient_time:.2f}x faster")
    print(f"Time saved:               {inefficient_time - efficient_time:.3f}s ({(1 - efficient_time/inefficient_time)*100:.1f}%)")
    print("=" * 60)

    print("\nKey benefits of batch processing:")
    print("  ✓ Reduced database round-trips (bulk inserts)")
    print("  ✓ Parallel operations (sending multiple emails at once)")
    print("  ✓ Lower network overhead")
    print("  ✓ Better resource utilization")
    print("  ✓ Higher throughput under load")

    print("\nEven when there's only ONE event, it's passed as a")
    print("single-item list for API consistency.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
