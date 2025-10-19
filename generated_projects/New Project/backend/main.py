# project_root/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from app.api.v1.greet import router as greet_router
import app.db.mongodb as db

# Initialize FastAPI app
app = FastAPI()

# CORS middleware setup
origins = [
    "http://localhost:8000",  # Update this to your frontend's URL or other origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
@app.on_event("startup")
async def startup_db_client():
    db.client = AsyncIOMotorClient('mongodb://localhost:27017')  # Replace with your MongoDB URI
    db.database = db.client['greeting_db']  # Specify the database name

@app.on_event("shutdown")
def shutdown_db_client():
    db.client.close()

# Include the greet router
app.include_router(greet_router, prefix="/api/greet", tags=["greet"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Error handling
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return HTTPException(status_code=500, detail=str(exc))