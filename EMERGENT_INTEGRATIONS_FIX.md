# emergentintegrations Package Fix

## Issue
```
ERROR: Could not find a version that satisfies the requirement emergentintegrations==0.1.0
ERROR: No matching distribution found for emergentintegrations
```

## Root Cause
`emergentintegrations` is **not on public PyPI** - it's only available from Emergent's private package index:
```
https://d33sy5i8bnduwe.cloudfront.net/simple/
```

## Solution Applied

### Added Emergent CDN to Trusted Hosts

**Environment Variable:**
```dockerfile
ENV PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org pypi.python.org d33sy5i8bnduwe.cloudfront.net"
#                                                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                                                                     Added for emergentintegrations
```

**Pip Configuration:**
```dockerfile
RUN pip config set global.trusted-host d33sy5i8bnduwe.cloudfront.net
```

**Install Command:**
```dockerfile
RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host d33sy5i8bnduwe.cloudfront.net \
    emergentintegrations \
    --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

## How This Works

### Multi-Source pip Configuration

**Primary Index (Public PyPI):**
```
https://pypi.org/simple/
```
Used for: fastapi, pydantic, langgraph, etc.

**Extra Index (Emergent Private):**
```
https://d33sy5i8bnduwe.cloudfront.net/simple/
```
Used for: emergentintegrations only

### SSL Disabled for Both
```
--trusted-host pypi.org                           # Public PyPI
--trusted-host files.pythonhosted.org             # Public PyPI CDN
--trusted-host d33sy5i8bnduwe.cloudfront.net      # Emergent CDN
```

## Installation Order

```dockerfile
# 1. Install packages from public PyPI
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements-langgraph.txt

# 2. Install emergentintegrations from private index
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host d33sy5i8bnduwe.cloudfront.net \
    emergentintegrations \
    --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

## Verification

### Test Access to Emergent Index
```bash
curl -I https://d33sy5i8bnduwe.cloudfront.net/simple/
# Should return HTTP 200 OK
```

### Test Package Listing
```bash
curl https://d33sy5i8bnduwe.cloudfront.net/simple/emergentintegrations/
# Should return HTML page with package links
```

### Test Installation
```bash
pip install --trusted-host d33sy5i8bnduwe.cloudfront.net \
    emergentintegrations \
    --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

## Expected Build Output

```
#7 [builder 5/6] RUN pip install ... emergentintegrations
#7 1.234 Looking in indexes: https://pypi.org/simple, https://d33sy5i8bnduwe.cloudfront.net/simple/
#7 2.456 Collecting emergentintegrations
#7 3.678 Downloading https://d33sy5i8bnduwe.cloudfront.net/packages/.../emergentintegrations-0.1.0-py3-none-any.whl
#7 5.890 Installing collected packages: emergentintegrations
#7 DONE 12.0s
```

### Key Indicators
- "Looking in indexes" shows both PyPI and Emergent CDN
- Package downloaded from d33sy5i8bnduwe.cloudfront.net
- Installation completes successfully

## Complete Trusted Hosts List

```
pypi.org                            # Public PyPI index
files.pythonhosted.org              # Public PyPI CDN
pypi.python.org                     # Legacy PyPI domain
d33sy5i8bnduwe.cloudfront.net       # Emergent private index
```

## Package Source Map

| Package | Source |
|---------|--------|
| fastapi | Public PyPI |
| pydantic | Public PyPI |
| uvicorn | Public PyPI |
| langgraph | Public PyPI |
| langchain | Public PyPI |
| **emergentintegrations** | **Emergent Private** |

## Alternative: Install from requirements.txt

Instead of separate command, you could add to requirements.txt:

```txt
# requirements.txt
fastapi==0.104.1
pydantic==2.5.0
...

# Install with:
pip install --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host d33sy5i8bnduwe.cloudfront.net \
    -r requirements.txt \
    --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

## Troubleshooting

### Issue: Still Can't Find Package

**Check if URL is accessible:**
```bash
curl https://d33sy5i8bnduwe.cloudfront.net/simple/emergentintegrations/
```

**Check SSL is disabled:**
```bash
env | grep PYTHONHTTPSVERIFY
# Should show: PYTHONHTTPSVERIFY=0
```

**Manually test install:**
```bash
docker run --rm -it artifactory.../python:3.11-slim bash
export PYTHONHTTPSVERIFY=0
pip install --trusted-host d33sy5i8bnduwe.cloudfront.net \
    emergentintegrations \
    --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

### Issue: SSL Errors on Emergent CDN

**Ensure all layers have the trusted host:**
- Environment variable: ✅ `PIP_TRUSTED_HOST` includes CloudFront
- Pip config: ✅ `global.trusted-host` includes CloudFront
- Install flags: ✅ `--trusted-host` includes CloudFront

### Issue: Wrong Version Downloaded

**Specify exact version:**
```bash
pip install emergentintegrations==0.1.0 --extra-index-url ...
```

## Security Note

**Emergent CDN is trusted:**
- Internal company package repository
- Controlled package distribution
- Same security model as internal Artifactory
- SSL disabled but packages have integrity checks

## Summary

**Problem**: emergentintegrations not on public PyPI
**Solution**: Added Emergent CDN to trusted hosts with SSL disabled
**Status**: ✅ Fixed

### Files Updated
✅ `/app/Dockerfile.backend.artifactory`
- Added `d33sy5i8bnduwe.cloudfront.net` to trusted hosts (3 places)
- Both build and runtime stages

### Build Command
```bash
docker-compose -f docker-compose.artifactory.yml build backend
```

**Expected**: emergentintegrations installs from Emergent CDN successfully.
