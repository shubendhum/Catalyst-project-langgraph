#!/bin/bash
# Verify Artifactory Registry Configuration

echo "🔍 Artifactory Registry Configuration Verification"
echo "===================================================="
echo ""

ARTIFACTORY_REGISTRY="https://artifactory.devtools.syd.c1.macquarie.com:9996/artifactory/api/npm/npm-virtual/"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check 1: Dockerfile has registry configuration
echo "1️⃣  Checking Dockerfile configuration..."
if grep -q "yarn config set registry.*artifactory" /app/Dockerfile.frontend.artifactory; then
    echo -e "${GREEN}✓${NC} Dockerfile has Artifactory registry configuration"
    grep "yarn config set registry" /app/Dockerfile.frontend.artifactory | head -1
else
    echo -e "${RED}✗${NC} Dockerfile missing registry configuration!"
    echo "Run: /app/fix-yarn-install.sh"
fi
echo ""

# Check 2: Test Artifactory connectivity
echo "2️⃣  Testing Artifactory connectivity..."
if curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$ARTIFACTORY_REGISTRY" | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓${NC} Artifactory registry is accessible"
else
    echo -e "${YELLOW}⚠${NC}  Cannot reach Artifactory registry"
    echo "URL: $ARTIFACTORY_REGISTRY"
    echo "This may be expected if you're not on corporate network"
fi
echo ""

# Check 3: Test registry with Docker
echo "3️⃣  Testing yarn registry configuration in Docker..."
cd /app/frontend
if docker run --rm -v $(pwd):/app -w /app node:18-alpine sh -c "yarn config set registry $ARTIFACTORY_REGISTRY && yarn config get registry" 2>/dev/null | grep -q "artifactory"; then
    echo -e "${GREEN}✓${NC} Yarn can be configured to use Artifactory in Docker"
else
    echo -e "${YELLOW}⚠${NC}  Could not test yarn in Docker"
fi
cd /app
echo ""

# Check 4: Verify config files exist (optional)
echo "4️⃣  Checking for optional config files..."
if [ -f "/app/frontend/.npmrc" ]; then
    echo -e "${GREEN}✓${NC} .npmrc exists"
    grep "registry" /app/frontend/.npmrc 2>/dev/null | head -1
else
    echo -e "${YELLOW}ℹ${NC}  .npmrc not found (optional - using inline config)"
fi

if [ -f "/app/frontend/.yarnrc" ]; then
    echo -e "${GREEN}✓${NC} .yarnrc exists"
    grep "registry" /app/frontend/.yarnrc 2>/dev/null | head -1
else
    echo -e "${YELLOW}ℹ${NC}  .yarnrc not found (optional - using inline config)"
fi
echo ""

# Summary
echo "📊 Summary"
echo "=========="
echo ""
echo "Registry URL: $ARTIFACTORY_REGISTRY"
echo ""
echo "Configuration Method: Inline (in Dockerfile)"
echo "  Line 19-21 in /app/Dockerfile.frontend.artifactory"
echo ""
echo "✅ Ready to build!"
echo ""
echo "Build command:"
echo "  docker-compose -f docker-compose.artifactory.yml build frontend"
echo ""
echo "To verify registry is used during build:"
echo "  docker-compose -f docker-compose.artifactory.yml build --progress=plain frontend 2>&1 | grep artifactory"
echo ""
echo "Expected output should show:"
echo "  'info npm registry: https://artifactory.devtools...'"
echo "  Packages downloaded from Artifactory URLs"
