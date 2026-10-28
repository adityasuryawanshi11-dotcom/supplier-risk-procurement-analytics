-- Run after loading the CSVs into the schema in schema.sql.
-- 1. Late delivery and unit defect rates by supplier.
SELECT supplier_name, category, po_count,
       ROUND(100 * late_rate, 1) AS late_order_pct,
       ROUND(100 * defect_rate, 2) AS defective_unit_pct
FROM supplier_metrics ORDER BY late_rate DESC;

-- 2. Spend and cost variance by category.
SELECT category, ROUND(SUM(actual_spend), 2) AS actual_spend,
       ROUND(SUM(contracted_spend), 2) AS contracted_spend,
       ROUND(100.0 * (SUM(actual_spend) - SUM(contracted_spend)) /
             SUM(contracted_spend), 2) AS variance_pct
FROM supplier_metrics GROUP BY category ORDER BY actual_spend DESC;

-- 3. Share of spend in each supplier's product category.
SELECT supplier_name, category, ROUND(actual_spend, 2) AS actual_spend,
       ROUND(100.0 * actual_spend / SUM(actual_spend) OVER (PARTITION BY category), 1)
           AS category_spend_share_pct
FROM supplier_metrics ORDER BY category, category_spend_share_pct DESC;
