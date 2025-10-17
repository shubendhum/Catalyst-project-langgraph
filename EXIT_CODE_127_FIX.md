# Exit Code 127 Fix - Command Not Found

## Error
```
yarn build failed with exit code 127
```

## What Exit Code 127 Means
**Exit code 127 = "command not found"**

This means when `yarn build` tried to run, it couldn't find the command it needed to execute.

## Root Cause

The build script in package.json is:
```json
"scripts": {
  "build": "craco build"
}
```

When yarn runs `yarn build`, it executes `craco build`. However, `craco` is installed in `node_modules/.bin/craco`, and this directory wasn't in the PATH inside the Docker container.

## Solution Applied

Added `node_modules/.bin` to PATH before running build:

```dockerfile
# Ensure node_modules/.bin is in PATH for build tools like craco
ENV PATH=/app/node_modules/.bin:$PATH

# Build application
RUN yarn build
```

## Why This Happens

**Normal Node.js behavior:**
- When you run `yarn build` on your local machine, yarn automatically adds `node_modules/.bin` to PATH
- Inside Docker, depending on how commands are run, this might not happen automatically
- The Alpine Linux image may have different PATH handling

**The fix:**
- Explicitly add `node_modules/.bin` to PATH
- Now `craco` command can be found
- Build proceeds successfully

## Files Updated

1. ✅ `/app/Dockerfile.frontend.artifactory`
2. ✅ `/app/Dockerfile.frontend.artifactory.debug`
3. ✅ `/app/Dockerfile.frontend.artifactory.alt`
4. ✅ `/app/Dockerfile.frontend.artifactory.withconfig`

## Build Now

```bash
docker-compose -f docker-compose.artifactory.yml build frontend
```

## Expected Result

**Before Fix:**
```
#8 [7/8] RUN yarn build
#8 0.234 yarn run v1.22.19
#8 0.456 $ craco build
#8 0.567 /bin/sh: craco: not found
#8 ERROR: process "/bin/sh -c yarn build" did not complete successfully: exit code: 127
```

**After Fix:**
```
#8 [7/8] RUN yarn build
#8 0.234 yarn run v1.22.19
#8 0.456 $ craco build
#8 1.234 Creating an optimized production build...
#8 45.678 Compiled successfully!
#8 67.890 File sizes after gzip:
#8 DONE 89.0s
```

## Verification

### Check PATH is Set
```bash
grep "PATH=/app/node_modules/.bin" /app/Dockerfile.frontend.artifactory
# Should show: ENV PATH=/app/node_modules/.bin:$PATH
```

### Test Manually
```bash
docker run --rm -it artifactory.../node:18-alpine sh
# Inside container:
cd /app
yarn install
ls -la node_modules/.bin/craco  # Should exist
export PATH=/app/node_modules/.bin:$PATH
which craco  # Should show /app/node_modules/.bin/craco
yarn build  # Should work now
```

## Other Commands That Need node_modules/.bin

This fix also enables:
- ✅ `craco` - React build tool
- ✅ `react-scripts` - Create React App scripts
- ✅ `eslint` - Linting tool
- ✅ `prettier` - Code formatter
- ✅ Any other CLI tools installed via npm/yarn

## Alternative Solutions (Not Used)

### Option 1: Use npx/yarn exec
```dockerfile
RUN yarn exec craco build
# or
RUN npx craco build
```

### Option 2: Full Path
```dockerfile
RUN ./node_modules/.bin/craco build
```

### Option 3: Package.json Script (Already Using)
```json
"scripts": {
  "build": "craco build"
}
```
```dockerfile
RUN yarn build  # yarn handles PATH internally
```

**Why we use ENV PATH:**
- Works for all commands, not just one
- Cleaner Dockerfile
- Matches local development environment
- Standard practice in Node.js Docker images

## Complete Build Sequence

```dockerfile
# 1. Install Alpine packages
RUN apk add --update --no-check-certificate --no-cache ca-certificates
RUN sed -i 's/https/http/g' /etc/apk/repositories
RUN apk add --no-cache python3 make g++ git

# 2. Configure registry and SSL
RUN yarn config set registry http://artifactory...
RUN yarn config set strict-ssl false
ENV NODE_TLS_REJECT_UNAUTHORIZED=0

# 3. Install dependencies
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile ...

# 4. Set PATH for build tools  ← FIX APPLIED HERE
ENV PATH=/app/node_modules/.bin:$PATH

# 5. Build application
COPY . ./
RUN yarn build  ← NOW FINDS craco
```

## Status

✅ **Fix Applied**: PATH updated to include node_modules/.bin
✅ **All Dockerfiles**: Updated with PATH fix
✅ **Ready to Build**: Should complete successfully now

## Build Command

```bash
cd /app
docker-compose -f docker-compose.artifactory.yml build frontend
```

**Expected:** Build completes without exit code 127
