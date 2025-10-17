# Yarn Install Still Failing - Comprehensive Debug Guide

## Current Status
After multiple fixes, yarn install is still failing with exit code 1.

## What We've Fixed So Far
1. ✅ Build context: `.` → `./frontend`
2. ✅ Alpine SSL: HTTP repos + ca-certificates
3. ✅ Yarn SSL: strict-ssl false
4. ✅ NPM SSL: strict-ssl false
5. ✅ Invalid flag: Removed `--disable-ssl`
6. ✅ Timeouts: Increased to 600s
7. ✅ Concurrency: Limited to 1

## Next Steps to Debug

### Option 1: Use Debug Dockerfile (Recommended)

We've created a simplified debug version with extensive logging:

```bash
# Update docker-compose to use debug Dockerfile
cd /app
sed -i 's|dockerfile: ../Dockerfile.frontend.artifactory|dockerfile: ../Dockerfile.frontend.artifactory.debug|' docker-compose.artifactory.yml

# Build with full output
docker-compose -f docker-compose.artifactory.yml build --no-cache --progress=plain frontend 2>&1 | tee debug-build.log

# Check the log
cat debug-build.log | grep -A 20 "yarn install"
```

**Debug Dockerfile features:**
- Uses HTTP registry (not HTTPS)
- Sets NODE_TLS_REJECT_UNAUTHORIZED=0
- Tests registry accessibility with curl
- Verbose output from yarn
- No frozen-lockfile (more forgiving)
- Shows package.json content
- Adds extra logging at each step

### Option 2: Test Yarn Install Manually

```bash
# Run container interactively
docker run --rm -it --entrypoint sh \
  -v /app/frontend:/workspace \
  -w /workspace \
  artifactory.devtools.syd.c1.macquarie.com:9996/node:18-alpine

# Inside container, run these commands:
apk add --update --no-check-certificate --no-cache ca-certificates python3 make g++ git
export NODE_TLS_REJECT_UNAUTHORIZED=0
yarn config set registry http://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/
yarn config set strict-ssl false
yarn config list

# Try to install
yarn install --verbose

# If that fails, check what the actual error is
```

### Option 3: Check Artifactory Registry Accessibility

```bash
# Test if registry is accessible
curl -I http://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/

# Should return HTTP 200 or 30x redirect

# Test if you can fetch a specific package
curl http://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/react

# Should return package metadata JSON
```

### Option 4: Try Different Registry Approaches

#### A. Use Public NPM Temporarily (to isolate issue)
```dockerfile
# In Dockerfile, change registry to:
RUN yarn config set registry https://registry.npmjs.org/
```

If this works, the issue is Artifactory configuration/access.

#### B. Use HTTP Instead of HTTPS for Registry
```dockerfile
# Change to HTTP (already in debug version)
RUN yarn config set registry http://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/
```

#### C. Check if Authentication is Required
```bash
# Try with authentication
docker run --rm -it artifactory.../node:18-alpine sh
yarn config set registry http://artifactory...
yarn config set username YOUR_USERNAME
yarn config set password YOUR_PASSWORD
yarn install
```

### Option 5: Check Package.json Issues

```bash
# Validate package.json
cd /app/frontend
node -e "JSON.parse(require('fs').readFileSync('package.json'))"

# Check for problematic dependencies
cat package.json | grep -i "git+" # Check for git dependencies
cat package.json | grep "@" | head -20 # Check dependency versions
```

### Option 6: Try Without Frozen Lockfile

```dockerfile
# Remove --frozen-lockfile temporarily
RUN yarn install \
    --network-timeout 600000 \
    --network-concurrency 1
```

This allows yarn to regenerate yarn.lock if needed.

### Option 7: Use Standard Node Image

```dockerfile
# Try without Artifactory base image
FROM node:18-alpine as builder

# Then configure Artifactory as registry
RUN yarn config set registry http://artifactory...
```

## Common Root Causes

### 1. Artifactory Not Accessible
**Symptom**: Connection timeouts, ENOTFOUND errors
**Solution**: Check network, VPN, firewall rules

### 2. Artifactory Requires Authentication
**Symptom**: 401 Unauthorized, 403 Forbidden
**Solution**: Add authentication to .npmrc or yarn config

### 3. Artifactory NPM Proxy Not Configured
**Symptom**: Packages not found, 404 errors
**Solution**: Verify Artifactory has npm-virtual repository configured

### 4. Corrupt yarn.lock
**Symptom**: Dependency resolution errors
**Solution**: Delete yarn.lock and regenerate

### 5. Network/Proxy Issues
**Symptom**: Timeouts, connection resets
**Solution**: Configure proxy, use --network=host

### 6. Package.json Syntax Errors
**Symptom**: Parse errors
**Solution**: Validate JSON syntax

## Diagnostic Commands

### Inside Docker Container
```bash
# Check yarn configuration
yarn config list

# Check registry accessibility
curl http://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/

# Check DNS resolution
nslookup artifactory.devtools.syd.c1.macquarie.com

# Check network connectivity
ping -c 3 artifactory.devtools.syd.c1.macquarie.com

# Try yarn with extreme verbosity
yarn install --verbose --frozen-lockfile 2>&1 | tee install.log

# Check what's failing
tail -100 install.log
```

### On Host Machine
```bash
# Test Artifactory access
curl -I http://artifactory.devtools.syd.c1.macquarie.com:9996/

# Check if packages are cached
curl http://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/react | jq

# Check for authentication requirements
curl -v http://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/ 2>&1 | grep -i auth
```

## Emergency Fallbacks

### Fallback 1: Use Public NPM (No Artifactory)
```bash
# Edit docker-compose to use standard Dockerfile
sed -i 's|dockerfile: ../Dockerfile.frontend.artifactory|dockerfile: ../Dockerfile.frontend.standard|' docker-compose.artifactory.yml

# Build
docker-compose -f docker-compose.artifactory.yml build frontend
```

### Fallback 2: Build Locally, Copy to Docker
```bash
# Install on host
cd /app/frontend
yarn install

# Copy node_modules to Docker
# Add to Dockerfile:
COPY node_modules ./node_modules
```

### Fallback 3: Use Pre-built Image
```bash
# Build image elsewhere and import
docker save frontend:latest | docker load
```

## Request More Information

To help debug further, please provide:

1. **Full error output** from docker build
   ```bash
   docker-compose -f docker-compose.artifactory.yml build frontend 2>&1 | tail -100
   ```

2. **Yarn verbose output** 
   ```bash
   # Look for lines with "error:", "ERR!", or stack traces
   ```

3. **Registry accessibility test**
   ```bash
   curl -v http://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/ 2>&1
   ```

4. **Package.json dependencies count**
   ```bash
   cat /app/frontend/package.json | grep -c "^\s*\""
   ```

## Files to Try

1. **Dockerfile.frontend.artifactory.debug** - Most verbose, HTTP only
2. **Dockerfile.frontend.artifactory** - Current with enhanced logging
3. **Dockerfile.frontend.artifactory.alt** - Alternative retry logic
4. **Dockerfile.frontend.standard** - Public NPM (fallback)

## Quick Commands

```bash
# Try debug version
cd /app
sed -i 's|dockerfile: ../Dockerfile.frontend.artifactory|dockerfile: ../Dockerfile.frontend.artifactory.debug|' docker-compose.artifactory.yml
docker-compose -f docker-compose.artifactory.yml build --progress=plain frontend 2>&1 | tee debug.log

# Check specific errors
grep -i "error\|err\|fail" debug.log | tail -20

# Check registry config
grep "registry" debug.log

# Check yarn output
grep "yarn install" debug.log -A 30
```

## What to Look For in Logs

1. **"ENOTFOUND"** - DNS/network issue
2. **"ETIMEDOUT"** - Network timeout
3. **"401" / "403"** - Authentication required
4. **"404"** - Package not found in registry
5. **"ECONNREFUSED"** - Registry not accessible
6. **"certificate"** - SSL still causing issues
7. **"Parse error"** - package.json syntax issue
8. **"integrity check failed"** - Corrupted cache/download

## Next Action

**Please run the debug build and share the output:**
```bash
cd /app
# Use debug Dockerfile
docker build -f Dockerfile.frontend.artifactory.debug --no-cache --progress=plain /app/frontend 2>&1 | tee full-debug.log

# Share last 200 lines
tail -200 full-debug.log
```

This will give us the actual error message to work with.
