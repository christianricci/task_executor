"""
How to Use this class:
$ cd task_executor/..
$ python
from task_executor.model.setup import Engine
engine = Engine(db_file_full_path='./task_executor.sqlite')

engine.create_db()

engine.drop_task()
engine.create_task()
engine.drop_task_log()
engine.create_task_log()

from task_executor.model.orm import Task, TaskLog, Status
task_id = engine.add_task(tag='test',content="{'k1': 'value1'}")
task = engine.session.query(Task).filter(Task.id==1).first()
engine.add_task_log(message='dummy message', status=Status.IN_PROGRESS.name, task_id=task_id)
"""

from __future__ import annotations
import ast
import datetime
import json
import logging
import traceback
from typing import List, overload
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from ..exceptions import TaskError, TaskLogError
from .orm import Status, Task, TaskLog


class ExecutorActionDB:
    def __init__(self, db_file_full_path: str, echo=True):
        self.db_file_full_path = db_file_full_path
        self.engine = create_engine(f'sqlite:///{self.db_file_full_path}', echo=echo, pool_size=0, max_overflow=-1)
        self.session = sessionmaker(bind=self.engine)
        self.logger = logging.getLogger(__class__.__name__)

    def create_task(self):
        Task.__table__.create(self.engine)

    def drop_task(self):
        try:
            Task.__table__.drop(self.engine)
        except Exception as e:
            self.logger.debug(e.args)

    def create_task_log(self):
        TaskLog.__table__.create(self.engine)

    def drop_task_log(self):
        try:
            TaskLog.__table__.drop(self.engine)
        except Exception as e:
            self.logger.debug(e.args)

    def create_db(self):
        self.drop_task()
        self.create_task()
        self.drop_task_log()
        self.create_task_log()

    def add_task(self, tag, content):
        try:
            session = self.session()            
            task = Task(
                tag=tag,
                content=json.loads(json.dumps(ast.literal_eval(str(content)))),
                status=Status.NEW.name,
                created_at=str(datetime.datetime.now()),
                updated_at=str(datetime.datetime.now()))
            session.add(task)
            # session.flush()
            session.commit()
            session.close()
        except Exception as e:
            self.logger.error(e)
            raise TaskError(e)

    def add_multi_task(self, tag, content_list: List[str]):
        try:
            session = self.session()

            for content in content_list:
                task = Task(
                    tag=tag,
                    content=json.loads(json.dumps(ast.literal_eval(content))),
                    status=Status.NEW.name,
                    created_at=str(datetime.datetime.now()),
                    updated_at=str(datetime.datetime.now()))
                session.add(task)

            # session.flush()
            session.commit()
            session.close()
        except Exception as e:
            self.logger.error(e)
            raise TaskError(e)

    def update_task(self, task: Task, **kwargs) -> None:
        try:
            session = self.session()            
            task_session = session.query(Task).filter(Task.id==task.id)
            task_row = task_session.first()
            task_update = Task(
                tag=kwargs.get("tag") or task_row.tag,
                content=kwargs.get("content") or task_row.content,
                status=kwargs.get("status") or task_row.status,
                updated_at=str(datetime.datetime.now()))
            task_session.update({
                Task.tag: task_update.tag,
                Task.content: task_update.content,
                Task.status: task_update.status,
                Task.updated_at: task_update.updated_at
            }, synchronize_session = False)
            # session.flush()
            session.commit()
            session.close()
        except Exception as e:
            self.logger.error(e)
            raise TaskError(e)

    def remove_task(self, task: Task) -> None:
        try:
            session = self.session()            
            session.query(Task).filter(Task.id == Task.id).delete(synchronize_session=False)
            # session.flush()
            session.commit()
            session.close()
        except Exception as e:
            self.logger.error(e)
            raise TaskError(e)

    def add_task_log(self, task, status, message, created_at, updated_at):
        try:
            task: Task = task
            status: str = status

            task_log = TaskLog(
                message=str(message),
                status=status,
                created_at=created_at or str(datetime.datetime.now()),
                updated_at=updated_at or str(datetime.datetime.now()),
                task_id=task.id
            )
            session = self.session()            
            session.add(task_log)
            # session.flush()
            session.commit()
            session.close()

            return task_log
        except Exception as e:
            self.logger.error(e)
            raise TaskLogError(e)

    @overload
    def get_task(self, **kwargs) -> Task:
        ...

    @overload
    def get_task(self, **kwargs) -> List[Task]:
        ...

    def get_task(self, **kwargs) -> Task | List[Task]:
        try:
            session = self.session()            
            if kwargs.get("id"):
                result = session.query(Task).filter(Task.id==kwargs.get("id")).first()
            elif kwargs.get("tag") and kwargs.get("status"):
                result = session.query(Task).filter(Task.tag==kwargs.get("tag"), Task.status==kwargs.get("status")).all()
            elif kwargs.get("tag"):
                result = session.query(Task).filter(Task.tag==kwargs.get("tag")).all()
            else:
                raise ValueError("provide either id or tag")
            return result
        except Exception as e:
            self.logger.error(e)
            raise TaskError(e)
