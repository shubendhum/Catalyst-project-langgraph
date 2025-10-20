"""
Event-Driven Agent Base Class
Provides common functionality for agents in event-driven mode
"""
import logging
import asyncio
from typing import Optional, Callable
from abc import ABC, abstractmethod
from uuid import UUID

from events import AgentEvent, EventPublisher, EventConsumer, get_event_publisher
from config.environment import should_use_events

logger = logging.getLogger(__name__)


class EventDrivenAgent(ABC):
    """
    Base class for event-driven agents
    Handles event consumption, processing, and publishing
    """
    
    def __init__(
        self,
        agent_name: str,
        db,
        manager,
        llm_client
    ):
        self.agent_name = agent_name
        self.db = db
        self.manager = manager
        self.llm_client = llm_client
        self.event_enabled = should_use_events()
        
        if self.event_enabled:
            self.publisher = get_event_publisher()
            self.consumer = None  # Will be created when start_listening() is called
            logger.info(f"✅ {agent_name} initialized in EVENT-DRIVEN mode")
        else:
            self.publisher = None
            self.consumer = None
            logger.info(f"✅ {agent_name} initialized in SEQUENTIAL mode")
    
    @abstractmethod
    async def process_event(self, event: AgentEvent) -> AgentEvent:
        """
        Process incoming event and return result event
        Must be implemented by each agent
        
        Args:
            event: Incoming event from previous agent
            
        Returns:
            AgentEvent to publish to next agent
        """
        pass
    
    @abstractmethod
    async def process_direct(self, **kwargs) -> dict:
        """
        Process direct call (sequential mode)
        Must be implemented by each agent
        
        Args:
            kwargs: Agent-specific arguments
            
        Returns:
            dict with processing results
        """
        pass
    
    async def handle_event(self, event: AgentEvent):
        """
        Handle incoming event (wrapper with error handling)
        """
        try:
            logger.info(
                f"🎯 {self.agent_name} processing event: {event.event_type} "
                f"(trace: {event.trace_id}, task: {event.task_id})"
            )
            
            # Log to database for WebSocket updates
            await self._log(str(event.task_id), f"🤖 {self.agent_name}: Starting processing...")
            
            # Process event (agent-specific logic)
            result_event = await self.process_event(event)
            
            # Publish result event
            if result_event:
                await self.publisher.publish(result_event)
                logger.info(f"✅ {self.agent_name} completed. Published: {result_event.event_type}")
            
            await self._log(str(event.task_id), f"✅ {self.agent_name}: Processing complete")
            
        except Exception as e:
            logger.error(f"❌ {self.agent_name} failed: {e}")
            await self._log(str(event.task_id), f"❌ {self.agent_name}: Error - {str(e)}")
            
            # Publish failure event
            await self._publish_failure_event(event, str(e))
    
    async def _publish_failure_event(self, original_event: AgentEvent, error: str):
        """Publish failure event"""
        failure_event = AgentEvent(
            trace_id=original_event.trace_id,
            task_id=original_event.task_id,
            actor=self.agent_name,
            event_type=f"{self.agent_name}.failed",
            repo=original_event.repo,
            branch=original_event.branch,
            commit=original_event.commit,
            payload={
                "error": error,
                "original_event_type": original_event.event_type
            }
        )
        
        await self.publisher.publish(failure_event)
    
    async def _log(self, task_id: str, message: str):
        """Log to database for WebSocket updates"""
        log_doc = {
            "task_id": task_id,
            "agent_name": self.agent_name,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        try:
            await self.db.agent_logs.insert_one(log_doc)
            await self.manager.send_log(task_id, log_doc)
        except Exception as e:
            logger.error(f"Failed to log: {e}")
    
    def start_listening(self):
        """
        Start listening to event queue (event-driven mode only)
        This should be called in a background task
        """
        if not self.event_enabled:
            logger.info(f"{self.agent_name}: Not starting event listener (sequential mode)")
            return
        
        from events.consumer import create_consumer_for_agent
        
        self.consumer = create_consumer_for_agent(self.agent_name)
        
        logger.info(f"🎧 {self.agent_name} starting event listener...")
        
        # Start consuming in background
        def consume_wrapper(event: AgentEvent):
            """Sync wrapper for async handle_event"""
            asyncio.create_task(self.handle_event(event))
        
        try:
            self.consumer.start_consuming(consume_wrapper)
        except KeyboardInterrupt:
            logger.info(f"🛑 {self.agent_name} stopped listening")
            self.consumer.close()
    
    def stop_listening(self):
        """Stop listening to events"""
        if self.consumer:
            self.consumer.stop_consuming()
            self.consumer.close()
