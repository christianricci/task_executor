import ast
import datetime
import subprocess
import time
import threading
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, as_completed, wait
from pytest import fixture
from task_executor.model.orm import Status, Task
from task_executor.executor import Executor

def create_executor() -> Executor:
    executor: Executor = Executor(db_file_full_path="./unittest.sqlite")
    executor.create_db()
    return executor

def integration_test_fixture():
    tag = 'integtest'
    commands = [
            { "command": [ "echo", "0" ] },
            { "command": [ "echo", "1" ] },
            { "command": [ "cmd-not-exist", "2" ] },
            { "command": [ "echo", "3" ] },
            { "command": [ "echo", "4" ] }
    ]
    return tag, commands

def main():
    def run_task(task) -> Task:
        print(f"{datetime.datetime.now()} -> TaskId: {task.id}, ThreadName: {threading.current_thread().name}, ThreadId: {threading.current_thread().ident} started")
        created_at = datetime.datetime.now()

        try:
            process = subprocess.run(task.content["command"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            return_code = process.returncode
            message = { "output": process.stdout, "returnCode": process.returncode }

            if process.returncode == 0:
                status = Status.COMPLETED_OK
            else:
                status = Status.COMPLETED_ERROR

            # Update the status of the task depending on the standard error
            executor.update_task(task, status=status)
            task = executor.get_task_by_id(id=task.id)
            executor.add_task_log(task=task, message=message, status=status, created_at=created_at, updated_at=datetime.datetime.now())
        except Exception as e:
            return_code = 1
            message = { "output": e.__str__(), "returnCode": return_code }
            status = Status.COMPLETED_ERROR
            executor.update_task(task, status=status)
            task = executor.get_task_by_id(id=task.id)
            executor.add_task_log(task=task, message=message, status=status, created_at=created_at, updated_at=datetime.datetime.now())

        print(f"{datetime.datetime.now()} -> TaskId: {task.id}, ThreadName: {threading.current_thread().name}, ThreadId: {threading.current_thread().ident} finished")

    tag, commands = integration_test_fixture()
    executor: Executor = create_executor()
    output = []
    batch_size = 2
    max_workers = 2

    # Add task command into the TaskExecutor Database with Status NEW
    for cmd in commands:
        executor.add_task(tag=tag, content=cmd)

    # Execute the task in Get the first batch woth 2 tasks (batch_size) in status NEW
    tasks = executor.get_next_batch(tag, Status.NEW, batch_size=batch_size)

    # Run 2 x tasks in paralell (max_workers) until there are no more tasks with status NEW
    while len(tasks) != 0:
        with ThreadPoolExecutor(max_workers=max_workers) as thread_executor:
            thread_list = [ thread_executor.submit(run_task, task) for task in tasks ]
            wait(thread_list, return_when=ALL_COMPLETED)

        # Get the fisrt 2 tasks with status NEW     
        tasks = executor.get_next_batch(tag, Status.NEW, batch_size=batch_size)

    tasks = executor.get_task_by_tag(tag=tag)
    for task in tasks:
        output.append(ast.literal_eval(task.task_logs[0].message)["returnCode"])

    print(f"Execution returnCode: {output}")

if __name__ == "__main__":
    print(f"{datetime.datetime.now()} -> started")
    main()
    print(f"{datetime.datetime.now()} -> finished")