#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_KEY = "test-secret-value"


class AllocatorHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.headers.get("Authorization") != f"Bearer {TEST_KEY}":
            self.send_json(401, {"detail": {"code": "unauthorized", "message": "Invalid API token"}})
            return

        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/v1/lookup":
            name_key = urllib.parse.parse_qs(parsed.query).get("name_key", [""])[0]
            if name_key == "Known-Name-Key":
                self.send_json(200, {"found": True, "name_key": name_key, "z_code": "ZTST-10000-100001-010"})
            elif name_key == "Server-Failure":
                self.send_json(500, {"detail": {"code": "server_error", "message": "Test server failure"}})
            else:
                self.send_json(404, {"detail": {"code": "not_found", "message": "Name-Key was not found"}})
            return

        if parsed.path.startswith("/v1/status/"):
            self.send_json(404, {"detail": {"code": "not_found", "message": "Request was not found"}})
            return

        self.send_json(500, {"detail": {"code": "server_error", "message": "Unexpected test route"}})


def run_client(command: list[str], base_url: str, key: str = TEST_KEY) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.update(
        {
            "ZCODE_ALLOCATOR_URL": base_url,
            "ZCODE_API_KEY": key,
            "ZCODE_AGENT_NAME": "test-agent",
        }
    )
    return subprocess.run(command, env=environment, capture_output=True, text=True, timeout=20, check=False)


def closed_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def assert_secret_absent(result: subprocess.CompletedProcess[str]) -> None:
    assert TEST_KEY not in result.stdout
    assert TEST_KEY not in result.stderr


def test_client(label: str, command_prefix: list[str], base_url: str) -> None:
    missing = run_client(command_prefix + ["lookup", "--name-key", "Missing-Name-Key"], base_url)
    assert missing.returncode == 0, f"{label} lookup miss returned {missing.returncode}: {missing.stderr}"
    assert json.loads(missing.stdout) == {"found": False, "name_key": "Missing-Name-Key"}
    assert_secret_absent(missing)

    found = run_client(command_prefix + ["lookup", "--name-key", "Known-Name-Key"], base_url)
    assert found.returncode == 0, f"{label} known lookup failed: {found.stderr}"
    assert json.loads(found.stdout)["z_code"] == "ZTST-10000-100001-010"
    assert_secret_absent(found)

    status = run_client(command_prefix + ["status", "--request-id", "missing-request"], base_url)
    assert status.returncode == 2, f"{label} unknown status must remain nonzero"
    assert '"http_status": 404' in status.stderr
    assert_secret_absent(status)

    unauthorized = run_client(
        command_prefix + ["lookup", "--name-key", "Missing-Name-Key"],
        base_url,
        key="wrong-test-key",
    )
    assert unauthorized.returncode == 2, f"{label} unauthorized lookup must remain nonzero"
    assert '"http_status": 401' in unauthorized.stderr
    assert "wrong-test-key" not in unauthorized.stdout + unauthorized.stderr

    server_failure = run_client(command_prefix + ["lookup", "--name-key", "Server-Failure"], base_url)
    assert server_failure.returncode == 2, f"{label} server failure must remain nonzero"
    assert '"http_status": 500' in server_failure.stderr
    assert_secret_absent(server_failure)

    malformed = run_client(command_prefix, base_url)
    assert malformed.returncode != 0, f"{label} missing command must fail"
    assert_secret_absent(malformed)

    unavailable = run_client(
        command_prefix + ["lookup", "--name-key", "Missing-Name-Key"],
        f"http://127.0.0.1:{closed_port()}",
    )
    assert unavailable.returncode != 0, f"{label} transport failure must remain nonzero"
    assert "unavailable" in unavailable.stderr.lower()
    assert_secret_absent(unavailable)


def main() -> int:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js is required to test scripts/request_z_code.mjs")

    server = ThreadingHTTPServer(("127.0.0.1", 0), AllocatorHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        test_client("Node client", [node, str(ROOT / "scripts" / "request_z_code.mjs")], base_url)
        test_client("Python client", [sys.executable, str(ROOT / "scripts" / "request_z_code.py")], base_url)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    print("Client semantic tests passed for Node.js and Python helpers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
