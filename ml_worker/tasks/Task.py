import uuid
from abc import ABC, abstractmethod
from enum import Enum

from common_lib.models import House, User, PredictionStatus

class Task(ABC):
    def __init__(self, user: "User", house: "House"):
        self.task_id = uuid.uuid4()
        self.user = user
        self.house = house
        self._status = PredictionStatus.QUEUED

    @abstractmethod
    def execute(self) -> str:
        pass

    def set_status(self, status: PredictionStatus) -> None:
        if not isinstance(status, PredictionStatus):
            raise ValueError("Invalid status. Must be a TaskStatus enum value.")
        self._status = status

    def get_status(self) -> PredictionStatus:
        return self._status
