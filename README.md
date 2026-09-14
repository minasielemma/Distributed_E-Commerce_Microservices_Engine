# E-Commerce Microservices Platform

A enterprise-grade, event-driven multi-tenant e-commerce microservices platform built with **Python/Django REST Framework**, **Next.js**, **Kafka**, **gRPC**, **PostgreSQL**, **Redis**, and **Neo4j**.

**Language Composition**: Python (52.6%) | JavaScript (46.5%) | Other (0.9%)

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
        ┌────────────────────┬──────────┼──────────┬─────────────────┐
        ▼                    ▼          ▼          ▼                 ▼
   ┌──────────────┐   ┌──────────────┐ ┌──────┐ ┌────────────┐  ┌──────────────┐
   │  Identity    │   │   Catalog    │ │ Cart │ │   Order    │  │   Payment    │
   │   Service    │   │   Service    │ │ Serv │ │  Service   │  │   Service    │
   └──────┬───────┘   └──────┬───────┘ └──┬───┘ └──────┬─────┘  └──────┬───────┘
          │                  │            │          │              │
          ▼                  ▼            ▼          ▼              ▼
   ┌──────────────┐   ┌──────────────┐ ┌──────┐ ┌────────────┐  ┌──────────────┐
   │ identity_db  │   │  catalog_db  │ │Redis │ │  order_db  │  │  payment_db  │
   └──────────────┘   └──────────────┘ └──────┘ └────────────┘  └──────────────┘
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

## 📁 Project Structure

```
Distributed_E-Commerce_Microservices_Engine/
├── gateway/                          # NGINX API Gateway
├── storefront_site/                  # Next.js frontend
├── admin_portal/                     # Admin dashboard (Next.js)
├── identity_service/                 # Django auth service
├── catalog_service/                  # Django catalog service
├── inventory_service/                # Django inventory service
├── cart_service/                     # Django cart service (manage.py)
├── order_service/                    # Django order service
├── payment_service/                  # Django payment service
├── finance_service/                  # Django finance service
├── notification_service/             # Django notifications service
├── media_service/                    # Django media service
├── chat_service/                     # Django chat service
├── recommendation_service/           # Django recommendations service
├── docker-compose.yml                # Container orchestration
├── .env.example                      # Environment template
└── README.md                         # This file
```

---

## ⚡ Key Architectural Patterns

1. **Database-per-Service**: Each microservice strictly owns its Postgres database schema (`identity_db`, `catalog_db`, `order_db`, etc.). Direct cross-service database queries are forbidden.

2. **Saga Pattern (Choreography & Orchestration)**:
   - Order creation triggers `order.created` event → `inventory_service` reserves stock → `payment_service` processes payment → `order_service` confirms order (`PAID`).
   - If payment fails, a compensating event (`inventory.release`) is emitted to restore stock.
   - If inventory reservation fails, a compensating event (`payment.refund`) is emitted to refund payment.

3. **Transactional Outbox Pattern**: Database writes and event publications are wrapped in local DB transactions using `OutboxEvent` tables to guarantee at-least-once delivery to Kafka.

4. **Idempotent Consumers**: Event consumers track processed message IDs using `ProcessedEvent` records to prevent double-processing on duplicate message delivery.

5. **High Concurrency & Row Locking**: `select_for_update()` row-level locks are used during stock reservation and payment checkout to eliminate race conditions and over-booking.

---

## 🛠️ Tech Stack

### Backend
- **Framework**: Python 3.13 / Django 5.x / Django REST Framework
- **API Protocol**: REST (HTTP/1.1), gRPC (HTTP/2), WebSockets
- **WSGI Server**: Gunicorn
- **Django Management**: `manage.py` CLI for migrations, testing, and service management

### Frontend
- **Framework**: Next.js 14 / React
- **Package Manager**: npm
- **UI Styling**: TailwindCSS / Styled Components

### Messaging & Events
- **Event Streaming**: Apache Kafka 7.4 / Zookeeper
- **Message Format**: JSON

### Data Layer
- **Primary Database**: PostgreSQL 15 (one per microservice)
- **Cache**: Redis 7
- **Graph Database**: Neo4j 5.20 (Recommendations)

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **API Gateway**: NGINX
- **Service Communication**: REST, gRPC

---

## 🚀 Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/) (v2.0+)
- Python 3.13+ (for local development)
- Node.js 18+ (for frontend development)

### Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Configure database credentials, Kafka endpoints, Redis URLs, and payment provider keys in `.env`.

### Running the Infrastructure & Services

Start all microservices and database containers:

```bash
docker compose up -d
```

Check running container status:

```bash
docker compose ps
```

View logs for a specific service:

```bash
docker compose logs -f cart_service
```

Stop all services:

```bash
docker compose down
```

Stop and remove volumes (full reset):

```bash
docker compose down -v
```

---

## 🗄️ Database Setup & Migrations

Each microservice manages its own database schema. Apply migrations after starting containers:

```bash
# Example: Run migrations for Cart Service
docker compose exec cart_service python manage.py migrate

# Run for all Django services
docker compose exec identity_service python manage.py migrate
docker compose exec catalog_service python manage.py migrate
docker compose exec inventory_service python manage.py migrate
docker compose exec order_service python manage.py migrate
docker compose exec payment_service python manage.py migrate
docker compose exec finance_service python manage.py migrate
docker compose exec notification_service python manage.py migrate
docker compose exec media_service python manage.py migrate
docker compose exec chat_service python manage.py migrate
docker compose exec recommendation_service python manage.py migrate
```

---

## 🧪 Testing Suite & Resilience Verification

The platform includes unit, integration, and high-concurrency resilience test suites across all 14 microservices (**176+ tests** total).

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
docker compose exec -T media_service python manage.py test media --noinput
docker compose exec -T chat_service python manage.py test chat --noinput
docker compose exec -T recommendation_service python manage.py test recommendations --noinput
```

### Run Resilience & Race Condition Tests

Dedicated test modules (`tests/test_resilience.py`) test multithreaded concurrency, database rollbacks, and service outages:

```bash
# Inventory Service: Multi-threaded stock reservation & row locking
docker compose exec -T inventory_service python manage.py test inventory.tests.test_resilience --noinput

# Order Service: Downstream outage, gRPC fallback & Saga compensating events
docker compose exec -T order_service python manage.py test orders.tests.test_resilience --noinput

# Payment Service: Concurrent checkout idempotency & provider failure fallback
docker compose exec -T payment_service python manage.py test payments.tests.test_resilience --noinput
```

### Frontend Testing

```bash
# Test storefront
cd storefront_site
npm test

# Test admin portal
cd admin_portal
npm test
```

---

## 🔌 API Documentation

### Gateway Routes

| Method | Endpoint | Service |
|--------|----------|---------|
| `POST` | `/api/auth/login` | Identity Service |
| `POST` | `/api/auth/register` | Identity Service |
| `GET` | `/api/products` | Catalog Service |
| `GET` | `/api/cart` | Cart Service |
| `POST` | `/api/orders` | Order Service |
| `GET` | `/api/chat` | Chat Service (WebSocket) |

Detailed API specs available at `/api/docs` (Swagger/OpenAPI) when services are running.

---

## 📊 Monitoring & Observability

### Logging
- Structured JSON logging across all services
- Centralized log aggregation via Docker Compose

### Metrics
- Prometheus-compatible metrics endpoints
- Service performance and business metrics tracking

### Health Checks
All services expose health check endpoints at `/health`:

```bash
curl http://localhost:8000/health
```

---

## 🔐 Security Features

- **JWT Authentication**: Stateless token-based auth via Identity Service
- **Multi-Tenant Isolation**: Tenant data segregation at DB level
- **HTTPS Support**: TLS termination at NGINX gateway
- **Rate Limiting**: Request throttling per tenant
- **API Key Management**: Service-to-service authentication
- **Payment Security**: PCI-compliant payment handling via Polar.sh

---

## 🚢 Deployment

### Docker Compose (Development/Testing)
Already configured with `docker-compose.yml`

### Production Deployment
For production, consider:
- **Kubernetes**: Helm charts for orchestration
- **Service Mesh**: Istio for advanced traffic management
- **Managed Databases**: AWS RDS, Google Cloud SQL
- **Message Queue**: AWS SQS, Google Cloud Pub/Sub, or self-managed Kafka
- **CDN**: CloudFront or similar for static assets

---

## 📝 Development Workflow

### Local Setup (Without Docker)

1. **Backend**: Create virtual environments for each service
   ```bash
   cd cart_service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py runserver
   ```

2. **Frontend**: Install Node dependencies
   ```bash
   cd storefront_site
   npm install
   npm run dev
   ```

### Code Style & Linting

- **Python**: PEP 8 (Black formatter, flake8)
- **JavaScript**: ESLint + Prettier

```bash
# Python linting
black --check cart_service/
flake8 cart_service/

# JavaScript linting
cd storefront_site
npm run lint
npm run format
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See `LICENSE` file for details.

---

## 📞 Support & Contact

For issues, questions, or contributions, please:
- Open a GitHub Issue
- Contact: [Project Maintainer]

---

## 🔗 Quick Links

- [Docker Documentation](https://docs.docker.com/)
- [Django Documentation](https://docs.djangoproject.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Last Updated**: September 13, 2026 | **Status**: Active Development
