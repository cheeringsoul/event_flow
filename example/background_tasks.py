"""
Background Tasks Example

This example demonstrates how to use the @task decorator to create
long-running background tasks that run continuously alongside your application.
"""

import asyncio
import random
from datetime import datetime
from collections import deque
from event_flow.core.application import Application, AppEngine
from event_flow.core.decorators import task


class WorkerApp(Application):
    """
    Application with background workers processing a simulated queue
    """

    def __init__(self):
        super().__init__()
        self.queue = deque()
        self.processed_items = 0
        self.monitoring_reports = 0

    async def before_start(self):
        """Initialize the queue with some items"""
        print("=" * 60)
        print("Background Tasks Example")
        print("=" * 60)
        print("\nInitializing work queue...")

        # Add some initial items to the queue
        for i in range(5):
            self.queue.append(f"task-{i}")

        print(f"Added {len(self.queue)} items to queue")
        print("\nStarting background workers...\n")

    @task
    async def process_queue(self):
        """
        Async background task that continuously processes items from a queue.

        This demonstrates an async background worker that runs indefinitely.
        The @task decorator ensures it starts when the application starts.
        """
        while True:
            if self.queue:
                item = self.queue.popleft()
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] [AsyncWorker] Processing: {item}")

                # Simulate some async work (e.g., API call, database query)
                await asyncio.sleep(random.uniform(0.5, 1.5))

                self.processed_items += 1
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] [AsyncWorker] Completed: {item}")
            else:
                # Wait a bit before checking the queue again
                await asyncio.sleep(0.1)

    @task
    async def queue_feeder(self):
        """
        Another async task that adds items to the queue periodically.

        This simulates new work arriving while the application is running.
        """
        task_counter = 5
        while True:
            await asyncio.sleep(2)

            # Add a new item to the queue
            new_item = f"task-{task_counter}"
            self.queue.append(new_item)
            task_counter += 1

            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] [Feeder] Added new task: {new_item} (queue size: {len(self.queue)})")

    @task
    def blocking_monitor(self):
        """
        Synchronous background task that monitors the system.

        This demonstrates that sync functions can also be background tasks.
        They will automatically run in a thread pool to avoid blocking
        the async event loop.
        """
        import time

        while True:
            # Simulate a blocking operation (e.g., reading from a file, system metrics)
            time.sleep(3)

            self.monitoring_reports += 1
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] [SyncMonitor] Status Report #{self.monitoring_reports}:")
            print(f"[{timestamp}] [SyncMonitor]   - Queue size: {len(self.queue)}")
            print(f"[{timestamp}] [SyncMonitor]   - Processed: {self.processed_items}")


def main():
    """
    Main function to demonstrate background tasks
    """
    # Create and configure the engine
    engine = AppEngine()
    app = WorkerApp()
    engine.add_app(app)
    engine.start()


if __name__ == "__main__":
    main()
