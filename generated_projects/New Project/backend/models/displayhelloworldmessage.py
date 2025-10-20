from uuid import UUID
from pydantic import BaseModel, Field, constr
from datetime import datetime
from typing import Dict, Optional

class DisplayHelloWorldMessage(BaseModel):
    id: UUID = Field(default_factory=UUID, description="The unique identifier for the message")
    user_id: UUID = Field(..., description="The unique identifier of the user associated with the message")
    data: Dict[str, str] = Field(..., description="The data containing message details")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the message was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the message was last updated")

    class Config:
        schema_extra = {
            "example": {
                "id": UUID("123e4567-e89b-12d3-a456-426614174000"),
                "user_id": UUID("123e4567-e89b-12d3-a456-426614174001"),
                "data": {"message": "Hello, World!"},
                "created_at": "2023-10-05T12:34:56.789Z",
                "updated_at": "2023-10-06T12:34:56.789Z"
            }
        }

        # This will allow for MongoDB compatibility
        anystr_strip_whitespace = True
        use_enum_values = True