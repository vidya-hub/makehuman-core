"""Thin TCP client for the MakeHuman server-socket bridge.

The bridge (plugins/8_server_socket) speaks a simple one-request-per-connection
JSON protocol. Every request is a JSON object with exactly these keys::

    {"function": <str>, "params": {...}, "data": null, "error": ""}

The server reads a single request (recv 8192 bytes, so requests must stay
small), dispatches it to an operation, writes a JSON response of the same shape
and closes the connection. The response carries the result in ``data`` and any
failure message in ``error``.
"""

from __future__ import annotations

import json
import socket
from typing import Any


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 12345


class MakeHumanError(RuntimeError):
    """Raised when MakeHuman reports an error in the response ``error`` field."""


class MakeHumanConnectionError(RuntimeError):
    """Raised when MakeHuman cannot be reached (not running / socket disabled)."""


class MHClient:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                 timeout: float = 30.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def call(self, function: str, **params: Any) -> Any:
        """Send one command to MakeHuman and return the ``data`` payload.

        Raises MakeHumanConnectionError if MakeHuman is unreachable, and
        MakeHumanError if MakeHuman returns a non-empty ``error`` field.
        """
        request = json.dumps({
            "function": function,
            "params": params,
            "data": None,
            "error": "",
        })
        payload = request.encode("utf-8")
        if len(payload) > 8192:
            raise MakeHumanError(
                "Request exceeds the 8192-byte limit of the MakeHuman socket")

        try:
            with socket.create_connection((self.host, self.port), self.timeout) as sock:
                sock.settimeout(self.timeout)
                sock.sendall(payload)
                chunks = []
                while True:
                    chunk = sock.recv(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
        except (ConnectionRefusedError, socket.timeout, OSError) as exc:
            raise MakeHumanConnectionError(
                f"Could not reach MakeHuman at {self.host}:{self.port}. "
                "Make sure MakeHuman is running and the Socket plugin has "
                "'Accept connections' enabled. "
                f"({type(exc).__name__}: {exc})"
            ) from exc

        raw = b"".join(chunks).decode("utf-8").strip()
        if not raw:
            # Some ops (e.g. binary mesh responses) or a closed connection may
            # return nothing; treat as a bare OK.
            return "OK"

        try:
            response = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MakeHumanError(f"Invalid JSON response from MakeHuman: {exc}") from exc

        error = response.get("error")
        if error:
            raise MakeHumanError(str(error))
        return response.get("data")

    def ping(self) -> bool:
        """Return True if MakeHuman answers. Uses a known cheap read op."""
        self.call("getAvailableModifierNames")
        return True
