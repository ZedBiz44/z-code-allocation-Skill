import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def server():
    calls = []
    class Handler(BaseHTTPRequestHandler):
        response = {"z_code":"ZV-45000-100001-050", "request_id":"suzy-test-0001", "status":"reserved", "mapping_version":"test-v1"}
        def log_message(self, *args): pass
        def do_POST(self):
            type(self).last_path = self.path
            calls.append(json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0")))))
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps(self.response).encode())
        def do_GET(self):
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"detail":{"code":"not_found"}}')
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True); thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}", calls, Handler
    httpd.shutdown(); thread.join(); httpd.server_close()


def invoke(language, url, args):
    command = ["node", str(ROOT / "scripts/request_z_code.mjs")] if language == "node" else [sys.executable, str(ROOT / "scripts/request_z_code.py")]
    env = os.environ | {"ZCODE_ALLOCATOR_URL":url, "ZCODE_API_KEY":"test-only", "ZCODE_AGENT_NAME":"suzy"}
    return subprocess.run(command + args, env=env, capture_output=True, text=True, timeout=20)


BASE = ["allocate", "--request-id", "suzy-test-0001", "--name-key", "Example", "--folder", "ZVMP", "--page-type", "Research"]


@pytest.mark.parametrize("language", ["node", "python"])
def test_write_payload_reuses_explicit_id(language, server):
    url, calls, _ = server
    for _ in range(2):
        result = invoke(language, url, BASE)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["z_code"] == "ZV-45000-100001-050"
    assert calls[0] == calls[1]
    assert calls[0]["request_id"] == "suzy-test-0001"
    assert calls[0]["folder_key"] == "ZVMP"
    assert "z_knowledge_core" not in calls[0]


@pytest.mark.parametrize("language", ["node", "python"])
@pytest.mark.parametrize("case", ["missing-id", "unknown-flag", "missing-title", "abbreviated-flag"])
def test_invalid_commands_never_write(language, case, server):
    url, calls, _ = server
    args = list(BASE)
    if case == "missing-id": args = [args[0]] + args[3:]
    if case == "unknown-flag": args += ["--invented", "yes"]
    if case == "missing-title": args = ["confirm", "--z-code", "ZV-45000-100001-050", "--notion-url", "https://www.notion.so/example"]
    if case == "abbreviated-flag": args[1] = "--request-i"
    assert invoke(language, url, args).returncode != 0
    assert calls == []


@pytest.mark.parametrize("language", ["node", "python"])
def test_malformed_success_is_not_reported_as_success(language, server):
    url, _, handler = server
    handler.response = {"ok":True}
    result = invoke(language, url, BASE)
    assert result.returncode != 0
    assert "Incomplete success response" in result.stderr


@pytest.mark.parametrize('language', ['node', 'python'])
@pytest.mark.parametrize('command', ['rename-record', 'delete-record', 'rename-lane'])
def test_record_control_commands(language, command, server):
    url, calls, handler = server
    handler.response = {'z_code': 'Z1-40001-100011-050', 'status': 'deletion_pending',
                        'mirror_event_id': 99, 'record_title': 'Example-Reference-Check',
                        'lane_id': 2, 'name_key': 'Short-Example'}
    args = [command, '--reason', 'Approved test command']
    if command == 'rename-lane':
        args += ['--folder', 'Z1ST', '--name-key', 'Example', '--new-name-key', 'Short-Example']
    else:
        args += ['--z-code', handler.response['z_code'], '--notion-url', 'https://app.notion.com/p/' + 'a' * 32]
        if command == 'rename-record': args += ['--record-title', handler.response['record_title']]
    result = invoke(language, url, args)
    assert result.returncode == 0, result.stderr
    assert calls[0]['reason'] == 'Approved test command'
    assert len(calls) == 1
    assert handler.last_path == '/v1/admin/' + command
    assert 'requested_by' not in calls[0]
    if command == 'rename-record': assert calls[0]['record_title'] == handler.response['record_title']
    if command == 'delete-record': assert 'record_title' not in calls[0]
    if command == 'rename-lane': assert calls[0]['new_name_key'] == 'Short-Example'


@pytest.mark.parametrize('language', ['node', 'python'])
def test_delete_cannot_omit_original_url(language, server):
    url, calls, _ = server
    result = invoke(language, url, ['delete-record', '--z-code', 'Z1-40001-100011-050', '--reason', 'Approved deletion'])
    assert result.returncode != 0
    assert calls == []
