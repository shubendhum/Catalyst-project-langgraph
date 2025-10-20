"""
Preview Deployment Service
Handles Docker-in-Docker preview deployments with auto-generated URLs
"""
import logging
import asyncio
import docker
from docker.errors import DockerException
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from uuid import UUID

from config.environment import is_docker_desktop, get_config
from services.postgres_service import get_postgres_service

logger = logging.getLogger(__name__)


class PreviewDeploymentService:
    """
    Manages preview deployments with 3 modes:
    - docker_in_docker: Full auto-deploy with containers
    - compose_only: Generate docker-compose.yml
    - traefik: Auto-routing with clean URLs
    """
    
    def __init__(self):
        self.enabled = is_docker_desktop()
        
        if self.enabled:
            self.config = get_config()["preview"]
            self.mode = self.config["mode"]
            self.port_range = self.config["port_range"]
            self.base_domain = self.config.get("traefik_base_domain", "localhost")
            
            try:
                self.docker_client = docker.from_env()
                logger.info(f"✅ PreviewDeploymentService initialized ({self.mode} mode)")
            except DockerException as e:
                logger.error(f"Failed to connect to Docker: {e}")
                self.enabled = False
        else:
            logger.info("✅ PreviewDeploymentService (disabled for K8s)")
            self.docker_client = None
    
    async def deploy(
        self,
        task_id: str,
        project_name: str,
        repo_path: str,
        branch: str
    ) -> Dict:
        """
        Deploy preview based on configured mode
        
        Args:
            task_id: Task identifier
            project_name: Project name
            repo_path: Path to Git repository
            branch: Branch to deploy
            
        Returns:
            Deployment result with URLs and container info
        """
        if not self.enabled:
            return {
                "status": "skipped",
                "message": "Preview deployments not available in this environment"
            }
        
        if self.mode == "docker_in_docker":
            return await self._deploy_docker_in_docker(task_id, project_name, repo_path)
        
        elif self.mode == "traefik":
            return await self._deploy_with_traefik(task_id, project_name, repo_path)
        
        else:  # compose_only
            return await self._generate_compose_only(task_id, project_name, repo_path)
    
    async def _deploy_docker_in_docker(
        self,
        task_id: str,
        project_name: str,
        repo_path: str
    ) -> Dict:
        """
        Mode A: Full Docker-in-Docker deployment
        """
        try:
            logger.info(f"🚀 Starting Docker-in-Docker deployment for {project_name}")
            
            # 1. Build images
            backend_image = await self._build_image(
                repo_path,
                "backend",
                f"catalyst-preview/{task_id[:8]}-backend"
            )
            
            frontend_image = await self._build_image(
                repo_path,
                "frontend",
                f"catalyst-preview/{task_id[:8]}-frontend"
            )
            
            # 2. Create network
            network_name = f"preview-{task_id[:8]}"
            network = self.docker_client.networks.create(
                network_name,
                driver="bridge",
                labels={"catalyst.preview": "true", "catalyst.task_id": task_id}
            )
            
            logger.info(f"✅ Created network: {network_name}")
            
            # 3. Start MongoDB
            db_container = self.docker_client.containers.run(
                image="mongo:5.0",
                name=f"preview-{task_id[:8]}-db",
                network=network_name,
                detach=True,
                remove=True,
                labels={"catalyst.preview": "true", "catalyst.task_id": task_id}
            )
            
            logger.info(f"✅ Started database container")
            
            # Wait for DB to be ready
            await asyncio.sleep(3)
            
            # 4. Start backend
            backend_port = await self._get_available_port()
            
            backend_container = self.docker_client.containers.run(
                image=backend_image,
                name=f"preview-{task_id[:8]}-backend",
                network=network_name,
                ports={'8001/tcp': backend_port},
                environment={
                    'MONGO_URL': f'mongodb://preview-{task_id[:8]}-db:27017',
                    'CORS_ORIGINS': '*',
                    'ENVIRONMENT': 'preview'
                },
                detach=True,
                remove=True,
                labels={"catalyst.preview": "true", "catalyst.task_id": task_id}
            )
            
            logger.info(f"✅ Started backend on port {backend_port}")
            
            # 5. Start frontend
            frontend_port = await self._get_available_port()
            
            frontend_container = self.docker_client.containers.run(
                image=frontend_image,
                name=f"preview-{task_id[:8]}-frontend",
                network=network_name,
                ports={'80/tcp': frontend_port},
                environment={
                    'REACT_APP_BACKEND_URL': f'http://localhost:{backend_port}'
                },
                detach=True,
                remove=True,
                labels={
                    "catalyst.preview": "true",
                    "catalyst.task_id": task_id,
                    "traefik.enable": "false"  # Direct port access for now
                }
            )
            
            logger.info(f"✅ Started frontend on port {frontend_port}")
            
            # 6. Health checks
            health_ok = await self._check_container_health(
                backend_container,
                frontend_container,
                backend_port,
                frontend_port
            )
            
            # 7. Save to Postgres
            await self._save_deployment_record(
                task_id=task_id,
                container_ids=[db_container.id, backend_container.id, frontend_container.id],
                network_id=network.id,
                backend_port=backend_port,
                frontend_port=frontend_port,
                project_name=project_name
            )
            
            return {
                "status": "deployed",
                "deployment_mode": "docker_in_docker",
                "preview_url": f"http://{project_name}-{task_id[:8]}.{self.base_domain}",
                "fallback_url": f"http://localhost:{frontend_port}",
                "backend_url": f"http://localhost:{backend_port}/api",
                "container_ids": [db_container.id, backend_container.id, frontend_container.id],
                "network_id": network.id,
                "health": "healthy" if health_ok else "unhealthy",
                "ports": {
                    "backend": backend_port,
                    "frontend": frontend_port
                }
            }
            
        except Exception as e:
            logger.error(f"Docker-in-Docker deployment failed: {e}")
            return {
                "status": "failed",
                "deployment_mode": "docker_in_docker",
                "error": str(e)
            }
    
    async def _deploy_with_traefik(
        self,
        task_id: str,
        project_name: str,
        repo_path: str
    ) -> Dict:
        """
        Mode C: Deploy with Traefik auto-routing
        """
        result = await self._deploy_docker_in_docker(task_id, project_name, repo_path)
        
        if result["status"] == "deployed":
            # Update containers with Traefik labels
            try:
                frontend_container_name = f"preview-{task_id[:8]}-frontend"
                container = self.docker_client.containers.get(frontend_container_name)
                
                # Traefik labels would be added during container creation
                # For now, just update the URL
                result["preview_url"] = f"http://{project_name}-{task_id[:8]}.{self.base_domain}"
                
            except Exception as e:
                logger.error(f"Failed to configure Traefik: {e}")
        
        return result
    
    async def _generate_compose_only(
        self,
        task_id: str,
        project_name: str,
        repo_path: str
    ) -> Dict:
        """
        Mode B: Generate docker-compose.yml only (no deployment)
        """
        try:
            compose_content = self._generate_preview_compose(project_name, repo_path)
            
            # Save to artifacts
            output_dir = Path(f"/app/artifacts/{task_id}/deployment")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            compose_path = output_dir / "docker-compose.preview.yml"
            compose_path.write_text(compose_content)
            
            logger.info(f"✅ Generated {compose_path}")
            
            return {
                "status": "deployed",
                "deployment_mode": "compose_only",
                "compose_file": str(compose_path),
                "instructions": f"""
# To deploy manually:
cd {output_dir.parent.parent}
docker-compose -f deployment/docker-compose.preview.yml up -d

# Access:
Frontend: http://localhost:3000
Backend: http://localhost:8001/api
"""
            }
            
        except Exception as e:
            logger.error(f"Compose generation failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _build_image(
        self,
        repo_path: str,
        component: str,
        tag: str
    ) -> str:
        """
        Build Docker image
        
        Args:
            repo_path: Path to repository
            component: "backend" or "frontend"
            tag: Image tag
            
        Returns:
            Image tag
        """
        try:
            build_path = Path(repo_path) / component
            
            if not build_path.exists():
                raise Exception(f"{component} directory not found in {repo_path}")
            
            # Check for Dockerfile
            dockerfile = build_path / "Dockerfile"
            if not dockerfile.exists():
                # Generate basic Dockerfile
                dockerfile_content = self._generate_dockerfile(component)
                dockerfile.write_text(dockerfile_content)
            
            logger.info(f"🐳 Building {component} image: {tag}")
            
            # Build image
            image, build_logs = self.docker_client.images.build(
                path=str(build_path),
                tag=tag,
                rm=True,
                forcerm=True
            )
            
            logger.info(f"✅ Built {tag}")
            
            return tag
            
        except Exception as e:
            logger.error(f"Failed to build {component} image: {e}")
            raise
    
    def _generate_dockerfile(self, component: str) -> str:
        """Generate basic Dockerfile for component"""
        if component == "backend":
            return """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
"""
        else:  # frontend
            return """FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
"""
    
    def _generate_preview_compose(self, project_name: str, repo_path: str) -> str:
        """Generate docker-compose.yml for manual deployment"""
        return f"""version: '3.8'

services:
  backend:
    build:
      context: {repo_path}/backend
      dockerfile: Dockerfile
    container_name: {project_name}-backend
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://db:27017
      - CORS_ORIGINS=*
    depends_on:
      - db
    networks:
      - preview-network

  frontend:
    build:
      context: {repo_path}/frontend
      dockerfile: Dockerfile
    container_name: {project_name}-frontend
    ports:
      - "3000:80"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8001
    depends_on:
      - backend
    networks:
      - preview-network

  db:
    image: mongo:5.0
    container_name: {project_name}-db
    volumes:
      - db_data:/data/db
    networks:
      - preview-network

volumes:
  db_data:

networks:
  preview-network:
    driver: bridge
"""
    
    async def _get_available_port(self) -> int:
        """Find available port in configured range"""
        import socket
        
        for port in range(self.port_range[0], self.port_range[1]):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('0.0.0.0', port))
                    return port
                except OSError:
                    continue
        
        raise Exception("No available ports in configured range")
    
    async def _check_container_health(
        self,
        backend_container,
        frontend_container,
        backend_port: int,
        frontend_port: int,
        timeout: int = 30
    ) -> bool:
        """
        Check if containers are healthy
        """
        try:
            import httpx
            
            # Wait for containers to start
            await asyncio.sleep(5)
            
            # Check backend
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        f"http://localhost:{backend_port}/api/",
                        timeout=10
                    )
                    backend_ok = response.status_code == 200
                except:
                    backend_ok = False
                
                # Check frontend
                try:
                    response = await client.get(
                        f"http://localhost:{frontend_port}/",
                        timeout=10
                    )
                    frontend_ok = response.status_code == 200
                except:
                    frontend_ok = False
            
            logger.info(f"Health check: Backend={backend_ok}, Frontend={frontend_ok}")
            
            return backend_ok and frontend_ok
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def _save_deployment_record(
        self,
        task_id: str,
        container_ids: List[str],
        network_id: str,
        backend_port: int,
        frontend_port: int,
        project_name: str
    ):
        """Save deployment record to Postgres"""
        try:
            db = get_postgres_service()
            
            preview_url = f"http://{project_name}-{task_id[:8]}.{self.base_domain}"
            fallback_url = f"http://localhost:{frontend_port}"
            backend_url = f"http://localhost:{backend_port}/api"
            
            expires_at = datetime.utcnow() + timedelta(hours=self.config.get("auto_cleanup_hours", 24))
            
            await db.execute("""
                INSERT INTO preview_deployments 
                (id, task_id, deployment_mode, preview_url, fallback_url, backend_url,
                 container_ids, network_id, status, health_status, deployed_at, expires_at, metadata)
                VALUES (uuid_generate_v4(), $1, $2, $3, $4, $5, $6, $7, 'deployed', 'healthy', NOW(), $8, $9)
            """,
                task_id,
                self.mode,
                preview_url,
                fallback_url,
                backend_url,
                container_ids,
                network_id,
                expires_at,
                {"backend_port": backend_port, "frontend_port": frontend_port}
            )
            
            logger.info(f"✅ Saved deployment record for task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to save deployment record: {e}")
    
    async def get_preview(self, task_id: str) -> Optional[Dict]:
        """Get preview deployment details"""
        if not self.enabled:
            return None
        
        try:
            db = get_postgres_service()
            
            result = await db.fetchrow("""
                SELECT * FROM preview_deployments WHERE task_id = $1
            """, task_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get preview: {e}")
            return None
    
    async def list_active_previews(self) -> List[Dict]:
        """List all active preview deployments"""
        if not self.enabled:
            return []
        
        try:
            db = get_postgres_service()
            
            results = await db.fetch("""
                SELECT * FROM preview_deployments 
                WHERE status = 'deployed' AND expires_at > NOW()
                ORDER BY deployed_at DESC
            """)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to list previews: {e}")
            return []
    
    async def cleanup_preview(self, task_id: str) -> bool:
        """
        Cleanup preview deployment
        Stops and removes containers, network
        """
        if not self.enabled:
            return False
        
        try:
            # Get deployment record
            preview = await self.get_preview(task_id)
            
            if not preview:
                logger.warning(f"Preview not found for task {task_id}")
                return False
            
            # Stop and remove containers
            for container_id in preview.get("container_ids", []):
                try:
                    container = self.docker_client.containers.get(container_id)
                    container.stop(timeout=10)
                    container.remove()
                    logger.info(f"✅ Removed container {container_id[:12]}")
                except Exception as e:
                    logger.error(f"Failed to remove container {container_id}: {e}")
            
            # Remove network
            network_id = preview.get("network_id")
            if network_id:
                try:
                    network = self.docker_client.networks.get(network_id)
                    network.remove()
                    logger.info(f"✅ Removed network {network_id[:12]}")
                except Exception as e:
                    logger.error(f"Failed to remove network: {e}")
            
            # Update database
            db = get_postgres_service()
            await db.execute("""
                UPDATE preview_deployments 
                SET status = 'cleaned_up', health_status = 'stopped'
                WHERE task_id = $1
            """, task_id)
            
            logger.info(f"✅ Cleaned up preview for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup preview: {e}")
            return False
    
    async def cleanup_expired_previews(self) -> int:
        """
        Cleanup all expired previews
        Returns count of cleaned up deployments
        """
        if not self.enabled:
            return 0
        
        try:
            db = get_postgres_service()
            
            # Get expired previews
            expired = await db.fetch("""
                SELECT task_id FROM preview_deployments
                WHERE status = 'deployed' AND expires_at < NOW()
            """)
            
            count = 0
            for record in expired:
                if await self.cleanup_preview(record["task_id"]):
                    count += 1
            
            logger.info(f"✅ Cleaned up {count} expired previews")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired previews: {e}")
            return 0


# Singleton instance
_preview_service = None


def get_preview_service() -> PreviewDeploymentService:
    """Get or create PreviewDeploymentService singleton"""
    global _preview_service
    if _preview_service is None:
        _preview_service = PreviewDeploymentService()
    return _preview_service
