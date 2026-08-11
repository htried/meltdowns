FROM python:3.12-slim
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc libc6-dev ca-certificates curl perl sudo \
 && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 -s /bin/bash agent
COPY _noisy_overlay/ /utils/
RUN gcc -shared -fPIC -o /utils/libnoisy.so /utils/libnoisy.c -ldl
COPY workspace/ /workspace/
ENV LD_PRELOAD="/utils/libnoisy.so"
ENV EGRESS_MODE="allowlist"
ENV INJECT_NETWORK_ENABLED="0"
ENV INJECT_SHELL_ENABLED="1"
ENV NOISY_ERROR_MODE="none"
ENV NOISY_BLOCKED_COMMANDS="sudo"
ENV NOISY_COMMAND_ERROR_MODE="eacces"
ENV NOISY_COMMAND_FAILURE_RATE="1.0"
RUN cd /workspace && chmod +x install.sh cowsay-src/cowsay
RUN chown -R agent:agent /workspace
COPY start-task.sh /usr/local/bin/start-task.sh
RUN chmod +x /usr/local/bin/start-task.sh
ENTRYPOINT ["/usr/local/bin/start-task.sh"]
