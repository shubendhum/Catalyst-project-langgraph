#!/bin/bash
# Makefile-style deployment script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

function print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

function print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

function print_error() {
    echo -e "${RED}✗ $1${NC}"
}

function print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Help function
function show_help() {
    cat << EOF
Catalyst Deployment Helper

Usage: ./deploy.sh [command]

Commands:
  local         - Start local development environment
  docker        - Build and run Docker containers
  docker-prod   - Build and run production Docker containers
  build         - Build Docker images
  test          - Run tests
  k8s           - Deploy to Kubernetes
  clean         - Clean up Docker containers and images
  logs          - Show logs
  help          - Show this help message

Examples:
  ./deploy.sh local
  ./deploy.sh docker-prod
  ./deploy.sh k8s
EOF
}

# Local development
function deploy_local() {
    print_header "Starting Local Development"
    
    print_info "Checking prerequisites..."
    command -v python3 >/dev/null 2>&1 || { print_error "Python 3 not found"; exit 1; }
    command -v node >/dev/null 2>&1 || { print_error "Node.js not found"; exit 1; }
    print_success "Prerequisites OK"
    
    print_info "Starting MongoDB..."
    docker run -d \
        --name catalyst-mongo-dev \
        -p 27017:27017 \
        -e MONGO_INITDB_ROOT_USERNAME=admin \
        -e MONGO_INITDB_ROOT_PASSWORD=catalyst_admin_pass \
        mongo:5.0 2>/dev/null || echo "MongoDB already running"
    
    print_success "MongoDB started"
    print_info "Backend: Run 'cd backend && uvicorn server:app --reload'"
    print_info "Frontend: Run 'cd frontend && yarn start'"
}

# Docker deployment
function deploy_docker() {
    print_header "Docker Deployment"
    
    print_info "Building and starting containers..."
    docker-compose up -d --build
    
    print_success "Containers started"
    docker-compose ps
    
    echo ""
    print_info "Access:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:8001/api"
    echo "  Logs:     docker-compose logs -f"
}

# Production Docker deployment
function deploy_docker_prod() {
    print_header "Production Docker Deployment"
    
    print_info "Building and starting production containers..."
    docker-compose -f docker-compose.prod.yml up -d --build
    
    print_success "Production containers started"
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    print_info "Access:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:8001/api"
    echo "  Logs:     docker-compose -f docker-compose.prod.yml logs -f"
}

# Build images
function build_images() {
    print_header "Building Docker Images"
    
    print_info "Building backend image..."
    docker build -f Dockerfile.backend -t catalyst-backend:latest .
    print_success "Backend image built"
    
    print_info "Building frontend image..."
    docker build -f Dockerfile.frontend -t catalyst-frontend:latest .
    print_success "Frontend image built"
    
    docker images | grep catalyst
}

# Kubernetes deployment
function deploy_k8s() {
    print_header "Kubernetes Deployment"
    
    print_info "Creating namespace..."
    kubectl create namespace catalyst 2>/dev/null || echo "Namespace exists"
    
    print_info "Creating secrets..."
    kubectl create secret generic catalyst-secrets \
        --from-literal=mongo-username=admin \
        --from-literal=mongo-password=catalyst_admin_pass \
        --from-literal=emergent-llm-key=sk-emergent-b14E29723DeDaF2A74 \
        --from-literal=mongo-url=mongodb://admin:catalyst_admin_pass@mongodb:27017 \
        -n catalyst 2>/dev/null || echo "Secrets exist"
    
    print_info "Deploying MongoDB..."
    kubectl apply -f k8s/mongodb-deployment.yaml -n catalyst
    
    print_info "Deploying Backend..."
    kubectl apply -f k8s/backend-deployment.yaml -n catalyst
    
    print_info "Deploying Frontend..."
    kubectl apply -f k8s/frontend-deployment.yaml -n catalyst
    
    print_success "Deployment complete"
    
    echo ""
    print_info "Checking status..."
    kubectl get pods -n catalyst
    
    echo ""
    print_info "Port forward:"
    echo "  kubectl port-forward service/catalyst-frontend 3000:80 -n catalyst"
    echo "  kubectl port-forward service/catalyst-backend 8001:8001 -n catalyst"
}

# Clean up
function clean_up() {
    print_header "Cleaning Up"
    
    print_info "Stopping containers..."
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    
    print_info "Removing images..."
    docker rmi catalyst-backend:latest 2>/dev/null || true
    docker rmi catalyst-frontend:latest 2>/dev/null || true
    
    print_success "Cleanup complete"
}

# Show logs
function show_logs() {
    print_header "Container Logs"
    
    if [ -f "docker-compose.prod.yml" ] && docker-compose -f docker-compose.prod.yml ps | grep -q Up; then
        docker-compose -f docker-compose.prod.yml logs -f
    else
        docker-compose logs -f
    fi
}

# Main
case "${1:-help}" in
    local)
        deploy_local
        ;;
    docker)
        deploy_docker
        ;;
    docker-prod)
        deploy_docker_prod
        ;;
    build)
        build_images
        ;;
    k8s)
        deploy_k8s
        ;;
    clean)
        clean_up
        ;;
    logs)
        show_logs
        ;;
    help|*)
        show_help
        ;;
esac
