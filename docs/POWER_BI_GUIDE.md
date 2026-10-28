# Build a Power BI report from the project data

The project includes import-ready CSVs, but **does not contain a finished Power BI `.pbix` file**. These steps let you create one in Power BI Desktop. Power BI Desktop is a separate application; the Python dashboard does not require it.

## 1. Import the data

1. Open Power BI Desktop. Choose **Get data → Text/CSV** and import `data/supplier_metrics.csv`.
2. Import `data/purchase_orders.csv` the same way.
3. Confirm the PO date fields are typed as **Date**, quantities/defects as whole numbers, and prices as decimal numbers. Ensure `supplier_id` is text in both tables.
4. In Model view, create a one-to-many relationship from `supplier_metrics[supplier_id]` (one) to `purchase_orders[supplier_id]` (many), with the supplier table filtering the PO table.

The supplier metrics CSV contains scores calculated with the **default weights** across the entire dataset. They are a fixed snapshot: filtering POs by a date in Power BI does not recalculate those risk scores. Re-export from the Python app or rebuild the scoring in Power BI if you need a different scenario.

## 2. Create measures

In the `purchase_orders` table, select **New measure** and add:

```DAX
Actual Spend =
SUMX(
    'purchase_orders',
    'purchase_orders'[quantity] * 'purchase_orders'[actual_unit_price]
)
```

```DAX
Contracted Spend =
SUMX(
    'purchase_orders',
    'purchase_orders'[quantity] * 'purchase_orders'[contracted_unit_price]
)
```

```DAX
Cost Variance % =
DIVIDE([Actual Spend] - [Contracted Spend], [Contracted Spend])
```

```DAX
Late Order % =
DIVIDE(
    COUNTROWS(FILTER('purchase_orders', 'purchase_orders'[delivery_date] > 'purchase_orders'[promised_date])),
    COUNTROWS('purchase_orders')
)
```

```DAX
Defect Rate % =
DIVIDE(SUM('purchase_orders'[defect_units]), SUM('purchase_orders'[quantity]))
```

Format the percentage measures as percentages and spend measures as currency. `late_rate`, `defect_rate`, and `category_share` in the supplier export are fractions; format them as percentages rather than multiplying by 100 twice.

## 3. Suggested visuals

- **Cards:** Actual Spend, Cost Variance %, Late Order %, Defect Rate %.
- **Bar chart:** supplier name by `risk_score`, colored or filtered by `risk_band`.
- **Bar chart:** category by Actual Spend.
- **Table:** supplier name, category, region, `risk_score`, `risk_band`, `late_rate`, and `defect_rate`.
- **Slicers:** category and region from `supplier_metrics`.

Save the finished file as your own `.pbix`. Verify that its grand totals match the Python dashboard before presenting, and label the data as synthetic. The supplied DAX measures should respond to category/region filters through the relationship; snapshot risk scores will remain fixed.
