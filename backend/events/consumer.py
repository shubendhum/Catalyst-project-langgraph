"""
Event Consumer for RabbitMQ
Handles consuming events from message queues
"""
import pika
import logging
import asyncio
from typing import Callable, List, Optional
from config.environment import should_use_events, get_config
from events.schemas import AgentEvent

logger = logging.getLogger(__name__)


class EventConsumer:
    """
    Consumes agent events from RabbitMQ
    Falls back to no-op if events not enabled (K8s environment)
    """
    
    def __init__(
        self, 
        agent_name: str,
        routing_keys: List[str],
        rabbitmq_url: Optional[str] = None
    ):
        self.agent_name = agent_name
        self.routing_keys = routing_keys
        self.enabled = should_use_events()
        self.connection = None
        self.channel = None
        self.consumer_tag = None
        
        if self.enabled:
            try:
                rabbitmq_url = rabbitmq_url or get_config()["event_streaming"]["url"]
                self.connection = pika.BlockingConnection(
                    pika.URLParameters(rabbitmq_url)
                )
                self.channel = self.connection.channel()
                
                # Declare queue
                self.queue_name = f"{agent_name}-queue"
                self.channel.queue_declare(
                    queue=self.queue_name,
                    durable=True,
                    arguments={
                        'x-message-ttl': 3600000,  # 1 hour
                        'x-max-length': 10000
                    }
                )
                
                # Bind to routing keys
                for routing_key in self.routing_keys:
                    self.channel.queue_bind(
                        exchange='catalyst.events',
                        queue=self.queue_name,
                        routing_key=routing_key
                    )
                    logger.info(f"📥 {agent_name} bound to {routing_key}")
                
                logger.info(f"✅ EventConsumer initialized for {agent_name}")
                
            except Exception as e:
                logger.warning(f"Failed to connect to RabbitMQ: {e}. Consumer disabled.")
                self.enabled = False
        else:
            logger.info(f"✅ EventConsumer for {agent_name} (no-op mode for K8s)")
    
    def start_consuming(
        self, 
        callback: Callable[[AgentEvent], None],
        prefetch_count: int = 1
    ):
        """
        Start consuming events from queue
        
        Args:
            callback: Function to call with each event
            prefetch_count: Number of messages to prefetch
        """
        if not self.enabled:
            logger.info(f"{self.agent_name} consumer not started (K8s mode)")
            return
        
        try:
            # Set QoS
            self.channel.basic_qos(prefetch_count=prefetch_count)
            
            # Wrapper for callback
            def on_message(ch, method, properties, body):
                try:
                    # Parse event
                    event = AgentEvent.from_json(body.decode('utf-8'))
                    
                    logger.info(
                        f"📨 {self.agent_name} received: {event.event_type} "
                        f"(trace: {event.trace_id})"
                    )
                    
                    # Call user callback
                    callback(event)
                    
                    # Acknowledge message
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
                    # Negative acknowledge - will retry or go to DLQ
                    ch.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=False  # Don't requeue, let it go to DLQ
                    )
            
            # Start consuming
            self.consumer_tag = self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=on_message,
                auto_ack=False
            )
            
            logger.info(f"🎧 {self.agent_name} listening on {self.queue_name}...")
            self.channel.start_consuming()
            
        except Exception as e:
            logger.error(f"Error in {self.agent_name} consumer: {e}")
    
    async def start_consuming_async(
        self,
        callback: Callable,
        prefetch_count: int = 1
    ):
        """
        Start consuming events asynchronously
        
        Args:
            callback: Async function to call with each event
            prefetch_count: Number of messages to prefetch
        """
        if not self.enabled:
            return
        
        def sync_wrapper(event: AgentEvent):
            """Wrapper to run async callback in event loop"""
            asyncio.create_task(callback(event))
        
        self.start_consuming(sync_wrapper, prefetch_count)
    
    def stop_consuming(self):
        """Stop consuming events"""
        if self.channel and self.consumer_tag:
            self.channel.basic_cancel(self.consumer_tag)
            logger.info(f"🛑 {self.agent_name} stopped consuming")
    
    def close(self):
        """Close connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info(f"EventConsumer for {self.agent_name} connection closed")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


def create_consumer_for_agent(agent_name: str) -> EventConsumer:
    """
    Create EventConsumer with appropriate routing keys for given agent
    
    Args:
        agent_name: Name of agent (planner, architect, coder, etc.)
        
    Returns:
        EventConsumer configured for that agent
    """
    routing_keys_map = {
        "planner": ["catalyst.task.initiated"],
        "architect": ["catalyst.plan.created"],
        "coder": ["catalyst.architecture.proposed"],
        "tester": ["catalyst.code.pr.opened"],
        "reviewer": ["catalyst.test.results"],
        "deployer": ["catalyst.review.decision"],
        "explorer": ["catalyst.explorer.scan.request"],
        "orchestrator": ["catalyst.*.complete", "catalyst.*.failed"]
    }
    
    routing_keys = routing_keys_map.get(agent_name, [])
    
    if not routing_keys:
        logger.warning(f"No routing keys defined for agent: {agent_name}")
    
    return EventConsumer(agent_name, routing_keys)
