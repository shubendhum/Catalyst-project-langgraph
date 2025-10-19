from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base User model with common fields."""
    email: EmailStr = Field(..., description="User's email address")
    is_active: bool = Field(default=True, description="Whether the user account is active")


class UserCreate(UserBase):
    """User creation model with password field."""
    password: str = Field(..., min_length=8, description="User's password")


class UserInDB(UserBase):
    """User model as stored in the database."""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the user")
    hashed_password: str = Field(..., description="Hashed password")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the user was created")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "collection": "users"
        }
    )


class User(UserBase):
    """User model returned to clients (without the password)."""
    id: UUID = Field(..., description="Unique identifier for the user")
    created_at: datetime = Field(..., description="When the user was created")
    
    model_config = ConfigDict(
        from_attributes=True
    )


class UserUpdate(BaseModel):
    """User update model with optional fields."""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, description="New password")
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(
        exclude_unset=True
    )