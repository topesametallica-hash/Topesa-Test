from __future__ import annotations

import json
import mimetypes
import os
import platform
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parent
STATIC_ROOT = ROOT / "static"
CONFIG_PATH = ROOT.parent / "relays.json"
HOST = os.environ.get("RELAY_HOST", "0.0.0.0")
PORT = int(os.environ.get("RELAY_PORT", "5000"))


@dataclass(frozen=True)
class RelayConfig:
    id: str
    name: str
    pin: int
    active_low: bool = True
    initial_on: bool = False


class RelayBackend:
    def __init__(self, relays: list[RelayConfig], demo: bool) -> None:
        self.relays = relays
        self.demo = demo
        self.states = {relay.id: relay.initial_on for relay in relays}
        self._gpio = None

        if not demo:
            try:
                import RPi.GPIO as GPIO  # type: ignore

                self._gpio = GPIO
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BCM)
                for relay in relays:
                    GPIO.setup(relay.pin, GPIO.OUT)
                    self.set_state(relay.id, relay.initial_on)
            except Exception as exc:
                self.demo = True
                print(f"GPIO unavailable, running in demo mode: {exc}")

    def snapshot(self) -> dict:
        return {
            "mode": "demo" if self.demo else "gpio",
            "relays": [
                {
                    **asdict(relay),
                    "on": self.states[relay.id],
                }
                for relay in self.relays
            ],
        }

    def set_state(self, relay_id: str, on: bool) -> dict:
        relay = self._find(relay_id)
        self.states[relay.id] = on
        if not self.demo and self._gpio is not None:
            output_on = self._gpio.LOW if relay.active_low else self._gpio.HIGH
            output_off = self._gpio.HIGH if relay.active_low else self._gpio.LOW
            self._gpio.output(relay.pin, output_on if on else output_off)
        return self.snapshot()

    def all_off(self) -> dict:
        for relay in self.relays:
            self.set_state(relay.id, False)
        return self.snapshot()

    def cleanup(self) -> None:
        self.all_off()
        if not self.demo and self._gpio is not None:
            self._gpio.cleanup()

    def _find(self, relay_id: str) -> RelayConfig:
        for relay in self.relays:
            if relay.id == relay_id:
                return relay
        raise KeyError(f"Unknown relay: {relay_id}")


def load_relays() -> list[RelayConfig]:
    if not CONFIG_PATH.exists():
        return [
            RelayConfig("relay-1", "Light", 17),
            RelayConfig("relay-2", "Pump", 27),
            RelayConfig("relay-3", "Fan", 22),
            RelayConfig("relay-4", "Spare", 23),
        ]

    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    relays = []
    for index, item in enumerate(data["relays"], start=1):
        relays.append(
            RelayConfig(
                id=item.get("id", f"relay-{index}"),
                name=item["name"],
                pin=item["pin"],
                active_low=item.get("active_low", True),
                initial_on=item.get("initial_on", False),
            )
        )
    return relays


def should_demo() -> bool:
    value = os.environ.get("RELAY_DEMO", "").lower()
    if value in {"1", "true", "yes"}:
        return True
    if value in {"0", "false", "no"}:
        return False
    return platform.system() != "Linux"


backend = RelayBackend(load_relays(), demo=should_demo())


class RelayRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/api/state":
            self._send_json(backend.snapshot())
            return
        self._send_static()

    def do_POST(self) -> None:
        if self.path == "/api/all-off":
            self._send_json(backend.all_off())
            return
        if self.path.startswith("/api/relays/"):
            relay_id = unquote(self.path.removeprefix("/api/relays/"))
            payload = self._read_json()
            try:
                self._send_json(backend.set_state(relay_id, bool(payload["on"])))
            except KeyError:
                self._send_json({"error": "Relay not found"}, HTTPStatus.NOT_FOUND)
            return
        self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args) -> None:
        print(f"{self.client_address[0]} - {format % args}")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def _send_static(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/":
            path = "/index.html"

        target = (STATIC_ROOT / path.lstrip("/")).resolve()
        if STATIC_ROOT.resolve() not in target.parents and target != STATIC_ROOT.resolve():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not target.exists() or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), RelayRequestHandler)
    print(f"Relay web app running at http://{HOST}:{PORT}")
    print(f"Mode: {'DEMO' if backend.demo else 'GPIO'}")
    try:
        server.serve_forever()
    finally:
        backend.cleanup()


if __name__ == "__main__":
    main()
