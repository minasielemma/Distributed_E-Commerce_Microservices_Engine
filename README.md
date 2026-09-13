# E-Commerce Microservices Platform

A enterprise-grade, event-driven multi-tenant e-commerce microservices platform built with **Python/Django REST Framework**, **Next.js**, **Kafka**, **gRPC**, **PostgreSQL**, **Redis**, and **Neo4j**.

---

## 🏛️ Architecture Overview

The system is designed following modern microservices standards, prioritizing database isolation, event-driven saga orchestration, transactional outbox patterns, and high-concurrency resilience.

```
                         ┌───────────────────────────┐
                         │   Storefront Site / UI    │
                         │      (Next.js App)        │
                         └─────────────┬─────────────┘
                                       │ HTTP / REST
                                       ▼
                         ┌───────────────────────────┐
                         │     NGINX API Gateway     │
                         │        (Port 80)          │
                         └─────────────┬─────────────┘
                                       │
      ┌────────────────────┬───────────┼───────────┬────────────────────┐
      ▼                    ▼           ▼           ▼                    ▼
┌──────────────┐   ┌──────────────┐ ┌─────┐ ┌──────────────┐   ┌──────────────┐
│  Identity    │   │   Catalog    │ │Cart │ │    Order     │   │   Payment    │
│   Service    │   │   Service    │ │Serv │ │   Service    │   │   Service    │
└──────┬───────┘   └──────┬───────┘ └──┬──┘ └──────┬───────┘   └──────┬───────┘
       │                  │            │           │                  │
       ▼                  ▼            ▼           ▼                  ▼
┌──────────────┐   ┌──────────────┐ ┌─────┐ ┌──────────────┐   ┌──────────────┐
│ identity_db  │   │  catalog_db  │ │Redis│ │   order_db   │   │  payment_db  │
└──────────────┘   └──────────────┘ └─────┘ └──────────────┘   └──────────────┘
                                  ▲                       ▲
                                  │ Kafka Events / Saga   │
                                  ▼                       ▼
                           ┌──────────────┐        ┌──────────────┐
                           │   Apache     │        │  Inventory   │
                           │   Kafka      │◄──────►│   Service    │
                           └──────────────┘        └──────────────┘
```

---

## 🧩 Microservices Summary

| Service | Port / Protocol | Database | Description |
| :--- | :--- | :--- | :--- |
| **`gateway`** | `80` (HTTP) | N/A | Reverse proxy & API Gateway routing all external traffic |
| **`storefront_site`** | `3001` (HTTP) | N/A | Customer storefront frontend web application (Next.js) |
| **`admin_portal`** | Internal | N/A | Multi-tenant admin dashboard interface |
| **`identity_service`** | `8000` (REST) | `identity_db` (Postgres) | User authentication, JWT issuance, roles & tenant management |
| **`catalog_service`** | `8000` (REST) / `50051` (gRPC) | `catalog_db` (Postgres) | Products, categories, attributes, and coupon verification |
| **`inventory_service`** | `8000` (REST) / `50052` (gRPC) | `inventory_db` (Postgres) | Multi-warehouse stock tracking, reservations, & movement audit |
| **`cart_service`** | `8000` (REST) | `cart_db` (Postgres) + Redis | Shopping cart management & temporary item storage |
| **`order_service`** | `8000` (REST) | `order_db` (Postgres) | Order lifecycle, sub-orders, outbox events & Saga orchestrator |
| **`payment_service`** | `8000` (REST) | `payment_db` (Postgres) | Checkout sessions, Polar.sh payment provider & webhook handling |
| **`finance_service`** | `8000` (REST) | `finance_db` (Postgres) | Double-entry accounting ledger, journal entries & tenant financial reporting |
| **`notification_service`**| `8000` (REST) | `notification_db` (Postgres) | Email, Webhook, and multi-channel notifications consumer |
| **`media_service`** | `8000` (REST) | `media_db` (Postgres) | Media upload, asset management, and image optimization |
| **`chat_service`** | `8000` (WebSocket) | `chat_db` (Postgres) | Real-time customer support & multi-participant messaging |
| **`recommendation_service`**| `8000` (REST) | Neo4j Graph DB | Graph-based product recommendations & view/like analytics |

---

## ⚡ Key Architectural Patterns

1. **Database-per-Service**: Each microservice strictly owns its Postgres database schema (`identity_db`, `catalog_db`, `order_db`, etc.). Direct cross-service database queries are forbidden.
2. **Saga Pattern (Choreography & Orchestration)**:
   - Order creation triggers `order.created` event -> `inventory_service` reserves stock -> `payment_service` processes payment -> `order_service` confirms order (`PAID`).
   - If payment fails, a compensating event (`inventory.release`) is emitted to restore stock.
   - If inventory reservation fails, a compensating event (`payment.refund`) is emitted to refund payment.
3. **Transactional Outbox Pattern**: Database writes and event publications are wrapped in local DB transactions using `OutboxEvent` tables to guarantee at-least-once delivery to Kafka.
4. **Idempotent Consumers**: Event consumers track processed message IDs using `ProcessedEvent` records to prevent double-processing on duplicate message delivery.
5. **High Concurrency & Row Locking**: `select_for_update()` row-level locks are used during stock reservation and payment checkout to eliminate race conditions and over-booking.

---

## 🚀 Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/) (v2.0+)

### Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

### Running the Infrastructure & Services

Start all microservices and database containers:

```bash
docker compose up -d
```

Check running container status:

```bash
docker compose ps
```

Stop all services:

```bash
docker compose down
```

---

## 🧪 Testing Suite & Resilience Verification

The platform includes unit, integration, and high-concurrency resilience test suites across all 11 microservices (**176 tests** total).

### Run All Tests

Run tests inside running containers using `docker compose exec`:

```bash
# Run Core Service Tests
docker compose exec -T identity_service python manage.py test authentication --noinput
docker compose exec -T catalog_service python manage.py test catalog --noinput
docker compose exec -T cart_service python manage.py test cart --noinput
docker compose exec -T inventory_service python manage.py test inventory --noinput
docker compose exec -T order_service python manage.py test orders --noinput
docker compose exec -T payment_service python manage.py test payments --noinput
docker compose exec -T finance_service python manage.py test finance --noinput
docker compose exec -T notification_service python manage.py test notifications --noinput
docker compose exec -T media_service python manage.py test media.tests --noinput
docker compose exec -T chat_service python manage.py test chat.tests --noinput
docker compose exec -T recommendation_service python manage.py test recommendations --noinput
```

### Run Resilience & Race Condition Tests

Dedicated test modules (`tests_resilience.py`) test multithreaded concurrency, database rollbacks, and service outages:

```bash
# Inventory Service: Multi-threaded stock reservation & row locking
docker compose exec -T inventory_service python manage.py test inventory.tests_resilience --noinput

# Order Service: Downstream outage, gRPC fallback & Saga compensating events
docker compose exec -T order_service python manage.py test orders.tests_resilience --noinput

# Payment Service: Concurrent checkout idempotency & provider failure fallback
docker compose exec -T payment_service python manage.py test payments.tests_resilience --noinput
```

---

## 🛠️ Tech Stack

- **Backend Framework**: Python 3.13 / Django 5.x / Django REST Framework
- **Frontend Framework**: Next.js 14 / React
- **API Protocol**: REST (HTTP/1.1), gRPC (HTTP/2), WebSockets
- **Event Streaming**: Apache Kafka 7.4 / Zookeeper
- **Databases**: PostgreSQL 15, Neo4j 5.20, Redis 7
- **API Gateway**: NGINX
