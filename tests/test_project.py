from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from ai_client import AIError, generate_supplier_brief
from analytics import DEFAULT_WEIGHTS, make_database, normalize_weights, report
from app import Handler, ThreadingHTTPServer, export_csv

ROOT = Path(__file__).resolve().parents[1]


def fixture_db():
    """A small dataset with hand-computable weighted rates and costs."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript((ROOT / "sql" / "schema.sql").read_text())
    db.executemany("INSERT INTO suppliers VALUES (?,?,?,?,?)", [
        ("A", "Alpha", "Seals", "North", 20), ("B", "Beta", "Seals", "South", 0)])
    db.executemany("INSERT INTO purchase_orders VALUES (?,?,?,?,?,?,?,?,?,?)", [
        ("1", "A", "2024-01-01", "2024-01-10", "2024-01-11", "Seal", 100, 10, 10, 12),
        ("2", "A", "2024-01-01", "2024-01-10", "2024-01-09", "Seal", 100, 0, 10, 8),
        ("3", "B", "2024-01-01", "2024-01-10", "2024-01-10", "Seal", 100, 0, 10, 10)])
    return db


class DataTests(unittest.TestCase):
    def test_data_counts_integrity_and_dates(self):
        with make_database() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0], 15)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM purchase_orders").fetchone()[0], 900)
            self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM purchase_orders WHERE delivery_date < order_date OR promised_date < order_date OR defect_units > quantity").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM supplier_metrics").fetchone()[0], 15)

    def test_aggregate_rates_and_score_against_hand_calculation(self):
        with fixture_db() as db:
            result = report(db)
            a = next(x for x in result["suppliers"] if x["supplier_id"] == "A")
            self.assertEqual(a["po_count"], 2)
            self.assertAlmostEqual(a["late_rate"], .5)
            self.assertAlmostEqual(a["defect_rate"], .05)
            self.assertAlmostEqual(a["actual_spend"], 2000)
            self.assertAlmostEqual(a["cost_variance_rate"], 0)
            self.assertAlmostEqual(a["category_share"], 2 / 3)
            # Delivery 30 + quality 25 + cost 0 + geography 3 + concentration 10 = 68.
            self.assertAlmostEqual(a["risk_score"], 68)
            self.assertEqual(a["risk_band"], "High")
            self.assertAlmostEqual(result["summary"]["late_rate"], 1/3)
            self.assertAlmostEqual(result["summary"]["defect_rate"], 10/300)

    def test_category_share_is_not_changed_by_region_filter(self):
        with fixture_db() as db:
            full = next(x for x in report(db)["suppliers"] if x["supplier_id"] == "A")
            filtered = report(db, region="North")["suppliers"][0]
            self.assertAlmostEqual(full["category_share"], filtered["category_share"])
            self.assertEqual(report(db, region="North")["summary"]["po_count"], 2)

    def test_weight_scenarios_and_invalid_weights(self):
        with fixture_db() as db:
            weights = dict.fromkeys(DEFAULT_WEIGHTS, 0)
            weights["geography"] = 10
            row = next(x for x in report(db, weights)["suppliers"] if x["supplier_id"] == "A")
            self.assertAlmostEqual(row["risk_score"], 20)
            self.assertEqual(row["risk_band"], "Low")
        for bad in (dict.fromkeys(DEFAULT_WEIGHTS, 0), {**DEFAULT_WEIGHTS, "quality": -1}, {**DEFAULT_WEIGHTS, "quality": float("nan")}, {"delivery": 30}):
            with self.assertRaises(ValueError):
                normalize_weights(bad)

    def test_export_contains_computed_numeric_metrics(self):
        with make_database() as db:
            rows = list(csv.DictReader(io.StringIO(export_csv(report(db)["suppliers"]))))
        self.assertEqual(len(rows), 15)
        self.assertGreater(float(rows[0]["risk_score"]), 0)
        self.assertIn(rows[0]["risk_band"], ("High", "Medium", "Low"))


class MockResponse:
    def __enter__(self): return self
    def __exit__(self, *args): return None
    def read(self):
        return json.dumps({"output": [{"content": [{"type": "output_text", "text": "Example analysis."}]}]}).encode()


class AITests(unittest.TestCase):
    def test_missing_key_is_clear(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(AIError, "OPENAI_API_KEY"):
                generate_supplier_brief({}, {})

    def test_aggregates_sent_and_text_parsed(self):
        with make_database() as db:
            data = report(db)
        captured = {}
        def fake_open(request, timeout):
            captured["request"] = request
            return MockResponse()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-only-key"}, clear=True), patch("urllib.request.urlopen", side_effect=fake_open):
            result = generate_supplier_brief(data["suppliers"][0], data["weights"])
        self.assertEqual(result, "Example analysis.")
        payload = json.loads(captured["request"].data)
        self.assertEqual(payload["model"], "gpt-4.1-mini")
        self.assertIn("risk_score", payload["input"])
        self.assertNotIn("PO-", payload["input"])
        self.assertNotIn("test-only-key", json.dumps(payload))


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_dashboard_assets_and_report(self):
        with urllib.request.urlopen(self.base + "/") as response:
            self.assertIn(b"Procurement overview", response.read())
        with urllib.request.urlopen(self.base + "/dashboard.js") as response:
            self.assertIn(b"renderOverview", response.read())
        with urllib.request.urlopen(self.base + "/api/report?category=Seals") as response:
            result = json.load(response)
        self.assertEqual(result["summary"]["supplier_count"], 3)
        self.assertEqual(result["summary"]["po_count"], 180)

    def test_export_and_bad_weights(self):
        with urllib.request.urlopen(self.base + "/api/export.csv?category=Seals") as response:
            self.assertEqual(len(list(csv.DictReader(io.StringIO(response.read().decode())))), 3)
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(self.base + "/api/report?delivery=20")
        self.assertEqual(caught.exception.code, 400)

    def test_ai_requires_key_and_json(self):
        request = urllib.request.Request(self.base + "/api/ai", data=b'{"supplier_id":"SUP-001"}', headers={"Content-Type": "application/json"})
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code, 503)
        self.assertIn("OPENAI_API_KEY", caught.exception.read().decode())
        request = urllib.request.Request(self.base + "/api/ai", data=b'{"supplier_id":"SUP-001"}', headers={"Content-Type": "text/plain"})
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
