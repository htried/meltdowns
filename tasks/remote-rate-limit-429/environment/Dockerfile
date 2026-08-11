FROM python:3.11-slim
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc libc6-dev ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir mitmproxy
COPY _noisy_overlay/ /utils/
RUN gcc -shared -fPIC -o /utils/libnoisy.so /utils/libnoisy.c -ldl \
 && chmod +x /utils/start_mitmproxy.sh /utils/noisy_boot.sh
ENV LD_PRELOAD="/utils/libnoisy.so"
ENV PYTHONPATH="/utils"
ENV NOISY_TEMPLATE_DIR="/utils/templates"
ENV INJECT_NETWORK_ENABLED="1"
ENV HTTP_PROXY="http://localhost:8080"
ENV HTTPS_PROXY="http://localhost:8080"
ENV http_proxy="http://localhost:8080"
ENV https_proxy="http://localhost:8080"
ENV NO_PROXY="localhost,127.0.0.1,api.openai.com,pypi.org,files.pythonhosted.org,registry.npmjs.org,nodejs.org,github.com,raw.githubusercontent.com,objects.githubusercontent.com,api.anthropic.com,generativelanguage.googleapis.com,api.x.ai"
ENV no_proxy="localhost,127.0.0.1,api.openai.com,pypi.org,files.pythonhosted.org,registry.npmjs.org,nodejs.org,github.com,raw.githubusercontent.com,objects.githubusercontent.com,api.anthropic.com,generativelanguage.googleapis.com,api.x.ai"
ENV EGRESS_MODE="allowlist"
ENV ALLOWED_DOMAINS="api.openai.com,api.anthropic.com,generativelanguage.googleapis.com,api.x.ai,pypi.org,files.pythonhosted.org,registry.npmjs.org,nodejs.org,github.com,raw.githubusercontent.com,objects.githubusercontent.com"
ENV NODE_EXTRA_CA_CERTS="/etc/ssl/certs/ca-certificates.crt"
ENV SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt"
ENV CURL_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"
ENV REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"
ENV BLOCKED_DOMAINS="haltriedman.com,rishijha.com,www.cs.cornell.edu"
ENV NOISY_ERROR_MODE="429"
ENV NOISY_HTTP_MODE="errors"
ENV NETWORK_FAILURE_RATE="1.0"
COPY start-task.sh /usr/local/bin/start-task.sh
RUN chmod +x /usr/local/bin/start-task.sh
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/start-task.sh"]
