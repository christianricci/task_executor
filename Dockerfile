FROM python:3.12.0
LABEL maintainer ricci.christian@gmail.com
RUN set -eux; \
	apt-get update; \
	apt-get install -y --no-install-recommends \
		git \
	; \
	rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/christianricci/task_executor.git
WORKDIR task_executor
RUN python setup.py sdist
RUN pip install dist/task_executor-0.1.tar.gz
CMD echo "docker run -ti <container_name> python -m task_executor.shell_executor --help"
CMD tail -f /dev/null
