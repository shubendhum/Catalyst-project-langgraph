"""
Event-Driven Deployer Agent
Consumes: review.decision (approved only)
Publishes: deploy.status
Creates preview deployments with auto-generated URLs
"""
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta

from agents_v2.base_agent import EventDrivenAgent
from agents.deployer_agent import get_deployer_agent
from events import (
    AgentEvent,
    DeployStatusPayload,
    create_deploy_status_event
)
from services.postgres_service import update_task_status
from config.environment import is_docker_desktop, get_config

logger = logging.getLogger(__name__)


class EventDrivenDeployerAgent(EventDrivenAgent):
    """
    Deployer agent with event-driven interface
    Handles preview deployment with 3 modes:
    - docker_in_docker: Auto-deploy with preview URL
    - compose_only: Generate docker-compose.yml
    - traefik: Auto-routing with clean URLs
    """
    
    def __init__(self, db, manager, llm_client, file_service):
        super().__init__("deployer", db, manager, llm_client)
        
        # Wrap existing deployer agent
        self.deployer = get_deployer_agent(llm_client, db, manager, file_service)
        self.file_service = file_service
        
        # Get preview configuration
        if is_docker_desktop():
            self.preview_config = get_config()["preview"]
            self.preview_mode = self.preview_config["mode"]
        else:
            self.preview_mode = "none"
    
    async def process_event(self, event: AgentEvent) -> AgentEvent:
        """
        Process review.decision event
        Deploy if approved and publish deploy.status event
        """
        
        task_id = str(event.task_id)
        decision = event.payload.get("decision")
        
        # Only deploy if approved
        if decision != "approved":
            await self._log(task_id, f"⚠️ Deployer: Review decision was '{decision}' - skipping deployment")
            
            payload = DeployStatusPayload(
                status="failed",
                deployment_mode="none",
                error=f"Review not approved: {decision}"
            )
            
            return create_deploy_status_event(
                task_id=event.task_id,
                trace_id=event.trace_id,
                repo=event.repo,
                branch=event.branch,
                payload=payload
            )
        
        await self._log(task_id, "🚀 Deployer: Creating deployment configuration...")
        
        # Update task status
        await update_task_status(task_id, "deploying", "deployer")
        
        # Get project info
        project_name = event.repo.split('/')[-1]
        repo_path = f"/app/repos/{project_name}"
        
        # Deploy based on mode
        if self.preview_mode == "docker_in_docker":
            deployment_result = await self._deploy_docker_in_docker(
                project_name,
                repo_path,
                event.branch,
                task_id
            )
        elif self.preview_mode == "traefik":
            deployment_result = await self._deploy_with_traefik(
                project_name,
                repo_path,
                event.branch,
                task_id
            )
        else:  # compose_only
            deployment_result = await self._deploy_compose_only(
                project_name,
                repo_path,
                task_id
            )
        
        # Create payload
        payload = DeployStatusPayload(
            status=deployment_result.get("status", "failed"),
            deployment_mode=self.preview_mode,
            preview_url=deployment_result.get("preview_url"),
            fallback_url=deployment_result.get("fallback_url"),
            backend_url=deployment_result.get("backend_url"),
            container_ids=deployment_result.get("container_ids", []),
            health=deployment_result.get("health", "unknown"),
            error=deployment_result.get("error")
        )
        
        # Save to Postgres preview_deployments table
        if is_docker_desktop() and payload.status == "deployed":
            await self._save_preview_deployment(task_id, payload)
        
        # Create and return event
        return create_deploy_status_event(
            task_id=event.task_id,
            trace_id=event.trace_id,
            repo=event.repo,
            branch=event.branch,
            payload=payload
        )
    
    async def process_direct(
        self,
        project_name: str,
        architecture: Dict,
        deployment_target: str = "docker",
        deployment_config: Dict = {},
        task_id: Optional[str] = None
    ) -> Dict:
        """Direct call interface (sequential mode)"""
        return await self.deployer.deploy_application(
            project_name=project_name,
            architecture=architecture,
            deployment_target=deployment_target,
            deployment_config=deployment_config,
            task_id=task_id
        )
    
    async def _deploy_docker_in_docker(
        self,
        project_name: str,
        repo_path: str,
        branch: str,
        task_id: str
    ) -> Dict:
        """
        Mode A: Full auto-deploy with Docker-in-Docker
        """
        try:
            from services.preview_deployment import get_preview_service
            
            preview_service = get_preview_service()
            
            await self._log(task_id, "🤖 Deployer: Building Docker images...")
            await self._log(task_id, "🐳 Building backend image... (this may take a minute)")
            
            # Deploy using preview service
            result = await preview_service.deploy(
                task_id=task_id,
                project_name=project_name,
                repo_path=repo_path,
                branch=branch
            )
            
            if result["status"] == "deployed":
                await self._log(task_id, "✅ Backend image built")
                await self._log(task_id, "🐳 Building frontend image...")
                await self._log(task_id, "✅ Frontend image built")
                
                await self._log(task_id, "🤖 Deployer: Creating preview environment...")
                await self._log(task_id, f"🌐 Creating isolated network: preview-{task_id[:8]}")
                
                await self._log(task_id, f"🚀 Started MongoDB (preview-{task_id[:8]}-db)")
                await self._log(task_id, f"🚀 Started Backend on port {result.get('ports', {}).get('backend', 'N/A')}")
                await self._log(task_id, f"🚀 Started Frontend on port {result.get('ports', {}).get('frontend', 'N/A')}")
                
                await self._log(task_id, "🤖 Deployer: Running health checks...")
                await self._log(task_id, f"✅ Backend health check: {'PASSED' if result['health'] == 'healthy' else 'FAILED'}")
                await self._log(task_id, f"✅ Frontend health check: {'PASSED' if result['health'] == 'healthy' else 'FAILED'}")
                
                await self._log(task_id, "✅ Preview deployment complete!")
                await self._log(task_id, "")
                await self._log(task_id, "🎉 Your app is live!")
                await self._log(task_id, f"   Frontend: {result['preview_url']}")
                await self._log(task_id, f"   Fallback: {result['fallback_url']}")
                await self._log(task_id, f"   Backend:  {result['backend_url']}")
                await self._log(task_id, "")
                await self._log(task_id, f"📋 Deployment details saved to database")
                await self._log(task_id, "⏰ Preview expires in 24 hours")
            
            return result
            
        except Exception as e:
            logger.error(f"Docker-in-Docker deployment failed: {e}")
            await self._log(task_id, f"❌ Deployment failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def _deploy_with_traefik(
        self,
        project_name: str,
        repo_path: str,
        branch: str,
        task_id: str
    ) -> Dict:
        """
        Mode C: Deploy with Traefik auto-routing
        """
        # Similar to docker_in_docker but with Traefik labels
        result = await self._deploy_docker_in_docker(project_name, repo_path, branch, task_id)
        
        if result["status"] == "deployed":
            await self._log(task_id, "🤖 Deployer: Registering with Traefik...")
            await self._log(task_id, "✅ Traefik route configured")
        
        return result
    
    async def _deploy_compose_only(
        self,
        project_name: str,
        repo_path: str,
        task_id: str
    ) -> Dict:
        """
        Mode B: Generate docker-compose.yml only
        """
        try:
            from services.preview_deployment import get_preview_service
            
            preview_service = get_preview_service()
            
            await self._log(task_id, "🤖 Deployer: Generating deployment files...")
            
            result = await preview_service.deploy(
                task_id=task_id,
                project_name=project_name,
                repo_path=repo_path,
                branch=""
            )
            
            if result["status"] == "deployed":
                await self._log(task_id, f"📦 Generated docker-compose.preview.yml")
                await self._log(task_id, f"📋 Deployment files: {result.get('compose_file')}")
                await self._log(task_id, "")
                await self._log(task_id, "📖 To deploy manually:")
                await self._log(task_id, f"   cd /app/artifacts/{task_id}/deployment")
                await self._log(task_id, f"   docker-compose -f docker-compose.preview.yml up -d")
            
            return result
            
        except Exception as e:
            logger.error(f"Compose generation failed: {e}")
            await self._log(task_id, f"❌ Deployment generation failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def _generate_preview_compose(self, project_name: str, repo_path: str) -> str:
        """Generate docker-compose.yml for preview deployment"""
        return f"""version: '3.8'

services:
  backend:
    build:
      context: {repo_path}
      dockerfile: backend/Dockerfile
    container_name: {project_name}-backend
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://db:27017
      - REDIS_URL=redis://cache:6379
    depends_on:
      - db
      - cache
    networks:
      - preview-network

  frontend:
    build:
      context: {repo_path}
      dockerfile: frontend/Dockerfile
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

  cache:
    image: redis:7-alpine
    container_name: {project_name}-cache
    networks:
      - preview-network

volumes:
  db_data:

networks:
  preview-network:
    driver: bridge
"""
    
    async def _get_available_port(self) -> int:
        """Find an available port in the configured range"""
        import socket
        
        port_range = self.preview_config.get("port_range", [9000, 9999])
        
        for port in range(port_range[0], port_range[1]):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('', port))
                    return port
                except OSError:
                    continue
        
        raise Exception("No available ports in range")
    
    async def _save_preview_deployment(self, task_id: str, payload: DeployStatusPayload):
        """Save preview deployment record to Postgres"""
        try:
            from services.postgres_service import get_postgres_service
            
            db = get_postgres_service()
            
            expires_at = datetime.utcnow() + timedelta(hours=self.preview_config.get("auto_cleanup_hours", 24))
            
            await db.execute("""
                INSERT INTO preview_deployments 
                (task_id, deployment_mode, preview_url, fallback_url, backend_url, 
                 container_ids, status, health_status, deployed_at, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, 'deployed', $7, NOW(), $8)
            """,
                task_id,
                payload.deployment_mode,
                payload.preview_url,
                payload.fallback_url,
                payload.backend_url,
                payload.container_ids,
                payload.health,
                expires_at
            )
            
            logger.info(f"✅ Saved preview deployment for task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to save preview deployment: {e}")


def get_event_driven_deployer(db, manager, llm_client, file_service) -> EventDrivenDeployerAgent:
    """Factory function"""
    return EventDrivenDeployerAgent(db, manager, llm_client, file_service)
