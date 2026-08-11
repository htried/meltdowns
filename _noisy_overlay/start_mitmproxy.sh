#!/bin/bash
# Start mitmproxy in regular mode - applications will use it via HTTP_PROXY/HTTPS_PROXY env vars
# This is more reliable than transparent mode in Docker containers

# Only run mitmproxy when network injection is enabled.
if [ "${INJECT_NETWORK_ENABLED:-0}" != "1" ]; then
    echo "mitmproxy disabled (INJECT_NETWORK_ENABLED=${INJECT_NETWORK_ENABLED:-0})"
    export MITMPROXY_ENABLED=0
    exit 0
fi

# Create mitmproxy config directory
mkdir -p /tmp/mitmproxy

# Start mitmproxy without LD_PRELOAD to avoid interference
# Use env -u to unset LD_PRELOAD for mitmproxy
env -u LD_PRELOAD mitmdump \
    --listen-host 0.0.0.0 \
    --listen-port 8080 \
    --set confdir=/tmp/mitmproxy \
    --scripts /utils/mitmproxy_addon.py \
    --set ssl_insecure=true \
    > /tmp/mitmproxy.log 2>&1 &

MITMPROXY_PID=$!
echo $MITMPROXY_PID > /tmp/mitmproxy.pid
export MITMPROXY_ENABLED=1

sleep 4

# Check if mitmproxy is running
if kill -0 $MITMPROXY_PID 2>/dev/null; then
    echo "mitmproxy started (PID: $MITMPROXY_PID)"
    echo "Proxy listening on 0.0.0.0:8080"
    echo "Applications will automatically use proxy via HTTP_PROXY/HTTPS_PROXY environment variables"
    
    CA_CERT="/tmp/mitmproxy/mitmproxy-ca-cert.pem"
    if [ -f "$CA_CERT" ]; then
        if [ "$(id -u)" -eq 0 ]; then
            CERT_DIR="/usr/local/share/ca-certificates"
            mkdir -p "$CERT_DIR"
            cp "$CA_CERT" "$CERT_DIR/mitmproxy-ca.crt"
            update-ca-certificates 2>/dev/null || true
        fi

        PYTHON_CERTIFI=$(python3 -c "import certifi; print(certifi.where())" 2>/dev/null || echo "")
        if [ -n "$PYTHON_CERTIFI" ] && [ -f "$PYTHON_CERTIFI" ]; then
            cat "$CA_CERT" >> "$PYTHON_CERTIFI" 2>/dev/null || true
            echo "mitmproxy CA certificate added to Python certifi bundle"
        fi
        
        echo "mitmproxy CA certificate installed"
    else
        echo "Warning: mitmproxy CA certificate not found at $CA_CERT"
        echo "HTTPS interception may not work properly"
    fi
else
    echo "ERROR: mitmproxy failed to start"
    cat /tmp/mitmproxy.log
    exit 1
fi

