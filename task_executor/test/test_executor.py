import ast
import datetime
import subprocess
import time
import pytest
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, as_completed, wait
from pytest import fixture
from task_executor.model.orm import Status, Task
from task_executor.exceptions import TaskError, TaskLogError
from task_executor.executor import Executor
from sqlalchemy.orm.session import sessionmaker

TAG = "task-runTest"
COMMAND = "{ 'command': 'some command'}"
COMMAND_FILE = 'unittest-commant.txt'

@fixture
def create_executor() -> Executor:
    executor: Executor = Executor(db_file_full_path="./unittest.sqlite", verbose=False)
    executor.create_db()
    return executor

@fixture
def get_executor() -> Executor:
    executor: Executor = Executor(db_file_full_path="./unittest.sqlite")
    executor.create_db()
    executor.add_task(tag = TAG, content = COMMAND)
    task = executor.get_task_by_id(id=1)
    executor.add_task_log(task=task, message='some message', status=Status.IN_PROGRESS, created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())    
    return executor

@fixture
def new_task():
    tag = TAG
    content = COMMAND
    return tag, content

@fixture
def integration_test_fixture():
    tag = 'integtest'
    commands = [
            "{ 'command': [ 'echo', '0' ] }",
            "{ 'command': [ 'echo', '1' ] }",
            "{ 'command': [ 'cmd-not-exist', '2' ] }",
            "{ 'command': [ 'echo', '3' ] }",
            "{ 'command': [ 'echo', '4' ] }"
    ]
    expect_cmd_output = [ 0, 0, 1, 0, 0 ]
    return tag, commands, expect_cmd_output

@fixture
def multi_command_fixture():
    with open(COMMAND_FILE, 'w') as f:
        f.write("{ \"command\": [ \"echo\", \"0\" ] }\n")
        f.write("{ \"command\": [ \"echo\", \"1\" ] }\n")
        f.write("{ \"command\": [ \"cmd-not-exist\", \"2\" ] }\n")
        f.write("{ \"command\": [ \"echo\", \"3\" ] }\n")
        f.write("{ \"command\": [ \"echo\", \"4\" ] }\n")
        f.write("{ \"command\": [ \"echo\", \"\\\"sometext\\\"\" ] }\n")

    return COMMAND_FILE

def test_init_database(create_executor):
    executor: Executor = create_executor
    assert isinstance(executor.engine.session, sessionmaker)

def test_add_task(create_executor, new_task):
    executor: Executor = create_executor
    executor.add_task(tag = new_task[0], content = new_task[1])
    task = executor.get_task_by_id(id=1)
    assert task.id == 1

def test_add_multi_task(create_executor, multi_command_fixture):
    file = multi_command_fixture
    executor: Executor = create_executor

    content_list = []
    with open(file, mode='r') as file:
        for line in file.readlines():
            content_list.append(line.rstrip('\n'))

    executor.add_multi_task(tag=TAG, content_list=content_list)

    task = executor.get_task_by_id(id=1)
    assert task.id == 1

def test_add_task_with_incorrect_value_throw_exception(create_executor):
    executor: Executor = create_executor
    with pytest.raises(TaskError, match=r".*IntegrityError.*"):
        executor.add_task(tag = None, content = None)

def test_add_task_log(create_executor, new_task):
    executor: Executor = create_executor
    executor.add_task(tag = new_task[0], content = new_task[1])
    task = executor.get_task_by_id(id=1)
    executor.add_task_log(task=task, message='some message', status=Status.IN_PROGRESS, created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())
    task = executor.get_task_by_id(id=1)
    assert task.task_logs[0].id == 1

def test_add_task_log_with_incorrect_value_throw_exception(create_executor):
    executor: Executor = create_executor
    with pytest.raises(TaskLogError, match=r".*NoneType.*"):
        executor.add_task_log(task=None, message=None, status=None, created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())

def test_get_task_by_id(get_executor):
    executor: Executor = get_executor
    id = 1
    task = executor.get_task_by_id(id = id)
    assert task.id == id

def test_get_task_by_id_when_not_exist(get_executor):
    executor: Executor = get_executor
    id = 100
    task = executor.get_task_by_id(id = id)
    assert task == None

def test_get_task_by_tag(get_executor):
    executor: Executor = get_executor
    tag = TAG
    task = executor.get_task_by_tag(tag = tag)
    assert task[0].tag == tag

def test_get_task_by_tag_when_not_exist(get_executor):
    executor: Executor = get_executor
    tag = "task-runTest-not-exit"
    task = executor.get_task_by_tag(tag = tag)
    assert task == []

def test_update_task(get_executor):
    executor: Executor = get_executor
    id = 1
    task = executor.get_task_by_id(id = id)
    task = executor.update_task(task, status = Status.COMPLETED_OK)
    task = executor.get_task_by_id(id = id)
    assert task.status == Status.COMPLETED_OK

def test_update_task_with_incorrect_value_throw_exception(get_executor):
    executor: Executor = get_executor
    id = 100
    task = executor.get_task_by_id(id = id)
    with pytest.raises(TaskError, match=r".*NoneType.*"):
        task = executor.update_task(task, status = Status.COMPLETED_OK)

def test_remove_task(get_executor):
    executor: Executor = get_executor
    id = 1
    task = executor.get_task_by_id(id = id)
    executor.remove_task(task)
    task = executor.get_task_by_id(id = id)
    assert task == None

def test_get_next_batch_with_staus_new(get_executor):
    executor: Executor = get_executor
    tasks = executor.get_next_batch(tag=TAG, status=Status.NEW, batch_size=100)
    assert len(tasks) == 1
    assert tasks[0].status == Status.IN_PROGRESS

def test_get_next_batch_with_status_re_process_not_found(get_executor):
    executor: Executor = get_executor
    tasks = executor.get_next_batch(tag=TAG, status=Status.RE_PROCESS, batch_size=100)
    assert tasks == []

def test_get_next_batch_with_status_re_process_found(get_executor):
    executor: Executor = get_executor
    tasks = executor.get_task_by_tag_and_status(tag=TAG, status=Status.NEW)
    for task in tasks:
        executor.update_task(task, tag=TAG, status=Status.RE_PROCESS)
    tasks = executor.get_next_batch(tag=TAG, status=Status.RE_PROCESS, batch_size=100)
    assert len(tasks) == 1
    assert tasks[0].status == Status.IN_PROGRESS

def test_integration_test(create_executor, integration_test_fixture):
    tag, commands, expect_cmd_output = integration_test_fixture
    executor: Executor = create_executor
    output = []
    batch_size = 2
    max_workers = 2

    def run_task(task: Task):
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
    assert expect_cmd_output == output