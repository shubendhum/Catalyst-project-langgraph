# app/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from app.api.routes import api_router
from app.config import MONGODB_URL

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = MongoClient(MONGODB_URL)
db = client.get_default_database()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Include the API routes
app.include_router(api_router, prefix="/api", tags=["API"])

# Add an error handler
@app.exception_handler(Exception)
async def unicorn_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)