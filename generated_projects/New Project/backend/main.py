#!/usr/bin/env python3
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import logging
import sys
from typing import List

# Import from your application modules
from app.core.config import settings
from app.db.mongodb import get_database, close_database_connection, init_db
from app.api.routes import greeting_router
from app.models.health import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Connect to database
    logger.info("Starting up application...")
    await init_db()
    logger.info("Database connection initialized")
    
    yield
    
    # Shutdown: Close database connection
    logger.info("Shutting down application...")
    await close_database_connection()
    logger.info("Database connection closed")


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Greeting API Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Main API router
api_router = APIRouter(prefix="/api")

# Health check endpoint
@api_router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify the API is running
    """
    try:
        # Verify database connection is working
        db = await get_database()
        await db.command("ping")
        return {
            "status": "ok",
            "message": "Service is healthy",
            "version": app.version
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

# Include greeting routes
api_router.include_router(greeting_router.router)

# Add all routes to the app
app.include_router(api_router)


@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint that redirects to API documentation
    """
    return {"message": "Welcome to the Greeting API", "docs": "/api/docs"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )