"""
Worker Thread Safety Utilities
Helpers for running async operations safely from worker threads
"""
import logging

logger = logging.getLogger(__name__)


async def safe_db_operation(operation_name: str, coro):
    """
    Safely execute a database operation that might be called from a worker thread.
    
    In event-driven mode, agents run in worker threads with isolated event loops.
    Motor (MongoDB async driver) is tied to the main event loop, so we can't use it
    from worker threads without getting "attached to a different loop" errors.
    
    This function wraps the operation and logs instead of executing to avoid errors.
    
    Args:
        operation_name: Name of the operation for logging
        coro: The coroutine to execute (or skip in worker context)
    
    Returns:
        None (operation is skipped)
    """
    logger.debug(f"Skipping {operation_name} in worker thread (Motor not thread-safe)")
    return None


async def safe_update_task_status(task_id: str, status: str, agent: str):
    """
    Safely update task status (noop in worker threads)
    
    NOTE: This is disabled in event-driven mode to avoid cross-loop issues.
    Task status should be tracked through events instead.
    """
    logger.info(f"Task {task_id} status: {status} (agent: {agent})")
    return None
