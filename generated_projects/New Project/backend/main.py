# app/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.database.mongo import connect_to_mongo, close_mongo_connection
from app.routes.messages import router as messages_router
from app.utils.error_handling import handle_error

app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for the example
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers for application startup and shutdown
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Include message-related routes
app.include_router(messages_router, prefix="/api", tags=["messages"])

# Error handling middleware
app.add_exception_handler(Exception, handle_error)