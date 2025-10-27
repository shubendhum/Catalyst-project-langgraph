#!/bin/bash
# Diagnostic Build Script for Frontend
# Helps identify where the build is failing

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Frontend Build Diagnostics                                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Step 1: Check local files${NC}"
echo "─────────────────────────────────────────────────────────────"

if [ -f frontend/package.json ]; then
    echo -e "${GREEN}✅${NC} frontend/package.json exists"
    echo "   Size: $(wc -c < frontend/package.json) bytes"
else
    echo -e "${RED}❌${NC} frontend/package.json MISSING"
    exit 1
fi

if [ -f frontend/nginx.conf ]; then
    echo -e "${GREEN}✅${NC} frontend/nginx.conf exists"
else
    echo -e "${RED}❌${NC} frontend/nginx.conf MISSING"
    exit 1
fi

if [ -f frontend/yarn.lock ]; then
    echo -e "${GREEN}✅${NC} frontend/yarn.lock exists (optional)"
else
    echo -e "${YELLOW}⚠️${NC}  frontend/yarn.lock missing (will be generated)"
fi

echo ""
echo -e "${BLUE}Step 2: Check Dockerfile${NC}"
echo "─────────────────────────────────────────────────────────────"

if [ -f Dockerfile.frontend.artifactory ]; then
    echo -e "${GREEN}✅${NC} Dockerfile.frontend.artifactory exists"
    echo "   Size: $(wc -c < Dockerfile.frontend.artifactory) bytes"
    echo "   Lines: $(wc -l < Dockerfile.frontend.artifactory)"
else
    echo -e "${RED}❌${NC} Dockerfile.frontend.artifactory MISSING"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 3: Check docker-compose config${NC}"
echo "─────────────────────────────────────────────────────────────"

if [ -f docker-compose.artifactory.yml ]; then
    echo -e "${GREEN}✅${NC} docker-compose.artifactory.yml exists"
    
    # Extract frontend build config
    echo "   Frontend build context: $(grep -A 3 'frontend:' docker-compose.artifactory.yml | grep 'context:' | awk '{print $2}')"
    echo "   Frontend dockerfile: $(grep -A 3 'frontend:' docker-compose.artifactory.yml | grep 'dockerfile:' | awk '{print $2}')"
else
    echo -e "${RED}❌${NC} docker-compose.artifactory.yml MISSING"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 4: Test network connectivity${NC}"
echo "─────────────────────────────────────────────────────────────"

if ping -c 1 registry.npmjs.org > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Can reach registry.npmjs.org"
else
    echo -e "${YELLOW}⚠️${NC}  Cannot ping registry.npmjs.org (may be blocked)"
fi

echo ""
echo -e "${BLUE}Step 5: Build with verbose logging${NC}"
echo "─────────────────────────────────────────────────────────────"
echo ""
echo -e "${YELLOW}Starting Docker build...${NC}"
echo "This will show detailed output to help identify where it hangs."
echo ""

# Build with progress=plain to see all output
docker-compose -f docker-compose.artifactory.yml build frontend --progress=plain 2>&1 | while IFS= read -r line; do
    echo "$(date '+%H:%M:%S') | $line"
    
    # Check for specific patterns
    if echo "$line" | grep -q "COPY package.json"; then
        echo -e "${GREEN}✓ Copying package.json${NC}"
    fi
    
    if echo "$line" | grep -q "yarn install"; then
        echo -e "${YELLOW}⚡ Starting yarn install - this may take 2-3 minutes${NC}"
    fi
    
    if echo "$line" | grep -q "DIAGNOSTIC: Yarn install completed"; then
        echo -e "${GREEN}✓ Yarn install complete!${NC}"
    fi
    
    if echo "$line" | grep -q "craco build"; then
        echo -e "${YELLOW}⚡ Starting React build${NC}"
    fi
done

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Build completed! Check output above for any errors.${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
