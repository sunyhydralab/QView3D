import HashTable


class PriorityTable:
    def __init__(self):
        self.__table = HashTable()
        self.__sorted_keys = []

    def add_job_queue(self, item):
        # Add key to sorted keys list
        self.__add_key(item.get_priority())
        # Get current tuple of queue list and next turn
        tuple = self.__table.get(item.get_priority())
        # If no queue has this priority yet, initialize the queue list and set next turn
        if tuple == None:
            queue_list = []
            next_turn = 0
        else:
            queue_list, next_turn = tuple
        queue_list.append(item)
        # Have to check if this will update the list or if I have to manually re set the tuple

    def __add_key(self, new_key):
        # Add key to sorted_keys list, could use binary search in the future
        for index in range(self.__sorted_keys):
            key = self.__sorted_keys[index]
            if new_key == key:
                return
            if new_key > key:
                self.__sorted_keys.insert(index, new_key)
                return
        self.__sorted_keys.append(new_key)
