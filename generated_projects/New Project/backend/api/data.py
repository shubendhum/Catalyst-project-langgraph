from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import jwt
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Greeting API",
    description="API for managing greetings",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
DB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "greeting_db")

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize MongoDB client
@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(DB_URL)
    app.mongodb = app.mongodb_client[DB_NAME]

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Pydantic models
class GreetingBase(BaseModel):
    name: str

class GreetingCreate(GreetingBase):
    pass

class Greeting(GreetingBase):
    id: str
    message: str
    timestamp: datetime

    class Config:
        orm_mode = True

class GreetingResponse(BaseModel):
    message: str

class GreetingListResponse(BaseModel):
    greetings: List[Greeting]

# JWT Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    disabled: Optional[bool] = None

# Authentication utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    
    # In a real application, you would fetch the user from the database
    # For demonstration purposes, we'll just return a mock user
    user = User(username=token_data.username, disabled=False)
    if user is None:
        raise credentials_exception
    return user

# Routes
@app.get("/api/greeting", response_model=GreetingResponse)
async def get_default_greeting():
    """
    Get a default hello world greeting
    """
    try:
        return {"message": "Hello, World!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/greeting/{name}", response_model=GreetingResponse)
async def get_personalized_greeting(name: str):
    """
    Get a personalized greeting
    """
    try:
        return {"message": f"Hello, {name}!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/greeting", response_model=Greeting, status_code=201)
async def create_greeting(
    greeting: GreetingCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Save a new greeting to the database
    """
    try:
        greeting_data = {
            "id": str(uuid.uuid4()),
            "name": greeting.name,
            "message": f"Hello, {greeting.name}!",
            "timestamp": datetime.utcnow()
        }
        
        result = await app.mongodb.greetings.insert_one(greeting_data)
        
        if not result.acknowledged:
            raise HTTPException(status_code=500, detail="Failed to create greeting")
            
        return greeting_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/greetings", response_model=GreetingListResponse)
async def get_greeting_history(current_user: User = Depends(get_current_user)):
    """
    Get history of saved greetings
    """
    try:
        greetings = []
        cursor = app.mongodb.greetings.find({})
        
        async for document in cursor:
            # Convert ObjectId to string
            if "_id" in document:
                document.pop("_id")
            
            greetings.append(document)
        
        return {"greetings": greetings}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# JWT token endpoint
@app.post("/token", response_model=Token)
async def login_for_access_token(username: str, password: str):
    """
    Get JWT access token
    
    In a real application, you would validate the username and password against the database
    """
    # Mock authentication - replace with real authentication
    if username != "testuser" or password != "testpassword":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Additional CRUD operations
@app.get("/api/greeting/id/{greeting_id}", response_model=Greeting)
async def get_greeting_by_id(
    greeting_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific greeting by ID
    """
    try:
        greeting = await app.mongodb.greetings.find_one({"id": greeting_id})
        if greeting:
            if "_id" in greeting:
                greeting.pop("_id")  # Remove MongoDB's _id
            return greeting
        
        raise HTTPException(status_code=404, detail="Greeting not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/greeting/{greeting_id}", response_model=Greeting)
async def update_greeting(
    greeting_id: str,
    greeting_update: GreetingCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing greeting
    """
    try:
        # Check if greeting exists
        existing = await app.mongodb.greetings.find_one({"id": greeting_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Greeting not found")
            
        # Prepare update data
        update_data = {
            "name": greeting_update.name,
            "message": f"Hello, {greeting_update.name}!",
            # Keep the original timestamp or update it if needed
            # "timestamp": datetime.utcnow()  # Uncomment to update timestamp
        }
        
        result = await app.mongodb.greetings.update_one(
            {"id": greeting_id}, {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Greeting not found")
            
        # Get updated greeting
        updated_greeting = await app.mongodb.greetings.find_one({"id": greeting_id})
        if "_id" in updated_greeting:
            updated_greeting.pop("_id")
            
        return updated_greeting
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/greeting/{greeting_id}", status_code=204)
async def delete_greeting(
    greeting_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a greeting
    """
    try:
        result = await app.mongodb.greetings.delete_one({"id": greeting_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Greeting not found")
            
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)