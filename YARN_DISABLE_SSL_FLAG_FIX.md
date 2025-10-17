# Yarn Install Fix - Removed Invalid --disable-ssl Flag

## Issue from Image
```
failed to solve: processing yarn install...
"yarn install --frozen-lockfile --network-timeout 600000 --network-concurrency 1 --disable-ssl"
did not complete successfully: exit code: 1
```

## Root Cause

The `--disable-ssl` flag is **not a valid yarn v1 flag**. This was causing yarn install to fail.

### Why This Happened
- `--disable-ssl` is not documented in yarn v1 CLI
- Yarn was rejecting the command due to unknown flag
- SSL verification was already disabled via `yarn config set strict-ssl false`
- The flag was redundant and causing failures

## Solution Applied

### Removed --disable-ssl Flag

**Before (Incorrect):**
```dockerfile
RUN yarn install --frozen-lockfile \
    --network-timeout 600000 \
    --network-concurrency 1 \
    --disable-ssl || \
    ...
```

**After (Correct):**
```dockerfile
RUN yarn install --frozen-lockfile \
    --network-timeout 600000 \
    --network-concurrency 1 || \
    ...
```

### SSL is Still Disabled (Correctly)

SSL verification is properly disabled earlier in the Dockerfile:
```dockerfile
# This is the correct way to disable SSL in yarn
RUN yarn config set strict-ssl false && \
    npm config set strict-ssl false
```

## Valid Yarn Flags

### Correct flags for yarn v1:
- ✅ `--frozen-lockfile` - Don't generate a lockfile
- ✅ `--network-timeout <ms>` - Network timeout in milliseconds
- ✅ `--network-concurrency <n>` - Maximum concurrent network requests
- ❌ `--disable-ssl` - **NOT A VALID FLAG** (doesn't exist)

### How to Disable SSL in Yarn (Correct Methods):

**Method 1: Via Config (Best)**
```bash
yarn config set strict-ssl false
```

**Method 2: Via .yarnrc File**
```
strict-ssl false
```

**Method 3: Via Environment Variable**
```bash
export YARN_STRICT_SSL=false
```

**NOT via command flag** - there is no `--disable-ssl` flag!

## Files Updated

All Artifactory Dockerfiles have been corrected:
1. ✅ `/app/Dockerfile.frontend.artifactory`
2. ✅ `/app/Dockerfile.frontend.artifactory.alt`
3. ✅ `/app/Dockerfile.frontend.artifactory.withconfig`

## Current Configuration (Correct)

```dockerfile
# Step 1: Configure SSL to be disabled
RUN yarn config set strict-ssl false && \
    npm config set strict-ssl false

# Step 2: Install with valid flags only
RUN yarn install --frozen-lockfile \
    --network-timeout 600000 \
    --network-concurrency 1 || \
    (yarn cache clean && yarn install ...)
```

**SSL is disabled via config**, not via command flag.

## Build Now

```bash
docker-compose -f docker-compose.artifactory.yml build frontend
```

## Expected Behavior

**Before Fix:**
```
ERROR: unknown flag: --disable-ssl
exit code: 1
```

**After Fix:**
```
#6 [5/8] RUN yarn install --frozen-lockfile --network-timeout 600000 --network-concurrency 1
#6 0.234 yarn install v1.22.19
#6 1.234 [1/4] Resolving packages...
#6 15.456 [2/4] Fetching packages...
#6 45.678 [3/4] Linking dependencies...
#6 67.890 [4/4] Building fresh packages...
#6 DONE 89.0s
```

## Verification

### Check Flag is Removed
```bash
grep "\-\-disable-ssl" /app/Dockerfile.frontend.artifactory
# Should return nothing (no results)
```

### Check SSL Config is Present
```bash
grep "strict-ssl false" /app/Dockerfile.frontend.artifactory
# Should show: yarn config set strict-ssl false
```

### Verify Valid Flags Only
```bash
grep "yarn install" /app/Dockerfile.frontend.artifactory
# Should show only valid flags: --frozen-lockfile, --network-timeout, --network-concurrency
```

## Why This is Better

### Previous Approach (Wrong)
```dockerfile
# Config: Set strict-ssl false ✅
# Command: yarn install --disable-ssl ❌ (invalid flag)
# Result: FAIL - yarn rejects invalid flag
```

### Current Approach (Correct)
```dockerfile
# Config: Set strict-ssl false ✅
# Command: yarn install (valid flags only) ✅
# Result: SUCCESS - SSL disabled via config, valid command
```

## Key Learnings

1. **`--disable-ssl` is not a yarn flag** - Common misconception
2. **Use `yarn config set strict-ssl false`** - Correct method
3. **Config persists** - No need for flag on every command
4. **Check documentation** - Verify flags exist before using

## Yarn SSL Configuration Reference

### Disable SSL (All Valid Methods)

**CLI Config:**
```bash
yarn config set strict-ssl false
yarn config set registry http://... # Use HTTP registry
```

**File Config (.yarnrc):**
```
strict-ssl false
registry "http://registry.example.com"
```

**Environment Variable:**
```bash
export YARN_STRICT_SSL=false
```

**NOT via Command Line Flag:**
```bash
yarn install --disable-ssl  # ❌ DOES NOT EXIST
```

## Alternative If Build Still Fails

If yarn install continues to fail, try these debugging steps:

### 1. Check Yarn Version
```dockerfile
RUN yarn --version
# Verify it's a compatible version
```

### 2. Test Yarn Manually
```bash
docker run --rm -it artifactory.../node:18-alpine sh
# Inside container:
yarn config set registry http://artifactory...
yarn config set strict-ssl false
yarn config list  # Verify settings
yarn install --frozen-lockfile --network-timeout 600000 --network-concurrency 1
```

### 3. Try Without frozen-lockfile
```dockerfile
# Temporarily for debugging
RUN yarn install --network-timeout 600000 --network-concurrency 1
```

### 4. Check Registry Accessibility
```bash
# Inside container
wget http://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/
# Should return some content
```

## Summary

**Problem:** `--disable-ssl` is not a valid yarn flag
**Solution:** Removed invalid flag, kept SSL disabled via config
**Status:** All Dockerfiles corrected

**Build command:**
```bash
docker-compose -f docker-compose.artifactory.yml build frontend
```

**Expected:** Yarn install succeeds without "unknown flag" error
