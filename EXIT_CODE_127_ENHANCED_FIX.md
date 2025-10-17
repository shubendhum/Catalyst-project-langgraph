# Exit Code 127 Still Failing - Enhanced Fix

## Issue
Still getting exit code 127 (command not found) at Dockerfile line 74 even after adding PATH.

## Root Cause Analysis

Exit code 127 can happen for several reasons:
1. **Command not in PATH** - We fixed this with ENV PATH
2. **devDependencies not installed** - By default, some scenarios skip devDependencies
3. **Binary not executable** - Permission issues
4. **Binary doesn't exist** - Installation incomplete

## Enhanced Solution Applied

### Fix 1: Explicitly Install devDependencies
```dockerfile
RUN yarn install --frozen-lockfile \
    --network-timeout 600000 \
    --network-concurrency 1 \
    --production=false \            # ← NEW: Ensure devDeps installed
    --verbose
```

**Why:** `--production=false` explicitly tells yarn to install devDependencies (where `@craco/craco` lives).

### Fix 2: Verify Installation Before Build
```dockerfile
RUN echo "=== Verifying installed packages ===" && \
    ls -la node_modules/.bin/ | grep craco || echo "WARNING: craco not found" && \
    test -f node_modules/.bin/craco && echo "✓ craco found" || echo "✗ craco NOT found"
```

**Why:** Catches the issue early if craco isn't installed.

### Fix 3: Use npx Instead of Direct Command
```dockerfile
RUN npx craco build
```

**Why:** `npx` is more robust:
- Searches node_modules/.bin automatically
- Doesn't rely on PATH being set correctly
- Standard practice for running local binaries
- Falls back to downloading if not found (though we don't want this)

## Changes Made

**Before:**
```dockerfile
RUN yarn install --frozen-lockfile ...
# (might skip devDependencies in some scenarios)

RUN yarn build  # Calls craco, might not find it
```

**After:**
```dockerfile
RUN yarn install --frozen-lockfile \
    --production=false ...  # ← Explicit devDeps

RUN echo "Verifying craco..." && \
    test -f node_modules/.bin/craco  # ← Verification

RUN npx craco build  # ← More reliable than yarn build
```

## Why yarn install Might Skip devDependencies

Several scenarios can cause devDependencies to be skipped:
1. **NODE_ENV=production** environment variable
2. **Yarn cache issues** - Corrupted cache
3. **Registry issues** - Some packages fail silently
4. **Permission issues** - Can't create symlinks in node_modules/.bin
5. **Alpine Linux issues** - Different behavior than other distros

## Build Now

```bash
docker-compose -f docker-compose.artifactory.yml build frontend
```

## What to Look For in Output

### During yarn install:
```
Starting yarn install attempt 1...
[1/4] Resolving packages...
[2/4] Fetching packages...
[3/4] Linking dependencies...
[4/4] Building fresh packages...
```

### Verification step should show:
```
=== Verifying installed packages ===
✓ craco binary found
```

### Build step should show:
```
=== Starting React build ===
Creating an optimized production build...
Compiled successfully!
```

## If Still Fails

### Check the verification output:
```
✗ craco binary NOT found
```

This means yarn install succeeded but didn't install craco. Possible causes:
1. **devDependencies still skipped** - Check NODE_ENV
2. **Registry doesn't have @craco/craco** - Check Artifactory
3. **Silent failure during install** - Check yarn-install.log

### Debug commands:
```bash
# Check if NODE_ENV is set
docker run --rm artifactory.../node:18-alpine env | grep NODE_ENV

# Manually test install
docker run --rm -it -v /app/frontend:/workspace -w /workspace \
  artifactory.../node:18-alpine sh

# Inside container:
yarn install --production=false --verbose 2>&1 | tee install.log
ls -la node_modules/.bin/craco
cat install.log | grep craco
```

## Alternative Solutions

### Option 1: Install craco globally (not recommended)
```dockerfile
RUN yarn global add @craco/craco
```

### Option 2: Use react-scripts directly
```dockerfile
# Modify package.json to use react-scripts instead of craco
RUN npx react-scripts build
```

### Option 3: Use npm instead of yarn
```dockerfile
RUN npm ci --include=dev
RUN npx craco build
```

## Files Updated

1. ✅ `/app/Dockerfile.frontend.artifactory`
   - Added `--production=false` to yarn install
   - Added craco verification step
   - Changed to `npx craco build`

## Complete Install & Build Section

```dockerfile
# Install with devDependencies explicitly
RUN yarn install --frozen-lockfile \
    --network-timeout 600000 \
    --network-concurrency 1 \
    --production=false \
    --verbose

# Verify craco is installed
RUN ls -la node_modules/.bin/craco && echo "✓ craco found"

# Copy source
COPY . ./

# Set environment
ENV PATH=/app/node_modules/.bin:$PATH

# Build using npx
RUN npx craco build
```

## Summary of All Fixes

1. ✅ Build context
2. ✅ Alpine SSL  
3. ✅ Yarn registry
4. ✅ Yarn SSL disabled
5. ✅ Invalid flags removed
6. ✅ Timeouts increased
7. ✅ PATH set for build tools
8. ✅ devDependencies explicitly installed ← **NEW**
9. ✅ Craco verification step ← **NEW**
10. ✅ Using npx for build ← **NEW**

## Expected Output

```
#6 [5/8] RUN yarn install --frozen-lockfile --production=false ...
#6 DONE 45.0s

#7 [6/8] RUN echo "=== Verifying..." && test -f node_modules/.bin/craco
#7 0.234 === Verifying installed packages ===
#7 0.456 ✓ craco binary found
#7 DONE 0.5s

#8 [7/8] RUN npx craco build
#8 1.234 Creating an optimized production build...
#8 45.678 Compiled successfully!
#8 DONE 67.0s
```

## Status

✅ Enhanced with explicit devDependencies installation
✅ Added verification step before build
✅ Using npx for more reliable execution

**If this still fails, we'll need to see the verification step output to diagnose further.**
