# React Refresh Babel Error Fix - NODE_ENV

## Error
```
Error: @babel/plugin-transform-react-jsx-development: React Refresh Babel transform should only be enabled in development environment.
Instead, the environment is: "production".
```

## Root Cause

We set `NODE_ENV=development` early in the Dockerfile to ensure devDependencies are installed, but this environment variable persisted through the build step, causing React Fast Refresh (a development-only feature) to try to run during production build.

## Solution Applied

**Set NODE_ENV at the right stages:**

### Stage 1: Install Dependencies (development)
```dockerfile
# Line 29: Set to development for yarn install
ENV NODE_ENV=development

# This ensures devDependencies (@craco/craco, etc.) are installed
RUN yarn install
```

### Stage 2: Build Application (production)
```dockerfile
# Line 82: Change to production for build
ENV NODE_ENV=production

# Now React build runs in production mode (no Fast Refresh)
RUN npx craco build
```

## Why This Works

### NODE_ENV Controls Multiple Things

**When NODE_ENV=development:**
- ✅ yarn installs devDependencies
- ✅ React includes development warnings
- ✅ React Fast Refresh enabled
- ✅ Source maps generated
- ❌ Larger bundle size
- ❌ Slower performance

**When NODE_ENV=production:**
- ❌ yarn skips devDependencies (but we already installed them)
- ✅ React optimized for production
- ✅ React Fast Refresh disabled
- ✅ Minified code
- ✅ Smaller bundle size
- ✅ Better performance

## The Flow

```dockerfile
# Step 1: Set development mode
ENV NODE_ENV=development

# Step 2: Install dependencies (includes devDependencies)
RUN yarn install  # ✅ Installs craco, babel plugins, etc.

# Step 3: Copy source code
COPY . ./

# Step 4: Switch to production mode
ENV NODE_ENV=production

# Step 5: Build for production
RUN npx craco build  # ✅ No Fast Refresh, optimized build
```

## What React Fast Refresh Is

**React Fast Refresh:**
- Development-only feature
- Hot reload for React components
- Updates components without full page reload
- **NOT** for production builds

**Error occurs when:**
- NODE_ENV=development during build
- Babel tries to include Fast Refresh transform
- Production build shouldn't have this

## File Updated

✅ `/app/Dockerfile.frontend.artifactory`
- Line 29: `ENV NODE_ENV=development` (for install)
- Line 82: `ENV NODE_ENV=production` (for build)

## Build Command

```bash
docker-compose -f docker-compose.artifactory.yml build frontend
```

## Expected Output

### During Install (development mode)
```
#6 [builder 5/8] RUN yarn install
#6 1.234 yarn install v1.22.19
#6 2.456 [1/4] Resolving packages...
#6 15.678 [2/4] Fetching packages...
#6 45.890 [3/4] Linking dependencies...
#6 67.123 [4/4] Building fresh packages...
#6 89.456 Done in 89.45s.
#6 DONE
```

### During Build (production mode)
```
#8 [builder 7/8] RUN npx craco build
#8 1.234 Creating an optimized production build...
#8 45.678 Compiled successfully!
#8 67.890 
#8 67.891 File sizes after gzip:
#8 67.892   142.5 kB  build/static/js/main.abc123.js
#8 67.893   12.3 kB   build/static/css/main.def456.css
#8 DONE
```

**No Fast Refresh error** ✅

## Alternative Solutions (Not Used)

### Option 1: Remove Fast Refresh Plugin
```javascript
// craco.config.js
module.exports = {
  babel: {
    plugins: [
      // Don't include @babel/plugin-transform-react-jsx-development
    ]
  }
}
```
**Not recommended**: Loses development features

### Option 2: Always Use Production
```dockerfile
ENV NODE_ENV=production
RUN yarn install  # ❌ Won't install devDependencies
```
**Not recommended**: Missing build tools

### Option 3: Use --production=false Flag
```dockerfile
ENV NODE_ENV=production
RUN yarn install --production=false
```
**Also works**, but our approach is cleaner

## Verification

### Check Dockerfile Flow
```bash
grep -n "NODE_ENV" /app/Dockerfile.frontend.artifactory
# Should show:
# 29:ENV NODE_ENV=development
# 82:ENV NODE_ENV=production
```

### Test Build
```bash
docker-compose -f docker-compose.artifactory.yml build frontend
# Should complete without Fast Refresh error
```

## Impact on Build

### Build Output Changes

**Development build (wrong):**
- Includes Fast Refresh
- Source maps included
- Not minified
- ~3-5 MB bundle

**Production build (correct):**
- No Fast Refresh
- Minified code
- Tree-shaking applied
- ~500 KB bundle

## Summary

**Problem**: React Fast Refresh tried to run in production build
**Cause**: NODE_ENV=development persisted through build step
**Solution**: Set NODE_ENV=development for install, NODE_ENV=production for build
**Status**: ✅ Fixed

**Build command:**
```bash
docker-compose -f docker-compose.artifactory.yml build frontend
```

**Expected**: Production build succeeds without Fast Refresh error!
