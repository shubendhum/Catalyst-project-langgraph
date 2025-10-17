# Artifactory NPM Registry Configuration - Complete Guide

## Problem
Yarn is using local/public npm registry links instead of going through Artifactory.

**Symptoms**:
- Build logs show `https://registry.npmjs.org/...` instead of Artifactory URL
- Packages downloaded from public npm instead of internal mirror
- Build may fail if public npm is blocked by firewall
- Build doesn't use cached packages in Artifactory

## Solution Overview

Configure npm/yarn to use Artifactory's npm registry proxy instead of the default public registry.

**Artifactory NPM Registry URL**:
```
https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/
```

## ✅ Quick Fix (Method 1: Inline Configuration)

### Already Applied!

The main Dockerfile (`Dockerfile.frontend.artifactory`) has been updated to configure the registry inline:

```dockerfile
# Configure yarn/npm to use Artifactory registry
RUN yarn config set registry https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/ && \
    npm config set registry https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/ && \
    yarn config list
```

### Build Now
```bash
docker-compose -f docker-compose.artifactory.yml build frontend
```

### Verify It's Using Artifactory
Check the build output - you should see:
```
info npm registry: https://artifactory.devtools.syd.c1.macquarie.com:9996/...
```

---

## Method 2: Using Configuration Files (.npmrc / .yarnrc)

### When to Use
- When you need authentication
- For local development consistency
- When managing multiple registries
- For better control over registry settings

### Step 1: Create Configuration Files

**Option A: No Authentication (Simple)**
```bash
cd /app/frontend

# Copy template files
cp .npmrc.artifactory .npmrc
cp .yarnrc.artifactory .yarnrc
```

**Option B: With Authentication**
```bash
cd /app/frontend

# Create .npmrc with auth token
cat > .npmrc << EOF
registry=https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/
//artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/:_authToken=YOUR_TOKEN_HERE
always-auth=true
fetch-timeout=300000
EOF

# Create .yarnrc
cat > .yarnrc << EOF
registry "https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/"
network-timeout 300000
EOF
```

### Step 2: Update Docker Compose

Change the Dockerfile to use config files:

```yaml
# docker-compose.artifactory.yml
frontend:
  build:
    context: ./frontend
    dockerfile: ../Dockerfile.frontend.artifactory.withconfig  # ← Changed
```

### Step 3: Build
```bash
docker-compose -f docker-compose.artifactory.yml build frontend
```

---

## Method 3: Using Interactive Configuration Script

```bash
/app/configure-artifactory-registry.sh
```

This script will:
1. Ask if you need authentication
2. Create appropriate config files
3. Update docker-compose.artifactory.yml
4. Provide verification steps

---

## Authentication Methods

### Method 1: Auth Token (Recommended)

**Get Token from Artifactory**:
1. Login to Artifactory web UI
2. Click your username → Edit Profile → Generate API Key
3. Use this token in .npmrc

**Configure**:
```bash
# .npmrc
registry=https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/
//artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/:_authToken=YOUR_TOKEN
always-auth=true
```

### Method 2: Username/Password (Base64)

```bash
# Generate base64 auth
echo -n "username:password" | base64

# Add to .npmrc
//artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/:_auth=BASE64_STRING
```

### Method 3: Environment Variables

```bash
# In Dockerfile
ARG NPM_TOKEN
RUN yarn config set //artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/:_authToken ${NPM_TOKEN}

# Build with:
docker build --build-arg NPM_TOKEN=your_token ...
```

---

## Verification

### 1. Check Registry Configuration
```bash
cd /app/frontend

# Check what registry yarn is using
docker run --rm -v $(pwd):/app -w /app node:18-alpine \
  sh -c "yarn config get registry"

# Should output:
# https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/
```

### 2. Test Registry Access
```bash
# Test if Artifactory registry is accessible
curl -I https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/

# Should return HTTP 200 OK
```

### 3. Build and Watch Output
```bash
docker-compose -f docker-compose.artifactory.yml build --progress=plain frontend 2>&1 | tee build.log

# Search for Artifactory URLs in output
grep "artifactory" build.log

# Should see multiple lines with:
# https://artifactory.devtools.syd.c1.macquarie.com:9996/...
```

### 4. Verify Downloaded Packages
```bash
# In build output, you should see packages being downloaded from Artifactory:
# info There appears to be trouble with your network connection. Retrying...
# info https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/react/-/react-19.0.0.tgz
```

---

## Available Dockerfile Options

| Dockerfile | Registry Configuration | Authentication | Use Case |
|------------|----------------------|----------------|----------|
| `Dockerfile.frontend.artifactory` | Inline (RUN yarn config set) | No | ✅ Default - Simple setup |
| `Dockerfile.frontend.artifactory.withconfig` | Uses .npmrc/.yarnrc files | Yes | Auth required |
| `Dockerfile.frontend.artifactory.alt` | Inline + retry logic | No | Network issues |
| `Dockerfile.frontend.standard` | Public npm registry | No | Fallback option |

---

## Troubleshooting

### Issue: Still Using Public Registry

**Check 1: Verify Dockerfile has registry config**
```bash
grep "yarn config set registry" /app/Dockerfile.frontend.artifactory
# Should show the RUN command with registry URL
```

**Check 2: Ensure correct Dockerfile is being used**
```bash
grep "dockerfile:" /app/docker-compose.artifactory.yml
# Should show: dockerfile: ../Dockerfile.frontend.artifactory
```

**Check 3: Build with no cache**
```bash
docker-compose -f docker-compose.artifactory.yml build --no-cache frontend
```

### Issue: Authentication Failures

**Error**: `unauthorized`, `403 Forbidden`, or `401 Unauthorized`

**Solutions**:
1. Verify token is valid: Check in Artifactory UI
2. Use config file method with auth
3. Check token has correct permissions in Artifactory
4. Try username/password instead of token

### Issue: Registry Not Accessible

**Error**: `ETIMEDOUT`, `ECONNREFUSED`, or `getaddrinfo ENOTFOUND`

**Solutions**:
1. Check network connectivity: `curl -I https://artifactory.devtools.syd.c1.macquarie.com:9996/`
2. Check corporate proxy settings
3. Try building with `--network=host`
4. Verify Artifactory URL is correct

### Issue: SSL Certificate Errors

**Error**: `certificate verify failed`, `self signed certificate`

**Solution 1 - Disable SSL verification (not recommended for production)**:
```bash
# In Dockerfile, add:
RUN yarn config set strict-ssl false
```

**Solution 2 - Add CA certificate**:
```dockerfile
# In Dockerfile
COPY ca-certificate.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates
```

---

## Configuration Files Reference

### .npmrc (No Auth)
```ini
registry=https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/
always-auth=false
fetch-timeout=300000
fetch-retries=3
```

### .npmrc (With Auth)
```ini
registry=https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/
//artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/:_authToken=${NPM_TOKEN}
always-auth=true
fetch-timeout=300000
```

### .yarnrc
```
registry "https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/"
network-timeout 300000
```

---

## Quick Commands Summary

```bash
# Method 1: Use updated Dockerfile (inline config) - RECOMMENDED
docker-compose -f docker-compose.artifactory.yml build frontend

# Method 2: Use configuration files
cp /app/frontend/.npmrc.artifactory /app/frontend/.npmrc
cp /app/frontend/.yarnrc.artifactory /app/frontend/.yarnrc
# Update docker-compose.artifactory.yml: dockerfile: ../Dockerfile.frontend.artifactory.withconfig
docker-compose -f docker-compose.artifactory.yml build frontend

# Method 3: Use configuration script
/app/configure-artifactory-registry.sh

# Verify registry
docker run --rm -v $(pwd)/frontend:/app -w /app node:18-alpine yarn config get registry

# Test build
docker-compose -f docker-compose.artifactory.yml build --no-cache --progress=plain frontend 2>&1 | tee build.log
grep "artifactory" build.log
```

---

## Files Created

- `/app/Dockerfile.frontend.artifactory` - ✅ Updated with inline registry config
- `/app/Dockerfile.frontend.artifactory.withconfig` - Uses .npmrc/.yarnrc files
- `/app/frontend/.npmrc.artifactory` - Template .npmrc file
- `/app/frontend/.yarnrc.artifactory` - Template .yarnrc file
- `/app/configure-artifactory-registry.sh` - Interactive configuration script
- `/app/ARTIFACTORY_REGISTRY_CONFIG.md` - This documentation

---

## What Should Happen After Fix

✅ Build logs show Artifactory URLs
✅ Packages downloaded from Artifactory
✅ Faster builds (using cached packages)
✅ No direct access to public npm
✅ Build works behind corporate firewall

---

## Support & Next Steps

**If registry configuration works**:
- Build should complete successfully
- Packages come from Artifactory
- Proceed with deployment

**If still having issues**:
1. Check Artifactory admin for npm registry status
2. Verify network access to Artifactory
3. Try standard Dockerfile as fallback
4. Contact Artifactory support team

**Fallback option** (if Artifactory unavailable):
```bash
# Use public npm registry instead
sed -i 's|dockerfile: ../Dockerfile.frontend.artifactory|dockerfile: ../Dockerfile.frontend.standard|' docker-compose.artifactory.yml
docker-compose -f docker-compose.artifactory.yml build frontend
```
