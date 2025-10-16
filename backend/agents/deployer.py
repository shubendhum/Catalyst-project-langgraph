import os
from datetime import datetime, timezone
import uuid
import hashlib

class DeployerAgent:
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager

    async def deploy(self, task_id: str, code: str, project_id: str):
        await self._log(task_id, "Deployer", "🚀 Starting deployment process...")
        
        try:
            # Simulate deployment
            commit_sha = hashlib.sha256(code.encode()).hexdigest()[:12]
            deployment_url = f"https://catalyst-{project_id[:8]}.deploy.catalyst.ai"
            
            await self._log(task_id, "Deployer", "📦 Building application...")
            await self._log(task_id, "Deployer", "☁️ Deploying to cloud...")
            
            # Create deployment record
            deployment_doc = {
                "id": str(uuid.uuid4()),
                "task_id": task_id,
                "url": deployment_url,
                "commit_sha": commit_sha,
                "cost": 0.25,
                "report": f"Deployment successful\nURL: {deployment_url}\nCommit: {commit_sha}\nStatus: Live",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await self.db.deployments.insert_one(deployment_doc)
            
            await self._log(task_id, "Deployer", f"✅ Deployment successful: {deployment_url}")
            
            return {
                "deployment_url": deployment_url,
                "commit_sha": commit_sha,
                "status": "success"
            }
        except Exception as e:
            await self._log(task_id, "Deployer", f"❌ Deployment failed: {str(e)}")
            return {"deployment_url": "", "commit_sha": "", "status": "failed", "error": str(e)}

    async def _log(self, task_id: str, agent_name: str, message: str):
        log_doc = {
            "task_id": task_id,
            "agent_name": agent_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(task_id, log_doc)