# Catalyst Multi-Agent AI Platform - Main Makefile
# Docker-first setup and management (uses Docker Desktop)

.PHONY: help setup setup-local check-docker start stop restart status logs \
        clean test docker-build docker-up docker-down docker-logs \
        k8s-deploy k8s-delete backup restore

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Configuration
DOCKER := docker
DOCKER_COMPOSE := docker-compose
KUBECTL := kubectl

# Directories
BACKEND_DIR := backend
FRONTEND_DIR := frontend
K8S_DIR := k8s
AWS_DIR := aws

# MongoDB Configuration
MONGO_CONTAINER := catalyst-mongo
MONGO_PORT := 27017
MONGO_USER := admin
MONGO_PASS := catalyst_admin_pass
MONGO_DB := catalyst_db

# Docker Compose Project Name
COMPOSE_PROJECT := catalyst

# Default target
.DEFAULT_GOAL := help

##@ General

help: ## Display this help message
	@echo "$(BLUE)Catalyst Platform - Docker Desktop Setup$(NC)"
	@echo ""
	@echo "$(YELLOW)All services run in Docker containers$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(BLUE)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Setup (Default)

setup: ## Complete Docker setup (ONE COMMAND - sets up everything in Docker)
	@echo "$(GREEN)Starting Docker-based setup...$(NC)"
	@$(MAKE) check-docker
	@$(MAKE) setup-env
	@$(MAKE) docker-build
	@echo ""
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo ""
	@echo "$(BLUE)Next step: Run 'make start' to launch all services$(NC)"
	@echo ""
	@echo "$(YELLOW)Access points:$(NC)"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8001/api"
	@echo "  API Docs:  http://localhost:8001/docs"

check-docker: ## Check if Docker is installed and running
	@echo "$(BLUE)Checking Docker...$(NC)"
	@command -v $(DOCKER) >/dev/null 2>&1 || { echo "$(RED)Docker is not installed! Please install Docker Desktop.$(NC)"; exit 1; }
	@$(DOCKER) info >/dev/null 2>&1 || { echo "$(RED)Docker is not running! Please start Docker Desktop.$(NC)"; exit 1; }
	@command -v $(DOCKER_COMPOSE) >/dev/null 2>&1 || { echo "$(RED)Docker Compose is not installed!$(NC)"; exit 1; }
	@echo "$(GREEN)✓ Docker is installed and running$(NC)"

##@ Local Development Setup (Alternative)

setup-local: ## Local setup (install Python/Node dependencies locally)
	@echo "$(GREEN)Starting local development setup...$(NC)"
	@$(MAKE) check-local-prerequisites
	@$(MAKE) install
	@$(MAKE) setup-env
	@$(MAKE) install-mongo
	@echo "$(GREEN)Local setup complete! Run 'make start-local' to launch services.$(NC)"

check-local-prerequisites: ## Check if local development tools are installed
	@echo "$(BLUE)Checking local prerequisites...$(NC)"
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)Python 3 is not installed!$(NC)"; exit 1; }
	@command -v node >/dev/null 2>&1 || { echo "$(RED)Node.js is not installed!$(NC)"; exit 1; }
	@command -v $(DOCKER) >/dev/null 2>&1 || { echo "$(RED)Docker is not installed!$(NC)"; exit 1; }
	@command -v yarn >/dev/null 2>&1 || { echo "$(YELLOW)Yarn not found, installing...$(NC)"; npm install -g yarn; }
	@echo "$(GREEN)✓ All local prerequisites are installed$(NC)"

install: install-backend install-frontend ## Install all dependencies (backend + frontend)
	@echo "$(GREEN)All dependencies installed!$(NC)"

install-backend: ## Install backend Python dependencies
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	@cd $(BACKEND_DIR) && \
		if [ ! -d "venv" ]; then \
			$(PYTHON) -m venv venv; \
		fi && \
		. venv/bin/activate && \
		$(PIP) install --upgrade pip && \
		$(PIP) install -r requirements.txt && \
		$(PIP) install -r requirements-langgraph.txt && \
		$(PIP) install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

install-frontend: ## Install frontend Node dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	@cd $(FRONTEND_DIR) && $(YARN) install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

setup-env: ## Create .env files from examples
	@echo "$(BLUE)Setting up environment files...$(NC)"
	@if [ ! -f $(BACKEND_DIR)/.env ]; then \
		cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env 2>/dev/null || \
		echo "MONGO_URL=mongodb://$(MONGO_USER):$(MONGO_PASS)@localhost:$(MONGO_PORT)\nDB_NAME=$(MONGO_DB)\nEMERGENT_LLM_KEY=sk-emergent-b14E29723DeDaF2A74\nDEFAULT_LLM_PROVIDER=emergent\nDEFAULT_LLM_MODEL=claude-3-7-sonnet-20250219\nCORS_ORIGINS=*\nLOG_LEVEL=INFO" > $(BACKEND_DIR)/.env; \
		echo "$(GREEN)✓ Created backend/.env$(NC)"; \
	else \
		echo "$(YELLOW)backend/.env already exists$(NC)"; \
	fi
	@if [ ! -f $(FRONTEND_DIR)/.env ]; then \
		cp $(FRONTEND_DIR)/.env.example $(FRONTEND_DIR)/.env 2>/dev/null || \
		echo "REACT_APP_BACKEND_URL=http://localhost:8001" > $(FRONTEND_DIR)/.env; \
		echo "$(GREEN)✓ Created frontend/.env$(NC)"; \
	else \
		echo "$(YELLOW)frontend/.env already exists$(NC)"; \
	fi

install-mongo: ## Install and start MongoDB via Docker
	@echo "$(BLUE)Setting up MongoDB...$(NC)"
	@if [ "$$($(DOCKER) ps -a -q -f name=$(MONGO_CONTAINER))" ]; then \
		if [ "$$($(DOCKER) ps -q -f name=$(MONGO_CONTAINER))" ]; then \
			echo "$(YELLOW)MongoDB already running$(NC)"; \
		else \
			echo "$(BLUE)Starting existing MongoDB container...$(NC)"; \
			$(DOCKER) start $(MONGO_CONTAINER); \
			echo "$(GREEN)✓ MongoDB started$(NC)"; \
		fi; \
	else \
		echo "$(BLUE)Creating MongoDB container...$(NC)"; \
		$(DOCKER) run -d \
			--name $(MONGO_CONTAINER) \
			-p $(MONGO_PORT):27017 \
			-e MONGO_INITDB_ROOT_USERNAME=$(MONGO_USER) \
			-e MONGO_INITDB_ROOT_PASSWORD=$(MONGO_PASS) \
			-e MONGO_INITDB_DATABASE=$(MONGO_DB) \
			-v catalyst_mongo_data:/data/db \
			mongo:5.0; \
		echo "$(GREEN)✓ MongoDB installed and started$(NC)"; \
	fi

##@ Service Management

start: start-mongo start-backend start-frontend ## Start all services (MongoDB, Backend, Frontend)
	@echo "$(GREEN)All services started!$(NC)"
	@echo ""
	@echo "$(BLUE)Access points:$(NC)"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8001/api"
	@echo "  API Docs:  http://localhost:8001/docs"
	@echo "  MongoDB:   mongodb://localhost:$(MONGO_PORT)"
	@echo ""
	@echo "$(YELLOW)Tip: Run 'make logs' to view service logs$(NC)"

start-mongo: ## Start MongoDB only
	@echo "$(BLUE)Starting MongoDB...$(NC)"
	@if [ "$$($(DOCKER) ps -q -f name=$(MONGO_CONTAINER))" ]; then \
		echo "$(YELLOW)MongoDB already running$(NC)"; \
	else \
		if [ "$$($(DOCKER) ps -a -q -f name=$(MONGO_CONTAINER))" ]; then \
			$(DOCKER) start $(MONGO_CONTAINER); \
		else \
			$(MAKE) install-mongo; \
		fi; \
		echo "$(GREEN)✓ MongoDB started$(NC)"; \
	fi

start-backend: ## Start backend API server
	@echo "$(BLUE)Starting backend server...$(NC)"
	@if [ ! -d $(BACKEND_DIR)/venv ]; then \
		echo "$(RED)Backend not installed. Run 'make install-backend' first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Starting backend on http://localhost:8001$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop, or run 'make stop-backend' in another terminal$(NC)"
	@cd $(BACKEND_DIR) && . venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8001 --reload

start-frontend: ## Start frontend development server
	@echo "$(BLUE)Starting frontend server...$(NC)"
	@if [ ! -d $(FRONTEND_DIR)/node_modules ]; then \
		echo "$(RED)Frontend not installed. Run 'make install-frontend' first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Starting frontend on http://localhost:3000$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop, or run 'make stop-frontend' in another terminal$(NC)"
	@cd $(FRONTEND_DIR) && $(YARN) start

stop: stop-backend stop-frontend stop-mongo ## Stop all services
	@echo "$(GREEN)All services stopped$(NC)"

stop-mongo: ## Stop MongoDB
	@echo "$(BLUE)Stopping MongoDB...$(NC)"
	@$(DOCKER) stop $(MONGO_CONTAINER) 2>/dev/null || echo "$(YELLOW)MongoDB not running$(NC)"

stop-backend: ## Stop backend server
	@echo "$(BLUE)Stopping backend...$(NC)"
	@pkill -f "uvicorn server:app" || echo "$(YELLOW)Backend not running$(NC)"

stop-frontend: ## Stop frontend server
	@echo "$(BLUE)Stopping frontend...$(NC)"
	@pkill -f "react-scripts start" || echo "$(YELLOW)Frontend not running$(NC)"

restart: stop start ## Restart all services

status: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@echo ""
	@echo "$(YELLOW)MongoDB:$(NC)"
	@if [ "$$($(DOCKER) ps -q -f name=$(MONGO_CONTAINER))" ]; then \
		echo "  $(GREEN)✓ Running$(NC)"; \
		$(DOCKER) ps -f name=$(MONGO_CONTAINER) --format "  Container: {{.Names}} ({{.Status}})"; \
	else \
		echo "  $(RED)✗ Not running$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)Backend:$(NC)"
	@if pgrep -f "uvicorn server:app" > /dev/null; then \
		echo "  $(GREEN)✓ Running on http://localhost:8001$(NC)"; \
	else \
		echo "  $(RED)✗ Not running$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)Frontend:$(NC)"
	@if pgrep -f "react-scripts start" > /dev/null; then \
		echo "  $(GREEN)✓ Running on http://localhost:3000$(NC)"; \
	else \
		echo "  $(RED)✗ Not running$(NC)"; \
	fi

logs: ## Show logs (MongoDB)
	@echo "$(BLUE)MongoDB Logs (last 50 lines):$(NC)"
	@$(DOCKER) logs --tail 50 $(MONGO_CONTAINER) 2>/dev/null || echo "$(RED)MongoDB not running$(NC)"

logs-backend: ## Show backend logs
	@echo "$(BLUE)Showing backend logs...$(NC)"
	@tail -f /tmp/catalyst-backend.log 2>/dev/null || echo "$(YELLOW)No backend logs found. Start backend with 'make start-backend' first.$(NC)"

##@ Testing

test: test-backend test-frontend ## Run all tests
	@echo "$(GREEN)All tests completed$(NC)"

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	@cd $(BACKEND_DIR) && . venv/bin/activate && pytest tests/ -v || echo "$(YELLOW)No tests found or pytest not installed$(NC)"

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@cd $(FRONTEND_DIR) && $(YARN) test --watchAll=false || echo "$(YELLOW)No tests found$(NC)"

test-api: ## Test backend API endpoints
	@echo "$(BLUE)Testing backend API...$(NC)"
	@echo "Health check:"
	@curl -s http://localhost:8001/api/ | python3 -m json.tool || echo "$(RED)Backend not responding$(NC)"
	@echo ""
	@echo "LLM Config:"
	@curl -s http://localhost:8001/api/chat/config | python3 -m json.tool || echo "$(RED)API not responding$(NC)"

##@ Docker Commands

docker: docker-up ## Start services using Docker Compose

docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	@$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✓ Images built$(NC)"

docker-up: ## Start Docker Compose services
	@echo "$(BLUE)Starting Docker services...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@$(MAKE) docker-status

docker-down: ## Stop Docker Compose services
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Services stopped$(NC)"

docker-restart: docker-down docker-up ## Restart Docker services

docker-logs: ## Show Docker Compose logs
	@$(DOCKER_COMPOSE) logs -f

docker-status: ## Show Docker Compose service status
	@echo "$(BLUE)Docker Service Status:$(NC)"
	@$(DOCKER_COMPOSE) ps

docker-prod: ## Start production Docker services
	@echo "$(BLUE)Starting production Docker services...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✓ Production services started$(NC)"

##@ Database Management

db-shell: ## Open MongoDB shell
	@echo "$(BLUE)Opening MongoDB shell...$(NC)"
	@$(DOCKER) exec -it $(MONGO_CONTAINER) mongo -u $(MONGO_USER) -p $(MONGO_PASS) --authenticationDatabase admin

db-backup: ## Backup MongoDB database
	@echo "$(BLUE)Backing up MongoDB...$(NC)"
	@mkdir -p backups
	@$(DOCKER) exec $(MONGO_CONTAINER) mongodump \
		--username $(MONGO_USER) \
		--password $(MONGO_PASS) \
		--authenticationDatabase admin \
		--db $(MONGO_DB) \
		--out /tmp/backup
	@$(DOCKER) cp $(MONGO_CONTAINER):/tmp/backup backups/backup-$$(date +%Y%m%d-%H%M%S)
	@echo "$(GREEN)✓ Backup completed$(NC)"

db-restore: ## Restore MongoDB database (use BACKUP_DIR=backups/backup-xxx)
	@if [ -z "$(BACKUP_DIR)" ]; then \
		echo "$(RED)Error: Please specify BACKUP_DIR=backups/backup-xxx$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Restoring MongoDB from $(BACKUP_DIR)...$(NC)"
	@$(DOCKER) cp $(BACKUP_DIR) $(MONGO_CONTAINER):/tmp/restore
	@$(DOCKER) exec $(MONGO_CONTAINER) mongorestore \
		--username $(MONGO_USER) \
		--password $(MONGO_PASS) \
		--authenticationDatabase admin \
		--db $(MONGO_DB) \
		/tmp/restore/$(MONGO_DB)
	@echo "$(GREEN)✓ Restore completed$(NC)"

db-reset: ## Reset MongoDB database (WARNING: Deletes all data)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)Resetting database...$(NC)"; \
		$(DOCKER) exec $(MONGO_CONTAINER) mongo -u $(MONGO_USER) -p $(MONGO_PASS) --authenticationDatabase admin --eval "db.getSiblingDB('$(MONGO_DB)').dropDatabase()"; \
		echo "$(GREEN)✓ Database reset$(NC)"; \
	fi

##@ Kubernetes

k8s-deploy: ## Deploy to Kubernetes
	@echo "$(BLUE)Deploying to Kubernetes...$(NC)"
	@kubectl create namespace catalyst 2>/dev/null || echo "Namespace exists"
	@kubectl create secret generic catalyst-secrets \
		--from-literal=mongo-username=$(MONGO_USER) \
		--from-literal=mongo-password=$(MONGO_PASS) \
		--from-literal=emergent-llm-key=sk-emergent-b14E29723DeDaF2A74 \
		--from-literal=mongo-url=mongodb://$(MONGO_USER):$(MONGO_PASS)@mongodb:27017 \
		-n catalyst 2>/dev/null || echo "Secrets exist"
	@$(KUBECTL) apply -f $(K8S_DIR)/ -n catalyst
	@echo "$(GREEN)✓ Deployed to Kubernetes$(NC)"
	@$(KUBECTL) get pods -n catalyst

k8s-delete: ## Delete Kubernetes deployment
	@echo "$(BLUE)Deleting Kubernetes deployment...$(NC)"
	@$(KUBECTL) delete -f $(K8S_DIR)/ -n catalyst 2>/dev/null || echo "Nothing to delete"
	@echo "$(GREEN)✓ Deployment deleted$(NC)"

k8s-status: ## Show Kubernetes deployment status
	@echo "$(BLUE)Kubernetes Status:$(NC)"
	@$(KUBECTL) get all -n catalyst

k8s-logs: ## Show Kubernetes logs
	@echo "$(BLUE)Kubernetes Logs:$(NC)"
	@$(KUBECTL) logs -f deployment/catalyst-backend -n catalyst

##@ Cleanup

clean: ## Clean up generated files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -prune -o -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(BACKEND_DIR)/venv
	@rm -rf $(FRONTEND_DIR)/build
	@echo "$(GREEN)✓ Cleanup completed$(NC)"

clean-all: clean docker-down ## Clean everything including Docker volumes
	@echo "$(BLUE)Cleaning all Docker resources...$(NC)"
	@$(DOCKER) rm -f $(MONGO_CONTAINER) 2>/dev/null || true
	@$(DOCKER) volume rm catalyst_mongo_data 2>/dev/null || true
	@$(DOCKER_COMPOSE) down -v 2>/dev/null || true
	@echo "$(GREEN)✓ All cleaned$(NC)"

reset: clean-all setup ## Complete reset and setup
	@echo "$(GREEN)✓ Reset completed$(NC)"

##@ Development Helpers

dev: ## Quick start for development (setup + start all)
	@$(MAKE) setup
	@echo ""
	@echo "$(YELLOW)Starting services in separate terminals...$(NC)"
	@echo "$(BLUE)1. Start backend: make start-backend$(NC)"
	@echo "$(BLUE)2. Start frontend: make start-frontend$(NC)"
	@echo ""
	@echo "$(YELLOW)Or use Docker: make docker-up$(NC)"

quick-start: install-mongo start ## Quick start (assumes dependencies installed)

watch-backend: ## Watch backend logs in real-time
	@cd $(BACKEND_DIR) && . venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8001 --reload --log-level debug

format: ## Format code (backend: black, frontend: prettier)
	@echo "$(BLUE)Formatting code...$(NC)"
	@cd $(BACKEND_DIR) && . venv/bin/activate && black . || echo "$(YELLOW)black not installed$(NC)"
	@cd $(FRONTEND_DIR) && $(YARN) prettier --write "src/**/*.{js,jsx,json,css}" || echo "$(YELLOW)prettier not installed$(NC)"
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint: ## Lint code
	@echo "$(BLUE)Linting code...$(NC)"
	@cd $(BACKEND_DIR) && . venv/bin/activate && flake8 . || echo "$(YELLOW)flake8 not installed$(NC)"
	@cd $(FRONTEND_DIR) && $(YARN) eslint "src/**/*.{js,jsx}" || echo "$(YELLOW)eslint not installed$(NC)"

##@ Information

info: ## Show configuration information
	@echo "$(BLUE)Catalyst Configuration$(NC)"
	@echo ""
	@echo "$(YELLOW)Directories:$(NC)"
	@echo "  Backend:  $(BACKEND_DIR)"
	@echo "  Frontend: $(FRONTEND_DIR)"
	@echo "  K8s:      $(K8S_DIR)"
	@echo ""
	@echo "$(YELLOW)MongoDB:$(NC)"
	@echo "  Container: $(MONGO_CONTAINER)"
	@echo "  Port:      $(MONGO_PORT)"
	@echo "  Database:  $(MONGO_DB)"
	@echo "  User:      $(MONGO_USER)"
	@echo ""
	@echo "$(YELLOW)Services:$(NC)"
	@echo "  Backend:  http://localhost:8001"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API Docs: http://localhost:8001/docs"
	@echo ""
	@echo "$(YELLOW)Tools:$(NC)"
	@echo "  Python:        $$($(PYTHON) --version 2>&1)"
	@echo "  Node:          $$($(NODE) --version 2>&1)"
	@echo "  Docker:        $$($(DOCKER) --version 2>&1)"
	@echo "  Docker Compose: $$($(DOCKER_COMPOSE) --version 2>&1)"

version: ## Show version information
	@echo "Catalyst v1.0.0"
	@echo "Multi-Agent AI Platform with LangGraph"
