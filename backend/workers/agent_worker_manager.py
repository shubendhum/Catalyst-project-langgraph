"""
Agent Worker Manager
Starts all agent event listeners in background
Only active in event-driven mode (Docker Desktop)
"""
import logging
import asyncio
from typing import List
from config.environment import should_use_events, is_docker_desktop

logger = logging.getLogger(__name__)


class AgentWorkerManager:
    """
    Manages agent worker processes that listen to event queues
    """
    
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager
        self.workers: List[asyncio.Task] = []
        self.enabled = should_use_events()
    
    async def start_all_workers(self):
        """
        Start all agent workers in background
        Each worker listens to its event queue
        """
        if not self.enabled:
            logger.info("⏭️ Agent workers not started (sequential mode)")
            return
        
        logger.info("🚀 Starting agent worker processes...")
        
        # Import agents
        from agents_v2.planner_agent_v2 import get_event_driven_planner
        from agents_v2.architect_agent_v2 import get_event_driven_architect
        from agents_v2.coder_agent_v2 import get_event_driven_coder
        from agents_v2.tester_agent_v2 import get_event_driven_tester
        from agents_v2.reviewer_agent_v2 import get_event_driven_reviewer
        from agents_v2.deployer_agent_v2 import get_event_driven_deployer
        from services.file_system_service import get_file_system_service
        from services.optimized_llm_client import get_optimized_llm_client
        
        # Get LLM client
        llm_client = get_optimized_llm_client(db=self.db)
        file_service = get_file_system_service()
        
        # Create agents
        agents = [
            get_event_driven_planner(self.db, self.manager, llm_client),
            get_event_driven_architect(self.db, self.manager, llm_client),
            get_event_driven_coder(self.db, self.manager, llm_client, file_service),
            get_event_driven_tester(self.db, self.manager, llm_client, file_service),
            get_event_driven_reviewer(self.db, self.manager, llm_client, file_service),
            get_event_driven_deployer(self.db, self.manager, llm_client, file_service)
        ]
        
        # Start each agent in its own task
        for agent in agents:
            worker_task = asyncio.create_task(
                self._run_agent_worker(agent)
            )
            self.workers.append(worker_task)
            logger.info(f"✅ Started {agent.agent_name} worker")
        
        logger.info(f"🎧 {len(self.workers)} agent workers listening to event queues")
    
    async def _run_agent_worker(self, agent):
        """
        Run agent worker (blocking - listens to queue)
        """
        try:
            # This blocks and listens to the queue
            agent.start_listening()
        except Exception as e:
            logger.error(f"Agent worker {agent.agent_name} failed: {e}")
    
    async def stop_all_workers(self):
        """Stop all agent workers"""
        if not self.workers:
            return
        
        logger.info("🛑 Stopping agent workers...")
        
        for task in self.workers:
            task.cancel()
        
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        self.workers.clear()
        logger.info("✅ All agent workers stopped")


# Global instance
_worker_manager = None


def get_worker_manager(db, manager) -> AgentWorkerManager:
    """Get or create AgentWorkerManager singleton"""
    global _worker_manager
    if _worker_manager is None:
        _worker_manager = AgentWorkerManager(db, manager)
    return _worker_manager
