# Quick Fix for "failed to compute cache key" Error

## Immediate Solution

Run these commands to fix the error:

```bash
# 1. Ensure nginx.conf is in frontend directory
cp nginx.conf frontend/nginx.conf

# 2. Clean Docker cache
docker system prune -af

# 3. Build with Artifactory
docker-compose -f docker-compose.artifactory.yml build --no-cache

# 4. Start services
docker-compose -f docker-compose.artifactory.yml up -d
```

## Or Use Makefile

```bash
# Automated fix
make clean-all
make setup-artifactory
make start-artifactory
```

---

## Understanding the Error

### The Problem

When Docker builds with `context: ./frontend`, it can only see files inside the `frontend/` directory. If the Dockerfile tries to COPY files from outside this directory, it fails.

**Example**:
```yaml
# docker-compose.artifactory.yml
frontend:
  build:
    context: ./frontend  # Docker can ONLY see files in frontend/
    dockerfile: ../Dockerfile.frontend.artifactory
```

```dockerfile
# Dockerfile.frontend.artifactory
COPY nginx.conf /etc/nginx/nginx.conf
# ❌ Fails if nginx.conf is in parent directory
# ✅ Works if nginx.conf is in frontend/ directory
```

---

## Complete Fix Steps

### Step 1: Verify File Locations

```bash
# Check if nginx.conf is in frontend directory
ls -la /app/frontend/nginx.conf

# If not found, copy it
cp /app/nginx.conf /app/frontend/nginx.conf
```

### Step 2: Verify requirements.txt in backend

```bash
# Check backend files
ls -la /app/backend/requirements.txt
ls -la /app/backend/requirements-langgraph.txt
```

### Step 3: Clean Docker Environment

```bash
# Remove old builds
docker-compose -f docker-compose.artifactory.yml down -v

# Clean Docker system
docker system prune -af
```

### Step 4: Build with No Cache

```bash
# Build from scratch
docker-compose -f docker-compose.artifactory.yml build --no-cache --progress=plain

# Watch for errors in output
```

### Step 5: Start Services

```bash
# Start everything
docker-compose -f docker-compose.artifactory.yml up -d

# Check status
docker-compose -f docker-compose.artifactory.yml ps
```

---

## Verify Build Context

### Test Backend Build

```bash
cd /app/backend

# List files Docker will see
ls -la

# Should show:
# requirements.txt ✓
# requirements-langgraph.txt ✓
# server.py ✓
# agents/ ✓

# Try build
docker build -f ../Dockerfile.backend.artifactory -t test-backend . --progress=plain
```

### Test Frontend Build

```bash
cd /app/frontend

# List files Docker will see
ls -la

# Should show:
# package.json ✓
# yarn.lock ✓
# nginx.conf ✓
# src/ ✓
# public/ ✓

# Try build
docker build -f ../Dockerfile.frontend.artifactory -t test-frontend . --progress=plain
```

---

## Common File Missing Errors

### Error: "nginx.conf: not found"

**Fix**:
```bash
cp /app/nginx.conf /app/frontend/nginx.conf
```

### Error: "requirements.txt: not found"

**Fix**:
```bash
# Verify it exists
ls -la /app/backend/requirements.txt

# If missing, check you're in the right directory
cd /app
ls -la backend/
```

### Error: "package.json: not found"

**Fix**:
```bash
# Verify it exists
ls -la /app/frontend/package.json

# If missing, check location
cd /app
ls -la frontend/
```

---

## Alternative: Use Root Context

If you keep having issues, modify docker-compose to use root context:

### Create New File: docker-compose.artifactory-root.yml

```yaml
version: '3.8'

services:
  mongodb:
    image: artifactory.devtools.syd.c1.macquarie.com:9996/mongo:5.0
    container_name: catalyst-mongo
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: catalyst_admin_pass
    volumes:
      - mongodb_data:/data/db
    networks:
      - catalyst-network

  backend:
    build:
      context: .                    # Root context
      dockerfile: Dockerfile.backend.artifactory.root
    container_name: catalyst-backend
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://admin:catalyst_admin_pass@mongodb:27017
      - DB_NAME=catalyst_db
      - EMERGENT_LLM_KEY=sk-emergent-b14E29723DeDaF2A74
      - DEFAULT_LLM_PROVIDER=emergent
    depends_on:
      - mongodb
    networks:
      - catalyst-network

  frontend:
    build:
      context: .                    # Root context
      dockerfile: Dockerfile.frontend.artifactory.root
    container_name: catalyst-frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - catalyst-network

networks:
  catalyst-network:
    driver: bridge

volumes:
  mongodb_data:
    driver: local
```

### Update Dockerfiles for Root Context

**Backend** (with root context):
```dockerfile
FROM artifactory.devtools.syd.c1.macquarie.com:9996/python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements-langgraph.txt ./
RUN pip install -r requirements.txt -r requirements-langgraph.txt
COPY backend/ ./
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## Debug Commands

### Check What Docker Sees

```bash
# Show build context for backend
cd /app/backend
find . -maxdepth 2 -type f

# Show build context for frontend
cd /app/frontend
find . -maxdepth 2 -type f
```

### Verbose Build Output

```bash
# See every step
docker-compose -f docker-compose.artifactory.yml build --progress=plain 2>&1 | tee build.log

# Check log for exact error
grep -i "failed" build.log
grep -i "not found" build.log
```

### Test Artifactory Connection

```bash
# Check if you can pull images
docker pull artifactory.devtools.syd.c1.macquarie.com:9996/python:3.11-slim

# If auth required
docker login artifactory.devtools.syd.c1.macquarie.com:9996
```

---

## Working Configuration

### Current Setup

```
/app/
├── backend/
│   ├── requirements.txt          ✓ In place
│   ├── requirements-langgraph.txt ✓ In place
│   ├── server.py                  ✓ In place
│   └── ... other files
│
├── frontend/
│   ├── package.json              ✓ In place
│   ├── yarn.lock                 ✓ In place
│   ├── nginx.conf                ✓ MUST be here
│   ├── src/                      ✓ In place
│   └── ... other files
│
├── Dockerfile.backend.artifactory    ✓ Updated
├── Dockerfile.frontend.artifactory   ✓ Updated
└── docker-compose.artifactory.yml    ✓ Correct contexts
```

---

## Success Checklist

Before building, verify:

- [ ] `/app/backend/requirements.txt` exists
- [ ] `/app/backend/requirements-langgraph.txt` exists
- [ ] `/app/frontend/package.json` exists
- [ ] `/app/frontend/yarn.lock` exists
- [ ] `/app/frontend/nginx.conf` exists ⭐ CRITICAL
- [ ] Can reach Artifactory: `ping artifactory.devtools.syd.c1.macquarie.com`
- [ ] Docker is running: `docker info`
- [ ] No old containers: `docker-compose -f docker-compose.artifactory.yml down -v`

---

## Final Working Commands

```bash
# Complete working process
cd /app

# 1. Ensure nginx.conf is copied
cp nginx.conf frontend/nginx.conf 2>/dev/null || echo "Already exists"

# 2. Clean everything
docker-compose -f docker-compose.artifactory.yml down -v
docker system prune -af

# 3. Build fresh
docker-compose -f docker-compose.artifactory.yml build --no-cache

# 4. Start services
docker-compose -f docker-compose.artifactory.yml up -d

# 5. Check status
docker-compose -f docker-compose.artifactory.yml ps

# 6. View logs if needed
docker-compose -f docker-compose.artifactory.yml logs -f
```

---

## Still Not Working?

### Option 1: Use Standard Images (Docker Hub)

```bash
# Use standard docker-compose without Artifactory
docker-compose up -d --build
```

### Option 2: Build Manually

```bash
# Backend
cd /app/backend
docker build -f ../Dockerfile.backend.artifactory -t catalyst-backend .

# Frontend
cd /app/frontend
docker build -f ../Dockerfile.frontend.artifactory -t catalyst-frontend .

# MongoDB
docker run -d --name catalyst-mongo \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=catalyst_admin_pass \
  -p 27017:27017 \
  artifactory.devtools.syd.c1.macquarie.com:9996/mongo:5.0
```

### Option 3: Contact Support

Provide these details:
```bash
# System info
docker --version
docker-compose --version
uname -a

# Error details
docker-compose -f docker-compose.artifactory.yml build 2>&1 | head -50

# File structure
ls -la /app/
ls -la /app/backend/
ls -la /app/frontend/
```

---

**The key fix: Ensure nginx.conf is in frontend/ directory!** 🎯

```bash
cp nginx.conf frontend/nginx.conf
```
