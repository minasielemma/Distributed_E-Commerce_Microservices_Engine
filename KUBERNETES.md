# Kubernetes Deployment & Minikube Guide

This document describes the Kubernetes setup for the microservices application, designed to run on Minikube alongside the existing Docker Compose deployment without interference.

---

## 1. Architectural Overview

The application is deployed to the `microservices` namespace in Kubernetes. The deployment consists of:
- **11 Isolated PostgreSQL StatefulSets** with dynamic PersistentVolumeClaims.
- **1 Neo4j Graph Database StatefulSet** with persistent storage.
- **Message Broker & Infrastructure**: Zookeeper, Kafka, and Redis.
- **11 REST & gRPC Backend Microservices**: `identity-service`, `catalog-service`, `order-service`, `payment-service`, `inventory-service`, `finance-service`, `cart-service`, `media-service`, `chat-service`, `recommendation-service`, and `notification-service`.
- **Background Workers**: Celery workers, Celery beat, and Kafka consumers.
- **Frontends**: `admin-portal` and `storefront-site`.
- **API Gateway**: Nginx-based API Gateway (`gateway`) exposed via NodePort `30080`.

---

## 2. Service Mapping Table

| Docker Compose Service | Docker Image | Kubernetes Resource | K8s Service Name | Persistent Storage |
|---|---|---|---|---|
| `identity_db` | `postgres:15-alpine` | StatefulSet | `identity-db` | PVC `identity-db-pvc` (1Gi) |
| `catalog_db` | `postgres:15-alpine` | StatefulSet | `catalog-db` | PVC `catalog-db-pvc` (1Gi) |
| `order_db` | `postgres:15-alpine` | StatefulSet | `order-db` | PVC `order-db-pvc` (1Gi) |
| `payment_db` | `postgres:15-alpine` | StatefulSet | `payment-db` | PVC `payment-db-pvc` (1Gi) |
| `inventory_db` | `postgres:15-alpine` | StatefulSet | `inventory-db` | PVC `inventory-db-pvc` (1Gi) |
| `finance_db` | `postgres:15-alpine` | StatefulSet | `finance-db` | PVC `finance-db-pvc` (1Gi) |
| `cart_db` | `postgres:15-alpine` | StatefulSet | `cart-db` | PVC `cart-db-pvc` (1Gi) |
| `media_db` | `postgres:15-alpine` | StatefulSet | `media-db` | PVC `media-db-pvc` (1Gi) |
| `chat_db` | `postgres:15-alpine` | StatefulSet | `chat-db` | PVC `chat-db-pvc` (1Gi) |
| `recommendation_db` | `postgres:15-alpine` | StatefulSet | `recommendation-db` | PVC `recommendation-db-pvc` (1Gi) |
| `notification_db` | `postgres:15-alpine` | StatefulSet | `notification-db` | PVC `notification-db-pvc` (1Gi) |
| `neo4j` | `neo4j:5.20.0-community` | StatefulSet | `neo4j` | PVC `neo4j-pvc` (2Gi) |
| `zookeeper` | `confluentinc/cp-zookeeper:7.4.0` | Deployment | `zookeeper` | None |
| `kafka` | `confluentinc/cp-kafka:7.4.0` | Deployment | `kafka` | None |
| `redis` | `redis:7-alpine` | Deployment | `redis` | None |
| `identity_service` | `micro_service-identity_service:latest` | Deployment | `identity-service` | PVC `shared-keys-pvc` |
| `catalog_service` | `micro_service-catalog_service:latest` | Deployment | `catalog-service` | PVC `shared-keys-pvc` |
| `order_service` | `micro_service-order_service:latest` | Deployment | `order-service` | PVC `shared-keys-pvc` |
| `order_service_worker` | `micro_service-order_service_worker:latest` | Deployment | None | PVC `shared-keys-pvc` |
| `order_service_beat` | `micro_service-order_service_beat:latest` | Deployment | None | PVC `shared-keys-pvc` |
| `order_service_kafka_consumer` | `micro_service-order_service_kafka_consumer:latest` | Deployment | None | PVC `shared-keys-pvc` |
| `payment_service` | `micro_service-payment_service:latest` | Deployment | `payment-service` | PVC `shared-keys-pvc` |
| `payment_service_kafka_consumer` | `micro_service-payment_service:latest` | Deployment | None | PVC `shared-keys-pvc` |
| `inventory_service` | `micro_service-inventory_service:latest` | Deployment | `inventory-service` | PVC `shared-keys-pvc` |
| `finance_service` | `micro_service-finance_service:latest` | Deployment | `finance-service` | PVC `shared-keys-pvc` |
| `finance_service_kafka_consumer` | `micro_service-finance_service_kafka_consumer:latest` | Deployment | None | PVC `shared-keys-pvc` |
| `cart_service` | `micro_service-cart_service:latest` | Deployment | `cart-service` | PVC `shared-keys-pvc` |
| `media_service` | `micro_service-media_service:latest` | Deployment | `media-service` | PVC `shared-keys-pvc`, PVC `media-uploads-pvc` |
| `chat_service` | `micro_service-chat_service:latest` | Deployment | `chat-service` | PVC `shared-keys-pvc` |
| `recommendation_service` | `micro_service-recommendation_service:latest` | Deployment | `recommendation-service` | PVC `shared-keys-pvc` |
| `recommendation_service_kafka_consumer` | `micro_service-recommendation_service_kafka_consumer:latest` | Deployment | None | PVC `shared-keys-pvc` |
| `notification_service` | `micro_service-notification_service:latest` | Deployment | `notification-service` | PVC `shared-keys-pvc` |
| `notification_service_kafka_consumer` | `micro_service-notification_service_kafka_consumer:latest` | Deployment | None | PVC `shared-keys-pvc` |
| `admin_portal` | `micro_service-admin_portal:latest` | Deployment | `admin-portal` | None |
| `storefront_site` | `micro_service-storefront_site:latest` | Deployment | `storefront-site` | None |
| `gateway` | `micro_service-gateway:latest` | Deployment | `gateway` (NodePort 30080) | None |

---

## 3. Directory Structure

```text
k8s/
├── base/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── nginx-configmap.yaml
│   ├── pvc/
│   │   ├── databases-pvc.yaml
│   │   └── app-pvc.yaml
│   ├── statefulsets/
│   │   ├── postgres-databases.yaml
│   │   └── neo4j.yaml
│   ├── deployments/
│   │   ├── infrastructure.yaml
│   │   ├── microservices.yaml
│   │   ├── workers.yaml
│   │   ├── frontends.yaml
│   │   └── gateway.yaml
│   ├── services/
│   │   ├── database-services.yaml
│   │   ├── infrastructure-services.yaml
│   │   ├── microservice-services.yaml
│   │   ├── frontend-services.yaml
│   │   └── gateway-service.yaml
│   ├── ingress.yaml
│   └── kustomization.yaml
└── overlays/
    └── minikube/
        └── kustomization.yaml
```

---

## 4. Quick Start & Management Commands

### Start Deployment
```bash
./scripts/minikube-up.sh
```

### Stop Deployment (Preserves Data & PVCs)
```bash
./scripts/minikube-down.sh
```

### Purge Deployment (Removes PVCs and Namespace)
```bash
./scripts/minikube-down.sh --purge
```

---

## 5. Storage & Persistence Testing

### Verification Procedure:
1. Deploy workloads using `./scripts/minikube-up.sh`.
2. Insert data into any database (e.g. `identity-db` or upload media via `media-service`).
3. Delete the Pod:
   ```bash
   kubectl delete pod identity-db-0 -n microservices
   ```
4. Verify the new Pod recovers and data remains intact.
5. Stop and restart Minikube:
   ```bash
   minikube stop
   minikube start
   ```
6. Verify all PVCs rebind and data is completely preserved.

---

## 6. Troubleshooting

- **ImagePullBackOff**: Ensure local Docker Compose images were loaded into Minikube using `minikube image load <image>`.
- **Pod CrashLoopBackOff**: Check logs using `kubectl logs <pod-name> -n microservices`.
- **Database Connection Error**: Verify database pod status using `kubectl get pods -l app=identity-db -n microservices`.
- **Cannot Connect to Admin Portal / Storefront / Gateway from Host**: When running Minikube with the `docker` driver, NodePorts (30080, 30001, 30002) are isolated within the Minikube container. Run `./scripts/expose_gateway.sh` to forward ports to `localhost`, or run `minikube tunnel`.

