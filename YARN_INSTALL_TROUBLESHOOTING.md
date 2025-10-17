# Docker Build - Yarn Install Failure Troubleshooting

## Error
```
failed to solve: process "/bin/sh -c yarn install --frozen-lockfile" did not complete
```

## Common Causes

### 1. Network/Registry Access Issues
**Symptom**: Timeout or connection errors during package download
**Cause**: Artifactory mirror can't reach npm registry or packages aren't cached

### 2. Memory/Resource Constraints
**Symptom**: Process killed without clear error message
**Cause**: Docker container runs out of memory during install

### 3. Incompatible Dependencies
**Symptom**: Dependency resolution failures
**Cause**: yarn.lock conflicts with package.json or has outdated packages

### 4. Build Context Issues
**Symptom**: "package.json not found" or "yarn.lock not found"
**Cause**: Files not in build context (should be fixed now)

## Solutions

### Solution 1: Use Updated Dockerfile with Increased Timeouts ✅ APPLIED

The main Dockerfile has been updated with:
```dockerfile
RUN yarn install --frozen-lockfile --network-timeout 300000 --network-concurrency 1
```

This adds:
- `--network-timeout 300000` - 5 minute timeout (vs default 30s)
- `--network-concurrency 1` - One download at a time (more stable)

### Solution 2: Use Alternative Dockerfile (If Solution 1 Fails)

Use `Dockerfile.frontend.artifactory.alt` which has:
- Build dependencies (python3, make, g++)
- Retry logic if install fails
- Yarn cache clean on retry
- No frozen-lockfile requirement

**Update docker-compose.artifactory.yml**:
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: ../Dockerfile.frontend.artifactory.alt  # ← Change this line
```

### Solution 3: Configure Artifactory NPM Registry

If your organization uses Artifactory as npm registry proxy:

**Create `.npmrc` in `/app/frontend/`**:
```
registry=https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/
always-auth=false
```

**Create `.yarnrc` in `/app/frontend/`**:
```
registry "https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/"
```

**Then update Dockerfile to copy these**:
```dockerfile
COPY package.json yarn.lock .npmrc .yarnrc ./
```

### Solution 4: Increase Docker Build Resources

**For Docker Desktop**:
1. Open Docker Desktop → Settings → Resources
2. Increase Memory to at least 4GB
3. Increase CPUs to at least 2
4. Apply & Restart

**For docker-compose**:
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: ../Dockerfile.frontend.artifactory
    shm_size: '2gb'  # Increase shared memory
  deploy:
    resources:
      limits:
        memory: 4G
```

### Solution 5: Build Without Frozen Lockfile

**Temporarily disable frozen-lockfile**:
```dockerfile
# Instead of:
RUN yarn install --frozen-lockfile

# Use:
RUN yarn install --network-timeout 600000
```

This allows yarn to regenerate lockfile if needed.

### Solution 6: Pre-download Dependencies Locally

**Build using local cache**:
```bash
# On host machine with good network
cd /app/frontend
yarn install

# Then build Docker with cache
cd /app
docker-compose -f docker-compose.artifactory.yml build frontend
```

### Solution 7: Use Public Registry Instead

If Artifactory mirror is problematic, use public registry:

**Create `Dockerfile.frontend.public`**:
```dockerfile
FROM node:18-alpine as builder
# ... rest same as artifactory version
```

**Update docker-compose to use public images**:
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: ../Dockerfile.frontend.public
```

## Step-by-Step Debugging

### Step 1: Check Build Context
```bash
cd /app/frontend
ls -la package.json yarn.lock
# Both should exist
```

### Step 2: Test Yarn Locally
```bash
cd /app/frontend
yarn install --frozen-lockfile
# If this works, Docker build should work
```

### Step 3: Build with Verbose Output
```bash
docker build -f Dockerfile.frontend.artifactory \
  --progress=plain \
  --no-cache \
  -t test-frontend \
  /app/frontend 2>&1 | tee build.log
```

### Step 4: Check Exact Error
```bash
# Look for specific error in build.log
cat build.log | grep -A 10 "error"
cat build.log | grep -A 10 "ERR"
```

### Step 5: Test with Alternative Dockerfile
```bash
cd /app/frontend
docker build -f ../Dockerfile.frontend.artifactory.alt -t test-frontend .
```

## Quick Fixes

### Fix 1: Increase Timeout (Fast)
```bash
# Edit Dockerfile.frontend.artifactory
# Change:
RUN yarn install --frozen-lockfile
# To:
RUN yarn install --frozen-lockfile --network-timeout 600000
```

### Fix 2: Use Alternative Dockerfile (Fast)
```bash
# Use the alternative Dockerfile
docker-compose -f docker-compose.artifactory.yml build frontend \
  --build-arg DOCKERFILE=Dockerfile.frontend.artifactory.alt
```

### Fix 3: Remove Frozen Lockfile (Fast)
```bash
# Edit Dockerfile, remove --frozen-lockfile flag
RUN yarn install --network-timeout 300000
```

## Build Commands After Fixes

### Using Docker Compose
```bash
# Rebuild with no cache
docker-compose -f docker-compose.artifactory.yml build --no-cache frontend

# With progress output
docker-compose -f docker-compose.artifactory.yml build --no-cache --progress=plain frontend
```

### Using Docker Directly
```bash
# From /app/frontend directory
cd /app/frontend

# Build with main Dockerfile
docker build -f ../Dockerfile.frontend.artifactory \
  --network=host \
  -t catalyst-frontend .

# Build with alternative Dockerfile
docker build -f ../Dockerfile.frontend.artifactory.alt \
  -t catalyst-frontend .
```

## Verification

After applying fixes, verify:

### 1. Check Dockerfile Changes
```bash
grep "yarn install" /app/Dockerfile.frontend.artifactory
# Should show: --network-timeout 300000 --network-concurrency 1
```

### 2. Test Build Locally
```bash
cd /app/frontend
docker build -f ../Dockerfile.frontend.artifactory -t test .
echo $?
# Should output: 0 (success)
```

### 3. Check Built Image
```bash
docker images | grep catalyst-frontend
# Should show the image with recent timestamp
```

### 4. Test Run Container
```bash
docker run -d -p 8080:80 --name test-frontend catalyst-frontend
sleep 5
curl http://localhost:8080/
docker stop test-frontend
docker rm test-frontend
```

## Additional Considerations

### Network Issues
If behind corporate proxy:
```dockerfile
# Add to Dockerfile before yarn install
ENV HTTP_PROXY=http://proxy.company.com:8080
ENV HTTPS_PROXY=http://proxy.company.com:8080
ENV NO_PROXY=localhost,127.0.0.1
```

### Artifactory Authentication
If Artifactory requires auth:
```bash
# Create .npmrc with auth
cd /app/frontend
echo "//artifactory.devtools.syd.c1.macquarie.com:9996/:_authToken=YOUR_TOKEN" > .npmrc
```

### DNS Resolution
If DNS issues:
```bash
# Build with host network
docker build --network=host -f Dockerfile.frontend.artifactory -t frontend .
```

## Files Reference

- `/app/Dockerfile.frontend.artifactory` - Main Dockerfile (with timeouts)
- `/app/Dockerfile.frontend.artifactory.alt` - Alternative (with retry logic)
- `/app/docker-compose.artifactory.yml` - Compose configuration
- `/app/frontend/package.json` - Dependencies
- `/app/frontend/yarn.lock` - Lock file

## Status Checklist

- [x] Build context fixed (frontend directory)
- [x] Increased yarn timeout to 5 minutes
- [x] Added network concurrency limit
- [x] Created alternative Dockerfile with retry logic
- [x] Added build dependencies (python3, make, g++)
- [ ] Verify network access to npm registry
- [ ] Confirm Docker resources adequate (4GB+ RAM)
- [ ] Test build completes successfully

## Support

If issue persists:
1. Check network connectivity to npm registry
2. Verify Artifactory mirror has npm packages cached
3. Try building with public Node image (node:18-alpine)
4. Contact Artifactory admin about npm registry access
5. Consider using pre-built images if available

## Related Documentation
- `ARTIFACTORY_BUILD_FIX.md` - Build context fix
- `ARTIFACTORY_QUICK_START.md` - Quick start guide
- `DOCKER_BUILD_FIX_SUMMARY.md` - Previous fixes
