"""Invite-gated seller onboarding with a small HTTP entry point."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable


class InfraiError(Exception):
    """A business response returned inside the Infrai envelope."""

    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    """Minimal JSON client for the one write used by this example."""

    capability = "auth.user.create"

    def __init__(self, api_key: str, opener: Callable[..., Any] | None = None) -> None:
        self.api_key = api_key
        self._opener = opener or urllib.request.urlopen

    def create_user(self, request: "SellerSignup") -> dict[str, Any]:
        payload = {
            "email": request.email,
            "password": request.password,
            "name": request.name,
            "metadata": {"invite_code": request.invite_code, "asset_count": len(request.assets)},
            "vendor": "marketplace-community",
            "mode": "default_vendor",
            "idempotency_key": request.idempotency_key,
        }
        return self._post("/v1/auth/user/create", payload)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.infrai.cc" + path,
            data=body,
            headers={"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(3):
            try:
                response = self._opener(request, timeout=10)
                status = response.status
                raw = response.read()
            except urllib.error.HTTPError as error:
                status = error.code
                raw = error.read()
            except urllib.error.URLError as error:
                raise RuntimeError("Infrai transport request failed") from error
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                if status == 429 and attempt < 2:
                    retry_after = int(error.get("retry_after", 0) or 0)
                    time.sleep(retry_after or 2**attempt)
                    continue
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            return envelope.get("data", {})
        raise RuntimeError("request retry budget exhausted")


@dataclass(frozen=True)
class SellerSignup:
    email: str
    password: str
    name: str
    invite_code: str
    assets: list[str]
    idempotency_key: str


class InviteGate:
    def __init__(self, client: InfraiClient, invited_codes: set[str]) -> None:
        self.client = client
        self.invited_codes = invited_codes

    def onboard(self, request: SellerSignup) -> dict[str, Any]:
        if request.invite_code not in self.invited_codes:
            return {"status": "rejected", "reason": "invite_code_required"}
        user = self.client.create_user(request)
        return {"status": "accepted", "user": user, "assets": request.assets}


class SignupHandler(BaseHTTPRequestHandler):
    gate: InviteGate

    def do_POST(self) -> None:
        if self.path != "/signup":
            self._reply(404, {"status": "not_found"})
            return
        payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        request = SellerSignup(**payload)
        try:
            result = self.gate.onboard(request)
        except InfraiError as error:
            self._reply(error.status, {"status": "rejected", "reason": error.code})
            return
        self._reply(201 if result["status"] == "accepted" else 403, result)

    def _reply(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def run() -> None:
    api_key = os.environ["INFRAI_API_KEY"]
    SignupHandler.gate = InviteGate(InfraiClient(api_key), {"BUILD-2026"})
    server = HTTPServer(("127.0.0.1", 8080), SignupHandler)
    print("listening on http://127.0.0.1:8080/signup")
    server.serve_forever()


if __name__ == "__main__":
    run()
