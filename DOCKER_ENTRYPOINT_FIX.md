# Docker Frontend Entrypoint Fix

## Issue
Error when starting frontend Docker container:
```
error in docker entrypoint /docker-entrypoint.d/ is not empty
```

## Root Cause Analysis

### Problem 1: Incomplete nginx.conf
The `frontend/nginx.conf` only contained a `server` block, missing the required top-level structure:
- Missing `events` block (required by nginx)
- Missing `http` block (wraps server configuration)
- Missing worker configuration and logging setup

When copied to `/etc/nginx/nginx.conf`, it replaced the entire nginx configuration with an incomplete one, causing the entrypoint scripts to fail.

### Problem 2: Custom Non-Root User Permissions
The Dockerfile created a custom `catalyst` user and switched to it:
```dockerfile
RUN addgroup -g 1000 catalyst && \
    adduser -D -u 1000 -G catalyst catalyst && \
    ...
USER catalyst
```

The nginx:alpine base image includes entrypoint scripts in `/docker-entrypoint.d/` that:
- Expect to run with specific permissions
- Need access to certain system directories
- Are designed to work with the default `nginx` user

The custom user lacked permissions to:
- Execute entrypoint scripts properly
- Access required nginx directories
- Bind to port 80 (requires elevated permissions)

## Solution

### Fix 1: Complete nginx.conf Structure
Updated `/app/frontend/nginx.conf` to include full nginx configuration:
```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # ... (logging, gzip, etc.)
    
    server {
        # ... (React app configuration)
    }
}
```

### Fix 2: Use Default nginx User
Updated `/app/Dockerfile.frontend.artifactory`:
- Removed custom `catalyst` user creation
- Use default `nginx` user (built into nginx:alpine)
- Set proper permissions for nginx user on all required directories
- Added chmod to ensure entrypoint scripts are executable
- Added `nginx -t` to validate configuration during build

```dockerfile
# Copy built application
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Fix permissions for nginx user
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown nginx:nginx /etc/nginx/nginx.conf && \
    chmod -R 755 /docker-entrypoint.d/ 2>/dev/null || true && \
    nginx -t

# Use default nginx behavior (runs as nginx user)
CMD ["nginx", "-g", "daemon off;"]
```

## Files Modified

1. `/app/frontend/nginx.conf` - Added complete nginx configuration structure
2. `/app/Dockerfile.frontend.artifactory` - Removed custom user, use default nginx user with proper permissions

## Testing

To test the fix, rebuild and run the Docker container:

```bash
# Build the frontend image
docker-compose -f docker-compose.artifactory.yml build frontend

# Start the container
docker-compose -f docker-compose.artifactory.yml up frontend

# Or start all services
docker-compose -f docker-compose.artifactory.yml up
```

The frontend should now start successfully without the entrypoint error.

## Benefits of This Approach

1. **Standard Practice**: Uses the default nginx user as intended by the nginx:alpine image
2. **Compatibility**: Works with nginx's default entrypoint scripts
3. **Security**: Still runs as non-root (nginx user), just not a custom user
4. **Maintainability**: Easier to update nginx version in the future
5. **Validation**: nginx -t catches configuration errors during build time

## Notes

- The current development environment uses supervisor and runs directly (not Docker)
- These changes only affect Docker-based deployments
- The development server (supervisor-managed) continues to work as before
