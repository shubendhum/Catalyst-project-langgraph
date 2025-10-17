#!/bin/bash
# Complete Artifactory Build Fix - Handles All Issues

set -e

echo "=========================================="
echo "Catalyst Artifactory - Complete Fix"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check we're in the right directory
if [ ! -f "docker-compose.artifactory.yml" ]; then
    echo -e "${RED}Error: Must run from /app directory${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1: Verifying all required files...${NC}"
echo ""

# Check backend files
echo "Backend files:"
if [ -f "backend/requirements.txt" ]; then
    echo -e "${GREEN}✓ backend/requirements.txt${NC}"
else
    echo -e "${RED}✗ backend/requirements.txt MISSING${NC}"
    exit 1
fi

if [ -f "backend/requirements-langgraph.txt" ]; then
    echo -e "${GREEN}✓ backend/requirements-langgraph.txt${NC}"
else
    echo -e "${RED}✗ backend/requirements-langgraph.txt MISSING${NC}"
    exit 1
fi

if [ -f "backend/server.py" ]; then
    echo -e "${GREEN}✓ backend/server.py${NC}"
else
    echo -e "${RED}✗ backend/server.py MISSING${NC}"
    exit 1
fi

echo ""
echo "Frontend files:"

if [ -f "frontend/package.json" ]; then
    echo -e "${GREEN}✓ frontend/package.json${NC}"
else
    echo -e "${RED}✗ frontend/package.json MISSING${NC}"
    exit 1
fi

if [ -f "frontend/yarn.lock" ]; then
    echo -e "${GREEN}✓ frontend/yarn.lock${NC}"
else
    echo -e "${RED}✗ frontend/yarn.lock MISSING${NC}"
    exit 1
fi

# Ensure nginx.conf is in frontend
if [ ! -f "frontend/nginx.conf" ]; then
    echo -e "${YELLOW}⚠ frontend/nginx.conf missing${NC}"
    if [ -f "nginx.conf" ]; then
        cp nginx.conf frontend/nginx.conf
        echo -e "${GREEN}✓ Copied nginx.conf to frontend/${NC}"
    else
        echo -e "${YELLOW}Creating default nginx.conf...${NC}"
        cat > frontend/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    server {
        listen 80;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /api {
            proxy_pass http://backend:8001;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
    }
}
EOF
        echo -e "${GREEN}✓ Created nginx.conf${NC}"
    fi
else
    echo -e "${GREEN}✓ frontend/nginx.conf${NC}"
fi

echo ""
echo -e "${BLUE}Step 2: Testing Artifactory connectivity...${NC}"
echo ""

if ping -c 1 -W 2 artifactory.devtools.syd.c1.macquarie.com &> /dev/null; then
    echo -e "${GREEN}✓ Can reach Artifactory${NC}"
else
    echo -e "${YELLOW}⚠ Cannot reach Artifactory${NC}"
    echo -e "${YELLOW}  Make sure you're connected to VPN${NC}"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Try to pull a test image
echo ""
echo "Testing Docker pull from Artifactory..."
if docker pull artifactory.devtools.syd.c1.macquarie.com:9996/python:3.11-slim &> /dev/null; then
    echo -e "${GREEN}✓ Can pull images from Artifactory${NC}"
else
    echo -e "${YELLOW}⚠ Cannot pull from Artifactory${NC}"
    echo ""
    echo "You may need to login:"
    echo "  docker login artifactory.devtools.syd.c1.macquarie.com:9996"
    echo ""
    read -p "Try to login now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker login artifactory.devtools.syd.c1.macquarie.com:9996
    fi
fi

echo ""
echo -e "${BLUE}Step 3: Cleaning Docker environment...${NC}"
echo ""

# Stop existing containers
echo "Stopping existing containers..."
docker-compose -f docker-compose.artifactory.yml down -v 2>/dev/null || true
echo -e "${GREEN}✓ Stopped containers${NC}"

# Ask about cache cleaning
echo ""
read -p "Clean Docker build cache? (Recommended: y) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleaning Docker cache..."
    docker builder prune -af
    echo -e "${GREEN}✓ Build cache cleaned${NC}"
fi

echo ""
read -p "Clean all Docker cache? (More thorough: y) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleaning all Docker resources..."
    docker system prune -af
    echo -e "${GREEN}✓ All cache cleaned${NC}"
fi

echo ""
echo -e "${BLUE}Step 4: Building images...${NC}"
echo ""
echo "This will take several minutes..."
echo "Building with --no-cache to ensure fresh build"
echo ""

# Build with explicit options
if DOCKER_BUILDKIT=1 docker-compose -f docker-compose.artifactory.yml build --no-cache --progress=plain 2>&1 | tee build.log; then
    echo ""
    echo -e "${GREEN}✓✓✓ Build completed successfully! ✓✓✓${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}✗✗✗ Build failed ✗✗✗${NC}"
    echo ""
    echo "Build log saved to: build.log"
    echo ""
    echo "Common issues:"
    echo "1. Network/VPN: Ensure connected to corporate network"
    echo "2. Authentication: Run 'docker login artifactory.devtools.syd.c1.macquarie.com:9996'"
    echo "3. File permissions: Check all files are readable"
    echo ""
    echo "Debug commands:"
    echo "  cat build.log | grep -i error"
    echo "  cat build.log | grep -i failed"
    echo ""
    exit 1
fi

# Verify images were built
echo ""
echo "Verifying images..."
if docker images | grep -q catalyst-backend; then
    echo -e "${GREEN}✓ Backend image built${NC}"
else
    echo -e "${RED}✗ Backend image not found${NC}"
fi

if docker images | grep -q catalyst-frontend; then
    echo -e "${GREEN}✓ Frontend image built${NC}"
else
    echo -e "${RED}✗ Frontend image not found${NC}"
fi

echo ""
echo -e "${BLUE}Step 5: Starting services...${NC}"
echo ""

if docker-compose -f docker-compose.artifactory.yml up -d; then
    echo ""
    echo -e "${GREEN}✓ Services started${NC}"
else
    echo ""
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi

echo ""
echo "Waiting for services to initialize..."
sleep 10

echo ""
echo "Service status:"
docker-compose -f docker-compose.artifactory.yml ps

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
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
echo "Testing backend..."
sleep 2
if curl -s http://localhost:8001/api/ | grep -q "message"; then
    echo -e "${GREEN}✓ Backend is responding${NC}"
else
    echo -e "${YELLOW}⚠ Backend may still be starting up${NC}"
    echo "  Check with: docker-compose -f docker-compose.artifactory.yml logs backend"
fi

echo ""
echo -e "${GREEN}Done!${NC}"
echo ""
