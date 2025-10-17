#!/bin/bash
# Artifactory Build Validation Script
# Validates that all files are in correct locations for Docker builds

set -e

echo "🔍 Catalyst Artifactory Build Validation"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validation counters
PASSED=0
FAILED=0

# Function to check file exists
check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description: $file"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $description: $file ${RED}NOT FOUND${NC}"
        ((FAILED++))
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $description: $dir"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $description: $dir ${RED}NOT FOUND${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "📁 Checking Directory Structure"
echo "--------------------------------"
check_dir "/app" "Root directory"
check_dir "/app/backend" "Backend directory"
check_dir "/app/frontend" "Frontend directory"
check_dir "/app/k8s" "Kubernetes directory"
echo ""

echo "🔧 Checking Backend Files"
echo "-------------------------"
check_file "/app/Dockerfile.backend.artifactory" "Backend Dockerfile"
check_file "/app/backend/requirements.txt" "Backend requirements"
check_file "/app/backend/requirements-langgraph.txt" "LangGraph requirements"
check_file "/app/backend/server.py" "Backend server"
check_file "/app/backend/.env" "Backend environment"
echo ""

echo "🎨 Checking Frontend Files"
echo "---------------------------"
check_file "/app/Dockerfile.frontend.artifactory" "Frontend Dockerfile"
check_file "/app/frontend/package.json" "Frontend package.json"
check_file "/app/frontend/yarn.lock" "Frontend yarn.lock"
check_file "/app/frontend/nginx.conf" "Frontend nginx.conf"
check_dir "/app/frontend/src" "Frontend source directory"
check_dir "/app/frontend/public" "Frontend public directory"
echo ""

echo "🐳 Checking Docker Compose Files"
echo "---------------------------------"
check_file "/app/docker-compose.artifactory.yml" "Artifactory docker-compose"
check_file "/app/docker-compose.yml" "Standard docker-compose"
echo ""

echo "☸️  Checking Kubernetes Files"
echo "-----------------------------"
check_file "/app/k8s/backend-deployment.artifactory.yaml" "Backend K8s deployment"
check_file "/app/k8s/frontend-deployment.artifactory.yaml" "Frontend K8s deployment"
check_file "/app/k8s/mongodb-deployment.artifactory.yaml" "MongoDB K8s deployment"
check_file "/app/k8s/deploy-artifactory.sh" "K8s deploy script"
echo ""

echo "🔍 Validating Docker Compose Configuration"
echo "-------------------------------------------"

# Check if docker-compose is valid
if docker-compose -f /app/docker-compose.artifactory.yml config > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker Compose configuration is valid"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} Docker Compose configuration has errors"
    ((FAILED++))
fi

# Extract and display build contexts
echo ""
echo "📋 Build Context Configuration:"
echo "-------------------------------"
echo "Backend:"
echo "  Context: . (root directory)"
echo "  Dockerfile: Dockerfile.backend.artifactory"
echo ""
echo "Frontend:"
echo "  Context: ./frontend"
echo "  Dockerfile: ../Dockerfile.frontend.artifactory"
echo ""

echo "🧪 Testing File Path Resolution"
echo "--------------------------------"

# Test if files can be accessed from their respective build contexts
cd /app

# Backend context test
if [ -f "./backend/requirements.txt" ] && [ -f "./backend/requirements-langgraph.txt" ]; then
    echo -e "${GREEN}✓${NC} Backend files accessible from root context"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} Backend files NOT accessible from root context"
    ((FAILED++))
fi

# Frontend context test
if [ -f "./frontend/package.json" ] && [ -f "./frontend/yarn.lock" ] && [ -f "./frontend/nginx.conf" ]; then
    echo -e "${GREEN}✓${NC} Frontend files accessible from frontend context"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} Frontend files NOT accessible from frontend context"
    ((FAILED++))
fi

echo ""
echo "📊 Validation Summary"
echo "====================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All validations passed! Ready to build with Artifactory.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Login to Artifactory:"
    echo "   docker login artifactory.devtools.syd.c1.macquarie.com:9996"
    echo ""
    echo "2. Build services:"
    echo "   docker-compose -f docker-compose.artifactory.yml build"
    echo ""
    echo "3. Or build individually:"
    echo "   # Backend"
    echo "   docker build -f Dockerfile.backend.artifactory -t catalyst-backend ."
    echo "   # Frontend"
    echo "   cd frontend && docker build -f ../Dockerfile.frontend.artifactory -t catalyst-frontend ."
    exit 0
else
    echo -e "${RED}❌ Validation failed! Please fix the issues above before building.${NC}"
    echo ""
    echo "Common fixes:"
    echo "1. Ensure all files are in correct directories"
    echo "2. Check docker-compose.artifactory.yml build contexts"
    echo "3. Verify Dockerfile COPY paths match build contexts"
    exit 1
fi
