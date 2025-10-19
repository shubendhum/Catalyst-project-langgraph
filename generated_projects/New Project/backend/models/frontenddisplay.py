from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Dict, Optional

class FrontendDisplay(BaseModel):
    id: UUID = Field(..., alias="_id")  # Assuming MongoDB _id is used for ID
    user_id: Optional[UUID] = Field(default=None, description="Associated User ID")
    data: Dict[str, str] = Field(..., description="Display data as a dictionary")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when updated")

    class Config:
        # Use alias for the MongoDB _id field
        allow_population_by_field_name = True
        json_encoders = {
            UUID: str  # Ensure UUIDs are represented as strings in JSON
        }