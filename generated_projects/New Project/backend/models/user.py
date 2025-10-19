from pydantic import BaseModel, EmailStr, Field
from uuid import UUID, uuid4
from datetime import datetime

class UserBase(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the user (UUID).")
    email: EmailStr = Field(..., description="User's email address, must be unique.")
    hashed_password: str = Field(..., description="Hashed password for the user's account.")
    is_active: bool = Field(default=True, description="Status indicating if the user is active.")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the user was created.")

    class Config:
        use_enum_values = True
        orm_mode = True  # Allows the model to work well with SQLAlchemy or ORM returns.
        

class UserCreate(UserBase):
    """Model for creating a user. Excludes the 'id' and 'created_at' fields."""
    id: UUID = None  # Users will not provide this when creating a user.
    created_at: datetime = None  # Users will not provide this when creating a user.


class UserRead(UserBase):
    """Model for reading user data, includes all fields."""
    pass


class UserUpdate(BaseModel):
    """Model for updating user data, allows partial updates."""
    email: EmailStr = Field(None, description="User's email address, optional for update.")
    hashed_password: str = Field(None, description="Hashed password for the user's account, optional for update.")
    is_active: bool = Field(None, description="Status indicating if the user is active, optional for update.")

    class Config:
        orm_mode = True  # Allows the model to work well with SQLAlchemy or ORM returns.