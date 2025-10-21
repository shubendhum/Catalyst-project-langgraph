"""
Rapid MVP Orchestrator
Fast-track workflow: User Requirements → Rapid MVP Developer → Deployed
Skips Planner and Architect for speed
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timezone

from agents.rapid_mvp_coder import get_rapid_mvp_coder
from agents.deployer_agent import get_deployer_agent
from services.file_system_service import get_file_system_service
from services.optimized_llm_client import get_optimized_llm_client

logger = logging.getLogger(__name__)


class RapidMVPOrchestrator:
    """
    Streamlined orchestrator for rapid MVP development
    Workflow: Requirements → MVP Developer → Deploy (optional)
    """
    
    def __init__(self, db, manager, config: Optional[Dict] = None):
        self.db = db
        self.manager = manager
        self.config = config or {}
        
        # Initialize LLM client
        self.optimized_llm_client = get_optimized_llm_client(
            db=db,
            default_model=self.config.get("model", "claude-3-7-sonnet-20250219")
        )
        
        # Initialize services
        self.file_service = get_file_system_service()
        
        # Initialize agents (only MVP Developer and Deployer)
        self.mvp_developer = get_rapid_mvp_coder(
            self.optimized_llm_client, db, manager, self.file_service
        )
        self.deployer = get_deployer_agent(
            self.optimized_llm_client, db, manager, self.file_service
        )
    
    async def execute_task(
        self,
        task_id: str,
        project_id: str,
        user_requirements: str
    ) -> Dict:
        """
        Execute rapid MVP workflow
        """
        logger.info(f"🚀 Starting Rapid MVP workflow for task {task_id}")
        
        try:
            await self._update_task_status(task_id, "mvp_development")
            await self._log(task_id, "⚡ Starting rapid MVP development...")
            await self._log(task_id, "🎯 Focusing on max value feature for quick 'aha moment'")
            
            # Get project info
            project = await self.db.projects.find_one({"id": project_id})
            project_name = project.get("name", f"MVP-{project_id[:8]}") if project else f"MVP-{project_id[:8]}"
            
            # Create minimal architecture (just what MVP needs)
            architecture = {
                "metadata": {
                    "user_requirements": user_requirements,
                    "project_name": project_name
                },
                "features": [
                    {"name": "Core Functionality", "priority": "High", "description": user_requirements}
                ],
                "data_models": [],  # MVP developer will infer
                "api_design": {"endpoints": []}
            }
            
            # STEP 1: MVP Development (replaces Planner + Architect + Coder)
            await self._log(task_id, "💻 Rapid MVP Developer: Generating core feature...")
            
            code_result = await self.mvp_developer.generate_code(
                architecture=architecture,
                project_name=project_name,
                task_id=task_id
            )
            
            if code_result["status"] != "success":
                raise Exception(f"MVP generation failed: {code_result.get('error')}")
            
            await self._log(task_id, f"✅ MVP Generated: {code_result['files_generated']} core files")
            await self._log(task_id, f"📁 Project: {code_result['project_path']}")
            
            # Save to database
            await self.db.tasks.update_one(
                {"id": task_id},
                {
                    "$set": {
                        "architecture": architecture,
                        "code_result": code_result,
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "project_path": code_result["project_path"],
                        "cost_stats": self.optimized_llm_client.get_stats(),
                        "workflow": "rapid_mvp"
                    }
                }
            )
            
            # Log cost
            cost_stats = self.optimized_llm_client.get_stats()
            await self._log(
                task_id,
                f"💰 MVP Cost: ${cost_stats['total_cost']:.4f} "
                f"({cost_stats['calls_made']} LLM calls)"
            )
            
            await self._update_task_status(task_id, "completed")
            await self._log(task_id, "🎉 Rapid MVP completed! Test it out!")
            
            return {
                "status": "success",
                "workflow": "rapid_mvp",
                "task_id": task_id,
                "project_name": project_name,
                "project_path": code_result["project_path"],
                "files_generated": code_result["files_generated"],
                "cost_stats": cost_stats,
                "code_result": code_result
            }
            
        except Exception as e:
            logger.error(f"Error in Rapid MVP workflow: {str(e)}")
            await self._log(task_id, f"❌ Error: {str(e)}")
            await self._update_task_status(task_id, "failed")
            
            await self.db.tasks.update_one(
                {"id": task_id},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "failed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            return {
                "status": "failed",
                "task_id": task_id,
                "error": str(e)
            }
    
    async def _update_task_status(self, task_id: str, status: str):
        """Update task status in database"""
        await self.db.tasks.update_one(
            {"id": task_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
    
    async def _log(self, task_id: str, message: str):
        """Log activity"""
        log_doc = {
            "task_id": task_id,
            "agent_name": "RapidMVP",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(task_id, log_doc)


def get_rapid_mvp_orchestrator(db, manager, config: Optional[Dict] = None) -> RapidMVPOrchestrator:
    """Factory function"""
    return RapidMVPOrchestrator(db, manager, config)
