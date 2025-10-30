"""
Multi-Application Architecture Example

This example demonstrates how to build a system with multiple applications
that communicate through a shared event bus managed by a single AppEngine.
"""

import asyncio
from datetime import datetime
from event_flow.core.application import Application, AppEngine
from event_flow.core.event import Event
from event_flow.core.decorators import on_event, timer, task


# Define events for inter-app communication
class OrderPlacedEvent(Event):
    """Event emitted when an order is placed"""
    pass


class OrderProcessedEvent(Event):
    """Event emitted when an order is processed"""
    pass


class InventoryUpdatedEvent(Event):
    """Event emitted when inventory is updated"""
    pass


class NotificationEvent(Event):
    """Event for sending notifications"""
    pass


class APIApp(Application):
    """
    Simulates an API application that receives orders
    """

    def __init__(self):
        super().__init__()
        self.orders_received = 0

    async def before_start(self):
        print("[APIApp] Starting API service...")

    @timer(interval=3, run_at_once=True)
    async def simulate_incoming_orders(self):
        """Simulate receiving orders from external API"""
        self.orders_received += 1
        order_data = {
            "order_id": f"ORD-{self.orders_received:03d}",
            "product": f"Product-{self.orders_received % 3 + 1}",
            "quantity": self.orders_received % 5 + 1,
            "customer": f"customer-{self.orders_received % 10 + 1}"
        }

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [APIApp] Received order: {order_data['order_id']}")

        # Publish event to the shared event bus
        await self.engine.pub_event(OrderPlacedEvent(order_data))


class OrderProcessorApp(Application):
    """
    Processes orders and updates inventory
    """

    def __init__(self):
        super().__init__()
        self.orders_processed = 0

    async def before_start(self):
        print("[OrderProcessorApp] Starting order processor...")

    @on_event(OrderPlacedEvent)
    async def process_orders(self, events: list[OrderPlacedEvent]):
        """Process incoming orders"""
        for event in events:
            order = event.data
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [OrderProcessorApp] Processing order: {order['order_id']}")

            # Simulate processing time
            await asyncio.sleep(0.5)

            self.orders_processed += 1

            # Emit events for other apps
            await self.engine.pub_event(OrderProcessedEvent(order))
            await self.engine.pub_event(InventoryUpdatedEvent({
                "product": order["product"],
                "quantity_change": -order["quantity"]
            }))


class InventoryApp(Application):
    """
    Manages inventory levels
    """

    def __init__(self):
        super().__init__()
        self.inventory = {
            "Product-1": 100,
            "Product-2": 100,
            "Product-3": 100
        }

    async def before_start(self):
        print("[InventoryApp] Starting inventory management...")
        print(f"[InventoryApp] Initial inventory: {self.inventory}")

    @on_event(InventoryUpdatedEvent)
    async def update_inventory(self, events: list[InventoryUpdatedEvent]):
        """Update inventory based on events"""
        for event in events:
            update = event.data
            product = update["product"]
            change = update["quantity_change"]

            if product in self.inventory:
                self.inventory[product] += change

                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] [InventoryApp] Updated {product}: "
                      f"{self.inventory[product]} units remaining")

                # Check for low inventory
                if self.inventory[product] < 20:
                    await self.engine.pub_event(NotificationEvent({
                        "type": "low_inventory",
                        "product": product,
                        "level": self.inventory[product]
                    }))

    @timer(interval=10, run_at_once=False)
    async def inventory_report(self):
        """Periodic inventory status report"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] [InventoryApp] === Inventory Report ===")
        for product, quantity in self.inventory.items():
            print(f"[{timestamp}] [InventoryApp]   {product}: {quantity} units")
        print()


class NotificationApp(Application):
    """
    Handles all notifications (emails, SMS, etc.)
    """

    def __init__(self):
        super().__init__()
        self.notifications_sent = 0

    async def before_start(self):
        print("[NotificationApp] Starting notification service...")

    @on_event(OrderProcessedEvent)
    async def notify_order_processed(self, events: list[OrderProcessedEvent]):
        """Send notification when orders are processed"""
        for event in events:
            order = event.data
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [NotificationApp] Sending order confirmation email "
                  f"for {order['order_id']} to {order['customer']}")
            self.notifications_sent += 1

    @on_event(NotificationEvent)
    async def handle_notifications(self, events: list[NotificationEvent]):
        """Handle various notification types"""
        for event in events:
            notification = event.data
            timestamp = datetime.now().strftime("%H:%M:%S")

            if notification["type"] == "low_inventory":
                print(f"[{timestamp}] [NotificationApp] ALERT: Low inventory for "
                      f"{notification['product']} ({notification['level']} units)")
                self.notifications_sent += 1


class MonitorApp(Application):
    """
    Monitors system health and performance
    """

    def __init__(self):
        super().__init__()
        self.health_checks = 0

    async def before_start(self):
        print("[MonitorApp] Starting monitoring service...")

    @timer(interval=8, run_at_once=False)
    async def health_check(self):
        """Periodic health check"""
        self.health_checks += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] [MonitorApp] System health check #{self.health_checks}")
        print(f"[{timestamp}] [MonitorApp] All applications running normally")
        print()


async def main():
    """
    Main function demonstrating multi-application architecture
    """
    print("=" * 60)
    print("Multi-Application Architecture Example")
    print("=" * 60)
    print("\nThis example demonstrates multiple apps communicating")
    print("through a shared event bus:\n")
    print("  • APIApp: Receives orders from external sources")
    print("  • OrderProcessorApp: Processes orders")
    print("  • InventoryApp: Manages inventory levels")
    print("  • NotificationApp: Sends notifications")
    print("  • MonitorApp: Monitors system health")
    print("\n" + "=" * 60 + "\n")

    # Create multiple applications
    api_app = APIApp()
    order_processor = OrderProcessorApp()
    inventory_app = InventoryApp()
    notification_app = NotificationApp()
    monitor_app = MonitorApp()

    # Create a single engine and add all apps
    engine = AppEngine()
    engine.add_app(api_app, order_processor, inventory_app, notification_app, monitor_app)

    # All apps now share the same event bus and can communicate with each other

    # Create a task to run the engine
    engine_task = asyncio.create_task(engine.start())

    # Let the system run for 20 seconds
    await asyncio.sleep(20)

    # Shutdown
    engine_task.cancel()

    try:
        await engine_task
    except asyncio.CancelledError:
        pass

    # Print summary
    print("\n" + "=" * 60)
    print("Multi-App System Summary:")
    print(f"  • Orders received: {api_app.orders_received}")
    print(f"  • Orders processed: {order_processor.orders_processed}")
    print(f"  • Notifications sent: {notification_app.notifications_sent}")
    print(f"  • Health checks performed: {monitor_app.health_checks}")
    print(f"  • Final inventory: {inventory_app.inventory}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
