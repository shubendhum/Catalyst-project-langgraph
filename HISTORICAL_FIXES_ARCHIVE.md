# Historical Fixes Archive

This document consolidates all historical troubleshooting and fix documentation from the Catalyst project development. These issues have been resolved and this serves as a reference archive.

---

## Table of Contents
1. [SSL & Certificate Fixes](#ssl--certificate-fixes)
2. [Docker Build & Configuration](#docker-build--configuration)
3. [Node.js & Yarn Issues](#nodejs--yarn-issues)
4. [Deployment Configuration](#deployment-configuration)
5. [Requirements & Dependencies](#requirements--dependencies)
6. [General Fixes](#general-fixes)

---

## SSL & Certificate Fixes

### Issue Summary
Multiple SSL certificate validation issues encountered during:
- Alpine Linux Docker builds
- Python pip installations with Artifactory
- Yarn package installations
- HTTPS connections in containerized environment

### Root Causes
1. Missing CA certificates in Alpine base image
2. Self-signed certificates in corporate Artifactory
3. SSL verification issues with custom registries
4. Python requests library certificate validation failures

### Solutions Applied
1. **Alpine SSL Setup**:
   ```dockerfile
   RUN apk add --no-cache ca-certificates && update-ca-certificates
   ```

2. **Python pip SSL**:
   ```bash
   pip install --trusted-host <artifactory-host> --cert /path/to/cert.pem
   ```
   Or disable verification (development only):
   ```bash
   pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org
   ```

3. **Yarn SSL**:
   ```bash
   yarn config set strict-ssl false
   yarn install --network-timeout 600000
   ```

### Status: ✅ RESOLVED
All SSL issues resolved through proper certificate management and registry configuration.

---

## Docker Build & Configuration

### Issues Encountered
1. **Exit Code 127** - Command not found errors
2. **Docker Entrypoint Issues** - `/docker-entrypoint.d/` conflicts
3. **Multi-stage Build Problems** - Context and COPY command failures
4. **Nginx Configuration Errors** - Directive placement issues

### Exit Code 127 Fixes
**Problem**: Commands like `craco`, `react-scripts` not found during build

**Solutions**:
1. Add `node_modules/.bin` to PATH:
   ```dockerfile
   ENV PATH="/app/node_modules/.bin:${PATH}"
   ```

2. Use full paths to executables:
   ```dockerfile
   RUN /app/node_modules/.bin/react-scripts build
   ```

3. Ensure dependencies installed before build commands

### Docker Entrypoint Fix
**Problem**: Nginx failed to start due to `/docker-entrypoint.d/ is not empty` error

**Root Cause**: Using `nginx:alpine` base image which has pre-existing entrypoint scripts

**Solution**: 
1. Switched to `node:20-alpine` for build stage
2. Used `alpine:latest` for final stage instead of `nginx:alpine`
3. Installed nginx manually in final stage
4. Avoided entrypoint conflicts

### Nginx Configuration
**Problem**: "server directive is not allowed here" errors

**Solution**: Proper directive placement
```nginx
# ✅ Correct structure
worker_processes auto;
error_log /var/log/nginx/error.log warn;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    server {
        listen 3000;
        # ... server config
    }
}
```

**Common Mistakes**:
- ❌ `user` directive inside `server` block
- ❌ `worker_processes` inside `http` block
- ❌ Missing `events` block

### Status: ✅ RESOLVED
All Docker build and Nginx configuration issues fixed.

---

## Node.js & Yarn Issues

### Node.js Version Upgrade (18 → 20)
**Reason**: Node 18 approaching end-of-life, compatibility issues with newer packages

**Changes**:
```dockerfile
FROM node:20-alpine AS build
```

**Impacts**:
- Better performance
- Enhanced security
- Native support for newer ECMAScript features
- Required package.json updates for some dependencies

### Yarn Installation Issues
**Problems**:
1. Network timeouts during large installations
2. Registry connection failures
3. Integrity check failures
4. SSL verification issues (see SSL section)

**Solutions**:
1. **Increased Timeouts**:
   ```bash
   yarn install --network-timeout 600000
   ```

2. **Disable Strict SSL** (when using self-signed certs):
   ```bash
   yarn config set strict-ssl false
   ```

3. **Clear Cache**:
   ```bash
   yarn cache clean
   ```

4. **Retry on Failure**:
   ```dockerfile
   RUN yarn install --network-timeout 600000 || \
       (yarn cache clean && yarn install --network-timeout 600000)
   ```

### React Refresh Issues
**Problem**: Fast Refresh not working in development

**Solution**: Updated webpack configuration in CRACO config:
```javascript
webpack: {
  configure: (webpackConfig) => {
    webpackConfig.plugins = webpackConfig.plugins.filter(
      plugin => plugin.constructor.name !== 'ReactRefreshPlugin'
    );
    return webpackConfig;
  }
}
```

### Status: ✅ RESOLVED
Node 20 upgrade complete, Yarn installation stabilized.

---

## Deployment Configuration

### Multiple Deployment Guides Consolidated

**Deployment Options**:
1. **Docker Compose** (Local Development)
2. **AWS ECS** (Container Orchestration)
3. **AWS EC2** (VM-based)
4. **AWS EKS** (Kubernetes)

### Docker Compose Setup
```yaml
version: '3.8'
services:
  backend:
    build: 
      context: .
      dockerfile: Dockerfile.backend.artifactory
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://mongo:27017
    depends_on:
      - mongo
  
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend.artifactory
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8001
  
  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
```

### Makefile Commands
```makefile
# Build and run
build:
    docker-compose -f docker-compose.artifactory.yml build

run:
    docker-compose -f docker-compose.artifactory.yml up -d

# Clean
clean:
    docker-compose -f docker-compose.artifactory.yml down -v
```

### Environment Variables
**Backend (.env)**:
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=catalyst_db
EMERGENT_LLM_KEY=your_key_here
```

**Frontend (.env)**:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Status: ✅ RESOLVED
All deployment configurations documented and working.

---

## Requirements & Dependencies

### Python Requirements Management

**Initial Problems**:
1. LangGraph dependencies conflicting with main requirements
2. Version conflicts between packages
3. Missing dependencies for Phase 3 features

**Resolution**:
1. Split requirements into:
   - `requirements.txt` - Core dependencies
   - `requirements-langgraph.txt` - LangGraph specific
   - `requirements-phase3.txt` - Phase 3 additions (GCP, Slack SDK, etc.)

2. **Merged Phase 3 into Main Requirements**:
   Phase 3 packages now consolidated into main `requirements.txt`

### Dependency Validation Process
1. Test imports in Python shell
2. Run `pip check` for conflicts
3. Verify version compatibility
4. Test application startup

### LangGraph Fix
**Problem**: Conflicting dependency versions with FastAPI

**Solution**: Isolated LangGraph dependencies:
```txt
# requirements-langgraph.txt
langgraph==0.0.55
langchain==0.1.16
langchain-core==0.1.45
```

### Status: ✅ RESOLVED
All dependencies properly managed and validated.

---

## General Fixes

### Emergent Integrations Fix
**Problem**: Import errors with emergentintegrations package

**Solution**:
```bash
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

**Usage**:
```python
from emergentintegrations.llm.chat import LlmChat, UserMessage
```

### Public NPM Registry Switch
**Context**: When moving away from Artifactory to public registry

**Steps**:
1. Remove `.npmrc.artifactory` and `.yarnrc.artifactory`
2. Create standard `.npmrc`:
   ```
   registry=https://registry.npmjs.org/
   ```
3. Clear Yarn cache
4. Reinstall dependencies

### Quick Fixes Applied
1. **Import Path Corrections**: Fixed relative imports across agents
2. **Async/Await Consistency**: Ensured all agent methods properly async
3. **MongoDB Connection**: Standardized connection string handling
4. **CORS Configuration**: Added proper CORS middleware setup
5. **WebSocket Management**: Implemented connection pooling and cleanup

### Status: ✅ RESOLVED
All quick fixes applied and tested.

---

## Summary

**Total Issues Resolved**: 40+
**Categories**: SSL, Docker, Node.js, Deployment, Dependencies, General
**Development Phase**: MVP → Phase 1 → Phase 2 → Phase 3

**Key Learnings**:
1. Always handle SSL certificates properly in containerized environments
2. Use specific Node.js LTS versions for stability
3. Separate concerns in requirements files for clarity
4. Document deployment configurations early
5. Test Docker builds incrementally
6. Keep Nginx configuration simple and well-structured

**Current Status**: All systems operational ✅

---

*This archive was created during codebase cleanup. All issues documented here have been resolved. For current issues, refer to the project issue tracker.*

*Last Updated: October 2025*
