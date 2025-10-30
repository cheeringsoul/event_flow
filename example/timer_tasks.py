"""
Timer-Based Tasks Example

This example demonstrates how to use the @timer decorator to create
periodic tasks that run at specified intervals.
"""

import asyncio
from datetime import datetime
from event_flow.core.application import Application, AppEngine
from event_flow.core.decorators import timer


class ScheduledApp(Application):
    """
    Application with various timer-based scheduled tasks
    """

    def __init__(self):
        super().__init__()
        self.sync_count = 0
        self.cache_cleanups = 0
        self.health_checks = 0

    @timer(interval=2, run_at_once=True)
    async def sync_data(self):
        """
        Runs every 2 seconds and executes immediately on startup.

        Use run_at_once=True when you want the task to execute immediately
        when the application starts, then continue at the specified interval.
        """
        self.sync_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Syncing data... (run #{self.sync_count})")

    @timer(interval=5, run_at_once=False)
    async def cleanup_cache(self):
        """
        Runs every 5 seconds, waits for the first interval before executing.

        Use run_at_once=False when you want to wait for the first interval
        before the task runs for the first time.
        """
        self.cache_cleanups += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Cleaning up cache... (cleanup #{self.cache_cleanups})")

    @timer(interval=3, run_at_once=True)
    def blocking_health_check(self):
        """
        Synchronous timer function that runs every 3 seconds.

        The framework automatically converts sync functions to async
        by running them in a thread pool, so blocking operations
        won't block the event loop.
        """
        self.health_checks += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Health check (sync function)... (check #{self.health_checks})")
        # Simulate a blocking operation
        import time
        time.sleep(0.1)

    async def before_start(self):
        """Hook that runs before the application starts"""
        print("=" * 60)
        print("Timer-Based Tasks Example")
        print("=" * 60)
        print("\nStarting scheduled tasks...")
        print("- sync_data: runs every 2 seconds (immediate)")
        print("- cleanup_cache: runs every 5 seconds (after delay)")
        print("- blocking_health_check: runs every 3 seconds (immediate, sync)")
        print("\nWatching tasks for 15 seconds...\n")


async def main():
    """
    Main function to demonstrate timer-based tasks
    """
    # Create and configure the engine
    engine = AppEngine()
    app = ScheduledApp()
    engine.add_app(app)

    # Create a task to run the engine
    engine_task = asyncio.create_task(app.start())

    # Let it run for 15 seconds to see the timers in action
    await asyncio.sleep(15)

    # Cancel the engine task
    engine_task.cancel()

    try:
        await engine_task
    except asyncio.CancelledError:
        pass

    print("\n" + "=" * 60)
    print("Timer Tasks Summary:")
    print(f"  - Data syncs: {app.sync_count}")
    print(f"  - Cache cleanups: {app.cache_cleanups}")
    print(f"  - Health checks: {app.health_checks}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
