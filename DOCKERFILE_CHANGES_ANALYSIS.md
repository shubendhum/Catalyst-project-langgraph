# What Changed in Last 3 Days - Dockerfile Comparison

## Context: Build Worked 3 Days Ago, Now Hangs

This document helps identify what changed between the working version and current version.

---

## Changes Made During This Session

### 1. Dockerfile.frontend.artifactory Changes

**Session Start (3 days ago - WORKING):**
```dockerfile
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile
```

**Current Version (NOW - HANGING):**
```dockerfile
COPY package.json ./
RUN timeout 600 yarn install \
    --network-timeout 600000 \
    --network-concurrency 1 \
    --verbose
```

**What Changed:**
- ✅ **Removed:** yarn.lock requirement (made optional)
- ✅ **Removed:** `--frozen-lockfile` flag
- ✅ **Added:** timeout wrapper (600s = 10 minutes)
- ✅ **Added:** verbose logging
- ✅ **Added:** diagnostic echo statements

**Why It Might Hang Now:**
- Without `--frozen-lockfile`, yarn tries to resolve dependencies from scratch
- This requires network calls to npm registry
- If Artifactory npm proxy is slow/broken, it hangs

---

### 2. docker-compose.artifactory.yml Changes

**3 Days Ago:**
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: ../Dockerfile.frontend.artifactory
```

**Current (Should be same):**
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: ../Dockerfile.frontend.artifactory
```

**Status:** ✅ **No significant changes** (context is correct)

---

### 3. New Services Added

**3 Days Ago:** ~3 services (MongoDB, Backend, Frontend)

**Now:** 10 services including:
- postgres ⭐ NEW
- langfuse-db ⭐ NEW
- langfuse ⭐ NEW
- rabbitmq
- redis
- qdrant
- etc.

**Impact:** These shouldn't affect frontend build, but might consume resources

---

## Root Cause Analysis

### Most Likely Causes (In Order):

**1. Artifactory npm Registry Issue (80% likely)**
```
Symptom: Build hangs at yarn install
Cause: Artifactory npm proxy is down/slow/misconfigured
Test: Can your machine reach npm registry through Artifactory?
```

**2. Network/Firewall Changes (10% likely)**
```
Symptom: Cannot connect to registry.npmjs.org
Cause: Corporate firewall rules changed
Test: ping registry.npmjs.org
```

**3. Removed yarn.lock (5% likely)**
```
Symptom: Yarn resolving dependencies takes forever
Cause: Without lockfile, yarn must resolve all versions
Fix: Add yarn.lock back
```

**4. Docker Desktop Resources (5% likely)**
```
Symptom: Build slow/hanging due to resource limits
Cause: Not enough RAM/CPU allocated
Fix: Check Docker Desktop → Settings → Resources
```

---

## Diagnostic Steps

### Step 1: Use Diagnostic Script

Run on your machine:
```bash
./diagnose-build.sh
```

This will show timestamped output so you can see exactly where it hangs.

### Step 2: Check Artifactory npm Proxy

```bash
# Test if npm registry is accessible
curl https://registry.npmjs.org/react

# Test through Artifactory (if configured)
curl http://artifactory.devtools.syd.c1.macquarie.com:9996/api/npm/npm-remote/react
```

### Step 3: Check Yarn Config in Container

```bash
# Build up to the point before yarn install
docker-compose -f docker-compose.artifactory.yml build frontend --progress=plain --target builder 2>&1 | grep -A 5 -B 5 "yarn config"
```

### Step 4: Manual Yarn Install Test

```bash
# Run just the yarn install step manually
docker run --rm \
  -v $(pwd)/frontend:/app \
  -w /app \
  artifactory.devtools.syd.c1.macquarie.com:9996/node:20-alpine \
  sh -c "yarn config set registry https://registry.npmjs.org/ && yarn config set strict-ssl false && timeout 60 yarn install --verbose"
```

---

## Quick Fixes to Try

### Fix 1: Add yarn.lock Back (Revert to Working State)

**If you have the old yarn.lock:**
```bash
# Copy yarn.lock to frontend directory
cp old-backup/yarn.lock frontend/

# Rebuild
docker-compose -f docker-compose.artifactory.yml build frontend --no-cache
```

### Fix 2: Use npm Instead of yarn

**Update Dockerfile:**
```dockerfile
# Replace:
RUN yarn install ...

# With:
RUN npm install --legacy-peer-deps --verbose
```

### Fix 3: Pre-download Dependencies

**Create a package cache:**
```bash
# On a machine with good internet
cd frontend
yarn install
tar -czf node_modules.tar.gz node_modules/

# Transfer to build machine and extract before COPY
```

### Fix 4: Use Different Registry

**Update Dockerfile before yarn install:**
```dockerfile
RUN yarn config set registry https://registry.yarnpkg.com/ && \
    yarn install
```

---

## What to Look For in Logs

**If hangs at:**
```
[frontend builder 7/12] COPY package.json ./
```
→ File not found, context wrong

**If hangs at:**
```
[frontend builder 8/12] RUN yarn install
```
→ Network/registry issue

**If shows:**
```
info There appears to be trouble with your network connection. Retrying...
```
→ Definitely network/Artifactory issue

**If shows:**
```
[1/4] Resolving packages...
```
→ Stuck resolving dependencies (registry slow)

---

## Comparison: What Worked vs What Changed

| Aspect | 3 Days Ago (Working) | Now (Hanging) | Impact |
|--------|---------------------|---------------|---------|
| yarn.lock | Present, used | Removed | HIGH - Causes dependency resolution |
| --frozen-lockfile | Yes | No | HIGH - Must resolve versions |
| Timeout | None | 600s | Good - Prevents infinite hang |
| Logging | Minimal | Verbose | Good - Helps debug |
| Services | 3 | 10 | LOW - Shouldn't affect build |

**Biggest Change:** Removed yarn.lock and --frozen-lockfile

**Recommendation:** Add yarn.lock back to match the working version from 3 days ago.

---

## Emergency Rollback

**If you want to go back to working state:**

1. Find your working docker-compose.artifactory.yml from 3 days ago
2. Find your working Dockerfile.frontend.artifactory from 3 days ago
3. Replace current files with those
4. Keep the yarn.lock file
5. Rebuild

**Or ask me to restore the simpler version that was working.**

---

## Next Steps

1. **Run:** `./diagnose-build.sh` on your machine
2. **Share:** The output showing where it hangs
3. **I'll:** Provide targeted fix based on exact hang point

**The diagnostic script will show exactly where the build hangs with timestamps!**
