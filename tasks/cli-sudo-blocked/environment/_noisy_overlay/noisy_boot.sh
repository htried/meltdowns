#!/usr/bin/env bash
set -euo pipefail

if [ "${INJECT_NETWORK_ENABLED:-0}" != "1" ]; then
  echo "noisy_boot: INJECT_NETWORK_ENABLED=${INJECT_NETWORK_ENABLED:-0}; skipping mitm"
  exit 0
fi

if [ "${MELTDOWNS_ALLOW_THIRD_PARTY:-0}" = "1" ] || \
   [ "${MELTDOWNS_ALLOW_THIRD_PARTY:-}" = "true" ] || \
   [ "${MELTDOWNS_ALLOW_THIRD_PARTY:-}" = "yes" ]; then
  export EGRESS_MODE=open
fi
export EGRESS_MODE="${EGRESS_MODE:-allowlist}"
case "${EGRESS_MODE}" in
  open|full) export EGRESS_MODE=open ;;
  allowlist|allow) export EGRESS_MODE=allowlist ;;
  lockdown|locked|none) export EGRESS_MODE=lockdown ;;
  *)
    echo "noisy_boot: unknown EGRESS_MODE=${EGRESS_MODE}; using allowlist" >&2
    export EGRESS_MODE=allowlist
    ;;
esac

if [ ! -x /utils/start_mitmproxy.sh ]; then
  echo "noisy_boot: missing /utils/start_mitmproxy.sh" >&2
  exit 1
fi

/utils/start_mitmproxy.sh

MITM_CA="/tmp/mitmproxy/mitmproxy-ca-cert.pem"
SYSTEM_CA="/etc/ssl/certs/ca-certificates.crt"
MERGED_CA="/tmp/mitmproxy/ca-certificates-with-mitmproxy.pem"

if [ ! -f "$MITM_CA" ]; then
  echo "noisy_boot: mitm CA missing at $MITM_CA" >&2
  exit 1
fi

if [ -f "$SYSTEM_CA" ]; then
  cat "$SYSTEM_CA" "$MITM_CA" > "$MERGED_CA"
else
  cp "$MITM_CA" "$MERGED_CA"
fi

{
  echo "SSL_CERT_FILE=$SYSTEM_CA"
  echo "CURL_CA_BUNDLE=$SYSTEM_CA"
  echo "REQUESTS_CA_BUNDLE=$SYSTEM_CA"
  echo "NODE_EXTRA_CA_CERTS=$SYSTEM_CA"
  echo "HTTP_PROXY=${HTTP_PROXY:-http://localhost:8080}"
  echo "HTTPS_PROXY=${HTTPS_PROXY:-http://localhost:8080}"
  echo "http_proxy=${http_proxy:-http://localhost:8080}"
  echo "https_proxy=${https_proxy:-http://localhost:8080}"
  echo "NO_PROXY=${NO_PROXY:-}"
  echo "no_proxy=${no_proxy:-${NO_PROXY:-}}"
  echo "LD_PRELOAD=${LD_PRELOAD:-/utils/libnoisy.so}"
  echo "EGRESS_MODE=${EGRESS_MODE:-allowlist}"
  echo "ALLOWED_DOMAINS=${ALLOWED_DOMAINS:-}"
} >> /etc/environment

export SSL_CERT_FILE="$SYSTEM_CA"
export CURL_CA_BUNDLE="$SYSTEM_CA"
export REQUESTS_CA_BUNDLE="$SYSTEM_CA"
export NODE_EXTRA_CA_CERTS="$SYSTEM_CA"
echo "noisy_boot: mitmproxy ready; CA merged at $MERGED_CA (EGRESS_MODE=${EGRESS_MODE})"
