"""
RabbitMQ Infrastructure Initialization
Ensures all exchanges, queues, and bindings are created on startup
"""
import pika
import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)


def init_rabbitmq(rabbitmq_url: str, max_retries: int = 10) -> bool:
    """
    Initialize RabbitMQ infrastructure on startup
    Creates exchange, queues, and bindings for event-driven agent system
    
    Args:
        rabbitmq_url: RabbitMQ connection URL
        max_retries: Maximum number of connection retry attempts
        
    Returns:
        bool: True if initialization successful, False otherwise
    """
    logger.info("🐰 Initializing RabbitMQ infrastructure...")
    
    # Agent routing key mappings
    routing_keys: Dict[str, str] = {
        "planner": "catalyst.task.initiated",
        "architect": "catalyst.plan.created",
        "coder": "catalyst.architecture.proposed",
        "tester": "catalyst.code.pr.opened",
        "reviewer": "catalyst.test.results",
        "deployer": "catalyst.review.decision",
        "explorer": "catalyst.explorer.scan.request",
        "orchestrator": "catalyst.*.complete"
    }
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting RabbitMQ connection (attempt {attempt + 1}/{max_retries})...")
            
            # Connect to RabbitMQ
            connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
            channel = connection.channel()
            
            # 1. Declare exchange (idempotent)
            channel.exchange_declare(
                exchange='catalyst.events',
                exchange_type='topic',
                durable=True
            )
            logger.info("✅ Created/verified exchange: catalyst.events (topic)")
            
            # 2. Create queues and bindings for each agent
            for agent_name, routing_key in routing_keys.items():
                queue_name = f"{agent_name}-queue"
                
                # Declare queue
                channel.queue_declare(
                    queue=queue_name,
                    durable=True,
                    arguments={
                        'x-message-ttl': 3600000,  # 1 hour TTL
                        'x-max-length': 10000       # Max 10k messages
                    }
                )
                
                # Bind queue to exchange with routing key
                channel.queue_bind(
                    exchange='catalyst.events',
                    queue=queue_name,
                    routing_key=routing_key
                )
                
                logger.info(f"✅ Created queue: {queue_name} → {routing_key}")
            
            # 3. Create dead letter queue for failed events
            channel.queue_declare(
                queue='failed-events',
                durable=True
            )
            logger.info("✅ Created dead letter queue: failed-events")
            
            # Close connection
            connection.close()
            
            logger.info("✅ RabbitMQ infrastructure initialized successfully!")
            logger.info(f"   📊 Created: 1 exchange, {len(routing_keys)} agent queues, 1 DLQ")
            
            return True
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.warning(f"RabbitMQ connection failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                sleep_time = min(2 ** attempt, 10)  # Exponential backoff, max 10s
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error("❌ Failed to initialize RabbitMQ after all retries")
                logger.error("   Event-driven mode will not work properly!")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error during RabbitMQ initialization: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                logger.error("❌ Failed to initialize RabbitMQ")
                return False
    
    return False


def verify_rabbitmq_setup(rabbitmq_url: str) -> bool:
    """
    Verify RabbitMQ infrastructure is correctly set up
    
    Args:
        rabbitmq_url: RabbitMQ connection URL
        
    Returns:
        bool: True if verification successful
    """
    try:
        connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
        channel = connection.channel()
        
        # Try to declare exchange (should already exist)
        channel.exchange_declare(
            exchange='catalyst.events',
            exchange_type='topic',
            durable=True,
            passive=True  # Check if exists without creating
        )
        
        connection.close()
        logger.info("✅ RabbitMQ verification successful")
        return True
        
    except Exception as e:
        logger.warning(f"RabbitMQ verification failed: {e}")
        return False
