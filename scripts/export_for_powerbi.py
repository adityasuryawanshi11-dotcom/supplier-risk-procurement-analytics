"""Export the default-weight supplier analytics for Power BI or Excel."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analytics import make_database, report
from app import export_csv

if __name__ == "__main__":
    with make_database() as db:
        metrics = report(db)["suppliers"]
    out = ROOT / "data" / "supplier_metrics.csv"
    out.write_text(export_csv(metrics), encoding="utf-8", newline="")
    print(f"Wrote {len(metrics)} supplier rows to {out}")
