"""
Dual-Mode Orchestrator
Switches between Sequential and Event-Driven execution based on environment
"""
import logging
from typing import Dict, Optional
from uuid import uuid4, UUID
from datetime import datetime

from config.environment import get_orchestration_mode, is_docker_desktop
from orchestrator.phase2_orchestrator import get_phase2_orchestrator
from events import get_event_publisher, AgentEvent
from services.postgres_service import create_task_record, update_task_status

logger = logging.getLogger(__name__)


class DualModeOrchestrator:
    """
    Orchestrator that adapts to environment:
    - Sequential mode for K8s (current implementation)
    - Event-driven mode for Docker Desktop (new implementation)
    """
    
    def __init__(self, db, manager, config: Optional[Dict] = None):
        self.db = db
        self.manager = manager
        self.config = config or {}
        self.mode = get_orchestration_mode()
        
        logger.info(f"🎯 DualModeOrchestrator initialized in {self.mode} mode")
        
        # Initialize executors
        if self.mode == "event_driven":
            self.event_publisher = get_event_publisher()
            logger.info("✅ Event-driven mode: using RabbitMQ")
        else:
            # Sequential mode - use existing Phase2 orchestrator
            self.sequential_executor = get_phase2_orchestrator(db, manager, config)
            logger.info("✅ Sequential mode: using direct agent calls")
    
    async def execute_task(
        self,
        task_id: str,
        project_id: str,
        user_requirements: str
    ) -> Dict:
        """
        Execute task using appropriate mode
        
        Args:
            task_id: Task identifier
            project_id: Project identifier
            user_requirements: User's requirements
            
        Returns:
            Execution result dictionary
        """
        
        if self.mode == "event_driven":
            return await self._execute_event_driven(task_id, project_id, user_requirements)
        else:
            return await self._execute_sequential(task_id, project_id, user_requirements)
    
    async def _execute_sequential(
        self,
        task_id: str,
        project_id: str,
        user_requirements: str
    ) -> Dict:
        """
        Execute in sequential mode (K8s environment)
        Uses existing Phase2Orchestrator
        """
        logger.info(f"▶️ Executing task {task_id} in SEQUENTIAL mode")
        
        return await self.sequential_executor.execute_task(
            task_id,
            project_id,
            user_requirements
        )
    
    async def _execute_event_driven(
        self,
        task_id: str,
        project_id: str,
        user_requirements: str
    ) -> Dict:
        """
        Execute in event-driven mode (Docker Desktop)
        Publishes initial event to trigger Planner agent
        """
        logger.info(f"▶️ Executing task {task_id} in EVENT-DRIVEN mode")
        
        trace_id = uuid4()
        
        # Create task record in Postgres
        await create_task_record(
            task_id=task_id,
            project_id=project_id,
            trace_id=str(trace_id),
            user_prompt=user_requirements
        )
        
        # Create initial event to trigger Planner
        event = AgentEvent(
            trace_id=trace_id,
            task_id=UUID(task_id),
            actor="orchestrator",
            event_type="task.initiated",
            repo=f"catalyst-generated/{project_id}",
            branch="main",
            commit="",
            timestamp=datetime.utcnow(),
            payload={
                "project_id": project_id,
                "user_requirements": user_requirements,
                "next_agent": "planner"
            },
            metadata={
                "orchestration_mode": "event_driven",
                "initiated_by": "chat_interface"
            }
        )
        
        # Publish event to RabbitMQ
        success = await self.event_publisher.publish(event)
        
        if success:
            logger.info(
                f"✅ Task {task_id} initiated via event system "
                f"(trace: {trace_id})"
            )
            
            # Log to MongoDB for WebSocket updates
            await self._log(task_id, "🚀 Task initiated in event-driven mode")
            await self._log(task_id, "📡 Event published to Planner agent")
            
            return {
                "status": "initiated",
                "mode": "event_driven",
                "task_id": task_id,
                "trace_id": str(trace_id),
                "message": "Task initiated. Agents will process asynchronously."
            }
        else:
            logger.error(f"Failed to publish initial event for task {task_id}")
            
            # Fallback to sequential
            logger.warning("⚠️ Falling back to sequential mode")
            return await self._execute_sequential(task_id, project_id, user_requirements)
    
    async def _log(self, task_id: str, message: str):
        """Log orchestrator activity (for WebSocket updates)"""
        log_doc = {
            "task_id": task_id,
            "agent_name": "Orchestrator",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(task_id, log_doc)


def get_dual_mode_orchestrator(db, manager, config: Optional[Dict] = None) -> DualModeOrchestrator:
    """Factory function to create DualModeOrchestrator"""
    return DualModeOrchestrator(db, manager, config)
