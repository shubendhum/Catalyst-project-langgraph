from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
import motor.motor_asyncio
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import os

app = FastAPI()

# MongoDB client
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client.mydatabase

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models
class User(BaseModel):
    username: str
    password: str

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str

class GreetingRequest(BaseModel):
    name: str

class GreetingResponse(BaseModel):
    message: str

# Exception handling
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

# JWT Methods
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

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

    # Here you would normally verify the user data from the DB
    # user = await get_user(token_data.username)  # Define this function
    user = None  # Placeholder for user verification
    if user is None:
        raise credentials_exception
    return user

# Routes

@app.get("/api/greet", response_model=GreetingResponse, status_code=200)
async def greet():
    return {"message": "Hello World"}

@app.post("/api/greet", response_model=GreetingResponse, status_code=200)
async def greet_with_name(greeting: GreetingRequest):
    if not greeting.name:
        raise HTTPException(status_code=400, detail="Bad Request - Name is required")
    return {"message": f"Hello, {greeting.name}"}

# Additional CRUD operations
@app.get("/api/users")
async def read_users():
    users = await db.users.find().to_list(100)  # Limit the number of results
    return users

@app.post("/api/users", response_model=UserInDB)
async def create_user(user: User):
    hashed_password = pwd_context.hash(user.password)
    user_in_db = UserInDB(**user.dict(), hashed_password=hashed_password)
    await db.users.insert_one(user_in_db.dict())
    return user_in_db

# More CRUD routes could be added with similar patterns...