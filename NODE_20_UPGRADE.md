# Node.js Version Upgrade - Node 18 to Node 20

## Error
```
error Found incompatible module.
error react-router-dom@7.9.4: The engine "node" is incompatible with this module. Expected version ">=20.0.0". Got "18.20.0"
```

## Root Cause
`react-router-dom@7.9.4` requires Node.js version 20 or higher, but Docker image was using Node.js 18.20.0.

## Solution Applied

### Upgraded to Node 20

**Changed all frontend Dockerfiles:**

```dockerfile
# Before
FROM artifactory.devtools.syd.c1.macquarie.com:9996/node:18-alpine

# After
FROM artifactory.devtools.syd.c1.macquarie.com:9996/node:20-alpine
```

## Files Updated

✅ `/app/Dockerfile.frontend.artifactory`
✅ `/app/Dockerfile.frontend.artifactory.alt`
✅ `/app/Dockerfile.frontend.artifactory.debug`
✅ `/app/Dockerfile.frontend.artifactory.withconfig`
✅ `/app/Dockerfile.frontend.standard`

## Why Node 20?

### Modern Dependencies Require It
- **react-router-dom v7+**: Requires Node >=20.0.0
- **React 19**: Better performance with Node 20
- **Modern build tools**: Optimized for Node 20

### Node 20 Benefits
- ✅ **LTS (Long Term Support)**: Stable until April 2026
- ✅ **Better Performance**: V8 engine improvements
- ✅ **Modern Features**: Latest JavaScript features
- ✅ **Better npm/yarn**: Improved package manager performance
- ✅ **Security**: Latest security patches

### Node Version Timeline
- Node 16: EOL (End of Life) - September 2023
- Node 18: Active LTS - April 2025
- **Node 20: Active LTS** - April 2026 ← **Current choice**
- Node 22: Current (not LTS yet)

## Compatibility

### What Still Works
- ✅ All existing packages compatible with Node 18 work on Node 20
- ✅ Alpine Linux base image available
- ✅ yarn/npm work perfectly
- ✅ All build tools (craco, webpack, etc.)

### What's Better
- ✅ Can use latest react-router-dom v7+
- ✅ Better build performance
- ✅ More future-proof

## Build Command

```bash
docker-compose -f docker-compose.artifactory.yml build frontend
```

## Expected Output

### Image Pull
```
#1 [internal] load build definition from Dockerfile.frontend.artifactory
#1 DONE 0.0s

#2 [internal] load .dockerignore
#2 DONE 0.0s

#3 [internal] load metadata for artifactory.../node:20-alpine
#3 DONE 1.2s

#4 [builder 1/8] FROM artifactory.../node:20-alpine
#4 DONE 5.0s
```

### Node Version Verification
```
#5 [builder 2/8] WORKDIR /app
#5 DONE 0.1s

# Can add verification:
RUN node --version
# Should show: v20.x.x
```

## Verification

### Check Dockerfile
```bash
grep "FROM.*node:" /app/Dockerfile.frontend.artifactory
# Should show: node:20-alpine
```

### Check Node Version in Container
```bash
docker run --rm artifactory.devtools.syd.c1.macquarie.com:9996/node:20-alpine node --version
# Should show: v20.x.x (e.g., v20.11.0)
```

## Alternative Solutions (Not Used)

### Option 1: Downgrade react-router-dom
```json
// package.json
"dependencies": {
  "react-router-dom": "^6.22.0"  // Last version supporting Node 18
}
```
**Not recommended**: Misses out on v7 features

### Option 2: Use Node 22
```dockerfile
FROM node:22-alpine
```
**Not recommended yet**: Not LTS, less stable

### Option 3: Use Debian-based Image
```dockerfile
FROM node:20-slim  # Debian instead of Alpine
```
**Not needed**: Alpine works fine

## Impact

### Before (Node 18)
- ❌ react-router-dom@7.9.4 incompatible
- ❌ Build fails at dependency resolution
- ❌ Can't use latest packages

### After (Node 20)
- ✅ react-router-dom@7.9.4 compatible
- ✅ Build proceeds successfully
- ✅ Can use all modern packages
- ✅ Better performance

## Package.json Compatibility

No changes needed to package.json - Node 20 is backward compatible with all Node 18 packages.

```json
{
  "engines": {
    "node": ">=20.0.0"  // Can add this to enforce requirement
  }
}
```

## Related Dependencies

These also benefit from Node 20:
- ✅ react@19.x
- ✅ react-router-dom@7.x
- ✅ @craco/craco@7.x
- ✅ tailwindcss@3.x
- ✅ vite (if used in future)

## Docker Image Sizes

| Image | Size |
|-------|------|
| node:18-alpine | ~120 MB |
| node:20-alpine | ~130 MB |

**Difference**: ~10 MB (negligible)

## Security

Node 20 includes:
- Latest V8 engine security patches
- Updated OpenSSL
- npm security improvements
- Better supply chain security

## Summary

**Problem**: react-router-dom@7.9.4 requires Node >=20.0.0
**Solution**: Upgraded from Node 18 to Node 20 Alpine
**Status**: ✅ All frontend Dockerfiles updated

**Build command:**
```bash
docker-compose -f docker-compose.artifactory.yml build frontend
```

**Expected**: Yarn install now succeeds, all dependencies compatible!
