"""
Event Publisher for RabbitMQ
Handles publishing events to the message broker
"""
import pika
import pika.exceptions
import logging
from typing import Optional
from config.environment import should_use_events, get_config
from events.schemas import AgentEvent

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Publishes agent events to RabbitMQ with automatic reconnection
    Falls back to no-op if events not enabled (K8s environment)
    """
    
    def __init__(self, rabbitmq_url: Optional[str] = None):
        self.enabled = should_use_events()
        self.rabbitmq_url = rabbitmq_url or (get_config()["event_streaming"]["url"] if self.enabled else None)
        self.connection = None
        self.channel = None
        
        if self.enabled:
            self._connect()
        else:
            logger.info("✅ EventPublisher initialized (no-op mode for K8s)")
    
    def _connect(self):
        """Establish connection to RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                return  # Already connected
            
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            
            # Declare exchange (idempotent)
            self.channel.exchange_declare(
                exchange='catalyst.events',
                exchange_type='topic',
                durable=True
            )
            
            logger.info("✅ EventPublisher connected to RabbitMQ")
        except Exception as e:
            logger.warning(f"Failed to connect to RabbitMQ: {e}")
            self.connection = None
            self.channel = None
            raise
    
    def _ensure_connection(self):
        """Ensure connection is alive, reconnect if needed"""
        try:
            if not self.connection or self.connection.is_closed:
                logger.info("Reconnecting to RabbitMQ...")
                self._connect()
            # Test connection with heartbeat
            self.connection.process_data_events(time_limit=0)
        except (pika.exceptions.AMQPConnectionError, 
                pika.exceptions.StreamLostError,
                pika.exceptions.ConnectionClosedByBroker,
                Exception) as e:
            logger.warning(f"Connection check failed, reconnecting: {e}")
            self.close()
            self._connect()
    
    async def publish(self, event: AgentEvent) -> bool:
        """
        Publish an event to RabbitMQ with automatic reconnection
        
        Args:
            event: AgentEvent to publish
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.enabled:
            # In K8s mode, events are disabled - just log
            logger.debug(f"Event (no-op): {event.event_type} from {event.actor}")
            return True
        
        # Retry publish with reconnection on failure
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Ensure connection is alive
                self._ensure_connection()
                
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
                
                # Skip Postgres audit logging (causes event loop issues in sync contexts)
                # Postgres audit can be re-enabled when full async refactor is done
                
                return True
                
            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.StreamLostError, 
                    pika.exceptions.ConnectionClosedByBroker,
                    ConnectionResetError) as e:
                logger.warning(f"Publish attempt {attempt + 1}/{max_retries} failed: {e}")
                self.close()  # Force close stale connection
                if attempt < max_retries - 1:
                    import time
                    time.sleep(0.5 * (attempt + 1))  # Backoff: 0.5s, 1s, 1.5s
                    continue
                else:
                    logger.error(f"Failed to publish event {event.event_type} after {max_retries} attempts")
                    return False
                    
            except Exception as e:
                logger.error(f"Unexpected error publishing event {event.event_type}: {e}")
                return False
        
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
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.debug("EventPublisher connection closed")
        except Exception as e:
            logger.debug(f"Error closing EventPublisher connection: {e}")
        finally:
            self.connection = None
            self.channel = None
    
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


def reset_event_publisher():
    """Reset singleton (useful for testing or reconnection)"""
    global _publisher
    if _publisher:
        _publisher.close()
    _publisher = None
