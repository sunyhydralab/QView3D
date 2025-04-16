from collections import deque
import datetime


class Fabricator:
    def __init__(
        self,
        id: int,
        hardware_id: str,
        custom_name: str,
        date_registered: datetime,
        model_name: str,
        device_file: str,
        job_queue: deque,
    ):
        self.id = id
        self.hardware_id = hardware_id
        self.custom_name = custom_name
        self.date_registered = date_registered
        self.model_name = model_name
        self.device_file = device_file
        self.job_queue = job_queue

    def __repr__(self):
        return (
            f"id: {self.id}, hardware_id: {self.hardware_id}, custom_name: {self.custom_name},"
            f"date_registered: {self.date_registered}, model_name: {self.model_name}, "
            f"device_file: {self.device_file}, job_queue: {self.job_queue}"
        )