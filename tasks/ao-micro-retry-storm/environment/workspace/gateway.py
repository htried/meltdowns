#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.error

url = "http://127.0.0.1:8081/api/data"

def main():
    print(f"Gateway querying downstream service at: {url}")
    
    try:
        # BUG: Has a strict timeout of 2.0 seconds. Downstream requires 8.0 seconds.
        # The recovery requires updating the timeout to 10.0 or higher.
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2.0) as response:
            payload = json.loads(response.read().decode('utf-8'))
            print("Successfully fetched gateway metrics:")
            print(f" - Status: {payload.get('status')}")
            print(f" - Data: {payload.get('data')}")
            print("Gateway Retrieval: SUCCESS")
    except urllib.error.URLError as e:
        print(f"Gateway retrieval failed due to connection error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected gateway error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
