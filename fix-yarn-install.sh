#!/bin/bash
# Quick fix for yarn install failures in Docker build

echo "🔧 Quick Fix for Yarn Install Issues"
echo "====================================="
echo ""

# Backup original Dockerfile
if [ ! -f "/app/Dockerfile.frontend.artifactory.backup" ]; then
    cp /app/Dockerfile.frontend.artifactory /app/Dockerfile.frontend.artifactory.backup
    echo "✓ Backed up original Dockerfile"
fi

# Apply fixes to main Dockerfile
echo "Applying fixes to Dockerfile.frontend.artifactory..."

cat > /app/Dockerfile.frontend.artifactory << 'EOF'
# Catalyst Frontend Dockerfile - Artifactory Version (Fixed)
# Multi-stage build for optimized production image
# Build context: /app/frontend (frontend directory)

# Stage 1: Build stage
FROM artifactory.devtools.syd.c1.macquarie.com:9996/node:18-alpine as builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    git \
    && yarn --version

# Copy package files from frontend directory
COPY package.json yarn.lock ./

# Install dependencies with increased timeout and retry logic
# Increased timeout to 10 minutes and limited concurrency
RUN yarn install --frozen-lockfile \
    --network-timeout 600000 \
    --network-concurrency 1 || \
    (echo "Retrying yarn install..." && \
     yarn cache clean && \
     yarn install --network-timeout 600000 --network-concurrency 1)

# Copy source code
COPY . ./

# Build arguments for environment variables
ARG REACT_APP_BACKEND_URL=http://localhost:8001
ENV REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}

# Build application
RUN yarn build

# Stage 2: Runtime stage with Nginx
FROM artifactory.devtools.syd.c1.macquarie.com:9996/nginx:alpine

# Copy custom nginx config from frontend directory
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application
COPY --from=builder /app/build /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1000 catalyst && \
    adduser -D -u 1000 -G catalyst catalyst && \
    chown -R catalyst:catalyst /usr/share/nginx/html && \
    chown -R catalyst:catalyst /var/cache/nginx && \
    chown -R catalyst:catalyst /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown catalyst:catalyst /var/run/nginx.pid

USER catalyst

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
EOF

echo "✓ Applied fixes:"
echo "  - Added build dependencies (python3, make, g++, git)"
echo "  - Increased network timeout to 10 minutes"
echo "  - Limited network concurrency to 1"
echo "  - Added retry logic with cache clean"
echo ""

# Option to use standard Node image instead
echo "Alternative: Use standard Node image (public registry)"
echo "To use this instead, run:"
echo "  cd /app"
echo "  sed -i 's|dockerfile: ../Dockerfile.frontend.artifactory|dockerfile: ../Dockerfile.frontend.standard|' docker-compose.artifactory.yml"
echo ""

echo "🚀 Ready to build!"
echo ""
echo "Try building now with:"
echo "  cd /app"
echo "  docker-compose -f docker-compose.artifactory.yml build frontend"
echo ""
echo "Or test all methods:"
echo "  /app/test-frontend-build.sh"
echo ""

echo "To restore original Dockerfile:"
echo "  cp /app/Dockerfile.frontend.artifactory.backup /app/Dockerfile.frontend.artifactory"
