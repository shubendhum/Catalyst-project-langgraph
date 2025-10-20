# Local Docker Development Setup Guide

## For Running Catalyst on Your Local Machine with Docker Desktop

This guide explains how to run the complete Catalyst stack (including Redis, Qdrant, RabbitMQ) on your local machine.

---

## Prerequisites

1. **Docker Desktop** installed and running
2. **Git** for cloning the repository
3. **Make** utility (comes with macOS/Linux, install on Windows)

---

## Quick Start - Complete Stack

### Option 1: Regular Docker Hub (Recommended)

```bash
# Clone repository
git clone <your-repo-url>
cd catalyst

# ONE COMMAND - Setup everything
make setup-complete-stack

# Start all services (MongoDB, Redis, Qdrant, RabbitMQ, Backend, Frontend)
make start-all-services

# Check health
make health-all-services
```

### Option 2: Artifactory Registry (For Organizations)

```bash
# Clone repository
git clone <your-repo-url>
cd catalyst

# ONE COMMAND - Setup with Artifactory
make setup-complete-artifactory

# Start all services from Artifactory
make start-all-artifactory

# Check health
make health-all-artifactory
```

---

## What Gets Started

When you run `make start-all-services` or `make start-all-artifactory`:

### Infrastructure Services
- ✅ **MongoDB** (port 27017) - Main database
- ✅ **Redis** (port 6379) - Caching & cost optimization
- ✅ **Qdrant** (ports 6333, 6334) - Vector database for learning
- ✅ **RabbitMQ** (ports 5672, 15672) - Message queue

### Application Services
- ✅ **Backend API** (port 8001) - FastAPI with all agents
- ✅ **Frontend** (port 3000) - React UI

### All Phase 4 Features Enabled
- Cost optimization with persistent Redis cache
- Learning service with Qdrant vector search
- Analytics and workspace features
- Parallel agent execution

---

## Service URLs (After Starting)

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | - |
| Backend API | http://localhost:8001/api | - |
| API Docs | http://localhost:8001/docs | - |
| MongoDB | mongodb://localhost:27017 | admin / catalyst_admin_pass |
| Redis | redis://localhost:6379 | - |
| Qdrant API | http://localhost:6333 | - |
| RabbitMQ AMQP | amqp://localhost:5672 | catalyst / catalyst_queue_2025 |
| RabbitMQ UI | http://localhost:15672 | catalyst / catalyst_queue_2025 |

---

## Common Commands

### Service Management

```bash
# Start everything
make start-all-services              # Regular
make start-all-artifactory           # Artifactory

# Stop everything
make stop-all-services               # Regular
make stop-all-artifactory            # Artifactory

# Restart
make restart-all-services            # Regular
make restart-all-artifactory         # Artifactory

# Check status
make status-all-services             # Regular
make status-all-artifactory          # Artifactory

# Health check
make health-all-services             # Regular
make health-all-artifactory          # Artifactory
```

### Logs

```bash
# Follow all logs
make logs-all-services               # Regular
make logs-all-artifactory            # Artifactory

# Individual service logs
make phase4-logs-redis
make phase4-logs-qdrant
make phase4-logs-rabbitmq
```

### Testing

```bash
# Test APIs
make test-api

# Test specific services
make phase4-test-redis
make phase4-test-qdrant
make phase4-test-rabbitmq
```

---

## Comparison: Old vs New Commands

### ❌ OLD (Missing Phase 4 Services)
```bash
make setup-artifactory    # Only MongoDB, Backend, Frontend
make start-artifactory    # Missing: Redis, Qdrant, RabbitMQ
```
**Result:** Backend falls back to in-memory cache/storage

### ✅ NEW (Complete Stack)
```bash
make setup-complete-artifactory    # Everything
make start-all-artifactory         # All 6 services running
```
**Result:** Full Phase 4 features with persistent storage

---

## Why This Matters

### Without Phase 4 Services (Old Setup)
- ❌ Cache resets on restart
- ❌ Learning data not persisted
- ❌ No vector similarity search
- ⚠️ In-memory fallbacks used

### With Phase 4 Services (New Setup)
- ✅ Persistent cache across restarts
- ✅ Learning patterns stored in Qdrant
- ✅ Fast vector similarity search
- ✅ Better cost optimization
- ✅ Production-like environment

---

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker ps

# Check for port conflicts
lsof -i :8001  # Backend
lsof -i :3000  # Frontend
lsof -i :6379  # Redis
lsof -i :6333  # Qdrant
```

### Health Check Failures

```bash
# Check individual services
make health-all-services

# View logs for failing service
docker logs catalyst-redis
docker logs catalyst-qdrant
docker logs catalyst-rabbitmq
```

### Clean Start

```bash
# Stop and remove everything
make clean-all-artifactory    # or
make stop-all-services && docker compose -f docker-compose.full.yml down -v

# Start fresh
make setup-complete-artifactory
make start-all-artifactory
```

---

## File Reference

### Docker Compose Files

| File | Purpose | Services Included |
|------|---------|-------------------|
| `docker-compose.yml` | Basic stack | MongoDB, Backend, Frontend |
| `docker-compose.artifactory.yml` | Basic Artifactory | MongoDB, Backend, Frontend |
| `docker-compose.phase4.yml` | Phase 4 only | MongoDB, Redis, Qdrant, RabbitMQ |
| `docker-compose.phase4.artifactory.yml` | Phase 4 Artifactory | MongoDB, Redis, Qdrant, RabbitMQ |
| **`docker-compose.full.yml`** ✅ NEW | **Complete stack** | **All 6 services** |
| **`docker-compose.artifactory.full.yml`** ✅ NEW | **Complete Artifactory** | **All 6 services** |

### Recommended for Local Development

Use `docker-compose.full.yml` or `docker-compose.artifactory.full.yml` to get everything running.

---

## Environment Variables (Local Docker)

The backend in Docker will connect to services using container networking:

```bash
MONGO_URL=mongodb://admin:catalyst_admin_pass@mongodb:27017
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
RABBITMQ_URL=amqp://catalyst:catalyst_queue_2025@rabbitmq:5672/catalyst
```

These are automatically configured in the docker-compose files.

---

## Summary

**For local Docker Desktop development with ALL Phase 4 features:**

```bash
# Setup once
make setup-complete-artifactory    # or make setup-complete-stack

# Start everything
make start-all-artifactory         # or make start-all-services

# Verify
make health-all-artifactory        # or make health-all-services

# Access
open http://localhost:3000         # Frontend
open http://localhost:15672        # RabbitMQ UI
```

**All 6 services will be running with persistent storage and full Phase 4 capabilities!**
