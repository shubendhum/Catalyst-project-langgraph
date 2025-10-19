from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Dict, Optional

class HelloWorldEndpoint(BaseModel):
    id: UUID = Field(..., description="Unique identifier for the HelloWorldEndpoint.")
    user_id: UUID = Field(..., description="Foreign key referencing the User.")
    data: Dict[str, str] = Field(..., description="Data associated with the HelloWorldEndpoint.")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the endpoint was created.")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the endpoint was last updated.")

    class Config:
        orm_mode = True  # Allows compatibility with ORM models, like SQLAlchemy
        json_encoders = {
            UUID: str  # Ensures UUIDs are serialized as strings in JSON
        }

# Example usage:
# endpoint = HelloWorldEndpoint(id=UUID('12345678-1234-5678-1234-567812345678'), user_id=UUID('87654321-4321-6789-4321-678943215678'), data={"key": "value"})