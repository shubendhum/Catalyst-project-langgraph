# Catalyst Platform Makefile
# Simplified commands for development and deployment

.PHONY: help setup env build up down restart logs clean test install-deps

# Default target
.DEFAULT_GOAL := help

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

## help: Display this help message
help:
	@echo "${BLUE}Catalyst Platform - Available Commands${NC}"
	@echo ""
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## //' | column -t -s ':'
	@echo ""

## setup: Initial setup - creates .env file from config.yaml
setup:
	@echo "${BLUE}Setting up Catalyst platform...${NC}"
	@if [ ! -f .env ]; then \
		echo "${YELLOW}Creating .env file from config.yaml...${NC}"; \
		python3 scripts/generate_env.py; \
		echo "${GREEN}✓ .env file created${NC}"; \
		echo "${YELLOW}⚠ Please edit .env and add your EMERGENT_LLM_KEY${NC}"; \
	else \
		echo "${GREEN}✓ .env file already exists${NC}"; \
	fi
	@echo "${GREEN}✓ Setup complete!${NC}"

## env: Show current environment variables
env:
	@echo "${BLUE}Current Environment Configuration:${NC}"
	@if [ -f .env ]; then \
		cat .env | grep -v '^#' | grep -v '^$$'; \
	else \
		echo "${RED}✗ .env file not found. Run 'make setup' first${NC}"; \
	fi

## install-deps: Install all dependencies (backend + frontend)
install-deps:
	@echo "${BLUE}Installing dependencies...${NC}"
	@echo "${YELLOW}Installing backend dependencies...${NC}"
	cd backend && pip install -r requirements.txt
	cd backend && pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
	@echo "${GREEN}✓ Backend dependencies installed${NC}"
	@echo "${YELLOW}Installing frontend dependencies...${NC}"
	cd frontend && yarn install
	@echo "${GREEN}✓ Frontend dependencies installed${NC}"
	@echo "${GREEN}✓ All dependencies installed!${NC}"

## build: Build all Docker images
build:
	@echo "${BLUE}Building Docker images...${NC}"
	docker-compose build --no-cache
	@echo "${GREEN}✓ Build complete!${NC}"

## up: Start all services (MongoDB, Backend, Frontend)
up:
	@echo "${BLUE}Starting Catalyst platform...${NC}"
	@if [ ! -f .env ]; then \
		echo "${RED}✗ .env file not found. Run 'make setup' first${NC}"; \
		exit 1; \
	fi
	docker-compose up -d
	@echo "${GREEN}✓ Catalyst is running!${NC}"
	@echo ""
	@echo "${YELLOW}Access URLs:${NC}"
	@echo "  Frontend: ${GREEN}http://localhost:3000${NC}"
	@echo "  Backend API: ${GREEN}http://localhost:8001${NC}"
	@echo "  API Docs: ${GREEN}http://localhost:8001/docs${NC}"
	@echo "  MongoDB: ${GREEN}mongodb://localhost:27017${NC}"
	@echo ""
	@echo "${YELLOW}Run 'make logs' to view logs${NC}"

## down: Stop all services
down:
	@echo "${BLUE}Stopping Catalyst platform...${NC}"
	docker-compose down
	@echo "${GREEN}✓ All services stopped${NC}"

## restart: Restart all services
restart: down up

## logs: View logs from all services
logs:
	@echo "${BLUE}Viewing logs (Ctrl+C to exit)...${NC}"
	docker-compose logs -f

## logs-backend: View backend logs only
logs-backend:
	@echo "${BLUE}Viewing backend logs (Ctrl+C to exit)...${NC}"
	docker-compose logs -f backend

## logs-frontend: View frontend logs only
logs-frontend:
	@echo "${BLUE}Viewing frontend logs (Ctrl+C to exit)...${NC}"
	docker-compose logs -f frontend

## logs-mongodb: View MongoDB logs only
logs-mongodb:
	@echo "${BLUE}Viewing MongoDB logs (Ctrl+C to exit)...${NC}"
	docker-compose logs -f mongodb

## status: Check status of all services
status:
	@echo "${BLUE}Service Status:${NC}"
	@docker-compose ps

## clean: Remove all containers, volumes, and images
clean:
	@echo "${RED}⚠ This will remove all containers, volumes, and images${NC}"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "${BLUE}Cleaning up...${NC}"; \
		docker-compose down -v --rmi all; \
		echo "${GREEN}✓ Cleanup complete${NC}"; \
	else \
		echo "${YELLOW}Cleanup cancelled${NC}"; \
	fi

## test: Run automated tests
test:
	@echo "${BLUE}Running tests...${NC}"
	@if [ -f backend/tests/test_all.py ]; then \
		python3 backend/tests/test_all.py; \
	else \
		echo "${YELLOW}No tests found${NC}"; \
	fi

## shell-backend: Open shell in backend container
shell-backend:
	@echo "${BLUE}Opening backend shell...${NC}"
	docker-compose exec backend /bin/bash

## shell-frontend: Open shell in frontend container
shell-frontend:
	@echo "${BLUE}Opening frontend shell...${NC}"
	docker-compose exec frontend /bin/sh

## shell-mongodb: Open MongoDB shell
shell-mongodb:
	@echo "${BLUE}Opening MongoDB shell...${NC}"
	docker-compose exec mongodb mongosh

## backup-db: Backup MongoDB database
backup-db:
	@echo "${BLUE}Backing up database...${NC}"
	@mkdir -p backups
	@docker-compose exec -T mongodb mongodump --archive > backups/catalyst_backup_$$(date +%Y%m%d_%H%M%S).archive
	@echo "${GREEN}✓ Database backed up to backups/catalyst_backup_*.archive${NC}"

## restore-db: Restore MongoDB database from backup
restore-db:
	@echo "${BLUE}Available backups:${NC}"
	@ls -lh backups/*.archive 2>/dev/null || echo "No backups found"
	@read -p "Enter backup filename: " backup_file; \
	if [ -f "$$backup_file" ]; then \
		echo "${BLUE}Restoring database...${NC}"; \
		docker-compose exec -T mongodb mongorestore --archive < "$$backup_file"; \
		echo "${GREEN}✓ Database restored${NC}"; \
	else \
		echo "${RED}✗ Backup file not found${NC}"; \
	fi

## dev: Start in development mode (with hot reload)
dev: up
	@echo "${GREEN}✓ Development mode active (hot reload enabled)${NC}"

## prod-build: Build for production
prod-build:
	@echo "${BLUE}Building for production...${NC}"
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
	@echo "${GREEN}✓ Production build complete${NC}"

## prod-up: Start in production mode
prod-up:
	@echo "${BLUE}Starting in production mode...${NC}"
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "${GREEN}✓ Production environment running${NC}"

## health: Check health of all services
health:
	@echo "${BLUE}Checking service health...${NC}"
	@echo ""
	@echo "${YELLOW}Backend API:${NC}"
	@curl -s http://localhost:8001/api/ | jq . || echo "${RED}✗ Backend not responding${NC}"
	@echo ""
	@echo "${YELLOW}Frontend:${NC}"
	@curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:3000 || echo "${RED}✗ Frontend not responding${NC}"
	@echo ""
	@echo "${YELLOW}MongoDB:${NC}"
	@docker-compose exec -T mongodb mongosh --eval "db.runCommand({ ping: 1 })" --quiet || echo "${RED}✗ MongoDB not responding${NC}"

## update: Pull latest changes and rebuild
update:
	@echo "${BLUE}Updating Catalyst platform...${NC}"
	git pull
	make build
	make restart
	@echo "${GREEN}✓ Platform updated!${NC}"

## init: Complete initialization (setup + install + build + up)
init: setup install-deps build up
	@echo ""
	@echo "${GREEN}╔════════════════════════════════════════════╗${NC}"
	@echo "${GREEN}║  ✓ Catalyst Platform Initialized!         ║${NC}"
	@echo "${GREEN}╚════════════════════════════════════════════╝${NC}"
	@echo ""
	@echo "${YELLOW}Next steps:${NC}"
	@echo "  1. Edit ${BLUE}.env${NC} and add your ${YELLOW}EMERGENT_LLM_KEY${NC}"
	@echo "  2. Run ${BLUE}make restart${NC} to apply changes"
	@echo "  3. Access platform at ${GREEN}http://localhost:3000${NC}"
	@echo ""