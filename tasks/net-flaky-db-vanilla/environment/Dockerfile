FROM python:3.12-slim
WORKDIR /workspace
COPY workspace/ /workspace/
ENV DB_IP="127.0.0.1"
ENV DB_PORT="5432"
COPY start-task.sh /usr/local/bin/start-task.sh
RUN chmod +x /usr/local/bin/start-task.sh
ENTRYPOINT ["/usr/local/bin/start-task.sh"]
