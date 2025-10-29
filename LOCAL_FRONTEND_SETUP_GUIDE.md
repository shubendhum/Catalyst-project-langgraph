# Local Development Setup - Frontend on Laptop + Backend in Docker

## The Problem

You're experiencing connection issues because:

1. **Frontend:** Running on your laptop at `localhost:3000`
2. **Backend:** Running inside Docker/Kubernetes (not accessible from your laptop)
3. **Network Isolation:** Your laptop and the Docker backend are in different networks

## Solution Options

### Option 1: Run Frontend in Docker Too (RECOMMENDED)

This is the simplest - run both frontend and backend in Docker.

**Steps:**

1. **Stop your local frontend** (Ctrl+C if running)

2. **Check Docker services:**
```bash
docker ps | grep catalyst
```

3. **Access the frontend at:**
```
http://localhost:3000
```

The frontend container will connect to the backend via the Docker network.

**Frontend .env in Docker:**
The Dockerfile builds with: `REACT_APP_BACKEND_URL=http://localhost:8001`
This works because both are in the same Docker network.

---

### Option 2: Expose Backend Port to Your Laptop

If you need to run frontend locally for development, you need port forwarding.

**Problem:** The backend Docker container port 8001 is only accessible within the Kubernetes cluster, not on your laptop.

**Steps:**

1. **Check if backend is in docker-compose:**
```bash
cd /path/to/catalyst
docker-compose -f docker-compose.artifactory.yml ps
```

2. **If running in Kubernetes (like Emergent platform):**

You need to set up port forwarding from the Kubernetes pod to your laptop:

```bash
# Find the backend pod
kubectl get pods | grep backend

# Port forward (run this in a separate terminal)
kubectl port-forward <backend-pod-name> 8001:8001
```

3. **Update your local frontend/.env:**
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

4. **Restart your local frontend:**
```bash
cd frontend
yarn start
```

---

### Option 3: Use the External Backend URL

If Catalyst is deployed with an external URL (like on Emergent platform):

**Steps:**

1. **Find the backend external URL:**
   - Check your deployment
   - Look for something like: `https://your-app.emergent.com` or `http://<external-ip>:8001`

2. **Update frontend/.env:**
```bash
REACT_APP_BACKEND_URL=https://your-backend-url.com
```

3. **Restart frontend:**
```bash
cd frontend
yarn start
```

---

## Why Health Check is Failing

The Docker health check is failing because:

```yaml
# In docker-compose.artifactory.yml line 111
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8001/api/"]
```

**Possible causes:**
1. `curl` command timing out in corporate proxy
2. Backend taking longer than 60s to start
3. SSL verification issues even for localhost

**Fix the Health Check:**

Create a file `/app/docker-compose.artifactory.override.local.yml`:

```yaml
version: '3.8'

services:
  backend:
    healthcheck:
      test: ["CMD-SHELL", "python3 -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8001/api/\")' || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 90s  # Increased for corporate environments
```

**Use it:**
```bash
docker-compose -f docker-compose.artifactory.yml -f docker-compose.artifactory.override.yml -f docker-compose.artifactory.override.local.yml up -d
```

---

## Recommended Approach for Your Setup

Since you're on the Emergent platform:

**1. Find Your App's External URL:**
   - Go to Emergent Dashboard
   - Look for your app URL (something like `https://<workspace>.emergent.com`)

**2. Update Frontend .env:**
```bash
# In your local frontend/.env
REACT_APP_BACKEND_URL=https://<your-backend-url>
```

**3. Run Frontend Locally:**
```bash
cd frontend
yarn start
```

**4. Open Browser:**
```
http://localhost:3000
```

Your local frontend will now connect to the backend running in Kubernetes.

---

## Quick Debug Commands

**Check if backend is running:**
```bash
# From inside the Kubernetes pod (where backend runs)
curl http://localhost:8001/api/

# From your laptop (will fail if not port-forwarded)
curl http://localhost:8001/api/
```

**Check Docker containers:**
```bash
docker ps | grep catalyst
docker logs catalyst-backend --tail 50
```

**Check port forwarding:**
```bash
# On your laptop
netstat -an | grep 8001
# or
lsof -i :8001
```

---

## Summary

**Your Current Issue:**
- Frontend (laptop) → Cannot reach → Backend (Docker/Kubernetes)

**Quick Fix:**
1. Use Option 1: Run frontend in Docker too
2. Or find your backend external URL and update REACT_APP_BACKEND_URL

**Health Check Fix:**
- Increase `start_period` to 90s
- Use Python health check instead of curl

Let me know which option you want to use, and I'll help you implement it!
