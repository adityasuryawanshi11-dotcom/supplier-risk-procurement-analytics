PRAGMA foreign_keys = ON;
CREATE TABLE suppliers (
    supplier_id TEXT PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    category TEXT NOT NULL,
    region TEXT NOT NULL,
    geo_exposure REAL NOT NULL CHECK (geo_exposure BETWEEN 0 AND 100)
);
CREATE TABLE purchase_orders (
    po_id TEXT PRIMARY KEY,
    supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
    order_date TEXT NOT NULL,
    promised_date TEXT NOT NULL,
    delivery_date TEXT NOT NULL,
    item TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    defect_units INTEGER NOT NULL CHECK (defect_units BETWEEN 0 AND quantity),
    contracted_unit_price REAL NOT NULL CHECK (contracted_unit_price > 0),
    actual_unit_price REAL NOT NULL CHECK (actual_unit_price > 0)
);
CREATE INDEX idx_po_supplier ON purchase_orders(supplier_id);

-- The dashboard executes this SQL view. Denominators are summed before division.
CREATE VIEW supplier_metrics AS
SELECT s.supplier_id, s.supplier_name, s.category, s.region, s.geo_exposure,
       COUNT(p.po_id) AS po_count,
       SUM(p.quantity) AS units,
       SUM(p.defect_units) AS defect_units,
       SUM(CASE WHEN p.delivery_date > p.promised_date THEN 1 ELSE 0 END) AS late_orders,
       SUM(p.quantity * p.actual_unit_price) AS actual_spend,
       SUM(p.quantity * p.contracted_unit_price) AS contracted_spend,
       1.0 * SUM(CASE WHEN p.delivery_date > p.promised_date THEN 1 ELSE 0 END) / COUNT(p.po_id) AS late_rate,
       1.0 * SUM(p.defect_units) / SUM(p.quantity) AS defect_rate,
       (SUM(p.quantity * p.actual_unit_price) - SUM(p.quantity * p.contracted_unit_price)) /
            SUM(p.quantity * p.contracted_unit_price) AS cost_variance_rate
FROM suppliers s JOIN purchase_orders p ON s.supplier_id = p.supplier_id
GROUP BY s.supplier_id, s.supplier_name, s.category, s.region, s.geo_exposure;
