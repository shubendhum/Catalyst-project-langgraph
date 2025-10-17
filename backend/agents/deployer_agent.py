"""
Deployer Agent
Creates Docker containers and handles deployment configuration
"""
import logging
import subprocess
from typing import Dict, Optional
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage
import json

logger = logging.getLogger(__name__)


class DeployerAgent:
    """
    Agent responsible for deployment via Docker
    """
    
    def __init__(self, llm_client, db, manager, file_service):
        self.llm_client = llm_client
        self.db = db
        self.manager = manager
        self.file_service = file_service
        self.agent_name = "Deployer"
    
    async def deploy_application(
        self,
        project_name: str,
        architecture: Dict,
        task_id: Optional[str] = None
    ) -> Dict:
        """
        Create Docker configuration and deployment files
        
        Args:
            project_name: Name of the project
            architecture: Technical architecture
            task_id: Task ID for logging
            
        Returns:
            Dictionary with deployment results
        """
        logger.info(f"Creating deployment configuration for: {project_name}")
        
        if task_id:
            await self._log(task_id, "🐳 Starting Docker deployment configuration...")
        
        deployment_result = {
            "docker_files": {},
            "deployment_instructions": "",
            "status": "pending"
        }
        
        try:
            # Generate Dockerfiles
            if task_id:
                await self._log(task_id, "📝 Generating Dockerfiles...")
            
            backend_dockerfile = await self._generate_backend_dockerfile(architecture)
            frontend_dockerfile = await self._generate_frontend_dockerfile(architecture)
            
            # Generate docker-compose.yml
            if task_id:
                await self._log(task_id, "🔧 Generating docker-compose configuration...")
            
            docker_compose = await self._generate_docker_compose(project_name, architecture)
            
            # Generate .dockerignore files
            backend_dockerignore = self._generate_dockerignore("backend")
            frontend_dockerignore = self._generate_dockerignore("frontend")
            
            # Generate deployment script
            deploy_script = self._generate_deploy_script(project_name)
            
            # Generate environment files
            env_production = self._generate_production_env(architecture)
            
            # Generate nginx config for frontend
            nginx_config = self._generate_nginx_config()
            
            deployment_files = {
                "backend/Dockerfile": backend_dockerfile,
                "frontend/Dockerfile": frontend_dockerfile,
                "docker-compose.yml": docker_compose,
                "backend/.dockerignore": backend_dockerignore,
                "frontend/.dockerignore": frontend_dockerignore,
                "deploy.sh": deploy_script,
                ".env.production": env_production,
                "frontend/nginx.conf": nginx_config,
                "README.DEPLOYMENT.md": await self._generate_deployment_readme(project_name)
            }
            
            # Save all deployment files
            if task_id:
                await self._log(task_id, "💾 Saving deployment configuration files...")
            
            for file_path, content in deployment_files.items():
                self.file_service.write_file(project_name, file_path, content)
            
            deployment_result["docker_files"] = deployment_files
            deployment_result["status"] = "success"
            deployment_result["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            if task_id:
                await self._log(task_id, "✅ Docker deployment configuration complete!")
                await self._log(task_id, "📦 Run: cd project && docker-compose up --build")
            
            return deployment_result
            
        except Exception as e:
            logger.error(f"Error during deployment: {str(e)}")
            deployment_result["status"] = "error"
            deployment_result["error"] = str(e)
            
            if task_id:
                await self._log(task_id, f"❌ Deployment error: {str(e)}")
            
            return deployment_result
    
    async def _generate_backend_dockerfile(self, architecture: Dict) -> str:
        """Generate Dockerfile for backend"""
        
        prompt = """Generate a production-ready Dockerfile for FastAPI backend.

Requirements:
- Python 3.11
- Multi-stage build for optimization
- Install dependencies from requirements.txt
- Use non-root user
- Expose port 8001
- Uvicorn as ASGI server
- Health check endpoint
- Proper layer caching

Generate complete Dockerfile."""

        response = await self.llm_client.ainvoke([HumanMessage(content=prompt)])
        return self._extract_code_from_response(response.content)
    
    async def _generate_frontend_dockerfile(self, architecture: Dict) -> str:
        """Generate Dockerfile for frontend"""
        
        prompt = """Generate a production-ready Dockerfile for React frontend.

Requirements:
- Node.js 18+
- Multi-stage build (build stage + nginx stage)
- Install dependencies and build React app
- Serve with Nginx
- Copy nginx.conf
- Expose port 80
- Health check endpoint
- Proper layer caching
- Optimize build size

Generate complete Dockerfile."""

        response = await self.llm_client.ainvoke([HumanMessage(content=prompt)])
        return self._extract_code_from_response(response.content)
    
    async def _generate_docker_compose(self, project_name: str, architecture: Dict) -> str:
        """Generate docker-compose.yml"""
        
        models = architecture.get('data_models', [])
        needs_db = len(models) > 0
        
        compose_content = f"""version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: {project_name}-backend
    restart: unless-stopped
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME={project_name}_db
    depends_on:
      - mongodb
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: {project_name}-frontend
    restart: unless-stopped
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  mongodb:
    image: mongo:7.0
    container_name: {project_name}-mongodb
    restart: unless-stopped
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  app-network:
    driver: bridge

volumes:
  mongodb_data:
"""
        return compose_content
    
    def _generate_dockerignore(self, service_type: str) -> str:
        """Generate .dockerignore file"""
        
        if service_type == "backend":
            return """__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
.env
*.log
.git
.gitignore
README.md
tests/
.pytest_cache
*.db
*.sqlite3
"""
        else:  # frontend
            return """node_modules
npm-debug.log
.git
.gitignore
README.md
.env.local
.env.development
.env.test
build
.DS_Store
coverage
.vscode
.idea
"""
    
    def _generate_deploy_script(self, project_name: str) -> str:
        """Generate deployment shell script"""
        
        return f"""#!/bin/bash

# Deployment script for {project_name}

echo "🚀 Starting deployment..."

# Build and start containers
echo "📦 Building Docker images..."
docker-compose build

echo "🔄 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker-compose ps

# Run database migrations if needed
# docker-compose exec backend python migrate.py

echo "✅ Deployment complete!"
echo ""
echo "Services running:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8001"
echo "  MongoDB: mongodb://localhost:27017"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
"""
    
    def _generate_production_env(self, architecture: Dict) -> str:
        """Generate production environment file"""
        
        return """# Production Environment Variables

# Backend
MONGO_URL=mongodb://mongodb:27017
DB_NAME=production_db
JWT_SECRET_KEY=CHANGE_THIS_IN_PRODUCTION
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production

# Frontend
REACT_APP_API_URL=http://localhost:8001/api
REACT_APP_ENV=production

# Add other production-specific variables here
"""
    
    def _generate_nginx_config(self) -> str:
        """Generate Nginx configuration for frontend"""
        
        return """server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss application/json;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Handle React Router
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }

    # API proxy (if needed)
    # location /api/ {
    #     proxy_pass http://backend:8001;
    #     proxy_set_header Host $host;
    #     proxy_set_header X-Real-IP $remote_addr;
    # }
}
"""
    
    async def _generate_deployment_readme(self, project_name: str) -> str:
        """Generate deployment instructions"""
        
        return f"""# Deployment Guide for {project_name}

## Prerequisites

- Docker Desktop or Docker Engine installed
- Docker Compose installed
- Ports 3000, 8001, and 27017 available

## Quick Start

### 1. Build and Run

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **MongoDB**: mongodb://localhost:27017

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

### 4. Stop Services

```bash
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v
```

## Manual Deployment

### Build Images

```bash
docker-compose build
```

### Start Services

```bash
docker-compose up -d
```

### Check Status

```bash
docker-compose ps
```

## Production Deployment

### Environment Variables

1. Copy `.env.production` to `.env`
2. Update the following variables:
   - `JWT_SECRET_KEY`: Generate a secure random key
   - `MONGO_URL`: Update with production MongoDB URL
   - `REACT_APP_API_URL`: Update with production backend URL

### Security Checklist

- [ ] Change JWT_SECRET_KEY
- [ ] Use strong database passwords
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Enable monitoring and logging
- [ ] Review CORS settings
- [ ] Update default credentials

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs [service-name]

# Rebuild container
docker-compose up --build [service-name]
```

### Port conflicts

Update port mappings in `docker-compose.yml`

### Database connection issues

Check MongoDB container is running:
```bash
docker-compose ps mongodb
```

## Health Checks

All services have health check endpoints:
- Frontend: http://localhost:3000/health
- Backend: http://localhost:8001/health
- MongoDB: Internal health check

## Scaling (Optional)

To run multiple instances:
```bash
docker-compose up --scale backend=3
```

## Backup Database

```bash
docker-compose exec mongodb mongodump --out=/backup
```

## Restore Database

```bash
docker-compose exec mongodb mongorestore /backup
```
"""
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract code from LLM response"""
        import re
        code_pattern = r'```(?:dockerfile|yaml|bash|nginx)?\n(.*?)\n```'
        matches = re.findall(code_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if matches:
            return matches[0].strip()
        
        return response.strip()
    
    async def _log(self, task_id: str, message: str):
        """Log agent activity"""
        log_doc = {
            "task_id": task_id,
            "agent_name": self.agent_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(task_id, log_doc)


def get_deployer_agent(llm_client, db, manager, file_service) -> DeployerAgent:
    """Get DeployerAgent instance"""
    return DeployerAgent(llm_client, db, manager, file_service)
