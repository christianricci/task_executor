import datetime
import logging
import os
import re
import subprocess
import threading
import traceback
import fire
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, as_completed, wait
from tqdm import tqdm
from .model.orm import Status, Task
from .executor import Executor

# Set logging
logfile = "shell-executor.debug.log"
logging.basicConfig(level=logging.DEBUG, 
                    format='%(name)s: %(asctime)s | %(levelname)s | %(filename)s:%(lineno)s | %(funcName)s - %(message)s',
                    handlers=[logging.FileHandler(logfile)])

class ShellExecutor(object):
    def __init__(self):
        self.executor: Executor = None
        self.db_name = f"{os.getcwd()}/shell-executor.sqlite"
        self.logger = logging.getLogger(__class__.__name__)

    def __log_start(self):
        print(f"Program started {datetime.datetime.now()} - debug file: {os.getcwd()}/{logfile}")

    def __log_end(self):
        print(f"Program finished {datetime.datetime.now()}")        

    def create_executor_db(self) -> None:
        """
        Create task executor database.
        """
        self.__log_start()
        
        self.executor: Executor = Executor(db_file_full_path=self.db_name)
        self.executor.create_db()
        self.logger.info(f"Database file {self.db_name}")
        
        self.__log_end()

    def __get_executor(self) -> None:
        self.executor: Executor = Executor(db_file_full_path=self.db_name)

    def add_command(self, tag, command) -> None:
        """
        Add command to the task executor database.

        example:
            python shell_executor.py add_command --tag=sandpit --command="{'command':['az','tag','list','--resource-id','/SUBSCRIPTIONS/...................']}"

        command = {'command':['az','tag','list','--resource-id','/SUBSCRIPTIONS/......']}
        tag = 'sandpit'           
        """
        self.__log_start()
        self.__get_executor()
        
        # Add task command into the TaskExecutor Database with Status NEW
        self.executor.add_task(tag=tag, content=command)
        
        self.__log_end()

    def add_multi_command(self, tag, command_file) -> None:
        """
        Add multiple command to the task executor database.

        example:
            python shell_executor.py add_command --tag=sandpit --command_file=commands.txt

        command = {'command':['az','tag','list','--resource-id','/SUBSCRIPTIONS/....']}
        tag = 'sandpit'           
        """
        self.__log_start()
        self.__get_executor()

        # Add task command into the TaskExecutor Database with Status NEW
        try:
            content_list = []
            with open(command_file, mode='r') as file:
                for line in file.readlines():
                    if re.match('^{.*}$', line) != None:
                        content_list.append(line.rstrip('\n'))
            self.executor.add_multi_task(tag=tag, content_list=content_list)
        except Exception as e:
            self.logger.error(e)
            print(e)

        self.__log_end()

    def run_command(self, tag, batch_size, max_workers):
        """
        Run commands. Example Argument:
            tag = 'sandpit'          
            batch_size = '2'
            max_workers = '2'
        """
        def run_task(task) -> Task:
            self.logger.info(f"TaskId: {task.id}, ThreadName: {threading.current_thread().name}, ThreadId: {threading.current_thread().ident} started")
            self.logger.info(f"Runing task with content: {task.content['command']}")
            created_at = datetime.datetime.now()

            try:
                process = subprocess.run(task.content["command"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                return_code = process.returncode
                message = { "stdout": process.stdout, "stderr": process.stderr, "returnCode": process.returncode }

                if process.returncode == 0:
                    status = Status.COMPLETED_OK
                else:
                    status = Status.COMPLETED_ERROR

                # Update the status of the task depending on the standard error
                self.executor.update_task(task, status=status)
                task = self.executor.get_task_by_id(id=task.id)
                self.executor.add_task_log(task=task, message=message, status=status, created_at=created_at, updated_at=datetime.datetime.now())
            except Exception as e:
                return_code = 1
                message = { "output": e.__str__(), "returnCode": return_code }
                status = Status.COMPLETED_ERROR
                self.executor.update_task(task, status=status)
                task = self.executor.get_task_by_id(id=task.id)
                self.executor.add_task_log(task=task, message=message, status=status, created_at=created_at, updated_at=datetime.datetime.now())
                self.logger.debug(f'command: {task.content["command"]}\nstatus: {status}\nmessage: {message}\nreturnCode: {return_code}\nUnexpected Error: {traceback.format_exc()}')

            self.logger.info(f"Status: {status}, TaskId: {task.id}, ThreadName: {threading.current_thread().name}, ThreadId: {threading.current_thread().ident} finished.")

        self.__log_start()
        self.__get_executor()

        # Show progress bar
        total_tasks = len(self.executor.get_task_by_tag_and_status(tag, Status.NEW))
        
        # Execute the task in Get the first batch woth 2 tasks (batch_size) in status NEW
        tasks = self.executor.get_next_batch(tag, Status.NEW, batch_size=batch_size)

        # Run 2 x tasks in paralell (max_workers) until there are no more tasks with status NEW

        for chunk in tqdm(range(0, total_tasks, batch_size), desc="Task Chunks"):
            if tasks == []:
                break
            self.logger.info(f"Processing chunk {chunk}")
            with ThreadPoolExecutor(max_workers=max_workers) as thread_executor:
                thread_list = [ thread_executor.submit(run_task, task) for task in tasks ]
                wait(thread_list, return_when=ALL_COMPLETED)

            # Get the fisrt 2 tasks with status NEW     
            tasks = self.executor.get_next_batch(tag, Status.NEW, batch_size=batch_size)

        self.__log_end()

if __name__ == "__main__":
    fire.Fire(ShellExecutor)
