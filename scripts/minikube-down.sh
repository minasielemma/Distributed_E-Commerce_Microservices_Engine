#!/bin/bash
set -e

echo "===================================================="
echo " Stopping Kubernetes Deployment"
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

if [ "$1" == "--purge" ]; then
    echo "WARNING: Purging ALL Kubernetes resources including PVCs..."
    $KUBECTL delete -k k8s/overlays/minikube --ignore-not-found
    $KUBECTL delete pvc --all -n microservices --ignore-not-found
    $KUBECTL delete namespace microservices --ignore-not-found
    echo "Kubernetes deployment and PVCs purged."
else
    echo "Tearing down Kubernetes workloads (preserving PVCs and storage)..."
    $KUBECTL delete -k k8s/overlays/minikube --ignore-not-found
    echo "Kubernetes workloads stopped. Persistent Volume Claims (PVCs) retained."
fi

echo "Docker Compose resources were NOT touched."
