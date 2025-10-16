# Catalyst Platform - Deployment Guide

Complete guide for deploying Catalyst AI platform independently on any infrastructure.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Deployment Options](#deployment-options)
5. [Make Commands Reference](#make-commands-reference)
6. [Environment Variables](#environment-variables)
7. [Tools & Dependencies](#tools--dependencies)
8. [Troubleshooting](#troubleshooting)
9. [Production Deployment](#production-deployment)
10. [Monitoring & Maintenance](#monitoring--maintenance)

---

## 🔧 Prerequisites

### Required Tools

| Tool | Version | Purpose | Installation |
|------|---------|---------|--------------|
| **Docker** | 24.0+ | Container runtime | [Install Docker](https://docs.docker.com/get-docker/) |
| **Docker Compose** | 2.20+ | Multi-container orchestration | [Install Compose](https://docs.docker.com/compose/install/) |
| **Make** | 4.0+ | Build automation | `apt install make` (Linux) / Pre-installed (macOS) |
| **Python** | 3.11+ | Backend runtime | [Install Python](https://python.org/downloads/) |
| **Node.js** | 18+ | Frontend runtime | [Install Node.js](https://nodejs.org/) |
| **Yarn** | 1.22+ | Frontend package manager | `npm install -g yarn` |
| **Git** | 2.0+ | Version control | [Install Git](https://git-scm.com/) |

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB free space
- OS: Linux, macOS, or Windows with WSL2

**Recommended:**
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 20+ GB SSD
- OS: Ubuntu 22.04 LTS or macOS 13+

### Network Requirements

- Port 3000: Frontend (React)
- Port 8001: Backend API (FastAPI)
- Port 27017: MongoDB
- Outbound: Access to LLM APIs (Anthropic, OpenAI, Google)

---

## 🚀 Quick Start

### One-Command Setup

```bash
# Clone repository
git clone https://github.com/your-org/catalyst.git
cd catalyst

# Initialize everything (setup + install + build + start)
make init
```

This command will:
1. Generate `.env` file from `config.yaml`
2. Install all Python and Node.js dependencies
3. Build Docker images
4. Start all services (MongoDB, Backend, Frontend)

### Manual Step-by-Step Setup

```bash
# 1. Generate environment file
make setup

# 2. Edit .env and add your EMERGENT_LLM_KEY
nano .env
# or
vim .env

# 3. Install dependencies
make install-deps

# 4. Build Docker images
make build

# 5. Start all services
make up
```

### Access the Platform

Once running, access:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **MongoDB**: mongodb://localhost:27017

---

## ⚙️ Configuration

### Configuration File (`config.yaml`)

All settings are managed in `config.yaml`. This is the **single source of truth** for your deployment.

#### Key Sections:

**1. Database Configuration**
```yaml
database:
  root_username: admin                    # MongoDB admin username
  root_password: catalyst_admin_pass      # MongoDB admin password (CHANGE IN PRODUCTION!)
  name: catalyst_db                       # Database name
  port: 27017                             # MongoDB port
  url: mongodb://localhost:27017          # Connection URL
```

**2. LLM Configuration** ⚠️ **IMPORTANT**
```yaml
llm:
  emergent_llm_key: "YOUR_EMERGENT_LLM_KEY_HERE"  # Get from https://emergent.sh
  default_provider: anthropic                      # anthropic, openai, or google
  default_model: claude-3-7-sonnet-20250219       # Model name
```

**How to get your Emergent LLM Key:**
1. Sign up at [Emergent.sh](https://emergent.sh)
2. Go to Profile → Universal Key
3. Generate or copy your key
4. Paste into `config.yaml` or `.env`

**3. Explorer Agent (Optional)**
```yaml
explorer:
  github_token: "YOUR_GITHUB_TOKEN"           # For repository analysis
  jira_url: "https://company.atlassian.net"   # Jira instance URL
  jira_username: "email@company.com"          # Jira username
  jira_api_token: "YOUR_JIRA_TOKEN"           # Jira API token
```

**4. Security Settings**
```yaml
security:
  enable_audit_logs: true          # Log all operations
  enable_pii_redaction: true       # Redact sensitive data
  session_timeout: 60              # Minutes
```

### Generating `.env` from `config.yaml`

The platform uses a Python script to convert `config.yaml` → `.env`:

```bash
# Automatic (via Make)
make setup

# Manual
python3 scripts/generate_env.py
```

This generates `.env` with all variables properly formatted for Docker Compose.

### Editing Environment Variables

**Method 1: Edit `config.yaml` and regenerate**
```bash
nano config.yaml
make setup  # Regenerate .env
make restart  # Apply changes
```

**Method 2: Edit `.env` directly**
```bash
nano .env
make restart  # Apply changes
```

---

## 🐳 Deployment Options

### Option 1: Docker Compose (Recommended)

**Development Mode** (with hot reload):
```bash
make dev
```

**Production Mode**:
```bash
make prod-build
make prod-up
```

**What's included:**
- MongoDB 7.0 (with authentication)
- FastAPI backend (uvicorn with hot reload)
- React frontend (webpack dev server or nginx)
- Docker network for service communication
- Persistent volumes for data

### Option 2: Local Development (No Docker)

**Terminal 1 - MongoDB:**
```bash
# Install MongoDB locally
mongod --dbpath ./data/db --port 27017
```

**Terminal 2 - Backend:**
```bash
cd backend
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
uvicorn server:app --reload --port 8001
```

**Terminal 3 - Frontend:**
```bash
cd frontend
yarn install
yarn start
```

### Option 3: Kubernetes (Advanced)

See [KUBERNETES.md](KUBERNETES.md) for Kubernetes deployment manifests.

### Option 4: Cloud Deployment

**AWS ECS:**
```bash
# Use docker-compose.yml with ECS CLI
ecs-cli compose up
```

**Google Cloud Run:**
```bash
# Deploy backend
gcloud run deploy catalyst-backend --source ./backend

# Deploy frontend
gcloud run deploy catalyst-frontend --source ./frontend
```

**Azure Container Instances:**
```bash
az container create --resource-group catalyst --file docker-compose.yml
```

---

## 📝 Make Commands Reference

### Essential Commands

| Command | Description |
|---------|-------------|
| `make help` | Display all available commands |
| `make init` | Complete initialization (setup + install + build + start) |
| `make setup` | Generate .env file from config.yaml |
| `make up` | Start all services |
| `make down` | Stop all services |
| `make restart` | Restart all services |
| `make logs` | View logs from all services |
| `make status` | Check status of all services |

### Development Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start in development mode (hot reload) |
| `make install-deps` | Install all dependencies |
| `make build` | Build Docker images |
| `make clean` | Remove all containers and volumes |
| `make test` | Run automated tests |

### Service-Specific Logs

| Command | Description |
|---------|-------------|
| `make logs-backend` | View backend logs only |
| `make logs-frontend` | View frontend logs only |
| `make logs-mongodb` | View MongoDB logs only |

### Shell Access

| Command | Description |
|---------|-------------|
| `make shell-backend` | Open shell in backend container |
| `make shell-frontend` | Open shell in frontend container |
| `make shell-mongodb` | Open MongoDB shell (mongosh) |

### Database Management

| Command | Description |
|---------|-------------|
| `make backup-db` | Backup MongoDB database |
| `make restore-db` | Restore MongoDB from backup |

### Production Commands

| Command | Description |
|---------|-------------|
| `make prod-build` | Build for production |
| `make prod-up` | Start in production mode |
| `make health` | Check health of all services |
| `make update` | Pull latest changes and rebuild |

### Configuration Commands

| Command | Description |
|---------|-------------|
| `make env` | Show current environment variables |

---

## 🔐 Environment Variables

### Complete Variable List

#### Database Variables
```bash
MONGO_ROOT_USERNAME=admin                    # MongoDB admin username
MONGO_ROOT_PASSWORD=catalyst_admin_pass      # MongoDB admin password
DB_NAME=catalyst_db                          # Database name
MONGO_PORT=27017                             # MongoDB port
MONGO_URL=mongodb://localhost:27017          # Full connection URL
```

#### Backend Variables
```bash
BACKEND_PORT=8001                            # Backend API port
CORS_ORIGINS=*                               # CORS allowed origins (* for dev)
LOG_LEVEL=INFO                               # Logging level (DEBUG, INFO, WARNING, ERROR)
```

#### Frontend Variables
```bash
FRONTEND_PORT=3000                           # Frontend port
REACT_APP_BACKEND_URL=http://localhost:8001  # Backend URL (frontend uses this)
REACT_APP_ENABLE_VISUAL_EDITS=true           # Enable visual editor (dev only)
ENABLE_HEALTH_CHECK=false                    # Enable health check endpoint
```

#### LLM Variables (REQUIRED)
```bash
EMERGENT_LLM_KEY=sk-emergent-xxxxx           # Universal LLM key from Emergent.sh
DEFAULT_LLM_PROVIDER=anthropic               # anthropic, openai, or google
DEFAULT_LLM_MODEL=claude-3-7-sonnet-20250219 # Model identifier
```

**Optional - Provider-specific keys:**
```bash
OPENAI_API_KEY=sk-xxxxx                      # Override with OpenAI key
ANTHROPIC_API_KEY=sk-ant-xxxxx               # Override with Anthropic key
GOOGLE_API_KEY=xxxxx                         # Override with Google key
```

#### Explorer Agent Variables (Optional)
```bash
GITHUB_TOKEN=ghp_xxxxx                       # GitHub personal access token
JIRA_URL=https://company.atlassian.net       # Jira instance URL
JIRA_USERNAME=email@company.com              # Jira username
JIRA_API_TOKEN=xxxxx                         # Jira API token
SERVICENOW_URL=https://instance.service-now.com  # ServiceNow URL
SERVICENOW_USERNAME=admin                    # ServiceNow username
SERVICENOW_PASSWORD=xxxxx                    # ServiceNow password
```

#### Security Variables
```bash
ENABLE_AUDIT_LOGS=true                       # Enable audit logging
ENABLE_PII_REDACTION=true                    # Redact PII from logs
SESSION_TIMEOUT=60                           # Session timeout (minutes)
```

#### Performance Variables
```bash
MAX_CONCURRENT_TASKS=5                       # Max parallel agent executions
AGENT_TIMEOUT=300                            # Agent timeout (seconds)
WEBSOCKET_PING_INTERVAL=30                   # WebSocket ping (seconds)
```

#### Monitoring Variables
```bash
ENABLE_METRICS=true                          # Enable metrics collection
ENABLE_PERFORMANCE_MONITORING=false          # Enable APM
SENTRY_DSN=                                  # Sentry error tracking DSN
```

### Variable Priority

1. `.env` file (highest priority)
2. `config.yaml` (converted to .env)
3. Docker Compose defaults
4. Application defaults (lowest priority)

---

## 🛠️ Tools & Dependencies

### Backend Dependencies

**Core Framework:**
- `fastapi==0.110.1` - Modern web framework
- `uvicorn==0.25.0` - ASGI server
- `pydantic>=2.6.4` - Data validation

**Database:**
- `motor==3.3.1` - Async MongoDB driver
- `pymongo==4.5.0` - MongoDB Python driver

**LLM Integration:**
- `emergentintegrations` - Universal LLM library
  - Supports: OpenAI, Anthropic, Google
  - Auto-handles token counting
  - Built-in rate limiting

**Utilities:**
- `python-dotenv>=1.0.1` - Environment management
- `websockets` - WebSocket support
- `aiohttp>=3.8.0` - Async HTTP client

**Testing:**
- `pytest>=8.0.0` - Testing framework
- `httpx` - Async HTTP testing

### Frontend Dependencies

**Core:**
- `react@19.0.0` - UI library
- `react-dom@19.0.0` - React renderer
- `react-router-dom@7.5.1` - Routing

**State Management:**
- `zustand@5.0.8` - State management
- `axios@1.8.4` - HTTP client

**UI Components:**
- `@radix-ui/*` - Headless UI components
- `lucide-react@0.507.0` - Icons
- `tailwindcss@3.4.17` - Utility CSS
- `class-variance-authority@0.7.1` - Component variants

**Code Editor:**
- `monaco-editor@0.54.0` - Code editor
- `@monaco-editor/react@4.7.0` - React wrapper

**Visualization:**
- `react-flow-renderer@10.3.17` - DAG visualization
- `react-markdown@10.1.0` - Markdown rendering

**Forms:**
- `react-hook-form@7.56.2` - Form management
- `zod@3.24.4` - Schema validation

### System Dependencies

**Docker Images:**
- `python:3.11-slim` - Backend base
- `node:18-alpine` - Frontend build
- `nginx:alpine` - Frontend production
- `mongo:7.0` - Database

**Build Tools:**
- `gcc`, `g++`, `make` - Compilation
- `curl` - HTTP utilities
- `yarn` - Package management

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error:**
```
Error: bind: address already in use
```

**Solution:**
```bash
# Find process using port
lsof -i :3000  # or :8001, :27017

# Kill process
kill -9 <PID>

# Or change port in config.yaml
```

#### 2. MongoDB Connection Failed

**Error:**
```
pymongo.errors.ServerSelectionTimeoutError
```

**Solution:**
```bash
# Check MongoDB is running
make logs-mongodb

# Verify connection string in .env
cat .env | grep MONGO_URL

# Restart MongoDB
docker-compose restart mongodb
```

#### 3. Frontend Can't Connect to Backend

**Error:**
```
Network Error: Failed to fetch
```

**Solution:**
```bash
# Check backend is running
curl http://localhost:8001/api/

# Verify REACT_APP_BACKEND_URL in .env
cat .env | grep REACT_APP_BACKEND_URL

# Should be: http://localhost:8001 (for local)
# Update and restart:
make restart
```

#### 4. LLM API Errors

**Error:**
```
Error: Invalid API key
```

**Solution:**
```bash
# Verify key in .env
cat .env | grep EMERGENT_LLM_KEY

# Test key manually
curl -X POST https://api.emergent.sh/test \
  -H "Authorization: Bearer YOUR_KEY"

# Get new key from https://emergent.sh/profile/universal-key
```

#### 5. Docker Build Fails

**Error:**
```
ERROR: failed to solve
```

**Solution:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
make build

# Check disk space
df -h
```

#### 6. Dependencies Not Installing

**Error:**
```
ERROR: Could not find a version that satisfies the requirement
```

**Solution:**
```bash
# Update pip
pip install --upgrade pip

# Clear pip cache
pip cache purge

# Install with verbose output
pip install -r backend/requirements.txt -v
```

### Health Check Commands

```bash
# Check all services
make health

# Check individual service status
docker-compose ps

# View service logs
make logs

# Test backend API
curl http://localhost:8001/api/

# Test MongoDB
docker-compose exec mongodb mongosh --eval "db.runCommand({ ping: 1 })"
```

### Performance Issues

**Slow Response Times:**
```bash
# Check resource usage
docker stats

# Increase Docker resources (Docker Desktop)
# Settings → Resources → Memory: 8GB, CPUs: 4

# Check agent timeout
cat .env | grep AGENT_TIMEOUT
```

**High Memory Usage:**
```bash
# Restart services
make restart

# Clear MongoDB cache
docker-compose exec mongodb mongosh --eval "db.runCommand({clearLog: 'global'})"
```

---

## 🚀 Production Deployment

### Pre-Production Checklist

- [ ] Update `MONGO_ROOT_PASSWORD` to strong password
- [ ] Set `CORS_ORIGINS` to specific domains
- [ ] Configure SSL/TLS certificates
- [ ] Set up monitoring and alerting
- [ ] Configure automated backups
- [ ] Test disaster recovery
- [ ] Review security settings
- [ ] Set up rate limiting
- [ ] Configure CDN for frontend
- [ ] Enable production logging

### Production Configuration

**Update `config.yaml`:**
```yaml
deployment:
  environment: production
  mock_deployment: false

security:
  enable_audit_logs: true
  enable_pii_redaction: true

monitoring:
  enable_metrics: true
  enable_performance_monitoring: true
  sentry_dsn: "your-sentry-dsn"

database:
  root_password: "STRONG_PASSWORD_HERE"  # CHANGE THIS!
```

### Production Deployment Steps

```bash
# 1. Update configuration
nano config.yaml

# 2. Regenerate environment
make setup

# 3. Build production images
make prod-build

# 4. Start production services
make prod-up

# 5. Verify health
make health

# 6. Configure reverse proxy (nginx, traefik, etc.)
# 7. Set up SSL certificates (Let's Encrypt)
# 8. Configure monitoring (Prometheus, Grafana)
# 9. Set up automated backups
# 10. Test failover scenarios
```

### Reverse Proxy Setup (Nginx)

**`/etc/nginx/sites-available/catalyst`:**
```nginx
server {
    listen 80;
    server_name catalyst.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name catalyst.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/catalyst.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/catalyst.yourdomain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8001/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### SSL Certificate Setup

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d catalyst.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## 📊 Monitoring & Maintenance

### Database Backups

**Automated Daily Backups:**
```bash
# Add to crontab
crontab -e

# Add line:
0 2 * * * cd /path/to/catalyst && make backup-db
```

**Manual Backup:**
```bash
make backup-db
# Creates: backups/catalyst_backup_YYYYMMDD_HHMMSS.archive
```

**Restore Backup:**
```bash
make restore-db
# Follow prompts to select backup file
```

### Log Management

**View Logs:**
```bash
# All services
make logs

# Specific service
make logs-backend
make logs-frontend
make logs-mongodb
```

**Log Rotation:**
```bash
# Configure Docker log rotation
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Monitoring Endpoints

**Health Checks:**
```bash
# Backend health
curl http://localhost:8001/api/

# Database health
curl http://localhost:8001/api/health/db

# Full health check
make health
```

**Metrics (if enabled):**
```bash
# Prometheus metrics
curl http://localhost:8001/metrics

# Application metrics
curl http://localhost:8001/api/metrics
```

### Update Procedure

```bash
# 1. Backup database
make backup-db

# 2. Pull latest changes
git pull origin main

# 3. Update and restart
make update

# 4. Verify health
make health
```

### Security Updates

```bash
# Update Docker images
docker-compose pull

# Rebuild with latest base images
make build --no-cache

# Restart services
make restart
```

---

## 📚 Additional Resources

### Documentation Files

- **README.md** - Platform overview and features
- **REQUIREMENTS_VALIDATION.md** - Requirements compliance
- **DEPLOYMENT.md** - This file
- **API_DOCS.md** - API endpoint documentation
- **ARCHITECTURE.md** - System architecture details

### Online Resources

- **Emergent Platform**: https://emergent.sh
- **Docker Documentation**: https://docs.docker.com
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **React Documentation**: https://react.dev

### Support

- **GitHub Issues**: https://github.com/your-org/catalyst/issues
- **Community Forum**: https://forum.catalyst.ai
- **Email**: support@catalyst.ai

---

## 📄 License

Copyright © 2025 Catalyst AI Platform. All rights reserved.

---

**Deployment Guide Version**: 1.0.0  
**Last Updated**: October 2025  
**Platform Version**: 1.0.0
