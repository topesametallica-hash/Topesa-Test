from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json

HOST = "0.0.0.0"
PORT = 5000
ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "relay_state.json"

DEFAULT_STATE = {
    "Light": False,
    "Pump": False,
    "Fan": False,
    "Spare": False,
}


if not STATE_FILE.exists():
    STATE_FILE.write_text(json.dumps(DEFAULT_STATE))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/relays":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            state = self.load_state()
            self.wfile.write(json.dumps(state).encode())
            return

        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/relays":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            try:
                payload = json.loads(body.decode())
                self.save_state(payload)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()

                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as error:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()

                self.wfile.write(json.dumps({
                    "success": False,
                    "error": str(error)
                }).encode())

            return

        self.send_response(404)
        self.end_headers()

    def load_state(self):
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return DEFAULT_STATE

    def save_state(self, state):
        STATE_FILE.write_text(json.dumps(state))


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Relay API running at http://{HOST}:{PORT}")
    server.serve_forever()
