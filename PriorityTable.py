import HashTable


class PriorityTable:
    def __init__(self):
        self.__table = HashTable()
        self.__sorted_priority_list = []

    def add_job_queue(self, item):
        """
        Add a job queue to the table, based on it's priority
        """
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

    def remove_job_queue(self, item):
        """
        Removes the specified item from self.__table

        Returns True if the item is no longer in the table
        Returns False if item was not found in the table
        """
        tuple = self.__table.get(item.get_priority())
        # If item not in table, don't check further
        if tuple == None:
            return False
        queue_list, next_turn = tuple
        # Iterate through all queues, and find the one with a matching id to our item to remove
        for queue in queue_list:
            if queue.get_id() == item.get_id():
                # Remove the item from queue list
                queue_list.remove(queue)
                # Check if queue list for this priority is now empty, if so, remove priority from table
                if len(queue_list) == 0:
                    self.__table.remove(item.get_priority())
                    self.__sorted_priority_list.remove(item.get_priority())
                    return True
                # Fix the next_turn index
                next_turn %= len(queue_list)
                # Re set the table at the priority we just removed from
                self.__table.set(item.get_priority(), (queue_list, next_turn))
                return True
        return False

    def __add_key(self, new_priority):
        """
        Logic for adding new priority into __sorted_priority_list
        """
        # Add key to sorted_keys list, could use binary search in the future
        for index in range(self.__sorted_priority_list):
            key = self.__sorted_priority_list[index]
            if new_priority == key:
                return
            if new_priority > key:
                self.__sorted_priority_list.insert(index, new_priority)
                return
        self.__sorted_priority_list.append(new_priority)

    def get_sorted_priority_list(self):
        return self.__sorted_priority_list

    def get_item(self, key):
        return self.__table.get(key)

    def set_item(self, key, item):
        self.__table.set(key, item)
