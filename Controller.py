import PriorityTable


class Controller:
    def __init__(self, printers=[]):
        self.__queue_table = PriorityTable()
        self.__printers = printers

    def print_next_job(self):
        """
        Find the highest priority job and send to an available printer

        Return True if the job is dispatched
        Return False if there are no jobs to dispatch
        """

        sorted_priority_list = self.__queue_table.get_priority_list()
        for priority in sorted_priority_list:
            cur_queue_list, next_turn = self.__queue_table.get(priority)
            # Iterate through all job queues starting with the next turn
            index = next_turn
            for _ in range(len(cur_queue_list)):
                cur_job_queue = cur_queue_list[index]
                # If a queue has no jobs, move to next in list
                if cur_job_queue.isEmpty():
                    index = (index + 1) % len(cur_queue_list)
                    continue
                # If a job is found, see if there are any available pritners for it
                job = cur_job_queue.remove()
                available_printer = self.__check_available_printers(job)
                # Send the print out if possible
                if available_printer != None:
                    # TODO: implement printer class
                    available_printer.print(job)
                # If printer is not available, request assistance from staff on hand
                else:
                    self.__request_assistance()
                # Update table data
                self.__queue_table.set_item(
                    priority, (cur_queue_list, (index + 1) % len(cur_queue_list))
                )
                # Job dispatched
                return True
        # No job dispatched
        return False

    def __check_available_printers(self, job):
        """
        Search through all printers in __printers and see if any are compatable with the current job

        Return best printer if multiple are found
        Return None if no printers are available for this job
        """
        return None

    def __request_assistance(self):
        """
        Will put out a call to frontend to notify staff of assistance required

        May add additional parameters to this function in the future
        """
        pass
