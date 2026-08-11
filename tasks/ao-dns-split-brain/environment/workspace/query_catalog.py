#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.error

config_path = "config.json"

def load_config():
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config {config_path}: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    config = load_config()
    url = config.get("catalog_url")
    
    print(f"Connecting to catalog registry at: {url}")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CatalogClient/1.0'})
        with urllib.request.urlopen(req, timeout=2.0) as response:
            payload = json.loads(response.read().decode('utf-8'))
            print("Successfully retrieved product catalog:")
            for item in payload:
                print(f" - [ID {item.get('id')}] {item.get('name')}")
            print("Catalog Retrieval: SUCCESS")
    except urllib.error.URLError as e:
        print(f"Catalog retrieval failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
