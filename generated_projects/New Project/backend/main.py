# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
import uuid
from datetime import datetime
from api import router as api_router
from services import GreetingService  # assuming service files follow this pattern
from utils import get_greeting  # placeholder for utility functions

# Initialize FastAPI app
app = FastAPI()

# CORS middleware
origins = [
    "http://localhost:3000",  # Adjust according to your frontend location
    "https://example.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGODB_URL)

try:
    client.admin.command('ping')  # Validate connection
except ConnectionFailure:
    raise ConnectionError("Failed to connect to MongoDB")

db = client['your_database_name']  # replace with your database name

# Include the API router
app.include_router(api_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# API route handling
@app.get("/api/greeting")
async def fetch_greeting():
    """Fetches the current greeting message."""
    greeting = await get_greeting()  # Get greeting from utils or service
    if greeting is None:
        raise HTTPException(status_code=404, detail="Greeting not found")
    return {"message": greeting}

@app.post("/api/greeting")
async def update_greeting(message: str):
    """Updates the greeting message."""
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    success = await GreetingService.update_greeting(message)  # Business logic service
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update greeting")
    return {"success": True, "message": "Greeting updated successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)