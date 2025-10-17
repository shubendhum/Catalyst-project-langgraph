# Artifactory Docker Build Fix

## Problem Summary
Docker build errors occurred when using Artifactory mirrors due to incorrect build contexts and file path references in Dockerfiles and docker-compose configurations.

### Error Messages:
- `failed to compute cache key`
- `failed to calculate checksum`
- Files not found: `nginx.conf`, `requirements-langgraph.txt`, `yarn.lock`, `package.json`

## Root Cause
The frontend Dockerfile was using the wrong build context:
- **Build context**: `.` (root directory `/app`)
- **Expected files**: `package.json`, `yarn.lock`, `nginx.conf`
- **Actual location**: `/app/frontend/`

## Solution Applied

### 1. Frontend Dockerfile Fix (`Dockerfile.frontend.artifactory`)
**Updated build context comment** to reflect that it should be `/app/frontend`

### 2. Docker Compose Fix (`docker-compose.artifactory.yml`)
**Changed frontend build configuration:**
```yaml
# BEFORE:
frontend:
  build:
    context: .                              # Wrong: root directory
    dockerfile: Dockerfile.frontend.artifactory

# AFTER:
frontend:
  build:
    context: ./frontend                     # Correct: frontend directory
    dockerfile: ../Dockerfile.frontend.artifactory
```

## File Structure
```
/app/
├── Dockerfile.backend.artifactory          # Backend Dockerfile (uses context: .)
├── Dockerfile.frontend.artifactory         # Frontend Dockerfile (uses context: ./frontend)
├── docker-compose.artifactory.yml          # Compose file with correct contexts
├── backend/
│   ├── requirements.txt                    # Backend dependencies
│   ├── requirements-langgraph.txt          # LangGraph dependencies
│   └── ...
└── frontend/
    ├── package.json                        # Frontend dependencies
    ├── yarn.lock                           # Yarn lockfile
    ├── nginx.conf                          # Nginx configuration
    └── src/
        └── ...
```

## Build Instructions

### Using Docker Compose (Recommended)
```bash
# Build all services
docker-compose -f docker-compose.artifactory.yml build

# Build specific service
docker-compose -f docker-compose.artifactory.yml build frontend
docker-compose -f docker-compose.artifactory.yml build backend

# Build and start services
docker-compose -f docker-compose.artifactory.yml up -d
```

### Using Docker Directly

#### Backend:
```bash
# Build context is root directory (to access backend/ folder)
docker build -f Dockerfile.backend.artifactory -t catalyst-backend:latest .
```

#### Frontend:
```bash
# Build context is frontend directory
cd frontend
docker build -f ../Dockerfile.frontend.artifactory -t catalyst-frontend:latest .
cd ..
```

### Building for Artifactory Registry
```bash
# Login to Artifactory
docker login artifactory.devtools.syd.c1.macquarie.com:9996

# Build and tag backend
docker build -f Dockerfile.backend.artifactory \
  -t artifactory.devtools.syd.c1.macquarie.com:9996/catalyst-backend:latest .

# Build and tag frontend
cd frontend
docker build -f ../Dockerfile.frontend.artifactory \
  -t artifactory.devtools.syd.c1.macquarie.com:9996/catalyst-frontend:latest .
cd ..

# Push to Artifactory
docker push artifactory.devtools.syd.c1.macquarie.com:9996/catalyst-backend:latest
docker push artifactory.devtools.syd.c1.macquarie.com:9996/catalyst-frontend:latest
```

## Kubernetes Deployment

### Prerequisites
1. Artifactory credentials configured
2. Kubectl configured with cluster access
3. Namespace created: `catalyst`

### Deploy Script
```bash
# Run deployment script
chmod +x k8s/deploy-artifactory.sh
./k8s/deploy-artifactory.sh
```

### Manual Deployment
```bash
# Create namespace
kubectl create namespace catalyst

# Create Artifactory pull secret
kubectl create secret docker-registry artifactory-secret \
  --docker-server=artifactory.devtools.syd.c1.macquarie.com:9996 \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_PASSWORD \
  --docker-email=YOUR_EMAIL \
  -n catalyst

# Create app secrets
kubectl create secret generic catalyst-secrets \
  --from-literal=mongo-url=mongodb://admin:catalyst_admin_pass@mongodb:27017 \
  --from-literal=emergent-llm-key=sk-emergent-b14E29723DeDaF2A74 \
  -n catalyst

# Deploy services
kubectl apply -f k8s/mongodb-deployment.artifactory.yaml -n catalyst
kubectl apply -f k8s/backend-deployment.artifactory.yaml -n catalyst
kubectl apply -f k8s/frontend-deployment.artifactory.yaml -n catalyst
```

## Verification

### Check Build Context
```bash
# Test backend build
docker build -f Dockerfile.backend.artifactory -t test-backend .

# Test frontend build
cd frontend
docker build -f ../Dockerfile.frontend.artifactory -t test-frontend .
```

### Verify File Paths
```bash
# Check if files exist in correct locations
ls -la /app/backend/requirements*.txt
ls -la /app/frontend/package.json
ls -la /app/frontend/yarn.lock
ls -la /app/frontend/nginx.conf
```

### Test Docker Compose
```bash
# Dry-run to check configuration
docker-compose -f docker-compose.artifactory.yml config

# Build without cache to verify all paths
docker-compose -f docker-compose.artifactory.yml build --no-cache
```

## Troubleshooting

### Issue: "failed to compute cache key"
**Cause**: File not found in build context
**Solution**: Verify build context matches file locations

### Issue: "COPY failed"
**Cause**: File path doesn't exist relative to build context
**Solution**: Check that files are copied from correct paths

### Issue: nginx.conf not found
**Cause**: Frontend build context was root instead of frontend directory
**Solution**: Use `context: ./frontend` in docker-compose.yml

### Issue: Permission denied when building
**Cause**: User doesn't have access to Artifactory or files
**Solution**: 
- Login to Artifactory: `docker login artifactory.devtools.syd.c1.macquarie.com:9996`
- Check file permissions: `ls -la`

## Key Changes Summary

1. ✅ Updated `docker-compose.artifactory.yml` to use correct frontend build context
2. ✅ Updated `Dockerfile.frontend.artifactory` documentation comments
3. ✅ Verified all file paths are correct relative to their build contexts
4. ✅ Backend Dockerfile already had correct paths (context: root)
5. ✅ Frontend Dockerfile now uses correct context (frontend directory)

## Testing Checklist

- [ ] Backend builds successfully with Artifactory
- [ ] Frontend builds successfully with Artifactory
- [ ] Docker compose builds all services
- [ ] Images can be pushed to Artifactory registry
- [ ] Kubernetes deployment uses correct image references
- [ ] Services start and communicate correctly
- [ ] Health checks pass in containerized environment

## Related Files
- `/app/Dockerfile.backend.artifactory` - Backend Dockerfile
- `/app/Dockerfile.frontend.artifactory` - Frontend Dockerfile
- `/app/docker-compose.artifactory.yml` - Compose configuration
- `/app/k8s/deploy-artifactory.sh` - Kubernetes deployment script
- `/app/k8s/*-deployment.artifactory.yaml` - K8s manifests

## Additional Notes
- Backend build context remains root (`.`) to access `backend/` directory
- Frontend build context changed to `./frontend` to access frontend files
- Nginx config is now correctly copied from frontend directory
- All Python requirements are in backend directory
- All Node.js files (package.json, yarn.lock) are in frontend directory
