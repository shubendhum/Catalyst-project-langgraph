"""
EKS (Kubernetes) Deployment Methods for Deployer Agent
Contains all Kubernetes/EKS deployment generation methods
"""


def generate_k8s_namespace(self, project_name: str) -> str:
    """Generate Kubernetes namespace"""
    
    return f"""apiVersion: v1
kind: Namespace
metadata:
  name: {project_name}
  labels:
    app: {project_name}
    managed-by: catalyst
"""


async def generate_k8s_backend_deployment(self, project_name: str, architecture: Dict) -> str:
    """Generate Kubernetes deployment for backend"""
    
    return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {project_name}-backend
  namespace: {project_name}
  labels:
    app: {project_name}
    component: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {project_name}
      component: backend
  template:
    metadata:
      labels:
        app: {project_name}
        component: backend
    spec:
      containers:
      - name: backend
        image: your-registry/{project_name}-backend:latest
        ports:
        - containerPort: 8001
          name: http
        env:
        - name: MONGO_URL
          valueFrom:
            configMapKeyRef:
              name: {project_name}-config
              key: mongo_url
        - name: DB_NAME
          value: "{project_name}_db"
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: {project_name}-secrets
              key: jwt_secret
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: {project_name}-backend
  namespace: {project_name}
spec:
  selector:
    app: {project_name}
    component: backend
  ports:
  - port: 8001
    targetPort: 8001
    protocol: TCP
  type: ClusterIP
"""


async def generate_k8s_frontend_deployment(self, project_name: str, architecture: Dict) -> str:
    """Generate Kubernetes deployment for frontend"""
    
    return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {project_name}-frontend
  namespace: {project_name}
  labels:
    app: {project_name}
    component: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {project_name}
      component: frontend
  template:
    metadata:
      labels:
        app: {project_name}
        component: frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/{project_name}-frontend:latest
        ports:
        - containerPort: 80
          name: http
        env:
        - name: REACT_APP_API_URL
          valueFrom:
            configMapKeyRef:
              name: {project_name}-config
              key: backend_url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: {project_name}-frontend
  namespace: {project_name}
spec:
  selector:
    app: {project_name}
    component: frontend
  ports:
  - port: 80
    targetPort: 80
    protocol: TCP
  type: LoadBalancer
"""


def generate_k8s_mongodb_statefulset(self, project_name: str) -> str:
    """Generate MongoDB StatefulSet"""
    
    return f"""apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
  namespace: {project_name}
spec:
  serviceName: mongodb
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:7.0
        ports:
        - containerPort: 27017
          name: mongo
        volumeMounts:
        - name: mongo-data
          mountPath: /data/db
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: mongo-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb
  namespace: {project_name}
spec:
  selector:
    app: mongodb
  ports:
  - port: 27017
    targetPort: 27017
  clusterIP: None
"""


def generate_k8s_services(self, project_name: str) -> str:
    """Generate Kubernetes services configuration"""
    
    return f"""# Services are defined in deployment files
# This file can contain additional service configurations if needed

# Example: Internal service for backend
apiVersion: v1
kind: Service
metadata:
  name: {project_name}-backend-internal
  namespace: {project_name}
spec:
  selector:
    app: {project_name}
    component: backend
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP
"""


async def generate_k8s_ingress(self, project_name: str, config: Dict) -> str:
    """Generate Kubernetes Ingress"""
    
    domain = config.get("domain", f"{project_name}.example.com")
    
    return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {project_name}-ingress
  namespace: {project_name}
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - {domain}
    - api.{domain}
    secretName: {project_name}-tls
  rules:
  - host: {domain}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {project_name}-frontend
            port:
              number: 80
  - host: api.{domain}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {project_name}-backend
            port:
              number: 8001
"""


def generate_k8s_configmap(self, project_name: str, architecture: Dict) -> str:
    """Generate Kubernetes ConfigMap"""
    
    return f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: {project_name}-config
  namespace: {project_name}
data:
  mongo_url: "mongodb://mongodb:27017"
  backend_url: "http://{project_name}-backend:8001/api"
  environment: "production"
  log_level: "info"
"""


def generate_k8s_secrets(self, project_name: str) -> str:
    """Generate Kubernetes Secrets template"""
    
    return f"""apiVersion: v1
kind: Secret
metadata:
  name: {project_name}-secrets
  namespace: {project_name}
type: Opaque
stringData:
  jwt_secret: "CHANGE_THIS_IN_PRODUCTION"
  # Add other secrets here
  # Use base64 encoding or external secret managers in production
"""


def generate_helm_chart(self, project_name: str) -> str:
    """Generate Helm Chart.yaml"""
    
    return f"""apiVersion: v2
name: {project_name}
description: A Helm chart for {project_name}
type: application
version: 0.1.0
appVersion: "1.0.0"
keywords:
  - catalyst
  - generated
maintainers:
  - name: Catalyst AI
    email: support@catalyst.ai
"""


async def generate_helm_values(self, project_name: str, architecture: Dict, config: Dict) -> str:
    """Generate Helm values.yaml"""
    
    return f"""# Default values for {project_name}

replicaCount:
  backend: 3
  frontend: 2

image:
  registry: your-registry
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: LoadBalancer
  backend:
    port: 8001
  frontend:
    port: 80

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: {project_name}.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: {project_name}-tls
      hosts:
        - {project_name}.example.com

resources:
  backend:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "1Gi"
      cpu: "1000m"
  frontend:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"

mongodb:
  enabled: true
  persistence:
    enabled: true
    size: 20Gi

autoscaling:
  enabled: true
  backend:
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
  frontend:
    minReplicas: 2
    maxReplicas: 5
    targetCPUUtilizationPercentage: 70

config:
  environment: production
  logLevel: info

secrets:
  jwtSecret: "CHANGE_THIS"
"""


async def generate_eks_terraform(self, project_name: str, config: Dict) -> str:
    """Generate Terraform for EKS cluster"""
    
    return f"""# EKS Cluster Terraform Configuration

terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
    kubernetes = {{
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }}
  }}
}}

provider "aws" {{
  region = var.aws_region
}}

# VPC Module
module "vpc" {{
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "{project_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = data.aws_availability_zones.available.names
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_dns_hostnames = true

  public_subnet_tags = {{
    "kubernetes.io/role/elb" = 1
  }}

  private_subnet_tags = {{
    "kubernetes.io/role/internal-elb" = 1
  }}

  tags = {{
    Environment = "production"
    Project     = "{project_name}"
  }}
}}

# EKS Cluster
module "eks" {{
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "{project_name}-eks"
  cluster_version = "1.28"

  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  cluster_endpoint_public_access = true

  eks_managed_node_group_defaults = {{
    ami_type = "AL2_x86_64"
  }}

  eks_managed_node_groups = {{
    {project_name}_nodes = {{
      name = "{project_name}-node-group"

      instance_types = ["t3.medium"]

      min_size     = 2
      max_size     = 5
      desired_size = 3

      capacity_type = "ON_DEMAND"
    }}
  }}

  tags = {{
    Environment = "production"
    Project     = "{project_name}"
  }}
}}

# Kubernetes Provider
provider "kubernetes" {{
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

  exec {{
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }}
}}

# Data sources
data "aws_availability_zones" "available" {{
  state = "available"
}}
"""


def generate_eks_terraform_variables(self, config: Dict) -> str:
    """Generate EKS Terraform variables"""
    
    return """variable "aws_region" {
  description = "AWS region for EKS cluster"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "node_instance_type" {
  description = "EC2 instance type for EKS nodes"
  type        = string
  default     = "t3.medium"
}

variable "node_min_size" {
  description = "Minimum number of nodes"
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of nodes"
  type        = number
  default     = 5
}

variable "node_desired_size" {
  description = "Desired number of nodes"
  type        = number
  default     = 3
}
"""


def generate_eks_terraform_outputs(self) -> str:
    """Generate EKS Terraform outputs"""
    
    return """output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_iam_role_arn" {
  description = "IAM role ARN of the EKS cluster"
  value       = module.eks.cluster_iam_role_arn
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}
"""


def generate_eks_deploy_script(self, project_name: str) -> str:
    """Generate EKS deployment script"""
    
    return f"""#!/bin/bash

# EKS Deployment Script for {project_name}

set -e

echo "☸️  Deploying {project_name} to EKS..."

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed"
    exit 1
fi

# Configure kubectl
echo "🔧 Configuring kubectl..."
aws eks update-kubeconfig --region ${{AWS_REGION:-us-east-1}} --name {project_name}-eks

# Create namespace
echo "📦 Creating namespace..."
kubectl create namespace {project_name} --dry-run=client -o yaml | kubectl apply -f -

# Apply Kubernetes manifests
echo "🚀 Applying Kubernetes manifests..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/mongodb-statefulset.yaml
kubectl wait --for=condition=ready pod -l app=mongodb -n {project_name} --timeout=300s
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Or use Helm
# echo "📦 Installing with Helm..."
# helm upgrade --install {project_name} ./helm \\
#   --namespace {project_name} \\
#   --create-namespace \\
#   --wait

# Get status
echo "✅ Deployment complete!"
echo ""
kubectl get pods -n {project_name}
echo ""
kubectl get services -n {project_name}
echo ""
kubectl get ingress -n {project_name}
"""


def generate_eks_cluster_setup_script(self, project_name: str, config: Dict) -> str:
    """Generate EKS cluster setup script"""
    
    return f"""#!/bin/bash

# EKS Cluster Setup Script for {project_name}

set -e

echo "🏗️  Setting up EKS cluster..."

# Check prerequisites
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed"
    exit 1
fi

# Initialize Terraform
echo "📦 Initializing Terraform..."
cd terraform-eks
terraform init

# Plan infrastructure
echo "📋 Planning infrastructure..."
terraform plan -out=tfplan

# Apply infrastructure
echo "🔄 Creating EKS cluster (this may take 15-20 minutes)..."
terraform apply tfplan

# Configure kubectl
echo "🔧 Configuring kubectl..."
CLUSTER_NAME=$(terraform output -raw cluster_name)
AWS_REGION=$(terraform output -raw aws_region || echo "us-east-1")
aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME

# Install essential add-ons
echo "📦 Installing cluster add-ons..."

# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"
helm repo add eks https://aws.github.io/eks-charts
helm repo update
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \\
  -n kube-system \\
  --set clusterName=$CLUSTER_NAME \\
  --set serviceAccount.create=false \\
  --set serviceAccount.name=aws-load-balancer-controller

# Install Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Install cert-manager for TLS
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

echo "✅ EKS cluster setup complete!"
echo ""
echo "Cluster information:"
terraform output
"""


async def generate_eks_github_actions(self, project_name: str) -> str:
    """Generate GitHub Actions workflow for EKS deployment"""
    
    return f"""name: Deploy to EKS

on:
  push:
    branches: [ main ]
  workflow_dispatch:

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY_BACKEND: {project_name}-backend
  ECR_REPOSITORY_FRONTEND: {project_name}-frontend
  EKS_CLUSTER_NAME: {project_name}-eks

jobs:
  deploy:
    name: Deploy to EKS
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{{{ secrets.AWS_ACCESS_KEY_ID }}}}
        aws-secret-access-key: ${{{{ secrets.AWS_SECRET_ACCESS_KEY }}}}
        aws-region: ${{{{ env.AWS_REGION }}}}

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2

    - name: Build and push backend image
      env:
        ECR_REGISTRY: ${{{{ steps.login-ecr.outputs.registry }}}}
        IMAGE_TAG: ${{{{ github.sha }}}}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:$IMAGE_TAG -f backend/Dockerfile backend/
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:$IMAGE_TAG
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:latest

    - name: Build and push frontend image
      env:
        ECR_REGISTRY: ${{{{ steps.login-ecr.outputs.registry }}}}
        IMAGE_TAG: ${{{{ github.sha }}}}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:$IMAGE_TAG -f frontend/Dockerfile frontend/
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:$IMAGE_TAG
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:latest

    - name: Update kube config
      run: aws eks update-kubeconfig --name $EKS_CLUSTER_NAME --region $AWS_REGION

    - name: Deploy to EKS
      env:
        ECR_REGISTRY: ${{{{ steps.login-ecr.outputs.registry }}}}
        IMAGE_TAG: ${{{{ github.sha }}}}
      run: |
        kubectl set image deployment/{project_name}-backend \\
          backend=$ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:$IMAGE_TAG \\
          -n {project_name}
        
        kubectl set image deployment/{project_name}-frontend \\
          frontend=$ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:$IMAGE_TAG \\
          -n {project_name}
        
        kubectl rollout status deployment/{project_name}-backend -n {project_name}
        kubectl rollout status deployment/{project_name}-frontend -n {project_name}

    - name: Verify deployment
      run: |
        kubectl get pods -n {project_name}
        kubectl get services -n {project_name}
"""


async def generate_eks_readme(self, project_name: str, config: Dict) -> str:
    """Generate EKS deployment README"""
    
    return f"""# EKS Deployment Guide for {project_name}

## Prerequisites

- AWS CLI configured
- kubectl installed
- Helm 3 installed
- Terraform installed (for infrastructure setup)
- Docker (for building images)
- eksctl (optional, for easier cluster management)

## Architecture

```
┌─────────────────────────────────────────┐
│           AWS Load Balancer             │
│              (Ingress)                  │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────┐           ┌───▼────┐
│Frontend│           │Backend │
│  Pods  │           │  Pods  │
│ (2-5)  │           │ (2-10) │
└────────┘           └───┬────┘
                         │
                    ┌────▼────┐
                    │ MongoDB │
                    │StatefulSet│
                    └─────────┘
```

## Quick Start

### 1. Create EKS Cluster

```bash
# Using provided script
./setup-eks-cluster.sh

# Or manually with eksctl
eksctl create cluster \\
  --name {project_name}-eks \\
  --region us-east-1 \\
  --nodegroup-name {project_name}-nodes \\
  --node-type t3.medium \\
  --nodes 3 \\
  --nodes-min 2 \\
  --nodes-max 5
```

### 2. Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name {project_name}-eks
```

### 3. Deploy Application

**Option A: Using kubectl**
```bash
./deploy-eks.sh
```

**Option B: Using Helm**
```bash
helm upgrade --install {project_name} ./helm \\
  --namespace {project_name} \\
  --create-namespace \\
  --wait
```

### 4. Access Application

```bash
# Get Load Balancer URL
kubectl get ingress -n {project_name}

# Or get service URL
kubectl get service {project_name}-frontend -n {project_name}
```

## Configuration

### Update Helm Values

```bash
# Edit values
nano helm/values.yaml

# Apply changes
helm upgrade {project_name} ./helm -n {project_name}
```

### Update Environment Variables

```bash
# Edit configmap
kubectl edit configmap {project_name}-config -n {project_name}

# Edit secrets
kubectl edit secret {project_name}-secrets -n {project_name}

# Restart pods
kubectl rollout restart deployment -n {project_name}
```

## Monitoring & Logging

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/{project_name}-backend -n {project_name}

# Frontend logs
kubectl logs -f deployment/{project_name}-frontend -n {project_name}

# All pods
kubectl logs -f -l app={project_name} -n {project_name}
```

### Monitor Resources

```bash
# Pod status
kubectl get pods -n {project_name}

# Resource usage
kubectl top pods -n {project_name}
kubectl top nodes

# Events
kubectl get events -n {project_name}
```

## Scaling

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment/{project_name}-backend --replicas=5 -n {project_name}

# Scale frontend
kubectl scale deployment/{project_name}-frontend --replicas=3 -n {project_name}
```

### Auto-scaling

Auto-scaling is configured in the Helm values:
- Backend: 2-10 replicas (70% CPU threshold)
- Frontend: 2-5 replicas (70% CPU threshold)

## CI/CD

### GitHub Actions

The `.github/workflows/deploy-eks.yml` workflow:
1. Builds Docker images
2. Pushes to Amazon ECR
3. Deploys to EKS
4. Verifies deployment

**Required GitHub Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## Backup & Recovery

### Database Backup

```bash
# Backup MongoDB
kubectl exec -n {project_name} mongodb-0 -- mongodump --archive > backup.archive

# Restore
kubectl exec -i -n {project_name} mongodb-0 -- mongorestore --archive < backup.archive
```

## Cost Optimization

- Use Spot Instances for non-critical workloads
- Enable Cluster Autoscaler
- Use Horizontal Pod Autoscaler
- Right-size node instances
- Use AWS Savings Plans

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod <pod-name> -n {project_name}
kubectl logs <pod-name> -n {project_name}
```

### Service not accessible

```bash
# Check service
kubectl get svc -n {project_name}

# Check ingress
kubectl describe ingress -n {project_name}

# Check load balancer
kubectl get svc {project_name}-frontend -n {project_name} -o jsonpath='{{.status.loadBalancer.ingress[0].hostname}}'
```

### Database issues

```bash
# Check MongoDB status
kubectl exec -it mongodb-0 -n {project_name} -- mongosh --eval "db.adminCommand('ping')"

# Check persistent volume
kubectl get pvc -n {project_name}
```

## Cleanup

### Delete Application

```bash
# Using kubectl
kubectl delete namespace {project_name}

# Using Helm
helm uninstall {project_name} -n {project_name}
```

### Delete Cluster

```bash
# Using Terraform
cd terraform-eks
terraform destroy

# Using eksctl
eksctl delete cluster --name {project_name}-eks
```

## Production Checklist

- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure logging (ELK stack, CloudWatch)
- [ ] Enable TLS/SSL with cert-manager
- [ ] Set up backup automation
- [ ] Configure network policies
- [ ] Enable pod security policies
- [ ] Set resource limits
- [ ] Configure health checks
- [ ] Set up disaster recovery
- [ ] Document runbooks
"""
