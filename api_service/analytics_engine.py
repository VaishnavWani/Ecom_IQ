import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from statistics import mean
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("EcomIQ-AnalyticsEngine")


# ──────────────────────────────────────────────
# MODEL: Database connection
# ──────────────────────────────────────────────

class Database:
    """Handles all raw SQL queries against the EcomIQ PostgreSQL database."""

    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "ecommerce_iq_db"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
        )
        self.conn.autocommit = False
        logger.info("Analytics Engine connected to PostgreSQL")

    def query(self, sql: str, params=None) -> list[dict]:
        """Execute a SELECT query and return rows as list of dicts."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params or [])
                rows = cur.fetchall()
            self.conn.commit()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            self.conn.rollback()
            return []


# ──────────────────────────────────────────────
# MODEL: Scope Filter Builder
# ──────────────────────────────────────────────

class ScopeFilter:
    """
    Builds SQL WHERE clause fragments from a scope dict.

    Scope keys supported:
        region          → filters on dim_regions.region_name  (alias: dr)
        courier_name    → filters on fact_shipments.courier_name
        payment_status  → filters on fact_payments.payment_status
        payment_method  → filters on dim_payment_methods.method_name (alias: dm)
        device_type     → filters on fact_user_clickstream.device_type
        return_reason   → filters on fact_returns.return_reason
        category        → filters on dim_categories.category_name (alias: dc)
        city            → filters on dim_customer_addresses.city (alias: dca)
        sku_id          → filters on the sku_id column in the relevant table
    """

    # Maps scope key → (sql_column_expression, value_transform)
    DIRECT_FILTERS = {
        "courier_name":   "fs.courier_name",
        "payment_status": "fp.payment_status",
        "device_type":    "fuc.device_type",
        "return_reason":  "fr.return_reason",
    }

    JOIN_FILTERS = {
        "region":          "dr.region_name",
        "payment_method":  "dm.method_name",
        "category":        "dc.category_name",
        "city":            "dca.city",
    }

    @staticmethod
    def build(scope: dict, allowed_keys: list[str]) -> tuple[str, list]:
        """
        Returns (where_clause_str, params_list) for the given scope keys.
        Only applies filters whose keys are in `allowed_keys`.

        Example:
            scope = {"region": "West India", "courier_name": "Delhivery"}
            allowed_keys = ["region", "courier_name"]
            → ("WHERE dr.region_name = %s AND fs.courier_name = %s", ["West India", "Delhivery"])
        """
        all_filters = {**ScopeFilter.DIRECT_FILTERS, **ScopeFilter.JOIN_FILTERS}
        conditions = []
        params = []

        for key in allowed_keys:
            if key in scope and key in all_filters:
                col = all_filters[key]
                conditions.append(f"{col} = %s")
                params.append(scope[key])

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        return where, params


# ──────────────────────────────────────────────
# MODEL: Signal Detector
# ──────────────────────────────────────────────

class SignalDetector:
    """Detects anomalies in a dict of {label: numeric_value} data."""

    @staticmethod
    def detect(data: dict) -> list[dict]:
        if not data or len(data) < 2:
            return []
        values = list(data.values())
        avg = mean(values)
        if avg == 0:
            return []
        signals = []
        for label, val in data.items():
            if val > avg * 1.5:
                signals.append({
                    "dimension": label,
                    "value": val,
                    "avg": round(avg, 2),
                    "severity": "HIGH" if val > avg * 2 else "MEDIUM",
                    "type": "spike"
                })
            elif val < avg * 0.5:
                signals.append({
                    "dimension": label,
                    "value": val,
                    "avg": round(avg, 2),
                    "severity": "MEDIUM",
                    "type": "drop"
                })
        return signals


# ──────────────────────────────────────────────
# CONTROLLER: Individual Analysis Functions
# ──────────────────────────────────────────────

class AnalysisController:
    """Runs SQL analytics queries. Every method accepts a scope dict for filtering."""

    def __init__(self, db: Database):
        self.db = db
        self.detector = SignalDetector()

    # ── 1. Payment Analysis ───────────────────────────────────────────────

    def payment_failure_by_method(self, scope: dict) -> dict:
        """Payment failure rate by method. Filterable by: payment_status, region, city."""
        # Build region/city join if needed
        region_join = ""
        where, params = ScopeFilter.build(scope, ["payment_status", "payment_method"])

        # If region/city scope exists, join through orders → customers → addresses
        extra_conditions = []
        if "region" in scope or "city" in scope:
            region_join = """
                JOIN fact_order_headers foh ON fp.order_id = foh.order_id
                JOIN dim_customers dc2 ON foh.customer_id = dc2.customer_id
                JOIN dim_customer_addresses dca ON dc2.address_id = dca.address_id
                JOIN dim_regions dr ON dca.region_id = dr.region_id
            """
            if "region" in scope:
                extra_conditions.append("dr.region_name = %s")
                params.append(scope["region"])
            if "city" in scope:
                extra_conditions.append("dca.city = %s")
                params.append(scope["city"])

        if extra_conditions:
            where = (where + " AND " if where else "WHERE ") + " AND ".join(extra_conditions)

        rows = self.db.query(f"""
            SELECT
                dm.method_name,
                COUNT(*) AS total,
                SUM(CASE WHEN fp.payment_status = 'failed' THEN 1 ELSE 0 END) AS failed,
                ROUND(
                    100.0 * SUM(CASE WHEN fp.payment_status = 'failed' THEN 1 ELSE 0 END)
                    / NULLIF(COUNT(*), 0), 2
                ) AS failure_rate_pct
            FROM fact_payments fp
            JOIN dim_payment_methods dm ON fp.method_id = dm.method_id
            {region_join}
            {where}
            GROUP BY dm.method_name
            ORDER BY failure_rate_pct DESC
        """, params)
        breakdown = {r["method_name"]: float(r["failure_rate_pct"] or 0) for r in rows}
        return {"breakdown": rows, "signals": self.detector.detect(breakdown)}

    def payment_failure_by_reason(self, scope: dict) -> dict:
        """Payment failure reasons. Filterable by: payment_method, region."""
        where, params = ScopeFilter.build(scope, ["payment_status"])

        extra_join = ""
        extra_cond = []
        if "payment_method" in scope:
            extra_join = "JOIN dim_payment_methods dm ON fp.method_id = dm.method_id"
            extra_cond.append("dm.method_name = %s")
            params.append(scope["payment_method"])
        if "region" in scope:
            extra_join += """
                JOIN fact_order_headers foh ON fp.order_id = foh.order_id
                JOIN dim_customers dc2 ON foh.customer_id = dc2.customer_id
                JOIN dim_customer_addresses dca ON dc2.address_id = dca.address_id
                JOIN dim_regions dr ON dca.region_id = dr.region_id
            """
            extra_cond.append("dr.region_name = %s")
            params.append(scope["region"])

        base_where = "WHERE fp.payment_status = 'failed' AND fp.failure_reason IS NOT NULL"
        if extra_cond:
            base_where += " AND " + " AND ".join(extra_cond)

        rows = self.db.query(f"""
            SELECT fp.failure_reason, COUNT(*) AS count
            FROM fact_payments fp
            {extra_join}
            {base_where}
            GROUP BY fp.failure_reason
            ORDER BY count DESC
        """, params)
        breakdown = {r["failure_reason"]: r["count"] for r in rows}
        return {"breakdown": rows, "signals": self.detector.detect(breakdown)}

    # ── 2. Order / Revenue Analysis ───────────────────────────────────────

    def orders_by_region(self, scope: dict) -> dict:
        """Order count and revenue per region. Filterable by: region, city, category."""
        extra_cond = []
        params = []
        extra_join = ""

        if "region" in scope:
            extra_cond.append("dr.region_name = %s")
            params.append(scope["region"])
        if "city" in scope:
            extra_cond.append("dca.city = %s")
            params.append(scope["city"])
        if "category" in scope:
            extra_join = """
                JOIN fact_order_lines fol ON foh.order_id = fol.order_id
                JOIN dim_skus ds ON fol.sku_id = ds.sku_id
                JOIN dim_categories dcat ON ds.category_id = dcat.category_id
            """
            extra_cond.append("dcat.category_name = %s")
            params.append(scope["category"])

        where = ("WHERE " + " AND ".join(extra_cond)) if extra_cond else ""

        rows = self.db.query(f"""
            SELECT
                dr.region_name,
                COUNT(DISTINCT foh.order_id) AS order_count,
                ROUND(SUM(foh.total_order_value)::numeric, 2) AS total_revenue
            FROM fact_order_headers foh
            JOIN dim_customers dc ON foh.customer_id = dc.customer_id
            JOIN dim_customer_addresses dca ON dc.address_id = dca.address_id
            JOIN dim_regions dr ON dca.region_id = dr.region_id
            {extra_join}
            {where}
            GROUP BY dr.region_name
            ORDER BY order_count DESC
        """, params)
        breakdown = {r["region_name"]: r["order_count"] for r in rows}
        return {"breakdown": rows, "signals": self.detector.detect(breakdown)}

    def revenue_by_category(self, scope: dict) -> dict:
        """Revenue by category. Filterable by: category, region."""
        extra_cond = []
        params = []
        extra_join = ""

        if "category" in scope:
            extra_cond.append("dc.category_name = %s")
            params.append(scope["category"])
        if "region" in scope:
            extra_join = """
                JOIN fact_order_headers foh2 ON fol.order_id = foh2.order_id
                JOIN dim_customers dc2 ON foh2.customer_id = dc2.customer_id
                JOIN dim_customer_addresses dca ON dc2.address_id = dca.address_id
                JOIN dim_regions dr ON dca.region_id = dr.region_id
            """
            extra_cond.append("dr.region_name = %s")
            params.append(scope["region"])

        where = ("WHERE " + " AND ".join(extra_cond)) if extra_cond else ""

        rows = self.db.query(f"""
            SELECT
                dc.category_name,
                COUNT(DISTINCT fol.order_id) AS order_count,
                ROUND(SUM(fol.line_value)::numeric, 2) AS total_revenue
            FROM fact_order_lines fol
            JOIN dim_skus ds ON fol.sku_id = ds.sku_id
            JOIN dim_categories dc ON ds.category_id = dc.category_id
            {extra_join}
            {where}
            GROUP BY dc.category_name
            ORDER BY total_revenue DESC
        """, params)
        breakdown = {r["category_name"]: float(r["total_revenue"] or 0) for r in rows}
        return {"breakdown": rows, "signals": self.detector.detect(breakdown)}

    # ── 3. Shipment / Courier Analysis ────────────────────────────────────

    def courier_performance(self, scope: dict) -> dict:
        """Courier stats. Filterable by: courier_name, region."""
        extra_cond = []
        params = []
        extra_join = ""

        if "courier_name" in scope:
            extra_cond.append("fs.courier_name = %s")
            params.append(scope["courier_name"])
        if "region" in scope:
            extra_join = """
                JOIN fact_order_headers foh ON fs.order_id = foh.order_id
                JOIN dim_customers dc ON foh.customer_id = dc.customer_id
                JOIN dim_customer_addresses dca ON dc.address_id = dca.address_id
                JOIN dim_regions dr ON dca.region_id = dr.region_id
            """
            extra_cond.append("dr.region_name = %s")
            params.append(scope["region"])

        where = ("WHERE " + " AND ".join(extra_cond)) if extra_cond else ""

        rows = self.db.query(f"""
            SELECT
                fs.courier_name,
                COUNT(*) AS total_shipments,
                SUM(CASE WHEN fs.event_type = 'delivery_failed' THEN 1 ELSE 0 END) AS failed,
                ROUND(
                    100.0 * SUM(CASE WHEN fs.event_type = 'delivery_failed' THEN 1 ELSE 0 END)
                    / NULLIF(COUNT(*), 0), 2
                ) AS failure_rate_pct
            FROM fact_shipments fs
            {extra_join}
            {where}
            GROUP BY fs.courier_name
            ORDER BY total_shipments DESC
        """, params)
        breakdown = {r["courier_name"]: r["total_shipments"] for r in rows}
        return {"breakdown": rows, "signals": self.detector.detect(breakdown)}

    def shipments_by_region(self, scope: dict) -> dict:
        """Shipments by region. Filterable by: region, courier_name."""
        extra_cond = []
        params = []

        if "region" in scope:
            extra_cond.append("dr.region_name = %s")
            params.append(scope["region"])
        if "courier_name" in scope:
            extra_cond.append("fs.courier_name = %s")
            params.append(scope["courier_name"])

        where = ("WHERE " + " AND ".join(extra_cond)) if extra_cond else ""

        rows = self.db.query(f"""
            SELECT
                dr.region_name,
                COUNT(fs.shipment_id) AS shipment_count
            FROM fact_shipments fs
            JOIN fact_order_headers foh ON fs.order_id = foh.order_id
            JOIN dim_customers dc ON foh.customer_id = dc.customer_id
            JOIN dim_customer_addresses dca ON dc.address_id = dca.address_id
            JOIN dim_regions dr ON dca.region_id = dr.region_id
            {where}
            GROUP BY dr.region_name
            ORDER BY shipment_count DESC
        """, params)
        breakdown = {r["region_name"]: r["shipment_count"] for r in rows}
        return {"breakdown": rows, "signals": self.detector.detect(breakdown)}

    # ── 4. Returns Analysis ───────────────────────────────────────────────

    def return_rate_by_sku(self, scope: dict, top_n: int = 10) -> dict:
        """Top SKUs by return count. Filterable by: return_reason, region, category."""
        extra_cond = []
        params = []
        extra_join = ""

        if "return_reason" in scope:
            extra_cond.append("fr.return_reason = %s")
            params.append(scope["return_reason"])
        if "category" in scope:
            extra_join += " JOIN dim_skus ds ON fol.sku_id = ds.sku_id JOIN dim_categories dcat ON ds.category_id = dcat.category_id"
            extra_cond.append("dcat.category_name = %s")
            params.append(scope["category"])
        if "region" in scope:
            extra_join += """
                JOIN fact_order_headers foh ON fol.order_id = foh.order_id
                JOIN dim_customers dc ON foh.customer_id = dc.customer_id
                JOIN dim_customer_addresses dca ON dc.address_id = dca.address_id
                JOIN dim_regions dr ON dca.region_id = dr.region_id
            """
            extra_cond.append("dr.region_name = %s")
            params.append(scope["region"])

        where = ("WHERE " + " AND ".join(extra_cond)) if extra_cond else ""
        params.append(top_n)

        rows = self.db.query(f"""
            SELECT
                fol.sku_id,
                COUNT(fr.return_id) AS return_count,
                COUNT(DISTINCT fol.order_id) AS order_count,
                ROUND(
                    100.0 * COUNT(fr.return_id) / NULLIF(COUNT(DISTINCT fol.order_id), 0), 2
                ) AS return_rate_pct
            FROM fact_order_lines fol
            LEFT JOIN fact_returns fr ON fol.line_id = fr.line_id
            {extra_join}
            {where}
            GROUP BY fol.sku_id
            HAVING COUNT(fr.return_id) > 0
            ORDER BY return_count DESC
            LIMIT %s
        """, params)
        breakdown = {r["sku_id"][:8]: r["return_count"] for r in rows}
        return {"top_n": top_n, "breakdown": rows, "signals": self.detector.detect(breakdown)}

    def return_reasons(self, scope: dict) -> dict:
        """Return reasons count. Filterable by: return_reason, region."""
        extra_cond = []
        params = []
        extra_join = ""

        if "return_reason" in scope:
            extra_cond.append("fr.return_reason = %s")
            params.append(scope["return_reason"])
        if "region" in scope:
            extra_join = """
                JOIN fact_order_lines fol ON fr.line_id = fol.line_id
                JOIN fact_order_headers foh ON fol.order_id = foh.order_id
                JOIN dim_customers dc ON foh.customer_id = dc.customer_id
                JOIN dim_customer_addresses dca ON dc.address_id = dca.address_id
                JOIN dim_regions dr ON dca.region_id = dr.region_id
            """
            extra_cond.append("dr.region_name = %s")
            params.append(scope["region"])

        where = ("WHERE " + " AND ".join(extra_cond)) if extra_cond else ""

        rows = self.db.query(f"""
            SELECT fr.return_reason, COUNT(*) AS count
            FROM fact_returns fr
            {extra_join}
            {where}
            GROUP BY fr.return_reason
            ORDER BY count DESC
        """, params)
        breakdown = {r["return_reason"]: r["count"] for r in rows}
        return {"breakdown": rows, "signals": self.detector.detect(breakdown)}

    # ── 5. Inventory Analysis ─────────────────────────────────────────────

    def inventory_by_warehouse(self, scope: dict) -> dict:
        """Inventory per warehouse. Filterable by: region (warehouse's region)."""
        extra_cond = []
        params = []
        extra_join = ""

        if "region" in scope:
            extra_join = "JOIN dim_warehouses dw ON fit.warehouse_id = dw.warehouse_id JOIN dim_regions dr ON dw.region_id = dr.region_id"
            extra_cond.append("dr.region_name = %s")
            params.append(scope["region"])

        where = ("WHERE " + " AND ".join(extra_cond)) if extra_cond else ""

        rows = self.db.query(f"""
            SELECT
                fit.warehouse_id,
                SUM(CASE WHEN fit.event_type = 'stock_added' THEN fit.quantity_change ELSE 0 END) AS stock_in,
                SUM(CASE WHEN fit.event_type != 'stock_added' THEN fit.quantity_change ELSE 0 END) AS stock_out,
                SUM(fit.quantity_change) AS net_change,
                COUNT(*) AS total_events
            FROM fact_inventory_transactions fit
            {extra_join}
            {where}
            GROUP BY fit.warehouse_id
            ORDER BY net_change ASC
        """, params)
        breakdown = {r["warehouse_id"][:8]: r["net_change"] for r in rows}
        return {"breakdown": rows, "signals": self.detector.detect(breakdown)}

    # ── 6. Clickstream Analysis ───────────────────────────────────────────

    def clickstream_by_device(self, scope: dict) -> dict:
        """Events by device type. Filterable by: device_type, region."""
        extra_cond = []
        params = []
        extra_join = ""

        if "device_type" in scope:
            extra_cond.append("fuc.device_type = %s")
            params.append(scope["device_type"])
        if "region" in scope:
            extra_join = """
                JOIN dim_customers dc ON fuc.customer_id = dc.customer_id
                JOIN dim_customer_addresses dca ON dc.address_id = dca.address_id
                JOIN dim_regions dr ON dca.region_id = dr.region_id
            """
            extra_cond.append("dr.region_name = %s")
            params.append(scope["region"])

        where = ("WHERE " + " AND ".join(extra_cond)) if extra_cond else ""

        rows = self.db.query(f"""
            SELECT fuc.device_type, COUNT(*) AS event_count
            FROM fact_user_clickstream fuc
            {extra_join}
            {where}
            GROUP BY fuc.device_type
            ORDER BY event_count DESC
        """, params)
        breakdown = {r["device_type"]: r["event_count"] for r in rows}
        return {"breakdown": rows, "signals": self.detector.detect(breakdown)}

    def clickstream_funnel(self, scope: dict) -> dict:
        """Event type funnel. Filterable by: device_type, region."""
        extra_cond = []
        params = []
        extra_join = ""

        if "device_type" in scope:
            extra_cond.append("fuc.device_type = %s")
            params.append(scope["device_type"])
        if "region" in scope:
            extra_join = """
                JOIN dim_customers dc ON fuc.customer_id = dc.customer_id
                JOIN dim_customer_addresses dca ON dc.address_id = dca.address_id
                JOIN dim_regions dr ON dca.region_id = dr.region_id
            """
            extra_cond.append("dr.region_name = %s")
            params.append(scope["region"])

        where = ("WHERE " + " AND ".join(extra_cond)) if extra_cond else ""

        rows = self.db.query(f"""
            SELECT fuc.event_type, COUNT(*) AS count
            FROM fact_user_clickstream fuc
            {extra_join}
            {where}
            GROUP BY fuc.event_type
            ORDER BY count DESC
        """, params)
        breakdown = {r["event_type"]: r["count"] for r in rows}
        return {"breakdown": rows, "signals": self.detector.detect(breakdown)}


# ──────────────────────────────────────────────
# CONTROLLER: Investigation Engine (orchestrator)
# ──────────────────────────────────────────────

class InvestigationEngine:
    """
    Top-level orchestrator. Accepts a scope dict and passes it to every
    analysis query so results are genuinely filtered.

    Supported scope keys:
        region          → "West India" | "North India" | "South India" | "East India"
        city            → "Mumbai" | "Delhi" | "Bangalore" | "Chennai" | "Pune" | etc.
        courier_name    → "Delhivery" | "BlueDart" | "EcomExpress" | "DTDC"
        payment_status  → "success" | "failed"
        payment_method  → "UPI" | "Credit Card" | "Debit Card"
        device_type     → "mobile" | "desktop" | "tablet"
        return_reason   → "damaged" | "wrong_item" | "not_needed" | "size_issue"
        category        → "Electronics" | "Apparel" | "Home"
    """

    def __init__(self):
        self.db = Database()
        self.ctrl = AnalysisController(self.db)

    def run(self, scope: dict = None) -> dict:
        scope = scope or {}
        logger.info(f"Running investigation with scope: {scope}")

        return {
            "scope": scope,
            "payments": {
                "by_method": self.ctrl.payment_failure_by_method(scope),
                "by_reason": self.ctrl.payment_failure_by_reason(scope),
            },
            "orders": {
                "by_region": self.ctrl.orders_by_region(scope),
                "by_category": self.ctrl.revenue_by_category(scope),
            },
            "shipments": {
                "courier_performance": self.ctrl.courier_performance(scope),
                "by_region": self.ctrl.shipments_by_region(scope),
            },
            "returns": {
                "top_skus": self.ctrl.return_rate_by_sku(scope),
                "by_reason": self.ctrl.return_reasons(scope),
            },
            "inventory": {
                "by_warehouse": self.ctrl.inventory_by_warehouse(scope),
            },
            "clickstream": {
                "by_device": self.ctrl.clickstream_by_device(scope),
                "funnel": self.ctrl.clickstream_funnel(scope),
            },
        }
