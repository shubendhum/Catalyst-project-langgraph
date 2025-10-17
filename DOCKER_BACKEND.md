# Catalyst Backend - Docker Guide

Complete guide for building and deploying Catalyst backend using Docker with all dependencies.

---

## 📦 Docker Images Overview

### Three Optimized Images

| Image | Base | Size | Use Case | File |
|-------|------|------|----------|------|
| **Production** | python:3.11-slim (Debian) | ~400MB | Production deployments | `Dockerfile.backend.prod` |
| **Development** | python:3.11-slim | ~500MB | Local development | `Dockerfile.backend.dev` |
| **Minimal** | python:3.11-alpine | ~250MB | Resource-constrained envs | `Dockerfile.backend.alpine` |

### Image Features Comparison

| Feature | Production | Development | Minimal |
|---------|-----------|-------------|---------|
| Multi-stage build | ✅ | ❌ | ❌ |
| Non-root user | ✅ | ❌ | ✅ |
| Hot reload | ❌ | ✅ | ❌ |
| Debug tools | ❌ | ✅ | ❌ |
| Workers | 4 | 1 | 2 |
| Health check | ✅ | ✅ | ✅ |
| Security hardened | ✅ | ❌ | ✅ |

---

## 🔨 Building Docker Images

### Quick Build - All Images

```bash
# Build all three images at once
./scripts/build-backend-images.sh
```

This creates:
- `catalyst-backend:production` (recommended for prod)
- `catalyst-backend:dev` (hot reload for development)
- `catalyst-backend:alpine` (smallest size)

### Manual Builds

#### Production Image (Recommended)

```bash
docker build \
  -f Dockerfile.backend.prod \
  -t catalyst-backend:latest \
  -t catalyst-backend:1.0.0 \
  -t catalyst-backend:production \
  .
```

**Features:**
- Multi-stage build (smaller final image)
- Non-root user (security)
- 4 uvicorn workers
- Production-optimized
- Health checks enabled

#### Development Image

```bash
docker build \
  -f Dockerfile.backend.dev \
  -t catalyst-backend:dev \
  .
```

**Features:**
- Hot reload enabled
- Debug tools included (ipdb, black, flake8)
- Full development environment
- Single worker for easier debugging

#### Minimal Alpine Image

```bash
docker build \
  -f Dockerfile.backend.alpine \
  -t catalyst-backend:alpine \
  .
```

**Features:**
- Smallest image size (~250MB)
- Alpine Linux base
- Non-root user
- 2 workers
- Perfect for resource-constrained environments

---

## 🚀 Running Docker Containers

### Using Docker Compose (Recommended)

**Development:**
```bash
docker-compose up -d
```

**Production:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Standalone Docker Run

#### Development

```bash
docker run -d \
  --name catalyst-backend \
  --env-file backend/.env \
  -p 8001:8001 \
  -v $(pwd)/backend:/app/backend \
  catalyst-backend:dev
```

#### Production

```bash
docker run -d \
  --name catalyst-backend \
  --env-file backend/.env \
  -p 8001:8001 \
  --restart unless-stopped \
  --memory=\"2g\" \
  --cpus=\"2\" \
  --health-cmd=\"curl -f http://localhost:8001/api/ || exit 1\" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  catalyst-backend:production
```

#### With MongoDB Link

```bash
# Start MongoDB first
docker run -d \
  --name catalyst-mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:7.0

# Start backend with MongoDB link
docker run -d \
  --name catalyst-backend \
  --link catalyst-mongodb:mongodb \
  -e MONGO_URL=\"mongodb://admin:password@mongodb:27017\" \
  -e DB_NAME=\"catalyst_db\" \
  -e EMERGENT_LLM_KEY=\"your-key\" \
  -p 8001:8001 \
  catalyst-backend:production
```

---

## 📋 All Dependencies Included

### System Dependencies

**Production & Development (Debian):**
```bash
gcc, g++, make           # C/C++ compilers
libffi-dev               # Foreign function interface
libssl-dev               # SSL/TLS support
curl                     # HTTP client for health checks
ca-certificates          # SSL certificates
```

**Minimal (Alpine):**
```bash
gcc, musl-dev            # C compiler for Alpine
libffi-dev               # FFI support
openssl-dev              # SSL support
curl                     # Health checks
libstdc++                # C++ standard library
```

### Python Dependencies (30+)

All automatically installed from `backend/requirements.txt`:

#### Core Framework
```
fastapi==0.110.1
uvicorn[standard]==0.25.0
starlette>=0.37.2
python-multipart>=0.0.9
uvloop>=0.19.0           # High-performance event loop
```

#### Database
```
motor==3.3.1             # Async MongoDB driver
pymongo==4.5.0           # MongoDB driver
```

#### LLM Integration
```
emergentintegrations     # Universal LLM (custom index)
openai==1.99.9
aiohttp>=3.8.0
httpx>=0.23.0
google-generativeai>=0.3.0
```

#### Security
```
pyjwt>=2.10.1
bcrypt==4.1.3
passlib>=1.7.4
python-jose>=3.3.0
cryptography>=42.0.8
```

#### Configuration
```
python-dotenv>=1.0.1
pyyaml>=6.0
```

#### Networking
```
requests>=2.31.0
websockets>=13.0
```

#### Data Processing
```
pandas>=2.2.0
numpy>=1.26.0
```

#### Utilities
```
typer>=0.9.0
python-dateutil>=2.8.2
python-json-logger>=2.0.7
```

#### Testing (Dev only)
```
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
faker>=24.0.0
```

#### Code Quality (Dev only)
```
black>=24.1.1
isort>=5.13.2
flake8>=7.0.0
mypy>=1.8.0
bandit>=1.7.7
```

### Special: emergentintegrations

**Installed from custom index:**
```bash
pip install emergentintegrations \
  --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

This is handled automatically in all Dockerfiles.

---

## 🔧 Docker Image Architecture

### Production Image (Multi-Stage Build)

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder
- Install build dependencies
- Create virtual environment
- Install all Python packages
- Install emergentintegrations

# Stage 2: Runtime
FROM python:3.11-slim
- Copy only virtual environment (not build tools)
- Copy application code
- Create non-root user
- Set proper permissions
- Configure health check
- Start uvicorn with 4 workers
```

**Benefits:**
- Smaller final image (build tools removed)
- Faster deployment
- More secure (minimal attack surface)

### File Structure in Container

```
/app/backend/
├── server.py              # Main FastAPI app
├── requirements.txt       # Dependencies list
├── .env                   # Environment config (from volume/env-file)
├── agents/               # AI agents
│   ├── planner.py
│   ├── architect.py
│   ├── coder.py
│   ├── tester.py
│   ├── reviewer.py
│   ├── deployer.py
│   └── explorer.py
├── orchestrator/         # Workflow engine
│   └── executor.py
├── connectors/           # External integrations
│   ├── github_connector.py
│   └── jira_connector.py
├── logs/                 # Application logs
├── temp/                 # Temporary files
└── uploads/              # File uploads (if any)
```

---

## 🔐 Environment Variables

### Required in Docker

```bash
# Database
MONGO_URL="mongodb://admin:password@mongodb:27017"
DB_NAME="catalyst_db"

# LLM (Required)
EMERGENT_LLM_KEY="sk-emergent-xxxxx"

# API
CORS_ORIGINS="*"
```

### Optional

```bash
# Performance
MAX_CONCURRENT_TASKS="5"
AGENT_TIMEOUT="300"

# Security
ENABLE_AUDIT_LOGS="true"
ENABLE_PII_REDACTION="true"

# Monitoring
ENABLE_METRICS="true"
SENTRY_DSN=""

# Logging
LOG_LEVEL="INFO"
```

### Passing Environment Variables

**Method 1: .env file (Recommended)**
```bash
docker run -d \
  --env-file backend/.env \
  catalyst-backend:latest
```

**Method 2: Individual -e flags**
```bash
docker run -d \
  -e MONGO_URL="mongodb://mongodb:27017" \
  -e DB_NAME="catalyst_db" \
  -e EMERGENT_LLM_KEY="sk-xxxxx" \
  catalyst-backend:latest
```

**Method 3: Docker Compose**
```yaml
services:
  backend:
    env_file:
      - backend/.env
    environment:
      - MONGO_URL=mongodb://mongodb:27017
```

---

## 🏥 Health Checks

### Built-in Health Check

All images include health checks:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8001/api/ || exit 1
```

### Manual Health Check

```bash
# Check container health status
docker ps

# View health check logs
docker inspect catalyst-backend | jq '.[0].State.Health'

# Test endpoint manually
curl http://localhost:8001/api/
```

---

## 🔍 Debugging & Logs

### View Logs

```bash
# Follow logs
docker logs -f catalyst-backend

# Last 100 lines
docker logs --tail=100 catalyst-backend

# With timestamps
docker logs -t catalyst-backend

# Search logs
docker logs catalyst-backend 2>&1 | grep ERROR
```

### Access Container Shell

```bash
# Production/Minimal (uses bash or sh)
docker exec -it catalyst-backend /bin/bash

# Alpine (uses sh)
docker exec -it catalyst-backend /bin/sh

# As root (for debugging)
docker exec -u root -it catalyst-backend /bin/bash
```

### Run Commands Inside Container

```bash
# Check Python version
docker exec catalyst-backend python3 --version

# List installed packages
docker exec catalyst-backend pip list

# Test MongoDB connection
docker exec catalyst-backend python3 -c \"from motor.motor_asyncio import AsyncIOMotorClient; print('OK')\"

# Check emergentintegrations
docker exec catalyst-backend python3 -c \"import emergentintegrations; print('OK')\"
```

---

## 📊 Image Size Optimization

### Current Sizes

```
catalyst-backend:production    ~400MB
catalyst-backend:dev           ~500MB
catalyst-backend:alpine        ~250MB
```

### Optimization Techniques Used

1. **Multi-stage build** (Production)
   - Build dependencies in stage 1
   - Copy only runtime to stage 2
   - Reduces size by ~150MB

2. **.dockerignore**
   - Excludes unnecessary files
   - Faster builds
   - Smaller context

3. **Layer caching**
   - Requirements installed before code copy
   - Faster rebuilds on code changes

4. **Minimal base images**
   - Alpine: smallest (~250MB)
   - Debian slim: good balance (~400MB)

5. **No cache pip installs**
   - `--no-cache-dir` flag
   - Reduces image size

6. **Cleanup**
   - Remove apt cache
   - Remove build dependencies after install

---

## 🧪 Testing Docker Images

### Test Build

```bash
# Build and immediately run tests
docker build -f Dockerfile.backend.prod -t test-backend . && \
docker run --rm test-backend python3 -c "import fastapi, motor, emergentintegrations; print('All imports OK')"
```

### Test Container Startup

```bash
# Start with minimal config
docker run -d \
  --name test-backend \
  -e MONGO_URL="mongodb://localhost:27017" \
  -e DB_NAME="test_db" \
  -e EMERGENT_LLM_KEY="test-key" \
  -p 8001:8001 \
  catalyst-backend:latest

# Check if it started
docker ps | grep test-backend

# Check logs
docker logs test-backend

# Test API
curl http://localhost:8001/api/

# Cleanup
docker rm -f test-backend
```

### Test with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# Test backend
curl http://localhost:8001/api/

# View logs
docker-compose logs backend

# Stop
docker-compose down
```

---

## 🚀 Production Deployment

### Best Practices

1. **Use production image**
   ```bash
   catalyst-backend:production
   ```

2. **Set resource limits**
   ```bash
   docker run -d \
     --memory=\"2g\" \
     --cpus=\"2\" \
     --memory-swap=\"2g\" \
     catalyst-backend:production
   ```

3. **Configure restart policy**
   ```bash
   docker run -d \
     --restart unless-stopped \
     catalyst-backend:production
   ```

4. **Use health checks**
   ```bash
   --health-cmd=\"curl -f http://localhost:8001/api/ || exit 1\"
   --health-interval=30s
   --health-timeout=10s
   --health-retries=3
   ```

5. **Mount logs volume**
   ```bash
   docker run -d \
     -v /var/log/catalyst:/app/backend/logs \
     catalyst-backend:production
   ```

6. **Use secrets management**
   ```bash
   # Docker secrets (Swarm)
   echo \"sk-emergent-xxxxx\" | docker secret create llm_key -
   
   docker service create \
     --name catalyst-backend \
     --secret llm_key \
     catalyst-backend:production
   ```

### Docker Swarm Deployment

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml catalyst

# Check services
docker stack services catalyst

# Scale backend
docker service scale catalyst_backend=3

# Update service
docker service update --image catalyst-backend:1.0.1 catalyst_backend
```

### Kubernetes Deployment

See `kubernetes/backend-deployment.yaml` for K8s manifests.

---

## 🔄 Updating & Maintenance

### Update Image

```bash
# Rebuild image
docker build -f Dockerfile.backend.prod -t catalyst-backend:1.0.1 .

# Stop old container
docker stop catalyst-backend

# Remove old container
docker rm catalyst-backend

# Start new container
docker run -d \
  --name catalyst-backend \
  --env-file backend/.env \
  -p 8001:8001 \
  catalyst-backend:1.0.1
```

### Zero-Downtime Update (Docker Compose)

```bash
# Pull/build new image
docker-compose build backend

# Rolling update
docker-compose up -d --no-deps --build backend
```

### Cleanup Old Images

```bash
# Remove unused images
docker image prune -a

# Remove specific old version
docker rmi catalyst-backend:1.0.0
```

---

## 🐛 Troubleshooting

### Image Won't Build

**Error:** `failed to solve`

**Solution:**
```bash
# Clear build cache
docker builder prune -a

# Rebuild without cache
docker build --no-cache -f Dockerfile.backend.prod -t catalyst-backend:latest .
```

### Container Exits Immediately

**Check logs:**
```bash
docker logs catalyst-backend
```

**Common causes:**
- Missing environment variables
- MongoDB not accessible
- Invalid EMERGENT_LLM_KEY

**Solution:**
```bash
# Verify environment
docker run --rm catalyst-backend:latest env | grep MONGO_URL

# Test MongoDB connection
docker run --rm --link catalyst-mongodb:mongodb catalyst-backend:latest \
  python3 -c \"from pymongo import MongoClient; print(MongoClient('mongodb://mongodb:27017').server_info())\"
```

### High Memory Usage

**Check stats:**
```bash
docker stats catalyst-backend
```

**Solution:**
```bash
# Set memory limit
docker update --memory=\"1g\" catalyst-backend

# Or restart with limit
docker run -d --memory=\"1g\" catalyst-backend:latest
```

### Slow Startup

**Increase health check grace period:**
```bash
docker run -d \
  --health-start-period=60s \
  catalyst-backend:latest
```

---

## 📚 Additional Resources

- **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices/
- **Multi-stage Builds**: https://docs.docker.com/build/building/multi-stage/
- **Docker Compose**: https://docs.docker.com/compose/
- **Dockerfile Reference**: https://docs.docker.com/engine/reference/builder/

---

**Docker Guide Version**: 1.0.0  
**Last Updated**: October 2025  
**Platform Version**: 1.0.0
