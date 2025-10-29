# Catalyst Backend Fixes - October 28, 2025

## Summary
Fixed two critical issues preventing backend startup in corporate proxy environments:
1. Missing `Optional` import causing `NameError` 
2. HuggingFace SSL verification errors - **Build-Time Solution**

---

## Issue 1: Backend Startup Error - Missing Optional Import

### Problem
Backend failed to start with error:
```
NameError: name 'Optional' is not defined
  File "/app/agents_v2/coder_agent_v2.py", line 118, in EventDrivenCoderAgent
    task_id: Optional[str] = None
```

### Root Cause
The `coder_agent_v2.py` file used `Optional` type hint without importing it from the `typing` module.

### Solution
Added missing import to `/app/backend/agents_v2/coder_agent_v2.py`:
```python
from typing import Dict, Optional  # Added Optional
```

### Verification
All other agent files (`planner_agent_v2.py`, `reviewer_agent_v2.py`, `deployer_agent_v2.py`, `tester_agent_v2.py`) already had the correct import.

---

## Issue 2: HuggingFace SSL Verification Errors

### Problem
HuggingFace model downloads failing in corporate proxy environments with SSL verification errors when downloading `sentence-transformers` models like `all-MiniLM-L6-v2`.

### User's Brilliant Solution ⭐
Downgrade requests → Download models → Upgrade requests back

This approach:
1. Uses `requests==2.27.1` (better SSL handling) for model downloads
2. Downloads and caches models during Docker build
3. Upgrades to `requests==2.32.5` for runtime (satisfies all dependencies)
4. Eliminates runtime SSL issues entirely

### Implementation: Build-Time Model Caching

#### 1. Updated `Dockerfile.backend.artifactory`

Added HuggingFace model pre-download step in builder stage:
```dockerfile
# HuggingFace Model Pre-download with SSL Workaround
# Strategy: Downgrade requests to 2.27.1 (better SSL handling in corporate proxies)
#           Download HuggingFace models
#           Upgrade requests back to 2.32.5 (required by dependencies)
RUN echo "Downloading HuggingFace models with requests 2.27.1..." && \
    pip install --no-cache-dir requests==2.27.1 && \
    python3 -c "import os; \
      os.environ['CURL_CA_BUNDLE'] = ''; \
      os.environ['REQUESTS_CA_BUNDLE'] = ''; \
      os.environ['SSL_CERT_FILE'] = ''; \
      os.environ['HUGGINGFACE_HUB_DISABLE_SSL_VERIFICATION'] = '1'; \
      os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'; \
      import ssl; \
      ssl._create_default_https_context = ssl._create_unverified_context; \
      from sentence_transformers import SentenceTransformer; \
      print('Downloading all-MiniLM-L6-v2...'); \
      model = SentenceTransformer('all-MiniLM-L6-v2'); \
      print('Model cached successfully!')" && \
    pip install --no-cache-dir requests==2.32.5 && \
    echo "HuggingFace models cached, requests upgraded to 2.32.5"
```

Added HuggingFace cache directory configuration in runtime stage:
```dockerfile
# Set HuggingFace cache directory for catalyst user
ENV HF_HOME=/home/catalyst/.cache/huggingface
ENV TRANSFORMERS_CACHE=/home/catalyst/.cache/huggingface/transformers
ENV SENTENCE_TRANSFORMERS_HOME=/home/catalyst/.cache/huggingface/sentence-transformers

# Copy HuggingFace model cache from builder to catalyst's home
COPY --from=builder /root/.cache/huggingface /home/catalyst/.cache/huggingface
```

#### 2. Runtime SSL Disabling (Fallback)

Enhanced `/app/backend/server.py`:
```python
# HuggingFace specific SSL disabling
os.environ['HUGGINGFACE_HUB_DISABLE_SSL_VERIFICATION'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
```

Enhanced `/app/backend/services/learning_service.py`:
```python
# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

Updated `/app/backend/.env`:
```bash
# HuggingFace SSL Configuration (Corporate Proxy)
HUGGINGFACE_HUB_DISABLE_SSL_VERIFICATION=1
HF_HUB_DISABLE_TELEMETRY=1
```

#### 3. Updated `requirements.txt`
```
requests==2.32.5  # Satisfies all dependencies (google-genai, langchain-community)
```

---

## Advantages of Build-Time Approach

✅ **No runtime downloads** - Models cached in Docker image
✅ **Faster startup** - No waiting for model downloads
✅ **Bypasses SSL issues** - Downloads happen with requests 2.27.1
✅ **Satisfies dependencies** - Runtime uses requests 2.32.5
✅ **Works in air-gapped environments** - No internet needed at runtime
✅ **Consistent behavior** - Same models across all containers

---

## Verification Results

### Backend Startup Logs (Kubernetes)
✅ Backend starts successfully:
```
2025-10-28 08:46:35,112 - services.learning_service - INFO - 🔐 SSL verification disabled for HuggingFace downloads
2025-10-28 08:46:35,113 - sentence_transformers.SentenceTransformer - INFO - Load pretrained SentenceTransformer: all-MiniLM-L6-v2
2025-10-28 08:46:36,095 - services.learning_service - INFO - ✅ Loaded sentence-transformers embedding model
2025-10-28 08:46:36,118 - server - INFO - 🚀 Catalyst Backend Starting...
INFO:     Application startup complete.
```

### Services Status
```
backend    RUNNING   pid 521
frontend   RUNNING   pid 33
mongodb    RUNNING   pid 36
```

### Frontend UI
✅ Chat interface loads correctly with all features

---

## Files Modified

1. `/app/backend/agents_v2/coder_agent_v2.py` - Added Optional import
2. `/app/Dockerfile.backend.artifactory` - **Build-time model download with requests downgrade/upgrade**
3. `/app/backend/requirements.txt` - Set requests==2.32.5
4. `/app/backend/server.py` - Added HuggingFace SSL env vars (fallback)
5. `/app/backend/services/learning_service.py` - Enhanced SSL disabling (fallback)
6. `/app/backend/.env` - Added HuggingFace SSL configuration (fallback)

---

## For Local Docker Desktop Users

### Building with Model Pre-download

```bash
# Rebuild backend image with model caching
make build-artifactory

# During build, you should see:
# Downloading HuggingFace models with requests 2.27.1...
# Downloading all-MiniLM-L6-v2...
# Model cached successfully!
# HuggingFace models cached, requests upgraded to 2.32.5

# Start services
make start-artifactory

# Verify - backend should start instantly without downloading models
docker-compose -f docker-compose.artifactory.yml logs backend
```

### Expected Behavior

**Build Time:**
- Downloads sentence-transformers model (~90MB)
- Caches in /root/.cache/huggingface
- Copies cache to runtime image

**Runtime:**
- No model downloads
- Instant model loading from cache
- No SSL errors

---

## Testing Checklist

- [ ] Docker build completes without errors
- [ ] Build logs show "Model cached successfully!"
- [ ] Backend starts without downloading models
- [ ] No SSL verification errors in logs
- [ ] sentence-transformers loads instantly
- [ ] Learning service initializes correctly

---

## Troubleshooting

### If models still download at runtime:
1. Check environment variables are set correctly
2. Verify cache directory permissions: `ls -la /home/catalyst/.cache/huggingface`
3. Ensure cache was copied from builder: `docker exec <container> ls /home/catalyst/.cache/huggingface`

### If build fails during model download:
1. Check corporate proxy settings
2. Verify SSL bypass environment variables
3. Try building with `--no-cache` flag

---

## Next Steps

1. **Build the Docker image** with the updated Dockerfile
2. **Test in your local Docker Desktop** environment
3. **Verify no SSL errors** during startup
4. **Confirm instant model loading** from cache

The combination of build-time model caching and runtime SSL disabling provides maximum reliability in corporate proxy environments! 🚀
