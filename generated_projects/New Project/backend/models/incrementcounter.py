from datetime import datetime
from pydantic import BaseModel, Field, constr
from uuid import UUID
from typing import Dict, Any

class IncrementCounter(BaseModel):
    id: UUID = Field(..., description="Unique identifier for the increment counter", alias="_id")
    user_id: UUID = Field(..., description="Unique identifier for the user associated with this counter")
    data: Dict[str, Any] = Field(..., description="Additional data related to the increment counter")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the counter was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the counter was last updated")

    class Config:
        # To allow compatibility with MongoDB
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {UUID: str}  # Encode UUID as string for JSON serialization
        orm_mode = True  # Allow compatibility with ORM models

# Example usage:
# counter = IncrementCounter(id=UUID("12345678-1234-5678-1234-567812345678"), user_id=UUID("87654321-4321-8765-4321-567887654321"), data={"key": "value"})