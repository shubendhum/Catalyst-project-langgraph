#!/bin/bash
# Setup script for Artifactory Kubernetes deployment

set -e

ARTIFACTORY_URL="artifactory.devtools.syd.c1.macquarie.com:9996"
NAMESPACE="catalyst"

echo "Setting up Catalyst with Artifactory for Kubernetes"
echo "======================================================"

# Create namespace
echo "Creating namespace: $NAMESPACE"
kubectl create namespace $NAMESPACE 2>/dev/null || echo "Namespace already exists"

# Prompt for Artifactory credentials
read -p "Enter Artifactory username: " ARTIFACTORY_USER
read -sp "Enter Artifactory password: " ARTIFACTORY_PASS
echo ""
read -p "Enter Artifactory email: " ARTIFACTORY_EMAIL

# Create Docker registry secret for Artifactory
echo "Creating Artifactory image pull secret..."
kubectl create secret docker-registry artifactory-secret \
  --docker-server=$ARTIFACTORY_URL \
  --docker-username=$ARTIFACTORY_USER \
  --docker-password=$ARTIFACTORY_PASS \
  --docker-email=$ARTIFACTORY_EMAIL \
  -n $NAMESPACE 2>/dev/null || echo "Secret already exists"

# Create application secrets
echo "Creating application secrets..."
kubectl create secret generic catalyst-secrets \
  --from-literal=mongo-username=admin \
  --from-literal=mongo-password=catalyst_admin_pass \
  --from-literal=emergent-llm-key=sk-emergent-b14E29723DeDaF2A74 \
  --from-literal=mongo-url=mongodb://admin:catalyst_admin_pass@mongodb:27017 \
  -n $NAMESPACE 2>/dev/null || echo "Catalyst secrets already exist"

# Deploy services
echo "Deploying MongoDB..."
kubectl apply -f k8s/mongodb-deployment.artifactory.yaml -n $NAMESPACE

echo "Deploying Backend..."
kubectl apply -f k8s/backend-deployment.artifactory.yaml -n $NAMESPACE

echo "Deploying Frontend..."
kubectl apply -f k8s/frontend-deployment.artifactory.yaml -n $NAMESPACE

echo ""
echo "Deployment complete!"
echo ""
echo "Check status with:"
echo "  kubectl get pods -n $NAMESPACE"
echo ""
echo "Port forward for testing:"
echo "  kubectl port-forward service/catalyst-frontend 3000:80 -n $NAMESPACE"
echo "  kubectl port-forward service/catalyst-backend 8001:8001 -n $NAMESPACE"
