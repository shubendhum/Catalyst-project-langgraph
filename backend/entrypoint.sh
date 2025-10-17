#!/bin/bash
# Entrypoint script for Catalyst Backend
# Handles initialization and graceful startup

set -e

echo "============================================"
echo "Catalyst Backend - Starting"
echo "============================================"
echo ""

# Function to wait for MongoDB
wait_for_mongo() {
    echo "Waiting for MongoDB to be ready..."
    
    MONGO_HOST=$(echo $MONGO_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    MONGO_PORT=$(echo $MONGO_URL | sed -n 's/.*:\([0-9]*\)$/\1/p')
    
    if [ -z "$MONGO_HOST" ]; then
        MONGO_HOST="mongodb"
    fi
    
    if [ -z "$MONGO_PORT" ]; then
        MONGO_PORT="27017"
    fi
    
    echo "Checking MongoDB at $MONGO_HOST:$MONGO_PORT"
    
    MAX_TRIES=30
    COUNT=0
    
    until nc -z $MONGO_HOST $MONGO_PORT 2>/dev/null || [ $COUNT -eq $MAX_TRIES ]; do
        echo "  Attempt $((COUNT+1))/$MAX_TRIES - MongoDB not ready yet..."
        COUNT=$((COUNT+1))
        sleep 2
    done
    
    if [ $COUNT -eq $MAX_TRIES ]; then
        echo "ERROR: MongoDB did not become ready in time"
        exit 1
    fi
    
    echo "✓ MongoDB is ready!"
    echo ""
}

# Function to verify environment variables
check_env_vars() {
    echo "Checking required environment variables..."
    
    REQUIRED_VARS=("MONGO_URL" "DB_NAME" "EMERGENT_LLM_KEY")
    MISSING_VARS=()
    
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            MISSING_VARS+=("$var")
        fi
    done
    
    if [ ${#MISSING_VARS[@]} -ne 0 ]; then
        echo "ERROR: Missing required environment variables:"
        for var in "${MISSING_VARS[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi
    
    echo "✓ All required environment variables are set"
    echo ""
}

# Function to verify Python dependencies
check_dependencies() {
    echo "Verifying Python dependencies..."
    
    python3 -c "import fastapi" || { echo "ERROR: FastAPI not installed"; exit 1; }
    python3 -c "import motor" || { echo "ERROR: Motor not installed"; exit 1; }
    python3 -c "import emergentintegrations" || { echo "ERROR: emergentintegrations not installed"; exit 1; }
    
    echo "✓ All dependencies verified"
    echo ""
}

# Function to display configuration
show_config() {
    echo "Backend Configuration:"
    echo "  Database: ${DB_NAME}"
    echo "  Environment: ${ENVIRONMENT:-development}"
    echo "  Log Level: ${LOG_LEVEL:-INFO}"
    echo "  Workers: ${WORKERS:-1}"
    echo ""
}

# Main execution
echo "Starting initialization..."
echo ""

# Check environment variables
check_env_vars

# Wait for MongoDB
wait_for_mongo

# Verify dependencies
check_dependencies

# Show configuration
show_config

echo "============================================"
echo "Starting FastAPI application..."
echo "============================================"
echo ""

# Execute the main command
exec "$@"