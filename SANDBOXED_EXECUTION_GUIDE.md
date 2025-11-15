# Sandboxed Code Execution Guide

## Overview

The Catalyst platform now includes a sandboxed code execution system that allows safe, isolated execution of generated code and tests in ephemeral Docker containers. This prevents untrusted code from affecting the host system.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Catalyst Backend                         │
│                                                             │
│  ┌──────────────┐      ┌─────────────────────────────┐    │
│  │ Tester Agent │─────>│   Sandbox Service           │    │
│  │              │      │   (sandbox.py)              │    │
│  └──────────────┘      └─────────────────────────────┘    │
│                                    │                        │
│  ┌──────────────┐                  │                        │
│  │ Coder Agent  │                  │                        │
│  │   (future)   │                  │                        │
│  └──────────────┘                  │                        │
│                                    │                        │
│  ┌─────────────────────────────────┼────────────────────┐  │
│  │         API Endpoints            │                    │  │
│  │  - POST /api/sandbox/run         │                    │  │
│  │  - POST /api/sandbox/test/python │                    │  │
│  │  - POST /api/sandbox/test/javascript                 │  │
│  │  - POST /api/sandbox/lint        │                    │  │
│  │  - GET  /api/sandbox/status      │                    │  │
│  └──────────────────────────────────┼────────────────────┘  │
└───────────────────────────────────┼─────────────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │    Docker Engine                │
                    │                                 │
                    │  ┌─────────────────────────┐   │
                    │  │ Sandbox Runner Image    │   │
                    │  │ - Python 3.11           │   │
                    │  │ - Git, Node.js, npm     │   │
                    │  │ - pytest, Jest          │   │
                    │  │ - flake8, ESLint        │   │
                    │  │ - Build tools           │   │
                    │  └─────────────────────────┘   │
                    │                                 │
                    │  Ephemeral Containers:          │
                    │  ┌─────────┐ ┌─────────┐       │
                    │  │Container│ │Container│       │
                    │  │  (runs) │ │(cleanup)│       │
                    │  └─────────┘ └─────────┘       │
                    └─────────────────────────────────┘
```

## Components

### 1. Dockerfile.sandbox

**Location:** `/app/Dockerfile.sandbox`

Pre-built Docker image with all necessary tools:
- Python 3.11 + testing tools (pytest, flake8, mypy, pylint, bandit)
- Node.js + npm + testing tools (jest, eslint, prettier)
- Git and build-essential
- Clean, isolated environment

### 2. Sandbox Service

**Location:** `/app/backend/services/sandbox.py`

Core service managing sandboxed execution:

**Features:**
- Ephemeral container creation and cleanup
- Temporary workspace mounting
- Resource limits (512MB RAM, 0.5 CPU)
- Timeout protection (300s default)
- Output capture (stdout, stderr, exit_code)
- Network access (for package installation)
- Automatic cleanup on completion/error

**Main Class:**
```python
class SandboxService:
    async def run_command(command, files, timeout, env_vars, requirements)
    async def run_python_tests(test_files, source_files, requirements)
    async def run_javascript_tests(test_files, source_files, package_json)
    async def run_linter(files, linter, linter_args)
    def get_status()
```

### 3. API Endpoints

**Base URL:** `http://localhost:8001/api`

#### POST /api/sandbox/run
Execute arbitrary command in sandbox.

**Request:**
```json
{
    "command": "python script.py",
    "files": {
        "script.py": "print('Hello from sandbox!')"
    },
    "timeout": 60,
    "env_vars": {
        "DEBUG": "1"
    },
    "requirements": ["requests", "numpy"]
}
```

**Response:**
```json
{
    "success": true,
    "stdout": "Hello from sandbox!\n",
    "stderr": "",
    "exit_code": 0,
    "duration": 2.5,
    "container_id": "a3f2b1c4",
    "timestamp": "2025-01-09T10:30:00"
}
```

#### POST /api/sandbox/test/python
Run Python tests with pytest.

**Request:**
```json
{
    "test_files": {
        "test_math.py": "def test_add():\n    assert 1+1 == 2"
    },
    "source_files": {
        "math_utils.py": "def add(a, b):\n    return a + b"
    },
    "requirements": ["pytest", "pytest-cov"],
    "pytest_args": "-v --cov=."
}
```

#### POST /api/sandbox/test/javascript
Run JavaScript tests with npm/Jest.

**Request:**
```json
{
    "test_files": {
        "math.test.js": "test('adds', () => { expect(1+2).toBe(3); });"
    },
    "package_json": "{\"scripts\": {\"test\": \"jest\"}}"
}
```

#### POST /api/sandbox/lint
Run code linters.

**Request:**
```json
{
    "files": {
        "example.py": "def hello():\n    print('world')"
    },
    "linter": "flake8",
    "linter_args": "--max-line-length=120"
}
```

#### GET /api/sandbox/status
Check sandbox service health.

**Response:**
```json
{
    "success": true,
    "status": "healthy",
    "docker_connected": true,
    "image_name": "catalyst-sandbox-runner:latest",
    "image_status": "ready",
    "image_size_mb": 450.23,
    "default_timeout": 300,
    "memory_limit": "512m",
    "cpu_quota": 50000,
    "network_mode": "catalyst-network"
}
```

### 4. Agent Integration

#### Tester Agent

**Location:** `/app/backend/agents_v2/tester_agent_v2.py`

The Tester agent now uses the sandbox service for all test execution:

**Flow:**
1. Agent receives `code.pr.opened` event
2. Loads files from repository path
3. Filters test files and source files
4. Calls sandbox service to run tests
5. Parses pytest/Jest output
6. Reports results back

**Key Methods:**
- `_run_tests_in_docker()` - Main entry point for Docker Desktop mode
- `_run_backend_tests_sandbox()` - Run Python tests via sandbox
- `_run_frontend_tests_sandbox()` - Run JavaScript tests via sandbox
- `_parse_pytest_output()` - Parse pytest results
- `_parse_jest_output()` - Parse Jest results

## Setup & Configuration

### Build the Sandbox Image

```bash
# Build the sandbox-runner image
docker-compose -f docker-compose.artifactory.yml build sandbox-runner

# Verify image exists
docker images | grep catalyst-sandbox-runner
```

### Start Services

```bash
# Start all services including sandbox
docker-compose -f docker-compose.artifactory.yml up -d

# Check sandbox service status via API
curl http://localhost:8001/api/sandbox/status
```

### Configuration

**Resource Limits** (in `sandbox.py`):
```python
SandboxService(
    memory_limit="512m",     # RAM limit
    cpu_quota=50000,         # 0.5 CPU cores
    default_timeout=300,     # 5 minutes
    network_mode="catalyst-network"
)
```

**Environment Variables:**
- None required - uses Docker socket from host
- Backend must have `/var/run/docker.sock` mounted (already configured)

## Usage Examples

### 1. Direct API Call - Run Python Script

```bash
curl -X POST http://localhost:8001/api/sandbox/run \
  -H "Content-Type: application/json" \
  -d '{
    "command": "python hello.py",
    "files": {
      "hello.py": "print(\"Hello, World!\")"
    }
  }'
```

### 2. Run Python Tests

```bash
curl -X POST http://localhost:8001/api/sandbox/test/python \
  -H "Content-Type: application/json" \
  -d '{
    "test_files": {
      "test_calc.py": "def test_add():\n    assert 2+2 == 4"
    },
    "requirements": ["pytest"]
  }'
```

### 3. Lint Python Code

```bash
curl -X POST http://localhost:8001/api/sandbox/lint \
  -H "Content-Type: application/json" \
  -d '{
    "files": {
      "example.py": "def hello( ):\n    print( \"world\" )"
    },
    "linter": "flake8"
  }'
```

### 4. Run with Custom Requirements

```bash
curl -X POST http://localhost:8001/api/sandbox/run \
  -H "Content-Type: application/json" \
  -d '{
    "command": "python -c \"import requests; print(requests.__version__)\"",
    "requirements": ["requests"]
  }'
```

### 5. Agent Workflow (Automatic)

When a task is executed:
```
User creates task
    ↓
Planner → Architect → Coder generates code
    ↓
code.pr.opened event published
    ↓
Tester Agent receives event
    ↓
Tester loads code files
    ↓
Tester calls sandbox.run_python_tests()
    ↓
Sandbox creates container, runs pytest, captures output
    ↓
Tester parses results
    ↓
test.results event published
```

## Security & Isolation

### What's Isolated
- ✅ Filesystem (temporary workspace per execution)
- ✅ Process space (separate container)
- ✅ Resource limits (CPU, Memory)
- ✅ Execution timeout (prevents infinite loops)

### What's NOT Isolated
- ⚠️ Network access (enabled for package installation)
- ⚠️ Docker socket (backend has access to host Docker)

### Best Practices
1. Always set reasonable timeouts
2. Validate input before execution
3. Monitor resource usage
4. Review sandbox logs regularly
5. Keep sandbox image updated

## Troubleshooting

### Issue: "Image not found" error

**Solution:**
```bash
# Build the image
docker-compose build sandbox-runner

# Or pull from registry if available
docker pull catalyst-sandbox-runner:latest
```

### Issue: Container startup fails

**Check Docker socket:**
```bash
# Verify Docker is accessible
docker ps

# Check backend container has socket mounted
docker inspect catalyst-backend | grep docker.sock
```

### Issue: Tests timeout

**Increase timeout:**
```python
# In API call
{
    "command": "pytest",
    "timeout": 600  # 10 minutes
}
```

**Or update default:**
```python
# In sandbox.py
SandboxService(default_timeout=600)
```

### Issue: Out of memory

**Check container logs:**
```bash
docker logs catalyst-backend | grep -i memory
```

**Increase memory limit:**
```python
# In sandbox.py
SandboxService(memory_limit="1g")
```

### Issue: Package installation fails

**Check network access:**
```bash
# Test from within sandbox
docker run --rm catalyst-sandbox-runner:latest \
  pip install requests
```

## Monitoring & Logs

### Backend Logs
```bash
# View sandbox execution logs
docker logs catalyst-backend | grep -i sandbox

# Real-time monitoring
docker logs -f catalyst-backend | grep -i sandbox
```

### Container Lifecycle
```bash
# List running sandbox containers (should be 0 when idle)
docker ps --filter "ancestor=catalyst-sandbox-runner:latest"

# Check for orphaned containers
docker ps -a --filter "ancestor=catalyst-sandbox-runner:latest"
```

### API Health Check
```bash
# Check status endpoint
curl http://localhost:8001/api/sandbox/status | jq

# Expected response
{
  "success": true,
  "status": "healthy",
  "docker_connected": true,
  "image_status": "ready"
}
```

## Performance Considerations

### Container Creation Overhead
- Average: 1-3 seconds per execution
- Includes: container creation, workspace mounting, command execution
- Cleanup: automatic, ~0.5 seconds

### Resource Usage
- Memory: 512MB per container (configurable)
- CPU: 0.5 cores per container (configurable)
- Disk: Temporary workspace (~10-100MB)
- Network: Bandwidth for package downloads

### Optimization Tips
1. **Pre-install dependencies** in Dockerfile.sandbox for faster execution
2. **Batch operations** when possible (multiple tests in one call)
3. **Cache requirements** by including common packages in base image
4. **Monitor cleanup** to prevent container accumulation

## Future Enhancements

### Planned Features
- [ ] Network isolation mode (disable network for untrusted code)
- [ ] Persistent cache for installed packages
- [ ] GPU support for ML workloads
- [ ] Multi-language support (Go, Rust, Java)
- [ ] Custom Docker images per project
- [ ] Execution queue for high concurrency
- [ ] Detailed resource metrics and billing

### Integration Opportunities
- Coder agent validation (syntax check before commit)
- Security scanning (bandit, safety)
- Performance profiling (cProfile, memory_profiler)
- Code coverage reporting
- Benchmark execution

## API Reference

Full API documentation available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

Look for "Sandbox Execution Endpoints" section.

## Support

For issues or questions:
1. Check this guide first
2. Review backend logs: `docker logs catalyst-backend`
3. Verify Docker connectivity: `docker ps`
4. Check API status: `curl http://localhost:8001/api/sandbox/status`

## Version History

- **v1.0.0** (2025-01-09): Initial implementation
  - Basic sandbox execution
  - Python and JavaScript test support
  - Linter integration
  - Tester agent integration
  - API endpoints
