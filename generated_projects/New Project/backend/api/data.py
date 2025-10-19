from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
import jwt
from typing import Optional

# Initialize FastAPI app
app = FastAPI()

# MongoDB client initialization
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["greet_app"]
collection = db["greetings"]

# JWT secret key and algorithm
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models
class GreetingRequest(BaseModel):
    name: str

class GreetingResponse(BaseModel):
    message: str

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    disabled: Optional[bool] = None

# Dependency for user authentication 
def fake_decode_token(token):
    return User(username=token)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Note: In real applications, you'd validate the token and get the user
    user = fake_decode_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return user

# POST endpoint to greet a user
@app.post("/api/greet", response_model=GreetingResponse, status_code=status.HTTP_200_OK)
async def greet_user(greeting: GreetingRequest, current_user: User = Depends(get_current_user)):
    if not greeting.name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name is required")
    
    greeting_message = f"Hello, {greeting.name}!"
    
    # Saving greeting to the MongoDB collection (optional)
    await collection.insert_one({"name": greeting.name, "message": greeting_message})

    return GreetingResponse(message=greeting_message)

# GET endpoint for default greeting
@app.get("/api/greet", response_model=GreetingResponse, status_code=status.HTTP_200_OK)
async def get_default_greeting(current_user: User = Depends(get_current_user)):
    return GreetingResponse(message="Hello, Guest!")

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal Server Error"},
    )

# Function to create a fake token for demonstration purposes
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Here you should take the username and password, validate them and return a JWT token
    return Token(access_token="fake-token", token_type="bearer")

# To run the application, use the command below:
# uvicorn your_filename:app --reload