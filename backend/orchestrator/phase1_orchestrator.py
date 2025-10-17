"""
Phase 1 Orchestrator - Planner → Architect → Coder Flow
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
import uuid

from agents.planner_agent import get_planner_agent
from agents.architect_agent import get_architect_agent
from agents.coder import get_coder_agent
from services.file_system_service import get_file_system_service
from llm_client import get_llm_client

logger = logging.getLogger(__name__)


class Phase1Orchestrator:
    """
    Orchestrator for Phase 1: Planner → Architect → Coder flow
    Generates complete full-stack applications from user requirements
    """
    
    def __init__(self, db, manager, config: Optional[Dict] = None):
        self.db = db
        self.manager = manager
        self.config = config or {}
        
        # Initialize LLM client
        self.llm_client = get_llm_client(self.config)
        
        # Initialize services
        self.file_service = get_file_system_service()
        
        # Initialize agents
        self.planner = get_planner_agent(self.llm_client)
        self.architect = get_architect_agent(self.llm_client)
        self.coder = get_coder_agent(self.llm_client, db, manager, self.file_service)
    
    async def execute_task(
        self,
        task_id: str,
        project_id: str,
        user_requirements: str
    ) -> Dict:
        """
        Execute complete Phase 1 flow: Planner → Architect → Coder
        
        Args:
            task_id: Task identifier for tracking
            project_id: Project identifier
            user_requirements: User's description of what to build
            
        Returns:
            Dictionary with results and status
        """
        logger.info(f"Starting Phase 1 execution for task {task_id}")
        
        try:
            # Update task status
            await self._update_task_status(task_id, "planning")
            await self._log(task_id, "🚀 Starting application development process...")
            
            # Get project info
            project = await self.db.projects.find_one({"id": project_id})
            project_name = project.get("name", f"Project_{project_id[:8]}") if project else f"Project_{project_id[:8]}"
            
            # STEP 1: Planner - Create development plan
            await self._log(task_id, "📋 Planner Agent: Analyzing requirements and creating plan...")
            plan = await self.planner.create_plan(
                user_requirements=user_requirements,
                project_name=project_name
            )
            await self._log(task_id, f"✅ Plan created with {len(plan.get('features', []))} features")
            
            # Save plan to database
            await self.db.tasks.update_one(
                {"id": task_id},
                {"$set": {"plan": plan, "status": "architecting"}}
            )
            
            # STEP 2: Architect - Design technical architecture
            await self._update_task_status(task_id, "architecting")
            await self._log(task_id, "🏗️  Architect Agent: Designing technical architecture...")
            
            architecture = await self.architect.design_architecture(
                plan=plan,
                project_name=project_name
            )
            await self._log(task_id, f"✅ Architecture designed with {len(architecture.get('data_models', []))} models")
            
            # Save architecture to database
            await self.db.tasks.update_one(
                {"id": task_id},
                {"$set": {"architecture": architecture, "status": "coding"}}
            )
            
            # STEP 3: Coder - Generate complete code
            await self._update_task_status(task_id, "coding")
            await self._log(task_id, "💻 Coder Agent: Generating complete application code...")
            
            code_result = await self.coder.generate_code(
                architecture=architecture,
                project_name=project_name,
                task_id=task_id
            )
            
            if code_result["status"] == "success":
                await self._log(task_id, f"✅ Code generation complete! Generated {code_result['files_generated']} files")
                await self._log(task_id, f"📁 Project saved at: {code_result['project_path']}")
                
                # Update task with completion
                await self.db.tasks.update_one(
                    {"id": task_id},
                    {
                        "$set": {
                            "code_result": code_result,
                            "status": "completed",
                            "completed_at": datetime.now(timezone.utc).isoformat(),
                            "project_path": code_result["project_path"]
                        }
                    }
                )
                
                await self._update_task_status(task_id, "completed")
                await self._log(task_id, "🎉 Application development completed successfully!")
                
                return {
                    "status": "success",
                    "task_id": task_id,
                    "project_name": project_name,
                    "project_path": code_result["project_path"],
                    "files_generated": code_result["files_generated"],
                    "plan": plan,
                    "architecture": architecture,
                    "code_result": code_result
                }
            else:
                raise Exception(f"Code generation failed: {code_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in Phase 1 execution: {str(e)}")
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
        """Log orchestrator activity"""
        log_doc = {
            "task_id": task_id,
            "agent_name": "Orchestrator",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(task_id, log_doc)


def get_phase1_orchestrator(db, manager, config: Optional[Dict] = None) -> Phase1Orchestrator:
    """Get Phase1Orchestrator instance"""
    return Phase1Orchestrator(db, manager, config)
