FROM python:3.12-slim
WORKDIR /workspace
COPY workspace/ /workspace/
ENV PATH="/workspace/.venv/bin:${PATH}"
RUN printf '#!/bin/sh\nexec "$@"\n' > /usr/local/bin/sudo && chmod +x /usr/local/bin/sudo && (cd /workspace && bash setup.sh) && rm -f /usr/local/bin/sudo
EXPOSE 8080
COPY start-task.sh /usr/local/bin/start-task.sh
RUN chmod +x /usr/local/bin/start-task.sh
ENTRYPOINT ["/usr/local/bin/start-task.sh"]
