# Methodology and data dictionary

## Scope

This is an explainable, illustrative risk-prioritization tool built using completely fictional data. The supplier names, regions, geography inputs, order quantities, prices, dates, defects, and relationships are generated for the demo. The dataset contains 15 suppliers across five categories and 900 completed purchase orders. Each PO contains one simplified item line. `scripts/generate_data.py` recreates the dataset with seed `20261027`.

The dashboard loads both CSVs into an in-memory SQLite database. The SQL view `supplier_metrics` in `sql/schema.sql` aggregates each supplier's data. Python transforms these aggregates into risk inputs, calculates the weighted score, and creates simple rule-based suggestions. The local browser sends requests to the Python server. Optional generative AI receives only the selected supplier's aggregate data when the user clicks the AI button.

## Source data dictionary

### `data/suppliers.csv` — one row per supplier

| Field | Meaning |
| --- | --- |
| `supplier_id` | Unique fictional supplier identifier. |
| `supplier_name` | Fictional supplier name. |
| `category` | Fictional product category. |
| `region` | Broad fictional operating region label. |
| `geo_exposure` | Manually assigned illustrative 0–100 exposure assumption. It is not a measured geopolitical risk and must not be used as a real-world regional rating. |

### `data/purchase_orders.csv` — one row per completed PO

| Field | Meaning |
| --- | --- |
| `po_id` | Unique fictional purchase-order identifier. |
| `supplier_id` | Foreign key to `suppliers.csv`. |
| `order_date` | Date the purchase order was placed, ISO format. |
| `promised_date` | Date the supplier promised delivery, ISO format. |
| `delivery_date` | Actual delivery date, ISO format. |
| `item` | Simplified item description. |
| `quantity` | Number of units ordered and delivered. |
| `defect_units` | Number of those units marked defective; not greater than quantity. |
| `contracted_unit_price` | Contracted price per unit, fictional USD. |
| `actual_unit_price` | Actual price per unit, fictional USD. |

### `data/supplier_metrics.csv`

A generated, default-weight snapshot with one row per supplier. The rate fields (`late_rate`, `defect_rate`, `cost_variance_rate`, `category_share`) are **fractions**, so 0.20 means 20%. Re-run `python scripts/export_for_powerbi.py` after regenerating the source data. The dashboard's **Export metrics** button exports the currently filtered suppliers with the current weights; it does not modify the bundled snapshot.

## Formulas

For each supplier, sum quantities and monetary values across its purchase orders:

- **Late-order rate** = number of POs where `delivery_date > promised_date` ÷ number of completed POs. An order delivered on its promised date is on time. This is PO-weighted, not unit-weighted.
- **Defect rate** = sum of `defect_units` ÷ sum of `quantity`. This is unit-weighted, not an average of per-order defect percentages.
- **Actual spend** = sum of (`quantity` × `actual_unit_price`).
- **Contracted spend** = sum of (`quantity` × `contracted_unit_price`).
- **Cost variance rate** = (`actual spend` − `contracted spend`) ÷ `contracted spend`. It is signed; negative variance is not treated as risk in the score.
- **Category spend share** = supplier actual spend ÷ total actual spend across **all suppliers in the same product category**. This denominator remains the complete category even when filtering by region.

Portfolio late and defect rates are calculated from the combined counts and quantities, respectively, rather than by simply averaging supplier rates.

## Risk scoring

The example thresholds below translate different metrics into a common 0–100 scale. `clip(x)` means keep `x` between 0 and 100.

| Component | Risk input on a 0–100 scale | Default weight |
| --- | --- | ---: |
| Delivery | `clip(100 × late_order_rate / 0.30)` | 30% |
| Quality | `clip(100 × defect_rate / 0.03)` | 25% |
| Cost | `clip(100 × max(0, cost_variance_rate) / 0.10)` | 20% |
| Geography | `clip(geo_exposure)` | 15% |
| Concentration | `clip(100 × (category_spend_share − 0.25) / 0.35)` | 10% |

**Overall score** = sum of (`component risk input` × `normalized component weight`). Weights entered as relative numbers are divided by their total; at least one must be positive. Each displayed contribution equals `component risk input × normalized weight`, so the contributions sum to the overall score, subject to display rounding.

- Low: `< 30`
- Medium: `30 ≤ score < 60`
- High: `score ≥ 60`

These thresholds and weights are chosen for an educational scenario; they have not been calibrated or validated against actual disruptions. They are not default industry standards, a prediction, or a probability of supplier failure. Adjusting weights is sensitivity analysis, not evidence of an objectively correct answer.

## Suggestions and AI

Rule-based suggestions correspond to the two largest weighted contributions. For example, when delivery is a major contributor, the application suggests reviewing lead times and a corrective-action plan. These suggestions are not generated by a language model.

The optional AI button calls the OpenAI Responses API with a concise prompt and the selected supplier's aggregate metrics. A live call requires an API key and may incur charges. AI text can be wrong and must be checked against the displayed metrics. The software's AI test uses a mock response and does not prove a live API call succeeded.

## Limitations and responsible interpretation

- This is synthetic, simplified, completed-PO data. It contains no open orders, partial deliveries, returns, freight, taxes, capacity, supplier financials, causal relationships, or independently verified risk data.
- The geography values and all thresholds are assumptions. A real project would need validated inputs, domain-expert review, sensitivity testing, robust quality checks, and outcome-based backtesting.
- The cost variance compares actual and contracted values for the same units; it is not profit impact, a negotiated saving, total cost of ownership, or a causal estimate.
- Category spend concentration is a concentration indicator, not proof of dependency, substitutability, or the savings available from switching suppliers.
- The local server has no login or authorization and is not designed for deployment or real confidential data.
