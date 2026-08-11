FROM python:3.12-slim
WORKDIR /workspace
RUN useradd -m -u 1000 -s /bin/bash agent
COPY workspace/ /workspace/
RUN printf '#!/bin/sh\nexec "$@"\n' > /usr/local/bin/sudo && chmod +x /usr/local/bin/sudo && (cd /workspace && bash setup.sh) && rm -f /usr/local/bin/sudo
RUN chown -R agent:agent /workspace
COPY start-task.sh /usr/local/bin/start-task.sh
RUN chmod +x /usr/local/bin/start-task.sh
ENTRYPOINT ["/usr/local/bin/start-task.sh"]
