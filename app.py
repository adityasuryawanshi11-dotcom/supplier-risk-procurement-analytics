"""Local, dependency-free procurement analytics dashboard."""
from __future__ import annotations

import csv
import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from analytics import DEFAULT_WEIGHTS, make_database, report
from ai_client import AIError, generate_supplier_brief

ROOT = Path(__file__).resolve().parent
EXPORT_FIELDS = ["supplier_id", "supplier_name", "category", "region", "po_count", "units", "defect_units", "late_orders", "actual_spend", "contracted_spend", "late_rate", "defect_rate", "cost_variance_rate", "geo_exposure", "category_share", "risk_score", "risk_band"]


def export_csv(rows: list[dict]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_FIELDS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def weights_from_query(query: dict):
    present = {k: query[k][0] for k in DEFAULT_WEIGHTS if k in query}
    return present if present else None


class Handler(BaseHTTPRequestHandler):
    def send_bytes(self, status, body, content_type="application/json; charset=utf-8", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, data):
        self.send_bytes(status, json.dumps(data, allow_nan=False).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        static = {"/": ("index.html", "text/html; charset=utf-8"),
                  "/style.css": ("style.css", "text/css; charset=utf-8"),
                  "/dashboard.js": ("dashboard.js", "text/javascript; charset=utf-8")}
        if parsed.path in static:
            filename, content_type = static[parsed.path]
            self.send_bytes(200, (ROOT / "static" / filename).read_bytes(), content_type)
            return
        if parsed.path not in ("/api/report", "/api/export.csv"):
            self.send_json(404, {"error": "Not found."})
            return
        query = parse_qs(parsed.query)
        try:
            with make_database() as db:
                data = report(db, weights=weights_from_query(query),
                              category=query.get("category", ["All"])[0],
                              region=query.get("region", ["All"])[0])
        except ValueError as exc:
            self.send_json(400, {"error": str(exc)})
            return
        if parsed.path == "/api/report":
            self.send_json(200, data)
        else:
            self.send_bytes(200, export_csv(data["suppliers"]).encode("utf-8"), "text/csv; charset=utf-8",
                            {"Content-Disposition": 'attachment; filename="supplier_metrics.csv"'})

    def do_POST(self):
        if urlparse(self.path).path != "/api/ai":
            self.send_json(404, {"error": "Not found."})
            return
        try:
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Content-Type must be application/json.")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16000:
                raise ValueError("Invalid request size.")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict) or not isinstance(body.get("supplier_id"), str):
                raise ValueError("Provide a supplier ID.")
            with make_database() as db:
                data = report(db, weights=body.get("weights"))
            supplier = next((r for r in data["suppliers"] if r["supplier_id"] == body["supplier_id"]), None)
            if supplier is None:
                raise ValueError("Supplier not found.")
            text = generate_supplier_brief(supplier, data["weights"])
            self.send_json(200, {"text": text})
        except (ValueError, json.JSONDecodeError, TypeError) as exc:
            self.send_json(400, {"error": str(exc) or "Invalid request."})
        except AIError as exc:
            self.send_json(503, {"error": str(exc)})


def main():
    host, port = "127.0.0.1", 8000
    try:
        server = ThreadingHTTPServer((host, port), Handler)
    except OSError as exc:
        raise SystemExit(f"Could not start on http://{host}:{port}: {exc}\nClose the other app using port {port} and retry.")
    print(f"Procurement analytics is running at http://{host}:{port}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
