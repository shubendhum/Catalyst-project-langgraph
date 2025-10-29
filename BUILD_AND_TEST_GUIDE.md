# Build and Test Guide - HuggingFace Model Caching

## Overview
This guide walks through building and testing the Docker image with pre-cached HuggingFace models, eliminating runtime SSL issues in corporate proxy environments.

---

## Build Instructions

### 1. Clean Previous Build (Optional)
```bash
# Remove old images to ensure fresh build
docker-compose -f docker-compose.artifactory.yml down
docker rmi catalyst-backend-artifactory 2>/dev/null || true
```

### 2. Build Backend Image
```bash
# Build with the new Dockerfile
make build-artifactory

# OR directly:
docker-compose -f docker-compose.artifactory.yml build backend
```

### 3. Watch for Build Success Indicators

During the build, you should see these messages:

```
Step X: Downloading HuggingFace models with requests 2.27.1 for SSL compatibility...
Downloading all-MiniLM-L6-v2...
Downloading (…)e9125/.gitattributes: 100%|██████████| ...
Downloading (…)_Pooling/config.json: 100%|██████████| ...
Downloading (…)b20bca/.gitattributes: 100%|██████████| ...
Downloading (…)model.safetensors: 100%|██████████| 90.9M/90.9M ...
Model cached successfully!
HuggingFace models cached, requests upgraded to 2.32.5
```

**Build Time:** Expect ~5-10 minutes depending on your network speed (model is ~90MB)

---

## Verification Steps

### 4. Inspect Built Image

```bash
# Check if model cache exists in the image
docker run --rm catalyst-backend-artifactory ls -lah /home/catalyst/.cache/huggingface

# Should show:
# drwxr-xr-x catalyst catalyst .
# drwxr-xr-x catalyst catalyst ..
# drwxr-xr-x catalyst catalyst hub
# drwxr-xr-x catalyst catalyst sentence-transformers
```

### 5. Check requests Version

```bash
# Verify requests is at 2.32.5 in final image
docker run --rm catalyst-backend-artifactory pip show requests | grep Version

# Should output:
# Version: 2.32.5
```

---

## Start and Test

### 6. Start Services

```bash
make start-artifactory

# OR directly:
docker-compose -f docker-compose.artifactory.yml up -d
```

### 7. Monitor Backend Startup

```bash
# Follow backend logs
docker-compose -f docker-compose.artifactory.yml logs -f backend

# Watch for these SUCCESS indicators:
# ✅ "Load pretrained SentenceTransformer: all-MiniLM-L6-v2" (should be INSTANT)
# ✅ "Loaded sentence-transformers embedding model"
# ✅ "Catalyst Backend Starting..."
# ✅ "Application startup complete"
```

**Expected Startup Time:** <5 seconds (no model download!)

### 8. Verify No SSL Errors

```bash
# Check for SSL-related errors (should be NONE)
docker-compose -f docker-compose.artifactory.yml logs backend | grep -i "ssl\|certificate\|verify"

# Should only show:
# "SSL verification disabled for HuggingFace downloads"
# No errors or warnings about SSL verification failures
```

---

## Success Criteria Checklist

- [ ] **Build Success**: Docker build completes without errors
- [ ] **Model Download**: Build logs show "Model cached successfully!"
- [ ] **Version Check**: Runtime uses requests==2.32.5
- [ ] **Cache Present**: /home/catalyst/.cache/huggingface exists in container
- [ ] **Fast Startup**: Backend starts in <5 seconds
- [ ] **No Downloads**: No "Downloading" messages in runtime logs
- [ ] **No SSL Errors**: No SSL verification failures at runtime
- [ ] **Model Loaded**: "Loaded sentence-transformers embedding model" appears
- [ ] **API Working**: Backend responds to health check

---

## Testing Backend API

### 9. Test Health Endpoint

```bash
# Inside container
curl http://localhost:8001/api/

# OR from host (if ports mapped)
curl http://localhost:8001/api/
```

### 10. Test Learning Service

The learning service uses the cached sentence-transformers model:

```bash
# Check if learning service initialized
docker-compose -f docker-compose.artifactory.yml logs backend | grep "learning_service"

# Should show:
# ✅ Loaded sentence-transformers embedding model
```

---

## Troubleshooting

### Problem: Build fails during model download

**Symptoms:**
```
ERROR: Could not connect to...
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solutions:**
1. Check your corporate proxy settings
2. Verify SSL bypass environment variables in Dockerfile
3. Try building with `--no-cache`:
   ```bash
   docker-compose -f docker-compose.artifactory.yml build --no-cache backend
   ```

### Problem: Models still download at runtime

**Symptoms:**
```
Downloading (…)model.safetensors: ...
```

**Solutions:**
1. Check if cache was copied correctly:
   ```bash
   docker exec catalyst-backend ls -la /home/catalyst/.cache/huggingface
   ```
2. Verify environment variables:
   ```bash
   docker exec catalyst-backend env | grep HF_HOME
   ```
3. Rebuild image ensuring cache copy step succeeds

### Problem: Permission errors accessing cache

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/home/catalyst/.cache/huggingface/...'
```

**Solutions:**
1. Check ownership:
   ```bash
   docker exec catalyst-backend ls -ln /home/catalyst/.cache
   ```
2. Should show uid=1000 gid=1000 (catalyst user)
3. If incorrect, rebuild image - RUN chown command may have failed

### Problem: Backend starts but model not found

**Symptoms:**
```
OSError: all-MiniLM-L6-v2 does not appear to be a valid model
```

**Solutions:**
1. Verify cache contents:
   ```bash
   docker exec catalyst-backend find /home/catalyst/.cache/huggingface -name "*.safetensors"
   ```
2. Should find pytorch_model.bin or model.safetensors
3. If empty, rebuild image - download step may have failed

---

## Performance Comparison

### Before (Runtime Download with SSL Issues):
- 🐌 Startup: 30-60 seconds
- ❌ SSL errors: Frequent failures
- 📡 Network: Required internet access
- 🔄 Consistency: Different models per container

### After (Build-Time Caching):
- ⚡ Startup: <5 seconds
- ✅ SSL errors: None
- 📴 Network: No internet needed at runtime
- 🎯 Consistency: Same models across all containers

---

## Integration with CI/CD

For automated builds in your CI/CD pipeline:

```yaml
# Example GitLab CI
build-backend:
  stage: build
  script:
    - docker build -f Dockerfile.backend.artifactory -t catalyst-backend:$CI_COMMIT_SHA .
    # Verify model was cached
    - docker run --rm catalyst-backend:$CI_COMMIT_SHA ls /home/catalyst/.cache/huggingface/hub
  artifacts:
    reports:
      build_log: build.log
```

---

## Next Steps

After successful build and test:

1. ✅ Tag the working image
2. ✅ Push to your registry
3. ✅ Update docker-compose.yml to use new image
4. ✅ Deploy to staging/production
5. ✅ Monitor startup times and logs

---

## Support

If you encounter issues not covered in this guide:
1. Check Docker build logs: `docker-compose -f docker-compose.artifactory.yml build backend 2>&1 | tee build.log`
2. Check runtime logs: `docker-compose -f docker-compose.artifactory.yml logs backend > runtime.log`
3. Review the complete fixes documentation: `/app/FIXES_APPLIED_OCT_28_2025.md`

---

**Last Updated:** October 28, 2025
**Docker Strategy:** Multi-stage build with requests downgrade/upgrade
**Model:** sentence-transformers/all-MiniLM-L6-v2 (90.9 MB)
