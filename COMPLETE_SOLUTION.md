# COMPLETE SOLUTION - Artifactory Build Issues

## 🚨 If You're Getting Build Errors, Run This:

```bash
./complete-fix.sh
```

This handles **ALL** common issues automatically.

---

## Manual Fix (If Script Doesn't Work)

### Step 1: Ensure All Files Are in Place

```bash
# Check backend files
ls -la backend/requirements.txt
ls -la backend/requirements-langgraph.txt

# Check frontend files
ls -la frontend/package.json
ls -la frontend/yarn.lock

# Copy nginx.conf if needed
cp nginx.conf frontend/nginx.conf 2>/dev/null || echo "Already exists"
```

### Step 2: Login to Artifactory

```bash
docker login artifactory.devtools.syd.c1.macquarie.com:9996
# Enter your credentials
```

### Step 3: Clean Everything

```bash
# Stop containers
docker-compose -f docker-compose.artifactory.yml down -v

# Clean Docker cache (important!)
docker system prune -af
docker builder prune -af
```

### Step 4: Build Fresh (No Cache)

```bash
# Build with no cache and plain progress
DOCKER_BUILDKIT=1 docker-compose -f docker-compose.artifactory.yml build --no-cache --progress=plain
```

### Step 5: Start Services

```bash
docker-compose -f docker-compose.artifactory.yml up -d
```

---

## Common Errors and Fixes

### Error: "failed to compute cache key: /requirements-langgraph.txt"

**Cause**: Docker can't find the file in the build context

**Fix**:
```bash
# Verify file exists
ls -la backend/requirements-langgraph.txt

# Clean Docker cache
docker builder prune -af

# Rebuild
cd backend
docker build -f ../Dockerfile.backend.artifactory -t test-backend . --no-cache

# If successful, use docker-compose
cd ..
docker-compose -f docker-compose.artifactory.yml up -d --build
```

### Error: "failed to compute cache key: /nginx.conf"

**Fix**:
```bash
# Copy nginx.conf to frontend
cp nginx.conf frontend/nginx.conf

# Verify
ls -la frontend/nginx.conf

# Rebuild
docker-compose -f docker-compose.artifactory.yml build --no-cache
```

### Error: "failed to solve with frontend"

**Fix**:
```bash
# Test frontend build manually
cd frontend
ls -la package.json yarn.lock nginx.conf

# Build
docker build -f ../Dockerfile.frontend.artifactory -t test-frontend . --no-cache --progress=plain

# Check for specific errors in output
```

### Error: "unauthorized" or "denied: access forbidden"

**Fix**:
```bash
# Login to Artifactory
docker login artifactory.devtools.syd.c1.macquarie.com:9996

# Pull test image
docker pull artifactory.devtools.syd.c1.macquarie.com:9996/python:3.11-slim
```

---

## Verification Checklist

Before building, verify:

```bash
# 1. Check all required files exist
echo "Checking backend..."
[ -f backend/requirements.txt ] && echo "✓ requirements.txt" || echo "✗ requirements.txt MISSING"
[ -f backend/requirements-langgraph.txt ] && echo "✓ requirements-langgraph.txt" || echo "✗ requirements-langgraph.txt MISSING"
[ -f backend/server.py ] && echo "✓ server.py" || echo "✗ server.py MISSING"

echo "Checking frontend..."
[ -f frontend/package.json ] && echo "✓ package.json" || echo "✗ package.json MISSING"
[ -f frontend/yarn.lock ] && echo "✓ yarn.lock" || echo "✗ yarn.lock MISSING"
[ -f frontend/nginx.conf ] && echo "✓ nginx.conf" || echo "✗ nginx.conf MISSING"

# 2. Test Artifactory connectivity
ping -c 1 artifactory.devtools.syd.c1.macquarie.com && echo "✓ Can reach Artifactory" || echo "✗ Cannot reach Artifactory (VPN?)"

# 3. Test Docker login
docker pull artifactory.devtools.syd.c1.macquarie.com:9996/python:3.11-slim && echo "✓ Can pull images" || echo "✗ Need to login"
```

---

## Debug Mode

### See Exactly What's Failing

```bash
# Build with full output
docker-compose -f docker-compose.artifactory.yml build --progress=plain 2>&1 | tee build-debug.log

# Search for errors
grep -i "error\|failed\|not found" build-debug.log

# Check specific service
docker-compose -f docker-compose.artifactory.yml build backend --progress=plain
docker-compose -f docker-compose.artifactory.yml build frontend --progress=plain
```

### Test Individual Builds

```bash
# Test backend manually
cd /app/backend
echo "Files in build context:"
ls -la
echo ""
echo "Building..."
docker build -f ../Dockerfile.backend.artifactory -t test-backend . --no-cache

# Test frontend manually
cd /app/frontend
echo "Files in build context:"
ls -la
echo ""
echo "Building..."
docker build -f ../Dockerfile.frontend.artifactory -t test-frontend . --no-cache
```

---

## Alternative: Use Standard Docker Hub

If Artifactory keeps failing, use standard images temporarily:

```bash
# Use regular docker-compose
docker-compose up -d --build

# Access same endpoints
# Frontend: http://localhost:3000
# Backend:  http://localhost:8001/api
```

---

## File Structure Reference

Your files should be organized like this:

```
/app/
├── backend/
│   ├── requirements.txt              ← Must exist here
│   ├── requirements-langgraph.txt    ← Must exist here
│   ├── server.py                     ← Must exist here
│   ├── agents/
│   ├── chat_interface/
│   └── ...
│
├── frontend/
│   ├── package.json                  ← Must exist here
│   ├── yarn.lock                     ← Must exist here
│   ├── nginx.conf                    ← Must exist here (copy from root)
│   ├── src/
│   ├── public/
│   └── ...
│
├── Dockerfile.backend.artifactory
├── Dockerfile.frontend.artifactory
├── docker-compose.artifactory.yml
├── complete-fix.sh                   ← Run this!
└── nginx.conf                        ← Original (keep it)
```

---

## Complete Working Commands

### Option 1: Automated Script (Best)

```bash
./complete-fix.sh
```

### Option 2: Manual Step-by-Step

```bash
# 1. Prepare files
cp nginx.conf frontend/nginx.conf

# 2. Login to Artifactory
docker login artifactory.devtools.syd.c1.macquarie.com:9996

# 3. Clean everything
docker-compose -f docker-compose.artifactory.yml down -v
docker system prune -af
docker builder prune -af

# 4. Build
DOCKER_BUILDKIT=1 docker-compose -f docker-compose.artifactory.yml build --no-cache

# 5. Start
docker-compose -f docker-compose.artifactory.yml up -d

# 6. Check status
docker-compose -f docker-compose.artifactory.yml ps
docker-compose -f docker-compose.artifactory.yml logs -f
```

### Option 3: One-Line Fix

```bash
cp nginx.conf frontend/nginx.conf && docker system prune -af && docker-compose -f docker-compose.artifactory.yml up -d --build --force-recreate
```

---

## Expected Output (Success)

When build succeeds, you should see:

```
✓ Building backend
✓ Building frontend
✓ Container catalyst-mongodb   Started
✓ Container catalyst-backend   Started
✓ Container catalyst-frontend  Started
```

Test endpoints:
```bash
curl http://localhost:8001/api/
# Should return: {"message":"Catalyst AI Platform API","version":"1.0.0"}

curl http://localhost:3000/
# Should return HTML content
```

---

## Still Having Issues?

### Collect Debug Information

```bash
# Run this and share the output
echo "=== System Info ==="
docker --version
docker-compose --version
uname -a

echo "=== File Check ==="
ls -la backend/requirements*.txt
ls -la frontend/package.json frontend/nginx.conf

echo "=== Network Check ==="
ping -c 2 artifactory.devtools.syd.c1.macquarie.com

echo "=== Docker Check ==="
docker info | grep -i "Server Version\|Operating System"

echo "=== Build Attempt ==="
docker-compose -f docker-compose.artifactory.yml build --no-cache 2>&1 | head -100
```

### Contact Support With

1. Output from debug commands above
2. Content of `build-debug.log` (if created)
3. Exact error message
4. Which step failed

---

## Quick Reference

| Problem | Solution |
|---------|----------|
| Missing nginx.conf | `cp nginx.conf frontend/nginx.conf` |
| Can't reach Artifactory | Check VPN connection |
| Authentication error | `docker login artifactory.devtools.syd.c1.macquarie.com:9996` |
| Build cache issues | `docker builder prune -af` |
| Any other error | `./complete-fix.sh` |

---

**🎯 Run `./complete-fix.sh` for automatic fix of all issues!**
