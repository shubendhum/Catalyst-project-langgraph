# Phase 4 Infrastructure Setup Guide

This guide explains how to start the Phase 4 infrastructure services (Redis, Qdrant, RabbitMQ) for the Catalyst platform.

---

## Quick Start

### Option 1: Using Makefile (Recommended)

```bash
# Complete setup (install dependencies + start services)
make phase4-setup

# Or step by step:
make phase4-install-deps  # Install Python dependencies
make phase4-start         # Start infrastructure services
make phase4-health        # Check health of all services
```

### Option 2: Using Docker Compose Directly

```bash
# Start services
docker compose -f docker-compose.phase4.yml up -d

# Check status
docker compose -f docker-compose.phase4.yml ps

# View logs
docker compose -f docker-compose.phase4.yml logs -f

# Stop services
docker compose -f docker-compose.phase4.yml stop
```

---

## Services Started

### 1. **MongoDB** (Existing)
- **Port**: 27017
- **URL**: `mongodb://localhost:27017`
- **Purpose**: Main database for projects, users, conversations

### 2. **Redis** (New - Phase 4)
- **Port**: 6379
- **URL**: `redis://localhost:6379`
- **Purpose**: Caching layer for cost optimization
- **Features**:
  - LLM response caching
  - Token usage tracking
  - Budget management data

### 3. **Qdrant** (New - Phase 4)
- **Port**: 6333 (HTTP), 6334 (gRPC)
- **URL**: `http://localhost:6333`
- **Purpose**: Vector database for learning service
- **Features**:
  - Pattern storage with embeddings
  - Similarity search for similar projects
  - Success prediction based on history

### 4. **RabbitMQ** (New - Phase 4)
- **Port**: 5672 (AMQP), 15672 (Management UI)
- **URL**: `amqp://catalyst:catalyst_queue_2025@localhost:5672/catalyst`
- **Management UI**: http://localhost:15672
- **Credentials**: 
  - Username: `catalyst`
  - Password: `catalyst_queue_2025`
- **Purpose**: Message queue for async tasks
- **Features**:
  - Background task processing
  - Async learning updates
  - Scheduled analytics aggregation

---

## Makefile Commands

### Starting Services
```bash
make phase4-start          # Start all Phase 4 services
make phase4-stop           # Stop all services
make phase4-restart        # Restart all services
make phase4-status         # Check service status
```

### Health & Testing
```bash
make phase4-health         # Check health of all services
make phase4-test-redis     # Test Redis connection
make phase4-test-qdrant    # Test Qdrant connection
make phase4-test-rabbitmq  # Test RabbitMQ connection
```

### Logs
```bash
make phase4-logs           # View all logs
make phase4-logs-redis     # View Redis logs only
make phase4-logs-qdrant    # View Qdrant logs only
make phase4-logs-rabbitmq  # View RabbitMQ logs only
```

### Management
```bash
make phase4-ui-rabbitmq    # Open RabbitMQ Management UI
make phase4-info           # Show infrastructure information
make phase4-clean          # Stop and remove all (DESTRUCTIVE)
```

---

## Environment Variables

The following variables are automatically set in `/app/backend/.env`:

```env
# Phase 4 Infrastructure
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
RABBITMQ_URL=amqp://catalyst:catalyst_queue_2025@localhost:5672/catalyst

# Phase 4 Features
ENABLE_COST_OPTIMIZER=true
ENABLE_LEARNING_SERVICE=true
ENABLE_CONTEXT_MANAGER=true
ENABLE_WORKSPACES=true
ENABLE_ANALYTICS=true
```

---

## Integration with Backend

The Phase 4 services are automatically used by the backend when available:

### Cost Optimizer
- **With Redis**: Persistent cache across restarts, faster lookups
- **Without Redis**: In-memory cache (TTL: 1 hour)

```python
# Automatic failover
if redis_available:
    cache_response_in_redis(...)
else:
    cache_response_in_memory(...)
```

### Learning Service
- **With Qdrant**: Production-quality vector search, scalable
- **Without Qdrant**: In-memory numpy-based similarity search

```python
# Automatic failover
if qdrant_available:
    search_in_qdrant(...)
else:
    search_in_memory(...)
```

### Features
- **Sentence Transformers**: Better embeddings (384-dim)
- **Fallback**: Simple hash-based embeddings (128-dim)

---

## After Starting Services

### 1. Restart Backend
```bash
sudo supervisorctl restart backend

# Or if running locally
cd backend && uvicorn server:app --reload
```

### 2. Check Backend Logs
```bash
tail -f /var/log/supervisor/backend.err.log
```

Look for these messages:
```
✅ Connected to Redis at redis://localhost:6379
✅ Connected to Qdrant at http://localhost:6333
✅ Loaded sentence-transformers embedding model
```

### 3. Verify Integration
```bash
# Check cache stats (should show redis_connected: true)
curl http://localhost:8001/api/optimizer/cache-stats | python3 -m json.tool

# Check learning stats
curl http://localhost:8001/api/learning/stats | python3 -m json.tool
```

---

## Troubleshooting

### Services Not Starting

**Check Docker**:
```bash
docker ps
docker logs catalyst-redis
docker logs catalyst-qdrant
docker logs catalyst-rabbitmq
```

**Check Ports**:
```bash
# Make sure ports are not in use
lsof -i :6379  # Redis
lsof -i :6333  # Qdrant
lsof -i :5672  # RabbitMQ
```

### Redis Connection Failed

```bash
# Test Redis manually
docker exec catalyst-redis redis-cli ping
# Should return: PONG

# Check logs
docker logs catalyst-redis
```

### Qdrant Not Responding

```bash
# Test Qdrant health
curl http://localhost:6333/healthz

# Check logs
docker logs catalyst-qdrant

# Check collections
curl http://localhost:6333/collections
```

### RabbitMQ Issues

```bash
# Test RabbitMQ
docker exec catalyst-rabbitmq rabbitmq-diagnostics ping

# Check logs
docker logs catalyst-rabbitmq

# Open management UI
open http://localhost:15672
```

### Backend Not Connecting

**Check .env file**:
```bash
cat backend/.env | grep -E "REDIS|QDRANT|RABBITMQ"
```

**Check backend logs**:
```bash
tail -n 50 /var/log/supervisor/backend.err.log | grep -E "Redis|Qdrant|RabbitMQ"
```

---

## Data Persistence

All Phase 4 services use Docker volumes for data persistence:

```bash
# List volumes
docker volume ls | grep catalyst

# Volumes created:
# - redis_data       (Redis cache and data)
# - qdrant_data      (Vector database)
# - rabbitmq_data    (Queue data)
```

### Backing Up Data

```bash
# Backup Redis
docker exec catalyst-redis redis-cli BGSAVE

# Backup Qdrant
docker exec catalyst-qdrant sh -c 'tar czf /tmp/qdrant-backup.tar.gz /qdrant/storage'
docker cp catalyst-qdrant:/tmp/qdrant-backup.tar.gz ./qdrant-backup.tar.gz
```

---

## Performance Tuning

### Redis Configuration

Current settings in docker-compose.phase4.yml:
```yaml
command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
```

**For production**:
- Increase maxmemory (e.g., 2gb)
- Consider Redis Cluster for scalability
- Enable persistence with AOF + RDB

### Qdrant Configuration

**For production**:
- Increase `QDRANT__SERVICE__MAX_SEARCH_THREADS`
- Use quantization for larger datasets
- Enable HNSW index optimization

### RabbitMQ Configuration

**For high throughput**:
- Increase prefetch count
- Use quorum queues for reliability
- Configure ha-mode for high availability

---

## Upgrading from MVP

The system automatically uses Phase 4 infrastructure when available:

**MVP (In-Memory)**:
- ✅ Works without external services
- ❌ Data lost on restart
- ❌ Limited scalability

**Phase 4 (Infrastructure)**:
- ✅ Persistent data
- ✅ Scalable to production
- ✅ Better performance
- ✅ Production-ready

**Migration is seamless** - just start the services and restart backend!

---

## Production Deployment

### Docker Swarm
```bash
docker stack deploy -c docker-compose.phase4.yml catalyst-phase4
```

### Kubernetes
```bash
kubectl apply -f k8s/phase4/
```

### Cloud Services

**Managed alternatives**:
- **Redis**: AWS ElastiCache, Redis Cloud
- **Qdrant**: Qdrant Cloud, self-hosted on EC2/K8s
- **RabbitMQ**: AWS MQ, CloudAMQP

---

## Monitoring

### Health Checks

All services have built-in health checks:

```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 5s
  timeout: 3s
  retries: 5
```

### Metrics

**Redis Metrics**:
```bash
docker exec catalyst-redis redis-cli INFO stats
```

**Qdrant Metrics**:
```bash
curl http://localhost:6333/metrics
```

**RabbitMQ Metrics**:
- Management UI: http://localhost:15672
- Prometheus endpoint: http://localhost:15672/api/metrics

---

## Next Steps

1. **Start services**: `make phase4-start`
2. **Restart backend**: `sudo supervisorctl restart backend`
3. **Verify integration**: Check cache stats and learning stats
4. **Test features**: Use Phase 4 API endpoints
5. **Monitor performance**: Watch logs and metrics

---

## Support

For issues or questions:
1. Check logs: `make phase4-logs`
2. Verify health: `make phase4-health`
3. Review this guide
4. Check backend logs for connection status

---

**Phase 4 infrastructure is now production-ready with persistent storage and scalability!** 🚀
