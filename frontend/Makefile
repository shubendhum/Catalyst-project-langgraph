# Frontend Makefile
# Separate Makefile for frontend-specific tasks

.PHONY: install start build test lint format clean

# Configuration
YARN := yarn
NPM := npm

# Colors
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m

install: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	@$(YARN) install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

start: ## Start development server
	@echo "$(BLUE)Starting frontend development server...$(NC)"
	@$(YARN) start

build: ## Build for production
	@echo "$(BLUE)Building for production...$(NC)"
	@$(YARN) build
	@echo "$(GREEN)✓ Build completed$(NC)"

build-analyze: ## Build and analyze bundle size
	@echo "$(BLUE)Building and analyzing...$(NC)"
	@GENERATE_SOURCEMAP=false $(YARN) build
	@npx source-map-explorer 'build/static/js/*.js'

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	@$(YARN) test --watchAll=false --coverage

test-watch: ## Run tests in watch mode
	@$(YARN) test

lint: ## Run ESLint
	@echo "$(BLUE)Running linter...$(NC)"
	@$(YARN) eslint "src/**/*.{js,jsx}"

lint-fix: ## Fix linting issues
	@echo "$(BLUE)Fixing linting issues...$(NC)"
	@$(YARN) eslint "src/**/*.{js,jsx}" --fix
	@echo "$(GREEN)✓ Linting issues fixed$(NC)"

format: ## Format code with Prettier
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(YARN) prettier --write "src/**/*.{js,jsx,json,css,md}"
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting
	@$(YARN) prettier --check "src/**/*.{js,jsx,json,css,md}"

serve: build ## Serve production build
	@echo "$(BLUE)Serving production build...$(NC)"
	@npx serve -s build -l 3000

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning up...$(NC)"
	@rm -rf build
	@rm -rf coverage
	@rm -rf .cache
	@echo "$(GREEN)✓ Cleanup completed$(NC)"

clean-all: clean ## Clean everything including node_modules
	@rm -rf node_modules
	@rm -rf yarn.lock package-lock.json
	@echo "$(GREEN)✓ All cleaned$(NC)"

update: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@$(YARN) upgrade-interactive --latest

help: ## Show this help
	@echo "Frontend Makefile Commands:"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
