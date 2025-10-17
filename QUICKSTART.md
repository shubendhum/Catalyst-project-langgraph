# Catalyst - Quick Start Guide

Get Catalyst up and running in 5 minutes!

# Catalyst - Quick Start Guide

Get Catalyst up and running in 5 minutes!

## Choose Your Deployment Method

### 🚀 Option 1: Makefile (Fastest - One Command!)

```bash
# Complete setup + start services
make setup
make start

# Or for Docker
make docker-up
```

**Access**: http://localhost:3000

**That's it!** See [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) for all Makefile commands.

---

### 2. Local Development (Manual)

```bash
# Start MongoDB
docker run -d --name catalyst-mongo -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=catalyst_admin_pass \
  mongo:5.0

# Backend (Terminal 1)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-langgraph.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend (Terminal 2)
cd frontend
yarn install
yarn start
```

**Access**: http://localhost:3000

---

### 2. Docker (Recommended for Testing)

```bash
# Start everything with one command
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Access**: 
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/api
- API Docs: http://localhost:8001/docs

---

### 3. Production Docker

```bash
# Copy and configure environment
cp .env.production .env
# Edit .env with your configuration

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

### 4. Kubernetes

```bash
# Create namespace
kubectl create namespace catalyst

# Create secrets
kubectl create secret generic catalyst-secrets \
  --from-literal=mongo-username=admin \
  --from-literal=mongo-password=catalyst_admin_pass \
  --from-literal=emergent-llm-key=sk-emergent-b14E29723DeDaF2A74 \
  --from-literal=mongo-url=mongodb://admin:catalyst_admin_pass@mongodb:27017 \
  -n catalyst

# Deploy all services
kubectl apply -f k8s/mongodb-deployment.yaml -n catalyst
kubectl apply -f k8s/backend-deployment.yaml -n catalyst
kubectl apply -f k8s/frontend-deployment.yaml -n catalyst

# Check status
kubectl get pods -n catalyst

# Port forward for testing
kubectl port-forward service/catalyst-frontend 3000:80 -n catalyst
```

**Access**: http://localhost:3000

---

### 5. AWS EC2 (One-Click Script)

```bash
# Configure AWS CLI
aws configure

# Edit the script with your key pair name
nano aws/deploy-ec2.sh
# Change: KEY_NAME="your-key-pair"

# Run deployment
./aws/deploy-ec2.sh

# SSH into instance (use IP from script output)
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# On EC2 instance
git clone <your-repo-url>
cd catalyst
docker-compose -f docker-compose.prod.yml up -d
```

**Access**: http://YOUR_EC2_IP:3000

---

## Using the Deployment Helper Script

```bash
# Make it executable
chmod +x deploy.sh

# Show help
./deploy.sh help

# Local development
./deploy.sh local

# Docker deployment
./deploy.sh docker

# Production Docker
./deploy.sh docker-prod

# Kubernetes
./deploy.sh k8s

# View logs
./deploy.sh logs

# Clean up
./deploy.sh clean
```

---

## Configuration

### Set LLM Provider

**Option 1: Use Emergent LLM Key (Default)**
```bash
# Already configured in .env
EMERGENT_LLM_KEY=sk-emergent-b14E29723DeDaF2A74
DEFAULT_LLM_PROVIDER=emergent
```

**Option 2: Custom Anthropic API Key**
```bash
# Edit .env
ANTHROPIC_API_KEY=sk-ant-your-key
DEFAULT_LLM_PROVIDER=anthropic
```

**Option 3: AWS Bedrock**
```bash
# Edit .env
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
DEFAULT_LLM_PROVIDER=bedrock
```

### Change LLM Provider via API

```bash
# Set to Emergent LLM Key
curl -X POST http://localhost:8001/api/chat/config \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "emergent",
    "model": "claude-3-7-sonnet-20250219",
    "api_key": null,
    "aws_config": null
  }'

# Set to custom Anthropic
curl -X POST http://localhost:8001/api/chat/config \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "anthropic",
    "model": "claude-3-7-sonnet-20250219",
    "api_key": "sk-ant-your-key"
  }'
```

---

## Testing

### Backend API Test

```bash
# Health check
curl http://localhost:8001/api/

# Get LLM config
curl http://localhost:8001/api/chat/config

# Create conversation
curl -X POST http://localhost:8001/api/chat/conversations

# Send message
curl -X POST http://localhost:8001/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "conversation_id": "test-123"}'
```

### Frontend Test

Open http://localhost:3000 in your browser

---

## Troubleshooting

### Backend not starting
```bash
# Check logs
docker logs catalyst-backend

# Check MongoDB connection
docker exec -it catalyst-mongo mongo -u admin -p catalyst_admin_pass
```

### Frontend can't connect to backend
```bash
# Check backend URL in .env
cat frontend/.env

# Test backend API
curl http://localhost:8001/api/
```

### Port already in use
```bash
# Change ports in docker-compose.yml
ports:
  - "3001:80"  # Frontend
  - "8002:8001"  # Backend
```

---

## Next Steps

1. **Read Full Documentation**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. **Configure Production**: Update environment variables
3. **Setup SSL**: For HTTPS in production
4. **Enable Monitoring**: Setup Prometheus/Grafana
5. **Backup MongoDB**: Setup automated backups

---

## Support

- **Documentation**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Issues**: GitHub Issues
- **Email**: support@catalyst.ai

---

## Quick Reference

| Service | Local Port | Docker Port | Description |
|---------|-----------|-------------|-------------|
| Frontend | 3000 | 3000 | React UI |
| Backend | 8001 | 8001 | FastAPI |
| MongoDB | 27017 | 27017 | Database |
| API Docs | 8001/docs | 8001/docs | Swagger UI |

**Default Credentials**:
- MongoDB: admin / catalyst_admin_pass
- Emergent LLM Key: sk-emergent-b14E29723DeDaF2A74
