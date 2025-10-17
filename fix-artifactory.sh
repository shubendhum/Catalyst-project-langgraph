#!/bin/bash
# Automated fix for Docker build errors with Artifactory

set -e

echo "================================================"
echo "Catalyst Artifactory Build Fix Script"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Verify we're in the right directory
if [ ! -f "docker-compose.artifactory.yml" ]; then
    echo -e "${RED}Error: docker-compose.artifactory.yml not found!${NC}"
    echo "Please run this script from the /app directory"
    exit 1
fi

echo -e "${GREEN}✓ Found docker-compose.artifactory.yml${NC}"

# Step 2: Copy nginx.conf to frontend directory
echo ""
echo "Step 1: Ensuring nginx.conf is in frontend directory..."
if [ ! -f "frontend/nginx.conf" ]; then
    if [ -f "nginx.conf" ]; then
        cp nginx.conf frontend/nginx.conf
        echo -e "${GREEN}✓ Copied nginx.conf to frontend/${NC}"
    else
        echo -e "${YELLOW}⚠ nginx.conf not found, creating default...${NC}"
        cat > frontend/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

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
        echo -e "${GREEN}✓ Created default nginx.conf${NC}"
    fi
else
    echo -e "${GREEN}✓ nginx.conf already exists in frontend/${NC}"
fi

# Step 3: Verify required files
echo ""
echo "Step 2: Verifying required files..."

errors=0

if [ ! -f "backend/requirements.txt" ]; then
    echo -e "${RED}✗ backend/requirements.txt not found${NC}"
    errors=$((errors+1))
else
    echo -e "${GREEN}✓ backend/requirements.txt${NC}"
fi

if [ ! -f "backend/requirements-langgraph.txt" ]; then
    echo -e "${RED}✗ backend/requirements-langgraph.txt not found${NC}"
    errors=$((errors+1))
else
    echo -e "${GREEN}✓ backend/requirements-langgraph.txt${NC}"
fi

if [ ! -f "frontend/package.json" ]; then
    echo -e "${RED}✗ frontend/package.json not found${NC}"
    errors=$((errors+1))
else
    echo -e "${GREEN}✓ frontend/package.json${NC}"
fi

if [ ! -f "frontend/yarn.lock" ]; then
    echo -e "${YELLOW}⚠ frontend/yarn.lock not found (will be generated)${NC}"
else
    echo -e "${GREEN}✓ frontend/yarn.lock${NC}"
fi

if [ $errors -gt 0 ]; then
    echo -e "${RED}Found $errors critical errors. Please fix them first.${NC}"
    exit 1
fi

# Step 4: Check Artifactory connectivity
echo ""
echo "Step 3: Checking Artifactory connectivity..."
if ping -c 1 artifactory.devtools.syd.c1.macquarie.com &> /dev/null; then
    echo -e "${GREEN}✓ Can reach Artifactory${NC}"
else
    echo -e "${YELLOW}⚠ Cannot reach Artifactory (VPN required?)${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 5: Clean Docker environment
echo ""
echo "Step 4: Cleaning Docker environment..."
echo "This will remove old containers and images..."
docker-compose -f docker-compose.artifactory.yml down -v 2>/dev/null || true
echo -e "${GREEN}✓ Stopped old containers${NC}"

echo ""
read -p "Clean Docker cache? (recommended, y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker system prune -af
    echo -e "${GREEN}✓ Docker cache cleaned${NC}"
fi

# Step 6: Build images
echo ""
echo "Step 5: Building Docker images with Artifactory..."
echo "This may take several minutes..."
echo ""

if docker-compose -f docker-compose.artifactory.yml build --progress=plain; then
    echo ""
    echo -e "${GREEN}✓ Build successful!${NC}"
else
    echo ""
    echo -e "${RED}✗ Build failed${NC}"
    echo ""
    echo "Common fixes:"
    echo "1. Verify VPN connection to Artifactory"
    echo "2. Login to Artifactory: docker login artifactory.devtools.syd.c1.macquarie.com:9996"
    echo "3. Check build logs above for specific errors"
    echo "4. See QUICK_FIX.md for detailed troubleshooting"
    exit 1
fi

# Step 7: Start services
echo ""
read -p "Start services now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting services..."
    docker-compose -f docker-compose.artifactory.yml up -d
    
    echo ""
    echo "Waiting for services to start..."
    sleep 5
    
    echo ""
    echo "Service status:"
    docker-compose -f docker-compose.artifactory.yml ps
    
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}Setup Complete!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo "Access your application:"
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8001/api"
    echo "  API Docs:  http://localhost:8001/docs"
    echo ""
    echo "View logs:"
    echo "  docker-compose -f docker-compose.artifactory.yml logs -f"
    echo ""
    echo "Stop services:"
    echo "  docker-compose -f docker-compose.artifactory.yml down"
else
    echo ""
    echo "Build complete. Start services manually with:"
    echo "  docker-compose -f docker-compose.artifactory.yml up -d"
fi

echo ""
