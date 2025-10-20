"""
Postgres Database Service
Handles async PostgreSQL connections with connection pooling
"""
import asyncpg
import logging
from typing import Optional, Dict, Any, List
from config.environment import should_use_postgres, get_config

logger = logging.getLogger(__name__)


class PostgresService:
    """
    PostgreSQL service with connection pooling
    Falls back to no-op if Postgres not available (K8s mode)
    """
    
    def __init__(self, postgres_url: Optional[str] = None):
        self.enabled = should_use_postgres()
        self.pool: Optional[asyncpg.Pool] = None
        self.postgres_url = postgres_url
        
        if self.enabled:
            if not self.postgres_url:
                config = get_config()
                self.postgres_url = config["databases"]["postgres"]["url"]
            logger.info("PostgresService initialized (will connect on first use)")
        else:
            logger.info("PostgresService initialized (disabled for K8s)")
    
    async def connect(self):
        """Create connection pool"""
        if not self.enabled or self.pool:
            return
        
        try:
            self.pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("✅ PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.enabled = False
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query without returning results"""
        if not self.enabled:
            return "SKIPPED"
        
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[Dict]:
        """Fetch multiple rows"""
        if not self.enabled:
            return []
        
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict]:
        """Fetch single row"""
        if not self.enabled:
            return None
        
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch single value"""
        if not self.enabled:
            return None
        
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")


# Singleton instance
_postgres_service = None


def get_postgres_service() -> PostgresService:
    """Get or create PostgresService singleton"""
    global _postgres_service
    if _postgres_service is None:
        _postgres_service = PostgresService()
    return _postgres_service


# Helper functions for common operations

async def create_task_record(
    task_id: str,
    project_id: str,
    trace_id: str,
    user_prompt: str
) -> bool:
    """Create a task record in Postgres"""
    try:
        db = get_postgres_service()
        await db.execute("""
            INSERT INTO tasks (id, project_id, trace_id, user_prompt, status, created_at)
            VALUES ($1, $2, $3, $4, 'pending', NOW())
        """, task_id, project_id, trace_id, user_prompt)
        return True
    except Exception as e:
        logger.error(f"Failed to create task record: {e}")
        return False


async def update_task_status(
    task_id: str,
    status: str,
    current_phase: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> bool:
    """Update task status"""
    try:
        db = get_postgres_service()
        
        if metadata:
            await db.execute("""
                UPDATE tasks 
                SET status = $1, current_phase = $2, metadata = $3, updated_at = NOW()
                WHERE id = $4
            """, status, current_phase, metadata, task_id)
        else:
            await db.execute("""
                UPDATE tasks 
                SET status = $1, current_phase = $2, updated_at = NOW()
                WHERE id = $3
            """, status, current_phase, task_id)
        
        return True
    except Exception as e:
        logger.error(f"Failed to update task status: {e}")
        return False


async def save_agent_event(event: 'AgentEvent') -> bool:
    """Save agent event to Postgres audit trail"""
    try:
        from events.schemas import AgentEvent
        
        db = get_postgres_service()
        await db.execute("""
            INSERT INTO agent_events (trace_id, task_id, actor, event_type, routing_key, payload, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
            str(event.trace_id),
            str(event.task_id),
            event.actor,
            event.event_type,
            event.to_routing_key(),
            event.payload,
            event.timestamp
        )
        return True
    except Exception as e:
        logger.error(f"Failed to save event to Postgres: {e}")
        return False


async def get_task_by_id(task_id: str) -> Optional[Dict]:
    """Get task by ID"""
    db = get_postgres_service()
    return await db.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)


async def get_active_tasks() -> List[Dict]:
    """Get all active tasks"""
    db = get_postgres_service()
    return await db.fetch("""
        SELECT * FROM active_tasks
        ORDER BY created_at DESC
    """)
