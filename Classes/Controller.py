import PriorityTable

class Controller:
    def __init__(self, printers=[]):
        self.__queueTable = PriorityTable()
        self.__printers = printers

    def printNextJob(self):
        """
        Find the highest priority job and send to an available printer

        Return True if the job is dispatched
        Return False if there are no jobs to dispatch
        """

        sortedPriorityList = self.__queueTable.get_priority_list()
        for priority in sortedPriorityList:
            curQueueList, nextTurn = self.__queueTable.get(priority)
            # Iterate through all job queues starting with the next turn
            index = nextTurn
            for _ in range(len(curQueueList)):
                curJobQueue = curQueueList[index]
                # If a queue has no jobs, move to next in list
                if curJobQueue.isEmpty():
                    index = (index + 1) % len(curQueueList)
                    continue
                # If a job is found, see if there are any available pritners for it
                job = curJobQueue.remove()
                availablePrinter = self.__checkAvailablePrinters(job)
                # Send the print out if possible
                if availablePrinter != None:
                    # TODO: implement printer class
                    availablePrinter.print(job)
                # If printer is not available, request assistance from staff on hand
                else:
                    self.__requestAssistance()
                # Update table data
                self.__queueTable.setItem(
                    priority, (curQueueList, (index + 1) % len(curQueueList))
                )
                # Job dispatched
                return True
        # No job dispatched
        return False

    def __checkAvailablePrinters(self, job):
        """
        Search through all printers in __printers and see if any are compatable with the current job

        Return best printer if multiple are found
        Return None if no printers are available for this job
        """
        return None

    def __requestAssistance(self):
        """
        Will put out a call to frontend to notify staff of assistance required

        May add additional parameters to this function in the future
        """
        pass
