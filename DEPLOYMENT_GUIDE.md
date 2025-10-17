# Catalyst AI Platform - Deployment Guide

Complete guide for deploying Catalyst on local machines, Kubernetes, and EC2.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [EC2 Deployment](#ec2-deployment)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker**: 20.10+ and Docker Compose 2.0+
- **Node.js**: 16+ (for local development)
- **Python**: 3.11+ (for local development)
- **MongoDB**: 5.0+ or MongoDB Atlas
- **Kubernetes**: 1.24+ (for K8s deployment)
- **AWS CLI**: 2.0+ (for EC2 deployment)

### Required API Keys

- **Emergent LLM Key**: `sk-emergent-b14E29723DeDaF2A74` (included)
- **Optional**: Custom Anthropic API Key
- **Optional**: AWS Bedrock credentials (access key, secret key, region)

---

## Local Development Setup

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd catalyst

# Install backend dependencies
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-langgraph.txt

# Install frontend dependencies
cd ../frontend
yarn install  # or npm install
```

### 2. Configure Environment

**Backend (.env)**:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

**Frontend (.env)**:
```bash
cp frontend/.env.example frontend/.env
# Edit frontend/.env with backend URL
```

### 3. Start MongoDB

```bash
# Using Docker
docker run -d \
  --name catalyst-mongo \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=catalyst_admin_pass \
  mongo:5.0
```

### 4. Run Services

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Frontend**:
```bash
cd frontend
yarn start  # or npm start
```

**Access**: 
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/api
- API Docs: http://localhost:8001/docs

---

## Docker Deployment

### Using Docker Compose (Recommended)

#### 1. Build and Start All Services

```bash
# Development mode
docker-compose up -d

# Production mode
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### 2. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001/api
- **MongoDB**: localhost:27017

### Manual Docker Build

#### Backend
```bash
# Build
docker build -f Dockerfile.backend -t catalyst-backend:latest .

# Run
docker run -d \
  --name catalyst-backend \
  -p 8001:8001 \
  -e MONGO_URL=mongodb://admin:catalyst_admin_pass@mongo:27017 \
  -e DB_NAME=catalyst_db \
  -e EMERGENT_LLM_KEY=sk-emergent-b14E29723DeDaF2A74 \
  --link catalyst-mongo:mongo \
  catalyst-backend:latest
```

#### Frontend
```bash
# Build
docker build -f Dockerfile.frontend \
  --build-arg REACT_APP_BACKEND_URL=http://localhost:8001 \
  -t catalyst-frontend:latest .

# Run
docker run -d \
  --name catalyst-frontend \
  -p 3000:80 \
  catalyst-frontend:latest
```

---

## Kubernetes Deployment

### Prerequisites

```bash
# Verify kubectl is configured
kubectl cluster-info

# Create namespace
kubectl create namespace catalyst
```

### 1. Deploy MongoDB

```bash
kubectl apply -f k8s/mongodb-deployment.yaml -n catalyst
```

### 2. Create Secrets

```bash
kubectl create secret generic catalyst-secrets \
  --from-literal=mongo-username=admin \
  --from-literal=mongo-password=catalyst_admin_pass \
  --from-literal=emergent-llm-key=sk-emergent-b14E29723DeDaF2A74 \
  -n catalyst
```

### 3. Deploy Backend

```bash
kubectl apply -f k8s/backend-deployment.yaml -n catalyst
kubectl apply -f k8s/backend-service.yaml -n catalyst
```

### 4. Deploy Frontend

```bash
kubectl apply -f k8s/frontend-deployment.yaml -n catalyst
kubectl apply -f k8s/frontend-service.yaml -n catalyst
```

### 5. Setup Ingress (Optional)

```bash
kubectl apply -f k8s/ingress.yaml -n catalyst
```

### 6. Verify Deployment

```bash
# Check pods
kubectl get pods -n catalyst

# Check services
kubectl get services -n catalyst

# View logs
kubectl logs -f deployment/catalyst-backend -n catalyst
```

### 7. Access Application

```bash
# Port forward (for testing)
kubectl port-forward service/catalyst-frontend 3000:80 -n catalyst
kubectl port-forward service/catalyst-backend 8001:8001 -n catalyst

# Access: http://localhost:3000
```

---

## EC2 Deployment

### Option 1: Using Docker on EC2

#### 1. Launch EC2 Instance

```bash
# Launch instance (AWS CLI)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups catalyst-sg \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Catalyst-Server}]'
```

**Security Group Rules**:
- Port 22 (SSH)
- Port 80 (HTTP)
- Port 443 (HTTPS)
- Port 3000 (Frontend)
- Port 8001 (Backend API)

#### 2. Connect to EC2

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

#### 3. Install Docker

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again
exit
ssh -i your-key.pem ubuntu@your-ec2-ip
```

#### 4. Deploy Application

```bash
# Clone repository
git clone <repository-url>
cd catalyst

# Create .env files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Update frontend/.env with EC2 public IP
echo "REACT_APP_BACKEND_URL=http://YOUR_EC2_IP:8001" > frontend/.env

# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f
```

#### 5. Access Application

- **Frontend**: http://YOUR_EC2_IP:3000
- **Backend**: http://YOUR_EC2_IP:8001/api

### Option 2: Using ECS (Elastic Container Service)

#### 1. Push Images to ECR

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Create repositories
aws ecr create-repository --repository-name catalyst-backend
aws ecr create-repository --repository-name catalyst-frontend

# Build and push backend
docker build -f Dockerfile.backend -t catalyst-backend:latest .
docker tag catalyst-backend:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/catalyst-backend:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/catalyst-backend:latest

# Build and push frontend
docker build -f Dockerfile.frontend -t catalyst-frontend:latest .
docker tag catalyst-frontend:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/catalyst-frontend:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/catalyst-frontend:latest
```

#### 2. Create ECS Task Definition

See `aws/ecs-task-definition.json`

#### 3. Deploy to ECS

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://aws/ecs-task-definition.json

# Create cluster
aws ecs create-cluster --cluster-name catalyst-cluster

# Create service
aws ecs create-service \
  --cluster catalyst-cluster \
  --service-name catalyst-service \
  --task-definition catalyst-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}"
```

---

## Configuration

### Backend Environment Variables

```bash
# Database
MONGO_URL=mongodb://admin:password@localhost:27017
DB_NAME=catalyst_db

# LLM Configuration
EMERGENT_LLM_KEY=sk-emergent-b14E29723DeDaF2A74
DEFAULT_LLM_PROVIDER=emergent  # emergent, anthropic, bedrock
DEFAULT_LLM_MODEL=claude-3-7-sonnet-20250219

# Optional: Custom Provider Keys
ANTHROPIC_API_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# API Configuration
CORS_ORIGINS=*
LOG_LEVEL=INFO

# Performance
MAX_CONCURRENT_TASKS=5
AGENT_TIMEOUT=300
```

### Frontend Environment Variables

```bash
# Backend URL
REACT_APP_BACKEND_URL=http://localhost:8001

# Development
WDS_SOCKET_PORT=443
REACT_APP_ENABLE_VISUAL_EDITS=true
```

### MongoDB Setup

```bash
# Connect to MongoDB
mongo mongodb://admin:catalyst_admin_pass@localhost:27017

# Create database and user
use catalyst_db
db.createUser({
  user: "catalyst_user",
  pwd: "catalyst_pass",
  roles: [{role: "readWrite", db: "catalyst_db"}]
})
```

---

## Troubleshooting

### Backend Not Starting

```bash
# Check logs
docker logs catalyst-backend

# Check MongoDB connection
mongo mongodb://admin:catalyst_admin_pass@localhost:27017

# Verify environment variables
docker exec catalyst-backend env | grep MONGO_URL
```

### Frontend Cannot Connect to Backend

```bash
# Check REACT_APP_BACKEND_URL
cat frontend/.env

# Test backend API
curl http://localhost:8001/api/

# Check CORS settings
docker exec catalyst-backend env | grep CORS_ORIGINS
```

### MongoDB Connection Issues

```bash
# Check MongoDB is running
docker ps | grep mongo

# Check MongoDB logs
docker logs catalyst-mongo

# Test connection
mongo mongodb://admin:catalyst_admin_pass@localhost:27017
```

### LLM API Errors

```bash
# Verify Emergent LLM Key
docker exec catalyst-backend env | grep EMERGENT_LLM_KEY

# Check API configuration
curl http://localhost:8001/api/chat/config

# Test LLM connection
curl -X POST http://localhost:8001/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "conversation_id": "test-123"}'
```

### Kubernetes Pod Issues

```bash
# Describe pod
kubectl describe pod <pod-name> -n catalyst

# Check logs
kubectl logs <pod-name> -n catalyst

# Check events
kubectl get events -n catalyst --sort-by='.lastTimestamp'

# Restart deployment
kubectl rollout restart deployment/catalyst-backend -n catalyst
```

---

## Monitoring and Maintenance

### Health Checks

```bash
# Backend health
curl http://localhost:8001/api/

# Frontend health
curl http://localhost:3000/

# MongoDB health
mongo mongodb://admin:catalyst_admin_pass@localhost:27017 --eval "db.adminCommand('ping')"
```

### Backup MongoDB

```bash
# Backup
docker exec catalyst-mongo mongodump \
  --username admin \
  --password catalyst_admin_pass \
  --authenticationDatabase admin \
  --out /backup/$(date +%Y%m%d)

# Restore
docker exec catalyst-mongo mongorestore \
  --username admin \
  --password catalyst_admin_pass \
  --authenticationDatabase admin \
  /backup/20240101
```

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Production Recommendations

1. **Use HTTPS**: Setup SSL/TLS certificates (Let's Encrypt)
2. **Secure MongoDB**: Use strong passwords, enable authentication
3. **Environment Secrets**: Use AWS Secrets Manager or Kubernetes Secrets
4. **Monitoring**: Setup Prometheus + Grafana
5. **Logging**: Use ELK stack or CloudWatch
6. **Backups**: Automate MongoDB backups
7. **Scaling**: Use Kubernetes HPA or ECS Auto Scaling
8. **CDN**: Use CloudFront for frontend static assets

---

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Documentation: <repository-url>/docs
- Email: support@catalyst.ai
