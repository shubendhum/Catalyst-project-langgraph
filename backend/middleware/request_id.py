"""
Request ID Middleware
Generates and injects request IDs into all requests for tracing
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import uuid
import time
import logging

from utils.logging_utils import set_request_id, get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Set in context
        set_request_id(req_id)
        
        # Add to request state
        request.state.request_id = req_id
        
        # Log request start
        start_time = time.time()
        
        logger.info(
            "Request started",
            extra={
                "path": str(request.url.path),
                "method": request.method,
                "req_id": req_id,
                "client": request.client.host if request.client else None
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Log request end
            logger.info(
                "Request completed",
                extra={
                    "path": str(request.url.path),
                    "method": request.method,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                    "req_id": req_id
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = req_id
            
            return response
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "path": str(request.url.path),
                    "method": request.method,
                    "latency_ms": latency_ms,
                    "req_id": req_id
                },
                exc_info=True
            )
            raise
