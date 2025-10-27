# Docker Desktop Proxy Configuration for Organization Laptop

## Problem
Running Docker on organization laptop with:
- Corporate proxy
- SSL inspection (MITM proxy)
- Self-signed certificates
- HuggingFace downloads failing with SSL errors

## Solution: Configure Docker Desktop for Corporate Proxy

### Step 1: Configure Docker Desktop Proxy Settings

**On Mac:**
1. Open Docker Desktop
2. Go to **Settings** (gear icon)
3. Click **Resources** → **Proxies**
4. Enable **Manual proxy configuration**
5. Set:
   ```
   Web Server (HTTP): http://your-proxy:port
   Secure Web Server (HTTPS): http://your-proxy:port
   Bypass: localhost,127.0.0.1,.local
   ```

**On Windows:**
1. Open Docker Desktop
2. Go to **Settings**
3. Click **Resources** → **Proxies**
4. Enable **Manual proxy configuration**
5. Configure same as above

**To find your proxy settings:**
```bash
# On Mac
echo $HTTP_PROXY
echo $HTTPS_PROXY

# On Windows (PowerShell)
$env:HTTP_PROXY
$env:HTTPS_PROXY

# Or check system settings
# Mac: System Preferences → Network → Advanced → Proxies
# Windows: Settings → Network & Internet → Proxy
```

### Step 2: Update docker-compose.artifactory.yml

Add proxy environment variables to ALL services:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.backend.artifactory
      args:
        HTTP_PROXY: ${HTTP_PROXY}
        HTTPS_PROXY: ${HTTPS_PROXY}
        NO_PROXY: ${NO_PROXY}
    environment:
      HTTP_PROXY: ${HTTP_PROXY}
      HTTPS_PROXY: ${HTTPS_PROXY}
      NO_PROXY: localhost,127.0.0.1,mongodb,redis,qdrant,rabbitmq
      CURL_CA_BUNDLE: ""
      REQUESTS_CA_BUNDLE: ""
      SSL_CERT_FILE: ""
      PYTHONHTTPSVERIFY: "0"
    # ... rest of config

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend.artifactory
      args:
        HTTP_PROXY: ${HTTP_PROXY}
        HTTPS_PROXY: ${HTTPS_PROXY}
        NO_PROXY: ${NO_PROXY}
    environment:
      HTTP_PROXY: ${HTTP_PROXY}
      HTTPS_PROXY: ${HTTPS_PROXY}
      NO_PROXY: localhost,127.0.0.1,backend
    # ... rest of config
```

### Step 3: Create .env file in project root

Create `/app/.env` (if it doesn't exist):

```bash
# Proxy Configuration
# Replace with your organization's proxy
HTTP_PROXY=http://proxy.yourcompany.com:8080
HTTPS_PROXY=http://proxy.yourcompany.com:8080
NO_PROXY=localhost,127.0.0.1,.local,mongodb,redis,qdrant

# SSL Configuration (disable for corporate proxy)
CURL_CA_BUNDLE=""
REQUESTS_CA_BUNDLE=""
SSL_CERT_FILE=""
PYTHONHTTPSVERIFY=0
```

### Step 4: Alternative - Use Host Network Proxy

If you can't find proxy settings, Docker can inherit from host:

**Mac/Linux:**
```bash
# In your shell profile (~/.zshrc or ~/.bashrc)
export HTTP_PROXY=http://proxy.yourcompany.com:8080
export HTTPS_PROXY=http://proxy.yourcompany.com:8080
export NO_PROXY=localhost,127.0.0.1
```

**Windows (PowerShell profile):**
```powershell
$env:HTTP_PROXY="http://proxy.yourcompany.com:8080"
$env:HTTPS_PROXY="http://proxy.yourcompany.com:8080"
$env:NO_PROXY="localhost,127.0.0.1"
```

### Step 5: Configure Docker Daemon (Alternative Method)

**Mac:** Create/edit `~/.docker/daemon.json`:
```json
{
  "proxies": {
    "default": {
      "httpProxy": "http://proxy.yourcompany.com:8080",
      "httpsProxy": "http://proxy.yourcompany.com:8080",
      "noProxy": "localhost,127.0.0.1,*.local"
    }
  }
}
```

**Windows:** Create/edit `C:\Users\YourUsername\.docker\daemon.json`

After editing, restart Docker Desktop.

### Step 6: Build with Proxy

```bash
# Set proxy in current shell
export HTTP_PROXY=http://proxy.yourcompany.com:8080
export HTTPS_PROXY=http://proxy.yourcompany.com:8080
export NO_PROXY=localhost,127.0.0.1

# Build with proxy
docker-compose -f docker-compose.artifactory.yml build
```

### Step 7: Test Connectivity

**Test from container:**
```bash
# Start backend container
docker-compose -f docker-compose.artifactory.yml up -d backend

# Test internet connectivity
docker exec catalyst-backend curl -I https://huggingface.co

# Test with SSL disabled
docker exec catalyst-backend curl -k -I https://huggingface.co

# Check environment variables
docker exec catalyst-backend env | grep PROXY
```

## Common Issues & Solutions

### Issue 1: "Connection refused" or "Cannot connect"
**Solution:** Proxy not configured
- Check Docker Desktop proxy settings
- Verify proxy URL is correct
- Test proxy from host: `curl -x http://proxy:port https://google.com`

### Issue 2: SSL certificate errors persist
**Solution:** SSL verification still enabled
- Add to docker-compose:
  ```yaml
  environment:
    CURL_CA_BUNDLE: ""
    REQUESTS_CA_BUNDLE: ""
    SSL_CERT_FILE: ""
  ```
- Or use `-k` flag: `curl -k https://...`

### Issue 3: Some URLs work, others don't
**Solution:** NO_PROXY not configured
- Add internal services to NO_PROXY:
  ```
  NO_PROXY=localhost,127.0.0.1,mongodb,redis,qdrant,rabbitmq,.local
  ```

### Issue 4: Build works but runtime fails
**Solution:** Proxy in build args but not environment
- Add proxy to BOTH build args AND environment variables

### Issue 5: Proxy requires authentication
**Solution:** Include credentials in proxy URL
```bash
HTTP_PROXY=http://username:password@proxy.yourcompany.com:8080
```

## Quick Test

```bash
# 1. Check if proxy is needed
curl https://huggingface.co
# If fails → need proxy

# 2. Test with proxy
curl -x http://proxy:port https://huggingface.co
# If works → proxy is correct

# 3. Test with proxy and no SSL
curl -k -x http://proxy:port https://huggingface.co
# If works → need both proxy and SSL disable
```

## Final Configuration Checklist

- [ ] Docker Desktop proxy settings configured
- [ ] `.env` file created with proxy settings
- [ ] `docker-compose.artifactory.yml` has proxy environment variables
- [ ] NO_PROXY includes internal services
- [ ] SSL verification disabled (CURL_CA_BUNDLE="")
- [ ] Tested connectivity from container
- [ ] Rebuild images with: `docker-compose -f docker-compose.artifactory.yml build`
- [ ] Restart containers: `docker-compose -f docker-compose.artifactory.yml up -d`

## Alternative: Use Organization's Docker Registry Mirror

Some organizations provide Docker registry mirrors that work within the corporate network:

```yaml
# docker-compose.artifactory.yml
services:
  backend:
    image: artifactory.yourcompany.com/catalyst-backend:latest
```

Ask your IT team for:
- Docker registry mirror URL
- Artifactory/Nexus credentials
- Internal PyPI mirror URL
- Internal NPM registry URL

## Need Help?

Contact your organization's IT support and ask for:
1. Proxy server address and port
2. Whether proxy requires authentication
3. Internal package registry URLs (PyPI, NPM)
4. Certificate bundle for SSL inspection

---

**After configuration, rebuild and restart:**
```bash
docker-compose -f docker-compose.artifactory.yml down
docker-compose -f docker-compose.artifactory.yml build
docker-compose -f docker-compose.artifactory.yml up -d
```
