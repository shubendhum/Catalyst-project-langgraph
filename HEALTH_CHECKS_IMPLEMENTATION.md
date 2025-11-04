# End-to-End Health Checks Implementation Guide

## Overview
This document describes the comprehensive health check system for Docker Desktop deployment.

---

## Backend Changes

### 1. Health Check Router (`/app/backend/routers/health.py`)

**Created:** New health check router with multiple endpoints

**Endpoints:**

#### `GET /api/health`
- **Purpose:** Comprehensive health check of all dependencies
- **Response:** JSON with status of MongoDB, Redis, Qdrant, and LLM
- **Status Codes:** 
  - 200: System healthy or degraded (with fallbacks)
  - 503: System unhealthy (critical services down)

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-30T12:34:56.789Z",
  "dependencies": {
    "mongodb": {
      "status": "healthy",
      "version": "5.0.27"
    },
    "redis": {
      "status": "healthy",
      "version": "7.0.12",
      "connected_clients": 3
    },
    "qdrant": {
      "status": "degraded",
      "message": "Qdrant library not available, using in-memory fallback",
      "collections_count": 0
    },
    "model": {
      "status": "healthy",
      "provider": "emergent",
      "model": "claude-3-7-sonnet-20250219",
      "key_configured": true
    }
  }
}
```

#### `GET /api/health/ready`
- **Purpose:** Kubernetes-style readiness probe
- **Checks:** MongoDB only (critical dependency)
- **Status Codes:** 200 (ready) or 503 (not ready)

#### `GET /api/health/live`
- **Purpose:** Kubernetes-style liveness probe
- **Checks:** Service is alive
- **Status Codes:** 200 always (unless server is dead)

**Dependency Checks:**

1. **MongoDB** - Critical
   - Pings database
   - Returns version
   - 2-second timeout

2. **Redis** - Optional (has fallback)
   - Pings Redis
   - Returns version, uptime, client count
   - Falls back to in-memory cache if unavailable

3. **Qdrant** - Optional (has fallback)
   - Lists collections
   - Falls back to in-memory vector store if unavailable

4. **LLM Model** - Critical
   - Checks if EMERGENT_LLM_KEY is set
   - Returns provider and model name
   - Shows key prefix for verification

### 2. Wire Router in Main Application

**File:** `/app/backend/server.py`

**Add to imports:**
```python
from routers.health import router as health_router
```

**Add to app initialization:**
```python
# Health check routes
app.include_router(health_router, prefix="/api")
```

---

## Frontend Changes

### 1. Status Page Component (`/app/frontend/src/pages/Status.tsx`)

**Features:**
- Traffic-light cards for each dependency (green/amber/red)
- Auto-refresh every 10 seconds
- Manual refresh button
- Last refresh timestamp
- Overall system status badge
- Detailed status information per dependency

**Status Colors:**
- 🟢 Green: `healthy` - Service operational
- 🟡 Amber: `degraded` - Service unavailable but has fallback
- 🔴 Red: `unhealthy` - Service down, no fallback

**Card Information:**
- MongoDB: Version, connection status
- Redis: Version, connected clients
- Qdrant: Collection count
- LLM Model: Provider, model name, key status

### 2. Status Page Styling (`/app/frontend/src/pages/Status.css`)

**Features:**
- Responsive grid layout (auto-fit, min 280px)
- Card-based design with hover effects
- Color-coded status indicators
- Dark mode support
- Mobile-friendly

### 3. Add Route to Application

**File:** `/app/frontend/src/App.js` or `/app/frontend/src/App.tsx`

**Add import:**
```javascript
import Status from './pages/Status';
```

**Add route:**
```javascript
<Route path="/status" element={<Status />} />
```

### 4. Add Navbar Link

**File:** Your navbar component (e.g., `/app/frontend/src/components/Navbar.js`)

**Add link:**
```javascript
<Link to="/status">Status</Link>
```

---

## Docker Compose Changes

### Update `docker-compose.yml` or `docker-compose.artifactory.yml`

**Add healthchecks for each service:**

```yaml
services:
  # API/Backend Service
  backend:
    # ... existing config ...
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8001/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 90s

  # Frontend Service
  frontend:
    # ... existing config ...
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:3000/"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s

  # Redis Service
  redis:
    # ... existing config ...
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 10s

  # Qdrant Service
  qdrant:
    # ... existing config ...
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:6333/readyz"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
```

**Health Check Parameters:**
- `test`: Command to run for health check
- `interval`: Time between checks (default: 30s)
- `timeout`: Maximum time for check to complete (default: 30s)
- `retries`: Number of consecutive failures before unhealthy (default: 3)
- `start_period`: Grace period before checks start (useful for slow startup)

---

## Implementation Steps for Docker Desktop

### Step 1: Backend Setup

1. **Wire health router in server.py:**
```python
# Add to imports section
from routers.health import router as health_router

# Add after other router inclusions (around line 180-200)
app.include_router(health_router, prefix="/api")
```

2. **Verify environment variables are set:**
```bash
# In backend/.env
EMERGENT_LLM_KEY=your-key-here
DEFAULT_LLM_PROVIDER=emergent
DEFAULT_LLM_MODEL=claude-3-7-sonnet-20250219
MONGO_URL=mongodb://mongodb:27017/catalyst
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
```

### Step 2: Frontend Setup

1. **Add Status route to App.js/tsx:**
```javascript
// Add import
import Status from './pages/Status';

// Add route in <Routes> or <Switch>
<Route path="/status" element={<Status />} />
```

2. **Add navbar link** (if you have a navbar):
```javascript
<Link to="/status" className="nav-link">
  Status
</Link>
```

### Step 3: Docker Compose Update

1. **Update your docker-compose file** with the healthcheck configurations shown above

2. **Ensure curl is available** in containers:
   - Backend: Should already have curl (Python images usually do)
   - Frontend: Nginx image includes curl
   - Redis: Redis image includes redis-cli
   - Qdrant: Qdrant image includes curl

### Step 4: Build and Test

```bash
# Build images
docker-compose -f docker-compose.artifactory.yml build

# Start services
docker-compose -f docker-compose.artifactory.yml up -d

# Check health status
docker-compose ps
# Should show "healthy" for all services after start_period

# Test backend endpoint
curl http://localhost:8001/api/health | jq

# Test readiness
curl http://localhost:8001/api/health/ready

# Test liveness
curl http://localhost:8001/api/health/live

# Access frontend status page
# Open browser: http://localhost:3000/status
```

---

## Acceptance Criteria Verification

### ✅ Criterion 1: Backend /health endpoint
```bash
curl http://localhost:8001/api/health

# Should return:
# - HTTP 200 with per-dependency statuses
# - JSON with mongodb, redis, qdrant, model status
# - Each dependency shows "healthy", "degraded", or "unhealthy"
```

### ✅ Criterion 2: Frontend /status page
```
Open browser: http://localhost:3000/status

Should show:
- Overall system status (green/amber/red badge)
- 4 cards: MongoDB, Redis, Qdrant, LLM Model
- Each card with traffic-light color (green/amber/red)
- Last refresh time
- Auto-refresh every 10 seconds
- Manual "Refresh Now" button
```

### ✅ Criterion 3: Docker Compose healthchecks
```bash
docker-compose ps

Should show:
NAME                STATUS
catalyst-backend    Up X minutes (healthy)
catalyst-frontend   Up X minutes (healthy)
catalyst-redis      Up X minutes (healthy)
catalyst-qdrant     Up X minutes (healthy)
```

**Test unhealthy scenario:**
```bash
# Stop Redis
docker stop catalyst-redis

# Check compose status
docker-compose ps
# catalyst-redis should show as "stopped" or "unhealthy"

# Check API health
curl http://localhost:8001/api/health
# Should return status: "degraded" with redis showing fallback

# Check frontend
# /status page should show Redis as amber/red with fallback message

# Restart Redis
docker start catalyst-redis

# Wait for healthcheck
sleep 15

# Verify all healthy again
docker-compose ps
```

---

## Monitoring Commands

### Check Health via CLI
```bash
# Overall health
curl -s http://localhost:8001/api/health | jq .status

# Specific dependency
curl -s http://localhost:8001/api/health | jq .dependencies.mongodb

# Pretty print all
curl -s http://localhost:8001/api/health | jq
```

### Watch Health Status
```bash
# Poll every 5 seconds
watch -n 5 'curl -s http://localhost:8001/api/health | jq'

# Or use this one-liner
while true; do 
  curl -s http://localhost:8001/api/health | jq .status
  sleep 5
done
```

### Check Docker Health
```bash
# All services
docker-compose ps

# Specific service
docker inspect catalyst-backend --format='{{.State.Health.Status}}'

# Health check logs
docker inspect catalyst-backend --format='{{range .State.Health.Log}}{{.Output}}{{end}}'
```

---

## Troubleshooting

### Health Check Fails with "curl: command not found"

**Solution:** Add curl to Dockerfile
```dockerfile
# In Dockerfile
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
```

### Frontend Can't Reach Backend Health Endpoint

**Solution:** Check REACT_APP_BACKEND_URL
```bash
# In frontend/.env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Qdrant Healthcheck Fails

**Alternative:** Use collections endpoint
```yaml
qdrant:
  healthcheck:
    test: ["CMD", "curl", "-fsS", "http://localhost:6333/collections"]
```

### Redis Healthcheck Fails with "redis-cli: not found"

**Alternative:** Use telnet
```yaml
redis:
  healthcheck:
    test: ["CMD-SHELL", "timeout 1 bash -c 'cat < /dev/null > /dev/tcp/localhost/6379'"]
```

---

## Files Summary

### Created Files:
1. `/app/backend/routers/health.py` - Health check router (200 lines)
2. `/app/frontend/src/pages/Status.tsx` - Status page component (220 lines)
3. `/app/frontend/src/pages/Status.css` - Status page styles (180 lines)
4. `/app/HEALTH_CHECKS_IMPLEMENTATION.md` - This documentation

### Files to Modify:
1. `/app/backend/server.py` - Add health router (2 lines)
2. `/app/frontend/src/App.js` - Add status route (2 lines)
3. `/app/frontend/src/components/Navbar.js` - Add status link (3 lines)
4. `/app/docker-compose.artifactory.yml` - Add healthchecks (~40 lines)

---

## Production Considerations

### Load Balancer Integration
```yaml
# Use readiness probe for load balancer
GET /api/health/ready
# Remove from pool if 503
```

### Monitoring Integration
```python
# Prometheus metrics endpoint
from prometheus_client import Counter, Gauge

health_check_counter = Counter('health_checks_total', 'Total health checks')
dependency_status = Gauge('dependency_status', 'Dependency status', ['service'])
```

### Alerting
```yaml
# Alert if unhealthy for > 5 minutes
groups:
  - name: health
    rules:
      - alert: ServiceUnhealthy
        expr: health_status == 0
        for: 5m
        annotations:
          summary: "Service {{ $labels.service }} is unhealthy"
```

---

**Status:** ✅ Ready for implementation on Docker Desktop  
**Priority:** 🟢 IMPROVEMENT - Enhances operational visibility  
**Impact:** Better monitoring, faster troubleshooting, clear dependency status
