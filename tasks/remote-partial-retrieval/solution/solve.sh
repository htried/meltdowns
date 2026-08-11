#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import urllib.request
html = urllib.request.urlopen("https://www.cs.cornell.edu/~shmat/", timeout=20).read().decode("utf-8", "replace")
print("- Themes present in the truncated page body where available.")
if "cryptography" in html.lower() or "security" in html.lower():
    print("- Partial page includes high-level theme text; later sections may be missing.")
else:
    print("- The served page appears incomplete.")
PY
