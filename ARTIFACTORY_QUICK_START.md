# Artifactory Docker Build - Quick Reference

## ✅ Build Fix Applied

The Docker build errors for Artifactory have been resolved by fixing the build context paths.

## 🎯 Key Changes

### Frontend Build Context
```yaml
# docker-compose.artifactory.yml
frontend:
  build:
    context: ./frontend              # ← Changed from "."
    dockerfile: ../Dockerfile.frontend.artifactory
```

This ensures Docker can find:
- `package.json`
- `yarn.lock`
- `nginx.conf`
- `src/` directory

### Backend Build Context
```yaml
# docker-compose.artifactory.yml
backend:
  build:
    context: .                       # ← Stays root (to access backend/)
    dockerfile: Dockerfile.backend.artifactory
```

This ensures Docker can find:
- `backend/requirements.txt`
- `backend/requirements-langgraph.txt`
- `backend/` directory

## 🚀 Quick Start

### 1. Login to Artifactory
```bash
docker login artifactory.devtools.syd.c1.macquarie.com:9996
# Enter username and password when prompted
```

### 2. Build with Docker Compose
```bash
# Build all services
docker-compose -f docker-compose.artifactory.yml build

# Or build individually
docker-compose -f docker-compose.artifactory.yml build backend
docker-compose -f docker-compose.artifactory.yml build frontend
```

### 3. Run Services
```bash
docker-compose -f docker-compose.artifactory.yml up -d
```

## 🔧 Manual Build Commands

### Backend
```bash
# From /app directory
docker build \
  -f Dockerfile.backend.artifactory \
  -t artifactory.devtools.syd.c1.macquarie.com:9996/catalyst-backend:latest \
  .
```

### Frontend
```bash
# From /app/frontend directory
cd frontend
docker build \
  -f ../Dockerfile.frontend.artifactory \
  -t artifactory.devtools.syd.c1.macquarie.com:9996/catalyst-frontend:latest \
  .
cd ..
```

## 📦 Push to Artifactory

```bash
# Push backend
docker push artifactory.devtools.syd.c1.macquarie.com:9996/catalyst-backend:latest

# Push frontend
docker push artifactory.devtools.syd.c1.macquarie.com:9996/catalyst-frontend:latest
```

## ☸️ Kubernetes Deployment

### Using Deploy Script (Recommended)
```bash
chmod +x k8s/deploy-artifactory.sh
./k8s/deploy-artifactory.sh
```

The script will:
1. Create namespace `catalyst`
2. Prompt for Artifactory credentials
3. Create image pull secrets
4. Deploy MongoDB, Backend, and Frontend

### Manual Deployment
```bash
# Create namespace
kubectl create namespace catalyst

# Create Artifactory secret
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

# Deploy
kubectl apply -f k8s/mongodb-deployment.artifactory.yaml -n catalyst
kubectl apply -f k8s/backend-deployment.artifactory.yaml -n catalyst
kubectl apply -f k8s/frontend-deployment.artifactory.yaml -n catalyst
```

### Check Deployment Status
```bash
# Check pods
kubectl get pods -n catalyst

# Check services
kubectl get svc -n catalyst

# View logs
kubectl logs -f deployment/catalyst-backend -n catalyst
kubectl logs -f deployment/catalyst-frontend -n catalyst
```

### Port Forward for Testing
```bash
# Frontend
kubectl port-forward service/catalyst-frontend 3000:80 -n catalyst

# Backend
kubectl port-forward service/catalyst-backend 8001:8001 -n catalyst
```

## 🔍 Verification

### Check File Structure
```bash
# Backend files
ls -la /app/backend/requirements*.txt
ls -la /app/backend/server.py

# Frontend files
ls -la /app/frontend/package.json
ls -la /app/frontend/yarn.lock
ls -la /app/frontend/nginx.conf
```

### Test Build (without cache)
```bash
# Backend
docker build --no-cache -f Dockerfile.backend.artifactory -t test-backend .

# Frontend (from frontend directory)
cd frontend
docker build --no-cache -f ../Dockerfile.frontend.artifactory -t test-frontend .
```

## 🐛 Troubleshooting

### Error: "failed to compute cache key"
**Solution**: Verify build context matches file locations
```bash
# For backend (context: .)
ls -la ./backend/requirements.txt

# For frontend (context: ./frontend)
ls -la ./frontend/package.json
```

### Error: "COPY failed: no source files"
**Solution**: Check Dockerfile COPY paths
- Backend copies from `backend/` directory (context is root)
- Frontend copies from current directory (context is ./frontend)

### Error: "unauthorized: authentication required"
**Solution**: Login to Artifactory
```bash
docker login artifactory.devtools.syd.c1.macquarie.com:9996
```

### Error: K8s pods in ImagePullBackOff
**Solution**: Verify image pull secret
```bash
# Check secret exists
kubectl get secret artifactory-secret -n catalyst

# Recreate if needed
kubectl delete secret artifactory-secret -n catalyst
kubectl create secret docker-registry artifactory-secret \
  --docker-server=artifactory.devtools.syd.c1.macquarie.com:9996 \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_PASSWORD \
  --docker-email=YOUR_EMAIL \
  -n catalyst
```

## 📋 File Reference

### Artifactory Build Files
- `Dockerfile.backend.artifactory` - Backend Dockerfile
- `Dockerfile.frontend.artifactory` - Frontend Dockerfile
- `docker-compose.artifactory.yml` - Docker Compose config
- `k8s/deploy-artifactory.sh` - Kubernetes deployment script
- `k8s/*-deployment.artifactory.yaml` - Kubernetes manifests

### Documentation
- `ARTIFACTORY_BUILD_FIX.md` - Detailed fix documentation
- `ARTIFACTORY_QUICK_START.md` - This file

## 🎓 Build Context Explained

**Build Context** is the directory Docker uses as the base for COPY commands.

### Backend Example
```dockerfile
# Context: . (root /app)
COPY backend/requirements.txt ./
# Copies from: /app/backend/requirements.txt
# To: /app/requirements.txt (in container)
```

### Frontend Example
```dockerfile
# Context: ./frontend (/app/frontend)
COPY package.json yarn.lock ./
# Copies from: /app/frontend/package.json
# To: /app/package.json (in container)
```

## ✨ What's Fixed

1. ✅ Frontend build context changed from `.` to `./frontend`
2. ✅ Frontend Dockerfile path updated in docker-compose
3. ✅ All COPY commands now reference correct paths
4. ✅ nginx.conf correctly copied from frontend directory
5. ✅ package.json and yarn.lock accessible from build context
6. ✅ Backend build context remains root (correct)

## 🎯 Testing Checklist

- [ ] Backend builds without errors
- [ ] Frontend builds without errors
- [ ] Both services start in Docker Compose
- [ ] Images can be pushed to Artifactory
- [ ] K8s deployment succeeds
- [ ] Pods reach Running state
- [ ] Health checks pass
- [ ] Frontend serves UI correctly
- [ ] Backend API responds correctly
- [ ] Chat interface works end-to-end

## 📞 Support

For issues or questions:
1. Check documentation in `ARTIFACTORY_BUILD_FIX.md`
2. Verify file structure and paths
3. Review Docker build output for specific errors
4. Check Kubernetes logs if deploying to K8s

## 🔗 Related Documentation
- `README.md` - Main project documentation
- `DEPLOYMENT.md` - General deployment guide
- `DEPLOYMENT_GUIDE.md` - Comprehensive deployment docs
- `DOCKER_BUILD_TROUBLESHOOTING.md` - Docker build troubleshooting
