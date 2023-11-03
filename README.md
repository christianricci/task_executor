# Task Executor
Task executor is a tools that help to automate task executions at big scale by adding shell commands in a database and executing them in parallel.
## Build and Install
```
python setup.py sdist
pip install dist/task_executor-0.1.tar.gz
```
### Create database
```
python -m task_executor.shell_executor create_executor_db
```
### Add tasks
Single task
```
python -m task_executor.shell_executor add_command my-tag '{"command": ["echo", "hello-world-!!!"]}'
```
Or and a dummy data for testing (tag is my-tag in this case)
```
for i in {1..20}; do 
echo "python -m task_executor.shell_executor add_command my-tag '{ \"command\": [ \"bash\", \"-c\",\"echo \\\"print number ${i}\\\";sleep 1;date\"]}'" | bash
done
```
Or from a query
```
cat <<EOF | sqlite3 <SAME_DB_FILE_NAME>.sqlite | bash
select distinct
'python -m task_executor.shell_executor ' ||
'add_command my-tag '||
'''{"command": ["az","tag","list","--resource-id","'||ResourceId ||'"]}'''
from billing
where SubscriptionName = 'sandpit';
EOF
```
### Add multi tasks
```
cat <<EOF | sqlite3 <SAME_DB_FILE_NAME>.sqlite > commands.txt
select distinct
'{"command": ["az","tag","list","--resource-id","'||ResourceId ||'"]}'
from billing
where SubscriptionName = 'sandpit';
EOF

python -m task_executor.shell_executor add_multi_command sandpit commands.txt
```
### Run tasks
```
python -m task_executor.shell_executor run_command my-tag 6 3
```
## Database Output
```
$ sqlite3 shell-executor.sqlite
sqlite> .mode table
sqlite> select * from tasks;
+----+-----------+-------------------------------------+-----------------+----------------------------+----------------------------+
| id |    tag    |               content               |     status      |         created_at         |         updated_at         |
+----+-----------+-------------------------------------+-----------------+----------------------------+----------------------------+
| 1  | integtest | {"command": ["echo", "0"]}          | COMPLETED_OK    | 2023-10-20 21:04:29.988344 | 2023-10-20 21:04:35.166864 |
| 2  | integtest | {"command": ["echo", "1"]}          | COMPLETED_OK    | 2023-10-20 21:04:30.006625 | 2023-10-20 21:04:35.184036 |
| 3  | integtest | {"command": ["cmd-not-exist", "2"]} | COMPLETED_ERROR | 2023-10-20 21:04:30.016242 | 2023-10-20 21:04:40.302282 |
| 4  | integtest | {"command": ["echo", "3"]}          | COMPLETED_OK    | 2023-10-20 21:04:30.024641 | 2023-10-20 21:04:40.321427 |
| 5  | integtest | {"command": ["echo", "4"]}          | COMPLETED_OK    | 2023-10-20 21:04:30.034222 | 2023-10-20 21:04:45.439917 |
+----+-----------+-------------------------------------+-----------------+----------------------------+----------------------------+
sqlite> select * from task_logs;
+----+-------------------------------------------------------------------------------------+-----------------+----------------------------+----------------------------+---------+
| id |                                       message                                       |     status      |         created_at         |         updated_at         | task_id |
+----+-------------------------------------------------------------------------------------+-----------------+----------------------------+----------------------------+---------+
| 1  | {'output': '0\n', 'returnCode': 0}                                                  | COMPLETED_OK    | 2023-10-20 21:04:30.119001 | 2023-10-20 21:04:35.179697 | 1       |
| 2  | {'output': '1\n', 'returnCode': 0}                                                  | COMPLETED_OK    | 2023-10-20 21:04:30.129155 | 2023-10-20 21:04:35.210941 | 2       |
| 3  | {'output': "[Errno 2] No such file or directory: 'cmd-not-exist'", 'returnCode': 1} | COMPLETED_ERROR | 2023-10-20 21:04:35.248953 | 2023-10-20 21:04:40.316146 | 3       |
| 4  | {'output': '3\n', 'returnCode': 0}                                                  | COMPLETED_OK    | 2023-10-20 21:04:35.249102 | 2023-10-20 21:04:40.361649 | 4       |
| 5  | {'output': '4\n', 'returnCode': 0}                                                  | COMPLETED_OK    | 2023-10-20 21:04:40.395919 | 2023-10-20 21:04:45.457182 | 5       |
+----+-------------------------------------------------------------------------------------+-----------------+----------------------------+----------------------------+---------+
```
## Sample python
```
$ PYTHONPATH=<PATH_TO_WORKSPACE>/task_executor/sample.py 
2023-10-20 21:04:29.886990 -> started
2023-10-20 21:04:30.085919 -> TaskId: 1, ThreadName: ThreadPoolExecutor-0_0, ThreadId: 140365577520704 started
2023-10-20 21:04:30.095446 -> TaskId: 2, ThreadName: ThreadPoolExecutor-0_1, ThreadId: 140365569066560 started
2023-10-20 21:04:35.194869 -> TaskId: 1, ThreadName: ThreadPoolExecutor-0_0, ThreadId: 140365577520704 finished
2023-10-20 21:04:35.221788 -> TaskId: 2, ThreadName: ThreadPoolExecutor-0_1, ThreadId: 140365569066560 finished
2023-10-20 21:04:35.248406 -> TaskId: 3, ThreadName: ThreadPoolExecutor-1_0, ThreadId: 140365569066560 started
2023-10-20 21:04:35.248864 -> TaskId: 4, ThreadName: ThreadPoolExecutor-1_1, ThreadId: 140365577520704 started
2023-10-20 21:04:40.335953 -> TaskId: 3, ThreadName: ThreadPoolExecutor-1_0, ThreadId: 140365569066560 finished
2023-10-20 21:04:40.379189 -> TaskId: 4, ThreadName: ThreadPoolExecutor-1_1, ThreadId: 140365577520704 finished
2023-10-20 21:04:40.395723 -> TaskId: 5, ThreadName: ThreadPoolExecutor-2_0, ThreadId: 140365577520704 started
2023-10-20 21:04:45.469917 -> TaskId: 5, ThreadName: ThreadPoolExecutor-2_0, ThreadId: 140365577520704 finished
Execution returnCode: [0, 0, 1, 0, 0]
2023-10-20 21:04:45.486748 -> finished
```
## Run from Docker
```
$ git clone https://github.com/christianricci/task_executor.git
$ cd task_executor
$ cat Dockerfile

$ docker build .
$ docker tag <image_id> task-executor:latest # Get the id from the previous cmd output
$ docker run -d -i --name task_executor task-executor:latest

$ docker exec -ti task_executor python -m task_executor.shell_executor
$ docker exec -ti task_executor python -m task_executor.shell_executor create_executor_db
$ docker exec -ti task_executor python -m task_executor.shell_executor add_command my-tag '{"command": ["echo","\"Hello World!!!\""]}'
$ docker exec -ti task_executor python -m task_executor.shell_executor run_command my-tag 1 1
$ docker exec -ti task_executor cat /task_executor/shell-executor.debug.log
```
