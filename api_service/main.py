import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

from dotenv import load_dotenv
from analytics_engine import InvestigationEngine
from agents.supervisor_agent import SupervisorAgent

load_dotenv()

app = FastAPI(
    title="EcomIQ API",
    description="EcomIQ Operational Intelligence API — data pipeline + AI investigation layer",
    version="2.0.0"
)

# Allow the local frontend (file://) and any dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared analytics engine instance (initialized once on startup)
_engine: Optional[InvestigationEngine] = None

def get_engine() -> InvestigationEngine:
    global _engine
    if _engine is None:
        _engine = InvestigationEngine()
    return _engine


class InvestigateRequest(BaseModel):
    scope: dict = {}


class InvestigationQuery(BaseModel):
    query: str
    include_raw_data: bool = False   # set True to also return SQL data alongside the report


# Shared supervisor instance
_supervisor: Optional[SupervisorAgent] = None

def get_supervisor() -> SupervisorAgent:
    global _supervisor
    if _supervisor is None:
        _supervisor = SupervisorAgent()
    return _supervisor

DB_HOST = os.getenv("DB_HOST", "ecommerce_iq_db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


@app.get("/")
def health_check():
    return {"status": "ok", "message": "EcomIQ API is running"}


@app.get("/orders")
def list_orders(limit: int = 20):
    if limit > 100:
        limit = 100
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM fact_order_headers ORDER BY event_timestamp DESC LIMIT %s",
                (limit,)
            )
            rows = cur.fetchall()
        conn.close()
        return {"count": len(rows), "orders": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/truncate-all")
def truncate_all_tables():
    tables = [
        "fact_user_clickstream",
        "fact_inventory_transactions",
        "fact_returns",
        "fact_shipments",
        "fact_payments",
        "fact_order_lines",
        "fact_order_headers",
        "dim_customers",
        "dim_customer_addresses",
        "dim_payment_methods",
        "dim_warehouses",
        "dim_skus",
        "dim_categories",
        "dim_regions",
    ]
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE")
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"Truncated {len(tables)} tables successfully", "tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# Analytics Engine Endpoints
# ─────────────────────────────────────────────────────────────────

@app.get("/analytics/full")
def analytics_full():
    """
    Runs a full investigation across ALL 14 tables.
    Returns signals, breakdowns, and KPIs for every operational area.
    No AI — pure SQL results. Use /investigate for AI-interpreted insights.
    """
    try:
        engine = get_engine()
        report = engine.run(scope={})
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analytics/investigate")
def analytics_investigate(body: InvestigateRequest):
    """
    Runs a scoped investigation. Pass a scope dict to narrow the analysis.

    Example scopes:
        {}                                → full investigation
        {"region": "West India"}          → (future: filter by region)
        {"courier_name": "Delhivery"}     → (future: filter by courier)
        {"payment_status": "failed"}      → (future: filter by payment status)

    Currently returns full SQL analytics report.
    AI interpretation will be added in Phase 3 (/investigate endpoint).
    """
    try:
        engine = get_engine()
        report = engine.run(scope=body.scope)
        return {"scope": body.scope, "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# AI Investigation Endpoint  (Phase 3)
# ─────────────────────────────────────────────────────────────────

@app.post("/investigate")
def investigate(body: InvestigationQuery):
    """
    🤖 AI-Powered Operational Investigation

    Ask any natural language question about your e-commerce operations.
    The system will:
      1. Extract investigation scope from your question (Fetcher Agent)
      2. Run SQL analytics on the relevant tables (Analytics Engine)
      3. Generate an AI investigation report (Runner Agent)

    Example queries:
      - "Why is Delhivery performing poorly in West India?"
      - "Why are payments failing?"
      - "Which SKUs have the most returns?"
      - "How are mobile users behaving vs desktop?"
      - "What is the revenue breakdown by region?"
    """
    try:
        supervisor = get_supervisor()
        result = supervisor.investigate(user_query=body.query)

        response = {
            "query": result["query"],
            "scope_extracted": result["scope"],
            "report": result["report"],
        }

        if body.include_raw_data:
            response["raw_analytics"] = result["analytics"]

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))