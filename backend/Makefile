# Backend Makefile
# Separate Makefile for backend-specific tasks

.PHONY: install test lint format clean run shell

# Configuration
PYTHON := python3
PIP := pip3
VENV := venv
REQUIREMENTS := requirements.txt requirements-langgraph.txt

# Colors
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m

install: ## Install backend dependencies
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		$(PYTHON) -m venv $(VENV); \
	fi
	@. $(VENV)/bin/activate && \
		$(PIP) install --upgrade pip && \
		$(PIP) install -r requirements.txt && \
		$(PIP) install -r requirements-langgraph.txt && \
		$(PIP) install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

install-dev: install ## Install development dependencies
	@. $(VENV)/bin/activate && \
		$(PIP) install pytest black flake8 mypy pytest-asyncio pytest-cov
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"

run: ## Run backend server
	@echo "$(BLUE)Starting backend server...$(NC)"
	@. $(VENV)/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8001 --reload

run-prod: ## Run backend in production mode
	@echo "$(BLUE)Starting backend in production mode...$(NC)"
	@. $(VENV)/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	@. $(VENV)/bin/activate && pytest tests/ -v --cov=. --cov-report=html

test-watch: ## Run tests in watch mode
	@. $(VENV)/bin/activate && pytest-watch tests/

lint: ## Run linter
	@echo "$(BLUE)Running linter...$(NC)"
	@. $(VENV)/bin/activate && flake8 . --exclude=venv,__pycache__ --max-line-length=120

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	@. $(VENV)/bin/activate && black . --exclude=venv
	@echo "$(GREEN)✓ Code formatted$(NC)"

type-check: ## Run type checker
	@echo "$(BLUE)Running type checker...$(NC)"
	@. $(VENV)/bin/activate && mypy . --exclude=venv

shell: ## Open Python shell with app context
	@. $(VENV)/bin/activate && $(PYTHON)

clean: ## Clean up generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf htmlcov .coverage
	@echo "$(GREEN)✓ Cleanup completed$(NC)"

clean-all: clean ## Clean everything including venv
	@rm -rf $(VENV)
	@echo "$(GREEN)✓ All cleaned$(NC)"

freeze: ## Freeze dependencies
	@. $(VENV)/bin/activate && $(PIP) freeze > requirements-frozen.txt
	@echo "$(GREEN)✓ Dependencies frozen to requirements-frozen.txt$(NC)"

help: ## Show this help
	@echo "Backend Makefile Commands:"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
