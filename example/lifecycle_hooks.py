"""
Lifecycle Hooks Example

This example demonstrates how to use lifecycle hooks (before_start and exit)
to manage resources and perform setup/cleanup operations.
"""

import asyncio
from datetime import datetime
from event_flow.core.application import Application, AppEngine
from event_flow.core.event import Event
from event_flow.core.decorators import on_event, timer


# Simulated database connection class
class DatabaseConnection:
    def __init__(self, url: str):
        self.url = url
        self.connected = False

    async def connect(self):
        """Simulate connecting to a database"""
        print(f"  Connecting to database: {self.url}")
        await asyncio.sleep(0.5)
        self.connected = True
        print("  Database connected!")

    async def close(self):
        """Simulate closing the database connection"""
        print("  Closing database connection...")
        await asyncio.sleep(0.2)
        self.connected = False
        print("  Database disconnected!")

    async def execute(self, query: str):
        """Simulate executing a query"""
        if not self.connected:
            raise RuntimeError("Database not connected")
        print(f"  Executing query: {query}")
        await asyncio.sleep(0.1)
        return "Query result"


# Custom event
class DataEvent(Event):
    """Event that requires database access"""
    pass


class DatabaseApp(Application):
    """
    Application that demonstrates lifecycle management with a database connection
    """

    def __init__(self):
        super().__init__()
        self.db = None
        self.events_processed = 0

    async def before_start(self):
        """
        Called before the application starts.

        Use this hook to:
        - Initialize connections (database, message queues, etc.)
        - Load configuration
        - Perform health checks
        - Set up resources needed by the application
        """
        print("\n" + "=" * 60)
        print("Lifecycle Hooks Example")
        print("=" * 60)
        print("\n[BEFORE_START] Initializing application...")

        # Initialize database connection
        self.db = DatabaseConnection("postgresql://localhost/mydb")
        await self.db.connect()

        # Perform any other setup
        print("  Loading configuration...")
        await asyncio.sleep(0.2)

        print("  Running health checks...")
        await asyncio.sleep(0.2)

        print("\n[BEFORE_START] Application initialization complete!\n")

    async def exit(self):
        """
        Called when the application is shutting down.

        Use this hook to:
        - Close database connections
        - Flush buffers
        - Save state
        - Clean up resources
        - Log shutdown information
        """
        print("\n[EXIT] Application shutting down...")

        # Show statistics
        print(f"  Events processed during runtime: {self.events_processed}")

        # Close database connection
        if self.db and self.db.connected:
            await self.db.close()

        # Perform other cleanup
        print("  Saving application state...")
        await asyncio.sleep(0.2)

        print("  Flushing logs...")
        await asyncio.sleep(0.1)

        print("[EXIT] Cleanup complete!")
        print("=" * 60)

    @on_event(DataEvent)
    async def handle_data_event(self, events: list[DataEvent]):
        """Process data events using the database connection"""
        for event in events:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Processing DataEvent: {event.data}")

            # Use the database connection that was initialized in before_start
            await self.db.execute(f"INSERT INTO events VALUES ('{event.data}')")

            self.events_processed += 1

    @timer(interval=2, run_at_once=True)
    async def periodic_task(self):
        """A timer task that also uses the database"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Running periodic database maintenance...")
        await self.db.execute("VACUUM ANALYZE")


def main():
    """
    Main function to demonstrate lifecycle hooks
    """
    # Create and configure the engine
    engine = AppEngine()
    app = DatabaseApp()
    engine.add_app(app)

    # You can also add engine-level hooks
    @engine.before_start
    async def engine_setup():
        print("[ENGINE] Engine-level setup running...")
        await asyncio.sleep(0.1)
        print("[ENGINE] Engine ready!")

    @engine.exit
    async def engine_cleanup():
        print("\n[ENGINE] Engine-level cleanup running...")
        await asyncio.sleep(0.1)
        print("[ENGINE] Engine shutdown complete!")

    engine.start()


if __name__ == "__main__":
    main()
