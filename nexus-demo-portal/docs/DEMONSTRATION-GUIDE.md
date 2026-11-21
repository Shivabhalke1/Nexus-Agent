# NEXUS Demo Portal — Hackathon Demonstration Guide (CICADA 2026)

This guide provides a structured 5-minute live demonstration script for hackathon judges and evaluators, highlighting normal e-commerce workloads, live observability telemetry, and all 6 controlled failure scenarios.

---

## Part 1 — Normal E-Commerce Workload (2 Minutes)

1. **Open the Homepage**:
   - Navigate to [http://localhost:3000](http://localhost:3000).
   - Show the clean product catalog, hero section, and category previews.
2. **Product Browsing & Search**:
   - Click **Catalog** ([http://localhost:3000/products](http://localhost:3000/products)).
   - Filter by **Electronics & Audio** tab.
   - Type `"Wireless"` in the search bar. Real-time filtering updates the grid.
3. **Product Details & Cart**:
   - Click on the **AeroPulse Wireless ANC Headphones**.
   - Show stock status (`In Stock (45 units)`) and SKU.
   - Select quantity `2` and click **Add to Cart**.
   - Notice the cart icon in the navbar updates its count badge to `2`.
4. **Simulated Checkout**:
   - Click the cart icon or visit [http://localhost:3000/cart](http://localhost:3000/cart).
   - Review order breakdown (Subtotal, Free Express Shipping, Total).
   - Click **Proceed to Checkout** ([http://localhost:3000/checkout](http://localhost:3000/checkout)).
   - Click **Place Simulated Order**.
   - Show the generated confirmation page with receipt number (e.g. `NEXUS-20261120-XXXX`) and order summary.
5. **Order History**:
   - Click **My Orders** in the navbar ([http://localhost:3000/orders](http://localhost:3000/orders)) to display recorded customer orders.

---

## Part 2 — Observability & Telemetry Inspection (1.5 Minutes)

1. **Component Health Probes**:
   - Open [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) in a browser or terminal:
   ```bash
   curl -s http://localhost:8000/api/v1/health | jq .
   ```
   - Highlight component-level visibility: API status and live database ping latency.
2. **Prometheus Scraping Endpoint**:
   - Open [http://localhost:8000/metrics](http://localhost:8000/metrics):
   ```bash
   curl -s http://localhost:8000/metrics | grep nexus_
   ```
   - Show `nexus_requests_total`, `nexus_response_time_avg_ms`, `nexus_system_cpu_percent`, and status code breakdown.
3. **Structured JSON Telemetry**:
   - Open [http://localhost:8000/api/v1/metrics](http://localhost:8000/api/v1/metrics):
   - Highlight the real-time request breakdown by endpoint, latency distribution buckets, and host metrics (`psutil`).
4. **Audit Event Log Stream**:
   - Open [http://localhost:8000/api/v1/metrics/events](http://localhost:8000/api/v1/metrics/events):
   - Show structured records for `USER_REGISTERED`, `CART_ITEM_ADDED`, and `ORDER_CREATED` with unique correlation IDs (`X-Request-ID`).

---

## Part 3 — Controlled Failure Simulator Demonstration (1.5 Minutes)

1. **Access the Developer Control Panel**:
   - Navigate to [http://localhost:3000/simulator](http://localhost:3000/simulator).
   - Show all 6 scenario cards with live status badges.
2. **Scenario 2 — Slow API Response**:
   - Click **Activate** on *Scenario 2 (Slow API Response)*.
   - Badge turns yellow with an active countdown timer.
   - Refresh the Product Catalog ([http://localhost:3000/products](http://localhost:3000/products)).
   - Observe the 1500ms latency. Inspect network tab to verify `X-Response-Time-Ms: 1512ms`.
   - Click **Deactivate Scenario**. Catalog returns immediately to sub-20ms speed.
3. **Scenario 4 — Database Connection Failure**:
   - Click **Activate** on *Scenario 4 (Database Connection Failure)*.
   - Check the health endpoint: `curl -s http://localhost:8000/api/v1/health`.
   - Observe `HTTP 503 DATABASE_UNAVAILABLE`.
   - Click the top right **Reset All Scenarios** emergency button.
   - Observe immediate recovery; health returns to `HTTP 200 OK` with zero data corruption.
4. **Scenario 6 — Repeated Failed Login Stress**:
   - Click **Activate** on *Scenario 6 (Repeated Failed Logins)*.
   - Check the event stream ([http://localhost:8000/api/v1/metrics/events](http://localhost:8000/api/v1/metrics/events)).
   - Notice the burst of `AUTH_LOGIN_FAILED` warning events with synthetic account domains, demonstrating realistic telemetry generation for security alerting in the Local Collector.
