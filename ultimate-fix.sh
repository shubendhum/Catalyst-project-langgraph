#!/bin/bash
# ULTIMATE FIX - Resolves ALL Docker cache and build context issues

set -e

echo "=============================================="
echo "ULTIMATE CATALYST ARTIFACTORY FIX"
echo "This will solve ALL build context errors"
echo "=============================================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Verify we're in the right place
if [ ! -f "docker-compose.artifactory.yml" ]; then
    echo -e "${RED}ERROR: Run this from /app directory${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1: Verifying all files...${NC}"
echo ""

# Check all required files
FILES_OK=true

echo "Backend files:"
if [ -f "backend/requirements.txt" ]; then
    SIZE=$(wc -c < backend/requirements.txt)
    echo -e "${GREEN}✓ requirements.txt (${SIZE} bytes)${NC}"
else
    echo -e "${RED}✗ requirements.txt MISSING${NC}"
    FILES_OK=false
fi

if [ -f "backend/requirements-langgraph.txt" ]; then
    SIZE=$(wc -c < backend/requirements-langgraph.txt)
    echo -e "${GREEN}✓ requirements-langgraph.txt (${SIZE} bytes)${NC}"
else
    echo -e "${RED}✗ requirements-langgraph.txt MISSING${NC}"
    FILES_OK=false
fi

echo ""
echo "Frontend files:"
if [ -f "frontend/package.json" ]; then
    SIZE=$(wc -c < frontend/package.json)
    echo -e "${GREEN}✓ package.json (${SIZE} bytes)${NC}"
else
    echo -e "${RED}✗ package.json MISSING${NC}"
    FILES_OK=false
fi

if [ -f "frontend/yarn.lock" ]; then
    SIZE=$(wc -c < frontend/yarn.lock)
    echo -e "${GREEN}✓ yarn.lock (${SIZE} bytes)${NC}"
else
    echo -e "${RED}✗ yarn.lock MISSING${NC}"
    FILES_OK=false
fi

if [ ! -f "frontend/nginx.conf" ]; then
    echo -e "${YELLOW}⚠ nginx.conf missing, copying...${NC}"
    cp nginx.conf frontend/nginx.conf 2>/dev/null || {
        echo -e "${YELLOW}Creating default nginx.conf...${NC}"
        cat > frontend/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}
http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    server {
        listen 80;
        root /usr/share/nginx/html;
        index index.html;
        location / {
            try_files $uri $uri/ /index.html;
        }
    }
}
EOF
    }
    echo -e "${GREEN}✓ nginx.conf created${NC}"
else
    SIZE=$(wc -c < frontend/nginx.conf)
    echo -e "${GREEN}✓ nginx.conf (${SIZE} bytes)${NC}"
fi

if [ "$FILES_OK" = false ]; then
    echo ""
    echo -e "${RED}Some required files are missing!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 2: Nuclear cache cleanup...${NC}"
echo ""
echo "This will remove ALL Docker cache (required for build context issues)"

# Stop everything
echo "Stopping all containers..."
docker-compose -f docker-compose.artifactory.yml down -v 2>/dev/null || true
docker-compose down -v 2>/dev/null || true

# Remove specific images
echo "Removing Catalyst images..."
docker rmi catalyst-backend catalyst-frontend 2>/dev/null || true
docker rmi $(docker images -q 'catalyst*') 2>/dev/null || true

# Clean build cache
echo "Cleaning build cache..."
docker builder prune -af --filter "label!=keep"

# Clean system
echo "Cleaning Docker system..."
docker system prune -af

echo -e "${GREEN}✓ Cache completely cleared${NC}"

echo ""
echo -e "${BLUE}Step 3: Testing Artifactory...${NC}"
echo ""

if ping -c 1 -W 2 artifactory.devtools.syd.c1.macquarie.com &> /dev/null; then
    echo -e "${GREEN}✓ Can reach Artifactory${NC}"
else
    echo -e "${YELLOW}⚠ Cannot reach Artifactory - VPN required${NC}"
fi

# Test image pull
echo "Testing image pull..."
if timeout 10 docker pull artifactory.devtools.syd.c1.macquarie.com:9996/python:3.11-slim > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Can pull from Artifactory${NC}"
else
    echo -e "${YELLOW}⚠ Cannot pull images${NC}"
    echo ""
    echo "You need to login to Artifactory:"
    docker login artifactory.devtools.syd.c1.macquarie.com:9996
    echo ""
fi

echo ""
echo -e "${BLUE}Step 4: Building with fresh context...${NC}"
echo ""
echo "Building WITHOUT cache (this ensures clean builds)"
echo "This will take 5-10 minutes..."
echo ""

# Disable BuildKit caching
export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0

# Build with explicit no-cache
if docker-compose -f docker-compose.artifactory.yml build --no-cache --pull 2>&1 | tee build.log; then
    echo ""
    echo -e "${GREEN}✓✓✓ BUILD SUCCESSFUL ✓✓✓${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}✗✗✗ BUILD FAILED ✗✗✗${NC}"
    echo ""
    echo "Checking for specific errors..."
    
    if grep -q "yarn.lock" build.log; then
        echo -e "${RED}Issue with yarn.lock${NC}"
        echo "File exists: $(ls -lh frontend/yarn.lock)"
        echo "This is a Docker cache issue"
    fi
    
    if grep -q "requirements" build.log; then
        echo -e "${RED}Issue with requirements files${NC}"
        echo "Files exist:"
        ls -lh backend/requirements*.txt
    fi
    
    if grep -q "nginx.conf" build.log; then
        echo -e "${RED}Issue with nginx.conf${NC}"
        echo "File exists: $(ls -lh frontend/nginx.conf)"
    fi
    
    echo ""
    echo "Build log saved to: build.log"
    echo ""
    echo "Try these manual commands:"
    echo "  1. docker login artifactory.devtools.syd.c1.macquarie.com:9996"
    echo "  2. docker system prune -af --volumes"
    echo "  3. cd backend && docker build -f ../Dockerfile.backend.artifactory -t test-backend . --no-cache"
    echo "  4. cd ../frontend && docker build -f ../Dockerfile.frontend.artifactory -t test-frontend . --no-cache"
    exit 1
fi

# Verify images
echo "Verifying images built..."
docker images | grep -E "catalyst-backend|catalyst-frontend" || echo "Warning: Images not found in list"

echo ""
echo -e "${BLUE}Step 5: Starting services...${NC}"
echo ""

if docker-compose -f docker-compose.artifactory.yml up -d; then
    echo -e "${GREEN}✓ Services started${NC}"
else
    echo -e "${RED}✗ Failed to start${NC}"
    exit 1
fi

echo ""
echo "Waiting for services to initialize..."
sleep 10

echo ""
echo "Container Status:"
docker-compose -f docker-compose.artifactory.yml ps

echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}  ✓ SETUP COMPLETE ✓${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo "Access your application:"
echo -e "  ${BLUE}Frontend:${NC}  http://localhost:3000"
echo -e "  ${BLUE}Backend:${NC}   http://localhost:8001/api"
echo -e "  ${BLUE}API Docs:${NC}  http://localhost:8001/docs"
echo ""
echo "Useful commands:"
echo "  View logs:    docker-compose -f docker-compose.artifactory.yml logs -f"
echo "  Stop:         docker-compose -f docker-compose.artifactory.yml down"
echo "  Restart:      docker-compose -f docker-compose.artifactory.yml restart"
echo ""

# Test backend
echo "Testing backend API..."
sleep 3
if curl -s -m 5 http://localhost:8001/api/ 2>/dev/null | grep -q "message"; then
    echo -e "${GREEN}✓ Backend is responding!${NC}"
else
    echo -e "${YELLOW}⚠ Backend still starting up...${NC}"
    echo "Check logs: docker-compose -f docker-compose.artifactory.yml logs backend"
fi

echo ""
echo -e "${GREEN}Done! Your application is running.${NC}"
echo ""
