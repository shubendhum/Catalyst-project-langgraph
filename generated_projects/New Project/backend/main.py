# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import motor.motor_asyncio
import os
import uuid
from datetime import datetime
from bson import ObjectId

# Initialize FastAPI application
app = FastAPI()

# CORS middleware setup
origins = [
    "http://localhost:3000",  # Allow your frontend to connect
    "https://yourfrontend.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_DETAILS = os.getenv("MONGO_DETAILS", "mongodb://localhost:27017")  # use your MongoDB URI
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.your_database_name  # Change this to your database name
users_collection = database.users
helloworldendpoints_collection = database.helloworldendpoints
frontenddisplays_collection = database.frontenddisplays
stylingwithtailwindcsss_collection = database.stylingwithtailwindcsss

# Pydantic models for serialization
class User(BaseModel):
    id: str
    email: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = None

class HelloWorldResponse(BaseModel):
    message: str

class HelloWorldData(BaseModel):
    user_id: str
    data: dict

# Create a health check endpoint
@app.get("/api/health", response_model=HelloWorldResponse)
async def health_check():
    return HelloWorldResponse(message="API is healthy!")

# Hello World endpoint
@app.get("/api/hello", response_model=HelloWorldResponse)
async def hello_world():
    return HelloWorldResponse(message="Hello, World!")

# Error handling for Invalid Object ID
@app.exception_handler(ValueError)
async def value_error_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )

# Run the server with `uvicorn main:app --reload`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)