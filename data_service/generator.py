import uuid
import random
import time
from datetime import datetime

class EcomIqDataGenerator:
    def __init__(self, producer):
        self.producer = producer
        
        # 1. Lookups for 7 Dimension Tables
        self.regions_lookup = {
            "R1": {"name": "West India", "country": "India"},
            "R2": {"name": "North India", "country": "India"},
            "R3": {"name": "South India", "country": "India"},
            "R4": {"name": "East India", "country": "India"}
        }
        self.cities = {
            "R1": ["Mumbai", "Pune"],
            "R2": ["Delhi", "Jaipur"],
            "R3": ["Bangalore", "Chennai"],
            "R4": ["Kolkata", "Bhubaneswar"]
        }
        self.categories = ["C1_Electronics", "C2_Apparel", "C3_Home"]
        self.couriers = ["Delhivery", "BlueDart", "EcomExpress", "DTDC"]
        self.payment_methods = ["UPI", "Credit Card", "Debit Card"]
        self.devices = ["mobile", "desktop", "tablet"]

    def uid(self):
        return str(uuid.uuid4())

    # --- Seed 7 Dimension Tables ---
    def seed_dimensions(self):
        """Generates static master records to Kafka."""
        
        # Dim 1: Regions
        self.region_ids = list(self.regions_lookup.keys())
        for rid, info in self.regions_lookup.items():
            self.producer.send("topic_dim_regions", {
                "region_id": rid, "region_name": info["name"], "country": info["country"]
            })

        # Dim 2: Categories
        for cat in self.categories:
            self.producer.send("topic_dim_categories", {
                "category_id": cat, "category_name": cat.split("_")[1]
            })

        # Dim 3: SKUs
        self.sku_ids = [self.uid() for _ in range(50)]
        for sku in self.sku_ids:
            self.producer.send("topic_dim_skus", {
                "sku_id": sku,
                "category_id": random.choice(self.categories),
                "baseline_price": round(random.uniform(200, 5000), 2)
            })

        # Dim 4: Customer Addresses
        self.address_ids = [self.uid() for _ in range(100)]
        for addr in self.address_ids:
            rid = random.choice(self.region_ids)
            self.producer.send("topic_dim_customer_addresses", {
                "address_id": addr,
                "city": random.choice(self.cities[rid]),
                "region_id": rid
            })

        # Dim 5: Customers
        self.customer_ids = [self.uid() for _ in range(80)]
        for cust in self.customer_ids:
            self.producer.send("topic_dim_customers", {
                "customer_id": cust,
                "address_id": random.choice(self.address_ids),
                "registration_date": str(datetime.now())
            })

        # Dim 6: Warehouses
        self.warehouse_ids = [self.uid() for _ in range(5)]
        for wh in self.warehouse_ids:
            self.producer.send("topic_dim_warehouses", {
                "warehouse_id": wh,
                "region_id": random.choice(self.region_ids)
            })

        # Dim 7: Payment Methods
        self.method_ids = [f"PM_{i}" for i in range(len(self.payment_methods))]
        for i, pm in enumerate(self.payment_methods):
            self.producer.send("topic_dim_payment_methods", {
                "method_id": self.method_ids[i], "method_name": pm
            })

        self.producer.flush()

    # --- Generate 7 Fact Events ---
    def generate_order_flow(self):
        """Generates transactional events linked to the dimensions."""
        order_id = self.uid()
        line_id = self.uid()
        cust_id = random.choice(self.customer_ids)
        sku_id = random.choice(self.sku_ids)
        wh_id = random.choice(self.warehouse_ids)
        val = round(random.uniform(300, 4000), 2)
        ts = str(datetime.now())

        # Fact 8: Order Header
        self.producer.send("topic_fact_order_headers", {
            "order_id": order_id, "customer_id": cust_id, "total_order_value": val, "event_timestamp": ts
        })

        # Fact 9: Order Line
        self.producer.send("topic_fact_order_lines", {
            "line_id": line_id, "order_id": order_id, "sku_id": sku_id,
            "warehouse_id": wh_id, "quantity": random.randint(1, 4), "line_value": val
        })

        # Fact 10: Payment
        status = random.choice(["success", "success", "failed"])
        self.producer.send("topic_fact_payments", {
            "payment_id": self.uid(), "order_id": order_id, "method_id": random.choice(self.method_ids),
            "amount": val, "payment_status": status,
            "failure_reason": "gateway_error" if status == "failed" else None, "event_timestamp": ts
        })

        # Fact 11: Shipment
        self.producer.send("topic_fact_shipments", {
            "shipment_id": self.uid(), "order_id": order_id,
            "courier_name": random.choice(self.couriers),
            "event_type": "dispatched", "event_timestamp": ts
        })

        # Fact 12: Returns (Occasional)
        if random.random() < 0.15:
            self.producer.send("topic_fact_returns", {
                "return_id": self.uid(), "line_id": line_id,
                "return_reason": "damaged", "return_status": "return_requested", "event_timestamp": ts
            })

        # Fact 14: User Clickstream (Occasional)
        if random.random() < 0.6:
            self.producer.send("topic_fact_user_clickstream", {
                "event_id": self.uid(), "customer_id": cust_id, "sku_id": sku_id,
                "device_type": random.choice(self.devices), "event_type": "product_view", "event_timestamp": ts
            })

    # Fact 13: Inventory Updates
    def generate_inventory_event(self):
        self.producer.send("topic_fact_inventory_transactions", {
            "transaction_id": self.uid(), "sku_id": random.choice(self.sku_ids),
            "warehouse_id": random.choice(self.warehouse_ids),
            "event_type": "stock_added", "quantity_change": random.randint(10, 50),
            "event_timestamp": str(datetime.now())
        })