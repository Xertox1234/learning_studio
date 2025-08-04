#!/usr/bin/env python3
import http.server
import socketserver
import sys

PORT = 9999

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

print(f"Starting test server on port {PORT}...")
print(f"Try accessing: http://127.0.0.1:{PORT}")
print(f"Also try: http://localhost:{PORT}")
print(f"And: http://0.0.0.0:{PORT}")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"Server started successfully on port {PORT}")
    httpd.serve_forever()