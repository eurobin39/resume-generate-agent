from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from code_assistant.definition import orchestrator as code_orchestrator
from resume_assistant.definition import orchestrator as resume_orchestrator


def run_resume_agent(user_input: str, job_description: str = "") -> str:
    return resume_orchestrator(user_input=user_input, job_description=job_description, stream=False)


def run_code_agent(user_request: str, code: str) -> str:
    return code_orchestrator(user_request=user_request, code=code, stream=False)


class AgentGatewayHandler(BaseHTTPRequestHandler):
    server_version = "AgentGateway/1.0"

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        raw_len = self.headers.get("Content-Length")
        if not raw_len:
            return {}
        length = int(raw_len)
        data = self.rfile.read(length).decode("utf-8")
        if not data.strip():
            return {}
        parsed = json.loads(data)
        if not isinstance(parsed, dict):
            raise ValueError("JSON body must be an object")
        return parsed

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self._read_json_body()
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body"})
            return
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        try:
            if self.path == "/v1/resume/run":
                user_input = str(payload.get("user_input", "")).strip()
                job_description = str(payload.get("job_description", ""))
                if not user_input:
                    self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {"error": "Missing required field: user_input"},
                    )
                    return
                output = run_resume_agent(user_input=user_input, job_description=job_description)
                self._send_json(HTTPStatus.OK, {"output": output})
                return

            if self.path == "/v1/code/run":
                user_request = str(payload.get("user_request", "")).strip()
                code = str(payload.get("code", ""))
                if not user_request:
                    self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {"error": "Missing required field: user_request"},
                    )
                    return
                if not code.strip():
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Missing required field: code"})
                    return
                output = run_code_agent(user_request=user_request, code=code)
                self._send_json(HTTPStatus.OK, {"output": output})
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
        except Exception as exc:  # pragma: no cover
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        # Keep default logging concise for local integration usage.
        super().log_message(format, *args)


def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), AgentGatewayHandler)
    print(f"Agent gateway listening on http://{host}:{port}")
    print("Routes: GET /health, POST /v1/resume/run, POST /v1/code/run")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Expose resume/code agents over HTTP.")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    args = parser.parse_args()
    serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
