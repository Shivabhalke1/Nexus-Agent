# NEXUS Demo Portal — Database Schema Specification

## 1. Overview
The database layer is built on PostgreSQL with SQLAlchemy 2.0 ORM and managed through Alembic migrations.

## 2. Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ ORDERS : places
    USERS ||--o| CARTS : owns
    CATEGORIES ||--o{ PRODUCTS : contains
    CARTS ||--o{ CART_ITEMS : holds
    PRODUCTS ||--o{ CART_ITEMS : referenced_in
    ORDERS ||--o{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : purchased_in

    USERS {
        int id PK
        string email UK
        string hashed_password
        string full_name
        string role
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    CATEGORIES {
        int id PK
        string name UK
        string slug UK
        text description
        string image_url
        timestamp created_at
        timestamp updated_at
    }

    PRODUCTS {
        int id PK
        int category_id FK
        string name
        string slug UK
        string sku UK
        text description
        decimal price
        int stock
        string image_url
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    CARTS {
        int id PK
        int user_id FK
        string session_id UK
        timestamp created_at
        timestamp updated_at
    }

    CART_ITEMS {
        int id PK
        int cart_id FK
        int product_id FK
        int quantity
        decimal unit_price
        timestamp created_at
        timestamp updated_at
    }

    ORDERS {
        int id PK
        string order_number UK
        int user_id FK
        decimal total_amount
        string status
        text shipping_address
        string payment_method
        timestamp created_at
        timestamp updated_at
    }

    ORDER_ITEMS {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal unit_price
        decimal subtotal
        timestamp created_at
        timestamp updated_at
    }

    APPLICATION_EVENTS {
        int id PK
        string event_type
        string request_id
        string severity
        text payload
        timestamp timestamp
        timestamp created_at
        timestamp updated_at
    }
```

## 3. Data Integrity & Safety Constraints
- **SKU & Slug Uniqueness**: Products and categories enforce unique slugs and SKUs for SEO-friendly routing and catalog integrity.
- **Cascading Deletes**: User removal cascades to their cart, while orders and order items remain historical records with `RESTRICT` on product deletion.
- **Non-destructive Failure Testing**: Controlled database fault injection scenarios test connectivity refusal without dropping or altering production tables.
