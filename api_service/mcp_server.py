"""
EcomIQ MCP Server
=================
Exposes the Analytics Engine as MCP tools so AI agents can call them.

Runs on port 9500 (separate from the FastAPI server on 8000).

Tools exposed:
    - run_full_investigation    → full report across all 14 tables
    - run_scoped_investigation  → filtered report by scope params
    - get_payment_analysis      → payment failures only
    - get_shipment_analysis     → courier / shipment data only
    - get_order_analysis        → orders + revenue only
    - get_return_analysis       → returns only
    - get_inventory_analysis    → inventory only
    - get_clickstream_analysis  → user behaviour only
"""

import uvicorn
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from analytics_engine import InvestigationEngine, AnalysisController, Database

# ── Shared engine instance ────────────────────────────────────────────────────
_engine = None
_ctrl = None

def get_engine() -> InvestigationEngine:
    global _engine
    if _engine is None:
        _engine = InvestigationEngine()
    return _engine

def get_ctrl() -> AnalysisController:
    global _ctrl
    if _ctrl is None:
        db = Database()
        _ctrl = AnalysisController(db)
    return _ctrl


# ── MCP Server setup ──────────────────────────────────────────────────────────
mcp = FastMCP("EcomIQ_Analytics_MCP")


# ── Tool 1: Full investigation ────────────────────────────────────────────────
@mcp.tool()
def run_full_investigation() -> dict:
    """
    Runs a complete investigation across ALL 14 EcomIQ tables (7 dim + 7 fact).
    Returns payments, orders, shipments, returns, inventory, and clickstream analysis.
    Use this when the user asks a general question with no specific filter.
    """
    engine = get_engine()
    return engine.run(scope={})


# ── Tool 2: Scoped investigation ──────────────────────────────────────────────
@mcp.tool()
def run_scoped_investigation(scope: dict) -> dict:
    """
    Runs an investigation filtered by the given scope.

    Scope keys you can use:
        region         - "West India" | "North India" | "South India" | "East India"
        city           - "Mumbai" | "Delhi" | "Bangalore" | "Chennai" | "Pune"
        courier_name   - "Delhivery" | "BlueDart" | "EcomExpress" | "DTDC"
        payment_status - "success" | "failed"
        payment_method - "UPI" | "Credit Card" | "Debit Card"
        device_type    - "mobile" | "desktop" | "tablet"
        return_reason  - "damaged" | "wrong_item" | "not_needed" | "size_issue"
        category       - "Electronics" | "Apparel" | "Home"

    Example: {"region": "West India", "courier_name": "Delhivery"}
    """
    engine = get_engine()
    return engine.run(scope=scope)


# ── Tool 3: Payment analysis ──────────────────────────────────────────────────
@mcp.tool()
def get_payment_analysis(scope: dict = {}) -> dict:
    """
    Returns payment failure rates by method and failure reason breakdown.
    Use when the user asks about payment issues, failures, or UPI/card problems.

    Optional scope: {"region": "West India"} or {"payment_method": "UPI"}
    """
    ctrl = get_ctrl()
    return {
        "by_method": ctrl.payment_failure_by_method(scope),
        "by_reason": ctrl.payment_failure_by_reason(scope),
    }


# ── Tool 4: Shipment / Courier analysis ──────────────────────────────────────
@mcp.tool()
def get_shipment_analysis(scope: dict = {}) -> dict:
    """
    Returns courier performance stats and shipment volume by region.
    Use when the user asks about deliveries, couriers, or logistics problems.

    Optional scope: {"courier_name": "Delhivery"} or {"region": "West India"}
    """
    ctrl = get_ctrl()
    return {
        "courier_performance": ctrl.courier_performance(scope),
        "by_region": ctrl.shipments_by_region(scope),
    }


# ── Tool 5: Order / Revenue analysis ─────────────────────────────────────────
@mcp.tool()
def get_order_analysis(scope: dict = {}) -> dict:
    """
    Returns order counts and revenue by region and category.
    Use when the user asks about sales performance, revenue, or order trends.

    Optional scope: {"region": "North India"} or {"category": "Electronics"}
    """
    ctrl = get_ctrl()
    return {
        "by_region": ctrl.orders_by_region(scope),
        "by_category": ctrl.revenue_by_category(scope),
    }


# ── Tool 6: Returns analysis ──────────────────────────────────────────────────
@mcp.tool()
def get_return_analysis(scope: dict = {}) -> dict:
    """
    Returns top returned SKUs and return reason breakdown.
    Use when the user asks about product returns, defective items, or return rates.

    Optional scope: {"return_reason": "damaged"} or {"region": "South India"}
    """
    ctrl = get_ctrl()
    return {
        "top_skus": ctrl.return_rate_by_sku(scope),
        "by_reason": ctrl.return_reasons(scope),
    }


# ── Tool 7: Inventory analysis ────────────────────────────────────────────────
@mcp.tool()
def get_inventory_analysis(scope: dict = {}) -> dict:
    """
    Returns inventory levels and stock movement per warehouse.
    Use when the user asks about stock levels, stockouts, or warehouse health.

    Optional scope: {"region": "East India"}
    """
    ctrl = get_ctrl()
    return {
        "by_warehouse": ctrl.inventory_by_warehouse(scope),
    }


# ── Tool 8: Clickstream / User behaviour analysis ─────────────────────────────
@mcp.tool()
def get_clickstream_analysis(scope: dict = {}) -> dict:
    """
    Returns user behaviour breakdown by device type and event funnel.
    Use when the user asks about mobile vs desktop, checkout drop-offs, or user behaviour.

    Optional scope: {"device_type": "mobile"} or {"region": "West India"}
    """
    ctrl = get_ctrl()
    return {
        "by_device": ctrl.clickstream_by_device(scope),
        "funnel": ctrl.clickstream_funnel(scope),
    }


# ── CORS middleware (so agents on other ports can call this) ──────────────────
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

# Build the ASGI app (used by docker/uvicorn)
http_app = mcp.http_app(middleware=middleware)


if __name__ == "__main__":
    uvicorn.run(http_app, host="0.0.0.0", port=9500)
