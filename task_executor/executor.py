import logging
import traceback
from typing import List
from .model.orm import Status, Task
from .model.executor_action_db import ExecutorActionDB


class Executor:
    def __init__(self, db_file_full_path='./task_executor.sqlite', verbose=False):
        self.db_file_full_path = db_file_full_path
        self.engine = self.init_db_engine(verbose=verbose)
        self.logger = logging.getLogger(__class__.__name__)

    def add_task(self, tag, content) -> None:
        self.engine.add_task(tag=tag, content=content)
        self.logger.debug(f"New Task added for tag: {tag}")

    def add_multi_task(self, tag, content_list: List[str]) -> None:
        self.engine.add_multi_task(tag=tag, content_list=content_list)
        self.logger.debug(f"New Task content_list added for tag: {tag}")

    def update_task(self, task: Task, **kwargs) -> None:
        self.engine.update_task(task=task, **kwargs)
    
    def remove_task(self, task: Task) -> None:
        self.engine.remove_task(task=task)

    def add_task_log(self, task: Task, message: str, status: Status, created_at, updated_at) -> None:
        self.engine.add_task_log(task=task, message=message, status=status, created_at=created_at, updated_at=updated_at)

    def get_task_by_tag(self, tag: str) -> List[Task]:
        task_list = self.engine.get_task(tag=tag)
        return task_list

    def get_task_by_tag_and_status(self, tag: str, status: Status) -> List[Task]:
        task_list = self.engine.get_task(tag=tag, status=status)
        return task_list

    def get_task_by_id(self, id: int) -> Task:
        task = self.engine.get_task(id=id)
        return task

    def create_db(self):
        self.engine.create_db()

    def init_db_engine(self, verbose=False):
        try:
            return ExecutorActionDB(self.db_file_full_path, echo=verbose)
        except Exception as e:
            self.logger.error(e)
            raise e

    def get_next_batch(self, tag, status, batch_size: int = 1) -> List[Task]:
        tasks: List[Task] = self.get_task_by_tag_and_status(tag, status)
        count = len(tasks) if len(tasks) < batch_size else batch_size
        task_list : List[Task] = list()
        for id in range(count):
            self.update_task(tasks[id], status=Status.IN_PROGRESS)
            tasks[id].status = Status.IN_PROGRESS
            task_list.append(tasks[id])
        return task_list
