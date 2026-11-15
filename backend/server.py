"""Serve the standalone HTML dashboard and its same-origin BigQuery API."""
from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

from backend.queries import QUESTIONS, dashboard_payload, question_payload

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
load_dotenv(ROOT / ".env")


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self._api(parsed.path, parse_qs(parsed.query))
            return
        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _api(self, path: str, query: dict[str, list[str]]) -> None:
        if path == "/api/health":
            self._json(200, {"status": "ok"})
            return
        if path == "/api/questions":
            self._json(200, {"questions": [{"id": key, "label": value[0]} for key, value in QUESTIONS.items()]})
            return
        try:
            if path == "/api/dashboard":
                self._json(200, dashboard_payload())
            elif path == "/api/question":
                values = query.get("id", [])
                if len(values) != 1:
                    raise ValueError("Select one supported question.")
                self._json(200, question_payload(values[0]))
            else:
                self._json(404, {"error": "API endpoint not found."})
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            print(f"Dashboard API failure: {type(exc).__name__}", flush=True)
            self._json(
                503,
                {"error": "BigQuery analytics are unavailable. Check project, credentials, datasets, and dbt tables."},
            )


def main() -> None:
    host = os.getenv("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.getenv("DASHBOARD_PORT", "8501"))
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Cafeteria dashboard ready at http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping dashboard server.", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
