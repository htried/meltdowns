#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import urllib.error, urllib.request
url = "https://rishijha.com/data.txt"
try:
    urllib.request.urlopen(url, timeout=20).read()
    print("The data file was accessible.")
except urllib.error.HTTPError as exc:
    print(f"The requested data file is unavailable: HTTP {exc.code}.")
except Exception as exc:
    print(f"The requested data file is unavailable: {exc}.")
PY
