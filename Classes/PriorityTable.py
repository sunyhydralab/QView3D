import HashTable


class PriorityTable:
    def __init__(self):
        self.__table = HashTable()
        self.__sortedPriorityList = []

    def addJobQueue(self, item):
        """
        Add a job queue to the table, based on it's priority
        """
        # Add key to sorted keys list
        self.__add_key(item.getPriority())
        # Get current tuple of queue list and next turn
        tuple = self.__table.get(item.getPriority())
        # If no queue has this priority yet, initialize the queue list and set next turn
        if tuple == None:
            queueList = []
            nextTurn = 0
        else:
            queueList, nextTurn = tuple
        queueList.append(item)
        # Have to check if this will update the list or if I have to manually re set the tuple

    def removeJobQueue(self, item):
        """
        Removes the specified item from self.__table

        Returns True if the item is no longer in the table
        Returns False if item was not found in the table
        """
        tuple = self.__table.get(item.getPriority())
        # If item not in table, don't check further
        if tuple == None:
            return False
        queueList, nextTurn = tuple
        # Iterate through all queues, and find the one with a matching id to our item to remove
        for queue in queueList:
            if queue.getId() == item.getId():
                # Remove the item from queue list
                queueList.remove(queue)
                # Check if queue list for this priority is now empty, if so, remove priority from table
                if len(queueList) == 0:
                    self.__table.remove(item.getPriority())
                    self.__sortedPriorityList.remove(item.getPriority())
                    return True
                # Fix the next_turn index
                nextTurn %= len(queueList)
                # Re set the table at the priority we just removed from
                self.__table.set(item.getPriority(), (queueList, nextTurn))
                return True
        return False

    def __add_key(self, newPriority):
        """
        Logic for adding new priority into __sortedPriorityList
        """
        # Add key to sorted_keys list, could use binary search in the future
        for index in range(self.__sortedPriorityList):
            key = self.__sortedPriorityList[index]
            if newPriority == key:
                return
            if newPriority > key:
                self.__sortedPriorityList.insert(index, newPriority)
                return
        self.__sortedPriorityList.append(newPriority)

    def getSortedPriorityList(self):
        return self.__sortedPriorityList

    def getItem(self, key):
        return self.__table.get(key)

    def setItem(self, key, item):
        self.__table.set(key, item)
