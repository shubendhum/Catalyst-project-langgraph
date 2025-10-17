#!/bin/bash
# Quick verification that SSL certificate verification is disabled

echo "🔒 SSL Certificate Verification Check"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

checks_passed=0
checks_total=4

echo "Checking Dockerfile.frontend.artifactory..."
echo ""

# Check 1: yarn config set strict-ssl false
if grep -q "yarn config set strict-ssl false" /app/Dockerfile.frontend.artifactory; then
    echo -e "${GREEN}✓${NC} yarn config set strict-ssl false - FOUND"
    ((checks_passed++))
else
    echo -e "${RED}✗${NC} yarn config set strict-ssl false - MISSING"
fi

# Check 2: npm config set strict-ssl false
if grep -q "npm config set strict-ssl false" /app/Dockerfile.frontend.artifactory; then
    echo -e "${GREEN}✓${NC} npm config set strict-ssl false - FOUND"
    ((checks_passed++))
else
    echo -e "${RED}✗${NC} npm config set strict-ssl false - MISSING"
fi

# Check 3: --disable-ssl flag in yarn install
if grep -q "\-\-disable-ssl" /app/Dockerfile.frontend.artifactory; then
    echo -e "${GREEN}✓${NC} --disable-ssl flag in yarn install - FOUND"
    ((checks_passed++))
else
    echo -e "${RED}✗${NC} --disable-ssl flag in yarn install - MISSING"
fi

# Check 4: SSL disabled comment
if grep -q "SSL verification disabled" /app/Dockerfile.frontend.artifactory; then
    echo -e "${GREEN}✓${NC} SSL verification comment - FOUND"
    ((checks_passed++))
else
    echo -e "${RED}✗${NC} SSL verification comment - MISSING"
fi

echo ""
echo "Score: $checks_passed/$checks_total"
echo ""

if [ $checks_passed -eq $checks_total ]; then
    echo -e "${GREEN}✅ All SSL verification checks disabled!${NC}"
    echo ""
    echo "Ready to build:"
    echo "  docker-compose -f docker-compose.artifactory.yml build frontend"
    echo ""
    echo "This should bypass certificate verification errors."
    exit 0
else
    echo -e "${RED}⚠️  Some SSL checks missing${NC}"
    echo ""
    echo "Run this to apply all fixes:"
    echo "  /app/fix-yarn-install.sh"
    exit 1
fi
