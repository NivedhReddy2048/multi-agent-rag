"""In-memory Event Bus providing Publisher-Subscriber decoupling."""

from typing import Dict, List, Callable, Any
from core.events.events import Event
from core.logger import get_logger

logger = get_logger("core.events.bus")

EventHandler = Callable[[Event], None]


class EventBus:
    """Publish-Subscribe Event Bus for decoupling system subsystems."""

    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler):
        """Subscribe a handler callback to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler '{handler.__name__}' to event '{event_type}'")

    def unsubscribe(self, event_type: str, handler: EventHandler):
        """Unsubscribe a handler from an event type."""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def publish(self, event: Event):
        """Publish an event to all subscribed handlers."""
        handlers = self._subscribers.get(event.event_type, [])
        logger.info(f"Publishing event '{event.event_type}' (ID: {event.event_id}) to {len(handlers)} handlers")
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error handling event '{event.event_type}' in '{handler.__name__}': {e}", exc_info=True)


# Global singleton instance
event_bus = EventBus()
