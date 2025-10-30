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
            try:
                await self._log(str(event.task_id), f"🤖 {self.agent_name}: Starting processing...")
            except Exception as log_error:
                logger.error(f"Error in _log (start): {log_error}")
            
            # Process event (agent-specific logic)
            try:
                result_event = await self.process_event(event)
            except Exception as process_error:
                logger.error(f"Error in process_event: {process_error}")
                raise
            
            # Publish result event
            if result_event:
                try:
                    await self.publisher.publish(result_event)
                    logger.info(f"✅ {self.agent_name} completed. Published: {result_event.event_type}")
                except Exception as publish_error:
                    logger.error(f"Error in publisher.publish: {publish_error}")
                    raise
            
            try:
                await self._log(str(event.task_id), f"✅ {self.agent_name}: Processing complete")
            except Exception as log_error:
                logger.error(f"Error in _log (complete): {log_error}")
            
        except Exception as e:
            logger.error(f"❌ {self.agent_name} failed: {e}", exc_info=True)
            try:
                await self._log(str(event.task_id), f"❌ {self.agent_name}: Error - {str(e)}")
            except Exception as log_error:
                logger.error(f"Error in _log (error): {log_error}")
            
            # Publish failure event
            try:
                await self._publish_failure_event(event, str(e))
            except Exception as failure_error:
                logger.error(f"Error publishing failure event: {failure_error}")
    
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
        """
        Log to database for WebSocket updates
        NOTE: This method may be called from worker threads with isolated event loops.
        Motor (MongoDB async driver) is tied to the main event loop, so we skip logging
        from worker threads to avoid "attached to a different loop" errors.
        """
        # Skip logging from worker threads - Motor doesn't support cross-loop operations
        # TODO: Implement thread-safe logging mechanism (queue-based or synchronous)
        logger.info(f"[{self.agent_name}] {message}")
        return
    
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
        
        # Consumer handles async callbacks directly (creates event loop in worker thread)
        try:
            self.consumer.start_consuming(self.handle_event)
        except KeyboardInterrupt:
            logger.info(f"🛑 {self.agent_name} stopped listening")
            self.consumer.close()
    
    def stop_listening(self):
        """Stop listening to events"""
        if self.consumer:
            self.consumer.stop_consuming()
            self.consumer.close()
