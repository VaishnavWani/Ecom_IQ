# EcomIQ
### Real-Time Operational Intelligence for E-Commerce Fulfillment

---

## The Problem

E-commerce operations run on data that lives in silos — orders, payments, shipments, returns, and inventory sit in separate systems that don't talk to each other. When something breaks (a courier mishandling a product category, a payment gateway degrading, a supplier shipping defective batches), nobody notices until the damage has compounded for days.

**The cost isn't the failure itself — it's the time between when it starts and when someone finds out.**

---

## The Solution

EcomIQ is a real-time data pipeline that streams every operational event — orders, payments, shipments, returns, inventory, and customer clickstream — into one unified, queryable model. It replaces manual, cross-system spreadsheet investigation with a single query.

**Architecture:** Kafka → Spark Structured Streaming → PostgreSQL (star schema) → REST API

- **7 fact streams**: orders, order lines, payments, shipments, returns, inventory transactions, clickstream
- **7 dimension tables**: regions, categories, SKUs, customers, addresses, warehouses, payment methods
- Fully containerized (Docker), queryable via API, ready for BI tools (Power BI)

---

## Who Needs This

| User | Their Problem |
|---|---|
| **3PL / Warehouse Operators** | Managing multiple clients' SKUs across regions — need to isolate whether a failure is courier-side, warehouse-side, or product-side |
| **D2C Brands (self-fulfilled)** | Need to catch payment fraud spikes or gateway degradation before losses compound |
| **Marketplace Operators** | Need root-cause tracing across seller, SKU, and region to know who's responsible |

---

## Case Study: Tracing a Regional Courier Failure

**The scenario:** A courier begins mishandling electronics shipments in one region, driving up damaged-goods returns.

### Before EcomIQ
1. Ops "feels like" returns are up this week
2. Analyst exports CSVs from WMS, payment processor, and shipment tracker separately
3. Manually joins them in Excel by order ID and timestamp — takes **3-4 hours**
4. Root cause identified after **~5 days** of the courier continuing to ship the same broken way
5. Estimated cost: 5 days × daily order volume × return/refund rate — losses that compound daily

### After EcomIQ
1. A single query joins `fact_returns` → `fact_order_lines` → `fact_shipments`, filtered by region and courier
2. Spike surfaces **within minutes** of the underlying event starting, not days later
3. Ops reroutes the courier for that category **same-day**
4. Detection lag: **days → minutes**

---

## What Exists Today

✅ End-to-end streaming pipeline (Kafka, Spark, Postgres) — tested and verified
✅ Fully dockerized — one-command startup across all services
✅ REST API layer for querying operational data
✅ Star-schema data model supporting cross-domain root-cause queries (region × courier × SKU × payment status)

---

## The Core Value

**EcomIQ doesn't predict the future — it closes the gap between when a problem starts and when someone notices.** That gap, not the failure itself, is where revenue quietly disappears.
