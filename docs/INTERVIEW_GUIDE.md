# Interview preparation and demo guide

## A 45-second explanation

> This is a personal supplier-risk and procurement analytics demonstration built with fictional purchase-order data. It loads 900 simulated POs for 15 suppliers into SQLite, uses SQL to calculate delivery, quality, and cost metrics, and applies an explainable weighted score that also includes illustrative geographic exposure and category spend concentration. The Python dashboard lets me investigate the drivers, adjust weights, and export the scorecard. There is also an optional generative-AI feature that can turn one supplier's aggregate metrics into a written brief. I would validate the thresholds and inputs with procurement experts before applying this to real decisions.

Adapt this to reflect your own understanding and the work you actually did. If asked how it was built, be honest about any coding assistance you received and be ready to explain the implementation.

## Two-minute live walkthrough

1. Start the dashboard (`python app.py` or `py app.py`) before the interview. On **Overview**, identify the dataset as simulated and point to 15 suppliers, 900 POs, and six high-risk suppliers under the default assumptions.
2. Go to **Supplier analysis** and choose **Horizon Rotary**. Its displayed score is about **79.5 / 100**, high under the example thresholds. Explain that the score is a weighted indicator, not a 79.5% probability of disruption.
3. Explain its key evidence: **15 of 38** orders were late (**39.5%**), **121 of 4,396** units were defective (**2.75%**), and actual spend was **7.64%** above contracted spend. These values are generated examples.
4. Show the risk contributions: delivery **30.0**, quality **22.9**, cost **15.3**, geography **11.3**, and concentration **0.0**, which sum to approximately **79.5** after rounding. Delivery hits its maximum input because 39.5% is above the illustrative 30% cap. The concentration contribution is zero because its category share is below 25%.
5. Adjust a weight to demonstrate sensitivity. Explain that each slider is a relative weight, and the app normalizes the five values to add up to 100%. Click **Reset defaults** afterward.
6. Open **Spend & cost**, then **Methodology**. Explain that a positive cost variance is a comparison to contracted prices, not a proven saving. If AI has been configured and tested before the interview, optionally generate a brief; otherwise show the offline rule-based recommendations.

## Likely interview questions

**Why these five factors?**
They cover operational reliability, quality, commercial performance, a scenario assumption for geography, and concentration of spend. They are a starting framework, not a complete supplier-risk model.

**How is the score calculated?**
First SQL aggregates the PO data. Python rescales each input to 0–100 using fixed thresholds. It multiplies each score by its normalized weight and adds the contributions. The model and individual contributions are visible in the application and source code.

**What do the weights represent?**
They express the relative importance of each risk factor in this demonstration: 30% delivery, 25% quality, 20% cost, 15% geography, and 10% concentration. They were selected for the demo, not estimated from historical disruptions. For real use I would work with category managers and perform sensitivity analysis.

**Why use a weighted model instead of machine learning?**
It is easy to explain, needs no labeled historical disruption data, and makes assumptions visible. Its weakness is that it depends heavily on the chosen thresholds and weights and does not establish predictive accuracy.

**How did you measure delivery and quality?**
A PO is late when its delivery date is after the promised date. Late rate is late POs divided by total POs. Defect rate is total defective units divided by total units, which avoids giving a small order and a large order equal influence on quality.

**What is cost variance?**
I compare actual quantity-weighted spend with contracted quantity-weighted spend: `(actual − contracted) / contracted`. The calculation excludes freight, tax, and other total-cost factors. A positive variance is not automatically waste or a proven saving.

**Why use category spend share instead of total company spend share?**
Suppliers within the same category are compared to other suppliers in that category. A large category share can flag concentration for investigation. It does not establish whether another supplier is qualified or can take over the volume.

**What does generative AI do?**
It can write a concise brief based on the selected supplier's already calculated aggregate metrics. It does not determine the risk score. A configured API key and internet connection are required. The default rule-based suggestions are separate from AI. Be clear whether you actually configured and tested a live call; the automated test uses a mocked response.

**Why SQLite and Python?**
SQLite provides a lightweight SQL database that runs locally, and Python calculates the model and serves the dashboard. The use of the standard library keeps the demo easy to reproduce without separate packages or database infrastructure.

**How would you improve it for a real company?**
Use approved data and access controls; validate supplier identities and data quality; add lead-time severity, partial deliveries, returns, supplier capacity, and financial inputs; calibrate the weights with subject-matter experts; test sensitivity and backtest against historical outcomes; and connect to a governed database. Do not expose the current local prototype to the internet or confidential production data.

## Questions you should be able to answer about the code

- `scripts/generate_data.py` uses a fixed random seed to make reproducible fictional data.
- `sql/schema.sql` creates the supplier and purchase-order tables plus a `supplier_metrics` SQL view.
- `analytics.py` loads the CSVs into SQLite, calculates category totals and risk components, normalizes weights, and creates rule-based next steps.
- `app.py` serves the local dashboard and exposes endpoints for metrics, export, and optional AI.
- `ai_client.py` sends an optional request to the OpenAI Responses API, keeping the API key in an environment variable.
- `static/` contains the interface, styling, and browser interaction code.
- `tests/test_project.py` checks data integrity, hand-calculated results, filtering, exports, HTTP endpoints, and a mocked AI response.

## Accuracy checklist before presenting

- Identify the data as simulated, and describe this as a personal prototype.
- Do not claim actual company cost savings, real supplier disruptions, production deployment, validated predictions, or a completed Power BI report unless you have independently done those things.
- Test the dashboard on the computer you will use. If you want to demo AI, configure a key and verify the live call in advance; otherwise use the offline features.
- Read the code and methodology, practice changing weights, and be prepared to describe your own contribution and any coding assistance honestly.
