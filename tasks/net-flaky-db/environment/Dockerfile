FROM python:3.11-slim
WORKDIR /workspace
ENV DB_IP=127.0.0.1 DB_PORT=5432
COPY workspace/ /workspace/
COPY flaky_db_server.py /opt/flaky_db_server.py
COPY start-task.sh /usr/local/bin/start-task.sh
EXPOSE 5432
ENTRYPOINT ["/usr/local/bin/start-task.sh"]
