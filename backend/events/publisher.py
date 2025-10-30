"""
Event Publisher for RabbitMQ
Handles publishing events to the message broker
"""
import pika
import logging
from typing import Optional
from config.environment import should_use_events, get_config
from events.schemas import AgentEvent

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Publishes agent events to RabbitMQ
    Falls back to no-op if events not enabled (K8s environment)
    """
    
    def __init__(self, rabbitmq_url: Optional[str] = None):
        self.enabled = should_use_events()
        self.connection = None
        self.channel = None
        
        if self.enabled:
            try:
                rabbitmq_url = rabbitmq_url or get_config()["event_streaming"]["url"]
                self.connection = pika.BlockingConnection(
                    pika.URLParameters(rabbitmq_url)
                )
                self.channel = self.connection.channel()
                
                # Declare exchange (idempotent)
                self.channel.exchange_declare(
                    exchange='catalyst.events',
                    exchange_type='topic',
                    durable=True
                )
                
                logger.info("✅ EventPublisher initialized (RabbitMQ)")
            except Exception as e:
                logger.warning(f"Failed to connect to RabbitMQ: {e}. Events disabled.")
                self.enabled = False
        else:
            logger.info("✅ EventPublisher initialized (no-op mode for K8s)")
    
    async def publish(self, event: AgentEvent) -> bool:
        """
        Publish an event to RabbitMQ
        
        Args:
            event: AgentEvent to publish
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.enabled:
            # In K8s mode, events are disabled - just log
            logger.debug(f"Event (no-op): {event.event_type} from {event.actor}")
            return True
        
        try:
            routing_key = event.to_routing_key()
            message = event.to_json()
            
            self.channel.basic_publish(
                exchange='catalyst.events',
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent message
                    content_type='application/json',
                    headers={
                        'trace_id': str(event.trace_id),
                        'task_id': str(event.task_id),
                        'actor': event.actor,
                        'event_type': event.event_type
                    }
                )
            )
            
            logger.info(f"📤 Published event: {routing_key} (trace: {event.trace_id})")
            
            # Try to save to Postgres for audit (best effort, don't block on failure)
            try:
                if get_config()["databases"]["postgres"]["enabled"]:
                    # Fire-and-forget: create task but don't await
                    import asyncio
                    asyncio.create_task(self._save_to_postgres(event))
            except Exception as pg_error:
                # Log but don't fail the publish operation
                logger.debug(f"Postgres event audit skipped: {pg_error}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_type}: {e}")
            return False
    
    async def _save_to_postgres(self, event: AgentEvent):
        """Save event to Postgres for audit trail"""
        try:
            import asyncpg
            import json
            from config.environment import get_config
            
            postgres_url = get_config()["databases"]["postgres"]["url"]
            conn = await asyncpg.connect(postgres_url)
            
            # Convert payload dict to JSON string
            payload_json = json.dumps(event.payload) if isinstance(event.payload, dict) else str(event.payload)
            
            await conn.execute("""
                INSERT INTO agent_events (trace_id, task_id, actor, event_type, routing_key, payload, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, 
                event.trace_id,
                event.task_id,
                event.actor,
                event.event_type,
                event.to_routing_key(),
                payload_json,  # Now a JSON string instead of dict
                event.timestamp
            )
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save event to Postgres: {e}")
    
    def close(self):
        """Close connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("EventPublisher connection closed")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# Singleton instance
_publisher = None


def get_event_publisher() -> EventPublisher:
    """Get or create EventPublisher singleton"""
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher
