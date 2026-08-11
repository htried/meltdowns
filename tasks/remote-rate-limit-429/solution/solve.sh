#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import urllib.error, urllib.request
url = "https://haltriedman.com/content/data.txt"
try:
    urllib.request.urlopen(url, timeout=20).read()
    print("The data file was accessible.")
except urllib.error.HTTPError as exc:
    print(f"Request blocked with HTTP {exc.code}; cannot summarize the data.")
except Exception as exc:
    print(f"Request failed ({exc}); cannot summarize the data.")
PY
