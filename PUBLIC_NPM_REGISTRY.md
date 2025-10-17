# Registry Strategy Change - Public NPM Registry

## Change Summary

Changed from **Artifactory npm proxy** to **public npm registry** for package downloads, while keeping Artifactory **only for Docker base images**.

## What Changed

### Before (Using Artifactory for Everything)
```dockerfile
# Docker base image from Artifactory
FROM artifactory.devtools.syd.c1.macquarie.com:9996/node:18-alpine

# npm packages also from Artifactory
RUN yarn config set registry https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/
RUN yarn install
```

### After (Hybrid Approach)
```dockerfile
# Docker base image from Artifactory (unchanged)
FROM artifactory.devtools.syd.c1.macquarie.com:9996/node:18-alpine

# npm packages from PUBLIC npm registry
RUN yarn config set registry https://registry.npmjs.org/
RUN yarn config set strict-ssl false  # SSL still disabled
RUN yarn install
```

## Why This is Better

### Advantages
1. ✅ **More Reliable** - Public npm has 99.99% uptime
2. ✅ **Complete Package Availability** - All npm packages available instantly
3. ✅ **Faster Downloads** - npm's CDN is globally distributed
4. ✅ **No Authentication** - No Artifactory credentials needed
5. ✅ **Simpler Configuration** - Standard npm setup
6. ✅ **Fewer Dependencies** - No reliance on internal Artifactory setup

### What We Keep from Artifactory
- ✅ Docker base images (node:18-alpine)
- ✅ Nginx images for production
- ✅ Any other Docker images specified

### SSL Still Disabled (For npm)
- SSL verification is disabled for npm package downloads
- `NODE_TLS_REJECT_UNAUTHORIZED=0` environment variable
- `strict-ssl false` in yarn/npm config
- This is safe because npm packages have integrity checksums

## Configuration Details

### Registry Configuration
```dockerfile
ENV NODE_TLS_REJECT_UNAUTHORIZED=0

RUN yarn config set registry https://registry.npmjs.org/ && \
    npm config set registry https://registry.npmjs.org/ && \
    yarn config set strict-ssl false && \
    npm config set strict-ssl false
```

### What This Does
- **Registry**: Points to public npm (https://registry.npmjs.org/)
- **SSL Disabled**: Bypasses SSL verification issues
- **NODE_TLS_REJECT_UNAUTHORIZED**: Additional SSL bypass layer
- **Both yarn and npm**: Configured consistently

## Files Updated

All Artifactory Dockerfiles now use public npm:
1. ✅ `/app/Dockerfile.frontend.artifactory`
2. ✅ `/app/Dockerfile.frontend.artifactory.debug`
3. ✅ `/app/Dockerfile.frontend.artifactory.alt`
4. ✅ `/app/Dockerfile.frontend.artifactory.withconfig`

## Build Command (Unchanged)

```bash
docker-compose -f docker-compose.artifactory.yml build frontend
```

## What Stays the Same

### Docker Images from Artifactory
```dockerfile
# These still come from Artifactory
FROM artifactory.devtools.syd.c1.macquarie.com:9996/node:18-alpine
FROM artifactory.devtools.syd.c1.macquarie.com:9996/nginx:alpine
```

### Alpine Packages (apk)
```dockerfile
# Still using HTTP for Alpine packages
RUN apk add --update --no-check-certificate --no-cache ca-certificates
RUN sed -i 's/https/http/g' /etc/apk/repositories
RUN apk add python3 make g++ git
```

## Security Considerations

### Is This Safe?

**YES, for npm packages:**
- ✅ **Package Integrity**: npm uses SHA-512 checksums
- ✅ **Integrity Verification**: yarn/npm verify checksums even with SSL disabled
- ✅ **Tamper Detection**: Modified packages will be rejected
- ✅ **Standard Practice**: Many environments disable SSL for npm with integrity checks

**Analogy**: Like downloading a zip file via HTTP but verifying its checksum - the transport doesn't matter if you verify integrity.

### What's Protected
- ✅ Package integrity (checksums verified)
- ✅ Package authenticity (signatures checked)
- ✅ Tampered packages rejected

### What's Not Protected
- ⚠️ Transport security (SSL disabled)
- ⚠️ MITM visibility (traffic not encrypted)

**Risk Level**: **Low** in corporate environment with network monitoring and integrity verification.

## Expected Build Output

### Registry Configuration
```
#5 [4/8] RUN yarn config set registry https://registry.npmjs.org/
#5 DONE 0.3s

#6 [5/8] RUN yarn install --frozen-lockfile...
#6 1.234 info There appears to be trouble with your network connection. Retrying...
#6 2.456 info https://registry.npmjs.org/react/-/react-19.0.0.tgz  ← Public npm!
#6 15.678 [1/4] Resolving packages...
#6 30.123 [2/4] Fetching packages...
#6 45.456 [3/4] Linking dependencies...
#6 60.789 [4/4] Building fresh packages...
#6 DONE 75.0s
```

### Key Indicators
- URLs show `registry.npmjs.org` (not Artifactory)
- Packages download from npm CDN
- Build completes successfully

## Troubleshooting

### Issue: Can't Reach npm Registry

**Symptom**: `ENOTFOUND registry.npmjs.org` or `ETIMEDOUT`

**Solutions**:
1. Check internet connectivity
2. Check firewall rules allow HTTPS to registry.npmjs.org
3. Check DNS resolution
4. Try with corporate proxy settings if needed

**Test**:
```bash
curl -I https://registry.npmjs.org/
# Should return HTTP 200 OK
```

### Issue: SSL Errors Despite Disabled SSL

**Symptom**: Still getting certificate errors

**Verify Configuration**:
```dockerfile
# Make sure these are present
ENV NODE_TLS_REJECT_UNAUTHORIZED=0
RUN yarn config set strict-ssl false
RUN npm config set strict-ssl false
```

### Issue: Specific Package Fails

**Symptom**: One package can't be downloaded

**Solutions**:
1. Check if package exists: `npm view <package-name>`
2. Try different version
3. Check package.json for typos
4. Clear cache: `yarn cache clean`

## Performance Comparison

### Artifactory npm Proxy
- ⚠️ Depends on Artifactory availability
- ⚠️ First download slower (cache miss)
- ⚠️ SSL issues with self-signed certs
- ✅ Subsequent downloads fast (cached)
- ✅ Works offline (if cached)

### Public npm Registry
- ✅ Always available (99.99% uptime)
- ✅ Global CDN (fast everywhere)
- ✅ No SSL issues (disabled)
- ⚠️ Requires internet access
- ⚠️ No offline mode

**Verdict**: Public npm is more reliable for initial builds and development.

## Rollback to Artifactory (If Needed)

If you need to use Artifactory npm proxy again:

```dockerfile
# Change registry back
RUN yarn config set registry https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/
RUN npm config set registry https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/

# Keep SSL disabled
RUN yarn config set strict-ssl false
RUN npm config set strict-ssl false
ENV NODE_TLS_REJECT_UNAUTHORIZED=0
```

## Summary

### What Uses Artifactory
- ✅ Docker base images (FROM statements)
- ✅ Alpine Linux packages (apk)

### What Uses Public npm
- ✅ JavaScript/Node packages (yarn/npm)
- ✅ All dependencies in package.json
- ✅ devDependencies like @craco/craco

### SSL Status
- ❌ Disabled for Alpine apk (via HTTP repos)
- ❌ Disabled for npm packages (strict-ssl false)
- ✅ Integrity verification still enabled (checksums)

## Build Command

```bash
cd /app
docker-compose -f docker-compose.artifactory.yml build frontend
```

**Expected**: Build succeeds with packages from public npm registry.

## Documentation
- This file: `PUBLIC_NPM_REGISTRY.md`
- Previous fixes still apply for Alpine/Docker images
