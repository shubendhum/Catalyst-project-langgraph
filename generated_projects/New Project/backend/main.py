from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os
import uuid
from pydantic import BaseModel
from datetime import datetime

#MongoDB connection details
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "mydatabase")

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# Pydantic models
class User(BaseModel):
    id: str = str(uuid.uuid4())
    email: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = datetime.now()

class DisplayHelloWorldMessage(BaseModel):
    id: str = str(uuid.uuid4())
    user_id: str
    data: dict
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

# API endpoints
@app.get("/api/hello")
async def read_hello():
    try:
        return {"message": "Hello, World!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    try:
        server_status = client.admin.command('ping')
        return {"status": "Healthy", "server_status": server_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database connection error.")

# Route for user creation (example)
@app.post("/api/users/", response_model=User)
async def create_user(user: User):
    try:
        user_dict = user.dict()
        db.users.insert_one(user_dict)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Further endpoints and logic can be added here

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)