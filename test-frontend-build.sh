#!/bin/bash
# Test different Docker build approaches for frontend
# Helps identify which method works in your environment

set -e

echo "🔨 Frontend Docker Build Tester"
echo "================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to frontend directory
cd /app/frontend

# Test counter
PASSED=0
FAILED=0

# Function to test build
test_build() {
    local dockerfile=$1
    local tag=$2
    local description=$3
    
    echo -e "${BLUE}Testing: $description${NC}"
    echo "Dockerfile: $dockerfile"
    echo "Building..."
    
    if docker build -f ../$dockerfile -t $tag . > /tmp/build_$tag.log 2>&1; then
        echo -e "${GREEN}✅ SUCCESS${NC}: $description"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}: $description"
        echo "Last 20 lines of error:"
        tail -n 20 /tmp/build_$tag.log
        ((FAILED++))
        return 1
    fi
    echo ""
}

echo "📋 Pre-flight Checks"
echo "-------------------"

# Check files exist
if [ -f "package.json" ] && [ -f "yarn.lock" ]; then
    echo -e "${GREEN}✓${NC} package.json and yarn.lock found"
else
    echo -e "${RED}✗${NC} package.json or yarn.lock missing!"
    exit 1
fi

if [ -f "nginx.conf" ]; then
    echo -e "${GREEN}✓${NC} nginx.conf found"
else
    echo -e "${RED}✗${NC} nginx.conf missing!"
    exit 1
fi

# Check Docker is running
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker is running"
else
    echo -e "${RED}✗${NC} Docker is not running!"
    exit 1
fi

echo ""
echo "🧪 Running Build Tests"
echo "---------------------"
echo ""

# Test 1: Standard Dockerfile (public registry)
echo "Test 1/4: Standard Node Image (Public Registry)"
test_build "Dockerfile.frontend.standard" "catalyst-frontend-standard" "Standard Node:18-alpine"
sleep 2
echo ""

# Test 2: Artifactory with timeouts
echo "Test 2/4: Artifactory with Network Timeouts"
test_build "Dockerfile.frontend.artifactory" "catalyst-frontend-artifactory" "Artifactory with timeouts"
sleep 2
echo ""

# Test 3: Alternative with retry logic
echo "Test 3/4: Alternative Dockerfile (Retry Logic)"
test_build "Dockerfile.frontend.artifactory.alt" "catalyst-frontend-alt" "Alternative with retry"
sleep 2
echo ""

# Test 4: Docker Compose build
echo "Test 4/4: Docker Compose Build"
cd /app
if docker-compose -f docker-compose.artifactory.yml build frontend > /tmp/build_compose.log 2>&1; then
    echo -e "${GREEN}✅ SUCCESS${NC}: Docker Compose build"
    ((PASSED++))
else
    echo -e "${RED}❌ FAILED${NC}: Docker Compose build"
    echo "Last 20 lines of error:"
    tail -n 20 /tmp/build_compose.log
    ((FAILED++))
fi
cd /app/frontend
echo ""

# Summary
echo "📊 Test Summary"
echo "==============="
echo -e "Passed: ${GREEN}$PASSED${NC}/4"
echo -e "Failed: ${RED}$FAILED${NC}/4"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo ""
    echo "Recommended build method:"
    echo "  docker-compose -f docker-compose.artifactory.yml build frontend"
    echo ""
    exit 0
elif [ $PASSED -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Some tests passed${NC}"
    echo ""
    echo "Working build methods:"
    docker images | grep "catalyst-frontend" | head -n 5
    echo ""
    echo "You can use any of the successful methods above."
    echo ""
    echo "To use a specific Dockerfile, update docker-compose.artifactory.yml:"
    echo "  frontend:"
    echo "    build:"
    echo "      dockerfile: ../Dockerfile.frontend.standard  # or .alt"
    exit 0
else
    echo -e "${RED}❌ All tests failed${NC}"
    echo ""
    echo "Common issues to check:"
    echo "1. Network connectivity to npm registry"
    echo "2. Docker resources (need 4GB+ RAM)"
    echo "3. Artifactory access (try standard Node image)"
    echo "4. Check build logs in /tmp/build_*.log"
    echo ""
    echo "Next steps:"
    echo "1. Review logs: ls -lh /tmp/build_*.log"
    echo "2. Check most recent error: tail -50 /tmp/build_*.log"
    echo "3. See YARN_INSTALL_TROUBLESHOOTING.md for solutions"
    exit 1
fi
