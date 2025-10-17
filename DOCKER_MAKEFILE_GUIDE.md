# Makefile Docker-First Setup Guide

## 🐳 Docker Desktop Setup (Default)

The Catalyst Makefile now uses **Docker Desktop as the primary setup method**. Everything runs in containers!

## ⚡ Quick Start

### Prerequisites
- **Docker Desktop** installed and running
- That's it! No Python, Node.js, or other tools needed locally

### One-Command Setup

```bash
# 1. Complete setup (builds Docker images)
make setup

# 2. Start all services
make start

# Access at http://localhost:3000
```

**That's it! Everything runs in Docker containers.**

---

## 📋 Docker-First Commands

### Setup & Installation

```bash
make setup              # Complete Docker setup (builds all images)
make check-docker       # Verify Docker Desktop is running
make setup-env          # Create .env files
```

### Service Management (Docker)

```bash
make start              # Start all services in Docker (default)
make stop               # Stop all Docker services
make restart            # Restart Docker services
make status             # Show service status
make logs               # View Docker Compose logs
```

### Docker Operations

```bash
make docker-build       # Build/rebuild Docker images
make docker-up          # Start Docker Compose services
make docker-down        # Stop and remove containers
make docker-logs        # Stream Docker logs
make docker-status      # Show container status
make docker-prod        # Start in production mode
```

### Testing

```bash
make test               # Run tests in Docker containers
make test-api           # Test API endpoints with curl
```

### Database (Docker)

```bash
make db-shell           # Open MongoDB shell in container
make db-backup          # Backup MongoDB
make db-restore         # Restore MongoDB backup
```

### Kubernetes

```bash
make k8s-deploy         # Deploy to Kubernetes
make k8s-delete         # Delete deployment
make k8s-status         # Show status
```

### Cleanup

```bash
make clean              # Clean temporary files
make clean-all          # Remove all Docker volumes and images
make reset              # Complete reset and setup
```

---

## 🔧 Alternative: Local Development

If you prefer local development (Python/Node on your machine):

### Local Setup

```bash
make setup-local        # Install dependencies locally
make start-local        # Start services locally
make stop-local         # Stop local services
make restart-local      # Restart local services
```

### Local Service Commands

```bash
make start-backend-local    # Start backend with uvicorn
make start-frontend-local   # Start frontend with yarn
make stop-backend-local     # Stop backend
make stop-frontend-local    # Stop frontend
```

---

## 📊 Comparison: Docker vs Local

| Feature | Docker (Default) | Local |
|---------|------------------|-------|
| **Setup Time** | 5 min | 10-15 min |
| **Prerequisites** | Docker only | Python, Node, Docker |
| **Isolation** | ✅ Complete | ❌ Shares system |
| **Consistency** | ✅ Identical everywhere | ⚠️ May vary |
| **Resource Usage** | Moderate | Lower |
| **Portability** | ✅ Works anywhere | ⚠️ System dependent |
| **Recommended** | ✅ **YES** | For development only |

---

## 🚀 Docker Workflow Examples

### First Time Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd catalyst

# 2. Setup (builds images, creates .env)
make setup

# 3. Start services
make start

# 4. Access application
open http://localhost:3000
```

### Daily Development

```bash
# Morning
make start              # Start all services

# Check status
make status

# View logs
make logs

# End of day
make stop
```

### Making Code Changes

```bash
# Edit code in your editor
# ...

# Rebuild and restart
make docker-build
make restart

# Or for development (auto-reload)
make start
# Services hot-reload automatically!
```

### Testing Workflow

```bash
# Run all tests
make test

# Test API
make test-api

# View backend logs
make logs
```

### Database Operations

```bash
# Backup database
make db-backup

# Access MongoDB shell
make db-shell

# Restore from backup
make db-restore BACKUP_DIR=backups/backup-20240101
```

---

## 🎯 What Runs in Docker?

### Services (Docker Containers)

1. **MongoDB** - Database
   - Port: 27017
   - Auto-configured with credentials
   - Persistent volume for data

2. **Backend** - FastAPI + LangGraph
   - Port: 8001
   - Hot reload enabled
   - Connected to MongoDB

3. **Frontend** - React + Nginx
   - Port: 3000
   - Production-optimized
   - Connects to backend API

### Docker Compose Configuration

File: `docker-compose.yml`

```yaml
services:
  mongodb:
    image: mongo:5.0
    ports: ["27017:27017"]
    volumes: [mongodb_data:/data/db]
  
  backend:
    build: ./backend
    ports: ["8001:8001"]
    depends_on: [mongodb]
  
  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]
```

---

## 🔍 Verifying Docker Setup

### Check Docker Desktop

```bash
# Is Docker running?
docker info

# Check version
docker --version
docker-compose --version
```

### Using Makefile

```bash
# Automatic check
make check-docker

# Output:
# ✓ Docker is installed and running
```

### View Running Containers

```bash
# Using Make
make docker-status

# Using Docker directly
docker ps
```

---

## 🐛 Troubleshooting

### Docker Not Running

**Error**: "Docker is not running!"

**Solution**:
```bash
# macOS/Windows: Open Docker Desktop application
# Linux: sudo systemctl start docker
```

### Port Already in Use

**Error**: "Port 3000 is already allocated"

**Solution**:
```bash
# Stop conflicting service
make stop

# Or find and kill process
lsof -ti:3000 | xargs kill -9

# Then restart
make start
```

### Image Build Fails

**Error**: Build errors during `make setup`

**Solution**:
```bash
# Clean everything
make clean-all

# Rebuild from scratch
make setup
```

### Container Crashes

**Error**: Container exits immediately

**Solution**:
```bash
# Check logs
make logs

# Rebuild specific service
docker-compose build backend  # or frontend

# Restart
make restart
```

### Can't Connect to Backend

**Error**: Frontend can't reach backend

**Solution**:
```bash
# Verify services are running
make status

# Check backend URL in frontend/.env
cat frontend/.env
# Should be: REACT_APP_BACKEND_URL=http://localhost:8001

# Restart services
make restart
```

---

## 📖 Environment Variables

### Auto-Generated Files

`make setup` creates:

**backend/.env**:
```bash
MONGO_URL=mongodb://admin:catalyst_admin_pass@mongodb:27017
DB_NAME=catalyst_db
EMERGENT_LLM_KEY=sk-emergent-b14E29723DeDaF2A74
DEFAULT_LLM_PROVIDER=emergent
DEFAULT_LLM_MODEL=claude-3-7-sonnet-20250219
```

**frontend/.env**:
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Custom Configuration

Edit `.env` files after `make setup`:

```bash
# Edit backend config
nano backend/.env

# Edit frontend config
nano frontend/.env

# Restart to apply changes
make restart
```

---

## 🎨 Docker Commands Reference

### Core Commands

| Command | Description |
|---------|-------------|
| `make setup` | Complete Docker setup |
| `make start` | Start all services |
| `make stop` | Stop all services |
| `make restart` | Restart services |
| `make logs` | View logs |
| `make status` | Service status |

### Development Commands

| Command | Description |
|---------|-------------|
| `make docker-build` | Rebuild images |
| `make test` | Run tests |
| `make db-shell` | MongoDB shell |
| `make clean` | Clean temp files |

### Advanced Commands

| Command | Description |
|---------|-------------|
| `make docker-prod` | Production mode |
| `make k8s-deploy` | Deploy to K8s |
| `make db-backup` | Backup database |
| `make reset` | Full reset |

---

## 💡 Pro Tips

### 1. Fast Iteration

```bash
# Hot reload is enabled
# Just edit files and save
# Backend/Frontend reload automatically
```

### 2. View Specific Service Logs

```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs  
docker-compose logs -f frontend

# MongoDB logs
docker-compose logs -f mongodb
```

### 3. Execute Commands in Containers

```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend sh

# MongoDB shell
docker-compose exec mongodb mongo -u admin -p catalyst_admin_pass
```

### 4. Rebuild Single Service

```bash
# Rebuild backend only
docker-compose build backend

# Restart backend only
docker-compose restart backend
```

### 5. Check Resource Usage

```bash
# Docker stats
docker stats

# Container sizes
docker-compose ps --services | xargs -I {} docker-compose images {}
```

---

## 🚀 Production Deployment

### Production Mode

```bash
# Use production compose file
make docker-prod

# Or directly
docker-compose -f docker-compose.prod.yml up -d
```

### Differences: Dev vs Prod

| Feature | Development | Production |
|---------|-------------|------------|
| Hot Reload | ✅ Enabled | ❌ Disabled |
| Optimization | Minimal | Full |
| Logs | Verbose | Structured |
| Resources | No limits | Limited |
| Nginx | Not used | ✅ Enabled |

---

## 📚 Additional Resources

- **Docker Desktop**: https://www.docker.com/products/docker-desktop
- **Docker Compose Docs**: https://docs.docker.com/compose/
- **Makefile Guide**: See [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)
- **Full Deployment**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## ✅ Checklist

Before starting:
- [ ] Docker Desktop installed
- [ ] Docker Desktop is running
- [ ] Cloned repository

Setup:
- [ ] Run `make setup`
- [ ] Verify `.env` files created
- [ ] Check Docker images built

Start:
- [ ] Run `make start`
- [ ] Verify services running (`make status`)
- [ ] Access http://localhost:3000

---

**Everything runs in Docker - Simple, Consistent, Portable!** 🐳✨
