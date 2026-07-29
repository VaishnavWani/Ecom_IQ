-- Dimension tables
CREATE TABLE dim_regions (
    region_id      VARCHAR(50),
    region_name    VARCHAR(100),
    country        VARCHAR(100)
);

CREATE TABLE dim_categories (
    category_id    VARCHAR(50),
    category_name  VARCHAR(100)
);

CREATE TABLE dim_skus (
    sku_id          VARCHAR(50),
    category_id     VARCHAR(50),
    baseline_price  DOUBLE PRECISION
);

CREATE TABLE dim_customer_addresses (
    address_id  VARCHAR(50),
    city        VARCHAR(100),
    region_id   VARCHAR(50)
);

CREATE TABLE dim_customers (
    customer_id         VARCHAR(50),
    address_id          VARCHAR(50),
    registration_date   VARCHAR(50)
);

CREATE TABLE dim_warehouses (
    warehouse_id  VARCHAR(50),
    region_id     VARCHAR(50)
);

CREATE TABLE dim_payment_methods (
    method_id    VARCHAR(50),
    method_name  VARCHAR(100)
);

-- Fact tables
CREATE TABLE fact_order_headers (
    order_id           VARCHAR(50),
    customer_id        VARCHAR(50),
    total_order_value  DOUBLE PRECISION,
    event_timestamp    VARCHAR(50)
);

CREATE TABLE fact_order_lines (
    line_id       VARCHAR(50),
    order_id      VARCHAR(50),
    sku_id        VARCHAR(50),
    warehouse_id  VARCHAR(50),
    quantity      INTEGER,
    line_value    DOUBLE PRECISION
);

CREATE TABLE fact_payments (
    payment_id       VARCHAR(50),
    order_id         VARCHAR(50),
    method_id        VARCHAR(50),
    amount           DOUBLE PRECISION,
    payment_status   VARCHAR(50),
    failure_reason   VARCHAR(100),
    event_timestamp  VARCHAR(50)
);

CREATE TABLE fact_shipments (
    shipment_id      VARCHAR(50),
    order_id         VARCHAR(50),
    courier_name     VARCHAR(100),
    event_type       VARCHAR(50),
    event_timestamp  VARCHAR(50)
);

CREATE TABLE fact_returns (
    return_id        VARCHAR(50),
    line_id          VARCHAR(50),
    return_reason    VARCHAR(100),
    return_status    VARCHAR(50),
    event_timestamp  VARCHAR(50)
);

CREATE TABLE fact_inventory_transactions (
    transaction_id    VARCHAR(50),
    sku_id            VARCHAR(50),
    warehouse_id      VARCHAR(50),
    event_type        VARCHAR(50),
    quantity_change   INTEGER,
    event_timestamp   VARCHAR(50)
);

CREATE TABLE fact_user_clickstream (
    event_id      VARCHAR(50),
    customer_id   VARCHAR(50),
    sku_id        VARCHAR(50),
    device_type   VARCHAR(50),
    event_type    VARCHAR(50),
    event_timestamp  VARCHAR(50)
);