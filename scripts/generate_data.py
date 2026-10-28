"""Reproducible, fictional procurement data. Run from the project root."""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SEED = 20261027

# All names, scores, transactions, and commercial relationships are invented.
# Geography exposure is a hypothetical scenario input, not a real country rating.
SPECS = [
    # name, category, region, scenario exposure, order count, late chance,
    # unit defect rate, unit cost variance, reference price, item
    ("Atlas Sealworks", "Seals", "North America", 20, 88, .08, .004, .01, 18, "Industrial seal"),
    ("Meridian Gasket Co.", "Seals", "Europe", 45, 54, .22, .013, .04, 18, "Industrial seal"),
    ("Pacifica Polymer", "Seals", "Asia-Pacific", 75, 38, .42, .025, .08, 18, "Industrial seal"),
    ("Northstar Fasteners", "Fasteners", "North America", 20, 88, .10, .006, .01, 6, "Fastener kit"),
    ("Ironbridge Components", "Fasteners", "Europe", 45, 54, .19, .012, .03, 6, "Fastener kit"),
    ("Stratus Hardware", "Fasteners", "Asia-Pacific", 75, 38, .34, .022, .06, 6, "Fastener kit"),
    ("Prairie Motion", "Bearings", "North America", 20, 88, .12, .006, .02, 55, "Bearing assembly"),
    ("Vector Bearings", "Bearings", "Europe", 45, 54, .24, .015, .04, 55, "Bearing assembly"),
    ("Horizon Rotary", "Bearings", "Asia-Pacific", 75, 38, .39, .027, .07, 55, "Bearing assembly"),
    ("Cedar Flow Control", "Valves", "North America", 20, 88, .11, .005, .02, 120, "Control valve"),
    ("Andes Valve Works", "Valves", "Latin America", 60, 54, .25, .017, .05, 120, "Control valve"),
    ("Eastern Process Parts", "Valves", "Asia-Pacific", 75, 38, .38, .029, .09, 120, "Control valve"),
    ("Summit Electrics", "Electrical", "North America", 20, 88, .09, .005, .01, 85, "Electrical assembly"),
    ("Beacon Controls", "Electrical", "Europe", 45, 54, .21, .014, .04, 85, "Electrical assembly"),
    ("Solstice Industrial", "Electrical", "Latin America", 60, 38, .37, .023, .06, 85, "Electrical assembly"),
]


def generate():
    DATA.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    suppliers, orders = [], []
    for index, (name, category, region, exposure, count, late_prob, defect_rate, cost_bias, ref_price, item) in enumerate(SPECS, 1):
        supplier_id = f"SUP-{index:03d}"
        suppliers.append(dict(supplier_id=supplier_id, supplier_name=name, category=category,
                              region=region, geo_exposure=exposure))
        for _ in range(count):
            order = date(2024, 1, 1) + timedelta(days=rng.randrange(900))
            promised = order + timedelta(days=rng.randint(14, 45))
            late_days = rng.randint(1, 18) if rng.random() < late_prob else -rng.randint(0, 7)
            delivered = promised + timedelta(days=late_days)
            quantity = rng.randint(40, 700) if category in ("Seals", "Fasteners") else rng.randint(15, 240)
            observed_defects = max(0, min(quantity, round(quantity * rng.uniform(.7, 1.3) * defect_rate)))
            contracted = round(ref_price * rng.uniform(.90, 1.10), 2)
            actual = round(contracted * max(.85, 1 + rng.gauss(cost_bias, .018)), 2)
            orders.append(dict(po_id=f"PO-{len(orders)+1:05d}", supplier_id=supplier_id,
                order_date=order.isoformat(), promised_date=promised.isoformat(),
                delivery_date=delivered.isoformat(), item=item, quantity=quantity,
                defect_units=observed_defects, contracted_unit_price=f"{contracted:.2f}",
                actual_unit_price=f"{actual:.2f}"))
    for filename, rows in [("suppliers.csv", suppliers), ("purchase_orders.csv", orders)]:
        with (DATA / filename).open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(f"Generated {len(suppliers)} fictional suppliers and {len(orders)} fictional completed purchase orders (seed {SEED}).")

if __name__ == "__main__":
    generate()
