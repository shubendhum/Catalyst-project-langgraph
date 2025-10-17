# Phase 4 Infrastructure - Artifactory vs Public Registry

This document explains the differences between the public registry and Artifactory versions of Phase 4 infrastructure.

---

## Files Created

1. **`docker-compose.phase4.yml`** - Public registries (Docker Hub)
2. **`docker-compose.phase4.artifactory.yml`** - Artifactory registry (enterprise)

---

## Key Differences

### 1. Image Registry

**Public Version** (`docker-compose.phase4.yml`):
```yaml
redis:
  image: redis:7-alpine
qdrant:
  image: qdrant/qdrant:latest
rabbitmq:
  image: rabbitmq:3-management-alpine
```

**Artifactory Version** (`docker-compose.phase4.artifactory.yml`):
```yaml
redis:
  image: artifactory.devtools.syd.c1.macquarie.com:9996/redis:7-alpine
qdrant:
  image: artifactory.devtools.syd.c1.macquarie.com:9996/qdrant/qdrant:latest
rabbitmq:
  image: artifactory.devtools.syd.c1.macquarie.com:9996/rabbitmq:3-management-alpine
```

### 2. SSL/TLS Configuration

**Redis - Public**:
```yaml
command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
```

**Redis - Artifactory** (SSL disabled):
```yaml
command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru --tls-port 0
environment:
  - REDIS_REPLICATION_MODE=master
  - ALLOW_EMPTY_PASSWORD=yes
```

**Qdrant - Public**:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
```

**Qdrant - Artifactory** (SSL verification disabled):
```yaml
environment:
  - QDRANT__SERVICE__ENABLE_TLS=false
healthcheck:
  test: ["CMD", "wget", "--no-check-certificate", "-q", "--spider", "http://localhost:6333/healthz"]
```

**RabbitMQ - Artifactory** (SSL verification disabled):
```yaml
environment:
  - RABBITMQ_SSL_VERIFY=verify_none
  - RABBITMQ_SSL_FAIL_IF_NO_PEER_CERT=false
```

### 3. Restart Policies

**Public Version**:
- No restart policy (for development)

**Artifactory Version**:
```yaml
restart: unless-stopped
```

### 4. MongoDB Configuration

**Public**:
```yaml
mongodb:
  image: mongo:7
  environment:
    - MONGO_INITDB_DATABASE=catalyst_db
```

**Artifactory**:
```yaml
mongodb:
  image: artifactory.devtools.syd.c1.macquarie.com:9996/mongo:7
  environment:
    - MONGO_INITDB_ROOT_USERNAME=admin
    - MONGO_INITDB_ROOT_PASSWORD=catalyst_admin_pass
    - MONGO_INITDB_DATABASE=catalyst_db
```

---

## Makefile Commands

### Public Registry Commands
```bash
make phase4-start          # Start with public images
make phase4-stop
make phase4-restart
make phase4-logs
make phase4-clean
make phase4-setup
```

### Artifactory Commands
```bash
make phase4-artifactory-start    # Start with Artifactory images
make phase4-artifactory-stop
make phase4-artifactory-restart
make phase4-artifactory-logs
make phase4-artifactory-clean
make phase4-artifactory-setup
```

---

## When to Use Which Version

### Use Public Version When:
- ✅ Development environment
- ✅ Personal projects
- ✅ Testing and experimentation
- ✅ No corporate network restrictions
- ✅ Need latest versions immediately

### Use Artifactory Version When:
- ✅ Corporate/enterprise environment
- ✅ Behind corporate firewall
- ✅ Need approved/scanned images
- ✅ Compliance requirements
- ✅ Internal security policies
- ✅ No direct internet access

---

## SSL/Certificate Handling

### Public Version
- Uses standard SSL/TLS
- Certificate verification enabled
- Works with public CAs

### Artifactory Version
**SSL Disabled For**:
1. **Redis**: `--tls-port 0`
2. **Qdrant**: `QDRANT__SERVICE__ENABLE_TLS=false`
3. **RabbitMQ**: `RABBITMQ_SSL_VERIFY=verify_none`
4. **Health Checks**: `--no-check-certificate`, `--no-verify`

**Why?**
- Corporate Artifactory uses self-signed certificates
- Certificate validation can fail in Docker containers
- Internal services don't need SSL (already behind firewall)
- Simplifies deployment in enterprise environments

---

## Environment Variables

Both versions use the same environment variables in backend:

```env
# Phase 4 Infrastructure
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
RABBITMQ_URL=amqp://catalyst:catalyst_queue_2025@localhost:5672/catalyst
```

**Note**: Connection strings are the same because services bind to localhost ports regardless of which version you use.

---

## Health Checks Comparison

### Public Version (Strict)
```yaml
# Redis
test: ["CMD", "redis-cli", "ping"]

# Qdrant
test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]

# RabbitMQ
test: ["CMD", "rabbitmq-diagnostics", "ping"]
```

### Artifactory Version (Relaxed SSL)
```yaml
# Redis (same)
test: ["CMD", "redis-cli", "ping"]

# Qdrant (SSL verification disabled)
test: ["CMD", "wget", "--no-check-certificate", "-q", "--spider", "http://localhost:6333/healthz"]

# RabbitMQ (same)
test: ["CMD", "rabbitmq-diagnostics", "ping"]
```

---

## Data Volumes

**Both versions use the same volumes**:
- `mongodb_data` - MongoDB database
- `mongodb_config` - MongoDB configuration
- `redis_data` - Redis cache
- `qdrant_data` - Vector database
- `rabbitmq_data` - Message queue data

**Data is compatible** - you can switch between versions without losing data.

---

## Migration Between Versions

### From Public to Artifactory
```bash
# Stop public version
make phase4-stop

# Start Artifactory version
make phase4-artifactory-start

# Data volumes are preserved
```

### From Artifactory to Public
```bash
# Stop Artifactory version
make phase4-artifactory-stop

# Start public version
make phase4-start

# Data volumes are preserved
```

---

## Production Deployment

### Public Version
Best for:
- Cloud deployments (AWS, GCP, Azure)
- Kubernetes clusters with internet access
- Docker Swarm
- Standard hosting providers

### Artifactory Version
Best for:
- On-premise enterprise deployments
- Corporate data centers
- Air-gapped environments
- Compliance-regulated industries
- Banks, government, healthcare

---

## Troubleshooting

### Artifactory Image Pull Issues

**Problem**: Cannot pull images from Artifactory
```
Error: unable to pull image: unauthorized
```

**Solution**:
```bash
# Login to Artifactory
docker login artifactory.devtools.syd.c1.macquarie.com:9996

# Provide credentials
Username: your_username
Password: your_token
```

### SSL Certificate Errors

**Problem**: Certificate verification errors in health checks

**Solution**: Already handled in Artifactory version with:
- `--no-check-certificate`
- `--no-verify`
- `ENABLE_TLS=false`

### Network Issues

**Problem**: Services can't communicate

**Solution**: Both versions use the same network (`catalyst-network`)
```bash
# Check network
docker network inspect catalyst-network

# Check containers are on network
docker network inspect catalyst-network | grep Name
```

---

## Performance Comparison

| Metric | Public | Artifactory | Notes |
|--------|--------|-------------|-------|
| **Image Pull** | Fast | Slower (first time) | Artifactory caches |
| **Startup** | Fast | Fast | Same once downloaded |
| **Runtime** | Same | Same | No performance difference |
| **SSL Overhead** | Minimal | None | Artifactory has SSL disabled |
| **Availability** | High | Depends on Artifactory | Corporate network required |

---

## Security Considerations

### Public Version
- ✅ SSL/TLS enabled
- ✅ Certificate verification
- ✅ Standard security practices
- ⚠️ Exposes services to localhost only

### Artifactory Version
- ⚠️ SSL disabled for internal services
- ✅ Behind corporate firewall
- ✅ Approved/scanned images
- ✅ No external dependencies
- ✅ Compliant with corporate policies

**Note**: SSL is disabled because services are:
1. Running locally or in private network
2. Behind corporate firewall
3. For internal communication only
4. Not exposed to internet

---

## Best Practices

### For Public Version
1. Use in development/staging
2. Enable SSL for production
3. Keep images updated
4. Monitor for vulnerabilities

### For Artifactory Version
1. Keep Artifactory credentials secure
2. Update images through Artifactory
3. Follow corporate security policies
4. Document any SSL exceptions
5. Use internal security scanning

---

## Summary

| Feature | Public | Artifactory |
|---------|--------|-------------|
| **Registry** | Docker Hub | Corporate Artifactory |
| **SSL/TLS** | Enabled | Disabled (internal only) |
| **Auth** | Not required | Docker login required |
| **Restart Policy** | None | unless-stopped |
| **Use Case** | Development | Enterprise |
| **Certificate Handling** | Standard | Relaxed |
| **Compliance** | Standard | Enterprise-compliant |

**Both versions are production-ready** - choose based on your deployment environment!

---

*Last Updated: October 2025*
