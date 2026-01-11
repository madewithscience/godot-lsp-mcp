from __future__ import annotations

import json
import socket
from pathlib import Path


def make_lsp_message(json_obj: dict) -> bytes:
    body = json.dumps(json_obj)
    content_length = len(body.encode('utf-8'))
    return f"Content-Length: {content_length}\r\n\r\n{body}".encode("utf-8")


def receive_lsp_message(conn: socket.socket, buffer: bytes = b'') -> tuple[dict, bytes] | tuple[None, bytes]:
    conn.settimeout(2.0)
    while b"\r\n\r\n" not in buffer:
        try:
            data = conn.recv(1024)
        except socket.timeout:
            return None, buffer
        if not data:
            return None, buffer
        buffer += data
    headers, body_start = buffer.split(b"\r\n\r\n", 1)
    content_length = 0
    for line in headers.split(b"\r\n"):
        if line.startswith(b"Content-Length:"):
            content_length = int(line.split(b":")[1].strip())
            break

    while len(body_start) < content_length:
        try:
            chunk = conn.recv(1024)
        except socket.timeout:
            break
        body_start += chunk

    message_body = body_start[:content_length]
    remaining_buffer = body_start[content_length:]

    resp = json.loads(message_body.decode("utf-8"))
    return resp, remaining_buffer


def send_initialize(conn: socket.socket):
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "processId": None,
            "rootUri": None,
            "capabilities": {},
        }
    }
    conn.sendall(make_lsp_message(request))


def send_initialized(conn: socket.socket):
    notification = {
        "jsonrpc": "2.0",
        "method": "initialized",
        "params": {}
    }
    conn.sendall(make_lsp_message(notification))


def check_file(conn: socket.socket, gdscript_path: Path):
    message = {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": gdscript_path.as_uri(),
                "languageId": "gdscript",
                "version": 1,
                "text": gdscript_path.read_text()
            }
        }
    }
    conn.sendall(make_lsp_message(message))


def get_project_dir(host: str = '127.0.0.1', port: int = 6005) -> Path:
    with socket.create_connection((host, port)) as sock:
        send_initialize(conn=sock)
        buffer = b""
        while True:
            response, buffer = receive_lsp_message(conn=sock, buffer=buffer)
            if response and "method" in response and response["method"] == "gdscript_client/changeWorkspace":
                return Path(response["params"]["path"])
            if not response:
                break

    return Path.cwd()  # Fallback


def validate_gdscript(scripts: list[Path], host: str = '127.0.0.1', port: int = 6005) -> list[dict]:
    out: list[dict] = []
    with socket.create_connection((host, port)) as sock:
        send_initialize(conn=sock)
        send_initialized(conn=sock)
        buffer = b""
        for script in scripts:
            try:
                check_file(conn=sock, gdscript_path=script)
                # We might need to wait for the specific publishDiagnostics notification
                while True:
                    response, buffer = receive_lsp_message(conn=sock, buffer=buffer)
                    if not response:
                        break
                    if response.get("method") == "textDocument/publishDiagnostics":
                        params = response.get("params")
                        if params and Path(convert_script_to_uri(params.get("uri"))).name == script.name:
                            out.append(params)
                            break
                    if "id" in response and response["id"] == 1:
                        # This is the initialize response, we already got it or it's coming late
                        continue
            except Exception as e:
                print(e)
    return out


def convert_script_to_uri(script: str) -> Path:
    if script.startswith("file://"):
        return Path.from_uri(script)

    return Path(script)

