from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict, field_validator


class GreetingBase(BaseModel):
    """Base model for greeting data."""
    name: str = Field(..., description="Name of the person being greeted")
    message: str = Field(..., description="The full greeting message")

    @field_validator('name', 'message')
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v


class GreetingCreate(GreetingBase):
    """Model for creating a new greeting."""
    pass


class GreetingInDB(GreetingBase):
    """Model for greeting as stored in database."""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the greeting")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the greeting was created")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "name": "John",
                "message": "Hello, John!",
                "timestamp": "2023-01-01T00:00:00Z"
            }
        },
        # For MongoDB compatibility
        arbitrary_types_allowed=True,
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }
    )


class Greeting(GreetingInDB):
    """Model for greeting responses."""
    pass