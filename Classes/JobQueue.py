import Queue
import Job


class JobQueue:
    def __init__(self, id, priority=0):
        self.__queue = Queue()
        self.__id = id
        self.__priority = priority

    def add(self, item):
        self.__queue.add(item)

    def remove(self):
        return self.__queue.remove()

    def isEmpty(self):
        return self.__queue.isEmpty()

    def peek(self):
        return self.__queue.peek()

    def setPriority(self, priority):
        self.__priority = priority

    def getPriority(self):
        return self.__priority

    def getId(self):
        return self.__id
