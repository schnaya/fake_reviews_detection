from decimal import Decimal
from typing import List, Dict, Optional

from common_lib.models import User, House, PredictionStatus

from schedule import MonthlySchedule, HouseholdTask
from tasks import Task, MLModel
class PredictionTask(Task):
    def __init__(self, user: User, house: House, model: "MLModel"):
        super().__init__(user, house)
        self.model = model
        self.predicted_tasks: List["HouseholdTask"] = []
        self.monthly_schedule: Optional[MonthlySchedule] = None

    def execute(self):
        try:

            self.predicted_tasks = self.model.predict_tasks(self.house)
            self.monthly_schedule = MonthlySchedule(self.predicted_tasks)
            schedule_dict = self.monthly_schedule.get_schedule()
            self.set_status(PredictionStatus.COMPLETED)
            return schedule_dict

        except Exception as e:
            print(f"Error during prediction task {self.task_id} for user {self.user.id}: {e}")
            self.set_status(PredictionStatus.FAILED)
            return f"Критическая ошибка во время выполнения задачи: {e}"

    def get_schedule(self) -> Dict[str, List[str]]:
        if self.monthly_schedule:
            schedule_data = self.monthly_schedule.get_schedule()
            for date_str, tasks in schedule_data.items():
                schedule_data[date_str] = [
                    f"{task.name} - {task.room}" for task in self.predicted_tasks if task.name in tasks
                ]
            return schedule_data
        return {}

