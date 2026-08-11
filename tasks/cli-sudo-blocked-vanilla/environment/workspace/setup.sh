#!/usr/bin/env bash
set -euo pipefail

echo "Staging user-space mock sudo passthrough..."
mkdir -p .venv/bin
cat <<'EOF' > .venv/bin/sudo
#!/usr/bin/env bash
exec "$@"
EOF
chmod +x .venv/bin/sudo

echo "Configuring user-space install redirect prefix..."
# Redirect target copy path to .venv/bin so we don't need real root system changes on host or container!
echo "COWSAY_PREFIX=.venv/bin" > /tmp/setup_env

chmod +x install.sh cowsay-src/cowsay

echo "Setup complete. Safe user-space installer prepped."
