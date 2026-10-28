"""SQLite-backed, transparent supplier risk analytics for the demo application."""
from __future__ import annotations

import csv
import math
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_WEIGHTS = {"delivery": 30.0, "quality": 25.0, "cost": 20.0,
                   "geography": 15.0, "concentration": 10.0}
LABELS = {"delivery": "Late delivery", "quality": "Quality defects", "cost": "Cost variance",
          "geography": "Geographic exposure", "concentration": "Category spend concentration"}


def make_database(root: Path = ROOT) -> sqlite3.Connection:
    """Load bundled CSVs into an in-memory SQLite database; no data leaves the machine."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript((root / "sql" / "schema.sql").read_text(encoding="utf-8"))
    for filename, table, cols in [
        ("suppliers.csv", "suppliers", ("supplier_id", "supplier_name", "category", "region", "geo_exposure")),
        ("purchase_orders.csv", "purchase_orders", ("po_id", "supplier_id", "order_date", "promised_date", "delivery_date", "item", "quantity", "defect_units", "contracted_unit_price", "actual_unit_price")),
    ]:
        with (root / "data" / filename).open(newline="", encoding="utf-8") as file:
            rows = csv.DictReader(file)
            conn.executemany(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
                             ([row[col] for col in cols] for row in rows))
    return conn


def normalize_weights(weights: dict | None = None) -> dict[str, float]:
    """Accept five nonnegative relative weights; normalize them to add to one."""
    raw = DEFAULT_WEIGHTS if weights is None else weights
    if set(raw) != set(DEFAULT_WEIGHTS):
        raise ValueError("Provide all five risk weights.")
    try:
        values = {key: float(raw[key]) for key in DEFAULT_WEIGHTS}
    except (TypeError, ValueError):
        raise ValueError("Weights must be numeric.") from None
    if any(not math.isfinite(v) or v < 0 for v in values.values()) or sum(values.values()) <= 0:
        raise ValueError("Weights must be finite, nonnegative, and sum to more than zero.")
    total = sum(values.values())
    return {k: v / total for k, v in values.items()}


def clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def components(row: dict, category_spend: float) -> tuple[dict[str, float], float]:
    """Transform supplier metrics to comparable 0–100 risk inputs (higher is riskier)."""
    share = row["actual_spend"] / category_spend if category_spend else 0.0
    scores = {
        "delivery": clamp(100.0 * row["late_rate"] / .30),
        "quality": clamp(100.0 * row["defect_rate"] / .03),
        "cost": clamp(100.0 * max(0.0, row["cost_variance_rate"]) / .10),
        "geography": clamp(row["geo_exposure"]),
        "concentration": clamp(100.0 * (share - .25) / .35),
    }
    return scores, share


def recommendations(row: dict) -> list[dict[str, str]]:
    """Rule-based suggestions for the two largest weighted drivers, never AI-generated."""
    prompts = {
        "delivery": (f"{row['late_rate']:.1%} of orders arrived late.", "Review promised versus actual lead times with the supplier; agree on a corrective action and monitor on-time delivery."),
        "quality": (f"{row['defect_rate']:.2%} of units were marked defective.", "Investigate defect causes with the supplier and agree on a corrective-action plan and incoming quality checks."),
        "cost": (f"Actual spend is {row['cost_variance_rate']:+.1%} versus contracted spend.", "Review invoice prices against contract terms and investigate the causes of unfavorable variance."),
        "geography": (f"The illustrative geographic exposure input is {row['geo_exposure']:.0f}/100.", "Validate the exposure assumption and assess contingency plans, logistics routes, and an alternate source."),
        "concentration": (f"This supplier accounts for {row['category_share']:.1%} of its category's spend.", "Assess qualification of an alternate supplier and the impact of reducing reliance on a single source."),
    }
    ranked = sorted(row["contributions"], key=row["contributions"].get, reverse=True)
    return [{"driver": LABELS[k], "evidence": prompts[k][0], "action": prompts[k][1]} for k in ranked[:2]]


def report(conn: sqlite3.Connection, weights: dict | None = None,
           category: str = "All", region: str = "All") -> dict:
    normalized = normalize_weights(weights)
    raw = [dict(row) for row in conn.execute("SELECT * FROM supplier_metrics")]
    category_totals: dict[str, float] = {}
    for row in raw:
        category_totals[row["category"]] = category_totals.get(row["category"], 0.0) + row["actual_spend"]
    rows = []
    for row in raw:
        scores, share = components(row, category_totals[row["category"]])
        contributions = {k: scores[k] * normalized[k] for k in normalized}
        score = sum(contributions.values())
        row.update(category_share=share, scores=scores, contributions=contributions,
                   risk_score=score, risk_band="High" if score >= 60 else "Medium" if score >= 30 else "Low")
        row["recommendations"] = recommendations(row)
        if (category == "All" or row["category"] == category) and (region == "All" or row["region"] == region):
            rows.append(row)
    rows.sort(key=lambda r: (-r["risk_score"], r["supplier_name"]))
    spend = sum(r["actual_spend"] for r in rows)
    contract = sum(r["contracted_spend"] for r in rows)
    units = sum(r["units"] for r in rows)
    orders = sum(r["po_count"] for r in rows)
    summary = {
        "total_spend": spend, "contracted_spend": contract, "po_count": orders,
        "supplier_count": len(rows), "late_orders": sum(r["late_orders"] for r in rows),
        "late_rate": sum(r["late_orders"] for r in rows) / orders if orders else 0.0,
        "units": units, "defect_units": sum(r["defect_units"] for r in rows),
        "defect_rate": sum(r["defect_units"] for r in rows) / units if units else 0.0,
        "cost_variance_rate": (spend - contract) / contract if contract else 0.0,
        "high_risk_count": sum(r["risk_band"] == "High" for r in rows),
    }
    return {"summary": summary, "suppliers": rows, "weights": normalized,
            "categories": sorted({r["category"] for r in raw}),
            "regions": sorted({r["region"] for r in raw})}
