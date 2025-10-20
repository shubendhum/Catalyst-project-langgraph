from pydantic import BaseModel, Field
from pydantic.networks import EmailStr
from typing import Dict, Optional
from uuid import UUID
from datetime import datetime

class BackendAPIEndpoint(BaseModel):
    id: UUID = Field(..., description="Unique identifier for the backend API endpoint")
    user_id: Optional[UUID] = Field(None, description="ID of the associated user")
    data: Dict = Field(..., description="Data related to the backend API endpoint")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the endpoint was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the endpoint was last updated")

    class Config:
        # This class will hold MongoDB specific configurations
        json_encoders = {
            UUID: str,  # Encode UUIDs as strings for MongoDB
            datetime: lambda v: v.isoformat() if v else None,  # Encode datetimes as ISO strings
        }
        # Add other MongoDB-related configurations if necessary
        arbitrary_types_allowed = True