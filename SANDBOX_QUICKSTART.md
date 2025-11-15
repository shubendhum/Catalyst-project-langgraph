# Sandbox Execution - Quick Start Guide

## What is Sandboxed Execution?

The Catalyst platform now runs generated code and tests in **isolated Docker containers** instead of on the host machine. This provides:

✅ **Safety** - Untrusted code can't affect your system  
✅ **Isolation** - Each execution gets a clean environment  
✅ **Resource Control** - Memory and CPU limits prevent runaway processes  
✅ **Automatic Cleanup** - Containers are removed after execution  

## Quick Setup (5 minutes)

### 1. Build the Sandbox Image

```bash
# Build the sandbox-runner image (one-time setup)
docker-compose -f docker-compose.artifactory.yml build sandbox-runner
```

This creates an image with Python, Node.js, Git, pytest, Jest, and other tools.

### 2. Start Services

```bash
# Start all services (if not already running)
docker-compose -f docker-compose.artifactory.yml up -d
```

### 3. Verify Installation

```bash
# Check sandbox service status
curl http://localhost:8001/api/sandbox/status | jq

# Expected output:
# {
#   "success": true,
#   "status": "healthy",
#   "docker_connected": true,
#   "image_status": "ready"
# }
```

## Quick Test

### Run a Simple Python Script

```bash
curl -X POST http://localhost:8001/api/sandbox/run \
  -H "Content-Type: application/json" \
  -d '{
    "command": "python hello.py",
    "files": {
      "hello.py": "print(\"Hello from sandbox!\")"
    }
  }' | jq
```

**Expected output:**
```json
{
  "success": true,
  "stdout": "Hello from sandbox!\n",
  "stderr": "",
  "exit_code": 0,
  "duration": 2.1,
  "container_id": "a3f2b1c4"
}
```

### Run Python Tests

```bash
curl -X POST http://localhost:8001/api/sandbox/test/python \
  -H "Content-Type: application/json" \
  -d '{
    "test_files": {
      "test_math.py": "def test_add():\\n    assert 1+1 == 2"
    }
  }' | jq
```

## Automated Test Suite

Run the comprehensive test suite:

```bash
# Install aiohttp if needed
pip install aiohttp

# Run all tests
python /app/test_sandbox.py
```

**Tests included:**
1. ✅ Sandbox service status
2. ✅ Simple command execution
3. ✅ Python script execution
4. ✅ Python tests with pytest
5. ✅ Code linting with flake8
6. ✅ Timeout protection
7. ✅ Python requirements installation

## How Agents Use It

When you create a task in Catalyst:

1. **Coder Agent** generates code
2. **Tester Agent** receives code via event
3. **Tester calls Sandbox Service** to run tests
4. **Sandbox creates ephemeral container**
5. **Tests run in isolation**
6. **Results captured and returned**
7. **Container automatically cleaned up**

All of this happens automatically - no manual intervention needed!

## Configuration

Default settings (in `/app/backend/services/sandbox.py`):

```python
memory_limit = "512m"        # 512MB RAM per container
cpu_quota = 50000            # 0.5 CPU cores (50%)
default_timeout = 300        # 5 minutes max execution time
network_mode = "catalyst-network"  # Network access enabled
```

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/sandbox/run` | Run any command |
| `POST /api/sandbox/test/python` | Run pytest tests |
| `POST /api/sandbox/test/javascript` | Run Jest tests |
| `POST /api/sandbox/lint` | Run code linters |
| `GET /api/sandbox/status` | Check service health |

Full API docs: http://localhost:8001/docs

## Troubleshooting

### Image not found error?

```bash
# Rebuild the image
docker-compose build sandbox-runner

# Verify it exists
docker images | grep sandbox-runner
```

### Container creation fails?

```bash
# Check Docker is accessible
docker ps

# Check backend has Docker socket mounted
docker inspect catalyst-backend | grep docker.sock
```

### Tests timeout?

```bash
# Increase timeout in request
curl -X POST http://localhost:8001/api/sandbox/run \
  -d '{"command": "...", "timeout": 600}'  # 10 minutes
```

### Out of memory?

```bash
# Check container logs
docker logs catalyst-backend | grep -i memory

# Increase limit in sandbox.py
memory_limit = "1g"  # 1GB instead of 512MB
```

## Monitoring

### View sandbox execution logs:

```bash
# Real-time monitoring
docker logs -f catalyst-backend | grep -i sandbox
```

### Check for orphaned containers:

```bash
# Should be empty when idle
docker ps --filter "ancestor=catalyst-sandbox-runner:latest"
```

### API health check:

```bash
curl http://localhost:8001/api/sandbox/status | jq '.status'
```

## Next Steps

1. ✅ **Production Use**: Sandbox is ready for agent workflows
2. 📖 **Full Guide**: See `/app/SANDBOXED_EXECUTION_GUIDE.md` for details
3. 🔧 **Customize**: Modify `Dockerfile.sandbox` to add tools
4. 📊 **Monitor**: Check logs and metrics regularly
5. 🚀 **Scale**: Add more resources as needed

## Resources

- **Full Documentation**: `/app/SANDBOXED_EXECUTION_GUIDE.md`
- **Test Suite**: `/app/test_sandbox.py`
- **Sandbox Service**: `/app/backend/services/sandbox.py`
- **Tester Agent**: `/app/backend/agents_v2/tester_agent_v2.py`
- **API Docs**: http://localhost:8001/docs

## Support

Issues? Check:
1. ✅ Backend running: `docker ps | grep backend`
2. ✅ Image built: `docker images | grep sandbox`
3. ✅ Status endpoint: `curl localhost:8001/api/sandbox/status`
4. ✅ Backend logs: `docker logs catalyst-backend`

---

**That's it! Your sandbox is ready for isolated code execution.** 🎉
