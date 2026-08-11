#!/usr/bin/env python3
import socketserver

class Handler(socketserver.BaseRequestHandler):
    counter = 0
    def handle(self):
        type(self).counter += 1
        data = self.request.recv(1024)
        if type(self).counter % 2 == 1:
            return
        if data:
            self.request.sendall(b"OK\n")

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

Server(("0.0.0.0", 5432), Handler).serve_forever()
