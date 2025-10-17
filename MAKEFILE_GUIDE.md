# Makefile Usage Guide

Complete guide for using Makefiles to set up and manage Catalyst locally.

## Quick Start

### One-Command Setup

```bash
# Complete setup (install everything + MongoDB)
make setup

# Start all services
make start
```

That's it! Your Catalyst platform is now running.

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001/api
- **API Docs**: http://localhost:8001/docs
- **MongoDB**: mongodb://localhost:27017

---

## Main Makefile Commands

### Setup & Installation

```bash
make setup              # Complete one-command setup
make check-prerequisites # Check if required tools are installed
make install            # Install all dependencies (backend + frontend)
make install-backend    # Install backend Python dependencies
make install-frontend   # Install frontend Node dependencies
make install-mongo      # Install and start MongoDB via Docker
make setup-env          # Create .env files from examples
```

### Service Management

```bash
make start              # Start all services (MongoDB, Backend, Frontend)
make start-mongo        # Start MongoDB only
make start-backend      # Start backend API server
make start-frontend     # Start frontend development server

make stop               # Stop all services
make stop-mongo         # Stop MongoDB
make stop-backend       # Stop backend server
make stop-frontend      # Stop frontend server

make restart            # Restart all services
make status             # Show status of all services
make logs               # Show MongoDB logs
```

### Testing

```bash
make test               # Run all tests (backend + frontend)
make test-backend       # Run backend tests
make test-frontend      # Run frontend tests
make test-api           # Test backend API endpoints with curl
```

### Docker Commands

```bash
make docker             # Start services using Docker Compose
make docker-build       # Build Docker images
make docker-up          # Start Docker Compose services
make docker-down        # Stop Docker Compose services
make docker-restart     # Restart Docker services
make docker-logs        # Show Docker Compose logs
make docker-status      # Show Docker service status
make docker-prod        # Start production Docker services
```

### Database Management

```bash
make db-shell           # Open MongoDB shell
make db-backup          # Backup MongoDB database
make db-restore         # Restore MongoDB (use BACKUP_DIR=path)
make db-reset           # Reset database (WARNING: Deletes all data)
```

### Kubernetes

```bash
make k8s-deploy         # Deploy to Kubernetes
make k8s-delete         # Delete Kubernetes deployment
make k8s-status         # Show Kubernetes deployment status
make k8s-logs           # Show Kubernetes logs
```

### Cleanup

```bash
make clean              # Clean up generated files and caches
make clean-all          # Clean everything including Docker volumes
make reset              # Complete reset and setup
```

### Development Helpers

```bash
make dev                # Quick start for development
make quick-start        # Quick start (assumes dependencies installed)
make watch-backend      # Watch backend logs in real-time
make format             # Format code (backend: black, frontend: prettier)
make lint               # Lint code
```

### Information

```bash
make info               # Show configuration information
make version            # Show version information
make help               # Display help message with all commands
```

---

## Backend Makefile

Located in `/backend/Makefile`

```bash
cd backend

make install            # Install backend dependencies
make install-dev        # Install development dependencies
make run                # Run backend server
make run-prod           # Run backend in production mode
make test               # Run tests with coverage
make test-watch         # Run tests in watch mode
make lint               # Run linter (flake8)
make format             # Format code (black)
make type-check         # Run type checker (mypy)
make shell              # Open Python shell
make clean              # Clean up generated files
make clean-all          # Clean everything including venv
make freeze             # Freeze dependencies to requirements-frozen.txt
make help               # Show backend help
```

---

## Frontend Makefile

Located in `/frontend/Makefile`

```bash
cd frontend

make install            # Install frontend dependencies
make start              # Start development server
make build              # Build for production
make build-analyze      # Build and analyze bundle size
make test               # Run tests with coverage
make test-watch         # Run tests in watch mode
make lint               # Run ESLint
make lint-fix           # Fix linting issues
make format             # Format code (Prettier)
make format-check       # Check code formatting
make serve              # Serve production build
make clean              # Clean build artifacts
make clean-all          # Clean everything including node_modules
make update             # Update dependencies interactively
make help               # Show frontend help
```

---

## Common Workflows

### First Time Setup

```bash
# 1. Complete setup
make setup

# 2. Start services (in separate terminals)
# Terminal 1: Backend
make start-backend

# Terminal 2: Frontend
make start-frontend

# Or use Docker instead
make docker-up
```

### Daily Development

```bash
# Start all services
make start

# Check status
make status

# View logs
make logs

# Run tests
make test

# Stop services
make stop
```

### Using Docker

```bash
# Start with Docker
make docker-up

# View logs
make docker-logs

# Stop
make docker-down
```

### Testing Workflow

```bash
# Test API
make test-api

# Test backend
make test-backend

# Test frontend
make test-frontend

# Run all tests
make test
```

### Database Operations

```bash
# Backup database
make db-backup

# Restore database
make db-restore BACKUP_DIR=backups/backup-20240101-120000

# Open MongoDB shell
make db-shell

# Reset database (WARNING: destructive)
make db-reset
```

### Code Quality

```bash
# Format all code
make format

# Lint all code
make lint

# Backend specific
cd backend
make format
make lint
make type-check

# Frontend specific
cd frontend
make format
make lint
make lint-fix
```

### Production Deployment

```bash
# Build production images
make docker-build

# Start production services
make docker-prod

# Or deploy to Kubernetes
make k8s-deploy
```

---

## Environment Variables

### Automatic Setup

```bash
make setup-env
```

This creates:
- `backend/.env` with MongoDB connection and LLM config
- `frontend/.env` with backend URL

### Manual Configuration

Edit `.env` files after creation:

**backend/.env**:
```bash
MONGO_URL=mongodb://admin:catalyst_admin_pass@localhost:27017
DB_NAME=catalyst_db
EMERGENT_LLM_KEY=sk-emergent-b14E29723DeDaF2A74
DEFAULT_LLM_PROVIDER=emergent
DEFAULT_LLM_MODEL=claude-3-7-sonnet-20250219
```

**frontend/.env**:
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## Troubleshooting

### Prerequisites Check Failed

```bash
# Check what's missing
make check-prerequisites

# Install missing tools:
# - Python 3.11+: https://python.org
# - Node.js 16+: https://nodejs.org
# - Docker: https://docker.com
```

### Backend Won't Start

```bash
# Reinstall dependencies
cd backend
make clean-all
make install

# Check MongoDB
make status
make start-mongo
```

### Frontend Won't Start

```bash
# Reinstall dependencies
cd frontend
make clean-all
make install
```

### Port Already in Use

```bash
# Stop all services
make stop

# Or stop specific service
make stop-backend
make stop-frontend
```

### MongoDB Connection Issues

```bash
# Check MongoDB status
make status

# Restart MongoDB
make stop-mongo
make start-mongo

# View logs
make logs
```

### Docker Issues

```bash
# Clean Docker resources
make docker-down
make clean-all

# Rebuild
make docker-build
make docker-up
```

---

## Advanced Usage

### Custom MongoDB Configuration

Edit `Makefile` variables:
```makefile
MONGO_PORT := 27018  # Change port
MONGO_DB := my_catalyst_db  # Change database name
```

### Running Specific Backend Module

```bash
cd backend
. venv/bin/activate
python -m agents.planner
```

### Running Frontend Tests with Coverage

```bash
cd frontend
make test
# Coverage report in coverage/lcov-report/index.html
```

### Building Optimized Frontend

```bash
cd frontend
make build
make serve  # Test production build locally
```

---

## Performance Tips

### Faster Startup

```bash
# Keep MongoDB running
make start-mongo

# Start only what you need
make start-backend  # Or
make start-frontend
```

### Parallel Testing

```bash
# Backend with pytest-xdist
cd backend
. venv/bin/activate
pytest -n auto

# Frontend
cd frontend
yarn test --maxWorkers=4
```

### Docker Build Optimization

```bash
# Use BuildKit
DOCKER_BUILDKIT=1 make docker-build

# Cache layers
make docker-build  # Subsequent builds are faster
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup
        run: make setup
      - name: Test
        run: make test
```

### GitLab CI Example

```yaml
test:
  script:
    - make setup
    - make test
```

---

## Makefile Targets Summary

| Category | Target | Description |
|----------|--------|-------------|
| **Setup** | `make setup` | Complete one-command setup |
| **Services** | `make start` | Start all services |
| **Services** | `make stop` | Stop all services |
| **Services** | `make status` | Show service status |
| **Testing** | `make test` | Run all tests |
| **Docker** | `make docker-up` | Start Docker services |
| **Database** | `make db-backup` | Backup database |
| **K8s** | `make k8s-deploy` | Deploy to Kubernetes |
| **Cleanup** | `make clean` | Clean generated files |
| **Info** | `make help` | Show all commands |

---

## Quick Reference Card

### Essential Commands

```bash
make setup              # First time setup
make start              # Start services
make stop               # Stop services
make test               # Run tests
make docker-up          # Use Docker
make clean              # Clean up
make help               # Show help
```

### Service URLs

```bash
http://localhost:3000        # Frontend
http://localhost:8001/api    # Backend API
http://localhost:8001/docs   # API Documentation
mongodb://localhost:27017    # MongoDB
```

---

## Support

For issues or questions:
- Run `make help` for command list
- Run `make info` for configuration
- Check logs with `make logs`
- See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed docs

---

**All Makefiles are production-ready and tested!** 🎉
