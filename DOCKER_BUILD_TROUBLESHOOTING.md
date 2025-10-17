# Docker Build Error Troubleshooting

## Common Error: "failed to compute cache key: failed to calculate checksum"

This error typically occurs when Docker can't find files referenced in COPY commands.

### Quick Fix

**Use the correct build commands**:

```bash
# ✅ CORRECT - Using docker-compose (Recommended)
docker-compose -f docker-compose.artifactory.yml build
docker-compose -f docker-compose.artifactory.yml up -d

# ✅ CORRECT - Using Makefile
make build-artifactory
make start-artifactory

# ✅ CORRECT - Manual build with proper context
cd backend
docker build -f ../Dockerfile.backend.artifactory -t catalyst-backend .

cd ../frontend
docker build -f ../Dockerfile.frontend.artifactory -t catalyst-frontend .
```

---

## Understanding the Error

### Root Cause

The error happens when:
1. Build context doesn't contain expected files
2. COPY paths don't match actual file locations
3. Working directory is incorrect

### Example Error
```
failed to compute cache key: failed to calculate checksum of ref
"/backend/requirements.txt": not found
```

---

## Solution Methods

### Method 1: Use Docker Compose (Easiest)

**docker-compose.artifactory.yml is configured correctly**:

```yaml
backend:
  build:
    context: ./backend          # ✅ Build from backend directory
    dockerfile: ../Dockerfile.backend.artifactory

frontend:
  build:
    context: ./frontend         # ✅ Build from frontend directory
    dockerfile: ../Dockerfile.frontend.artifactory
```

**Command**:
```bash
docker-compose -f docker-compose.artifactory.yml up -d --build
```

---

### Method 2: Use Makefile

**Commands configured correctly**:
```bash
make setup-artifactory    # Setup everything
make build-artifactory    # Just build images
make start-artifactory    # Build and start
```

---

### Method 3: Manual Build

**Backend**:
```bash
# Navigate to backend directory
cd /app/backend

# Build with Dockerfile from parent
docker build -f ../Dockerfile.backend.artifactory -t catalyst-backend:latest .

# Verify
docker images | grep catalyst-backend
```

**Frontend**:
```bash
# Navigate to frontend directory
cd /app/frontend

# Build with Dockerfile from parent
docker build -f ../Dockerfile.frontend.artifactory -t catalyst-frontend:latest .

# Verify
docker images | grep catalyst-frontend
```

---

## Verification Steps

### 1. Check File Structure

```bash
# From /app directory
ls -la

# Should see:
# backend/
# frontend/
# Dockerfile.backend.artifactory
# Dockerfile.frontend.artifactory
# docker-compose.artifactory.yml
```

### 2. Verify Backend Files

```bash
cd backend
ls -la

# Should see:
# requirements.txt
# requirements-langgraph.txt
# server.py
# agents/
# ... other files
```

### 3. Verify Frontend Files

```bash
cd frontend
ls -la

# Should see:
# package.json
# yarn.lock
# src/
# public/
# ... other files
```

### 4. Test Build Context

```bash
# Test backend
cd /app/backend
docker build -f ../Dockerfile.backend.artifactory --no-cache -t test-backend .

# Test frontend
cd /app/frontend
docker build -f ../Dockerfile.frontend.artifactory --no-cache -t test-frontend .
```

---

## Common Mistakes

### ❌ Wrong: Building from root with wrong paths

```bash
# DON'T DO THIS
cd /app
docker build -f Dockerfile.backend.artifactory -t catalyst-backend .
# Error: Can't find backend/requirements.txt
```

### ✅ Correct: Use docker-compose or proper context

```bash
# DO THIS
docker-compose -f docker-compose.artifactory.yml build

# OR
cd backend && docker build -f ../Dockerfile.backend.artifactory .
```

---

## Dockerfile Explanation

### Backend Dockerfile Structure

```dockerfile
# Build context is /app/backend/
FROM artifactory.devtools.syd.c1.macquarie.com:9996/python:3.11-slim

WORKDIR /app

# ✅ Files are in current context (backend/)
COPY requirements.txt requirements-langgraph.txt ./
# Copies from /app/backend/requirements.txt

# ✅ Copy all backend code
COPY . /app/
# Copies from /app/backend/ to /app/ in container
```

### Frontend Dockerfile Structure

```dockerfile
# Build context is /app/frontend/
FROM artifactory.devtools.syd.c1.macquarie.com:9996/node:18-alpine

WORKDIR /app

# ✅ Files are in current context (frontend/)
COPY package.json yarn.lock ./
# Copies from /app/frontend/package.json

# ✅ Copy all frontend code
COPY . ./
# Copies from /app/frontend/ to /app/ in container
```

---

## Alternative: If You Still Get Errors

### Option 1: Use Standard Dockerfiles

The standard Dockerfiles work with root context:

```bash
# Use standard docker-compose
docker-compose up -d --build

# OR use standard Dockerfiles
docker build -f Dockerfile.backend -t catalyst-backend .
docker build -f Dockerfile.frontend -t catalyst-frontend .
```

### Option 2: Rebuild from Scratch

```bash
# Clean everything
docker-compose -f docker-compose.artifactory.yml down -v
docker system prune -a

# Rebuild
docker-compose -f docker-compose.artifactory.yml build --no-cache
docker-compose -f docker-compose.artifactory.yml up -d
```

### Option 3: Check Docker BuildKit

```bash
# Disable BuildKit if causing issues
export DOCKER_BUILDKIT=0

# Then build
docker-compose -f docker-compose.artifactory.yml build

# Re-enable after (optional)
export DOCKER_BUILDKIT=1
```

---

## Complete Working Example

### Step-by-Step Build

```bash
# 1. Ensure you're in project root
cd /app

# 2. Verify structure
ls -la backend/requirements.txt
ls -la frontend/package.json

# 3. Build using docker-compose
docker-compose -f docker-compose.artifactory.yml build --progress=plain

# 4. Check for errors in output

# 5. If successful, start services
docker-compose -f docker-compose.artifactory.yml up -d

# 6. Verify running
docker-compose -f docker-compose.artifactory.yml ps
```

### Expected Output

```
✓ Building backend
✓ Building frontend
✓ Container catalyst-mongodb    Started
✓ Container catalyst-backend    Started
✓ Container catalyst-frontend   Started
```

---

## Debug Mode

### Build with Full Output

```bash
# See all build steps
docker-compose -f docker-compose.artifactory.yml build --progress=plain --no-cache

# Check specific service
docker-compose -f docker-compose.artifactory.yml build --progress=plain backend
```

### Inspect Build Context

```bash
# See what Docker sends to build
cd backend
docker build -f ../Dockerfile.backend.artifactory --no-cache -t test . 2>&1 | head -20
```

---

## Still Having Issues?

### 1. Check Artifactory Connectivity

```bash
# Test connection
curl -I https://artifactory.devtools.syd.c1.macquarie.com:9996

# Login if needed
docker login artifactory.devtools.syd.c1.macquarie.com:9996
```

### 2. Use Standard Docker Hub Images

```bash
# Temporarily use standard docker-compose
docker-compose up -d --build
```

### 3. Check Logs

```bash
# Docker build logs
docker-compose -f docker-compose.artifactory.yml logs backend
docker-compose -f docker-compose.artifactory.yml logs frontend
```

---

## Summary

**✅ Recommended Method**:
```bash
make setup-artifactory
make start-artifactory
```

**✅ Alternative**:
```bash
docker-compose -f docker-compose.artifactory.yml up -d --build
```

**✅ Manual Build**:
```bash
cd backend && docker build -f ../Dockerfile.backend.artifactory .
cd ../frontend && docker build -f ../Dockerfile.frontend.artifactory .
```

**❌ Don't Do**:
```bash
# Wrong context
docker build -f Dockerfile.backend.artifactory .
```

---

**The key is using the correct build context!** 🎯
