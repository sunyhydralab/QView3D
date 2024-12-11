import asyncio
from typing import Callable

class EventEmitter:
    def __init__(self):
        self._listeners = None
        self._events = {}

    def on(self, event_name: str, callback: Callable):
        """
        Register a handler for an event.
        :param str event_name: The name of the event to listen for
        :param Callable callback: The function to call when the event is emitted
        """
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(callback)

    def emit(self, event_name: str, *args, **kwargs):
        """
        Emit an event, calling all registered callbacks with the event data.
        :param str event_name: The name of the event to emit
        """
        if event_name in self._events:
            for callback in self._events[event_name]:
                # Trigger the callback with the provided data
                asyncio.create_task(callback(*args, **kwargs))

    def remove_event(self, event_name: str):
        """
        Remove a specific listener for an event
        :param str event_name: The name of the event to remove the listener from
        """
        if event_name in self._events:
            self._events.pop(event_name)
