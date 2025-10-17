# Artifactory Configuration for Catalyst

## Overview

This guide explains how to configure Catalyst to use your organization's Artifactory mirror instead of Docker Hub.

**Artifactory Details**:
- URL: `artifactory.devtools.syd.c1.macquarie.com`
- Port: `9996`
- Full URL: `artifactory.devtools.syd.c1.macquarie.com:9996`

---

## Quick Start

### Using Artifactory Docker Files

```bash
# 1. Use Artifactory docker-compose
docker-compose -f docker-compose.artifactory.yml up -d

# Or with Makefile
make setup-artifactory
make start-artifactory
```

---

## Setup Methods

### Method 1: Docker Compose (Recommended)

**Use the Artifactory-specific compose file**:

```bash
# Build and start
docker-compose -f docker-compose.artifactory.yml up -d --build

# View logs
docker-compose -f docker-compose.artifactory.yml logs -f

# Stop
docker-compose -f docker-compose.artifactory.yml down
```

---

### Method 2: Docker Build Directly

**Build images using Artifactory Dockerfiles**:

```bash
# Backend
docker build -f Dockerfile.backend.artifactory -t catalyst-backend:latest .

# Frontend
docker build -f Dockerfile.frontend.artifactory -t catalyst-frontend:latest .
```

---

### Method 3: Configure Docker Daemon (Global)

**Set Artifactory as default registry mirror**:

**Linux/macOS** (`/etc/docker/daemon.json`):
```json
{
  "registry-mirrors": ["https://artifactory.devtools.syd.c1.macquarie.com:9996"],
  "insecure-registries": ["artifactory.devtools.syd.c1.macquarie.com:9996"]
}
```

**Windows** (Docker Desktop Settings → Docker Engine):
```json
{
  "registry-mirrors": ["https://artifactory.devtools.syd.c1.macquarie.com:9996"],
  "insecure-registries": ["artifactory.devtools.syd.c1.macquarie.com:9996"]
}
```

**Restart Docker**:
```bash
# Linux
sudo systemctl restart docker

# macOS/Windows
# Restart Docker Desktop
```

---

## Images Using Artifactory

### Base Images

All images are pulled from Artifactory:

| Original | Artifactory Mirror |
|----------|--------------------|
| `python:3.11-slim` | `artifactory.devtools.syd.c1.macquarie.com:9996/python:3.11-slim` |
| `node:18-alpine` | `artifactory.devtools.syd.c1.macquarie.com:9996/node:18-alpine` |
| `nginx:alpine` | `artifactory.devtools.syd.c1.macquarie.com:9996/nginx:alpine` |
| `mongo:5.0` | `artifactory.devtools.syd.c1.macquarie.com:9996/mongo:5.0` |

---

## Files Created

### 1. Dockerfile.backend.artifactory

**Multi-stage Dockerfile** for backend with Artifactory:
```dockerfile
FROM artifactory.devtools.syd.c1.macquarie.com:9996/python:3.11-slim as builder
# ... build stage

FROM artifactory.devtools.syd.c1.macquarie.com:9996/python:3.11-slim
# ... runtime stage
```

### 2. Dockerfile.frontend.artifactory

**Multi-stage Dockerfile** for frontend with Artifactory:
```dockerfile
FROM artifactory.devtools.syd.c1.macquarie.com:9996/node:18-alpine as builder
# ... build stage

FROM artifactory.devtools.syd.c1.macquarie.com:9996/nginx:alpine
# ... runtime stage
```

### 3. docker-compose.artifactory.yml

**Docker Compose** using Artifactory images:
```yaml
services:
  mongodb:
    image: artifactory.devtools.syd.c1.macquarie.com:9996/mongo:5.0
  
  backend:
    build:
      dockerfile: Dockerfile.backend.artifactory
  
  frontend:
    build:
      dockerfile: Dockerfile.frontend.artifactory
```

---

## Makefile Integration

Use Makefile commands for Artifactory:

```bash
make setup-artifactory      # Setup with Artifactory
make start-artifactory      # Start with Artifactory
make stop-artifactory       # Stop Artifactory services
make build-artifactory      # Build Artifactory images
make logs-artifactory       # View Artifactory logs
```

---

## Kubernetes Deployment

### Update Image References

**MongoDB Deployment** (`k8s/mongodb-deployment.yaml`):
```yaml
spec:
  containers:
  - name: mongodb
    image: artifactory.devtools.syd.c1.macquarie.com:9996/mongo:5.0
```

**Backend Deployment** (`k8s/backend-deployment.yaml`):
```yaml
spec:
  containers:
  - name: backend
    image: artifactory.devtools.syd.c1.macquarie.com:9996/catalyst-backend:latest
```

**Frontend Deployment** (`k8s/frontend-deployment.yaml`):
```yaml
spec:
  containers:
  - name: frontend
    image: artifactory.devtools.syd.c1.macquarie.com:9996/catalyst-frontend:latest
```

### Create Image Pull Secret

If Artifactory requires authentication:

```bash
# Create secret
kubectl create secret docker-registry artifactory-secret \
  --docker-server=artifactory.devtools.syd.c1.macquarie.com:9996 \
  --docker-username=your-username \
  --docker-password=your-password \
  --docker-email=your-email@company.com \
  -n catalyst

# Reference in deployment
spec:
  imagePullSecrets:
  - name: artifactory-secret
```

---

## Troubleshooting

### Image Pull Errors

**Error**: `Error response from daemon: Get https://registry-1.docker.io/v2/`

**Solution**: Verify Artifactory files are being used:
```bash
# Check which compose file
docker-compose -f docker-compose.artifactory.yml config

# Check Dockerfile
cat Dockerfile.backend.artifactory | grep FROM
```

---

### Connection Timeout

**Error**: `dial tcp: lookup artifactory.devtools.syd.c1.macquarie.com: no such host`

**Solution**:
1. Verify VPN connection
2. Test connectivity:
   ```bash
   ping artifactory.devtools.syd.c1.macquarie.com
   curl -I https://artifactory.devtools.syd.c1.macquarie.com:9996
   ```
3. Check DNS resolution:
   ```bash
   nslookup artifactory.devtools.syd.c1.macquarie.com
   ```

---

### Authentication Errors

**Error**: `unauthorized: authentication required`

**Solution**: Login to Artifactory:
```bash
docker login artifactory.devtools.syd.c1.macquarie.com:9996
# Enter username and password
```

---

### SSL/TLS Errors

**Error**: `x509: certificate signed by unknown authority`

**Solution 1** - Add to insecure registries:
```json
{
  "insecure-registries": ["artifactory.devtools.syd.c1.macquarie.com:9996"]
}
```

**Solution 2** - Add CA certificate:
```bash
# Linux
sudo cp artifactory-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# macOS
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain artifactory-ca.crt
```

---

## CI/CD Integration

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    stages {
        stage('Build') {
            steps {
                sh 'docker-compose -f docker-compose.artifactory.yml build'
            }
        }
        
        stage('Push to Artifactory') {
            steps {
                sh '''
                    docker tag catalyst-backend:latest artifactory.devtools.syd.c1.macquarie.com:9996/catalyst-backend:latest
                    docker push artifactory.devtools.syd.c1.macquarie.com:9996/catalyst-backend:latest
                '''
            }
        }
    }
}
```

### GitLab CI

```yaml
build:
  stage: build
  script:
    - docker login -u $ARTIFACTORY_USER -p $ARTIFACTORY_PASSWORD artifactory.devtools.syd.c1.macquarie.com:9996
    - docker-compose -f docker-compose.artifactory.yml build
    - docker-compose -f docker-compose.artifactory.yml push
```

---

## Verification

### Check Image Source

```bash
# Inspect built image
docker image inspect catalyst-backend:latest | grep -i artifactory

# Should show Artifactory in layers
```

### Test Build

```bash
# Build backend
docker build -f Dockerfile.backend.artifactory -t test-backend .

# Build frontend
docker build -f Dockerfile.frontend.artifactory -t test-frontend .

# Verify successful build
docker images | grep test
```

### Test Run

```bash
# Start services
docker-compose -f docker-compose.artifactory.yml up -d

# Check logs
docker-compose -f docker-compose.artifactory.yml logs

# Verify running
curl http://localhost:8001/api/
curl http://localhost:3000/
```

---

## Best Practices

### 1. Use Specific Tags

❌ **Avoid**:
```dockerfile
FROM artifactory.devtools.syd.c1.macquarie.com:9996/python:latest
```

✅ **Use**:
```dockerfile
FROM artifactory.devtools.syd.c1.macquarie.com:9996/python:3.11-slim
```

### 2. Cache Authentication

```bash
# Save credentials
docker login artifactory.devtools.syd.c1.macquarie.com:9996

# Credentials saved in ~/.docker/config.json
```

### 3. Use Build Args

```dockerfile
ARG ARTIFACTORY_URL=artifactory.devtools.syd.c1.macquarie.com:9996
FROM ${ARTIFACTORY_URL}/python:3.11-slim
```

### 4. Image Scanning

```bash
# Scan images for vulnerabilities
docker scan artifactory.devtools.syd.c1.macquarie.com:9996/catalyst-backend:latest
```

---

## Support

### Internal Support

- **Artifactory Admin**: Contact your DevOps team
- **Network Issues**: Contact IT support
- **VPN Access**: Contact security team

### Documentation

- **Artifactory Docs**: Internal wiki
- **Docker Docs**: https://docs.docker.com
- **Catalyst Docs**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## Summary

✅ **Artifactory-specific files created**:
- `Dockerfile.backend.artifactory`
- `Dockerfile.frontend.artifactory`
- `docker-compose.artifactory.yml`

✅ **All images use Artifactory mirror**:
- Python, Node, Nginx, MongoDB

✅ **Multiple deployment methods**:
- Docker Compose
- Docker build
- Kubernetes
- CI/CD pipelines

✅ **Troubleshooting guide included**

---

**Your Catalyst deployment now uses Artifactory mirror exclusively!** 🎉
