# NEXUS Demo Portal — API Reference Documentation

## Base URL
- Development: `http://localhost:8000/api/v1`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Standard Response Format
All JSON endpoints return a standard envelope:
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... },
  "error": null
}
```

Standard error envelope:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Product with identifier 'xyz' was not found.",
    "details": null
  },
  "request_id": "97fc78cb-4572-4366-a2c6-0f6a92c47568"
}
```

---

## Core Endpoints Summary

### 1. Catalog & Products
- `GET /api/v1/products/categories`: List all categories.
- `GET /api/v1/products`: List paginated products (`?category=slug&search=text&page=1&page_size=12`).
- `GET /api/v1/products/{slug}`: Get product details by slug.

### 2. Authentication & Profile
- `POST /api/v1/auth/register`: Create user account (`email`, `password`, `full_name`).
- `POST /api/v1/auth/login`: Authenticate and receive JWT token (`email`, `password`).
- `POST /api/v1/auth/logout`: End session (Bearer token required).
- `GET /api/v1/auth/me`: Current user profile (Bearer token required).

### 3. Shopping Cart
- `GET /api/v1/cart`: Get cart and computed totals (Header: `X-Session-ID` or `Authorization`).
- `POST /api/v1/cart/items`: Add item (`product_id`, `quantity`).
- `PUT /api/v1/cart/items/{id}`: Modify quantity (`quantity`).
- `DELETE /api/v1/cart/items/{id}`: Remove item.
- `DELETE /api/v1/cart`: Clear cart.

### 4. Orders & Checkout
- `POST /api/v1/orders/checkout`: Convert cart to confirmed order (`shipping_address`, `payment_method`).
- `GET /api/v1/orders`: List order history.
- `GET /api/v1/orders/{order_number}`: Get detailed receipt.

### 5. Health & Diagnostics
- `GET /api/v1/health`: Truthful component health check (API + DB).
- `GET /api/v1/health/live`: Liveness check.
- `GET /api/v1/health/ready`: Database readiness check.

### 6. Observability
- `GET /metrics`: Prometheus plaintext format scraping.
- `GET /api/v1/metrics`: Complete application and system telemetry JSON.
- `GET /api/v1/metrics/system`: Host resource metrics (CPU, RAM, Disk, Uptime).
- `GET /api/v1/metrics/events`: Recent structured application audit events.

### 7. Failure Simulator (Authorized Test Environments)
- `GET /api/v1/simulator/status`: Current active status of all 6 scenarios.
- `POST /api/v1/simulator/scenarios/{name}/activate`: Activate scenario with duration.
- `POST /api/v1/simulator/scenarios/{name}/deactivate`: Deactivate scenario.
- `POST /api/v1/simulator/reset`: Emergency stop for all scenarios.
