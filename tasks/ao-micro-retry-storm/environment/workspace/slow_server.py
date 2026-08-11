#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import time
import json

class SlowHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/data":
            print("[slow-server] Received query. Injecting 8 seconds delay to simulate lag...")
            time.sleep(8.0)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            resp = {"status": "success", "data": "Staged downstream cluster metrics"}
            self.wfile.write(json.dumps(resp).encode('utf-8'))
            print("[slow-server] Response returned successfully.")
            return
            
        self.send_response(404)
        self.end_headers()

def main():
    server = HTTPServer(('127.0.0.1', 8081), SlowHandler)
    try:
        print("[slow-server] Mock lagging service running on 127.0.0.1:8081...")
        server.serve_forever()
    except Exception as e:
        print(f"[slow-server] Server crashed: {e}")
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
