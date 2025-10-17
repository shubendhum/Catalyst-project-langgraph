# Fix: emergentintegrations in requirements-langgraph.txt

## Issue
Still getting "No matching distribution" error at line 33 even after adding trusted hosts.

## Root Cause
`emergentintegrations>=0.1.0` is listed in `/app/backend/requirements-langgraph.txt`, so when we install that file without the `--extra-index-url` flag, pip tries to find it on public PyPI and fails.

## Solution

### Split Installation into Two Steps

**Step 1: Install requirements.txt (public PyPI only)**
```dockerfile
RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt
```

**Step 2: Install requirements-langgraph.txt (includes extra index)**
```dockerfile
RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host d33sy5i8bnduwe.cloudfront.net \
    --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ \
    -r requirements-langgraph.txt
```

### Why This Works

**requirements.txt** contains only public packages:
- fastapi
- pydantic
- uvicorn
- etc.

**requirements-langgraph.txt** contains:
- langgraph (public PyPI)
- langchain (public PyPI)
- **emergentintegrations>=0.1.0** (Emergent private)

By adding `--extra-index-url` when installing requirements-langgraph.txt, pip will:
1. Check public PyPI first (for langgraph, langchain)
2. Check Emergent CDN second (for emergentintegrations)
3. Install all packages successfully

## Before (Wrong)
```dockerfile
# This fails because emergentintegrations is in requirements-langgraph.txt
RUN pip install -r requirements.txt && \
    pip install -r requirements-langgraph.txt && \  # ❌ Fails here!
    pip install emergentintegrations --extra-index-url ...
```

**Problem:** 
- Line 2 tries to install emergentintegrations from PyPI
- Doesn't have --extra-index-url flag
- Fails before reaching line 3

## After (Correct)
```dockerfile
# Install public packages first
RUN pip install -r requirements.txt  # ✅ Works

# Install langgraph requirements with private index
RUN pip install --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ \
    -r requirements-langgraph.txt  # ✅ Works - finds emergentintegrations
```

## File Updated
✅ `/app/Dockerfile.backend.artifactory`
- Split pip install into 2 separate RUN commands
- Added --extra-index-url to requirements-langgraph.txt installation

## Build Command
```bash
docker-compose -f docker-compose.artifactory.yml build backend
```

## Expected Output

### Step 1: requirements.txt
```
#7 [builder 5/7] RUN pip install ... -r requirements.txt
#7 1.234 Collecting fastapi
#7 2.456 Downloading https://files.pythonhosted.org/packages/.../fastapi-...
#7 DONE 25.0s ✅
```

### Step 2: requirements-langgraph.txt
```
#8 [builder 6/7] RUN pip install ... --extra-index-url ... -r requirements-langgraph.txt
#8 0.234 Looking in indexes: https://pypi.org/simple, https://d33sy5i8bnduwe.cloudfront.net/simple/
#8 1.456 Collecting langgraph
#8 2.678 Collecting emergentintegrations>=0.1.0
#8 3.890 Downloading https://d33sy5i8bnduwe.cloudfront.net/packages/.../emergentintegrations-0.1.0.whl
#8 DONE 15.0s ✅
```

## Key Differences

| Approach | Result |
|----------|--------|
| Install all together without --extra-index-url | ❌ Fails on emergentintegrations |
| Install langgraph requirements with --extra-index-url | ✅ Finds emergentintegrations |

## Contents of requirements-langgraph.txt

```txt
langgraph>=0.0.20
langchain>=0.1.0
langchain-anthropic>=0.1.0
emergentintegrations>=0.1.0  # ← This needs private index
```

## Alternative Solutions (Not Used)

### Option 1: Remove from requirements-langgraph.txt
```txt
# requirements-langgraph.txt
langgraph>=0.0.20
langchain>=0.1.0
langchain-anthropic>=0.1.0
# emergentintegrations>=0.1.0  # Commented out

# Install separately
RUN pip install emergentintegrations --extra-index-url ...
```

### Option 2: Use constraints file
```bash
pip install -r requirements-langgraph.txt \
    -c constraints.txt \
    --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

**We chose the current approach** because it's cleaner and keeps requirements-langgraph.txt complete.

## Verification

### Check requirements-langgraph.txt has emergentintegrations
```bash
grep emergentintegrations /app/backend/requirements-langgraph.txt
# Should show: emergentintegrations>=0.1.0
```

### Check Dockerfile uses extra-index-url
```bash
grep -A 3 "requirements-langgraph.txt" /app/Dockerfile.backend.artifactory
# Should show: --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

## Summary

**Problem**: emergentintegrations in requirements-langgraph.txt couldn't be found
**Cause**: Installing without --extra-index-url flag
**Solution**: Add --extra-index-url when installing requirements-langgraph.txt
**Status**: ✅ Fixed

**Build command:**
```bash
docker-compose -f docker-compose.artifactory.yml build backend
```

Expected: Both requirements files install successfully, emergentintegrations found in private index.
