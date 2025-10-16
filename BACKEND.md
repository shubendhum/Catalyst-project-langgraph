# Catalyst Backend Configuration Guide

Complete guide for configuring and deploying the Catalyst backend independently.

---

## 📋 Backend Architecture

### Technology Stack

- **Framework**: FastAPI 0.110.1
- **Runtime**: Python 3.11+
- **Server**: Uvicorn (ASGI)
- **Database**: MongoDB 7.0 (via Motor async driver)
- **LLM**: Claude 3.7 Sonnet (via emergentintegrations)
- **WebSocket**: Native FastAPI WebSocket support

### Project Structure

```
backend/
├── server.py              # Main FastAPI application
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration (generated)
├── .env.example          # Environment template
├── agents/               # AI agent implementations
│   ├── __init__.py
│   ├── planner.py        # Requirements analysis
│   ├── architect.py      # System design
│   ├── coder.py          # Code generation
│   ├── tester.py         # Testing & validation
│   ├── reviewer.py       # Code review
│   ├── deployer.py       # Deployment simulation
│   └── explorer.py       # Enterprise exploration
├── orchestrator/         # Agent orchestration
│   ├── __init__.py
│   └── executor.py       # DAG execution engine
└── connectors/           # External integrations
    ├── __init__.py
    ├── github_connector.py
    └── jira_connector.py
```

---

## ⚙️ Environment Configuration

### Environment Files

**Three .env files are used:**

1. **Root `.env`** - Used by docker-compose
2. **`backend/.env`** - Backend-specific configuration
3. **`frontend/.env`** - Frontend-specific configuration

### Auto-Generation from config.yaml

```bash
# Generate all .env files
python3 scripts/generate_env.py

# Or use Make
make setup
```

This creates:
- `.env` → Root docker-compose variables
- `backend/.env` → Backend configuration
- `frontend/.env` → Frontend configuration

---

## 🔐 Backend Environment Variables

### Required Variables

#### 1. Database Connection

```bash
# MongoDB connection URL
MONGO_URL="mongodb://admin:password@mongodb:27017"

# For Docker: uses service name 'mongodb'
# For local: use 'localhost'

# Database name
DB_NAME="catalyst_db"
```

**Connection Formats:**
```bash
# Local development
MONGO_URL="mongodb://localhost:27017"

# Docker Compose (with auth)
MONGO_URL="mongodb://admin:password@mongodb:27017"

# Remote MongoDB
MONGO_URL="mongodb://user:pass@host.example.com:27017/?authSource=admin"

# MongoDB Atlas
MONGO_URL="mongodb+srv://user:pass@cluster.mongodb.net/catalyst_db"
```

#### 2. LLM Configuration (REQUIRED)

```bash
# Universal Emergent LLM Key
EMERGENT_LLM_KEY="sk-emergent-xxxxx"

# Default provider (anthropic, openai, google)
DEFAULT_LLM_PROVIDER="anthropic"

# Default model
DEFAULT_LLM_MODEL="claude-3-7-sonnet-20250219"
```

**How to get EMERGENT_LLM_KEY:**
1. Sign up at [emergent.sh](https://emergent.sh)
2. Navigate to Profile → Universal Key
3. Generate or copy your key
4. Add to `backend/.env`

**Alternative - Provider-specific keys:**
```bash
# Override with specific provider keys (optional)
OPENAI_API_KEY="sk-xxxxx"
ANTHROPIC_API_KEY="sk-ant-xxxxx"
GOOGLE_API_KEY="xxxxx"
```

#### 3. CORS Configuration

```bash
# CORS allowed origins
CORS_ORIGINS="*"

# For production, use specific domains:
# CORS_ORIGINS="https://catalyst.yourdomain.com,https://app.yourdomain.com"
```

### Optional Variables

#### Explorer Agent Integrations

```bash
# GitHub integration
GITHUB_TOKEN="ghp_xxxxx"

# Jira integration
JIRA_URL="https://yourcompany.atlassian.net"
JIRA_USERNAME="email@company.com"
JIRA_API_TOKEN="xxxxx"

# ServiceNow integration
SERVICENOW_URL="https://instance.service-now.com"
SERVICENOW_USERNAME="admin"
SERVICENOW_PASSWORD="xxxxx"
```

#### Security Settings

```bash
# Enable audit logging
ENABLE_AUDIT_LOGS="true"

# Enable PII redaction in logs
ENABLE_PII_REDACTION="true"

# Session timeout (minutes)
SESSION_TIMEOUT="60"
```

#### Performance Tuning

```bash
# Max concurrent task executions
MAX_CONCURRENT_TASKS="5"

# Agent execution timeout (seconds)
AGENT_TIMEOUT="300"

# WebSocket ping interval (seconds)
WEBSOCKET_PING_INTERVAL="30"
```

#### Monitoring

```bash
# Enable metrics collection
ENABLE_METRICS="true"

# Enable APM
ENABLE_PERFORMANCE_MONITORING="false"

# Sentry error tracking
SENTRY_DSN=""
```

#### Deployment

```bash
# Environment name
ENVIRONMENT="development"

# Mock deployment (true for testing)
MOCK_DEPLOYMENT="true"
```

#### Logging

```bash
# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL="INFO"
```

---

## 🚀 Running the Backend

### Option 1: Docker Compose (Recommended)

```bash
# Start all services (MongoDB + Backend + Frontend)
docker-compose up -d

# Backend only
docker-compose up -d mongodb backend

# View logs
docker-compose logs -f backend

# Access backend shell
docker-compose exec backend /bin/bash
```

### Option 2: Local Development

**Terminal 1 - Start MongoDB:**
```bash
# Install MongoDB locally
# Ubuntu/Debian
sudo apt-get install mongodb

# macOS
brew install mongodb-community

# Start MongoDB
mongod --dbpath ./data/db --port 27017
```

**Terminal 2 - Start Backend:**
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Update .env for local MongoDB
# MONGO_URL="mongodb://localhost:27017"

# Start server
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

**Access:**
- API: http://localhost:8001/api/
- Docs: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### Option 3: Production Deployment

```bash
# Build production image
docker build -f Dockerfile.backend -t catalyst-backend:latest .

# Run with production config
docker run -d \
  --name catalyst-backend \
  --env-file backend/.env \
  -p 8001:8001 \
  catalyst-backend:latest

# Or use docker-compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d backend
```

---

## 📦 Dependencies Installation

### Python Packages

**Core dependencies:**
```bash
pip install -r backend/requirements.txt
```

**emergentintegrations (Universal LLM):**
```bash
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

### Dependency List (requirements.txt)

```
# Web Framework
fastapi==0.110.1
uvicorn==0.25.0
starlette>=0.37.2
python-multipart>=0.0.9

# Database
motor==3.3.1
pymongo==4.5.0

# Data Validation
pydantic>=2.6.4
email-validator>=2.2.0

# LLM Integration
emergentintegrations        # Universal LLM library
openai==1.99.9
aiohttp>=3.8.0
google-generativeai>=0.3.0

# Authentication & Security
pyjwt>=2.10.1
bcrypt==4.1.3
passlib>=1.7.4
python-jose>=3.3.0
cryptography>=42.0.8

# Configuration
python-dotenv>=1.0.1

# HTTP & WebSocket
requests>=2.31.0
websockets

# Data Processing
pandas>=2.2.0
numpy>=1.26.0

# Utilities
tzdata>=2024.2
typer>=0.9.0

# Testing
pytest>=8.0.0

# AWS (optional)
boto3>=1.34.129
requests-oauthlib>=2.0.0
```

### Verify Installation

```bash
# Check Python version
python3 --version  # Should be 3.11+

# Check pip
pip --version

# List installed packages
pip list

# Verify emergentintegrations
python3 -c "import emergentintegrations; print('✓ emergentintegrations installed')"
```

---

## 🔌 API Endpoints

### Health & Info

```bash
GET /api/                    # API info
GET /api/health             # Health check (if configured)
```

### Projects

```bash
POST /api/projects          # Create project
GET  /api/projects          # List all projects
GET  /api/projects/{id}     # Get project details
```

**Example:**
```bash
curl -X POST http://localhost:8001/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "description": "A test project"
  }'
```

### Tasks

```bash
POST /api/tasks             # Create and execute task
GET  /api/tasks             # List tasks (optional: ?project_id=xxx)
GET  /api/tasks/{id}        # Get task details
```

**Example:**
```bash
curl -X POST http://localhost:8001/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "abc-123",
    "prompt": "Build a todo app"
  }'
```

### Agent Logs

```bash
GET /api/logs/{task_id}     # Get task execution logs
```

### Deployments

```bash
GET /api/deployments/{task_id}  # Get deployment report
```

### Explorer

```bash
POST /api/explorer/scan     # Scan enterprise system
GET  /api/explorer/scans    # List all scans
```

**Example:**
```bash
curl -X POST http://localhost:8001/api/explorer/scan \
  -H "Content-Type: application/json" \
  -d '{
    "system_name": "SailPoint IdentityIQ",
    "repo_url": "https://github.com/sailpoint/identityiq",
    "jira_project": "SAILPOINT-IIQ"
  }'
```

### WebSocket

```
WS /ws/{task_id}            # Real-time log streaming
```

**JavaScript Example:**
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/task-id-123');
ws.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(log.agent_name, log.message);
};
```

---

## 🗄️ Database Schema

### Collections

#### projects
```javascript
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "status": "active|archived",
  "created_at": "ISO8601"
}
```

#### tasks
```javascript
{
  "id": "uuid",
  "project_id": "uuid",
  "prompt": "string",
  "graph_state": {
    "planner": "completed|pending|failed",
    "architect": "completed",
    // ... other agents
  },
  "status": "pending|running|completed|failed",
  "cost": 0.85,
  "created_at": "ISO8601"
}
```

#### agent_logs
```javascript
{
  "id": "uuid",
  "task_id": "uuid",
  "agent_name": "Planner|Architect|Coder|...",
  "message": "string",
  "timestamp": "ISO8601"
}
```

#### deployments
```javascript
{
  "id": "uuid",
  "task_id": "uuid",
  "url": "https://deployed-app.com",
  "commit_sha": "abc123",
  "cost": 0.25,
  "report": "string",
  "created_at": "ISO8601"
}
```

#### explorer_scans
```javascript
{
  "id": "uuid",
  "system_name": "string",
  "brief": "string",
  "risks": ["risk1", "risk2"],
  "proposals": ["proposal1", "proposal2"],
  "created_at": "ISO8601"
}
```

---

## 🧪 Testing the Backend

### Manual API Testing

```bash
# Test root endpoint
curl http://localhost:8001/api/

# Create project
curl -X POST http://localhost:8001/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","description":"Testing"}'

# List projects
curl http://localhost:8001/api/projects

# Check MongoDB connection
docker-compose exec mongodb mongosh --eval "db.runCommand({ping: 1})"
```

### Automated Testing

```bash
# Run pytest
cd backend
pytest

# With coverage
pytest --cov=. --cov-report=html
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8001/api/

# Using locust
locust -f tests/locustfile.py
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Module Not Found: emergentintegrations

**Error:**
```
ModuleNotFoundError: No module named 'emergentintegrations'
```

**Solution:**
```bash
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

#### 2. MongoDB Connection Failed

**Error:**
```
pymongo.errors.ServerSelectionTimeoutError: No servers found
```

**Solution:**
```bash
# Check MongoDB is running
docker-compose ps mongodb

# Or local
systemctl status mongodb

# Verify MONGO_URL in backend/.env
cat backend/.env | grep MONGO_URL

# Test connection
python3 -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017'); print(client.server_info())"
```

#### 3. CORS Errors

**Error:**
```
Access to fetch at 'http://localhost:8001/api/' from origin 'http://localhost:3000' has been blocked by CORS
```

**Solution:**
```bash
# Update CORS_ORIGINS in backend/.env
CORS_ORIGINS="http://localhost:3000"

# Or allow all (development only)
CORS_ORIGINS="*"

# Restart backend
docker-compose restart backend
```

#### 4. LLM API Errors

**Error:**
```
Error: Invalid API key
```

**Solution:**
```bash
# Check key in backend/.env
cat backend/.env | grep EMERGENT_LLM_KEY

# Verify key is valid
curl -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-sonnet-20240229","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

#### 5. Port Already in Use

**Error:**
```
Error: bind: address already in use
```

**Solution:**
```bash
# Find process using port 8001
lsof -i :8001
sudo netstat -tulpn | grep 8001

# Kill process
kill -9 <PID>

# Or change port in backend/.env
BACKEND_PORT=8002
```

---

## 🔒 Security Best Practices

### Production Checklist

- [ ] Change `MONGO_ROOT_PASSWORD` from default
- [ ] Set `CORS_ORIGINS` to specific domains
- [ ] Use strong `SESSION_TIMEOUT` value
- [ ] Enable `ENABLE_AUDIT_LOGS=true`
- [ ] Enable `ENABLE_PII_REDACTION=true`
- [ ] Set `LOG_LEVEL=WARNING` or `ERROR`
- [ ] Use HTTPS/TLS for all connections
- [ ] Implement rate limiting
- [ ] Set up monitoring and alerting
- [ ] Regular security updates
- [ ] Backup database regularly

### Environment Security

```bash
# Never commit .env files
echo "*.env" >> .gitignore

# Use .env.example as template
cp backend/.env.example backend/.env

# Restrict .env permissions
chmod 600 backend/.env
```

---

## 📊 Monitoring

### Logs

```bash
# View backend logs
docker-compose logs -f backend

# View specific lines
docker-compose logs --tail=100 backend

# Search logs
docker-compose logs backend | grep ERROR
```

### Health Checks

```bash
# Check API
curl http://localhost:8001/api/

# Check MongoDB
docker-compose exec backend python3 -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; asyncio.run(AsyncIOMotorClient('mongodb://mongodb:27017').admin.command('ping'))"
```

### Metrics

```bash
# If metrics enabled
curl http://localhost:8001/metrics
```

---

## 🚀 Production Deployment

### Using Docker

```bash
# Build production image
docker build \
  -f Dockerfile.backend \
  -t catalyst-backend:1.0.0 \
  .

# Run with production settings
docker run -d \
  --name catalyst-backend \
  --env-file backend/.env \
  --restart unless-stopped \
  -p 8001:8001 \
  catalyst-backend:1.0.0
```

### Using Systemd (Linux)

Create `/etc/systemd/system/catalyst-backend.service`:

```ini
[Unit]
Description=Catalyst Backend API
After=network.target mongodb.service

[Service]
Type=simple
User=catalyst
WorkingDirectory=/opt/catalyst/backend
Environment="PATH=/opt/catalyst/venv/bin"
EnvironmentFile=/opt/catalyst/backend/.env
ExecStart=/opt/catalyst/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable catalyst-backend
sudo systemctl start catalyst-backend
sudo systemctl status catalyst-backend
```

---

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Motor Docs**: https://motor.readthedocs.io
- **MongoDB Docs**: https://docs.mongodb.com
- **Emergent Platform**: https://emergent.sh
- **Python Docs**: https://docs.python.org/3/

---

**Backend Guide Version**: 1.0.0  
**Last Updated**: October 2025  
**Platform Version**: 1.0.0
