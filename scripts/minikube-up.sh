#!/bin/bash
set -e

echo "===================================================="
echo " Starting Minikube & Deploying Microservices App"
echo "===================================================="

# Determine kubectl command location
if [ -f "/snap/google-cloud-cli/current/bin/kubectl" ]; then
    KUBECTL="/snap/google-cloud-cli/current/bin/kubectl"
elif command -v kubectl &>/dev/null; then
    KUBECTL="kubectl"
else
    KUBECTL="minikube kubectl --"
fi

echo "Using kubectl binary: $KUBECTL"

if ! command -v minikube &>/dev/null; then
    echo "ERROR: Minikube is not installed or not in PATH."
    exit 1
fi

if ! minikube status | grep -q "host: Running"; then
    echo "Starting Minikube cluster..."
    minikube start --driver=docker --listen-address=0.0.0.0 --ports=8080:30080,8081:30081
else
    echo "Minikube is already running."
fi

echo "Ensuring NGINX Ingress controller addon is enabled..."
minikube addons enable ingress &>/dev/null || true


REQUIRED_IMAGES=(
    "micro_service-identity_service:latest"
    "micro_service-catalog_service:latest"
    "micro_service-order_service:latest"
    "micro_service-order_service_worker:latest"
    "micro_service-order_service_beat:latest"
    "micro_service-order_service_kafka_consumer:latest"
    "micro_service-payment_service:latest"
    "micro_service-inventory_service:latest"
    "micro_service-finance_service:latest"
    "micro_service-finance_service_kafka_consumer:latest"
    "micro_service-cart_service:latest"
    "micro_service-media_service:latest"
    "micro_service-chat_service:latest"
    "micro_service-recommendation_service:latest"
    "micro_service-recommendation_service_kafka_consumer:latest"
    "micro_service-notification_service:latest"
    "micro_service-notification_service_kafka_consumer:latest"
    "micro_service-admin_portal:latest"
    "micro_service-storefront_site:latest"
    "micro_service-gateway:latest"
)

MISSING_IMAGES=0
for img in "${REQUIRED_IMAGES[@]}"; do
    if ! docker image inspect "$img" &>/dev/null; then
        echo "Missing local Docker image: $img"
        MISSING_IMAGES=1
    fi
done

if [ "$MISSING_IMAGES" -eq 1 ]; then
    echo "Building missing Docker Compose images..."
    docker compose build
fi

echo "Loading Docker images into Minikube..."
ALL_IMAGES_TO_LOAD=(
    "${REQUIRED_IMAGES[@]}"
    "postgres:15-alpine"
    "neo4j:5.20.0-community"
    "confluentinc/cp-zookeeper:7.4.0"
    "confluentinc/cp-kafka:7.4.0"
    "redis:7-alpine"
)

for img in "${ALL_IMAGES_TO_LOAD[@]}"; do
    echo "-> Loading $img into Minikube..."
    minikube image load "$img"
done

echo "Applying Kubernetes manifests via Kustomize..."
$KUBECTL apply -k k8s/overlays/minikube

echo "Waiting for database statefulsets to become ready..."
$KUBECTL rollout status statefulset identity-db -n microservices --timeout=120s || true
$KUBECTL rollout status statefulset catalog-db -n microservices --timeout=120s || true
$KUBECTL rollout status statefulset order-db -n microservices --timeout=120s || true

echo "Waiting for infrastructure deployments..."
$KUBECTL rollout status deployment redis -n microservices --timeout=120s || true
$KUBECTL rollout status deployment zookeeper -n microservices --timeout=120s || true
$KUBECTL rollout status deployment kafka -n microservices --timeout=120s || true

echo "Waiting for microservices deployments..."
$KUBECTL rollout status deployment identity-service -n microservices --timeout=120s || true
$KUBECTL rollout status deployment catalog-service -n microservices --timeout=120s || true
$KUBECTL rollout status deployment order-service -n microservices --timeout=120s || true
$KUBECTL rollout status deployment gateway -n microservices --timeout=120s || true

echo "===================================================="
echo " Kubernetes Workloads Status"
echo "===================================================="
$KUBECTL get pods -n microservices
echo ""
$KUBECTL get svc -n microservices
echo ""

MINIKUBE_IP=$(minikube ip 2>/dev/null || echo "127.0.0.1")
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "<YOUR-IP>")
echo "===================================================="
echo " Access Information (Zero-Script Standard Ingress)"
echo "===================================================="
echo " Standard ClusterIP Ingress active. No helper scripts needed!"
echo ""
echo " Host Machine Access:"
echo "   - Storefront Site:       http://localhost:8080/"
echo "   - Admin Portal:          http://localhost:8081/"
echo "   - Catalog Products API:  http://localhost:8080/api/catalog/storefront/products/"
echo ""
echo " LAN / Internet Access:"
echo "   - Storefront Site:       http://${LOCAL_IP}:8080/"
echo "   - Admin Portal:          http://${LOCAL_IP}:8081/"
echo "   - Catalog Products API:  http://${LOCAL_IP}:8080/api/catalog/storefront/products/"
echo "===================================================="


