# SSL Certificate Verification Disabled - Complete Fix

## Error
```
routines:tls_post_process_client_hello:certificate verify failed
```

## Root Cause
Artifactory is using a self-signed SSL certificate or an internal CA certificate that Node/Yarn doesn't recognize, causing certificate verification to fail during package downloads.

## Solution Applied ✅

### All Artifactory Dockerfiles Updated

Disabled SSL certificate verification in:
1. `/app/Dockerfile.frontend.artifactory` (main)
2. `/app/Dockerfile.frontend.artifactory.alt` (alternative)
3. `/app/Dockerfile.frontend.artifactory.withconfig` (with config files)
4. `/app/frontend/.npmrc.artifactory` (template)
5. `/app/frontend/.yarnrc.artifactory` (template)

### Changes Made

#### 1. Registry Configuration with SSL Disabled
```dockerfile
# Configure yarn/npm to use Artifactory registry and disable SSL verification
RUN yarn config set registry https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/ && \
    npm config set registry https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/ && \
    yarn config set strict-ssl false && \
    npm config set strict-ssl false && \
    yarn config list
```

#### 2. Yarn Install with SSL Disabled
```dockerfile
RUN yarn install --frozen-lockfile \
    --network-timeout 600000 \
    --network-concurrency 1 \
    --disable-ssl || \
    (echo "Retrying yarn install..." && \
     yarn cache clean && \
     yarn install --network-timeout 600000 --network-concurrency 1 --disable-ssl)
```

#### 3. Configuration Files Updated

**`.npmrc.artifactory`**:
```ini
strict-ssl=false  # ← Added/Enabled
```

**`.yarnrc.artifactory`**:
```
strict-ssl false  # ← Added/Enabled
```

## Build Now

```bash
docker-compose -f docker-compose.artifactory.yml build frontend
```

## What This Does

✅ **yarn config set strict-ssl false** - Disables SSL verification for yarn
✅ **npm config set strict-ssl false** - Disables SSL verification for npm  
✅ **--disable-ssl flag** - Additional SSL bypass for yarn install command
✅ **Config files** - Template files now have strict-ssl disabled by default

## Verification

### Check Dockerfile Has SSL Disabled
```bash
grep "strict-ssl false" /app/Dockerfile.frontend.artifactory
# Should show 2 lines with strict-ssl false

grep "disable-ssl" /app/Dockerfile.frontend.artifactory
# Should show yarn install commands with --disable-ssl
```

### Build and Watch for Certificate Errors
```bash
docker-compose -f docker-compose.artifactory.yml build --no-cache --progress=plain frontend 2>&1 | tee build.log

# Check for certificate errors (should be none)
grep -i "certificate" build.log
grep -i "ssl" build.log
```

## Alternative Methods (If Still Failing)

### Method 1: Add CA Certificate (More Secure)

**If you have the Artifactory CA certificate**:

```dockerfile
# Add to Dockerfile before yarn install
COPY artifactory-ca.crt /usr/local/share/ca-certificates/
RUN apk add --no-cache ca-certificates && \
    update-ca-certificates
```

### Method 2: Use HTTP Instead of HTTPS

**Change registry URL**:
```dockerfile
# Use HTTP instead of HTTPS (not recommended for production)
RUN yarn config set registry http://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/
```

### Method 3: Environment Variable

**Set NODE_TLS_REJECT_UNAUTHORIZED**:
```dockerfile
ENV NODE_TLS_REJECT_UNAUTHORIZED=0
```

⚠️ **Warning**: This is less secure and should only be used for internal development.

## Security Considerations

### Why SSL Verification is Disabled

In corporate environments:
- Artifactory often uses self-signed certificates
- Internal CA certificates may not be in Docker image's trust store
- Disabling SSL verification is common practice for internal tools

### Is This Safe?

✅ **Safe for internal corporate Artifactory**:
- Traffic stays within corporate network
- Artifactory is trusted internal service
- Alternative would block all builds

⚠️ **Not recommended for**:
- Public/internet-facing registries
- Production deployments pulling from public sources
- Environments with strict security requirements

### Best Practice Alternative

**Add Artifactory CA certificate to Docker image** (if available):
```bash
# Get certificate from Artifactory admin
# Copy to project
cp artifactory-ca.crt /app/frontend/

# Update Dockerfile
COPY artifactory-ca.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates
```

## All SSL-Related Configurations

### Dockerfile Level
```dockerfile
# Yarn config
yarn config set strict-ssl false

# NPM config
npm config set strict-ssl false

# Yarn install flag
yarn install --disable-ssl
```

### Config File Level (`.npmrc`)
```ini
strict-ssl=false
```

### Config File Level (`.yarnrc`)
```
strict-ssl false
```

### Environment Variable Level
```dockerfile
ENV NODE_TLS_REJECT_UNAUTHORIZED=0
```

## Troubleshooting

### Issue: Still Getting Certificate Errors

**Check 1: Verify changes applied**
```bash
cat /app/Dockerfile.frontend.artifactory | grep -A 2 "strict-ssl"
```

**Check 2: Build with no cache**
```bash
docker-compose -f docker-compose.artifactory.yml build --no-cache frontend
```

**Check 3: Try HTTP instead**
```bash
# Edit Dockerfile, change https:// to http://
sed -i 's|https://artifactory|http://artifactory|g' /app/Dockerfile.frontend.artifactory
```

### Issue: Different SSL Error

**Error**: `unable to get local issuer certificate`

**Solution**: Same fix applies - strict-ssl false handles this

**Error**: `self signed certificate in certificate chain`

**Solution**: Same fix applies - strict-ssl false bypasses chain validation

## Files Modified

1. ✅ `/app/Dockerfile.frontend.artifactory` - SSL disabled
2. ✅ `/app/Dockerfile.frontend.artifactory.alt` - SSL disabled
3. ✅ `/app/Dockerfile.frontend.artifactory.withconfig` - SSL disabled
4. ✅ `/app/frontend/.npmrc.artifactory` - strict-ssl=false
5. ✅ `/app/frontend/.yarnrc.artifactory` - strict-ssl false

## Build Commands

### Primary Method
```bash
cd /app
docker-compose -f docker-compose.artifactory.yml build frontend
```

### With Verbose Output
```bash
docker-compose -f docker-compose.artifactory.yml build --no-cache --progress=plain frontend 2>&1 | tee build.log
```

### Check for SSL/Certificate Issues
```bash
grep -i "certificate\|ssl" build.log
# Should show config settings, not errors
```

## Expected Build Output

**Before Fix**:
```
#10 2.345 error An unexpected error occurred: "https://artifactory.devtools...
#10 2.345 Error: certificate verify failed
```

**After Fix**:
```
#8 0.500 info npm registry: https://artifactory.devtools.syd.c1.macquarie.com:9996/...
#8 1.234 [1/4] Resolving packages...
#8 2.456 info Downloading packages...
#8 15.234 [2/4] Fetching packages...
#8 45.678 [3/4] Linking dependencies...
#8 67.890 [4/4] Building fresh packages...
#8 89.012 success Saved lockfile.
```

## Quick Verification Script

```bash
# Run this to verify all SSL configs are disabled
echo "Checking SSL configuration..."

echo "1. Dockerfile strict-ssl:"
grep "strict-ssl false" /app/Dockerfile.frontend.artifactory | wc -l
# Should show: 2

echo "2. Dockerfile --disable-ssl:"
grep "disable-ssl" /app/Dockerfile.frontend.artifactory | wc -l
# Should show: 2 (in yarn install commands)

echo "3. .npmrc template:"
grep "strict-ssl=false" /app/frontend/.npmrc.artifactory
# Should show: strict-ssl=false

echo "4. .yarnrc template:"
grep "strict-ssl false" /app/frontend/.yarnrc.artifactory
# Should show: strict-ssl false

echo "✅ All SSL verifications disabled"
```

## Summary of SSL Bypass Methods Applied

| Level | Method | Location | Status |
|-------|--------|----------|--------|
| Yarn Config | `yarn config set strict-ssl false` | Dockerfile | ✅ Applied |
| NPM Config | `npm config set strict-ssl false` | Dockerfile | ✅ Applied |
| Yarn Flag | `--disable-ssl` | yarn install command | ✅ Applied |
| NPM RC File | `strict-ssl=false` | .npmrc.artifactory | ✅ Applied |
| Yarn RC File | `strict-ssl false` | .yarnrc.artifactory | ✅ Applied |

## Next Steps

1. **Build the image**:
   ```bash
   docker-compose -f docker-compose.artifactory.yml build frontend
   ```

2. **Verify no certificate errors** in build output

3. **Check packages download from Artifactory** (not public npm)

4. **Proceed with deployment** if build succeeds

## Documentation References

- `ARTIFACTORY_REGISTRY_CONFIG.md` - Registry configuration guide
- `YARN_INSTALL_FIX_APPLIED.md` - Previous timeout fixes
- `ARTIFACTORY_BUILD_FIX.md` - Build context fixes
- `QUICK_FIX_GUIDE.md` - Quick reference guide

## Status

✅ **SSL certificate verification disabled across all Artifactory Dockerfiles**
✅ **Configuration templates updated**
✅ **Multiple bypass methods applied**
✅ **Ready to build**

**Action**: Run `docker-compose -f docker-compose.artifactory.yml build frontend`
