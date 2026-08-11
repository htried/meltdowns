FROM python:3.12-slim
WORKDIR /workspace
COPY workspace/ /workspace/
EXPOSE 6379
COPY start-task.sh /usr/local/bin/start-task.sh
RUN chmod +x /usr/local/bin/start-task.sh
ENTRYPOINT ["/usr/local/bin/start-task.sh"]
