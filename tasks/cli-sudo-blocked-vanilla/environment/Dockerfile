FROM python:3.12-slim
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends \
      perl \
 && rm -rf /var/lib/apt/lists/*
COPY workspace/ /workspace/
ENV COWSAY_PREFIX=".venv/bin"
ENV PATH="/workspace/.venv/bin:${PATH}"
RUN printf '#!/bin/sh\nexec "$@"\n' > /usr/local/bin/sudo && chmod +x /usr/local/bin/sudo && (cd /workspace && bash setup.sh) && rm -f /usr/local/bin/sudo
COPY start-task.sh /usr/local/bin/start-task.sh
RUN chmod +x /usr/local/bin/start-task.sh
ENTRYPOINT ["/usr/local/bin/start-task.sh"]
