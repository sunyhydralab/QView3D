import asyncio

class EventEmitter:
    def __init__(self):
        self._events = {}

    def on(self, event_name, callback):
        """Register a handler for an event."""
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(callback)

    def emit(self, event_name, *args, **kwargs):
        """Emit an event, calling all registered callbacks with the event data."""
        if event_name in self._events:
            for callback in self._events[event_name]:
                # Trigger the callback with the provided data
                asyncio.create_task(callback(*args, **kwargs))
