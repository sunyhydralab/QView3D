import asyncio

class EventEmitter:
    def __init__(self):
        self._events = {}

    def on(self, event_name, callback):
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(callback)

    def emit(self, event_name, *args, **kwargs):
        if event_name in self._events:
            for callback in self._events[event_name]:
                asyncio.create_task(callback(*args, **kwargs))

    def remove_event(self, event_name):
        if event_name in self._events:
            self._events.pop(event_name)
