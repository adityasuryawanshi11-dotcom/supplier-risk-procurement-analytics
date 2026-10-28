# Supplier Risk & Procurement Analytics

An interview-ready **personal demonstration project** that turns fictional purchase orders into an explainable supplier-risk dashboard. Python and SQLite perform the calculations; a local browser interface lets you explore results, compare spend, adjust weights, and generate an optional AI-written supplier brief.

> **Data disclosure:** All 15 suppliers and 900 purchase orders are synthetic. Scores, weights, thresholds, and geographic exposure values are illustrative. This is a decision-support prototype, not a validated production model or evidence of actual savings.

## What it does

- Loads supplier and purchase-order CSVs into an in-memory SQLite database and calculates supplier-level metrics with SQL.
- Compares late orders, defective units, actual versus contracted spend, fictional geographic exposure, and share of category spend.
- Scores each supplier on a 0–100 scale, shows each risk contribution, and lets the user change relative weights.
- Filters by product category or region, visualizes spend and risk, provides rule-based next steps, and exports the current supplier scorecard as CSV.
- Optionally calls the OpenAI Responses API for a natural-language summary of a selected supplier's **aggregated fictional metrics**. This feature requires a separately configured API key and internet access; the dashboard and its rule-based actions do not.
- Includes Power BI-ready exports and instructions for building a report in Power BI Desktop. It does **not** include a prebuilt `.pbix` file.

## Quick start

Requires Python 3.10 or later. No third-party Python packages are needed.

1. Download or clone the project and open a terminal inside the project folder.
2. Run:

   ```bash
   python app.py
   ```

   On Windows, if `python` does not work, try `py app.py`.
3. Open **http://127.0.0.1:8000** in your browser. Keep the terminal open while using the dashboard. Press `Ctrl+C` in the terminal to stop it.

New to Python or GitHub? Read [START_HERE.md](START_HERE.md) for a beginner-friendly setup and publishing walkthrough.

## Example baseline results

With the supplied data and default weights, the dashboard calculates:

| Metric | Result |
| --- | ---: |
| Suppliers / completed POs | 15 / 900 |
| Actual spend | $7,861,005.36 |
| Late orders | 176 / 900 = 19.6% |
| Defective units | 2,359 / 204,113 = 1.16% |
| High-risk suppliers | 6 / 15 |

These are **results in a synthetic dataset**, not company outcomes. Change filters or weights and the displayed results will change.

## Risk model

Each component is capped at 100, then multiplied by its weight. Default weights sum to 100%:

| Component | Default weight | Risk input |
| --- | ---: | --- |
| Delivery | 30% | Late-order rate scaled to 100 at 30% |
| Quality | 25% | Defective-unit rate scaled to 100 at 3% |
| Cost | 20% | Positive cost variance scaled to 100 at 10% |
| Geography | 15% | Fictional exposure input from 0 to 100 |
| Concentration | 10% | Supplier category spend share scaled from 25% to 60% |

A score below 30 is low, 30 to below 60 is medium, and 60 or above is high. The scoring thresholds and geography inputs are examples, not industry standards. Weights are normalized when changed. See [the full methodology](docs/METHODOLOGY.md) for formulas, denominators, and limitations.

## Optional generative AI

The dashboard runs without an API key. To enable AI briefs, set `OPENAI_API_KEY` in the **same terminal** before starting the app. Never commit a key to GitHub. The default model is `gpt-4.1-mini`; set `OPENAI_MODEL` to another model available to your API account if desired.

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "YOUR_API_KEY"
py app.py
```

macOS / Linux:

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
python3 app.py
```

In **Supplier analysis**, choose a supplier and click **Generate AI brief**. This sends that supplier's aggregate metrics, risk inputs, and weights to OpenAI; it does not send the full PO dataset. API usage may be billed separately. Review generated claims before using them. This demo's rule-based recommendations are distinct from generative AI and always work offline.

## Reproduce the data and run tests

```bash
python scripts/generate_data.py
python scripts/export_for_powerbi.py
python -m unittest discover -s tests -v
```

The generator uses a fixed seed and recreates the supplied supplier and purchase-order CSVs. It overwrites those two files; do not run it on files containing your own data. Run the export script after regenerating the data. The tests include independently hand-calculated examples, data integrity checks, HTTP endpoints, and a **mocked** AI request; they do not make a live OpenAI call.

## Project structure

```text
app.py                         Local Python web server and API endpoints
analytics.py                   Database loading, risk model, and recommendations
ai_client.py                   Optional OpenAI Responses API integration
static/                        HTML, CSS, and JavaScript dashboard
data/suppliers.csv             15 invented suppliers
data/purchase_orders.csv       900 invented completed purchase orders
data/supplier_metrics.csv      Default-weight export for Power BI / Excel
sql/schema.sql                 Database schema and SQL metrics view
sql/analysis_queries.sql       Additional procurement analysis queries
scripts/generate_data.py       Reproducible fictional-data generator
scripts/export_for_powerbi.py  Rebuild the supplier metrics export
tests/test_project.py          Unit and local HTTP integration tests
docs/                          Methodology, Power BI, and interview guides
```

## Documentation

- [Start here: setup and GitHub](START_HERE.md)
- [Methodology and data dictionary](docs/METHODOLOGY.md)
- [Interview preparation and demo script](docs/INTERVIEW_GUIDE.md)
- [Build a Power BI report from the exports](docs/POWER_BI_GUIDE.md)

The application binds to `127.0.0.1` for local use and has no authentication; it is not intended to be exposed to the internet or used with confidential production data without additional security, validation, and access controls.
