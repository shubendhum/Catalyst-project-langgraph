#!/bin/bash
# Configure Artifactory NPM Registry for Frontend Build

set -e

echo "🔧 Artifactory NPM Registry Configuration"
echo "=========================================="
echo ""

# Configuration
ARTIFACTORY_URL="artifactory.devtools.syd.c1.macquarie.com:9996"
ARTIFACTORY_REGISTRY="https://${ARTIFACTORY_URL}/artifactory/api/npm/npm-virtual/"

echo "Artifactory Registry: $ARTIFACTORY_REGISTRY"
echo ""

# Ask user for configuration method
echo "Select configuration method:"
echo "1. Inline configuration (in Dockerfile - no auth)"
echo "2. Use .npmrc and .yarnrc files (supports auth)"
echo "3. Use environment variables (for CI/CD)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "✅ Using inline configuration (already applied)"
        echo ""
        echo "The Dockerfile has been updated to configure registry inline:"
        echo "  yarn config set registry $ARTIFACTORY_REGISTRY"
        echo ""
        echo "This is already in /app/Dockerfile.frontend.artifactory"
        echo ""
        echo "Build with:"
        echo "  docker-compose -f docker-compose.artifactory.yml build frontend"
        ;;
    
    2)
        echo ""
        echo "📝 Using .npmrc and .yarnrc configuration files"
        echo ""
        
        # Check if auth is needed
        read -p "Does Artifactory require authentication? (y/n): " need_auth
        
        if [ "$need_auth" = "y" ] || [ "$need_auth" = "Y" ]; then
            echo ""
            echo "Authentication required. Choose method:"
            echo "1. Auth token"
            echo "2. Username/Password (base64)"
            echo ""
            read -p "Enter choice (1-2): " auth_method
            
            if [ "$auth_method" = "1" ]; then
                read -p "Enter auth token: " auth_token
                cat > /app/frontend/.npmrc << EOF
registry=$ARTIFACTORY_REGISTRY
//${ARTIFACTORY_URL}/artifactory/api/npm/npm-virtual/:_authToken=${auth_token}
always-auth=true
fetch-timeout=300000
EOF
            else
                read -p "Enter username: " username
                read -sp "Enter password: " password
                echo ""
                auth_base64=$(echo -n "${username}:${password}" | base64)
                cat > /app/frontend/.npmrc << EOF
registry=$ARTIFACTORY_REGISTRY
//${ARTIFACTORY_URL}/artifactory/api/npm/npm-virtual/:_auth=${auth_base64}
always-auth=true
fetch-timeout=300000
EOF
            fi
        else
            # No auth needed, use template
            cp /app/frontend/.npmrc.artifactory /app/frontend/.npmrc
        fi
        
        # Create .yarnrc
        cp /app/frontend/.yarnrc.artifactory /app/frontend/.yarnrc
        
        echo ""
        echo "✅ Configuration files created:"
        echo "  /app/frontend/.npmrc"
        echo "  /app/frontend/.yarnrc"
        echo ""
        echo "Update docker-compose.artifactory.yml to use config files:"
        echo "  dockerfile: ../Dockerfile.frontend.artifactory.withconfig"
        echo ""
        
        # Update docker-compose
        read -p "Update docker-compose.artifactory.yml automatically? (y/n): " update_compose
        if [ "$update_compose" = "y" ] || [ "$update_compose" = "Y" ]; then
            sed -i 's|dockerfile: ../Dockerfile.frontend.artifactory|dockerfile: ../Dockerfile.frontend.artifactory.withconfig|' /app/docker-compose.artifactory.yml
            echo "✅ docker-compose.artifactory.yml updated"
        fi
        ;;
    
    3)
        echo ""
        echo "🔐 Using environment variables"
        echo ""
        echo "Add to your build command or CI/CD:"
        echo ""
        echo "export NPM_CONFIG_REGISTRY=$ARTIFACTORY_REGISTRY"
        echo "export YARN_REGISTRY=$ARTIFACTORY_REGISTRY"
        echo ""
        echo "If authentication needed:"
        read -p "Enter auth token (or press Enter to skip): " auth_token
        if [ -n "$auth_token" ]; then
            echo "export NPM_TOKEN=$auth_token"
        fi
        echo ""
        echo "Then build with:"
        echo "  docker-compose -f docker-compose.artifactory.yml build frontend"
        ;;
    
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "📋 Verification Steps:"
echo "----------------------"
echo ""
echo "1. Check registry configuration:"
echo "   cd /app/frontend"
echo "   docker run --rm -v \$(pwd):/app -w /app node:18-alpine sh -c 'cat .npmrc || echo \"No .npmrc\"'"
echo ""
echo "2. Test yarn with Artifactory:"
echo "   cd /app/frontend"
echo "   docker run --rm -v \$(pwd):/app -w /app node:18-alpine sh -c 'yarn config get registry'"
echo ""
echo "3. Build Docker image:"
echo "   cd /app"
echo "   docker-compose -f docker-compose.artifactory.yml build frontend"
echo ""
echo "4. Check build logs for Artifactory URL:"
echo "   # Should see: https://artifactory.devtools.syd.c1.macquarie.com:9996/..."
echo ""

echo "🎯 Configuration Complete!"
echo ""
echo "The build should now use Artifactory registry instead of public npm."
