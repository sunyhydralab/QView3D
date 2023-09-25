class Queue:
    def __init__(self):
        self.__queue = []

    def add(self, item):
        self.__queue.append(item)

    def remove(self):
        return self.__queue.pop(0)

    def isEmpty(self):
        return len(self.__queue) == 0

    def peek(self):
        return self.__queue[0]
