import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

FILE_PATH = "feedback.json"

class Handler(BaseHTTPRequestHandler):

    # ------------- COMMON HEADERS ----------------
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ------------- OPTIONS (CORS preflight) ----------------
    def do_OPTIONS(self):
        self._set_headers()
        self.wfile.write(b'{}')  # empty JSON

    # ------------- POST: SAVE FEEDBACK ----------------
    def do_POST(self):
        if self.path == "/save-feedback":
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length)

            try:
                with open(FILE_PATH, "w") as f:
                    f.write(data.decode("utf-8"))

                self._set_headers(200)
                self.wfile.write(b'{"status": "saved"}')

            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        else:
            self._set_headers(404)
            self.wfile.write(b'{"error":"Invalid POST path"}')

    # ------------- GET: RETURN FEEDBACK ----------------
    def do_GET(self):
        if self.path == "/feedback.json":
            if os.path.exists(FILE_PATH):
                with open(FILE_PATH, "rb") as f:
                    content = f.read()

                self._set_headers(200)
                self.wfile.write(content)

            else:
                self._set_headers(404)
                self.wfile.write(b'{"error":"No feedback saved yet"}')

        else:
            self._set_headers(404)
            self.wfile.write(b'{"error":"Invalid GET path"}')


# ----------------- START SERVER -------------------
server = HTTPServer(("127.0.0.1", 3005), Handler)
print("Server running at http://127.0.0.1:3005")
server.serve_forever()
